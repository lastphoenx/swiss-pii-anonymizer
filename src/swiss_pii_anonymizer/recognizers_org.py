"""Presidio-Recognizer für Organisationen via GLiNER (urchade/gliner_multi_pii-v1).

GLiNER ist ein Zero-Shot-NER-Modell, das Presidio seit 2.2.x über die
eingebaute `GLiNERRecognizer`-Klasse unterstützt. Wir nutzen es gezielt nur
für ORGANIZATION — PERSON bleibt bei Flair (stärker für Deutsch, s.
nlp_flair.py), um Modell-Overlap/Kosten klein zu halten.

Ein Lade- oder Inferenzfehler (fehlendes `gliner`-Paket, kein Netzwerkzugriff
beim ersten Modell-Download, ...) darf nicht den ganzen Analyzer lahmlegen —
Konsumenten wie SlitProjektHub schalten bei JEDER Exception aus
`get_analyzer()`/`anonymize()` in einen kompletten Fallback-Modus (Verlust
von Flair-PERSON und den Prüfziffer-Recognizern, nicht nur ORGANIZATION).
`SafeGLiNERRecognizer` fängt solche Fehler deshalb selbst ab und deaktiviert
nur sich selbst.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts
from presidio_analyzer.predefined_recognizers import GLiNERRecognizer

log = logging.getLogger(__name__)

DEFAULT_GLINER_MODEL = "urchade/gliner_multi_pii-v1"


class SafeGLiNERRecognizer(GLiNERRecognizer):
    """GLiNERRecognizer, dessen Lade-/Inferenzfehler nur ihn selbst abschaltet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unavailable = False

    def load(self) -> None:
        try:
            super().load()
        except Exception:
            log.warning(
                "GLiNER-Modell %s konnte nicht geladen werden — "
                "ORGANIZATION-Erkennung ist für diese Sitzung deaktiviert.",
                self.model_name,
                exc_info=True,
            )
            self._unavailable = True

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: Optional[NlpArtifacts] = None
    ) -> List[RecognizerResult]:
        if self._unavailable:
            return []
        try:
            return super().analyze(text=text, entities=entities, nlp_artifacts=nlp_artifacts)
        except Exception:
            log.warning("GLiNER-Analyse fehlgeschlagen — für diesen Text übersprungen.", exc_info=True)
            return []


def build_organization_recognizer(model_name: str = DEFAULT_GLINER_MODEL) -> SafeGLiNERRecognizer:
    """GLiNER-Recognizer, beschränkt auf ORGANIZATION (deutsches Zero-Shot-Label "organization")."""
    return SafeGLiNERRecognizer(
        model_name=model_name,
        entity_mapping={"organization": "ORGANIZATION"},
        supported_language="de",
        name=f"GLiNER ORGANIZATION ({model_name})",
    )
