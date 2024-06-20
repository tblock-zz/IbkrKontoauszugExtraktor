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
def calculate_profit_loss(a, b):
    if globals.debug:
      print(a.to_string())
      print(b.to_string())

    colsRemove = ['Bis','Gebühr','EURUSD','Preis']
    a = a.drop(columns=colsRemove, errors='ignore')
    b = b.drop(columns=colsRemove, errors='ignore')

    check_quantity(a,b)
    merged = pd.merge(a, b, on=['Symbol'], suffixes=('_Kauf', '_Verkauf'))
    merged['Preis_Differenz'] = merged['EkEuro_Verkauf'] + merged['EkEuro_Kauf']
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
    dp.showStartStocks(stocksStart) # todo calculate EkEuro
    stocksBuy = filter.tableStocksBuy(tables)
    dp.showBoughtStocks(stocksBuy)
    stocksBuy  ["Menge"] /= 100
    stocksStart["Menge"] /= 100
    dp.showExecutedPuts(p)
    stocksSold = filter.tableStocksSell(tables)
    p = filter.merge(stocksStart,p)
    p = filter.merge(stocksBuy,p)
    if globals.debug:
        print("\nAktien gesamt:\n", p.to_string())

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
    filter.tableRemainingExecutedPuts(p)
    #p = p[p["Menge"]>0]
    p["Menge"] *= 100
    dp.showRemainingStocks(p)
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
        for table in availableTables: print(f"  '{table}'")
    if args.table:
        dp.showSpecificTable(tables,args.table,args.columns)

    if args.tax:
        showTaxRelevantTables(tables)
    if args.new:
        showCorrectedCalculation(tables,args.new)
#--------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__": 
    main()
