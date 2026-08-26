from swiss_pii_anonymizer import anonymize


def test_names_redacted_as_whole_units(fake_flair):
    text = "Das Projekt wurde von Maria Muster vorgeschlagen und von Peter Meier geprueft."
    r = anonymize(text)
    assert "Maria Muster" not in r.text
    assert "Peter Meier" not in r.text
    assert r.text == "Das Projekt wurde von [PERSON] vorgeschlagen und von [PERSON] geprueft."


def test_product_name_not_falsely_redacted(fake_flair):
    text = "Die Loesung heisst Digitaler Sportpass und betrifft Neue Anmeldung."
    r = anonymize(text)
    assert r.text == text
    assert r.findings == []


def test_phone_and_person_combined(fake_flair):
    text = "Ansprechpartnerin Anna Keller, Tel. 044 555 66 77."
    r = anonymize(text)
    assert "Anna Keller" not in r.text
    assert "044 555 66 77" not in r.text
    types = {f.entity_type for f in r.findings}
    assert types == {"PERSON", "CH_PHONE_NUMBER"}


def test_ahv_and_iban_redacted(fake_flair):
    text = "AHV-Nr. 756.1234.5678.97. IBAN CH93 0076 2011 6238 5295 7."
    r = anonymize(text)
    assert "756.1234.5678.97" not in r.text
    assert "CH93 0076 2011 6238 5295 7" not in r.text
    types = {f.entity_type for f in r.findings}
    assert types == {"CH_AHV_NR", "IBAN_CODE"}


def test_budget_figure_not_treated_as_pii(fake_flair):
    text = "Budget 2027: CHF 850'000."
    r = anonymize(text)
    assert r.text == text


def test_analyze_only_no_mutation(fake_flair):
    text = "Kontakt Maria Muster."
    findings = None
    from swiss_pii_anonymizer import analyze

    findings = analyze(text)
    assert any(f.entity_type == "PERSON" and f.text == "Maria Muster" for f in findings)
