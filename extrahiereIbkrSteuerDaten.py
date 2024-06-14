'''
todos
Call kauf
put kauf
Aktien kauf
Aktien verkauf
gekaufte Aktien verkauf mit puts
umrechnen in euro
'''

import pandas as pd
import argparse
import csv
import re

#--------------------------------------------------------------------------------------------------------------------
debug = False
#--------------------------------------------------------------------------------------------------------------------
def getEncoding(filename:str) -> str:
    import chardet
    with open(filename, 'rb') as f:  # Öffnen im Binärmodus
        rawdata = f.read()
    result = chardet.detect(rawdata)
    encoding = result['encoding']
    print("Encoding = ", encoding)
    return encoding
#--------------------------------------------------------------------------------------------------------------------
pattern = r',(?=(?:[^"]*"[^"]*")*[^"]*$)'
def count_delimiters(text:str, s:str=","):
    matches = re.findall(pattern, text)
    nrs = len(matches)
    return nrs
#--------------------------------------------------------------------------------------------------------------------
def alignSeparators(file_path, output_file, encoding):
    with open(file_path, 'r', encoding=encoding) as file:
        lines = file.readlines()

    max_separators = max(count_delimiters(line) for line in lines)
    # Jede Zeile auf die maximale Anzahl an Separatoren auffüllen
    aligned_lines = []
    for line in lines:
        current_separators = count_delimiters(line)
        aligned_lines.append(line.strip() + ',' * (max_separators - current_separators) + '\n')
    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(aligned_lines)
    return output_file
#--------------------------------------------------------------------------------------------------------------------
class MyCustomError(Exception):
    pass
