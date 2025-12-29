'''
Filters the tables for specific information and returns the filterend table.
'''
import pandas as pd
import numpy as np
import globals
import language as lg

global tables
global sp

pd.options.mode.chained_assignment = None  # Disable the warning

lng = lg.selected
#--------------------------------------------------------------------------------------------------------------------
# table operations
#--------------------------------------------------------------------------------------------------------------------
def setTables(_tables):
    global tables
    tables = _tables
#--------------------------------------------------------------------------------------------------------------------
def merge(frm,to):
    return pd.concat([to.copy(), frm], ignore_index=True)    
#--------------------------------------------------------------------------------------------------------------------
def addCols(table,cols):
    table[cols] = np.nan
    return table
#--------------------------------------------------------------------------------------------------------------------
def delCols(table,cols):
    for col in cols:
        del table[col]
    return table    
#--------------------------------------------------------------------------------------------------------------------
def renameCols(table,cols):
    for i in range(0,len(cols),2): 
        table.rename(columns={cols[i]: cols[i+1]}, inplace=True)
    return table
#--------------------------------------------------------------------------------------------------------------------
def toNumber(table,cols):
    for i in cols:        
        table[i] = table[i].astype(float)
    return table    
#--------------------------------------------------------------------------------------------------------------------
def getRowsOfColumnsContainingStr(table, colName:str, pattern:str):
        return table[table[colName].str.contains(pattern, na=False)]
#--------------------------------------------------------------------------------------------------------------------
def getRowsOfColumnsMatchingFormula(table, colName:str, pattern:str):
    if globals.debug:    print(f"Filter {colName} mit {pattern}")
    temp = table.copy()
    temp[colName] = pd.to_numeric(temp[colName], errors='coerce')
    return table[temp.eval(f"`{colName}` {pattern}")]

#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
def addEurUsdToTable(tables,t,sTable:str):
    eu = "USDEUR"
    acc = lng[sTable]
    dt = acc['time'] # suche nach transaktionszeit
    tf = tableForex(tables)
    for index, row in t.iterrows():
        datetime = row[dt]
        usdToEur = findWechselkurs(tf,datetime,"")
        t.loc[index, eu] = usdToEur
    return t
#--------------------------------------------------------------------------------------------------------------------
def handleTable(tables, accessName, colsToShow):
    acc     = lng[accessName]
    name, u = acc['name'], acc['usedCols']
    r = None
    n = tables.get(name)
    if n is not None:
        filtered_table = getRowsOfColumnsContainingStr(n,u[0],u[1])
        filtered_table = filtered_table.iloc[:, 0:colsToShow]
        r = filtered_table
        delCols(r,acc['delCols'])
    return r, name
#--------------------------------------------------------------------------------------------------------------------
# the various tables to handle
#--------------------------------------------------------------------------------------------------------------------
def tableTransactions(tables):
    return tables.get(lng['Transaktionen'])
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
def tableForex(tables):
    acc = lng['Forex']
    name, f, r, n = acc['name'], acc['filters'], acc['renames'], acc['toNumber']
    t = tables.get(name).copy()[f]
    t = renameCols(t,r)
    # wandle nach datetime und lösche Zeilen ohne
    c = lng['Forex']['time']
    t[c] = pd.to_datetime(t[c], errors='coerce')
    t = t.dropna(subset=[c])
    # umwandlung string nach zahl    
    return toNumber(t,n)
#--------------------------------------------------------------------------------------------------------------------
def tableStocksStart(tables): 
    acc = lng['Performance']
    name, f, r = acc['name'], acc['filterStocks'], acc['renames']
    t = tables.get(name)
    t = renameCols(t,r)
    t = getRowsOfColumnsContainingStr(t, f["col"], f["val"])
    # filter nach symbol und menge
    t = t[acc['filters']]
    # wandle mengen string nach zahl
    t[r[1]] = t[r[1]].astype(int)
    # filtere 0 mengen raus
    t = t[t[r[1]] > 0]
    return t
#--------------------------------------------------------------------------------------------------------------------
def tableStocksBuy(tables):
    acc = lng['Aktien']
    name, f, r, n = acc['name'], acc['filterBuy'], acc['renames'], acc['toNumber']
    t = renameCols(tables.get(name),r)
    #t = getRowsOfColumnsContainingStr(t, f["col"], f["val"])
    t = getRowsOfColumnsMatchingFormula(t, f["col"], f["val"])
    t = toNumber(t[acc['filters']],n)
    t = addEurUsdToTable(tables, t, 'Aktien')
    p,g,w,m = acc['preis'],acc['gebühr'],'USDEUR',acc['menge']
    t['EkEuro'] = (t[g]-t[p]*t[m])*t[w]
    return t
