
# IbkrKontoauszugExtraktor für 2025 und davor

## Disclaimer
Bitte beachten Sie, dass dieses Programm und die daraus resultierenden Daten nicht geprüft sind. Dies ist keine Steuerberatung. Es wird daher keine Garantie für die Richtigkeit der Ausgaben übernommen. Eine Überprüfung der Ausgaben ist unerlässlich. Bei Bedarf konsultieren Sie bitte Ihren Steuerberater.

## Captrader/IBKR Kontoauszug CSV-Extraktor  
Dieses Python-Skript ermöglicht es, einzelne Tabellen aus den Kontoauszügen von Captrader bzw. IBKR effizient zu extrahieren und Berechnungen nach dem Fifo Prinzip mit USD.EUR Umrechnung vorzunehmen.

### Anwendung
Führen Sie das Skript mit dem folgenden Befehl aus:
```bash
python extrahiereIbkrSteuerDaten.py <Pfad/Dateiname_der_CSV_Kontoauszugsdatei> --align converted --tax --new <Dateiname_vorhandener_Aktien>
```
Hierbei ist `--new` gefolgt vom Dateinamen, in dem alle Aktien mir Einstandskursen, mit Datum und USD.EUR Kurs aufgeführt sind, die bereits vor den Transaktionen im neuen Captrader CSV-Dokument vorhanden waren. Ein praktisches Beispiel hierfür ist:
```bash
python extrahiereIbkrSteuerDaten.py Captrader2025.csv --align converted --tax --new stocksbefore.csv
```
Am Ende dieses Prozesses wird die Datei `stocksafter.csv` erstellt. Sie enthält die Übersicht der Aktien, die nach allen Transaktionen noch im Bestand sind. Diese Datei nutzt dasselbe Format wie die ursprüngliche Datei.

### Export 
Mit der Option `--csv <Dateiname>` können die extrahierten Daten in eine Datei exportiert werden. Dabei wird das Format automatisch anhand der Dateiendung gewählt:
- **.csv**: Erstellt eine einfache CSV-Datei mit den Detaildaten.
- **.ods**: Erstellt ein Open Document Spreadsheet (z.B. für LibreOffice oder Excel). Dieses enthält mehrere formatierte Arbeitsblätter:
  - **Steuer Übersicht**: Eine Zusammenfassung der Gewinne und Verluste (Aktien FIFO, Optionen, Dividenden, Zinsen).
  - **Aktien**: Detaillierte FIFO-Berechnung der Aktiengeschäfte.
  - **Optionen**: Detaillierte Auflistung der Optionsgeschäfte (Stillhaltergeschäfte und Käufe).

## Beispiel: Neues Konto ab 2023 bei Captrader
1. Laden Sie den Captrader-Auszug für 2023 (`CaptraderDateiName.csv`) von Ihrem Konto herunter.
2. Benennen Sie die Datei `stocksbefore.csv` die alle noch vorhandenen Aktien vor 2023 enthält in `stocksbefore2023.csv` um und führen Sie das Skript aus:
   ```bash
   python extrahiereIbkrSteuerDaten.py CaptraderDateiName.csv --align Captrader2023.csv --tax --new stocksbefore2023.csv
   ```
   Sie erhalten dadurch die Berechnungen für das Jahr 2023. 
3. Kopieren Sie die Datei `stocksafter.csv` zur Vorbereitung auf das folgende Jahr und benennen Sie diese in `stocksbefore2024.csv` um.

Wiederholen Sie diesen Prozess jährlich mit den entsprechenden neuen Daten.
Im nächsten Jahr also Anfang 2025 Captrader Auszug von 2024 laden und umbenennen nach Captrader2024.csv. Dann das Programm ausführen.   
`python extrahiereIbkrSteuerDaten.py Captrader2024.csv --align converted --tax --new stocksbefore2024.csv`  


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

Open todo's:  
- sortieren nach Datum

## Anhang
In Deutschland gilt das FIFO Prinzip.

- Kauf Dollar am Datum_usd zum Kurs usdeur_kauf
- Kaufs einer Aktie
  - Datum_ek, Anzahl_ek, Kurs Dollar_ek, usdeur_ek
- Verkauf einer Aktie
  - Datum_vk, Kurs Dollar_vk, Kurs usdeur_vk
- Berechnung:
  - Einfach: Gewinn = Anzahl*(usdeur_vk - usdeur_ek)
