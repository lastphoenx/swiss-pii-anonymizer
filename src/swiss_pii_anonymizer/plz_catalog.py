"""Lookup gegen das amtliche Schweizer Ortschaftenverzeichnis (PLZ -> Ortsnamen).

Quelle: Bundesamt für Landestopografie (swisstopo), "Amtliches
Ortschaftenverzeichnis mit Postleitzahl und Perimeter" (PLZO). Die
kompakte Zuordnung liegt vorverarbeitet in `data/ch_plz.json`
(erzeugt via `scripts/build_ch_plz_data.py`) — kein Netzwerkzugriff zur
Laufzeit nötig.

Damit wird `CH_LOCATION` hart gegen echte Daten validiert statt gegen eine
reine "4 Ziffern + grossgeschriebenes Wort"-Heuristik — dieselbe
Philosophie wie bei `CH_AHV_NR`/`CH_UID` (Prüfziffer statt Vermutung), nur
per Lookup statt Prüfziffer.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DATA_PATH = Path(__file__).resolve().parent / "data" / "ch_plz.json"
_catalog: Optional[Dict[str, List[str]]] = None


def _normalize(name: str) -> str:
    return " ".join(name.split()).casefold()


def _load() -> Dict[str, List[str]]:
    global _catalog
    if _catalog is None:
        try:
            _catalog = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            _catalog = {}
    return _catalog


def known_names_for_plz(plz: str) -> List[str]:
    """Bekannte Ortschafts-/Gemeindenamen für eine 4-stellige PLZ (leer, wenn unbekannt)."""
    return _load().get(plz, [])


def is_known_ch_location(plz: str, name: str) -> bool:
    """True, wenn `name` im amtlichen Verzeichnis als Ortschaft/Gemeinde zu `plz` geführt wird."""
    candidates = known_names_for_plz(plz)
    if not candidates:
        return False
    target = _normalize(name)
    return any(_normalize(c) == target for c in candidates)
