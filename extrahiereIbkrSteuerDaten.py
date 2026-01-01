'''
todos
   move prints to display.py
'''
import pandas as pd
import argparse
import globals

import alignCsv as al
import csvLoader as db
import filter
import display as dp
import exportCsv
import exportOds
from collections import deque
#--------------------------------------------------------------------------------------------------------------------
import language as lg
lng = lg.selected
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
def calculateRemaining(p, c):
    """
    Korrigierte Version: Verbleibende Aktien nach FIFO.
    
    Args:
        p: DataFrame mit gekauften Aktien (Menge > 0)
        c: DataFrame mit verkauften Aktien (Menge < 0)
        
    Returns:
        DataFrame mit verbleibenden Aktien-Beständen
    """
    cols = lng['Aktien']
    cTime, cMenge, cSymbol = cols['time'], cols['menge'], cols['symbol']

    # Sortiere beide DataFrames nach Datum
    p_sorted = p.sort_values([cSymbol, cTime]).copy()
    c_sorted = c.sort_values([cSymbol, cTime]).copy()
    # Konvertiere Verkaufsmenge zu positiv für Berechnung
    c_sorted[cMenge] = abs(c_sorted[cMenge])
    # Erstelle eine Kopie der Käufe für die Verarbeitung
    remaining_buys = []
    for symbol in p_sorted[cSymbol].unique():
        symbol_buys = p_sorted[p_sorted[cSymbol] == symbol].copy()
        symbol_sells = c_sorted[c_sorted[cSymbol] == symbol].copy()
        # FIFO: Verkaufe zuerst die ältesten Aktien
        for _, sell_row in symbol_sells.iterrows():
            sell_quantity = sell_row[cMenge]
            while sell_quantity > 0 and not symbol_buys.empty:
                # Nimm den ältesten Kauf
                oldest_buy = symbol_buys.iloc[0]
                buy_quantity = oldest_buy[cMenge]
                # Verkaufe die verfügbare Menge
                quantity_to_sell = min(sell_quantity, buy_quantity)
                # Reduziere sowohl Kaufs- als auch Verkaufsmenge
                symbol_buys.at[symbol_buys.index[0], cMenge] -= quantity_to_sell
                sell_quantity -= quantity_to_sell
                # Entferne komplett verkaufte Käufe
                if symbol_buys.iloc[0][cMenge] <= 0:
                    symbol_buys = symbol_buys.iloc[1:]
        # Füge verbleibende Käufe zu der Liste hinzu
        for _, remaining_buy in symbol_buys.iterrows():
            remaining_buys.append(remaining_buy.to_dict())
    # Konvertiere zu DataFrame
    if remaining_buys:
        result_df = pd.DataFrame(remaining_buys)
        return result_df.sort_values([cSymbol, cTime])
    else:
        return pd.DataFrame(columns=p.columns)
