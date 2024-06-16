'''
Filters the tables for specific information and returns the filterend table.
'''
import pandas as pd
import language as lg

global tables
global sp

lng = lg.selected
#--------------------------------------------------------------------------------------------------------------------
def setTables(_tables):
    global tables
    tables = _tables
#--------------------------------------------------------------------------------------------------------------------
def merge(frm,to):
    return pd.concat([to.copy(), frm], ignore_index=True)    
#--------------------------------------------------------------------------------------------------------------------
def getRowsOfColumnsContainingStr(table, colName:str, pattern:str):
        return table[table[colName].str.contains(pattern, na=False)]
#--------------------------------------------------------------------------------------------------------------------
def delCols(table,cols):
    for col in cols:
        del table[col]
    return table    
#--------------------------------------------------------------------------------------------------------------------
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
def handleTable(tables, accessName, colsToShow):
    acc     = lng[accessName]
    name, u = acc['name'], acc['usedCols']
    r       = fTable(tables.get(name),u[0],u[1],colsToShow)
    delCols(r,acc['delCols'])
    return r, name
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
def tableZinsen(tables):
    return handleTable(tables, 'Zinsen', 4)
#--------------------------------------------------------------------------------------------------------------------
def tableDividenden(tables):
    return handleTable(tables, 'Dividenden', 5)
#--------------------------------------------------------------------------------------------------------------------
def tableQuellensteuer(tables):
    return handleTable(tables, 'Quellensteuer', 5)
#--------------------------------------------------------------------------------------------------------------------
def tableStocksStart(tables): 
    acc     = lng['Performance']
    name, f, r = acc['name'], acc['filters'], acc['renames']

    t = getRowsOfColumnsContainingStr(tables.get(name), f[0], f[1]).copy()
    t.rename(columns={r[0]: r[1]}, inplace=True)
    t.rename(columns={r[2]: r[3]}, inplace=True)
    # filter nach ticker und menge
    t = t[[r[3],r[1]]]
    # wandle mengen string nach zahl
    t[r[1]] = t[r[1]].astype(int)
    # filtere 0 mengen raus
    t = t[t[r[1]] > 0]
    return t
#--------------------------------------------------------------------------------------------------------------------
def tableStocksBuy(tables):
    acc = lng['Aktien']
    t = tables.get(acc['name'])
    f = acc['filterBuy']
    t = getRowsOfColumnsContainingStr(t, f[0], f[1]).copy()
    t = t[acc['filters']]
    r = acc['renames']
    for i in range(0,len(r),2):
        t.rename(columns={r[i]: r[i+1]}, inplace=True)
    r = acc['toNumber']
    for i in range(len(r)):        
        t[r[i]] = t[r[i]].astype(float)
    return t
#--------------------------------------------------------------------------------------------------------------------
def tableStocksSell(tables):
    acc = lng['Aktien']
    t = tables.get(acc['name'])
    f = acc['filterSold']
    t = getRowsOfColumnsContainingStr(t, f[0], f[1]).copy()
    t = t[acc['filters']]
    r = acc['renames']
    for i in range(0,len(r),2):
        t.rename(columns={r[i]: r[i+1]}, inplace=True)
    r = acc['toNumber']
    for i in range(len(r)):        
        t[r[i]] = t[r[i]].astype(float)
    return t
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
def tableRemainingExecutedPuts(p):    
    p.drop(lng['Transaktionen']['bis'], axis=1, inplace=True)
    return p
#--------------------------------------------------------------------------------------------------------------------
def tablePerformance(tables):    
    acc   = lng['Realisiert']
    subCol= acc['usedCols'][0]
    rslt = handleTable(tables, 'Realisiert', 7)
    t,name = rslt[0], rslt[1]
    t = t[t[subCol] != acc['filters'][0]].copy()
    # rename
    c = t[subCol]
    for i, item in enumerate(acc['renames']):
        c.iat[i] = item
    return t,name
#--------------------------------------------------------------------------------------------------------------------
def transactionsOptions(tables):
    return tables.get(lng['Transaktionen']['name'])
#--------------------------------------------------------------------------------------------------------------------
def soldOptions(tables):
    t = transactionsOptions(tables)
    acc = lng['Transaktionen']
    f = acc['filterSoldOptions']
    t = getRowsOfColumnsContainingStr(t, f[0], f[1]).copy()
    cols = lng['Transaktionen']['filters2']
    for i in cols:
        t[i] = pd.to_numeric(t[i])
    e = acc['erlös']
    t[e] = t[e].astype(float)
    return t[t[e] > 0]
#--------------------------------------------------------------------------------------------------------------------
def boughtOptions(tables):
    t = transactionsOptions(tables)
    acc = lng['Transaktionen']
    f = acc['filterSoldOptions']
    t = getRowsOfColumnsContainingStr(t, f[0], f[1]).copy()
    cols = lng['Transaktionen']['filters2']
    for i in cols:
        t[i] = pd.to_numeric(t[i])
    e = acc['erlös']
    t[e] = t[e].astype(float)
    return t[t[e] < 0]
#--------------------------------------------------------------------------------------------------------------------
def soldCallsPuts(tables):
    t = soldOptions(tables)
    acc = lng['Transaktionen']
    f = acc['filterCallsPuts']
    df = getRowsOfColumnsContainingStr(t, f[0], f[1])
    return df[acc['filters']]
#--------------------------------------------------------------------------------------------------------------------
def boughtCallsPuts(tables):
    t = boughtOptions(tables)
    acc = lng['Transaktionen']
    f = acc['filterCallsPuts']
    df = getRowsOfColumnsContainingStr(t, f[0], f[1])
    return df[acc['filters']]
#--------------------------------------------------------------------------------------------------------------------
def getOptionValues(tableSoldCallsPuts):
    cols = lng['Transaktionen']['filters2']
    return tableSoldCallsPuts[cols].sum()
#--------------------------------------------------------------------------------------------------------------------
def splitSymbolExecutedShorts(table):
    acc = lng['Transaktionen']
    symbol = acc['symbol']
    split_columns = table[symbol].str.split(' ', expand=True)
    split_columns.columns = acc['splits']
    table = table.drop(columns=[symbol]).join(split_columns)
    table = table.drop_duplicates(keep=False)
    return table[acc['filterExecutedShorts']]   
#--------------------------------------------------------------------------------------------------------------------
def executedOptions(tables):    
    acc = lng['Transaktionen']
    f   = acc['filterExeOptions']
    return getRowsOfColumnsContainingStr(transactionsOptions(tables), f[0], f[1])
#--------------------------------------------------------------------------------------------------------------------
def executedCalls(executedOptionsTable):
    acc = lng['Transaktionen']
    f   = acc['filterExeCalls']    
    calls = getRowsOfColumnsContainingStr(executedOptionsTable, f[0], f[1])
    calls = splitSymbolExecutedShorts(calls)
    return calls[acc['filterExecutedShorts']]
#--------------------------------------------------------------------------------------------------------------------
def executedPuts(executedOptionsTable):
    acc = lng['Transaktionen']
    f   = acc['filterExePuts']    
    puts = getRowsOfColumnsContainingStr(executedOptionsTable,  f[0], f[1])
    puts = splitSymbolExecutedShorts(puts)
    return puts[acc['filterExecutedShorts']]
#--------------------------------------------------------------------------------------------------------------------
