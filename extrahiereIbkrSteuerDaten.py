'''
todos
 move check_quantity,calculate_profit_loss and update_stock_quantities
   to filter.py
   move prints to display.py
'''
import pandas as pd
import argparse
import globals

import alignCsv as al
import csvLoader as db
import filter
import display as dp

import language as lg
lng = lg.selected

#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
def check_quantity(a, b):
    a_aggregated = a.groupby('Symbol')['Menge'].sum().reset_index()
    b_aggregated = b.groupby('Symbol')['Menge'].sum().reset_index()   
    merged = pd.merge(a_aggregated, b_aggregated, on='Symbol', how='left', suffixes=('_a', '_b'))    
    merged['Menge_b'] = merged['Menge_b'].fillna(0)    
    merged['invalid'] = merged['Menge_a'] < merged['Menge_b']
    invalids = merged[merged['invalid']]
    count = merged['invalid'].sum()
    if(count>0):
        print("\n!!! Fehler Anzahl der verkauften Aktien höher als der Bestand für")
        print(invalids['Symbol'].to_string())
        print("\n Bestand:\n",a.to_string())
        print("\n Verkauf:\n",b.to_string())
        exit()        
    return count, invalids
#--------------------------------------------------------------------------------------------------------------------
def fifo_merge(a, b):
    # !!!! todo use language strings
    ltr = lng['Transaktionen']
    strTime   = ltr['time']
    strMenge = ltr['menge']
    strSymbol = ltr['symbol']
    strEkEuro = 'EkEuro'

    a = a.sort_values(by=strTime)
    b = b.sort_values(by=strTime)
    
    merged_list = []

    for symbol in a[strSymbol].unique():
        a_symbol = a[a[strSymbol] == symbol].copy()
        b_symbol = b[b[strSymbol] == symbol].copy()
        
        while not a_symbol.empty and not b_symbol.empty:
            a_row = a_symbol.iloc[0]
            b_row = b_symbol.iloc[0]
            
            menge_kauf = a_row[strMenge]
            menge_verkauf = b_row[strMenge]
            
            menge = min(menge_kauf, menge_verkauf)
            
            ek_euro_kauf = a_row['EkEuro'] 
            ek_euro_verkauf = b_row['EkEuro'] * (menge)
            
            merged_list.append({
                f'{strTime}_Kauf': a_row[strTime],
                #'Datum/Zeit_Kauf': a_row[strTime],
                f'{strSymbol}' : symbol,
                f'{strMenge}_Kauf': menge,
                f'{strEkEuro}_Kauf': ek_euro_kauf,
                f'{strTime}_Verkauf': b_row[strTime],
                f'{strMenge}_Verkauf': menge,
                f'{strEkEuro}_Verkauf': ek_euro_verkauf,
                'Preis_Differenz': ek_euro_verkauf + ek_euro_kauf
            })
            
            a_symbol.at[a_symbol.index[0], 'Menge'] -= menge
            b_symbol.at[b_symbol.index[0], 'Menge'] -= menge
            
            if a_symbol.iloc[0]['Menge'] == 0:
                a_symbol = a_symbol.iloc[1:]
            if b_symbol.iloc[0]['Menge'] == 0:
                b_symbol = b_symbol.iloc[1:]
        
        # Add remaining rows in a_symbol to merged_list
        for _, row in a_symbol.iterrows():
            merged_list.append({
                f'{strTime}_Kauf': row[strTime],
                f'{strSymbol}' : symbol,
                f'{strMenge}_Kauf': row['Menge'],
                f'{strEkEuro}_Kauf': row['EkEuro'],
                f'{strTime}_Verkauf': None,
                f'{strMenge}_Verkauf': None,
                f'{strEkEuro}_Verkauf': None,
                'Preis_Differenz': None
            })
    
    merged_df = pd.DataFrame(merged_list)
    return merged_df
#--------------------------------------------------------------------------------------------------------------------
def calculate_profit_loss(a, b):
    a = a.sort_values(by='Datum/Zeit')
    b = b.sort_values(by='Datum/Zeit')
    if globals.debug:
      print("#" * 80)
      print(a.to_string())
      print(b.to_string())

    colsRemove = ['Bis','Gebühr','USDEUR','Preis']
    a = a.drop(columns=colsRemove, errors='ignore')
    b = b.drop(columns=colsRemove, errors='ignore')
    if globals.debug:
      print("#" * 80)
      print(a.to_string())
      print(b.to_string())

    check_quantity(a,b)
    # Berechne den Kaufpreis pro Aktie
    b['EkEuro'] = b['EkEuro'] / b['Menge']
    merged = fifo_merge(a,b)

    #merged = pd.merge(a, b, on=['Symbol'], suffixes=('_Kauf', '_Verkauf'))
    if globals.debug:
      print("#" * 80)
      print(merged.to_string())
      print("#" * 80)
    return merged
