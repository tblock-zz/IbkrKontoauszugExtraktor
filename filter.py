'''
Filters the tables for specific information and returns the filterend table.
'''
import pandas as pd

global tables

def setTables(_tables):
    global tables
    tables = _tables
#--------------------------------------------------------------------------------------------------------------------
def mergePutsAndStocks(frm,to):
    return pd.concat([to.copy(), frm], ignore_index=True)    
#--------------------------------------------------------------------------------------------------------------------
def getRowsOfColumnsContainingStr(table, col:str, str:str):
        return table[table[col].str.contains(str, na=False)]
#--------------------------------------------------------------------------------------------------------------------
def fTable(table, headerColumnName, search, range):
    result = None
    #table = tables.get(table_name)
    if table is not None:
        filtered_table = getRowsOfColumnsContainingStr(table,headerColumnName,search)
        #filtered_table = table[table[headerColumnName].str.contains(search, na=False)]
        filtered_table = filtered_table.iloc[:, 0:range]
        result = filtered_table
    return result
#--------------------------------------------------------------------------------------------------------------------
def delCols(table,cols):
    for col in cols:
        del table[col]
    return table    
#--------------------------------------------------------------------------------------------------------------------
def tableZinsen(tables):
    name = 'Zinsen'
    r = fTable(tables.get(name),'Währung','Gesamt*',4)
    delCols(r, ['Datum', 'Beschreibung'])
    return r, name
#--------------------------------------------------------------------------------------------------------------------
def tableDividenden(tables):
    name = 'Dividenden'
    r = fTable(tables.get(name),'Währung','Gesamt*',5)
    delCols(r, ['Datum', 'Beschreibung', 'Code'])
    return r, name
#--------------------------------------------------------------------------------------------------------------------
def tableQuellensteuer(tables):
    name = 'Quellensteuer'
    r = fTable(tables.get(name),'Währung','Gesamt*',5)
    delCols(r, ['Datum', 'Beschreibung', 'Code'])
    return r, name
#--------------------------------------------------------------------------------------------------------------------
def tableStocksStart(tables): 
    t = tables.get('Mark-to-Market-Performance-Überblick')
    t = getRowsOfColumnsContainingStr(t, "Vermögenswertkategorie", "Aktien")
    colCount = "Menge"
    t = t.rename(columns={'Vorher Menge': colCount})
    t = t[["Symbol",colCount]]
    t[colCount] = t[colCount].astype(int)
    t = t[t[colCount] > 0]
    t.rename(columns={'Vorher Menge': colCount}, inplace=True)
    t.rename(columns={'Symbol': 'Ticker'}, inplace=True)
    return t
#--------------------------------------------------------------------------------------------------------------------
def tableRemainingExecutedPuts(p):    
    p.drop('Bis', axis=1, inplace=True)
    return p
#--------------------------------------------------------------------------------------------------------------------
def tablePerformance(tables):    
    table_name = 'Übersicht  zur realisierten und unrealisierten Performance'
    subCol     = 'Vermögenswertkategorie'
    t = fTable(tables.get(table_name),subCol,'Gesamt',7)
    delCols(t, ['Symbol', 'Kostenanp.'])
    t = t[t[subCol] != 'Gesamt (Alle Vermögenswerte)']
    # rename
    c = t[subCol]
    for i, item in enumerate(['Gesamt Aktien','Gesamt Optionen','Gesamt Devisen']):
        c.iat[i] = item
    return t,table_name
#--------------------------------------------------------------------------------------------------------------------
def transactionsOptions(tables):
    return tables.get('Transaktionen Aktien- und Indexoptionen')
#--------------------------------------------------------------------------------------------------------------------
def soldOptions(tables):
    t = transactionsOptions(tables)
    t = getRowsOfColumnsContainingStr(transactionsOptions(tables), "Code", "O")
    return t
#--------------------------------------------------------------------------------------------------------------------
def soldCallsPuts(tables):
    t = soldOptions(tables)
    df = getRowsOfColumnsContainingStr(soldOptions(tables), "Symbol", ".*?[CP]$")
    return df[['Symbol', 'Datum/Zeit', 'Menge', 'Erlös', 'Prov./Gebühr', 'Code']]
#--------------------------------------------------------------------------------------------------------------------
def soldOptionsValues(tableSoldCallsPuts):
    cols1 = ["Erlös","Prov./Gebühr"]
    for i in cols1:
        tableSoldCallsPuts[i] = pd.to_numeric(tableSoldCallsPuts[i])
    return tableSoldCallsPuts[cols1].sum()
#--------------------------------------------------------------------------------------------------------------------
def splitSymbolExecutedShorts(table):
    split_columns = table['Symbol'].str.split(' ', expand=True)
    split_columns.columns = ['Ticker', 'Bis', 'Preis', 'Typ']
    table = table.drop(columns=['Symbol']).join(split_columns)
    table = table.drop_duplicates(keep=False)
    return table[["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge']]   
#--------------------------------------------------------------------------------------------------------------------
def executedOptions(tables):    
    return getRowsOfColumnsContainingStr(transactionsOptions(tables), "Code", "A.*")
#--------------------------------------------------------------------------------------------------------------------
def executedCalls(executedOptionsTable):
    calls = getRowsOfColumnsContainingStr(executedOptionsTable, "Symbol", ".*?C$")
    calls = splitSymbolExecutedShorts(calls)
    return calls[["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge',]]   
#--------------------------------------------------------------------------------------------------------------------
def executedPuts(executedOptionsTable):
    puts = getRowsOfColumnsContainingStr(executedOptionsTable, "Symbol", ".*?P$")
    puts = splitSymbolExecutedShorts(puts)
    return puts[["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge',]]   
#--------------------------------------------------------------------------------------------------------------------
