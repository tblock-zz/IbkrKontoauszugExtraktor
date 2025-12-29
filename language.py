tableNames = {
'ger' : {
        "idSoldOptions" : "Verkaufte Optionen",
        "idSoldOptionsSum" : "Summe Einnahmen Optionen:",
        "idBoughtOptions" : "Gekaufte Optionen",
        "idBoughtOptionsSum" : "Summe Ausgaben Optionen:",
        "idBoughtStocks" : "Aktien gekauft:",
        "idSoldStocks" : "Aktien verkauft:",
        # short name, list name, used cols, to delete cols
        "Transaktionen" : {            
            'name'    : 'Transaktionen Aktien- und Indexoptionen', # tabellenname
            'renames'             : ['Prov./Gebühr', 'Gebühr', 'Erlös', 'Preis'],
            'filters'             : ['Symbol', 'Datum/Zeit', 'Menge', 'Preis', 'Gebühr', 'USDEUR', 'EkEuro', 'Code'],
            'toNumber'            : ['Preis', 'Gebühr'],
            'colsSum'             : ['EkEuro'],
            'splits'              : ['Symbol', 'Bis', 'Preis', 'Typ'],
            'filterExecutedShorts': ["Datum/Zeit", 'Symbol', 'Bis', 'Preis', 'Menge', 'Gebühr','USDEUR', 'EkEuro'],
            'filterSoldOptions'   : {
                "col" :"Code", 
                "val" : "^[OC]$"
            },
            'filterExeOptions'    :  {
                "col" :"Code", 
                "val" : "A.*"
            },
            'filterCallsPuts'     : {
                "col" :"Symbol", 
                "val" : ".*?[CP]$"
            },
            'filterExeCalls'      :  {
                "col" :"Symbol", 
                "val" : ".*?C$"
            },
            'filterExePuts'       :  {
                "col" :"Symbol", 
                "val" : ".*?P$"
            },
            'symbol'              : 'Symbol',
            'time'                : 'Datum/Zeit',
            'bis'                 : 'Bis',
            'erlös'               : 'Preis',
            'gebühr'              : 'Gebühr',
            'menge'               : 'Menge',
            'gewinn'              : 'Gewinn',
            'verlust'             : 'Verlust',
        } ,
        "Aktien" : {            
            'name'    : 'Transaktionen Aktien', 
            #                 vorher   , nachher usw.
            'renames'      : ['T.-Kurs','Preis', 'Prov./Gebühr', 'Gebühr'],
            # filter after renaming
            'filters'      : ['Datum/Zeit', 'Symbol', 'Preis', 'Menge', 'Gebühr', 'USDEUR', 'EkEuro'],
            'filterSold'   : {
                "col" :"Menge", 
                "val" : "<0"
            },
            'filterBuy'   : {
                "col" :"Menge", 
                "val" : ">0"
            },
            'toNumber'     : ['Preis', 'Menge', 'Gebühr','USDEUR'],
            'time'         : 'Datum/Zeit',
            'preis'        : 'Preis',
            'menge'        : 'Menge',
            'gebühr'       : 'Gebühr',
        },
        "Forex" : {            
            'name'    : 'Forex-G&V-Details', 
            'renames'      : ['Menge', 'USD', 'Erlös in EUR', 'EUR'],
            'filters'      : ['Datum/Zeit', 'Beschreibung', 'Menge', 'Erlös in EUR'], #, 'Prov./Gebühr'],
            'toNumber'     : ['USD', 'EUR'],
            'time'         : 'Datum/Zeit',
        },
        'Zinsen' : {
            'name'    : 'Zinsen',
            'usedCols': ['Währung','Gesamt*'],
            'delCols' :  ['Datum', 'Beschreibung']
        },
        'Dividenden' : {
            'name'    : 'Dividenden',
            'usedCols': ['Währung','Gesamt*'],
            'delCols' : ['Datum', 'Beschreibung', 'Code']
        },
        'Quellensteuer' : {
            'name'    : 'Quellensteuer',
            'usedCols': ['Währung','Gesamt*'],
            'delCols' : ['Datum', 'Beschreibung', 'Code']
        },
        'Performance' : {
            'name'    : 'Mark-to-Market-Performance-Überblick',
            'renames' : ['Vorher Menge', 'Menge'],
            'filterStocks'   : {
                "col" :"Vermögenswertkategorie", 
                "val" : "Aktien"
            },
            'filters': ["Symbol", "Menge"],
                       # Name vorher, Name nachher usw.
        },
        'Realisiert'  : {
            'name'    : 'Übersicht  zur realisierten und unrealisierten Performance',
            'usedCols': [ 'Vermögenswertkategorie','Gesamt'],
            'delCols' : ['Symbol', 'Kostenanp.'],
            'filters' : ['Gesamt (Alle Vermögenswerte)'],
            'renames' : ['Gesamt Aktien','Gesamt Optionen','Gesamt Devisen']
            # rename nach position
        }
    }
}

# language setting to german, other not supported yet
selected = tableNames['ger']