#--------------------------------------------------------------------------------------------------------------------
class CSVTableProcessor:
    def __init__(self, file_path, delimiter, decimal, encoding):
        self.file_path = file_path
        self.encoding = encoding
        self.delimiter = delimiter
        self.name = ""
        self.result = None
        try:
            self.data = pd.read_csv(file_path, delimiter=delimiter, decimal=decimal,
                                     encoding=encoding, header=None, quotechar='"',  encoding_errors='replace')
        except pd.errors.ParserError as e:
            print(f"Error reading CSV file: {e}")
            self.data = None
            exit()
        self.tables = self._split_into_tables()
    #-------------------------------------------------------------------------------------------------
    def _split_into_tables(self):
        """Teilt die Daten in separate Tabellen auf, basierend auf den Werten in Spalte A und B."""
        tables = {}
        current_table_name = None
        current_table_data = []

        for index, row in self.data.iterrows():
            table_name = row.iloc[0]
            row_type = row.iloc[1]

            if pd.notna(table_name) and row_type == 'Header':
                if current_table_name is not None and current_table_data:
                    # Speichern der vorherigen Tabelle
                    tables[current_table_name] = pd.DataFrame(current_table_data[1:], columns=current_table_data[0])
                current_table_name = table_name
                current_table_data = [row[2:].tolist()]
            elif row_type == 'Data':
                current_table_data.append(row[2:].tolist())
            #print(f"Processing row {index}: table_name={table_name}, row_type={row_type}")
        # Speichern der letzten Tabelle
        if current_table_name is not None and current_table_data:
            tables[current_table_name] = pd.DataFrame(current_table_data[1:], columns=current_table_data[0])

        return tables
    #-------------------------------------------------------------------------------------------------
    def get_table(self, table_name):
        """Gibt die Tabelle mit dem angegebenen Namen zurück."""
        return self.tables.get(table_name)
    #-------------------------------------------------------------------------------------------------
    def getRowsOfColumnsContainingStr(self, table, col:str, str:str):
        return table[table[col].str.contains(str, na=False)]
    #-------------------------------------------------------------------------------------------------
    def extractSold(self):
        table = self.get_table('Transaktionen')
        return self.getRowsOfColumnsContainingStr(table, "Code", "O")
    #-------------------------------------------------------------------------------------------------
    def extractExecutedShorts(self):
        table = self.get_table('Transaktionen')
        self.executed = self.getRowsOfColumnsContainingStr(table, "Code", "A.*")
        return self.executed
    #-------------------------------------------------------------------------------------------------
    def splitSymbolExecutedShorts(self,table):
        split_columns = table['Symbol'].str.split(' ', expand=True)
        split_columns.columns = ['Ticker', 'Bis', 'Preis', 'Typ']
        table = table.drop(columns=['Symbol']).join(split_columns)
        table = table.drop_duplicates(keep=False)
        return table[["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge']]   
    #-------------------------------------------------------------------------------------------------
    def getSoldOptions(self):
        df = self.extractSold()
        df = self.getRowsOfColumnsContainingStr(df, "Symbol", ".*?[CP]$")
        cols1 = ["Erlös","Prov./Gebühr"]
        for i in cols1:
            df[i] = pd.to_numeric(df[i])
        cols = ["Datum/Zeit", "Symbol"] + cols1
        str = df[cols].to_string() + "\n" + df[cols1].sum().to_string()
        print(str)
    #-------------------------------------------------------------------------------------------------
    def getExecutedCalls(self):
        calls = self.getRowsOfColumnsContainingStr(self.executed, "Symbol", ".*?C$")
        calls = self.splitSymbolExecutedShorts(calls)
        return calls[["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge',]]   
    #-------------------------------------------------------------------------------------------------
    def getExecutedPuts(self):
        puts = self.getRowsOfColumnsContainingStr(self.executed, "Symbol", ".*?P$")
        puts = self.splitSymbolExecutedShorts(puts)
        return puts[["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge',]]   
    #-------------------------------------------------------------------------------------------------
    def display_tables(self):
        """Zeigt alle Tabellen an."""
        for name, table in self.tables.items():
            print(f"Tabelle: {name}")
            print(table)
            print("\n")
    #-------------------------------------------------------------------------------------------------
    def filterTable(self, table_name, headerColumnName, search,range):
        self.result = None
        table = self.get_table(table_name)
        if table is None:
            raise MyCustomError(f"Tabelle '{table_name}' error.")
        else:
            filtered_table = table[table[headerColumnName].str.contains(search, na=False)]
            filtered_table = filtered_table.iloc[:, 0:range]
            self.result = filtered_table
            self.name = table_name
        return self.result
    #-------------------------------------------------------------------------------------------------
    def getNameResult(self):
        return [self.name, self.result]
    #-------------------------------------------------------------------------------------------------
    def delCols(self,cols):
        for col in cols:
            del self.result[col]
    #-------------------------------------------------------------------------------------------------
    def displayLastExecutionResult(self,col:str=None, filter:str = None):
        try:
            print(f"Tabelle: {self.name}")
            t = self.result
            if col is None:
                print(t.to_string(na_rep='-'))  # Gibt die gefilterte Tabelle aus, ohne Kürzungen
            else:
                print(t[t[col] == filter])
        except MyCustomError as e:
            print(f"Caught a custom exception: {e}")
#--------------------------------------------------------------------------------------------------------------------
def calculate_differences(puts_df, calls_df):
    p = puts_df
    # Konvertiere das Datum/Zeit Feld in ein datetime Objekt für einfachere Verarbeitung
    sd = 'Datum/Zeit'
    sp = 'Preis'
    sm = 'Menge'
    st = 'Ticker'
    
    p[sd] = pd.to_datetime(p[sd])
    calls_df[sd] = pd.to_datetime(calls_df[sd])
    # Konvertiere Preis- und Mengen-Spalten von String zu float bzw. int
    p[sp] = p[sp].astype(float)
    p[sm] = p[sm].astype(int)
    calls_df[sp] = calls_df[sp].astype(float)
    calls_df[sm] = calls_df[sm].astype(int)
    
    results = []    
    # Iteriere über die Ticker in den Calls
    for ticker in calls_df[st].unique():
        calls = calls_df[calls_df[st] == ticker]
        puts = p[p[st] == ticker]        
        # Berechne die minimale Anzahl an Puts und Calls
        total_quantity = min(puts[sm].sum(), calls[sm].sum())        
        if total_quantity > 0:
            # Iteriere über die Calls und Puts bis die Mengen aufgebraucht sind
            for call_idx, call_row in calls.iterrows():
                if total_quantity <= 0:
                    break
                for put_idx, put_row in puts.iterrows():
                    if total_quantity <= 0:
                        break                    
                    # Berechne die Menge für diese Transaktion
                    transaction_quantity = min(call_row[sm], put_row[sm], total_quantity)
                    if transaction_quantity > 0:
                        results.append({
                            st: ticker,
                            'Datum/Zeit_put': put_row[sd],
                            'Datum/Zeit_call': call_row[sd],
                            'Preis_put': put_row[sp],
                            'Preis_call': call_row[sp],
                            'Preis_Differenz': (call_row[sp] - put_row[sp]),
                            sm: transaction_quantity
                        })
                        # Reduziere die Mengen und die Transaktions Menge
                        p.at[put_idx, sm] -= transaction_quantity
                        calls_df.at[call_idx, sm] -= transaction_quantity
                        total_quantity -= transaction_quantity    
    # Erstelle einen DataFrame aus den Ergebnissen
    result_df = pd.DataFrame(results)
    return result_df
#--------------------------------------------------------------------------------------------------------------------
def showSpecificTable(obj, tableName:str,columns):
    table = obj.get_table(tableName)
    if table is not None:
        if columns:
            col_range = columns.split('-')
            start_col = int(col_range[0])
            end_col = int(col_range[1]) + 1
            table = table.iloc[:, start_col:end_col]
        print(f"Tabelle: {tableName}")
        print(table.to_string())
    else:
        print(f"Tabelle '{tableName}' nicht gefunden.")
#--------------------------------------------------------------------------------------------------------------------
def showTableColumn(prefix,table, frm, to):
    print(prefix,end=":")
    for i in range(frm,to):
        print(table.iloc[i],end=",")
    print()
#--------------------------------------------------------------------------------------------------------------------
def getExecutedShorts(obj):
    obj.getSoldOptions()
    executedShorts = obj.extractExecutedShorts()
    p = obj.getExecutedPuts()
    c = obj.getExecutedCalls()
    return executedShorts, p,c
#--------------------------------------------------------------------------------------------------------------------
def showTaxRelevantTables(obj):
    print("-"*100)
    table_name = 'Übersicht  zur realisierten und unrealisierten Performance'
    obj.filterTable(table_name,'Vermögenswertkategorie','Gesamt',7)
    obj.delCols(['Symbol', 'Kostenanp.'])
    # rename
    r = obj.getNameResult()[1]['Vermögenswertkategorie']
    for i, item in enumerate(['Gesamt Aktien','Gesamt Optionen','Gesamt Devisen']):
        r.iat[i] = item
    obj.displayLastExecutionResult()
    print("-"*100)
    obj.filterTable('Zinsen','Währung','Gesamt*',4)
    obj.delCols(['Datum', 'Beschreibung'])
    obj.displayLastExecutionResult("Währung","Gesamt Zinsen in EUR")
    print("-"*100)
    obj.filterTable('Quellensteuer','Währung','Gesamt*',5)
    obj.delCols(['Datum', 'Beschreibung', 'Code'])
    obj.displayLastExecutionResult('Währung',"Gesamt Quellensteuer in EUR")
    print("-"*100)
    obj.filterTable('Dividenden','Währung','Gesamt*',5)
    obj.delCols(['Datum', 'Beschreibung', 'Code'])
    obj.displayLastExecutionResult('Währung',"Gesamtwert in EUR")
    print("-"*100)
#--------------------------------------------------------------------------------------------------------------------
def showCorrectedCalculation(obj):
    print("-"*100)
    executedShorts,p,c = getExecutedShorts(obj)
    print("-"*100)
    #print("\nExecuted Shorts\n", executedShorts.to_string(na_rep='-'))
    print("\nAusgeführte Puts\n" , p.to_string(na_rep='-'))
    print("\nAusgeführte Calls\n", c.to_string(na_rep='-'))
    print()

    putsMinusCalls = calculate_differences(p, c)
    print("Calls vs puts:\n", putsMinusCalls.to_string(na_rep='-'))
    if 1:
        df = putsMinusCalls
        col= "Preis_Differenz"
        plus = df[df[col] > 0][col].sum()
        minus = df[df[col] < 0][col].sum()
        print("-"*100)
        print("Aktien Gewinn:", 100*plus)
        print("Aktien Verlust:", 100*minus)
        print("-"*100)

    if debug: print("Übrig gebliebene puts:\n", p.to_string(na_rep='-'))
    p.drop('Bis', axis=1, inplace=True)    
    p["Menge"] *= 100
    print("Bestehende Aktien:\n", p[p["Menge"]>0].to_string(na_rep='-'))
    print("-"*100)
#--------------------------------------------------------------------------------------------------------------------
def parseArguments():
    parser = argparse.ArgumentParser(description='Lade eine IBKR/CAPTRADER CSV Datei und erstelle Daraus separate Tabellen.')
    parser.add_argument('file_path', type=str, help='Dateiname mit Pfadangabe')
    parser.add_argument('--delimiter', type=str, default=',', help='Trennzeichen für Spalten in der CSV Datei')
    parser.add_argument('--decimal', type=str, default='.', help='Dezimalpunkt Zeichen für Nummern in der CSV Datei')
    parser.add_argument('--encoding', type=str, default='UTF-8-SIG', help='Zeichensatz der CSV Datei')
    parser.add_argument('--table', type=str, help='Tabellenname zum Anzeigen')
    parser.add_argument('--columns', type=str, help='Spalten zum Anzeigen (z.B., "0-5")')
    parser.add_argument('--tax', action='store_true', help='Tax output')
    parser.add_argument('--new', action='store_true', help='Manual calculation')
    parser.add_argument('--list', action='store_true', help='Ausgabe verfügbarer Tabellen')
    parser.add_argument('--align', type=str, help='Align csv separators')
    return parser.parse_args()
#--------------------------------------------------------------------------------------------------------------------
def main():
    args = parseArguments()
    filename = args.file_path

    if args.encoding != "UTF-8-SIG":    
        args.encoding = getEncoding(filename)
    if args.align:
        alignSeparators(args.file_path, args.align, args.encoding)
        filename = args.align

    processor = CSVTableProcessor(filename, delimiter=args.delimiter, decimal=args.decimal, encoding=args.encoding)
    if args.list:
        availableTables = list(processor.tables.keys())
        print("Verfügbare Tabellen:", availableTables)

    if args.tax:
        showTaxRelevantTables(processor)
    if args.new:
        showCorrectedCalculation(processor)
    if args.table:
        showSpecificTable(processor,args.table,args.columns)
#--------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
