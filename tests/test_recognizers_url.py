import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swiss_pii_anonymizer.recognizers_url import SafeUrlRecognizer


def test_finds_bare_domain():
    rec = SafeUrlRecognizer(supported_language="de")
    text = "Weitere Infos unter appswithlove.com."
    results = rec.analyze(text, ["URL"], None)
    matched = [text[r.start : r.end] for r in results]
    assert "appswithlove.com" in matched


def test_finds_url_with_scheme():
    rec = SafeUrlRecognizer(supported_language="de")
    text = "Siehe https://www.appswithlove.com/referenzen für Details."
    results = rec.analyze(text, ["URL"], None)
    matched = [text[r.start : r.end] for r in results]
    assert any("appswithlove.com" in m for m in matched)


def test_does_not_match_inside_email_address():
    # Regression: Presidios "Non schema URL"-Pattern matcht sonst faelschlich
    # "peter.be" aus "peter.beispiel@example.com", weil ".be" eine gueltige
    # Landes-TLD ist -- verifiziert, kein hypothetisches Problem.
    rec = SafeUrlRecognizer(supported_language="de")
    text = "Mail: peter.beispiel@example.com"
    results = rec.analyze(text, ["URL"], None)
    assert results == []


def test_does_not_match_email_domain_separately():
    rec = SafeUrlRecognizer(supported_language="de")
    text = "Kontakt: hans.mueller@appswithlove.com"
    results = rec.analyze(text, ["URL"], None)
    assert results == []
