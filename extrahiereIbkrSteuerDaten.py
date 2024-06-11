import pandas as pd
import argparse
import csv
import re
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
    def extractExecutedShorts(self):
        table = self.get_table('Transaktionen')
        self.executed = self.getRowsOfColumnsContainingStr(table, "Code", "A.*")
        return self.executed
    #-------------------------------------------------------------------------------------------------
    def splitSymbolExecutedShorts(self,table):
        split_columns = table['Symbol'].str.split(' ', expand=True)
        split_columns.columns = ['Ticker', 'Bis', 'Preis', 'Typ']
        table = table.drop(columns=['Symbol']).join(split_columns)
        return table[["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge']]   
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
    def displayLastExecutionResult(self):
        try:
            print(f"Tabelle: {self.name}")
            print(self.result.to_string(na_rep='-'))  # Gibt die gefilterte Tabelle aus, ohne Kürzungen
        except MyCustomError as e:
            print(f"Caught a custom exception: {e}")
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
def showTaxRelevantTables(obj):
    executedShorts = obj.extractExecutedShorts()
    #print("Executed Shorts\n", executedShorts.to_string(na_rep='-'))
    print("\nAusgeführte Calls\n", obj.getExecutedCalls().to_string(na_rep='-'))
    print("\nAusgeführte Puts\n" , obj.getExecutedPuts().to_string(na_rep='-'))
    print()

    table_name = 'Übersicht  zur realisierten und unrealisierten Performance'
    obj.filterTable(table_name,'Vermögenswertkategorie','Gesamt',7)
    obj.delCols(['Symbol', 'Kostenanp.'])
    # rename
    r = obj.getNameResult()[1]['Vermögenswertkategorie']
    for i, item in enumerate(['Gesamt Aktien','Gesamt Optionen','Gesamt Devisen']):
        r.iat[i] = item
    obj.displayLastExecutionResult()
    print("\n")

    obj.filterTable('Zinsen','Währung','Gesamt*',4)
    obj.delCols(['Datum', 'Beschreibung'])
    obj.displayLastExecutionResult()
    print("\n")
    obj.filterTable('Quellensteuer','Währung','Gesamt*',5)
    obj.delCols(['Datum', 'Beschreibung', 'Code'])
    obj.displayLastExecutionResult()
    print("\n")
    obj.filterTable('Dividenden','Währung','Gesamt*',5)
    obj.delCols(['Datum', 'Beschreibung', 'Code'])
    obj.displayLastExecutionResult()
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

    if args.table:
        showSpecificTable(processor,args.table,args.columns)
#--------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
