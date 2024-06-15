import pandas as pd
import globals

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
    if col is None:
        print(t.to_string(na_rep='-'))  # Gibt die gefilterte Tabelle aus, ohne Kürzungen
    else:
        print(t[t[col] == filter])
#--------------------------------------------------------------------------------------------------
def showSpecificTable(tables, tableName:str,columns):
    table = tables.get(tableName)
    if table is not None:
        if columns:
            col_range = columns.split('-')
            start_col = int(col_range[0])
            end_col = int(col_range[1]) + 1
            table = table.iloc[:, start_col:end_col]
        print(f"Tabelle: {tableName}")
        print(table.to_string())
    else:
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
    print("Bestehende Aktien:\n", t)
#--------------------------------------------------------------------------------------------------------------------
def showExecutedShorts(t):
    showLine()
    print("Executed Shorts\n", t.to_string(na_rep='-'))
#--------------------------------------------------------------------------------------------------
def showExecutedPuts(t):
    showLine()
    print("Ausgeführte Puts\n" , t.to_string(na_rep='-'))
#--------------------------------------------------------------------------------------------------
def showExecutedCalls(t):
    print("\nAusgeführte Calls\n", t.to_string(na_rep='-'))
#--------------------------------------------------------------------------------------------------
def showPutsVsCalls(t):
    if not t.empty:
        print("\nCalls vs puts:\n", t.to_string(na_rep='-'))
        col= "Preis_Differenz"
        plus = t[t[col] > 0][col].sum()
        minus = t[t[col] < 0][col].sum()
        showLine()
        print("Aktien Gewinn:", 100*plus)
        print("Aktien Verlust:", 100*minus)
        showLine()
#--------------------------------------------------------------------------------------------------
def showBoughtStocks(t):
    pass
#--------------------------------------------------------------------------------------------------
def showSoldStocks(t):
    pass
#--------------------------------------------------------------------------------------------------
def showRemainingStocks(p):
    if globals.debug: print("Übrig gebliebene puts:\n", p.to_string(na_rep='-'))
    print("\nBestehende Aktien aus puts vs calls:\n", p[p["Menge"]>0].to_string(na_rep='-'))
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
