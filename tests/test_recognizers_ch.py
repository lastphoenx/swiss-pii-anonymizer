import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swiss_pii_anonymizer.recognizers_ch import ChAhvRecognizer, ChPhoneRecognizer, ChUidRecognizer


def test_ahv_recognizer_finds_valid_and_skips_invalid():
    rec = ChAhvRecognizer()
    text = "Gültig: 756.1234.5678.97. Ungültig: 756.0000.0000.00."
    results = rec.analyze(text, ["CH_AHV_NR"], None)
    matched = [text[r.start : r.end] for r in results]
    assert "756.1234.5678.97" in matched
    assert "756.0000.0000.00" not in matched


def test_phone_recognizer_finds_ch_number():
    rec = ChPhoneRecognizer()
    text = "Bitte anrufen: 044 555 66 77 oder +41 79 123 45 67."
    results = rec.analyze(text, ["CH_PHONE_NUMBER"], None)
    matched = [text[r.start : r.end] for r in results]
    assert len(matched) == 2


def test_phone_recognizer_finds_number_with_parenthetical_trunk_zero():
    rec = ChPhoneRecognizer()
    text = "Kontakt: +41 (0)31 333 01 51."
    results = rec.analyze(text, ["CH_PHONE_NUMBER"], None)
    matched = [text[r.start : r.end] for r in results]
    assert "+41 (0)31 333 01 51" in matched


def test_uid_recognizer_finds_valid_and_skips_invalid():
    rec = ChUidRecognizer()
    text = "Gültig: CHE-116.281.710. Ungültig: CHE-116.281.711."
    results = rec.analyze(text, ["CH_UID"], None)
    matched = [text[r.start : r.end] for r in results]
    assert "CHE-116.281.710" in matched
    assert "CHE-116.281.711" not in matched
