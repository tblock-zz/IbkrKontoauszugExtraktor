# IbkrKontoauszugExtraktor
## Disclaimer
Bitte beachten Sie, dass dieses Programm und die daraus resultierenden Daten nicht geprüft sind. Es wird daher keine Garantie für die Richtigkeit der Ausgaben übernommen. Eine Überprüfung der Ausgaben ist unerlässlich. Bei Bedarf konsultieren Sie bitte Ihren Steuerberater.

## Captrader/Ibkr Kontoauszug Csv Extraktor  
Dieses Python-Skript ermöglicht es, einzelne Tabellen aus den Kontoauszügen von Captrader bzw. IBKR effizient zu extrahieren.

### Anwendung
Führen Sie das Skript mit dem folgenden Befehl aus:
`python extrahiereIbkrSteuerDaten.py <Pfad/Dateiname_der_CSV_Kontoauszugsdatei> --align converted --tax --new <Dateiname_vorhandener_Aktien>`

Hierbei ist --new gefolgt vom Dateinamen, in dem alle Aktien aufgeführt sind, die bereits vor den Transaktionen im neuen Captrader CSV-Dokument vorhanden waren. Ein praktisches Beispiel hierfür ist:

`python extrahiereIbkrSteuerDaten.py <Pfad/Dateiname_der_CSV_Kontoauszugsdatei> --align converted --tax --new stocksbefore.csv`

Am Ende dieses Prozesses wird die Datei stocksafter.csv erstellt. Sie enthält die Übersicht der Aktien, die nach allen Transaktionen noch im Bestand sind. Diese Datei nutzt dasselbe Format wie die ursprüngliche Datei.
## Beispiel: Neues Konto ab 2023 bei Captrader
1. Laden Sie den Captrader-Auszug für 2023 (Captrader2023.csv) von Ihrem Konto herunter.
2. Benennen Sie die Datei stocksbefore.csv in stocksbefore2023.csv um und führen Sie das Skript aus:

`python extrahiereIbkrSteuerDaten.py Captrader2023.csv --align converted --tax --new stocksbefore2023.csv`

Sie erhalten dadurch die Berechnungen für das Jahr 2023.

3. Kopieren Sie die Datei stocksafter.csv zur Vorbereitung auf das folgende Jahr und benennen Sie diese in stocksbefore2024.csv um.

Wiederholen Sie diesen Prozess jährlich mit den entsprechenden neuen Daten.

## Hilfe
Zur Anzeige weiterer Optionen nutzen Sie:

`python extrahiereIbkrSteuerDaten.py -h`


## Installation
Voraussetzung:
- python 3.10 installiert

Nach dem Klonen des Repositories folgendes eingeben:
`pip install -r requirements.txt`

Dies installiert alle benötigten Abhängigkeiten und stellt sicher, dass das Skript korrekt ausgeführt werden kann.

Open todo's:  
  Sprachanpassungen
