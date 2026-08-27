# swiss-pii-anonymizer

PII-Anonymisierung für deutschsprachige Texte, wiederverwendbar über mehrere
interne Tools (z.B. SlitProjektHub) — als eigenständiges Python-Paket, nicht
in eine einzelne Anwendung eingebaut.

Baut auf [Microsoft Presidio](https://microsoft.github.io/presidio/) als
Framework (Analyzer + Anonymizer, Konfidenz-Scoring, austauschbare
Recognizer) und ersetzt Presidios schwache deutsche Standard-NER durch
[Flair](https://github.com/flairNLP/flair) (`flair/ner-german-large`,
F1 92.3 auf CoNLL-03 Deutsch revidiert) für Personennamen und
[GLiNER](https://github.com/urchade/GLiNER) (`urchade/gliner_multi_pii-v1`)
für Organisationsnamen. Dazu kommen eigene, prüfziffer-validierte
Recognizer für Schweizer Identifikatoren sowie Presidios eingebaute
deutsche `DE_*`-Recognizer für Geschäftsidentifikatoren.

## Warum nicht nur Regex?

Eine reine Grossschreibungs-Heuristik kann im Deutschen nicht zuverlässig
zwischen einem Personennamen ("Maria Muster") und einem Produkt-/Projektnamen
("Digitaler Sportpass") unterscheiden — beides sind grammatikalisch zwei
grossgeschriebene Wörter hintereinander. Ein echtes NER-Modell (Flair) wurde
auf die tatsächliche Verteilung echter Namen trainiert und triftt diese
Unterscheidung deutlich zuverlässiger.

**Wichtig:** auch das beste NER-Modell ist nicht perfekt (~90-96 % F1 auf
Benchmark-Daten, bei unordentlichem Realtext eher darunter). Dieses Paket
ist eine automatisierte Vorfilterung, kein Ersatz für eine menschliche
Prüfung vor der Übertragung sensibler Inhalte an Cloud-Dienste.

## Erkannte Entitäten

| Entität | Erkennung | Hinweis |
|---|---|---|
| `PERSON` | Flair NER (`flair/ner-german-large`) | schliesst einen direkt vorangestellten Titel mit ein (s.u.) |
| `ORGANIZATION` | GLiNER (`urchade/gliner_multi_pii-v1`, Zero-Shot) | Firmen-/Organisationsnamen im Fliesstext |
| `EMAIL_ADDRESS` | Presidio (regex) | |
| `IBAN_CODE` | Presidio (regex + ISO-7064-Prüfsumme) | international, nicht nur CH |
| `CH_AHV_NR` | eigen (regex + EAN-13-Prüfziffer) | Format `756.NNNN.NNNN.NC` |
| `CH_UID` | eigen (regex + MOD-11-Prüfziffer) | Format `CHE-NNN.NNN.NNC` (Unternehmens-ID) |
| `CH_PHONE_NUMBER` | eigen (regex) | `+41`/`0041` (auch mit `(0)`) /`0`-Präfix |
| `CH_ADDRESS` | eigen (regex) | Strasse + Hausnummer, optional `, PLZ Ort` |
| `CH_LOCATION` | eigen (regex + amtliches PLZ-Verzeichnis) | PLZ + Ort, gegen echte Ortschaften/Gemeinden validiert |
| `DE_VAT_ID` | Presidio (regex) | deutsche USt-IdNr. (`DE` + 9 Ziffern) |
| `DE_HANDELSREGISTER` | Presidio (regex) | HRA/HRB-Nummer |

**Titel:** Ein akademischer/beruflicher Titel direkt vor einem erkannten
Namen (`Dr.`, `Prof.`, `Prof. Dr. med.`, `Mag.`, `lic. iur.`, `Dipl.-Ing.`,
...) wird in die `PERSON`-Spanne hineingezogen, statt separat/unredigiert
stehen zu bleiben — `"Dr. med. Maria Muster"` wird komplett zu `[PERSON]`.
Es entsteht bewusst kein eigener Entitätstyp dafür.

Weitere Entitäten (IP-Adresse, Kreditkarte, deutscher Personalausweis/
Reisepass/Führerschein/Sozialversicherungsnummer, ...) sind über Presidios
eingebaute Recognizer bzw. weitere GLiNER-Labels verfügbar und lassen sich
bei Bedarf ergänzen — siehe
[`docs/analyzer/adding_recognizers.md`](https://microsoft.github.io/presidio/analyzer/adding_recognizers/)
und [Presidios GLiNER-Sample](https://microsoft.github.io/presidio/samples/python/gliner/).

**CH_LOCATION** (PLZ + Ort) wird — anders als `CH_ADDRESS` — hart gegen das
amtliche Ortschaftenverzeichnis validiert (Bundesamt für Landestopografie
swisstopo, "Amtliches Ortschaftenverzeichnis mit Postleitzahl und
Perimeter", monatlich aktualisiert). Die Zuordnung liegt vorverarbeitet in
`src/swiss_pii_anonymizer/data/ch_plz.json` (~3'200 PLZ, DE/FR/IT/RM) —
kein Netzwerkzugriff zur Laufzeit nötig. Ein Regex-Fund wie "1234
Wunderland" oder "8001 Bern" (echte PLZ, falscher Ort) wird verworfen,
nicht nur nach Gross-/Kleinschreibung gefiltert. Neu generieren bei einer
swisstopo-Aktualisierung: `scripts/build_ch_plz_data.py <heruntergeladene
CSV>` (Download-Seite:
[swisstopo.admin.ch/amtliches-ortschaftenverzeichnis](https://www.swisstopo.admin.ch/de/amtliches-ortschaftenverzeichnis),
CSV-Variante, Koordinatensystem egal — wir nutzen nur Namensspalten).

**CH_ADDRESS** (Strasse + Hausnummer) bleibt eine strukturelle
Regex-Heuristik ohne Katalog-Validierung — ein Nicht-Treffer bei der
optionalen ", PLZ Ort"-Endung würde sonst den ganzen (gut über den
Strassen-Suffix verankerten) Adressfund verwerfen. Damit die
Gross-/Kleinschreibungs-Prüfung bei beiden Recognizern nicht durch
Presidios Standard-`IGNORECASE` ausgehebelt wird (z.B. "2021 bis heute"
fälschlich als "PLZ + Ort"), werden beide explizit case-sensitiv
kompiliert.

**Lange, unsegmentierte Texte:** Aus PDFs extrahierter Text landet oft als
ein einziger Fliesstext-Block ohne echte Satzgrenzen (Bullet-Punkte statt
Punkten, keine Zeilenumbrüche) — NER-Modelle degradieren auf solchem Text
spürbar. `FlairPersonRecognizer` chunkt deshalb über Presidios
`CharacterBasedTextChunker` (2000 Zeichen, 100 Überlappung) — für kurze
Texte ein No-Op, für lange ein Sicherheitsnetz gegen ein einzelnes
"Verwirrungsfenster" über das ganze Dokument.

**Ausfallsicherheit:** Scheitert der GLiNER-Modell-Download beim ersten
Aufruf (kein Netzwerk, Modell noch nicht im Cache), wird nur die
`ORGANIZATION`-Erkennung deaktiviert (mit Log-Warnung) — Flair-PERSON und
alle Regex-/Prüfziffer-Recognizer bleiben unberührt funktionsfähig
(`swiss_pii_anonymizer.recognizers_org.SafeGLiNERRecognizer`).

## Installation

```bash
pip install "swiss-pii-anonymizer @ git+https://github.com/lastphoenx/swiss-pii-anonymizer.git"
python -m spacy download de_core_news_lg
```

Das Flair-Modell (`flair/ner-german-large`, ~370 MB) und das GLiNER-Modell
(`urchade/gliner_multi_pii-v1`, ~500 MB) werden beim ersten Aufruf
automatisch von Hugging Face heruntergeladen und lokal zwischengespeichert
(`~/.flair/` bzw. `~/.cache/huggingface/`). **Auf einem Server ohne
Internetzugang:** `scripts/prefetch_models.py` auf einer Maschine mit
Zugang ausführen und `~/.flair/`, `~/.cache/huggingface/` + das
installierte spaCy-Modell auf den Zielserver kopieren. Schlägt nur der
GLiNER-Download fehl, bleibt der Rest des Analyzers trotzdem einsatzbereit
(s. Abschnitt "Ausfallsicherheit" oben).

## Verwendung

```python
from swiss_pii_anonymizer import anonymize, analyze

result = anonymize(
    "Kontaktperson ist Maria Muster, AHV-Nr. 756.1234.5678.97, "
    "IBAN CH93 0076 2011 6238 5295 7."
)
print(result.text)
# -> "Kontaktperson ist [PERSON], AHV-Nr. [CH_AHV_NR], IBAN [IBAN_CODE]."

for f in result.findings:
    print(f.entity_type, f.text, f.score)
```

Nur erkennen, ohne den Text zu verändern (z.B. für eine Vorschau/Bestätigung
im UI, bevor an einen Cloud-Provider gesendet wird):

```python
findings = analyze(text)
if findings:
    # z.B. Bestätigungs-Checkbox im UI einblenden
    ...
```

Beide Funktionen laden Flair-/spaCy-/GLiNER-Modelle lazy beim ersten Aufruf
(Prozess-weites Singleton) — nachfolgende Aufrufe sind schnell.

`get_analyzer()` akzeptiert wie bisher `flair_model=` und zusätzlich
optional `gliner_model=` (Default `urchade/gliner_multi_pii-v1`), falls ein
anderes GLiNER-Modell verwendet werden soll. Bestehende Aufrufe mit nur
`flair_model=` bleiben unverändert kompatibel.

## Entwicklung

```bash
pip install -e ".[test]"
python -m spacy download de_core_news_lg
pytest
```

Die Tests unter `tests/` laufen ohne Netzwerkzugriff — Flair und GLiNER
werden über Fakes (`tests/conftest.py`, autouse-Fixtures) ersetzt und
prüfen nur die Integrationslogik (Presidio-Verdrahtung, Titel-Merge,
Anonymizer-Ersetzung, Checksummen), nicht die NER-Erkennungsqualität
selbst. Für einen echten End-to-End-Test mit den echten Modellen:
`scripts/prefetch_models.py` ausführen, dann manuell mit realistischen
Testsätzen prüfen.

## Bekannte Grenzen

- Presidios eingebauter Deutsch-Support (Kontextwörter, Standard-Recognizer)
  ist schwächer als für Englisch — deshalb hier bewusst eine eigene,
  minimale Registry statt der Presidio-Standardkonfiguration.
- `CH_AHV_NR`/`CH_UID`/`IBAN_CODE` sind hart über Prüfziffern validiert
  (keine Heuristik) — sehr wenige falsch-positive Treffer, dafür werden
  Zahlenfolgen mit falscher Prüfziffer bewusst nicht gemeldet. `CH_LOCATION`
  ist analog hart über das amtliche PLZ-Verzeichnis validiert (s.u.).
- Automatische Filterung ist eine Vorstufe, kein Ersatz für menschliche
  Prüfung vor Cloud-Übertragung sensibler Inhalte.
- `ORGANIZATION` (GLiNER, Zero-Shot) ist anders als die Prüfziffer-Recognizer
  eine Wahrscheinlichkeitsschätzung — kein hartes Validierungskriterium wie
  bei `CH_AHV_NR`/`IBAN_CODE`. Höheres Recall-Potenzial, aber auch höheres
  Risiko für Fehltreffer bei ungewöhnlichen Firmennamen.
- Die Titel-Erkennung deckt gängige DACH-Titel ab (`Dr.`, `Prof.`, `Mag.`,
  `lic. iur.`, `Dipl.-Ing.`, ...), ist aber eine feste Liste, keine
  Freitext-Erkennung — seltene/ausländische Titel werden nicht erfasst.
- `CH_ADDRESS` bleibt eine reine Struktur-Heuristik (Strassen-Suffix +
  Hausnummer), keine Katalog-Validierung — Postfach-/Gebäude-Adressen ohne
  Strassen-Suffix im Namen werden nicht erfasst, mehrspaltige PDF-Layouts
  können Strasse/PLZ/Ort beim Extrahieren auseinanderreissen.
- `CH_LOCATION`-Regex-Kandidaten decken nur bis zu zwei durchgehend
  grossgeschriebene Wörter ab (z.B. nicht kantons-disambiguierte Namen wie
  "St-Sulpice VD", da "VD" komplett grossgeschrieben ist) — echte
  Doppelnamen mit Bindestrich (z.B. "Chavannes-près-Renens") funktionieren.
- Das amtliche Ortschaftenverzeichnis (swisstopo) deckt nur Orte mit
  fester geografischer Zuordnung ab — generische Sammel-/Postfach-PLZ ohne
  eigene Ortschaft (z.B. "3000"/"3003 Bern", "4000 Basel", "8000 Zürich",
  "6000 Luzern" — üblich in Behörden-/Geschäftskorrespondenz) fehlen im
  Datensatz und werden deshalb **nicht** als `CH_LOCATION` erkannt, obwohl
  sie gültige Adressen sind. Ein Fallback über "häufigster Ortsname im
  PLZ-Hunderterblock" wurde geprüft und wieder verworfen: die Dominanz
  schwankt stark (z.B. Zürich/Basel >75 % im eigenen Block, Bern/Luzern nur
  ~10-17 %, weil deren Blöcke viele Nachbargemeinden mitabdecken) — zu
  unzuverlässig für eine harte Validierung. Bis eine bessere Quelle
  (z.B. Die Post führt separat ein eigenes `PLZ_Verzeichnis`, das diese
  Sammelcodes evtl. abdeckt) eingebunden ist, bleibt das eine bekannte
  Lücke zugunsten von Präzision statt Recall.
- Das amtliche PLZ-Verzeichnis (`data/ch_plz.json`) ist eine Momentaufnahme
  (Stand: manueller Download von swisstopo) und wird nicht automatisch
  aktualisiert — bei Gemeindefusionen o.ä. `scripts/build_ch_plz_data.py`
  mit einer neuen swisstopo-CSV erneut ausführen. Lizenzbedingungen der
  swisstopo-Daten vor einer Weiterverbreitung des Pakets prüfen.
