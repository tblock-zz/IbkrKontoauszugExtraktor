tableNames = {
'ger' : {
        # short name, list name, used cols, to delete cols
        "Transaktionen" : {            
            'name'    : 'Transaktionen Aktien- und Indexoptionen', # tabellenname
            'filters'             : ['Symbol', 'Datum/Zeit', 'Menge', 'Erlös', 'Prov./Gebühr', 'Code'],
            'filters2'            : ['Erlös', 'Prov./Gebühr'],
            'splits'              : ['Ticker', 'Bis', 'Preis', 'Typ'],
            'filterExecutedShorts': ["Datum/Zeit", 'Ticker', 'Bis', 'Preis', 'Menge'],
            'filterSoldOptions'   : ["Code", "^[OC]$"],
            'filterExeOptions'    : ["Code", "A.*"],
            'filterCallsPuts'     : ["Symbol", ".*?[CP]$"],
            'filterExeCalls'      : ["Symbol", ".*?C$"],
            'filterExePuts'       : ["Symbol", ".*?P$"],
            'symbol'              : 'Symbol',
            'time'                : 'Datum/Zeit',
            'bis'                 : 'Bis',
            'erlös'               : 'Erlös',
            'gewinn'              : 'Gewinn',
            'verlust'             : 'Verlust',
        } ,
        "Aktien" : {            
            'name'    : 'Transaktionen Aktien', 
            'filters'      : ['Datum/Zeit', 'Symbol', 'T.-Kurs', 'Menge'], #, 'Prov./Gebühr'],
            'filterSold'   : ["Code", "^C;Ex$"],
            'filterBuy'    : ["Code", "^O$"],
            'renames'      : ['T.-Kurs', 'Preis', 'Symbol', 'Ticker'],
            'toNumber'     : ['Preis', 'Menge'],
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
            'filters': ["Vermögenswertkategorie", "Aktien"],
                       # Name vorher, Name nachher usw.
            'renames' : ['Vorher Menge', 'Menge', 'Symbol', 'Ticker']
        },
        'Realisiert'  : {
            'name'    : 'Übersicht  zur realisierten und unrealisierten Performance',
            'usedCols': [ 'Vermögenswertkategorie','Gesamt'],
            'delCols' : ['Symbol', 'Kostenanp.'],
            'filters' : ['Gesamt (Alle Vermögenswerte)'],
            # rename nach position
            'renames' : ['Gesamt Aktien','Gesamt Optionen','Gesamt Devisen']
        }
    }
}

# language setting to german, other not supported yet
selected = tableNames['ger']