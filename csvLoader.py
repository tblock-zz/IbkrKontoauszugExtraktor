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
def saveState(filename, tables_dict):
    """
    Saves multiple DataFrames into a single CSV file with a format compatible with CSVTableProcessor.
    Format: TableName, Header/Data, Col1, Col2, ...
    """
    output_rows = []
    for name, df in tables_dict.items():
        if df is None or df.empty:
            continue
        # Add Header row
        header_row = [name, 'Header'] + df.columns.tolist()
        output_rows.append(header_row)
        # Add Data rows
        for _, row in df.iterrows():
            data_row = [name, 'Data'] + row.tolist()
            output_rows.append(data_row)
    
    pd.DataFrame(output_rows).to_csv(filename, index=False, header=False)

#--------------------------------------------------------------------------------------------------------------------
def loadState(filename):
    """
    Loads one or more tables from a CSV file. 
    Supports both the dual-column prefix format and legacy single-table CSVs.
    """
    try:
        # First try to read with the multi-table processor format
        # We can use the existing CSVTableProcessor logic or a simplified version
        data = pd.read_csv(filename, header=None, quotechar='"')
        
        # Check if it looks like our multi-table format (Column 1 contains 'Header' or 'Data')
        if data.shape[1] >= 2 and data.iloc[:, 1].isin(['Header', 'Data']).any():
            tables = {}
            current_name = None
            current_data = []
            for _, row in data.iterrows():
                table_name = row.iloc[0]
                row_type = row.iloc[1]
                if row_type == 'Header':
                    if current_name and current_data:
                        tables[current_name] = pd.DataFrame(current_data[1:], columns=current_data[0])
                    current_name = table_name
                    # Get all columns from index 2 onwards, but only up to the last non-NaN entry
                    header_slice = row[2:]
                    last_valid_idx = header_slice.last_valid_index()
                    if last_valid_idx is not None:
                        header_cols = header_slice.loc[:last_valid_idx].tolist()
                    else:
                        header_cols = []
                    current_data = [header_cols]
                elif row_type == 'Data':
                    # Use the length of the header to slice the data
                    current_data.append(row[2:2+len(current_data[0])].tolist())
            
            if current_name and current_data:
                df = pd.DataFrame(current_data[1:], columns=current_data[0])
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except:
                        pass
                tables[current_name] = df
            return tables
        else:
            # Fallback for legacy single-table CSV (e.g. from stocksafter.csv)
            # We assume it's 'Aktien Beginn' if it's the old format
            df = pd.read_csv(filename)
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    pass
            return {"Aktien Beginn": df}
    except Exception as e:
        print(f"Warnung: State-Datei konnte nicht geladen werden ({e})")
        return {}

#--------------------------------------------------------------------------------------------------------------------
def saveRemainingStocks(name, df):
    saveState(name, {"Aktien Ende": df})

#--------------------------------------------------------------------------------------------------------------------
def loadStockFromYearBefore(name):
    tables = loadState(name)
    return tables.get("Aktien Ende", tables.get("Aktien Beginn", pd.DataFrame()))