#--------------------------------------------------------------------------------------------------------------------
def update_stock_quantities(a, b):
    # Aggregiere die Mengen der Verkäufe nach Symbol
    b_aggregated = b.groupby('Symbol')['Menge_Verkauf'].sum().reset_index()    
    # Mergen der Bestands- und Verkaufsdaten basierend auf Symbol
    merged = pd.merge(a, b_aggregated, on='Symbol', how='left')    
    # Ersetze NaN in Menge_Verkauf mit 0 (falls ein Symbol in a, aber nicht in b existiert)
    merged['Menge_Verkauf'] = merged['Menge_Verkauf'].fillna(0)    
    # Subtrahiere die verkauften Mengen von den Bestandsmengen
    merged['Menge'] = merged['Menge'] - merged['Menge_Verkauf']
    # Entferne die Spalte Menge_Verkauf und andere zusätzliche Spalten, die nicht in a vorhanden sind
    merged = merged[a.columns]
    return merged
#--------------------------------------------------------------------------------------------------------------------
def getExecutedShorts(tables):
    t=filter.soldCallsPuts(tables)
    s=filter.getSumOptions(t)
    dp.showSoldShorts(t,s)
    t=filter.boughtCallsPuts(tables)
    s=filter.getSumOptions(t)
    dp.showBoughtShorts(t,s)
    executedShorts = filter.executedOptions(tables)
    p = filter.executedPutsCalls(tables,executedShorts,'filterExePuts')
    c = filter.executedPutsCalls(tables,executedShorts,'filterExeCalls')
    return executedShorts, p,c
#--------------------------------------------------------------------------------------------------------------------
def showTaxRelevantTables(tables):
    dp.showPerformance(*filter.tablePerformance(tables))
    dp.showZinsen(*filter.tableZinsen(tables))
    dp.showQuellensteuer(*filter.tableQuellensteuer(tables))
    dp.showDividenden(*filter.tableDividenden(tables))
#--------------------------------------------------------------------------------------------------------------------
def showCorrectedCalculation(tables,filename:str):
    stocksStart = filter.tableStocksStart(tables)

    m = None
    try:     
        stocksStart = db.loadStockFromYearBefore(filename)
    except:  pass

    print("\n","!"*80,"\n  todo Kein Steuerdokument und vor Benutzung sorgfältig zu prüfen\n","!"*80)
    executedShorts,p,c = getExecutedShorts(tables)
    if globals.debug: dp.showExecutedShorts(executedShorts)
    dp.showStartStocks(stocksStart.sort_values(by='Datum/Zeit')) # todo calculate EkEuro
    stocksBuy = filter.tableStocksBuy(tables).sort_values(by='Datum/Zeit')
    dp.showBoughtStocks(stocksBuy)
    stocksBuy  ["Menge"] /= 100
    stocksStart["Menge"] /= 100
    p = p.sort_values(by='Datum/Zeit')
    dp.showExecutedPuts(p)
    stocksSold = filter.tableStocksSell(tables).sort_values(by='Datum/Zeit')
    p = filter.merge(stocksStart,p)
    p = filter.merge(stocksBuy,p)
    if globals.debug:
        print("\nAktien gesamt:\n", p.to_string())

    c = c.sort_values(by='Datum/Zeit')
    dp.showExecutedCalls(c)
    dp.showSoldStocks(stocksSold)
    stocksSold ["Menge"] /= -100
    c = c.drop(columns=["Bis"], errors='ignore')
    c = filter.merge(stocksSold,c)
    if globals.debug:
        print("\nAktien verkauft gesamt:\n", c.to_string())

    t = calculate_profit_loss(p,c)
    dp.showStocksSellProfit(t)
    p=update_stock_quantities(p,t)
    p = filter.tableRemainingExecutedPuts(p,t)
    p = p[p["Menge"]>0]
    p["Menge"] *= 100
    #y = y.iloc[:, :-1]
    dp.showRemainingStocks(p)
    #print(p)
    db.saveRemainingStocks("stocksafter.csv", p)    
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
    parser.add_argument('--new', type=str, help='Manual calculation')
    parser.add_argument('--list', action='store_true', help='Ausgabe verfügbarer Tabellen')
    parser.add_argument('--align', type=str, help='Align csv separators')
    #return parser.parse_args([r'C:\Users\TomHome\IONOS HiDrive\users\tblock\Tom\prg\python\IbkrKontoauszugExtraktor\converted', '--tax'])
    return parser.parse_args()
#--------------------------------------------------------------------------------------------------------------------
def main():
    args = parseArguments()
    filename = args.file_path

    if args.encoding != "UTF-8-SIG":    
        args.encoding = al.getEncoding(filename)
    if args.align:
        al.alignSeparators(args.file_path, args.align, args.encoding)
        filename = args.align

    tables = db.CSVTableProcessor(filename, delimiter=args.delimiter, decimal=args.decimal, encoding=args.encoding).getTables()
    #filter.setTables(tables)
    if args.list:
        availableTables = list(tables.keys())
        print("Verfügbare Tabellen:")
        for idx, table in enumerate(availableTables, start=1): print(f"  {idx}: '{table}'")
    if args.table:
        dp.showSpecificTable(tables,args.table,args.columns)

    if args.tax:
        showTaxRelevantTables(tables)
    if args.new:
        showCorrectedCalculation(tables,args.new)
#--------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__": 
    main()
