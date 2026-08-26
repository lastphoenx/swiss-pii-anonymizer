"""Fake-Flair-Tagger für Tests ohne Netzwerkzugriff/Modell-Download."""
import sys
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

KNOWN_NAMES = {"Maria Muster": "PER", "Peter Meier": "PER", "Anna Keller": "PER", "Hans Zimmer": "PER"}


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
