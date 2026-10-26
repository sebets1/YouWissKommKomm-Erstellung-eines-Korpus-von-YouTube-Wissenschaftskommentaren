# YouWissKommKomm: Erstellung eines Korpus von YouTube Wissenschaftskommentaren
### Code Repository


Dieses Repository enthält die Code Scripts, die für die Erstellung und Verarbeitung des **YouWissKommKomm Korpus** entwickelt wurden. 
Das Korpus umfasst etwa 1.2 Mio. Kommentare unter YouTube Videos von Kanälen zur Wissensvermittlung.
Eine Dokumentation des Korpus sowie eine Liste aller verwendeten Video-URLs sind in folgendem Repository abgelegt: https://github.com/sebets1/YouWissKommKomm-Korpus

Das File `video_data.csv` im Ordner `0_data` gibt zudem einen Einblick in die Datenmenge und verwendeten Videos.
Im Folgenden werden die Skripte kurz beschrieben. Im Ordner `0_data`befindet sich ausserdem ein kleines Demodatenset mit anonymisierten Kommentaren, 
mit dem die Skripte getestet werden können.

Das Repository besteht aus drei unterschiedlichen Teilen:

- Teil 1 enthält alle Scripts die zur Extraktion der Kommentare und Videometadaten von YouTube verwendet wurden.
- Teil 2 enthält das Script zur Verarbeitung und Annotation der Daten mit Fokus auf Gesprächsnachverfolgung und Antwortgeschwindigkeiten. Für dieses Script befindet sich im `0_data` Ordner ein Demodatensatz zum Ausprobieren.
- Teil 3 enthält die Scripts zum Aufbereiten des Korpus für den Upload auf die [Korpusplattform LCP](https://lcp.linguistik.uzh.ch/).

Da es sich um drei in sich abgeschlossene Teilprojekte handelt, befindet sich in jedem der drei Ordner ein separates 
`requirements.txt`-File mit den jeweils benötigten Python Packages.

*Dieses Repository entstand im Rahmen des Projekts **eee-ScienceDebates**.*
> https://eee-sciencedebates.digital/
>
> https://www.ds.uzh.ch/de/projekte/eee-sciencedebates.html

-------------------------------------
## 1 Scraping von YouTube Kommentaren
Der erste Teil des Repositories enthält die Scripts zur Erhebung der YouTube Kommentare und der zugehörigen Videometadaten. 
Das Scraping erfolgt über die YouTube Data API. Dafür wird ein eigener API-Key benötigt, der über die Google API Console 
erstellt werden muss. Die API unterliegt täglichen Anfragebeschränkungen. Für die Erstellung des Korpus wurde das Scraping 
deshalb über mehrere Wochen durchgeführt.

Der Ablauf besteht aus mehreren Schritten:

- `get_video_ids.py` erstellt anhand der Channel-ID eines YouTube-Kanals eine Liste aller zugehörigen Video-IDs und speichert diese in einer `.txt`-Datei.
- `scrape_youtube_comments.py` ruft anhand dieser Video-IDs die Kommentare und Antworten (Replies) ab. Das Script scraped nur Kommentare mit mindestens fünf Replies.
- `scrape_youtube_video_details.py` ruft die Metadaten der Videos, wie Titel und Informationen aus der Videobeschreibung, ab. Die Daten werden zunächst als .json gespeichert.
- `json2xml.py` konvertiert die als JSON vorliegenden YouTube-Kommentardaten in XML-Dateien im Header-Body-Format.
- `xml2pd-df.py` konvertiert die XML-Dateien anschliessend in einen Pandas DataFrame und speichert die Daten als CSV.

## 2 Konversationen und Antwortgeschwindigkeiten filtern
Input ist das CSV mit den Rohdaten des Korpus, bzw. das Beispieldatenset `data/demo_data.csv`.

Das Script `process_yt_corpus.py` gruppiert die Kommentare in Threads (ein Top-Level Kommentar mit allen Replies)
mithilfe der verfügbaren Thread IDs.

Danach werden folgende Informationen annotiert:

- Zuweisung eindeutiger Sprecher-IDs innerhalb jedes Threads
- Identifizierung, auf welchen Kommentar sich jede Antwort bezieht
- Berechnung der Zeitspanne bis zur Antwort
- Klassifizierung verschiedener Antworttypen (z. B. ob die ursprünglich Kommentierende in die Unterhaltung involviert ist, ob sich ein Antwortender nur einmal meldet oder aktiv an der Unterhaltung teilnimmt)
- Erkennung potenzieller Fehlklassifizierungen (gelöschte Antworten, Probleme mit Zeitstempeln usw.)

Schlussendlich speichert das Script das verarbeitete Korpus in eine neue CSV-Datei ab.

## 3 LCP Corpus Builder

Die zwei Scripts in diesem Ordner bereiten das Korpus für einen Upload auf die Korpus Plattform [LCP](https://lcp.linguistik.uzh.ch/) vor.
Zuerst führt das Script `prepare_for_lcp_corpus_builder.py` verschiedene Cleaning Schritte durch.
Anschliessend erstellt `lcp_yt_corpus_builder.py` mithilfe des Python Moduls `lcpcli`die Files für den Upload.


-------------------------------------

Veröffentlichung: 28.10.2026

Autorinnen: Seraina Betschart & Xenia Bojarski (Universität Zürich)
