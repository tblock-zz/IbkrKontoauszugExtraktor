'''
Loads the aligned Captrader csv file into memeory and makes pandas dataframes out of it.
All the containing tables can be retrieved with getTables()
'''
import pandas as pd
import numpy as np
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
        tables = self._split_into_tables()
        self.tables = {name: i.loc[:, i.columns.notnull()] for name, i in tables.items()}  
    #-------------------------------------------------------------------------------------------------
    def _split_into_tables(self):
        """Teilt die Daten in separate Tabellen auf, basierend auf den Werten in Spalte A und B."""
        tables = {}
        current_table_name = None
        current_table_data = []
        for index, row in self.data.iterrows():
            table_name = row.iloc[0]
            row_type   = row.iloc[1]
            if pd.notna(table_name) and row_type == 'Header':
                table_name = self.handleHeaderTransaktionen(row,index)
                #print(table_name)
                if current_table_name is not None and current_table_data:
                    # Speichern der vorherigen Tabelle
                    tables[current_table_name] = pd.DataFrame(current_table_data[1:], columns=current_table_data[0])
                    tables[current_table_name][['USDEUR','EkEuro']] =  np.nan
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
    def handleHeaderTransaktionen(self,row,index):
        table_name = row.iloc[0]
        if table_name == "Transaktionen" and row.iloc[3] == 'Vermögenswertkategorie':
            # Überprüfe, ob index + 1 innerhalb des gültigen Bereichs liegt
            if index + 1 < len(self.data):
                table_name += " " + self.data.iloc[index + 1, 3]
        return table_name
    #-------------------------------------------------------------------------------------------------
    def getTables(self):
        return self.tables
    #-------------------------------------------------------------------------------------------------
    def getTable(self, table_name):
        """Gibt die Tabelle mit dem angegebenen Namen oder der Position zurück."""
        if table_name.isdigit():
            index = int(table_name) - 1  # Da Listen bei 0 beginnen, subtrahieren wir 1
            if 0 <= index < len(self.tables):
                table_key = list(self.tables.keys())[index]
                return self.tables[table_key]
            else:
                print(f"Index {index + 1} liegt außerhalb des gültigen Bereichs.")
                return None
        else:
            return self.tables.get(table_name)
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
def saveTransactionsDevisen(name, df):
    df.to_csv(name, index=False)
#--------------------------------------------------------------------------------------------------------------------
def loadTransactionsDevisen(name):
    return pd.read_csv(name)
#--------------------------------------------------------------------------------------------------------------------
def saveRemainingStocks(name, df):
    df.to_csv(name, index=False)
#--------------------------------------------------------------------------------------------------------------------
def loadStockFromYearBefore(name):
    return pd.read_csv(name)