#--------------------------------------------------------------------------------------------------------------------
def calculateProfit(p: pd.DataFrame, c: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet den Gewinn/Verlust aus Aktienverkäufen nach dem deutschen FIFO-Prinzip.
    
    Args:
        p: DataFrame mit Kaufdaten (Spalten: Datum/Zeit, Symbol, Preis, Menge, Gebühr, USDEUR, EkEuro)
        c: DataFrame mit Verkaufsdaten (Spalten: Datum/Zeit, Symbol, Preis, Menge, Gebühr, USDEUR, EkEuro)
    
    Returns:
        DataFrame mit Verkäufen und berechneten Gewinnen/Verlusten
    """
    cols = lng['Aktien']
    cSymbol, cTime, cPreis, cMenge, cGebuehr = cols['symbol'], cols['time'], cols['preis'], cols['menge'], cols['gebühr']
    cSymbol = cols['symbol'] if 'symbol' in cols else cSymbol # Fallback or add to language.py if needed, currently 'Symbol' is in filters but not as key
    # In language.py for 'Aktien': 'filters': ['Datum/Zeit', 'Symbol', 'Preis', 'Menge', 'Gebühr', 'USDEUR', 'EkEuro']
    # We can map by index if they are stable or better by name strings
    # But user asked to use names from filters
    # filters = ['Datum/Zeit', 'Symbol', 'Preis', 'Menge', 'Gebühr', 'USDEUR', 'EkEuro']
    #             0             1         2        3        4         5         6
    f = cols['filters']
    cUsdEur, cEkEuro = f[5], f[6]

    # Sortiere Käufe nach Datum (FIFO: älteste zuerst)
    purchases = p.sort_values(cTime).copy()
    sales = c.sort_values(cTime).copy()
    # Erstelle FIFO-Queue pro Symbol für Käufe
    fifoQueues = {}
    for _, row in purchases.iterrows():
        symbol = row[cSymbol]
        if symbol not in fifoQueues:
            fifoQueues[symbol] = deque()
        preisProStueck = row[cPreis] * row[cUsdEur]  
        gebuehrProStueck = row[cGebuehr] * row[cUsdEur] / row[cMenge] if row[cMenge] != 0 else 0
        fifoQueues[symbol].append({
            'datum': row[cTime],
            'preisProStueck': preisProStueck,
            'gebuehrProStueck': gebuehrProStueck,
            'menge': row[cMenge]
        })
    # Berechne Gewinn für jeden Verkauf
    results = []
    for _, sale in sales.iterrows():
        symbol = sale[cSymbol]
        verkaufMenge = abs(sale[cMenge])
        verkaufErloesEuro = sale[cPreis] * sale[cUsdEur] * verkaufMenge
        verkaufGebuehr = abs(sale[cGebuehr] * sale[cUsdEur])
        if symbol not in fifoQueues or len(fifoQueues[symbol]) == 0:
            results.append({
                cTime: sale[cTime],
                cSymbol: symbol,
                'Verkauf Menge': verkaufMenge,
                'Verkauf Erlös [€]': verkaufErloesEuro,
                'Anschaffungskosten [€]': 0,
                'Gewinn [€]': verkaufErloesEuro - verkaufGebuehr,
                'Fehler': 'Keine Kaufdaten vorhanden'
            })
            continue
        # FIFO: Verbrauche älteste Käufe zuerst
        verbleibend = verkaufMenge
        anschaffungskosten = 0
        kaufgebuehren = 0
        while verbleibend > 0 and fifoQueues[symbol]:
            kauf = fifoQueues[symbol][0]
            if kauf['menge'] <= verbleibend:
                # Kompletter Kauf wird verbraucht
                anschaffungskosten += kauf['menge'] * kauf['preisProStueck']
                kaufgebuehren += kauf['menge'] * kauf['gebuehrProStueck']
                verbleibend -= kauf['menge']
                fifoQueues[symbol].popleft()
            else:
                # Teilweise Entnahme aus diesem Kauf
                anschaffungskosten += verbleibend * kauf['preisProStueck']
                kaufgebuehren += verbleibend * kauf['gebuehrProStueck']
                kauf['menge'] -= verbleibend
                verbleibend = 0
        # Gewinn = Verkaufserlös - Anschaffungskosten - Kaufgebühren - Verkaufsgebühren
        gewinn = verkaufErloesEuro - anschaffungskosten - kaufgebuehren - verkaufGebuehr
        results.append({
            cTime: sale[cTime],
            cSymbol: symbol,
            'Verkauf Menge': verkaufMenge,
            'Verkauf Erlös [€]': verkaufErloesEuro,
            'Anschaffungskosten [€]': anschaffungskosten,
            'Kaufgebühren [€]': kaufgebuehren,
            'Verkaufsgebühr [€]': verkaufGebuehr,
            'Gewinn [€]': gewinn,
            'Fehler': 'Nicht genug Kaufdaten' if verbleibend > 0 else None
        })
    return pd.DataFrame(results)
#--------------------------------------------------------------------------------------------------------------------
def getExecutedShorts(tables):
    cMenge = lng['Aktien']['menge']
    soldOpts=filter.soldCallsPuts(tables)
    soldOpts[cMenge] = soldOpts[cMenge].astype(float)*100
    sC=filter.getSumOptions(soldOpts)
    dp.showSoldShorts(soldOpts,sC)
    
    boughtOpts=filter.boughtCallsPuts(tables)
    boughtOpts[cMenge] = boughtOpts[cMenge].astype(float)*100
    sP=filter.getSumOptions(boughtOpts)
    dp.showBoughtShorts(boughtOpts,sP)
    
    dp.showLine()
    print(f"Gewinn aus Optionsgeschäften: {sC} + {sP} = {sC + sP}")
    dp.showLine()
    executedShorts = filter.executedOptions(tables)
    p = filter.executedPutsCalls(tables,executedShorts,'filterExePuts')
    c = filter.executedPutsCalls(tables,executedShorts,'filterExeCalls')
    return soldOpts, boughtOpts, executedShorts, p,c
#--------------------------------------------------------------------------------------------------------------------
def showTaxRelevantTables(tables):
    tPerf, namePerf = filter.tablePerformance(tables)
    dp.showPerformance(tPerf, namePerf)
    
    tZinsen, nameZinsen = filter.tableZinsen(tables)
    dp.showZinsen(tZinsen, nameZinsen)
    
    tQuellen, nameQuellen = filter.tableQuellensteuer(tables)
    dp.showQuellensteuer(tQuellen, nameQuellen)
    
    tDiv, nameDiv = filter.tableDividenden(tables)
    dp.showDividenden(tDiv, nameDiv)
    
    tDev, nameDev = filter.tableTransactionsDevisen(tables)
    dp.showTransactionsDevisen(tDev, nameDev)
    
    return {
        "zinsen": tZinsen,
        "quellensteuer": tQuellen,
        "dividenden": tDiv,
        "performance": tPerf
    }
#--------------------------------------------------------------------------------------------------------------------
def showCorrectedCalculation(tables,filename:str, exportFile:str=None):
    stocksStart = filter.tableStocksStart(tables)
    m = None
    try:     
        stocksStart = db.loadStockFromYearBefore(filename)
    except:  
        pass
    print("\n","!"*80,"\n  todo Kein Steuerdokument und vor Benutzung sorgfältig zu prüfen\n","!"*80)
    dp.showStartStocks(stocksStart.sort_values(by='Datum/Zeit')) # todo calculate EkEuro
    stocksBuy  = filter.tableStocksBuy(tables).sort_values(by='Datum/Zeit')
    stocksSold = filter.tableStocksSell(tables).sort_values(by='Datum/Zeit')
    dp.showBoughtStocks(stocksBuy)
    dp.showSoldStocks(stocksSold)
    #------------------------------------------------------
    c = stocksSold
    p = filter.merge(stocksStart, stocksBuy)
    t = calculateProfit(p,c)
    dp.showStocksSellProfit(t)
    r = calculateRemaining(p,c)
    dp.showRemainingStocks(r)
    db.saveRemainingStocks("stocksafter.csv", r)    
    #------------------------------------------------------
    sold, bought, executedShorts,puts,calls = getExecutedShorts(tables)
    if False:
        puts = puts.sort_values(by='Datum/Zeit')
        dp.showExecutedPuts(puts)
        calls = calls.sort_values(by='Datum/Zeit')
        dp.showExecutedCalls(calls)
    #------------------------------------------------------
    #------------------------------------------------------
    if exportFile:
         # Calculate sums for export
         profitStocks = t['Gewinn [€]'].sum()
         sumSoldOpts = filter.getSumOptions(sold)
         sumBoughtOpts = filter.getSumOptions(bought)
         totalOptProfit = sumSoldOpts + sumBoughtOpts

         # Gather tax data again for export (silent capture)
         # We want aggregated values for the Overview
         tZinsen, _ = filter.tableZinsen(tables)
         tQuellen, _ = filter.tableQuellensteuer(tables)
         tDiv, _ = filter.tableDividenden(tables)
         
         # Helper to sum specific columns safely
         def sumCol(df, col):
             if df is not None and col in df.columns:
                 return pd.to_numeric(df[col], errors='coerce').sum()
             return 0.0

         sumZinsen = sumCol(tZinsen, 'Gesamt Zinsen in EUR')
         sumQuellen = sumCol(tQuellen, 'Gesamt Quellensteuer in EUR')
         sumDiv = sumCol(tDiv, 'Gesamtwert in EUR')

         # 1. Steuer Übersicht Sheet
         overviewData = {
             "Zinsen (Gesamt)": sumZinsen,
             "Dividenden (Gesamt)": sumDiv,
             "Quellensteuer (Gesamt)": sumQuellen,
             " ": "", # Spacer
             "Gewinn/Verlust Aktien": profitStocks,
             "Gewinn/Verlust Optionen": totalOptProfit,
             "  ": "",
             "Details:": "Details siehe weitere Arbeitsblätter"
         }
         # We also want the detailed tables for Interest/Div/Tax in the overview or maybe separate?
         # User asked for "Overview with Div, Interest, Tax, StockProfit, OptionProfit". 
         # I will put the summary at top, and then the detailed tables below in the overview sheet.
         
         sheetOverview = [
             "Steuerliche Übersicht",
            overviewData,
             " ",
             "Detaillierte Tabellen:",
             "Dividenden", tDiv,
             "Zinsen", tZinsen,
             "Quellensteuer", tQuellen
         ]

         # 2. Aktien Sheet
         sheetStocks = [
             "Aktien Handel",
             "Startbestand", stocksStart,
             "Käufe", stocksBuy,
             "Verkäufe", stocksSold,
             " ",
             "Gewinn/Verlust Berechnung", t,
             ["Profit Aktien", "", "", "", "", "", "", profitStocks],
             " ",
             "Aktienbestand Ende", r
         ]

         # 3. Optionen Sheet
         sheetOptions = [
             "Optionsgeschäfte",
             "Verkaufte Optionen", sold,
             ["Summe Einnahmen", "", "", "", "", "", "", sumSoldOpts],
             " ",
             "Gekaufte Optionen", bought,
             ["Summe Ausgaben", "", "", "", "", "", "", sumBoughtOpts],
             " ",
             ["Gewinn aus Optionsgeschäften", "", "", "", "", "", "", totalOptProfit],
             " ",
             "Ausgeführte Calls (Aktienabnahme)", calls,
             "Ausgeführte Puts (Aktienzuteilung)", puts
         ]
         
         if exportFile.lower().endswith('.ods'):
             sheets = {
                 "Steuer Übersicht": sheetOverview,
                 "Aktien": sheetStocks,
                 "Optionen": sheetOptions
             }
             exportOds.exportToOds(exportFile, sheets)
         else:
             # Fallback to single sheet/CSV-like dump
             exportData = {
                 "Aktien Steuerjahr Beginn": stocksStart,
                 "Aktien gekauft": stocksBuy,
                 "Aktien verkauft": stocksSold,
                 "Berechnung Käufe - Verkäufe": t,
                 "Profit Aktien": profitStocks,
                 "Aktienbestand Steuerjahr Ende": r,
                 "Verkaufte Optionen": sold,
                 "Summe Einnahmen Optionen": sumSoldOpts,
                 "Gekaufte Optionen": bought,
                 "Summe Ausgaben Optionen": sumBoughtOpts,
                 "Gewinn aus Optionsgeschäften": totalOptProfit,
                 "Ausgeführte Puts (Aktienzuteilung)": puts,
                 "Ausgeführte Calls (Aktienabnahme)": calls
             }
             exportCsv.exportToCsv(exportFile, exportData)
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
    parser.add_argument('--csv', type=str, help='Dateiname für CSV Export der Ergebnisse')
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
    tax_data = {}
    if args.tax:
        tax_data = showTaxRelevantTables(tables)
    if args.new:
        showCorrectedCalculation(tables,args.new, args.csv)

        # Re-gather data for ODS if needed, this part inside showCorrectedCalculation handles the export.
        # However, showCorrectedCalculation is currently handling the export logic.
        # We need to make sure showCorrectedCalculation has access to the 'tax_data' from showTaxRelevantTables if we want to include it in the report.
        # But 'showCorrectedCalculation' is called AFTER 'showTaxRelevantTables'.
        # Actually, let's pass tax_data to showCorrectedCalculation if available, or just re-fetch it inside if needed. 
        # Simpler: Modify showCorrectedCalculation to call showTaxRelevantTables internally or extract data there?
        # Argument 'args.tax' controls if we show it on screen.
        # But for export we definitely want it.
        pass
#--------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__": 
    main()
