"""Regex-Recognizer für Schweizer Postadressen (Strasse+Nr., PLZ+Ort).

`CH_LOCATION` (PLZ + Ort) wird hart gegen das amtliche
Ortschaftenverzeichnis (swisstopo, siehe plz_catalog.py) validiert —
dieselbe "Prüfung statt Vermutung"-Philosophie wie bei
`CH_AHV_NR`/`CH_UID`, nur per Lookup statt Prüfziffer. Ein Regex-Fund, der
keiner echten PLZ+Ort-Kombination entspricht, wird verworfen.

`CH_ADDRESS` (Strasse + Hausnummer) bleibt eine strukturelle Heuristik ohne
Katalog-Validierung: die optionale ", PLZ Ort"-Endung würde sonst bei einem
Nicht-Treffer den GANZEN Fund verwerfen (inkl. des bereits gut verankerten
Strassennamens) — das Risiko einer nicht erkannten echten Adresse wiegt
hier schwerer als ein gelegentlicher Fehltreffer bei der Stadt-Endung.
"""
from __future__ import annotations

import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer

from .plz_catalog import is_known_ch_location

# Presidios PatternRecognizer kompiliert Patterns standardmässig mit
# re.IGNORECASE — das würde hier die Gross/Kleinschreibungs-Prüfung
# aushebeln (z.B. "2021 bis heute" fälschlich als "PLZ + Ort" matchen,
# weil "bis" unter IGNORECASE auch [A-ZÄÖÜ] erfüllt). Deshalb hier explizit
# ohne IGNORECASE kompilieren.
_CASE_SENSITIVE_FLAGS = re.DOTALL | re.MULTILINE

_STREET_SUFFIX = (
    r"(?:strasse|straße|str\.|gasse|weg|platz|allee|ring|quai|rain|halde|matte)"
)

# Schweizer Ortsnamen sind mehrsprachig (DE/FR/IT/RM) — Umlaute und
# französische/italienische Akzente werden hier ausdrücklich zugelassen,
# damit z.B. "Genève" oder "Chavannes-près-Renens" als eine Einheit
# matchen (nicht nur der deutsche Zeichensatz).
_UPPER_CHARS = "A-ZÄÖÜÀÂÇÈÉÊËÎÏÔÙÛŸŒ"
_LOWER_CHARS = "a-zäöüßàâçèéêëîïôùûÿœ'-"
_PROPER_WORD = rf"[{_UPPER_CHARS}][{_LOWER_CHARS}]+"


class ChAddressRecognizer(PatternRecognizer):
    """Strasse + Hausnummer, optional gefolgt von ', PLZ Ort'."""

    PATTERNS = [
        Pattern(
            "CH-Adresse (Strasse + Nr., optional PLZ + Ort)",
            r"\b[A-ZÄÖÜ][\wäöüß.-]*" + _STREET_SUFFIX + r"\s+\d{1,4}[a-zA-Z]?\b"
            rf"(?:,?\s*\d{{4}}\s+{_PROPER_WORD}(?:\s+{_PROPER_WORD})?)?",
            0.5,
        ),
    ]
    CONTEXT = ["adresse", "strasse", "wohnhaft", "sitz", "domizil", "hauptsitz", "niederlassung"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "de",
        supported_entity: str = "CH_ADDRESS",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns or self.PATTERNS,
            context=context or self.CONTEXT,
            supported_language=supported_language,
            global_regex_flags=_CASE_SENSITIVE_FLAGS,
        )


class ChLocationRecognizer(PatternRecognizer):
    """4-stellige PLZ + Ortsname ohne vorangehende Strasse (z.B. reine Absenderzeile).

    Hart validiert gegen das amtliche Ortschaftenverzeichnis (siehe
    plz_catalog.py) — kein Fehltreffer wie "2021 bis heute" oder eine
    beliebige PLZ+Wort-Kombination möglich, nur echte PLZ+Ort-Paare.
    """

    PATTERNS = [
        Pattern(
            "CH-PLZ + Ort",
            rf"\b(?:CH-)?\d{{4}}\s+{_PROPER_WORD}(?:\s+{_PROPER_WORD})?\b",
            0.4,
        ),
    ]
    CONTEXT = ["plz", "ort", "wohnort", "postleitzahl", "adresse", "sitz"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "de",
        supported_entity: str = "CH_LOCATION",
    ):
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns or self.PATTERNS,
            context=context or self.CONTEXT,
            supported_language=supported_language,
            global_regex_flags=_CASE_SENSITIVE_FLAGS,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        digits = re.search(r"\d{4}", pattern_text)
        if not digits:
            return False
        plz = digits.group()
        name = pattern_text[digits.end() :].strip(" ,")
        if not name:
            return False
        return is_known_ch_location(plz, name)
