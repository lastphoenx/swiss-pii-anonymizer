"""Presidio-Recognizer, der Flairs deutsches NER-Modell für PERSON-Erkennung nutzt.

Ersetzt/ergänzt spaCys deutlich schwächere deutsche Standard-NER — Flair
(flair/ner-german-large) erreicht F1 92.3 auf CoNLL-03 Deutsch (revidiert)
und unterscheidet Personennamen zuverlässiger von Produktnamen/Komposita
als eine reine Grossschreibungs-Heuristik.

Aus PDFs extrahierter Text landet oft als ein einziger, unsegmentierter
Fliesstext-Block (Bullet-Punkte statt echter Satzzeichen, keine
Zeilenumbrüche) — auf solchem Text degradiert NER-Qualität spürbar, weil
dem Modell die üblichen Satzgrenzen-Signale fehlen. Wir chunken deshalb
über Presidios `CharacterBasedTextChunker` (dieselbe Utility, die
`GLiNERRecognizer` in recognizers_org.py für ORGANIZATION nutzt) — das
begrenzt das "Verwirrungsfenster" pro Vorhersage und ist für kurze Texte
ein No-Op (ein Chunk => direkter Aufruf, unverändertes Verhalten).
"""
from __future__ import annotations

import logging
from typing import List, Optional

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.chunkers import BaseTextChunker, CharacterBasedTextChunker
from presidio_analyzer.nlp_engine import NlpArtifacts

log = logging.getLogger(__name__)

DEFAULT_FLAIR_MODEL = "flair/ner-german-large"
_DEFAULT_CHUNK_SIZE = 2000
_DEFAULT_CHUNK_OVERLAP = 100

# Flair-Tags -> Presidio-Entitätstypen. ORG standardmässig nicht aktiv,
# weil Fachbereichs-/Organisationsnamen in diesem Kontext oft bewusst
# sichtbar bleiben sollen (siehe FlairPersonRecognizer(entities=...)).
_TAG_MAP = {
    "PER": "PERSON",
    "ORG": "ORGANIZATION",
    "LOC": "LOCATION",
}


class FlairPersonRecognizer(EntityRecognizer):
    """Lädt ein Flair-SequenceTagger-Modell lazy und meldet Treffer an Presidio."""

    def __init__(
        self,
        model_name: str = DEFAULT_FLAIR_MODEL,
        entities: Optional[List[str]] = None,
        supported_language: str = "de",
        text_chunker: Optional[BaseTextChunker] = None,
    ):
        self.model_name = model_name
        self._tagger = None
        wanted = entities or ["PERSON"]
        super().__init__(
            supported_entities=wanted,
            name=f"Flair NER ({model_name})",
            supported_language=supported_language,
        )
        self._active_tags = {tag for tag, ent in _TAG_MAP.items() if ent in wanted}
        self.text_chunker = text_chunker or CharacterBasedTextChunker(
            chunk_size=_DEFAULT_CHUNK_SIZE, chunk_overlap=_DEFAULT_CHUNK_OVERLAP
        )

    def load(self) -> None:
        from flair.models import SequenceTagger

        log.info("Lade Flair-Modell %s ...", self.model_name)
        self._tagger = SequenceTagger.load(self.model_name)

    def _predict_chunk(self, chunk_text: str, entities: List[str]) -> List[RecognizerResult]:
        from flair.data import Sentence

        sentence = Sentence(chunk_text)
        self._tagger.predict(sentence)

        results: List[RecognizerResult] = []
        for span in sentence.get_spans("ner"):
            tag = span.tag
            if tag not in self._active_tags:
                continue
            entity_type = _TAG_MAP[tag]
            if entity_type not in entities:
                continue
            results.append(
                RecognizerResult(
                    entity_type=entity_type,
                    start=span.start_position,
                    end=span.end_position,
                    score=min(0.95, float(span.score)),
                    analysis_explanation=None,
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                    },
                )
            )
        return results

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        if self._tagger is None:
            self.load()

        return self.text_chunker.predict_with_chunking(
            text=text,
            predict_func=lambda chunk_text: self._predict_chunk(chunk_text, entities),
        )
