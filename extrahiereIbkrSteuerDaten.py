'''
Du bit ein python und pandas Experte und kennst dich außerdem mit IBKR aus.
Ich habe ein Modul, dass aus einer CSV Datei von IBKR die Steuertabellen in ein pandas dataframe überführt.

''' 
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

    # BOM entfernen (falls vorhanden)
    #if lines[0].startswith('\ufeff'):  lines[0] = lines[0][1:]

    max_separators = max(count_delimiters(line) for line in lines)
    # Jede Zeile auf die maximale Anzahl an Separatoren auffüllen
    aligned_lines = []
    for line in lines:
        current_separators = count_delimiters(line)
        # Füge die fehlenden Separatoren hinzu
        aligned_lines.append(line.strip() + ',' * (max_separators - current_separators) + '\n')
    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(aligned_lines)
    return output_file
#--------------------------------------------------------------------------------------------------------------------
class MyCustomError(Exception):
    pass
#--------------------------------------------------------------------------------------------------------------------
# wahrungsrecher.org/historisch/us-dollar/europa/april-2023
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
        #self.data = self.data.applymap (lambda x: str(x).replace(',', '.') if isinstance(x, str) else x)
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
            print(f"Table: {name}")
            print(table)
            print("\n")
    #-------------------------------------------------------------------------------------------------
    def filterTable(self, table_name, headerColumnName, search,range):
        table = self.get_table(table_name)
        if table is None:
            raise MyCustomError(f"Table '{table_name}' error.")
        else:
            filtered_table = table[table[headerColumnName].str.contains(search, na=False)]
            filtered_table = filtered_table.iloc[:, 0:range]
            self.result = filtered_table
            self.name = table_name
        return self.result
    #-------------------------------------------------------------------------------------------------
    def displayLastExecutionResult(self):
        try:
            print(f"Table: {self.name}")
            print(self.result.to_string(na_rep='-'))  # Gibt die gefilterte Tabelle aus, ohne Kürzungen
        except MyCustomError as e:
            print(f"Caught a custom exception: {e}")
#--------------------------------------------------------------------------------------------------------------------
def main():
    if 0:
        processor = CSVTableProcessor("./mytest.csv", delimiter=",", decimal=".", encoding='utf-8')
        executedShorts = processor.extractExecutedShorts()
    else:    
        parser = argparse.ArgumentParser(description='Process a CSV file and split it into separate tables.')
        parser.add_argument('file_path', type=str, default='./mytest.csv', help='Path to the CSV file')
        parser.add_argument('--delimiter', type=str, default=',', help='Delimiter used in the CSV file')
        parser.add_argument('--decimal', type=str, default='.', help='Decimal point character used in the CSV file')
        parser.add_argument('--encoding', type=str, default='UTF-8-SIG', help='Encoding of the CSV file')
        parser.add_argument('--table', type=str, help='Name of the table to display')
        parser.add_argument('--columns', type=str, help='Range of columns to display (e.g., "0-5")')
        parser.add_argument('--tax', action='store_true', help='Tax output')
        parser.add_argument('--list', action='store_true', help='List of available tables')
        parser.add_argument('--align', type=str, help='Align csv separators')
        args = parser.parse_args()

        filename = args.file_path

        if args.encoding != "UTF-8-SIG":    args.encoding = getEncoding(filename)
        if args.align:
            alignSeparators(args.file_path, args.align, args.encoding)
            filename = args.align

        processor = CSVTableProcessor(filename, delimiter=args.delimiter, decimal=args.decimal, encoding=args.encoding)
        if args.list:
            # Überprüfen der verfügbaren Tabellen
            available_tables = list(processor.tables.keys())
            print("Verfügbare Tabellen:", available_tables)
    

        if args.tax:            
            executedShorts = processor.extractExecutedShorts()
            #print("Executed Shorts\n", executedShorts.to_string(na_rep='-'))
            print("\nExecuted Calls\n", processor.getExecutedCalls().to_string(na_rep='-'))
            print("\nExecuted Puts\n" , processor.getExecutedPuts().to_string(na_rep='-'))
            
            table_name = 'Übersicht  zur realisierten und unrealisierten Performance'
            processor.filterTable(table_name,'Vermögenswertkategorie','Gesamt*',7)
            processor.displayLastExecutionResult()
            print("\n")
            processor.filterTable('Zinsen','Währung','Gesamt*',4)
            processor.displayLastExecutionResult()
            print("\n")
            processor.filterTable('Quellensteuer','Währung','Gesamt*',5)
            processor.displayLastExecutionResult()
            print("\n")
            processor.filterTable('Dividenden','Währung','Gesamt*',5)
            processor.displayLastExecutionResult()

        # Zugriff auf eine spezifische Tabelle
        if args.table:
            table_name = args.table
            table = processor.get_table(table_name)
            if table is not None:
                if args.columns:
                    col_range = args.columns.split('-')
                    start_col = int(col_range[0])
                    end_col = int(col_range[1]) + 1
                    table = table.iloc[:, start_col:end_col]
                print(f"Tabelle: {table_name}")
                print(table.to_string())
            else:
                print(f"Tabelle '{table_name}' nicht gefunden.")
#--------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    #data = pd.read_csv( "./mytest.csv", delimiter=",", decimal=".", encoding='latin1', header=None, quotechar='"')
    #print (data)