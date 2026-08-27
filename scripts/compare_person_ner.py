#!/usr/bin/env python3
"""Vergleicht Flair vs. GLiNER auf mehrdeutigen deutschen PERSON-Fällen.

Ausgelöst durch eine Diskussion, ob ein zweites, kontextsensitives Modell
(GLiNER, das wir bereits lokal für ORGANIZATION laufen haben) Flairs
PERSON-Übertriggerung auf generische Substantive ("Kunden",
"Mitarbeitende", "Administrierende") reduzieren könnte — und ob beide
Modelle Nachnamen, die gleichzeitig gebräuchliche Substantive sind
("Kaiser", "Bäcker", "Fuchs", "Koch", "Schäfer", "Weber"), zuverlässig vom
Substantiv unterscheiden.

WICHTIG: Dieses Skript braucht die ECHTEN Modelle (nicht die Fake-Tagger
aus den Tests) und damit entweder Netzwerkzugriff beim ersten Lauf oder
einen bereits gefüllten Modell-Cache (z.B. nach
`scripts/maintenance/prefetch_pii_models.py` auf einem SlitProjektHub-
Server). Es verändert NICHTS an der Paket-Logik — reines Diagnose-Tool,
um die Entscheidung "GLiNER zusätzlich für PERSON nutzen?" mit echten
Daten statt Vermutungen zu treffen.

Verwendung:
    python scripts/compare_person_ner.py
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@dataclass
class Case:
    text: str
    span: str  # exakter Teilstring, der PERSON sein sollte (oder nicht)
    expect_person: bool
    note: str


# Jeweils dasselbe Wort einmal als echter Nachname (PERSON), einmal als
# gewöhnliches Substantiv/Berufsbezeichnung (KEIN PERSON) im Satzkontext.
CASES = [
    Case("Herr Kaiser hat das Projekt termingerecht abgeschlossen.", "Kaiser", True, "Nachname"),
    Case("Der Kaiser regierte über ein riesiges Reich.", "Kaiser", False, "historischer Titel"),
    Case("Frau Bäcker leitet seit 2019 die Niederlassung Basel.", "Bäcker", True, "Nachname"),
    Case("Wir kauften frisches Brot beim Bäcker um die Ecke.", "Bäcker", False, "Berufsbezeichnung"),
    Case("Peter Fuchs war massgeblich an der Entwicklung beteiligt.", "Fuchs", True, "Nachname"),
    Case("Im Wald wurde ein Fuchs gesichtet.", "Fuchs", False, "Tier"),
    Case("Anna Koch verantwortet das Budget für dieses Projekt.", "Koch", True, "Nachname"),
    Case("Der Koch bereitete ein dreigängiges Menü zu.", "Koch", False, "Berufsbezeichnung"),
    Case("Thomas Schäfer koordiniert die Zusammenarbeit mit dem Kunden.", "Schäfer", True, "Nachname"),
    Case("Der Schäfer trieb die Herde über die Weide.", "Schäfer", False, "Berufsbezeichnung"),
    Case("Julia Weber ist die zuständige Ansprechpartnerin.", "Weber", True, "Nachname"),
    Case("Der Weber stellte den Stoff von Hand her.", "Weber", False, "Berufsbezeichnung (veraltet)"),
    Case("Wir begleiten unsere Kunden während des gesamten Projekts.", "Kunden", False, "generisches Substantiv"),
    Case("Alle Mitarbeitende erhalten eine Schulung.", "Mitarbeitende", False, "generisches Substantiv"),
    Case("Die Handhabung ist auch für Administrierende einfach.", "Administrierende", False, "generisches Substantiv"),
    Case("Wir vereinfachen den Menschen das Leben.", "Menschen", False, "generisches Substantiv"),
]


def _load_flair():
    from swiss_pii_anonymizer.nlp_flair import FlairPersonRecognizer

    rec = FlairPersonRecognizer()
    rec.load()
    return rec


def _load_gliner():
    from swiss_pii_anonymizer.recognizers_org import SafeGLiNERRecognizer
    from swiss_pii_anonymizer.chunking import SentenceAwareTextChunker

    rec = SafeGLiNERRecognizer(
        model_name="urchade/gliner_multi_pii-v1",
        entity_mapping={"person": "PERSON"},
        supported_language="de",
        name="GLiNER PERSON (Vergleichsskript)",
        text_chunker=SentenceAwareTextChunker(chunk_size=2000, chunk_overlap=200),
    )
    rec.load()
    return rec


def _person_spans(rec, text: str) -> list[str]:
    results = rec.analyze(text=text, entities=["PERSON"], nlp_artifacts=None)
    return [text[r.start : r.end] for r in results]


def _evaluate(name: str, rec) -> tuple[int, int]:
    print(f"\n=== {name} ===")
    correct = 0
    for case in CASES:
        spans = _person_spans(rec, case.text)
        found = any(case.span in s or s in case.span for s in spans)
        ok = found == case.expect_person
        correct += int(ok)
        mark = "OK" if ok else "FEHLER"
        erwartet = "PERSON" if case.expect_person else "kein PERSON"
        gefunden = spans if spans else "–"
        print(f"[{mark:6}] {case.span!r:16} ({case.note:28}) erwartet={erwartet:12} gefunden={gefunden}")
    print(f"{name}: {correct}/{len(CASES)} korrekt")
    return correct, len(CASES)


def main() -> None:
    print(f"{len(CASES)} Testfälle: je Wort einmal als Nachname (PERSON), einmal als Substantiv (kein PERSON).\n")

    print("Lade Flair (flair/ner-german-large) ...")
    flair_rec = _load_flair()
    flair_correct, total = _evaluate("Flair", flair_rec)

    print("\nLade GLiNER (urchade/gliner_multi_pii-v1, Label 'person') ...")
    gliner_rec = _load_gliner()
    gliner_correct, _ = _evaluate("GLiNER", gliner_rec)

    print("\n=== Zusammenfassung ===")
    print(f"Flair:  {flair_correct}/{total}")
    print(f"GLiNER: {gliner_correct}/{total}")
    print(
        "\nHinweis: Kleine Stichprobe (Handverlesen, nicht repräsentativ) — "
        "als erster Fingerzeig gedacht, nicht als endgültiger Beweis."
    )


if __name__ == "__main__":
    main()
