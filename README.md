# IbkrKontoauszugExtraktor
##Disclaimer
Dieses Programm und dessen Ergebnisse sind nicht geprüft und somit gibt es hier keine Garantie, dass die Ausgabe korrekt ist.
Die Ausgabe muss deshalb unbedingt noch überprüft werden. Notfalls wenden sie sich an ihren Steuerberater.

Captrader/Ibkr Kontoauszug Csv Extraktor  
Dieses Python Skript ermöglicht es einfach die einzelnen Tabellen aus dem Auszug von Captrader/IBKR zu extrahieren.

Einfach aufrufen mit  
`python extrahiereIbkrSteuerDaten.py Dateiname_mit_Pfadname_der_csv_Kontoauszugsdatei  --align converted --tax --new Datei_mit_vor_dem_Kontoauszug_vorhandene_Aktien`

Die Option `--new` hat als Argument 'Dateiname`. Es wird die Datei `Dateiname` eingelesen, in der man alle Aktien einträgt, die man schon vor den Transaktionen im neuen Captrader csv Dokument besaß. Die Datei 'stocksbefore.csv` ist ein Beispiel mit einer schon vorhandenen Aktie JNJ. Also wäre ein Beispiel:  
`python extrahiereIbkrSteuerDaten.py Dateiname_mit_Pfadname_der_csv_Kontoauszugsdatei  --align converted --tax --new stocksbefore.csv`

Am Ende wird die Datei `stocksafter.csv` geschrieben, von Aktien, die am Ende nach allen puts, calls und Aktienverkäufen noch übrig sind. Diese Datei hat das gleiche Format wie `Dateiname`. Man kann in `Dateiname` Aktien auch manuell einfügen, falls man nicht durch alle alten csv Dateien der zurückliegenden Jahre zurück gehen möchte.

Wenn alle Daten in `Dateiname` aktuell sind, so würde man als für einen Jahresabschluß 2023 die Datei `stocksafter.csv` für das nächste Jahr z.B. nach `stocksbefore2024.csv` kopieren.

## Beispiel neues Konto ab 2023 bei Captrader
Captrader Auszug von 2023: Captrader2023.csv vom eigenen Konto heruntergeladen   

Nutze die Datei stocksbefore.csv und nenne sie um nach stocksbefore2023.csv 
`python extrahiereIbkrSteuerDaten.py Captrader2023 --align converted --tax --new stocksbefore2023.csv`  
Man erhält die Berechnungen für 2023. 
Kopiere die Datei stocksafter.csv nach stocksbefore2024.csv schon mal zur Vorbereitung für das nächste Jahr 2024.

Im nächsten Jahr also Anfang 2025 Captrader Auszug von 2024 laden und umbennen nach Captrader2024.csv. Dann das Programm ausführen.   
`python extrahiereIbkrSteuerDaten.py Captrader2024 --align converted --tax --new stocksbefore2024.csv`  

Man erhält nun die Berechnungen für 2024 inklusive den Verbliebenen Aktien aus 2023. 
Kopiere die Datei stocksafter.csv nach stocksbefore2025.csv schon mal zur Vorbereitung für das nächste Jahr usw.


Hilfe mit  
`python extrahiereIbkrSteuerDaten.py -h`


Installation:
Voraussetzung:
python 3.10 installiert

Nach dem clonen des Repositories folgendes eingeben:
`pip install requirements.txt`

Open todo's:  
Umrechnen in Euro
