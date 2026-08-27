import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swiss_pii_anonymizer.checksums import (
    ch_uid_check_digit,
    ean13_check_digit,
    iban_mod97_valid,
    is_valid_ahv,
    is_valid_ch_uid,
)


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


def test_ch_uid_valid_known_examples():
    # Real, öffentlich bekannte UIDs (Beispiele aus diversen CH-Validator-Testsuiten)
    assert is_valid_ch_uid("CHE-116.281.710")
    assert is_valid_ch_uid("CHE-109.322.551")


def test_ch_uid_computed_checksum_roundtrip():
    base = "12345678"
    full = base + str(ch_uid_check_digit(base))
    formatted = f"CHE-{full[0:3]}.{full[3:6]}.{full[6:9]}"
    assert is_valid_ch_uid(formatted)


def test_ch_uid_invalid_checksum():
    assert not is_valid_ch_uid("CHE-116.281.711")


def test_ch_uid_wrong_length():
    assert not is_valid_ch_uid("CHE-116.281")
