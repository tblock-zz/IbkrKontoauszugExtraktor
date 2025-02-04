import pandas as pd
import globals
import language as lg

lng = lg.selected
#--------------------------------------------------------------------------------------------------
def copyAllRows(frm, to):
    # Übertragen der Spalten "Symbol" und "Menge" von Tabelle a zu Spalten "a" und "b" in Tabelle x
    neue_daten = pd.DataFrame({
        'Ticker': frm['Symbol'],
        'Menge': frm['Menge']
    })
    to = pd.concat([to, neue_daten], ignore_index=True)
    return to
#--------------------------------------------------------------------------------------------------------------------
def showLine():
    print("-"*80)
#--------------------------------------------------------------------------------------------------
def showTables(tables):
    """Zeigt alle Tabellen an."""
    for name, table in tables.items():
        print(f"Tabelle: {name}")
        print(table)
        print("\n")
#--------------------------------------------------------------------------------------------------
def showTableFiltered(t, name, col:str=None, filter:str = None):
    print(f"Tabelle: {name}")
    try:
      print(t[t[col] == filter])
    except:    
      try:
        print(t.to_string(na_rep='-'))  # Gibt die gefilterte Tabelle aus, ohne Kürzungen
      except:
        print("nicht verfügbar")    
#--------------------------------------------------------------------------------------------------
def showSpecificTable(tables, tableName:str,columns):   
    table = None
    try:
        if tableName.isdigit():
            index = int(tableName) - 1  # Da Listen bei 0 beginnen, subtrahieren wir 1
            if 0 <= index < len(tables):
                table_key = list(tables.keys())[index]
                table = tables[table_key]
                tableName = table_key
            else:
                print(f"Index {index + 1} liegt außerhalb des gültigen Bereichs.")
        else:
            table = tables.get(tableName)
        if columns:
            col_range = columns.split('-')
            start_col = int(col_range[0])
            end_col = int(col_range[1]) + 1
            table = table.iloc[:, start_col:end_col]
        print(f"Tabelle: {tableName}")
        print(table.to_string())
    except:
        print(f"Tabelle '{tableName}' nicht gefunden.")
#--------------------------------------------------------------------------------------------------------------------
def showTableColumn(prefix,table, frm, to):
    print(prefix,end=":")
    for i in range(frm,to):
        print(table.iloc[i],end=",")
    print()
#--------------------------------------------------------------------------------------------------------------------
def showStartStocks(t):
    showLine()
    showLine()
    print("Aktien Beginn:\n", t)
#--------------------------------------------------------------------------------------------------------------------
def showSoldShorts(t,sum=None):
    showLine()
    st = lng["idSoldOptions"]
    print(f"{st}\n", t.to_string(na_rep='-'))
    if not sum is None:
        showLine()
        sumStr = lng["idSoldOptionsSum"]
        print(sumStr,sum)
#--------------------------------------------------------------------------------------------------------------------
def showBoughtShorts(t,sum=None):
    showLine()
    st = lng["idBoughtOptions"]
    print(f"{st}\n", t.to_string(na_rep='-'))
    if not sum is None:
        showLine()
        sumStr = lng["idBoughtOptionsSum"]
        print(sumStr,sum)
#--------------------------------------------------------------------------------------------------
def showExecutedPuts(t):
    showLine()
    print("Ausgeführte Puts\n" , t.to_string(na_rep='-'))
#--------------------------------------------------------------------------------------------------
def showExecutedCalls(t):
    showLine()
    print("Ausgeführte Calls\n", t.to_string(na_rep='-'))
#--------------------------------------------------------------------------------------------------
def showExecutedShorts(t):
    print("\nAusgeführte Shorts\n", t.to_string(na_rep='-'))
#--------------------------------------------------------------------------------------------------
def showBoughtStocks(t):
    showLine()
    s = lng["idBoughtStocks"]
    print(s+"\n", t)
#--------------------------------------------------------------------------------------------------
def showSoldStocks(t):
    showLine()
    s = lng["idSoldStocks"]
    print(s+"\n", t)
#--------------------------------------------------------------------------------------------------
def showStocksSellProfit(t):
    showLine()
    t = t.dropna()
    print("Berechnung Käufe - Verkäufe:\n" ,t.to_string())
    showLine()
    sum = t['Preis_Differenz'].sum()
    print("Profit:" ,sum)
#--------------------------------------------------------------------------------------------------
def showRemainingStocks(p):
    showLine()
    if globals.debug: print("Übrig gebliebene puts:\n", p.to_string(na_rep='-'))
    #print("\nAktienbestand Ende:\n", p[p["Menge"]>0].to_string(na_rep='-'))
    print("\nAktienbestand Ende:\n", p)
    print("-"*100)
#--------------------------------------------------------------------------------------------------
def showPerformance(table,name):
    #obj.displayLastExecutionResult()
    showTableFiltered(table,name)
    print("-"*100)
#--------------------------------------------------------------------------------------------------
def showZinsen(table,name):
    showTableFiltered(table,name,"Währung","Gesamt Zinsen in EUR")
    print("-"*100)
#--------------------------------------------------------------------------------------------------
def showDividenden(table,name):
    showTableFiltered(table,name,"Währung","Gesamtwert in EUR")
    print("-"*100)
#--------------------------------------------------------------------------------------------------
def showQuellensteuer(table,name):
    showTableFiltered(table,name,"Währung","Gesamt Quellensteuer in EUR")
    print("-"*100)
#--------------------------------------------------------------------------------------------------
