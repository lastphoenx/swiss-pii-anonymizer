import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swiss_pii_anonymizer.recognizers_address import ChAddressRecognizer, ChLocationRecognizer


def test_address_recognizer_finds_street_and_number():
    rec = ChAddressRecognizer()
    text = "Firmensitz: Landoltstrasse 63, 3007 Bern."
    results = rec.analyze(text, ["CH_ADDRESS"], None)
    matched = [text[r.start : r.end] for r in results]
    assert "Landoltstrasse 63, 3007 Bern" in matched


def test_address_recognizer_ignores_plain_prose():
    rec = ChAddressRecognizer()
    text = "Wir entwickeln massgeschneiderte Individualsoftware seit 15 Jahren."
    results = rec.analyze(text, ["CH_ADDRESS"], None)
    assert results == []


def test_location_recognizer_finds_plz_and_city():
    rec = ChLocationRecognizer()
    text = "Rechnungsadresse: Petersplatz 1, Postfach, 4001 Basel."
    results = rec.analyze(text, ["CH_LOCATION"], None)
    matched = [text[r.start : r.end] for r in results]
    assert "4001 Basel" in matched


def test_location_recognizer_ignores_year_followed_by_lowercase_word():
    # Regression: Presidio kompiliert Patterns standardmässig mit re.IGNORECASE,
    # was "2021 bis heute" faelschlich wie "PLZ + Ort" aussehen liesse, wenn
    # die Gross/Kleinschreibungs-Pruefung nicht explizit erzwungen wird.
    rec = ChLocationRecognizer()
    text = "Projektlaufzeit: Februar 2021 bis heute, Auszeichnung 2022 gewonnen."
    results = rec.analyze(text, ["CH_LOCATION"], None)
    assert results == []


def test_location_recognizer_rejects_plausible_but_fake_combination():
    # "1234 Wunderland" sieht strukturell wie eine PLZ+Ort-Kombination aus,
    # ist aber keine echte Schweizer Ortschaft -- die Katalog-Validierung
    # (nicht nur Gross/Kleinschreibung) muss das verwerfen.
    rec = ChLocationRecognizer()
    text = "Adresse: 1234 Wunderland."
    results = rec.analyze(text, ["CH_LOCATION"], None)
    assert results == []


def test_location_recognizer_rejects_wrong_city_for_real_plz():
    # 8001 ist eine echte PLZ (Zuerich), aber nicht fuer "Bern".
    rec = ChLocationRecognizer()
    text = "Adresse: 8001 Bern."
    results = rec.analyze(text, ["CH_LOCATION"], None)
    assert results == []


def test_location_recognizer_finds_french_city_name():
    rec = ChLocationRecognizer()
    text = "Adresse: 1201 Genève."
    results = rec.analyze(text, ["CH_LOCATION"], None)
    matched = [text[r.start : r.end] for r in results]
    assert "1201 Genève" in matched


def test_location_recognizer_known_gap_generic_collector_plz():
    # Dokumentierte Grenze (README "Bekannte Grenzen"): generische
    # Sammel-/Postfach-PLZ ohne eigene Ortschaft (z.B. "3003 Bern", übliche
    # Bundesverwaltungs-Adresse) fehlen im amtlichen Ortschaftenverzeichnis
    # und werden deshalb bewusst NICHT erkannt -- Praezision vor Recall.
    # Dieser Test dokumentiert den Status quo, kein gewuenschtes Verhalten.
    rec = ChLocationRecognizer()
    text = "Adresse: 3003 Bern."
    results = rec.analyze(text, ["CH_LOCATION"], None)
    assert results == []
