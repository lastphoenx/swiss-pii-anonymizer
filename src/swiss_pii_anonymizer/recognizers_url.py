"""URL/Domain-Recognizer — Wrapper um Presidios eingebauten `UrlRecognizer`.

Presidios "Non schema URL"-Pattern (erkennt z.B. "appswithlove.com" ohne
`https://`-Präfix) kollidiert mit E-Mail-Adressen: der Teil vor dem "@"
kann zufällig wie eine eigene Domain aussehen, wenn er auf eine echte TLD
endet (z.B. "peter.be" in "peter.beispiel@example.com", weil ".be" eine
gültige Landes-TLD ist — verifiziert, kein hypothetisches Problem).
`SafeUrlRecognizer` verwirft deshalb Treffer, deren umgebendes
zusammenhängendes Token (bis zum nächsten Leerzeichen) ein "@" enthält —
das ist dann Teil einer E-Mail-Adresse, für die bereits EMAIL_ADDRESS
zuständig ist.
"""
from __future__ import annotations

from typing import List, Optional

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts
from presidio_analyzer.predefined_recognizers import UrlRecognizer


class SafeUrlRecognizer(UrlRecognizer):
    """UrlRecognizer, der Treffer verwirft, die eigentlich Teil einer E-Mail-Adresse sind."""

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: Optional[NlpArtifacts] = None
    ) -> List[RecognizerResult]:
        results = super().analyze(text=text, entities=entities, nlp_artifacts=nlp_artifacts)
        filtered = []
        for r in results:
            start = r.start
            while start > 0 and not text[start - 1].isspace():
                start -= 1
            end = r.end
            while end < len(text) and not text[end].isspace():
                end += 1
            if "@" in text[start:end]:
                continue
            filtered.append(r)
        return filtered
