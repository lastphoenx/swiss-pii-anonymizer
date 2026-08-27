#!/usr/bin/env python3
"""Baut src/swiss_pii_anonymizer/data/ch_plz.json aus dem amtlichen Ortschaftenverzeichnis.

Quelle: Bundesamt für Landestopografie (swisstopo), "Amtliches
Ortschaftenverzeichnis mit Postleitzahl und Perimeter" (PLZO), monatlich
aktualisiert. Download (CSV, beliebiges Koordinatensystem — wir nutzen nur
Namensspalten, keine Koordinaten):

    https://www.swisstopo.admin.ch/de/amtliches-ortschaftenverzeichnis
    -> "ortschaftenverzeichnis_plz_2056.csv.zip" (oder _4326, egal)

Dieses Skript liest die entpackte CSV (Semikolon-getrennt, UTF-8-BOM,
Spalten u.a. Ortschaftsname/PLZ4/Gemeindename) und schreibt eine kompakte
PLZ -> [Namen]-Zuordnung (Ortschaftsname + Gemeindename, dedupliziert) als
JSON. Damit läuft die Erkennung offline, ohne bei jedem Import die
Rohdaten neu zu parsen.

Verwendung:
    python scripts/build_ch_plz_data.py /pfad/zu/AMTOVZ_CSV_LV95.csv

Bei einer neuen swisstopo-Veröffentlichung: Datei neu herunterladen,
Skript erneut laufen lassen, `data/ch_plz.json` committen.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_OUTPUT = Path(__file__).resolve().parents[1] / "src" / "swiss_pii_anonymizer" / "data" / "ch_plz.json"


def build(csv_path: Path) -> dict[str, list[str]]:
    plz_to_names: dict[str, set[str]] = defaultdict(set)
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            plz = (row.get("PLZ4") or "").strip()
            if not plz or not plz.isdigit() or len(plz) != 4:
                continue
            for key in ("Ortschaftsname", "Gemeindename"):
                name = (row.get(key) or "").strip()
                if name:
                    plz_to_names[plz].add(name)
    return {plz: sorted(names) for plz, names in sorted(plz_to_names.items())}


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Verwendung: {sys.argv[0]} <pfad-zur-AMTOVZ-csv>", file=sys.stderr)
        raise SystemExit(2)

    csv_path = Path(sys.argv[1])
    data = build(csv_path)

    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"{len(data)} PLZ -> {_OUTPUT} ({_OUTPUT.stat().st_size:,} Bytes)")


if __name__ == "__main__":
    main()
