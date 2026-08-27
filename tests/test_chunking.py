import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swiss_pii_anonymizer.chunking import SentenceAwareTextChunker

_BOUNDARY = (" ", "\n", "\t")


def _starts_mid_word(text: str, start: int) -> bool:
    if start == 0 or text[start] in _BOUNDARY:
        return False
    return text[start - 1] not in _BOUNDARY


def test_never_splits_a_word_across_chunks():
    # Regression: der Presidio-Standard-Chunker liess bei diesem Text ein
    # abgetrenntes "n" (Rest von "massgeschneiderten") allein am
    # Chunk-Anfang stehen -- genau das Muster, das auf echtem PDF-Text zu
    # "Ser[ORGANIZATION]" statt "Service" führte.
    text = (
        "Wir sind spezialisiert auf die Entwicklung von massgeschneiderten "
        "Individualsoftware und Services fuer unsere Kunden seit vielen "
        "Jahren erfolgreich am Markt taetig."
    )
    chunker = SentenceAwareTextChunker(chunk_size=70, chunk_overlap=20, lookahead=10)
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    assert all(not _starts_mid_word(text, c.start) for c in chunks)


def test_full_coverage_no_gaps():
    text = "Satz eins ist hier. Satz zwei folgt gleich danach. Und ein dritter Satz."
    chunker = SentenceAwareTextChunker(chunk_size=30, chunk_overlap=10, lookahead=10)
    chunks = chunker.chunk(text)
    for a, b in zip(chunks, chunks[1:]):
        assert b.start <= a.end
    assert chunks[-1].end == len(text)


def test_prefers_sentence_boundary_when_available():
    text = "Erster Satz endet hier. Zweiter Satz beginnt sofort danach und ist länger."
    chunker = SentenceAwareTextChunker(chunk_size=25, chunk_overlap=5, lookahead=15)
    chunks = chunker.chunk(text)
    assert chunks[0].text.rstrip() == "Erster Satz endet hier."


def test_single_chunk_for_short_text():
    text = "Kurzer Text."
    chunker = SentenceAwareTextChunker(chunk_size=2000, chunk_overlap=200)
    chunks = chunker.chunk(text)
    assert len(chunks) == 1
    assert chunks[0].start == 0
    assert chunks[0].end == len(text)


def test_empty_text_returns_no_chunks():
    chunker = SentenceAwareTextChunker()
    assert chunker.chunk("") == []


def test_text_without_any_boundary_does_not_crash():
    text = "EinRiesigesWortOhneLeerzeichen" * 20
    chunker = SentenceAwareTextChunker(chunk_size=50, chunk_overlap=10, lookahead=5)
    chunks = chunker.chunk(text)
    assert chunks[-1].end == len(text)


def test_invalid_overlap_rejected():
    import pytest

    with pytest.raises(ValueError):
        SentenceAwareTextChunker(chunk_size=100, chunk_overlap=100)
