"""Öffentliche API: analyze()/anonymize() für deutschsprachige Texte."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

log = logging.getLogger(__name__)

DEFAULT_ENTITIES = (
    "PERSON",
    "EMAIL_ADDRESS",
    "IBAN_CODE",
    "CH_AHV_NR",
    "CH_PHONE_NUMBER",
    "ORGANIZATION",
    "DE_VAT_ID",
    "DE_HANDELSREGISTER",
    "CH_UID",
    "CH_ADDRESS",
    "CH_LOCATION",
)

_analyzer = None  # lazy Singleton — Modelle nur einmal pro Prozess laden


@dataclass
class Finding:
    entity_type: str
    start: int
    end: int
    text: str
    score: float


@dataclass
class AnonymizeResult:
    text: str
    findings: list[Finding]


def _build_analyzer(flair_model: str, gliner_model: str):
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_analyzer.predefined_recognizers import (
        DeHandelsregisterRecognizer,
        DeVatIdRecognizer,
        EmailRecognizer,
        IbanRecognizer,
    )

    from .nlp_flair import FlairPersonRecognizer
    from .recognizers_address import ChAddressRecognizer, ChLocationRecognizer
    from .recognizers_ch import ChAhvRecognizer, ChPhoneRecognizer, ChUidRecognizer
    from .recognizers_org import build_organization_recognizer

    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "de", "model_name": "de_core_news_lg"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=configuration).create_engine()

    registry = RecognizerRegistry(supported_languages=["de"])
    registry.add_recognizer(EmailRecognizer(supported_language="de"))
    registry.add_recognizer(IbanRecognizer(supported_language="de"))
    registry.add_recognizer(ChAhvRecognizer())
    registry.add_recognizer(ChPhoneRecognizer())
    registry.add_recognizer(ChUidRecognizer())
    registry.add_recognizer(ChAddressRecognizer())
    registry.add_recognizer(ChLocationRecognizer())
    registry.add_recognizer(DeVatIdRecognizer())
    registry.add_recognizer(DeHandelsregisterRecognizer())
    registry.add_recognizer(FlairPersonRecognizer(model_name=flair_model))
    # GLiNER-basierte Organisationserkennung — fällt bei Lade-/Inferenzfehlern
    # (fehlendes Paket, kein Netzwerk beim ersten Modell-Download, ...) still
    # auf "keine ORGANIZATION-Treffer" zurück, statt den ganzen Analyzer zu
    # blockieren (siehe recognizers_org.SafeGLiNERRecognizer).
    registry.add_recognizer(build_organization_recognizer(gliner_model))

    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["de"],
    )


def get_analyzer(flair_model: str = "flair/ner-german-large", gliner_model: str = None):
    """Lazy-Singleton — Flair-/spaCy-/GLiNER-Modelle werden erst beim ersten Aufruf geladen."""
    global _analyzer
    if _analyzer is None:
        from .recognizers_org import DEFAULT_GLINER_MODEL

        _analyzer = _build_analyzer(flair_model, gliner_model or DEFAULT_GLINER_MODEL)
    return _analyzer


def analyze(
    text: str,
    entities: Optional[Iterable[str]] = None,
    language: str = "de",
    score_threshold: float = 0.35,
) -> list[Finding]:
    """Nur Erkennung, keine Veränderung des Texts — z.B. für Vorschau/Bestätigung im UI."""
    if not text or not text.strip():
        return []
    from .recognizers_titles import merge_titles

    analyzer = get_analyzer()
    ents = list(entities) if entities is not None else list(DEFAULT_ENTITIES)
    results = analyzer.analyze(
        text=text,
        entities=ents,
        language=language,
        score_threshold=score_threshold,
    )
    results = merge_titles(text, results)
    return [
        Finding(entity_type=r.entity_type, start=r.start, end=r.end, text=text[r.start : r.end], score=r.score)
        for r in results
    ]


def anonymize(
    text: str,
    entities: Optional[Iterable[str]] = None,
    language: str = "de",
    score_threshold: float = 0.35,
) -> AnonymizeResult:
    """Erkennt PII und ersetzt sie durch `[ENTITY_TYPE]`-Platzhalter."""
    if not text or not text.strip():
        return AnonymizeResult(text=text or "", findings=[])

    from presidio_analyzer import RecognizerResult
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    from .recognizers_titles import merge_titles

    analyzer = get_analyzer()
    ents = list(entities) if entities is not None else list(DEFAULT_ENTITIES)
    raw_results = analyzer.analyze(
        text=text,
        entities=ents,
        language=language,
        score_threshold=score_threshold,
    )
    raw_results = merge_titles(text, raw_results)
    if not raw_results:
        return AnonymizeResult(text=text, findings=[])

    operators = {
        e: OperatorConfig("replace", {"new_value": f"[{e}]"}) for e in ents
    }
    anonymizer = AnonymizerEngine()
    result = anonymizer.anonymize(text=text, analyzer_results=raw_results, operators=operators)

    findings = [
        Finding(entity_type=r.entity_type, start=r.start, end=r.end, text=text[r.start : r.end], score=r.score)
        for r in raw_results
    ]
    return AnonymizeResult(text=result.text, findings=findings)
