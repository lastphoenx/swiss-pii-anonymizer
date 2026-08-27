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


def test_organization_redacted(fake_flair):
    text = "Rechnungsadresse: Beispiel AG, Musterstrasse 1."
    r = anonymize(text)
    assert "Beispiel AG" not in r.text
    assert "ORGANIZATION" in {f.entity_type for f in r.findings}


def test_title_merged_into_person_span(fake_flair):
    text = "Kontakt: Dr. Maria Muster, Tel. 044 555 66 77."
    r = anonymize(text)
    assert "Dr." not in r.text
    assert "Maria Muster" not in r.text
    person_findings = [f for f in r.findings if f.entity_type == "PERSON"]
    assert person_findings and person_findings[0].text == "Dr. Maria Muster"


def test_chained_titles_merged_into_person_span(fake_flair):
    text = "Prof. Dr. med. Hans Zimmer war anwesend."
    r = anonymize(text)
    assert "Prof." not in r.text
    person_findings = [f for f in r.findings if f.entity_type == "PERSON"]
    assert person_findings and person_findings[0].text == "Prof. Dr. med. Hans Zimmer"


def test_greeting_not_treated_as_title(fake_flair):
    text = "Guten Tag Maria Muster"
    r = anonymize(text)
    assert r.text == "Guten Tag [PERSON]"


def test_de_business_ids_redacted(fake_flair):
    text = "USt-IdNr. DE123456789, Handelsregister HRB 12345."
    r = anonymize(text)
    assert "DE123456789" not in r.text
    assert "HRB 12345" not in r.text
    types = {f.entity_type for f in r.findings}
    assert types == {"DE_VAT_ID", "DE_HANDELSREGISTER"}


def test_ch_uid_redacted(fake_flair):
    text = "Unternehmens-Identifikationsnummer: CHE-116.281.710."
    r = anonymize(text)
    assert "CHE-116.281.710" not in r.text
    assert "CH_UID" in {f.entity_type for f in r.findings}


def test_ch_address_redacted(fake_flair):
    text = "Firmensitz: Landoltstrasse 63, 3007 Bern."
    r = anonymize(text)
    assert "Landoltstrasse 63" not in r.text
    assert "CH_ADDRESS" in {f.entity_type for f in r.findings}


def test_phone_with_parenthetical_trunk_zero_redacted(fake_flair):
    text = "Kontakt: , +41 (0)31 333 01 51."
    r = anonymize(text)
    assert "+41 (0)31 333 01 51" not in r.text
    assert "CH_PHONE_NUMBER" in {f.entity_type for f in r.findings}


def test_long_unsegmented_text_keeps_correct_offsets(fake_flair):
    filler = "Dies ist ein langer Testtext ohne besondere Namen und Orte. " * 40
    assert len(filler) > 2000  # > FlairPersonRecognizer-Chunk-Grösse -> Chunking greift
    text = filler + "Kontakt ist Maria Muster, vielen Dank."
    r = anonymize(text)
    assert "Maria Muster" not in r.text
    assert r.text == filler + "Kontakt ist [PERSON], vielen Dank."
    assert r.text.startswith(filler[:200])  # Filler-Text bleibt unangetastet/unverschoben
