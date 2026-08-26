import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swiss_pii_anonymizer.checksums import ean13_check_digit, iban_mod97_valid, is_valid_ahv


def test_ahv_valid_checksum():
    base = "756123456789"
    c = ean13_check_digit(base)
    assert is_valid_ahv(f"756.1234.5678.9{c}")


def test_ahv_invalid_checksum():
    assert not is_valid_ahv("756.0000.0000.00")


def test_ahv_wrong_prefix():
    assert not is_valid_ahv("999.1234.5678.90")


def test_iban_valid_ch():
    assert iban_mod97_valid("CH93 0076 2011 6238 5295 7")


def test_iban_valid_de():
    assert iban_mod97_valid("DE89 3704 0044 0532 0130 00")


def test_iban_invalid_checksum():
    assert not iban_mod97_valid("CH93 0076 2011 6238 5295 8")


def test_iban_too_short():
    assert not iban_mod97_valid("CH93")