#--------------------------------------------------------------------------------------------------------------------
def tableStocksSell(tables):
    acc = lng['Aktien']
    name, f, r, n = acc['name'], acc['filters'], acc['renames'], acc['toNumber']
    t = tables.get(name)
    t = renameCols(t,r)
    f = acc['filterSold']
    #t = getRowsOfColumnsContainingStr(t, f["col"], f["val"]).copy()
    t = getRowsOfColumnsMatchingFormula(t, f["col"], f["val"])
    t = t[acc['filters']]
    # suche für jede Transaktion den zugehörigen Euro Umrechnungsfaktor
    # und wandle Erlös und Gebühr nach Euro
    t = addEurUsdToTable(tables, t, 'Aktien')
    t = toNumber(t,n)
    p,g,w,m = acc['preis'],acc['gebühr'],'USDEUR',acc['menge']
    t = toNumber(t,[p,g,w,m])
    t['EkEuro'] = (t[g]-t[p]*t[m])*t[w]
    return t
#--------------------------------------------------------------------------------------------------------------------
def tableRemainingExecutedPuts(p,t):    
    p.drop(lng['Transaktionen']['bis'], axis=1, inplace=True)
    t= t[t.isnull().any(axis=1)]  # Behalte nur Zeilen mit NaN oder None in irgendeiner Spalte
    t = t.drop(columns=t.filter(like='_Verkauf').columns)
    t = t.rename(columns=lambda x: x.replace('_Kauf', ''))
    p = p[p[['Datum/Zeit', 'Symbol']].apply(tuple, 1).isin(t[['Datum/Zeit', 'Symbol']].apply(tuple, 1))]
    p['Menge'] = p['Menge'].abs()
    return p
#--------------------------------------------------------------------------------------------------------------------
def tablePerformance(tables):    
    acc = lng['Realisiert']
    name, f, r = acc['name'], acc['filters'], acc['renames']
    subCol= acc['usedCols'][0]
    rslt = handleTable(tables, 'Realisiert', 7)
    t,name = rslt[0], rslt[1]
    t = t[t[subCol] != acc['filters'][0]].copy()
    # rename
    c = t[subCol]
    for i, item in enumerate(r):
        c.iat[i] = item
    return t,name
#--------------------------------------------------------------------------------------------------------------------
def tableTransactionsOptions(tables):
    return tables.get(lng['Transaktionen']['name'])
