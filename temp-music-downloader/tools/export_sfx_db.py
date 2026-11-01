#!/usr/bin/env python3
"""Copy curated SFX into starwars-db/database/sounds and write the SFX tables.

usage: tools/export_sfx_db.py [path/to/starwars-db]
Writes database/sound_effects.csv and database/sound_effect_entities.csv.
Paths in the table are relative to database/, like image paths.
"""
import csv, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
db = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent) / "database"
out = db / "sounds"
out.mkdir(exist_ok=True)

rows = list(csv.DictReader((ROOT / "data" / "sfx.csv").open(encoding="utf-8")))
links = list(csv.DictReader((ROOT / "data" / "sfx_entities.csv").open(encoding="utf-8")))
table = []
for r in rows:
    src = ROOT / r["file"]
    _, source, stem = r["sfx_id"].split(":")
    name = f"sfx__{source}__{src.name}"
    shutil.copy2(src, out / name)
    table.append({"sfx_id": r["sfx_id"], "title": stem.replace("_", " "), "category": r["category"],
                  "star_wars_analog": r["star_wars_analog"], "essential": r["essential"],
                  "path": f"sounds/{name}", "format": "ogg", "source": r["source"], "license": r["license"]})
for name, cols, data in (("sound_effects.csv", list(table[0]), table),
                         ("sound_effect_entities.csv", ["sfx_id", "entity_id", "relationship"], links)):
    with (db / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(data)
print(f"copied {len(table)} files, {len(links)} links")
