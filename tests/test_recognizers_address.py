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
