"""Regex+Prüfziffer-Recognizer für Schweizer Identifikatoren (AHV-Nr., Telefon)."""
from __future__ import annotations

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult

from .checksums import is_valid_ahv


class ChAhvRecognizer(PatternRecognizer):
    """Schweizer AHV-Nr./Sozialversicherungsnummer: 756.NNNN.NNNN.NC.

    Nur mit gültiger EAN-13-Prüfziffer (harte Validierung, keine Heuristik) —
    unterscheidet zuverlässig echte AHV-Nummern von zufälligen Ziffernfolgen.
    """

    PATTERNS = [
        Pattern(
            "AHV-Nr. (mit Trennzeichen)",
            r"\b756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}\b",
            0.4,
        ),
    ]
    CONTEXT = ["ahv", "ahv-nr", "ahv-nummer", "sozialversicherungsnummer", "versichertennummer"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "de",
        supported_entity: str = "CH_AHV_NR",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns or self.PATTERNS,
            context=context or self.CONTEXT,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        return is_valid_ahv(pattern_text)


class ChPhoneRecognizer(PatternRecognizer):
    """Schweizer Telefonnummern: +41/0041/0-Präfix, 9 Ziffern, übliche Trennzeichen."""

    PATTERNS = [
        Pattern(
            "CH-Telefon (+41 / 0041 / 0-Präfix)",
            # (?<!\d) statt \b: \b greift nicht vor "+" (kein Wortzeichen-Übergang)
            r"(?<!\d)(?:\+41|0041|0)\s?(?:[1-9]\d)\s?\d{3}\s?\d{2}\s?\d{2}\b",
            0.55,
        ),
    ]
    CONTEXT = ["telefon", "tel", "tel.", "mobile", "natel", "durchwahl", "kontakt"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "de",
        supported_entity: str = "CH_PHONE_NUMBER",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns or self.PATTERNS,
            context=context or self.CONTEXT,
            supported_language=supported_language,
        )
