"""Prüfziffer-Validierung für strukturierte Identifikatoren (AHV-Nr., IBAN)."""
from __future__ import annotations

import re

_DIGITS_RE = re.compile(r"\D+")


def _digits_only(value: str) -> str:
    return _DIGITS_RE.sub("", value)


def ean13_check_digit(twelve_digits: str) -> int:
    """EAN-13-Prüfziffer über die ersten 12 Ziffern (alternierend Gewicht 1/3)."""
    if len(twelve_digits) != 12 or not twelve_digits.isdigit():
        raise ValueError("Erwarte genau 12 Ziffern.")
    total = 0
    for i, ch in enumerate(twelve_digits):
        weight = 1 if i % 2 == 0 else 3
        total += int(ch) * weight
    return (10 - (total % 10)) % 10


def is_valid_ahv(value: str) -> bool:
    """Schweizer AHV-Nr./Sozialversicherungsnummer: 756.NNNN.NNNN.NC (13 Ziffern, EAN-13-Prüfziffer)."""
    digits = _digits_only(value)
    if len(digits) != 13 or not digits.startswith("756"):
        return False
    try:
        expected = ean13_check_digit(digits[:12])
    except ValueError:
        return False
    return expected == int(digits[12])


def iban_mod97_valid(value: str) -> bool:
    """ISO 7064 MOD 97-10 — Standard-IBAN-Prüfsumme (länderunabhängig)."""
    iban = re.sub(r"\s+", "", value or "").upper()
    if len(iban) < 15 or len(iban) > 34:
        return False
    if not iban[:2].isalpha() or not iban[2:4].isdigit():
        return False
    if not iban[4:].isalnum():
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False
