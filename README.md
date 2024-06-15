# IbkrKontoauszugExtraktor
##Disclaimer
Dieses Programm und dessen Ergebnisse sind nicht geprüft und somit gibt es hier keine Garantie, das die Ausgabe korrekt ist.
Die Ausgabe muss deshalb unbedingt noch überprüft werden. Notfalls wenden sie sich an ihren Steuerberater.

Ibkr Kontoauszug Csv Extraktor  
Dieses Python Skript ermöglicht es einfach die einzelnen Tabellen aus dem Auszug von IBKR zu extrahieren.

Einfach aufrufen mit  
`python extrahiereIbkrSteuerDaten.py Dateiname_mit_Pfadname_der_csv_Kontoauszugsdatei  --align converted --tax`

Um alles aus dem Auszug selber zu berechnen, bitte die Option --new eingeben. Es wird dann zusätzlich eine Datei `stocksbefore.csv` eingelesen, in der man alle Aktien einträgt, die man schon vor den Transaktionen im neuen Captrader csv Dokument besaß.

Am Ende wird die Datei `stocksafter.csv` geschrieben, von Aktien, die hinzugefügt wurden. Diese Datei hat das gleiche Format wie `stocksbefore.csv`. Man in `stocksbefore.csv` Aktien auch manuell einfügen, falls man nicht durch alle alten csv Dateien der zurückliegenden Jahre zurück gehen möchte.
Wenn alle Daten in `stocksbefore.csv` aktuell sind, so würde man nach der neuen Berechnung und Ausgabe von `stocksafter.csv` diese nach `stocksbefore.csv` kopieren.

Wahrscheinlic wird der Name zum Einlesen später als Parameter zu --tax hinzugefügt.

Hilfe mit  
`python extrahiereIbkrSteuerDaten.py -h`


Installation:
Voraussetzung:
python 3.10 installiert

Nach dem clonen des Repositories folgendes eingeben:
`pip install requirements.txt`
