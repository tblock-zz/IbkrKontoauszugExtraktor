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
from collections import deque

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
    fifo_queues = {}
    for _, row in purchases.iterrows():
        symbol = row['Symbol']
        if symbol not in fifo_queues:
            fifo_queues[symbol] = deque()
        preis_pro_stueck = row['Preis'] * row['USDEUR']  
        gebuehr_pro_stueck = row['Gebühr'] * row['USDEUR'] / row['Menge'] if row['Menge'] != 0 else 0
        fifo_queues[symbol].append({
            'datum': row['Datum/Zeit'],
            'preis_pro_stueck': preis_pro_stueck,
            'gebuehr_pro_stueck': gebuehr_pro_stueck,
            'menge': row['Menge']
        })
    # Berechne Gewinn für jeden Verkauf
    results = []
    for _, sale in sales.iterrows():
        symbol = sale['Symbol']
        verkauf_menge = abs(sale['Menge'])
        verkauf_erloes_euro = sale['Preis'] * sale['USDEUR'] * verkauf_menge
        verkauf_gebuehr = abs(sale['Gebühr'] * sale['USDEUR'])
        if symbol not in fifo_queues or len(fifo_queues[symbol]) == 0:
            results.append({
                'Datum/Zeit': sale['Datum/Zeit'],
                'Symbol': symbol,
                'Verkauf_Menge': verkauf_menge,
                'Verkauf_Erlös_Euro': verkauf_erloes_euro,
                'Anschaffungskosten_Euro': 0,
                'Gewinn_Euro': verkauf_erloes_euro - verkauf_gebuehr,
                'Fehler': 'Keine Kaufdaten vorhanden'
            })
            continue
        # FIFO: Verbrauche älteste Käufe zuerst
        verbleibend = verkauf_menge
        anschaffungskosten = 0
        kaufgebuehren = 0
        while verbleibend > 0 and fifo_queues[symbol]:
            kauf = fifo_queues[symbol][0]
            if kauf['menge'] <= verbleibend:
                # Kompletter Kauf wird verbraucht
                anschaffungskosten += kauf['menge'] * kauf['preis_pro_stueck']
                kaufgebuehren += kauf['menge'] * kauf['gebuehr_pro_stueck']
                verbleibend -= kauf['menge']
                fifo_queues[symbol].popleft()
            else:
                # Teilweise Entnahme aus diesem Kauf
                anschaffungskosten += verbleibend * kauf['preis_pro_stueck']
                kaufgebuehren += verbleibend * kauf['gebuehr_pro_stueck']
                kauf['menge'] -= verbleibend
                verbleibend = 0
        # Gewinn = Verkaufserlös - Anschaffungskosten - Kaufgebühren - Verkaufsgebühren
        gewinn = verkauf_erloes_euro - anschaffungskosten - kaufgebuehren - verkauf_gebuehr
        results.append({
            'Datum/Zeit': sale['Datum/Zeit'],
            'Symbol': symbol,
            'Verkauf_Menge': verkauf_menge,
            'Verkauf_Erlös_Euro': verkauf_erloes_euro,
            'Anschaffungskosten_Euro': anschaffungskosten,
            'Kaufgebühren_Euro': kaufgebuehren,
            'Verkaufsgebühr_Euro': verkauf_gebuehr,
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

    c = stocksSold
    p = filter.merge(stocksStart, stocksBuy)
    t = calculateProfit(p,c)
    dp.showStocksSellProfit(t)
    r = calculateRemaining(p,c)
    dp.showRemainingStocks(r)
    db.saveRemainingStocks("stocksafter.csv", r)    

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
