#!/usr/bin/env python3
"""Lädt Flair- und spaCy-Modelle einmalig vor (auf einer Maschine mit Internetzugang).

Danach liegen die Modelle im lokalen Cache (~/.flair, spaCy-Paket) und
`swiss_pii_anonymizer.get_analyzer()` läuft ohne Netzwerkzugriff.

Für einen Server ohne direkten Internetzugang: dieses Skript auf einer
Maschine mit Zugang ausführen, dann `~/.flair/` und die installierten
spaCy-Modell-Pakete (`de_core_news_lg`) auf den Zielserver kopieren.
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

    print("Fertig. Modelle sind lokal zwischengespeichert.")


if __name__ == "__main__":
    main()
