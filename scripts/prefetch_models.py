#!/usr/bin/env python3
"""Lädt Flair-, spaCy- und GLiNER-Modelle einmalig vor (auf einer Maschine mit Internetzugang).

Danach liegen die Modelle im lokalen Cache (~/.flair, ~/.cache/huggingface,
spaCy-Paket) und `swiss_pii_anonymizer.get_analyzer()` läuft ohne
Netzwerkzugriff.

Für einen Server ohne direkten Internetzugang: dieses Skript auf einer
Maschine mit Zugang ausführen, dann `~/.flair/`, `~/.cache/huggingface/`
und die installierten spaCy-Modell-Pakete (`de_core_news_lg`) auf den
Zielserver kopieren.

Hinweis: Schlägt der GLiNER-Download fehl (kein Netzwerk, Modell noch
nicht gecacht), bleibt der Rest des Analyzers (Flair-PERSON, alle
Regex-/Prüfziffer-Recognizer) trotzdem funktionsfähig — nur die
ORGANIZATION-Erkennung ist dann deaktiviert (siehe
`swiss_pii_anonymizer.recognizers_org.SafeGLiNERRecognizer`).
"""
from __future__ import annotations

import subprocess
import sys


def main() -> None:
    print("Lade spaCy-Modell de_core_news_lg ...")
    subprocess.run([sys.executable, "-m", "spacy", "download", "de_core_news_lg"], check=True)

    print("Lade Flair-Modell flair/ner-german-large ...")
    from flair.models import SequenceTagger

    SequenceTagger.load("flair/ner-german-large")

    print("Lade GLiNER-Modell urchade/gliner_multi_pii-v1 (ORGANIZATION) ...")
    from gliner import GLiNER

    GLiNER.from_pretrained("urchade/gliner_multi_pii-v1")

    print("Fertig. Modelle sind lokal zwischengespeichert.")


if __name__ == "__main__":
    main()
