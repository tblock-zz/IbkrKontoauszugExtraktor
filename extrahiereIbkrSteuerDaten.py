'''
todos
Call kauf Code:C
put kauf  Code:C
Aktien kauf
Aktien verkauf
umrechnen in euro
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
def subtractExecutedCallsFromPuts(puts_df, calls_df):
    p = puts_df
    # Konvertiere das Datum/Zeit Feld in ein datetime Objekt für einfachere Verarbeitung
    sd = 'Datum/Zeit'
    sp = 'Preis'
    sm = 'Menge'
    st = 'Ticker'
    
    p[sd] = p[sd].str.replace(',', '')
    p[sd] = pd.to_datetime(p[sd])
    calls_df[sd] = pd.to_datetime(calls_df[sd])
    # Konvertiere Preis- und Mengen-Spalten von String zu float bzw. int
    p[sp] = p[sp].astype(float)
    p[sm] = p[sm].astype(int)
    calls_df[sp] = calls_df[sp].astype(float)
    calls_df[sm] = calls_df[sm].astype(float)
    
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
def getExecutedShorts(tables):
    t=filter.soldCallsPuts(tables)
    r=filter.getOptionValues(t)
    dp.showExecutedShorts(t,r)
    t=filter.boughtCallsPuts(tables)
    r=filter.getOptionValues(t)
    dp.showExecutedShorts(t,r)
    executedShorts = filter.executedOptions(tables)
    p = filter.executedPuts(executedShorts)
    c = filter.executedCalls(executedShorts)
    return executedShorts, p,c
#--------------------------------------------------------------------------------------------------------------------
def showTaxRelevantTables(tables):
    dp.showPerformance(*filter.tablePerformance(tables))
    dp.showZinsen(*filter.tableZinsen(tables))
    dp.showQuellensteuer(*filter.tableQuellensteuer(tables))
    dp.showDividenden(*filter.tableDividenden(tables))
#--------------------------------------------------------------------------------------------------------------------
def showCorrectedCalculation(tables):
    stocksStart = filter.tableStocksStart(tables)
    m = None
    try:
        stocksStart = db.loadStockFromYearBefore("stocksbefore.csv")
    except:
        pass

    executedShorts,p,c = getExecutedShorts(tables)
    if globals.debug: dp.showExecutedShorts(executedShorts)
    dp.showStartStocks(stocksStart)
    stocksStart["Menge"] /= 100
    dp.showExecutedPuts(p)
    dp.showExecutedCalls(c)
    p = filter.mergePutsAndStocks(stocksStart,p)
    putsMinusCalls = subtractExecutedCallsFromPuts(p, c)
    dp.showPutsVsCalls(putsMinusCalls)
    filter.tableRemainingExecutedPuts(p)
    p = p[p["Menge"]>0]
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
    parser.add_argument('--new', action='store_true', help='Manual calculation')
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
    filter.setTables(tables)
    if args.list:
        availableTables = list(tables.keys())
        print("Verfügbare Tabellen:", availableTables)
    if args.table:
        dp.showSpecificTable(tables,args.table,args.columns)

    if args.tax:
        showTaxRelevantTables(tables)
    if args.new:
        showCorrectedCalculation(tables)
#--------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__": 
    main()
