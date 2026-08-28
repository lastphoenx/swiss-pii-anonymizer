"""Filtert bekannte generische deutsche Substantive aus PERSON-Treffern.

Deutsche Partizip-I-Nominalisierungen ("Mitarbeitende", "Studierende",
"Reisende", ...) und einige gebräuchliche Kollektiv-Substantive ("Kunden",
"Menschen", ...) werden von Flair auf unordentlichem Realtext (PDF-Extrakte
ohne saubere Satzgrenzen) gelegentlich als PERSON erkannt — beobachtet auf
einem echten Angebotsdokument, nicht hypothetisch.

Das ist bewusst eine **explizite Denyliste bekannter, wiederholt
beobachteter Fehltreffer** — kein allgemeines morphologisches Muster
(ein Regex auf "-ende$"/"-enden$" würde z.B. den echten deutschen
Nachnamen "Ende" fälschlich verwerfen). Konservativ statt breit: nur
Wörter, die exakt (nach Normalisierung von Gender-Stern/-Doppelpunkt und
Gross-/Kleinschreibung) in der Liste stehen, werden verworfen — ein Fund
wie "Herr Kaiser" oder "Anna Weber" bleibt unberührt, weil dort mehr als
ein Wort erkannt wurde bzw. das Wort selbst nicht in der Liste steht.
"""
from __future__ import annotations

import re
from typing import List

from presidio_analyzer import RecognizerResult

# Partizip-I-Nominalisierungen (generische Rollen-/Kollektivbezeichnungen,
# grammatikalisch keine Eigennamen) + gebräuchliche Substantive, die in
# Geschäfts-/Ausschreibungstexten regelmässig für "die betreffenden
# Personen" stehen. Nur Grundformen ohne Gender-Stern/-Doppelpunkt — die
# werden vor dem Abgleich entfernt (siehe _normalize).
_GENERIC_TERMS = {
    # Kollektiv-/Rollen-Substantive
    # "kund" zusätzlich zur Grundform: Gender-Stern verschmilzt bei
    # "Kund*innen" mit dem Wortstamm (nicht "Kunden*innen") — nach
    # Entfernen von "*innen" bleibt nur "kund" übrig, nicht "kunden".
    "kunde", "kunden", "kund", "kundin", "kundinnen",
    "mitarbeiter", "mitarbeiterin", "mitarbeiterinnen",
    "mensch", "menschen",
    "nutzer", "nutzern", "nutzerin", "nutzerinnen",
    "anbieter", "anbietern",
    "teilnehmer", "teilnehmern", "teilnehmerin", "teilnehmerinnen",
    "endnutzer", "enduser",
    "fachkraft", "fachkräfte", "führungskraft", "führungskräfte",
    "gruppe", "gruppen", "team", "teams",
    "kandidat", "kandidaten", "kandidatin", "kandidatinnen",
    "bewerber", "bewerbern", "bewerberin", "bewerberinnen",
    "ansprechpartner", "ansprechpartnern", "ansprechpartnerin", "ansprechpartnerinnen",
    "ansprechperson", "ansprechpersonen",
    "person", "personen",
    "vertreter", "vertretern", "vertreterin", "vertreterinnen",
    # Partizip-I-Nominalisierungen ("-end-")
    "mitarbeitende", "mitarbeitenden",
    "nutzende", "nutzenden",
    "administrierende", "administrierenden",
    "studierende", "studierenden",
    "lernende", "lernenden",
    "reisende", "reisenden",
    "teilnehmende", "teilnehmenden",
    "bewerbende", "bewerbenden",
    "auszubildende", "auszubildenden",
    "anbietende", "anbietenden",
    "anwesende", "anwesenden",
    "vorsitzende", "vorsitzenden",
    # Partizip-II-Nominalisierungen ("-t-")
    "interessierte", "interessierten",
    "betroffene", "betroffenen",
    "angestellte", "angestellten",
    "beschäftigte", "beschäftigten",
    "beteiligte", "beteiligten",
    "verantwortliche", "verantwortlichen",
}

_GENDER_MARKER_RE = re.compile(r"[*:_/]innen$", re.IGNORECASE)


def _normalize(word: str) -> str:
    word = word.strip()
    word = _GENDER_MARKER_RE.sub("", word)
    return word.casefold()


def is_generic_term(text: str) -> bool:
    """True, wenn `text` (ein einzelnes Wort) eine bekannte generische Bezeichnung ist."""
    return _normalize(text) in _GENERIC_TERMS


def filter_generic_person_terms(text: str, results: List[RecognizerResult]) -> List[RecognizerResult]:
    """Entfernt PERSON-Treffer, die exakt einem bekannten generischen Substantiv entsprechen.

    Nur einzelne Wörter werden geprüft — ein mehrwortiger Fund wie
    "Herr Kaiser" bleibt unberührt, auch wenn "Kaiser" allein nie in der
    Denyliste stünde.
    """
    filtered = []
    for r in results:
        if r.entity_type == "PERSON" and is_generic_term(text[r.start : r.end]):
            continue
        filtered.append(r)
    return filtered
