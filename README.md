# IbkrKontoauszugExtraktor

## Disclaimer
Bitte beachten Sie, dass dieses Programm und die daraus resultierenden Daten nicht geprüft sind. Es wird daher keine Garantie für die Richtigkeit der Ausgaben übernommen. Eine Überprüfung der Ausgaben ist unerlässlich. Bei Bedarf konsultieren Sie bitte Ihren Steuerberater.

## Captrader/IBKR Kontoauszug CSV-Extraktor
Dieses Python-Skript ermöglicht es, einzelne Tabellen aus den Kontoauszügen von Captrader bzw. IBKR effizient zu extrahieren.

### Anwendung
Führen Sie das Skript mit dem folgenden Befehl aus:
```bash
python extrahiereIbkrSteuerDaten.py <Pfad/Dateiname_der_CSV_Kontoauszugsdatei> --align converted --tax --new <Dateiname_vorhandener_Aktien>
```
Hierbei ist `--new` gefolgt vom Dateinamen, in dem alle Aktien aufgeführt sind, die bereits vor den Transaktionen im neuen Captrader CSV-Dokument vorhanden waren. Ein praktisches Beispiel hierfür ist:
```bash
python extrahiereIbkrSteuerDaten.py <Pfad/Dateiname_der_CSV_Kontoauszugsdatei> --align converted --tax --new stocksbefore.csv
```
Am Ende dieses Prozesses wird die Datei `stocksafter.csv` erstellt. Sie enthält die Übersicht der Aktien, die nach allen Transaktionen noch im Bestand sind. Diese Datei nutzt dasselbe Format wie die ursprüngliche Datei.

## Beispiel: Neues Konto ab 2023 bei Captrader
1. Laden Sie den Captrader-Auszug für 2023 (`CaptraderDateiName.csv`) von Ihrem Konto herunter.
2. Benennen Sie die Datei `stocksbefore.csv` in `stocksbefore2023.csv` um und führen Sie das Skript aus:
   ```bash
   python extrahiereIbkrSteuerDaten.py CaptraderDateiName.csv --align Captrader2023.csv --tax --new stocksbefore2023.csv
   ```
   Sie erhalten dadurch die Berechnungen für das Jahr 2023. 
3. Kopieren Sie die Datei `stocksafter.csv` zur Vorbereitung auf das folgende Jahr und benennen Sie diese in `stocksbefore2024.csv` um.

Wiederholen Sie diesen Prozess jährlich mit den entsprechenden neuen Daten.

### Hilfe
Zur Anzeige weiterer Optionen nutzen Sie:
```bash
python extrahiereIbkrSteuerDaten.py -h
```

## Installation
Voraussetzungen:
- Python 3.10 muss installiert sein.

Nach dem Klonen des Repositories führen Sie den folgenden Befehl aus:
```bash
pip install -r requirements.txt
```
