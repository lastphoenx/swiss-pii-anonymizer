"""Satzgrenzen-bewusster Text-Chunker für Flair/GLiNER.

Ausgelöst durch einen realen Fehler auf einem echten PDF-Angebotsdokument:
Presidios eingebauter `CharacterBasedTextChunker` verlängert nur das ENDE
eines Chunks bis zur nächsten Wortgrenze (Leerzeichen/Zeilenumbruch) — die
START-Position des NÄCHSTEN Chunks (`end - chunk_overlap`) wird dabei
NICHT an eine Wortgrenze angepasst und kann mitten in einem Wort landen.
Beobachtetes Symptom auf echtem Text: `"Ser[ORGANIZATION]"` statt
`"Service"`, `"Individualso[ORGANIZATION]"` statt `"Individualsoftware"` —
das Modell bekam den zweiten Wortteil als eigenen, isolierten Chunk-Anfang
serviert und hat daraus eine "Entität" gemacht.

`SentenceAwareTextChunker` behebt das: sowohl Start als auch Ende eines
Chunks werden auf eine Wortgrenze gezogen (nie mitten im Wort), und wenn
im Suchfenster um die Ziel-Chunkgrösse eine Satzgrenze (`. ! ?` gefolgt
von Leerzeichen) existiert, wird dort bevorzugt geschnitten — mehr
zusammenhängender Kontext pro Chunk als bei einem harten
Zeichen-Cutoff, was besonders für PERSON-Erkennung relevant ist (NER
verwechselt generische Substantive eher mit Namen, wenn der Satzkontext
mitten im Satz abreisst).

Chunk-Grössen bewusst moderat gehalten: `flair/ner-german-large` basiert
auf `xlm-roberta-large`, dessen Transformer-Positionsembeddings (wie bei
der gesamten RoBERTa-Familie) bei 512 Tokens enden — ein Chunk, der dieses
Limit überschreitet, würde vom Modell intern stillschweigend abgeschnitten
(genau das Kontext-Verlust-Problem, das wir eigentlich lösen wollen), ohne
dass wir das an unseren Chunk-Grenzen sehen würden. Bei grob 4-6 Zeichen
pro Subword-Token im Deutschen bleibt ~2000-2500 Zeichen ein sicherer
Rahmen; deutlich höher zu gehen ist kontraproduktiv.
"""
from __future__ import annotations

import re
from typing import List, Optional

from presidio_analyzer.chunkers import BaseTextChunker, TextChunk

_SENTENCE_END_RE = re.compile(r"[.!?][\"'\)\]]?(?=\s|$)")
_WORD_BOUNDARY_CHARS = (" ", "\n", "\t")


class SentenceAwareTextChunker(BaseTextChunker):
    """Chunkt an Satzgrenzen wenn möglich, sonst an Wortgrenzen — nie mitten im Wort."""

    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200, lookahead: int = 300):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and less than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._lookahead = lookahead

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def chunk_overlap(self) -> int:
        return self._chunk_overlap

    @staticmethod
    def _boundary_at_or_after(text: str, pos: int) -> int:
        n = len(text)
        while pos < n and text[pos] not in _WORD_BOUNDARY_CHARS:
            pos += 1
        return pos

    @staticmethod
    def _boundary_at_or_before(text: str, pos: int) -> int:
        while pos > 0 and text[pos - 1] not in _WORD_BOUNDARY_CHARS:
            pos -= 1
        return pos

    def _find_sentence_end(self, text: str, target: int) -> Optional[int]:
        window_start = max(0, target - self._lookahead)
        window_end = min(len(text), target + self._lookahead)
        best: Optional[int] = None
        for m in _SENTENCE_END_RE.finditer(text, window_start, window_end):
            candidate = m.end()
            if best is None or abs(candidate - target) < abs(best - target):
                best = candidate
        return best

    def chunk(self, text: str) -> List[TextChunk]:
        if not text:
            return []

        chunks: List[TextChunk] = []
        n = len(text)
        start = 0

        while start < n:
            target = min(start + self._chunk_size, n)
            if target >= n:
                end = n
            else:
                end = self._find_sentence_end(text, target)
                if end is None:
                    end = self._boundary_at_or_after(text, target)
                end = min(end, n)

            chunks.append(TextChunk(text=text[start:end], start=start, end=end))
            if end >= n:
                break

            naive_next = max(start + 1, end - self._chunk_overlap)
            next_start = self._boundary_at_or_after(text, naive_next)
            if next_start >= end:
                # Keine Wortgrenze zwischen naive_next und Chunk-Ende gefunden
                # (sehr kurzes/zusammenhängendes letztes Wort) -> davor suchen.
                next_start = self._boundary_at_or_before(text, naive_next)
            start = max(start + 1, next_start)

        return chunks