#--------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------
class EcbProvider:
    def __init__(self, csv_path='eurofxref-hist.csv'):
        self.df = pd.read_csv(csv_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df.set_index('Date', inplace=True)

    def get_usd_eur(self, target_date):
        # EZB-Kurse sind meistens EUR/USD (1 EUR = x USD)
        # Wir brauchen oft USD -> EUR (1/x)
        try:
            # Suche den nächsten verfügbaren Tag (EZB publiziert nicht an Wochenenden)
            idx = self.df.index.get_indexer([target_date], method='pad')[0]
            rate_usd = self.df.iloc[idx]['USD']
            return 1.0 / rate_usd
        except:
            return None
#--------------------------------------------------------------------------------------------------------------------
def getEcbRate(datetime):
    ecb = EcbProvider()
    date_only = pd.to_datetime(datetime).date()
    rate = ecb.get_usd_eur(pd.to_datetime(date_only))
    return rate
#--------------------------------------------------------------------------------------------------------------------
def findWechselkurs(forexTable,datetime,symbol):
    # suche nach 'Datum/Zeit', 'Menge' und 'Erlös in EUR'
    c = lng['Forex']['time']
    t = forexTable[forexTable[c] == datetime]
    if not t.empty:
        x = t.head(2)
        x = x['EUR']/x['USD']
        return abs(x.iloc[0])    
    # Fallback: EZB-Referenzkurs
    # Hier müsste eine Funktion aufgerufen werden, die in einer EZB-CSV sucht
    ezb_kurs = getEcbRate(datetime) 
    if ezb_kurs:
        return ezb_kurs
#--------------------------------------------------------------------------------------------------------------------
def addEurValuesToOptions(tables,usePositive:bool):
    acc = lng['Transaktionen']
    f,e,g,r,n = acc['filterSoldOptions'], acc['erlös'], acc['gebühr'], acc['renames'], acc['toNumber']
    eu = "USDEUR"
    t = tableTransactionsOptions(tables)
    t = renameCols(t,r)
    t = getRowsOfColumnsContainingStr(t, f["col"], f["val"]).copy()
    for i in n:       t[i] = pd.to_numeric(t[i])
    if usePositive:     t = t[t[e] > 0] 
    else:               t = t[t[e] < 0] 
    # suche für jede Transaktion den zugehörigen Euro Umrechnungsfaktor
    # und wandle Erlös und Gebühr nach Euro
    tf = tableForex(tables)
    strDateTime = acc['time'] # suche nach transaktionszeit
    for index, row in t.iterrows():
        datetime = row[strDateTime]
        usdToEur = findWechselkurs(tf,datetime,"")
        t.loc[index, eu] = usdToEur
    return t
#--------------------------------------------------------------------------------------------------------------------
def soldOptions(tables):
    return addEurValuesToOptions(tables, True)
#--------------------------------------------------------------------------------------------------------------------
def boughtOptions(tables):
    return addEurValuesToOptions(tables, False)
#--------------------------------------------------------------------------------------------------------------------
def splitOptionSymbol(df):
    acc = lng['Transaktionen']['symbol']
    if acc not in df.columns:
        return df
    
    # Symbol format "TSLA 03OCT25 420 P"
    # Split by first space: Ticker vs rest
    s = df[acc].str.split(' ', n=1, expand=True)
    if s.shape[1] >= 2:
        df[acc] = s[0]
        df.insert(1, 'Optionen', s[1])
    else:
        # Fallback if no space found
        df.insert(1, 'Optionen', '')
    return df

#--------------------------------------------------------------------------------------------------------------------
def calculateOptionsEuro(tables,t):
    acc = lng['Transaktionen']
    f = acc['filterCallsPuts']
    df = getRowsOfColumnsContainingStr(t, f["col"], f["val"])
    df = df[acc['filters']]
    df['EkEuro'] = (df[acc['erlös']] + df[acc['gebühr']])*df['USDEUR']
    m = acc['menge']
    if m in df.columns:
        df[m] = pd.to_numeric(df[m], errors='coerce') / 100.0
    df = splitOptionSymbol(df)
    return df
#--------------------------------------------------------------------------------------------------------------------
def soldCallsPuts(tables):
    t = soldOptions(tables)
    return calculateOptionsEuro(tables,t)
#--------------------------------------------------------------------------------------------------------------------
def boughtCallsPuts(tables):
    t = boughtOptions(tables)
    return calculateOptionsEuro(tables,t)
#--------------------------------------------------------------------------------------------------------------------
def getSumOptions(tableSoldCallsPuts):
    cols = lng['Transaktionen']['colsSum']
    t = tableSoldCallsPuts
    return t['EkEuro'].sum()
#--------------------------------------------------------------------------------------------------------------------
def splitSymbolExecutedShorts(table):
    acc = lng['Transaktionen']
    symbol = acc['symbol']
    t = table[symbol]
    split_columns = t.str.split(' ', expand=True)
    # Check if the number of split columns matches the expected number
    expected_columns = len(acc['splits'])
    if split_columns.shape[1] != expected_columns:
        empty_df = pd.DataFrame(columns=acc['filterExecutedShorts'])
        return empty_df
    split_columns.columns = acc['splits']
    table = delCols(table, [acc['erlös']])
    table = table.drop(columns=[symbol]).join(split_columns)
    table = table.drop_duplicates(keep=False)
    table = table[acc['filterExecutedShorts']]
    return table
#--------------------------------------------------------------------------------------------------------------------
def getOptions(table,type):
    f   = lng['Transaktionen'][type]
    return getRowsOfColumnsContainingStr(table, f["col"], f["val"])
#--------------------------------------------------------------------------------------------------------------------
def executedOptions(tables):
    return getOptions(tableTransactionsOptions(tables),'filterExeOptions')
#--------------------------------------------------------------------------------------------------------------------
def executedPutsCalls(tables,executedOptionsTable, type):
    acc = lng['Transaktionen']
    t = getOptions(executedOptionsTable, type)
    t = splitSymbolExecutedShorts(t)
    t = addEurUsdToTable(tables, t, 'Aktien')
    p,g,w,m = acc['erlös'],acc['gebühr'],'USDEUR',acc['menge']
    t = toNumber(t,[p,g,w,m])
    fac = -100.0 if type == 'filterExePuts' else 100.0
    t['EkEuro'] = (t[p]*t[m]*fac + t[g])*t[w]
    return t
#--------------------------------------------------------------------------------------------------------------------
