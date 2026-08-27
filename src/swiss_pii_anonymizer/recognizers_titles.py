"""Erweitert PERSON-Treffer um einen direkt vorangestellten Titel.

Presidio/Flair markieren bei "Dr. med. Maria Muster" typischerweise nur
"Maria Muster" als PERSON — der Titel bliebe unredigiert im Text stehen,
obwohl er in Kombination mit dem Namen re-identifizierend wirkt. Diese
Funktion zieht die Startgrenze eines PERSON-Treffers nach links, wenn
direkt davor ein akademischer/beruflicher Titel steht, sodass z.B.
"Prof. Dr. med. Maria Muster" als eine Einheit anonymisiert wird — es
entsteht bewusst kein eigener Entitätstyp, um bestehende Konsumenten
(z.B. SlitProjektHub) nicht mit einem neuen, unerwarteten Fund zu
überraschen.
"""
from __future__ import annotations

import re
from typing import List

from presidio_analyzer import RecognizerResult

_TITLE_TOKEN = (
    r"(?:Prof\.?|PD|Dr\.?|Mag\.?|Ing\.?|MSc|BSc|MA|BA|PhD|habil\."
    r"|med\.|iur\.|phil\.|oec\.|rer\.\s?nat\.|sc\."
    r"|lic\.\s?iur\.|lic\.\s?phil\.|lic\.\s?oec\."
    r"|Dipl\.-?Ing\.|Dipl\.\s?Kfm\.|Dipl\.\s?Volksw\.)"
)
_TITLE_PREFIX_RE = re.compile(r"(?:\b" + _TITLE_TOKEN + r"\s+)+$")


def expand_person_span_with_title(text: str, result: RecognizerResult) -> RecognizerResult:
    """Zieht die Startgrenze eines PERSON-Treffers vor einen direkt davorstehenden Titel."""
    if result.entity_type != "PERSON" or result.start <= 0:
        return result

    match = _TITLE_PREFIX_RE.search(text[: result.start])
    if not match:
        return result

    new_start = match.start()
    if new_start > 0 and text[new_start - 1].isalnum():
        # Treffer wäre mitten in einem Wort — nicht plausibel, ignorieren.
        return result

    return RecognizerResult(
        entity_type=result.entity_type,
        start=new_start,
        end=result.end,
        score=result.score,
        analysis_explanation=result.analysis_explanation,
        recognition_metadata=result.recognition_metadata,
    )


def merge_titles(text: str, results: List[RecognizerResult]) -> List[RecognizerResult]:
    return [expand_person_span_with_title(text, r) for r in results]
