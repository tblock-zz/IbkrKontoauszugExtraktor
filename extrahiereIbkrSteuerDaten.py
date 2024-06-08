import pandas as pd
import argparse

# wahrungsrecher.org/historisch/us-dollar/europa/april-2023
class CSVTableProcessor:
    def __init__(self, file_path, delimiter=';', decimal=',', encoding='latin1'):
        self.file_path = file_path
        self.data = pd.read_csv(file_path, delimiter=delimiter, decimal=decimal, encoding=encoding, header=None)
        self.data = self.data.applymap (lambda x: str(x).replace(',', '.') if isinstance(x, str) else x)
        self.tables = self._split_into_tables()

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

    def get_table(self, table_name):
        """Gibt die Tabelle mit dem angegebenen Namen zurück."""
        return self.tables.get(table_name)

    def display_tables(self):
        """Zeigt alle Tabellen an."""
        for name, table in self.tables.items():
            print(f"Table: {name}")
            print(table)
            print("\n")

def displayTable(processor,table_name, headerColumnName, search, range=7):
    table = processor.get_table(table_name)
    if table is not None:
        filtered_table = table[table[headerColumnName].str.contains(search, na=False)]
        filtered_table = filtered_table.iloc[:, 0:range]
        print(f"Table: {table_name}")
        print(filtered_table.to_string(na_rep='-'))  # Gibt die gefilterte Tabelle aus, ohne Kürzungen

def main():
    parser = argparse.ArgumentParser(description='Process a CSV file and split it into separate tables.')
    parser.add_argument('file_path', type=str, help='Path to the CSV file')
    parser.add_argument('--delimiter', type=str, default=';', help='Delimiter used in the CSV file')
    parser.add_argument('--decimal', type=str, default=',', help='Decimal point character used in the CSV file')
    parser.add_argument('--encoding', type=str, default='latin1', help='Encoding of the CSV file')
    parser.add_argument('--table', type=str, help='Name of the table to display')
    parser.add_argument('--columns', type=str, help='Range of columns to display (e.g., "0-5")')
    parser.add_argument('--tax', action='store_true', help='Tax output')
    parser.add_argument('--list', action='store_true', help='List of available tables')

    args = parser.parse_args()

    processor = CSVTableProcessor(args.file_path, delimiter=args.delimiter, decimal=args.decimal, encoding=args.encoding)
    
    # Überprüfen der verfügbaren Tabellen
    available_tables = list(processor.tables.keys())
    if args.list:
        print("Verfügbare Tabellen:", available_tables)
    
    #processor.display_tables()

    if args.tax:
        table_name = 'Übersicht  zur realisierten und unrealisierten Performance'
        displayTable(processor,table_name,'Vermögenswertkategorie','Gesamt*')
        print()
        displayTable(processor,'Zinsen','Währung','Gesamt*',4)
        print()
        displayTable(processor,'Quellensteuer','Währung','Gesamt*',5)
        print()
        displayTable(processor,'Dividenden','Währung','Gesamt*',5)

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

if __name__ == "__main__":
    main()
