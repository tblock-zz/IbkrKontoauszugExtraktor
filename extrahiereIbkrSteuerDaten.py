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
    # Sortiere beide DataFrames nach Datum
    p_sorted = p.sort_values(['Symbol', 'Datum/Zeit']).copy()
    c_sorted = c.sort_values(['Symbol', 'Datum/Zeit']).copy()
    # Konvertiere Verkaufsmenge zu positiv für Berechnung
    c_sorted['Menge'] = abs(c_sorted['Menge'])
    # Erstelle eine Kopie der Käufe für die Verarbeitung
    remaining_buys = []
    for symbol in p_sorted['Symbol'].unique():
        symbol_buys = p_sorted[p_sorted['Symbol'] == symbol].copy()
        symbol_sells = c_sorted[c_sorted['Symbol'] == symbol].copy()
        # FIFO: Verkaufe zuerst die ältesten Aktien
        for _, sell_row in symbol_sells.iterrows():
            sell_quantity = sell_row['Menge']
            while sell_quantity > 0 and not symbol_buys.empty:
                # Nimm den ältesten Kauf
                oldest_buy = symbol_buys.iloc[0]
                buy_quantity = oldest_buy['Menge']
                # Verkaufe die verfügbare Menge
                quantity_to_sell = min(sell_quantity, buy_quantity)
                # Reduziere sowohl Kaufs- als auch Verkaufsmenge
                symbol_buys.at[symbol_buys.index[0], 'Menge'] -= quantity_to_sell
                sell_quantity -= quantity_to_sell
                # Entferne komplett verkaufte Käufe
                if symbol_buys.iloc[0]['Menge'] <= 0:
                    symbol_buys = symbol_buys.iloc[1:]
        # Füge verbleibende Käufe zu der Liste hinzu
        for _, remaining_buy in symbol_buys.iterrows():
            remaining_buys.append(remaining_buy.to_dict())
    # Konvertiere zu DataFrame
    if remaining_buys:
        result_df = pd.DataFrame(remaining_buys)
        return result_df.sort_values(['Symbol', 'Datum/Zeit'])
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
    # Sortiere Käufe nach Datum (FIFO: älteste zuerst)
    purchases = p.sort_values('Datum/Zeit').copy()
    sales = c.sort_values('Datum/Zeit').copy()
    # Erstelle FIFO-Queue pro Symbol für Käufe
    fifoQueues = {}
    for _, row in purchases.iterrows():
        symbol = row['Symbol']
        if symbol not in fifoQueues:
            fifoQueues[symbol] = deque()
        preisProStueck = row['Preis'] * row['USDEUR']  
        gebuehrProStueck = row['Gebühr'] * row['USDEUR'] / row['Menge'] if row['Menge'] != 0 else 0
        fifoQueues[symbol].append({
            'datum': row['Datum/Zeit'],
            'preisProStueck': preisProStueck,
            'gebuehrProStueck': gebuehrProStueck,
            'menge': row['Menge']
        })
    # Berechne Gewinn für jeden Verkauf
    results = []
    for _, sale in sales.iterrows():
        symbol = sale['Symbol']
        verkaufMenge = abs(sale['Menge'])
        verkaufErloesEuro = sale['Preis'] * sale['USDEUR'] * verkaufMenge
        verkaufGebuehr = abs(sale['Gebühr'] * sale['USDEUR'])
        if symbol not in fifoQueues or len(fifoQueues[symbol]) == 0:
            results.append({
                'Datum/Zeit': sale['Datum/Zeit'],
                'Symbol': symbol,
                'verkaufMenge': verkaufMenge,
                'Verkauf_Erlös_Euro': verkaufErloesEuro,
                'Anschaffungskosten_Euro': 0,
                'Gewinn_Euro': verkaufErloesEuro - verkaufGebuehr,
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
            'Datum/Zeit': sale['Datum/Zeit'],
            'Symbol': symbol,
            'verkaufMenge': verkaufMenge,
            'Verkauf_Erlös_Euro': verkaufErloesEuro,
            'Anschaffungskosten_Euro': anschaffungskosten,
            'Kaufgebühren_Euro': kaufgebuehren,
            'Verkaufsgebühr_Euro': verkaufGebuehr,
            'Gewinn_Euro': gewinn,
            'Fehler': 'Nicht genug Kaufdaten' if verbleibend > 0 else None
        })
    return pd.DataFrame(results)
#--------------------------------------------------------------------------------------------------------------------
def getExecutedShorts(tables):
    t=filter.soldCallsPuts(tables)
    t['Menge'] = t['Menge'].astype(float)*100
    sC=filter.getSumOptions(t)
    dp.showSoldShorts(t,sC)
    t=filter.boughtCallsPuts(tables)
    t['Menge'] = t['Menge'].astype(float)*100
    sP=filter.getSumOptions(t)
    dp.showBoughtShorts(t,sP)
    dp.showLine()
    print(f"Gewinn aus Optionsgeschäften: {sC} + {sP} = {sC + sP}")
    dp.showLine()
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
    executedShorts,puts,calls = getExecutedShorts(tables)
    if False:
        puts = puts.sort_values(by='Datum/Zeit')
        dp.showExecutedPuts(puts)
        calls = calls.sort_values(by='Datum/Zeit')
        dp.showExecutedCalls(calls)
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
