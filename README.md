# swiss-pii-anonymizer

PII-Anonymisierung für deutschsprachige Texte, wiederverwendbar über mehrere
interne Tools (z.B. SlitProjektHub) — als eigenständiges Python-Paket, nicht
in eine einzelne Anwendung eingebaut.

Baut auf [Microsoft Presidio](https://microsoft.github.io/presidio/) als
Framework (Analyzer + Anonymizer, Konfidenz-Scoring, austauschbare
Recognizer) und ersetzt Presidios schwache deutsche Standard-NER durch
[Flair](https://github.com/flairNLP/flair) (`flair/ner-german-large`,
F1 92.3 auf CoNLL-03 Deutsch revidiert) für Personennamen. Dazu kommen
eigene, prüfziffer-validierte Recognizer für Schweizer Identifikatoren.

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
| `PERSON` | Flair NER (`flair/ner-german-large`) | |
| `EMAIL_ADDRESS` | Presidio (regex) | |
| `IBAN_CODE` | Presidio (regex + ISO-7064-Prüfsumme) | international, nicht nur CH |
| `CH_AHV_NR` | eigen (regex + EAN-13-Prüfziffer) | Format `756.NNNN.NNNN.NC` |
| `CH_PHONE_NUMBER` | eigen (regex) | `+41`/`0041`/`0`-Präfix |

Weitere Entitäten (Organisation, Ort, IP-Adresse, Kreditkarte, ...) lassen
sich über zusätzliche Presidio-Recognizer ergänzen — siehe
[`docs/analyzer/adding_recognizers.md`](https://microsoft.github.io/presidio/analyzer/adding_recognizers/).

## Installation

```bash
pip install "swiss-pii-anonymizer @ git+https://github.com/lastphoenx/swiss-pii-anonymizer.git"
python -m spacy download de_core_news_lg
```

Das Flair-Modell (`flair/ner-german-large`, ~370 MB) wird beim ersten
Aufruf automatisch von Hugging Face heruntergeladen und lokal
zwischengespeichert (`~/.flair/`). **Auf einem Server ohne
Internetzugang:** `scripts/prefetch_models.py` auf einer Maschine mit
Zugang ausführen und `~/.flair/` + das installierte spaCy-Modell auf den
Zielserver kopieren.

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

Beide Funktionen laden Flair-/spaCy-Modelle lazy beim ersten Aufruf
(Prozess-weites Singleton) — nachfolgende Aufrufe sind schnell.

## Entwicklung

```bash
pip install -e ".[test]"
python -m spacy download de_core_news_lg
pytest
```

Die Tests unter `tests/` laufen ohne Netzwerkzugriff — Flair wird über
einen Fake-Tagger (`tests/conftest.py`) ersetzt und prüft nur die
Integrationslogik (Presidio-Verdrahtung, Anonymizer-Ersetzung,
Checksummen), nicht die NER-Erkennungsqualität selbst. Für einen echten
End-to-End-Test mit dem echten Modell: `scripts/prefetch_models.py`
ausführen, dann manuell mit realistischen Testsätzen prüfen.

## Bekannte Grenzen

- Presidios eingebauter Deutsch-Support (Kontextwörter, Standard-Recognizer)
  ist schwächer als für Englisch — deshalb hier bewusst eine eigene,
  minimale Registry statt der Presidio-Standardkonfiguration.
- `CH_AHV_NR`/`IBAN_CODE` sind hart über Prüfziffern validiert (keine
  Heuristik) — sehr wenige falsch-positive Treffer, dafür werden
  Zahlenfolgen mit falscher Prüfziffer bewusst nicht gemeldet.
- Automatische Filterung ist eine Vorstufe, kein Ersatz für menschliche
  Prüfung vor Cloud-Übertragung sensibler Inhalte.
