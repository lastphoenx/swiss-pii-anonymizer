import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from presidio_analyzer import RecognizerResult

from swiss_pii_anonymizer.denylist import filter_generic_person_terms, is_generic_term


def test_known_generic_terms_recognized():
    for word in ["Kunden", "Mitarbeitende", "Administrierende", "Nutzende", "Menschen"]:
        assert is_generic_term(word), word


def test_gender_star_and_colon_normalized():
    assert is_generic_term("Kund*innen")
    assert is_generic_term("Kund:innen")
    assert is_generic_term("Mitarbeiter*innen")


def test_case_insensitive():
    assert is_generic_term("mitarbeitende")
    assert is_generic_term("MITARBEITENDE")


def test_real_surname_not_flagged():
    for word in ["Kaiser", "Weber", "Fuchs", "Koch", "Schäfer", "Bäcker", "Ende", "Maria Muster"]:
        assert not is_generic_term(word), word


def test_filter_removes_only_generic_person_results():
    text = "Kontakt: Maria Muster und Mitarbeitende, Firma: Beispiel AG."
    results = [
        RecognizerResult(entity_type="PERSON", start=text.index("Maria Muster"), end=text.index("Maria Muster") + len("Maria Muster"), score=0.9),
        RecognizerResult(entity_type="PERSON", start=text.index("Mitarbeitende"), end=text.index("Mitarbeitende") + len("Mitarbeitende"), score=0.8),
        RecognizerResult(entity_type="ORGANIZATION", start=text.index("Beispiel AG"), end=text.index("Beispiel AG") + len("Beispiel AG"), score=0.9),
    ]
    filtered = filter_generic_person_terms(text, results)
    kept = [(r.entity_type, text[r.start : r.end]) for r in filtered]
    assert ("PERSON", "Maria Muster") in kept
    assert ("ORGANIZATION", "Beispiel AG") in kept
    assert not any(t == "PERSON" and s == "Mitarbeitende" for t, s in kept)


def test_filter_ignores_non_person_entities_even_if_text_matches():
    text = "Kunden-Nr. 4711"
    results = [
        RecognizerResult(entity_type="ORGANIZATION", start=0, end=6, score=0.9),  # "Kunden"
    ]
    filtered = filter_generic_person_terms(text, results)
    assert filtered == results
