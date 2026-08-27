"""Regex-Recognizer für Schweizer Postadressen (Strasse+Nr., PLZ+Ort).

Anders als CH_AHV_NR/CH_UID gibt es hier keine Prüfziffer — die Erkennung
stützt sich auf strukturelle Signale (Strassen-Suffix + Hausnummer bzw.
4-stellige PLZ + grossgeschriebener Ortsname), nicht auf eine reine
Grossschreibungs-Heuristik (die Firmennamen fälschlicherweise träfe, siehe
README "Warum nicht nur Regex?"). Das ist trotzdem eine Wahrscheinlichkeits-
schätzung, kein hartes Kriterium — falsch-positive Treffer sind möglich
(z.B. eine Jahreszahl gefolgt von einem grossgeschriebenen Wort).
"""
from __future__ import annotations

import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer

# Presidios PatternRecognizer kompiliert Patterns standardmässig mit
# re.IGNORECASE — das würde hier die Gross/Kleinschreibungs-Prüfung
# aushebeln (z.B. "2021 bis heute" fälschlich als "PLZ + Ort" matchen,
# weil "bis" unter IGNORECASE auch [A-ZÄÖÜ] erfüllt). Deshalb hier explizit
# ohne IGNORECASE kompilieren.
_CASE_SENSITIVE_FLAGS = re.DOTALL | re.MULTILINE

_STREET_SUFFIX = (
    r"(?:strasse|straße|str\.|gasse|weg|platz|allee|ring|quai|rain|halde|matte)"
)


class ChAddressRecognizer(PatternRecognizer):
    """Strasse + Hausnummer, optional gefolgt von ', PLZ Ort'."""

    PATTERNS = [
        Pattern(
            "CH-Adresse (Strasse + Nr., optional PLZ + Ort)",
            r"\b[A-ZÄÖÜ][\wäöüß.-]*" + _STREET_SUFFIX + r"\s+\d{1,4}[a-zA-Z]?\b"
            r"(?:,?\s*\d{4}\s+[A-ZÄÖÜ][a-zäöüß-]+(?:\s+[A-ZÄÖÜ][a-zäöüß-]+)?)?",
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

    Schwächeres Signal als ChAddressRecognizer (kein Strassen-Suffix als
    Anker) — entsprechend niedrigerer Basis-Score, angehoben durch Kontext.
    """

    PATTERNS = [
        Pattern(
            "CH-PLZ + Ort",
            r"\b(?:CH-)?\d{4}\s+[A-ZÄÖÜ][a-zäöüß-]+(?:\s+[A-ZÄÖÜ][a-zäöüß-]+)?\b",
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
