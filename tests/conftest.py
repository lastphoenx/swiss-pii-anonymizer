"""Fake-Flair-Tagger für Tests ohne Netzwerkzugriff/Modell-Download."""
import sys
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

KNOWN_NAMES = {
    "Maria Muster": "PER",
    "Peter Meier": "PER",
    "Anna Keller": "PER",
    "Hans Zimmer": "PER",
    # Simuliert einen auf echtem Realtext beobachteten Flair-Fehltreffer
    # (generisches Substantiv fälschlich als PERSON erkannt) für
    # test_denylist_filters_generic_term_from_flair_output.
    "Mitarbeitende": "PER",
}


class _FakeSpan:
    def __init__(self, tag, start, end, score):
        self.tag, self.start_position, self.end_position, self.score = tag, start, end, score


class _FakeSentence:
    def __init__(self, text):
        self.text = text

    def get_spans(self, layer):
        spans = []
        for name, tag in KNOWN_NAMES.items():
            i = self.text.find(name)
            if i >= 0:
                spans.append(_FakeSpan(tag, i, i + len(name), 0.97))
        return spans


class _FakeTagger:
    def predict(self, sentence):
        pass


@pytest.fixture
def fake_flair(monkeypatch):
    """Ersetzt flair.data.Sentence + FlairPersonRecognizer.load durch Fakes.

    Testet die Integrationslogik (Span -> RecognizerResult, Registry-Verdrahtung,
    Anonymizer-Ersetzung) ohne echtes Modell laden zu müssen. Die Qualität der
    eigentlichen NER-Erkennung hängt vom echten flair/ner-german-large-Modell ab
    und wird hier NICHT geprüft — das ist Aufgabe eines separaten, manuell
    laufenden Integrationstests mit Netzwerkzugriff (siehe README).
    """
    import flair.data as flair_data
    from swiss_pii_anonymizer.nlp_flair import FlairPersonRecognizer

    monkeypatch.setattr(flair_data, "Sentence", _FakeSentence)
    monkeypatch.setattr(FlairPersonRecognizer, "load", lambda self: setattr(self, "_tagger", _FakeTagger()))

    from swiss_pii_anonymizer import engine

    engine._analyzer = None
    yield
    engine._analyzer = None


KNOWN_ORGS = {"Beispiel AG", "Muster GmbH"}


class _FakeGliner:
    def predict_entities(self, text, labels, flat_ner=True, threshold=0.3, multi_label=False):
        preds = []
        for name in KNOWN_ORGS:
            i = text.find(name)
            if i >= 0:
                preds.append({"label": "organization", "start": i, "end": i + len(name), "score": 0.9, "text": name})
        return preds


@pytest.fixture(autouse=True)
def fake_gliner(monkeypatch):
    """Ersetzt SafeGLiNERRecognizer.load durch einen Fake — kein Netzwerkzugriff/Modell-Download.

    Autouse, damit KEIN Test versehentlich versucht, das echte GLiNER-Modell
    von Hugging Face zu laden (langsam/netzwerkabhängig). Deckt zusammen mit
    `fake_flair` die komplette Registry ab, ohne dass jeder Test beide
    Fixtures einzeln anfordern muss.
    """
    from swiss_pii_anonymizer.recognizers_org import SafeGLiNERRecognizer

    monkeypatch.setattr(SafeGLiNERRecognizer, "load", lambda self: setattr(self, "gliner", _FakeGliner()))

    from swiss_pii_anonymizer import engine

    engine._analyzer = None
    yield
    engine._analyzer = None
