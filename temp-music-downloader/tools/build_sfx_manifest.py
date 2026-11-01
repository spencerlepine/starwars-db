#!/usr/bin/env python3
"""Build data/sfx.csv + data/sfx_entities.csv from the files under sfx/.

Each sound gets a category, the Star Wars sound it can stand in for, its
source and license, and links to starwars-db entities. Rules are keyed on
filename prefixes so new variants of a sound family are picked up
automatically.
"""
import csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SFX = ROOT / "sfx"
DATA = ROOT / "data"
DB = "databank:"

SOURCES = {
    "kenney-sci-fi": ("Kenney Sci-Fi Sounds (kenney.nl), via github.com/Boyquotes/kenney-sci-fi-sounds-for-godot@c094967", "CC0-1.0"),
    "kenney-digital": ("Kenney Digital Audio (kenney.nl), via github.com/Boyquotes/kenney-digital-audio-for-godot@185a77e", "CC0-1.0"),
    "synth": ("Procedurally synthesized by tools/synth_sfx.py (original, no samples)", "CC0-1.0"),
}

# (source, filename regex) -> (category, star_wars_analog, essential, [(entity, relationship)])
RULES = [
    # synthesized signatures
    ("synth", r"lightsaber_hum", "lightsaber", "Lightsaber idle hum (loopable)", "yes",
     [("1-the-phantom-menace:weapons+tech:lightsaber", "evokes")]),
    ("synth", r"lightsaber_(ignite|retract)", "lightsaber", "Lightsaber ignition / retraction", "yes",
     [("1-the-phantom-menace:weapons+tech:lightsaber", "evokes")]),
    ("synth", r"lightsaber_swing", "lightsaber", "Lightsaber swing (doppler whoosh)", "yes",
     [("1-the-phantom-menace:weapons+tech:lightsaber", "evokes")]),
    ("synth", r"lightsaber_clash", "lightsaber", "Lightsaber blade clash", "yes",
     [("1-the-phantom-menace:weapons+tech:lightsaber", "evokes")]),
    ("synth", r"blaster_bolt", "blaster", "Blaster bolt 'pew' (struck guy-wire style)", "yes",
     [("4-a-new-hope:weapons+tech:e-11-blaster-rifle", "evokes"),
      ("4-a-new-hope:weapons+tech:dl-44-blaster-pistol", "evokes")]),
    ("synth", r"blaster_heavy", "blaster", "Heavy blaster / laser cannon", "yes",
     [("4-a-new-hope:weapons+tech:dlt-19-heavy-blaster-rifle", "evokes")]),
    ("synth", r"droid_chatter", "droid", "Astromech droid chatter (R2-D2 style)", "yes",
     [("1-the-phantom-menace:characters:r2-d2", "evokes"),
      ("1-the-phantom-menace:driods:astromech-droid", "evokes")]),
    ("synth", r"droid_scream", "droid", "Astromech droid scream", "yes",
     [("1-the-phantom-menace:characters:r2-d2", "evokes")]),
    ("synth", r"hyperspace", "ship", "Jump to hyperspace", "yes",
     [("1-the-phantom-menace:weapons+tech:hyperdrive", "evokes"),
      ("3-revenge-of-the-sith:vehicles:millennium-falcon", "evokes")]),
    ("synth", r"starfighter_flyby", "ship", "Starfighter fly-by howl (TIE fighter style)", "yes",
     [("4-a-new-hope:vehicles:tie-fighter", "evokes")]),
    # Kenney sci-fi
    ("kenney-sci-fi", r"computer_noise", "ui", "Imperial computer consoles / control room", "no",
     [("3-revenge-of-the-sith:locations:death-star", "evokes")]),
    ("kenney-sci-fi", r"door_(open|close)", "environment", "Sliding blast doors (Death Star, Tantive IV)", "no",
     [("3-revenge-of-the-sith:locations:death-star", "evokes")]),
    ("kenney-sci-fi", r"engine_circular", "vehicle", "Repulsorlift hum (landspeeder, speeder bike)", "no",
     [("4-a-new-hope:vehicles:x-34-landspeeder", "evokes"),
      ("2-attack-of-the-clones:vehicles:speeder-bike", "evokes")]),
    ("kenney-sci-fi", r"explosion_crunch", "explosion", "Starfighter / TIE fighter explosion", "yes",
     [("4-a-new-hope:vehicles:tie-fighter", "evokes"),
      ("4-a-new-hope:vehicles:x-wing-starfighter", "evokes")]),
    ("kenney-sci-fi", r"force_field", "shield", "Deflector shield / energy shield", "no",
     [("1-the-phantom-menace:weapons+tech:gungan-personal-energy-shield", "evokes")]),
    ("kenney-sci-fi", r"impact_metal", "impact", "Bolt hitting hull / droid plating", "no",
     [("1-the-phantom-menace:driods:battle-droid", "evokes")]),
    ("kenney-sci-fi", r"laser_large", "blaster", "Turbolaser / superlaser blast", "yes",
     [("3-revenge-of-the-sith:weapons+tech:death-star-superlaser", "evokes"),
      ("4-a-new-hope:vehicles:imperial-star-destroyer", "evokes")]),
    ("kenney-sci-fi", r"laser_retro", "blaster", "Starfighter laser cannons (X-wing, TIE)", "yes",
     [("4-a-new-hope:vehicles:x-wing-starfighter", "evokes"),
      ("4-a-new-hope:vehicles:tie-fighter", "evokes")]),
    ("kenney-sci-fi", r"laser_small", "blaster", "Blaster pistol / rifle shot", "yes",
     [("4-a-new-hope:weapons+tech:e-11-blaster-rifle", "evokes"),
      ("4-a-new-hope:organizations:stormtroopers", "evokes")]),
    ("kenney-sci-fi", r"low_frequency_explosion", "explosion", "Death Star destruction / big boom", "yes",
     [("3-revenge-of-the-sith:locations:death-star", "evokes")]),
    ("kenney-sci-fi", r"slime", "creature", "Creature squelch (sarlacc, rancor)", "no",
     [("6-return-of-the-jedi:creatures:sarlacc", "evokes")]),
    ("kenney-sci-fi", r"space_engine_large", "ship", "Capital ship engine (Star Destroyer)", "no",
     [("4-a-new-hope:vehicles:imperial-star-destroyer", "evokes")]),
    ("kenney-sci-fi", r"space_engine", "ship", "Starship engine (Millennium Falcon)", "no",
     [("3-revenge-of-the-sith:vehicles:millennium-falcon", "evokes")]),
    ("kenney-sci-fi", r"thruster_fire", "ship", "Starfighter thrusters / afterburner", "no",
     [("4-a-new-hope:vehicles:x-wing-starfighter", "evokes")]),
    # Kenney digital
    ("kenney-digital", r"laser_", "blaster", "Blaster shot (arcade style)", "no",
     [("1-the-phantom-menace:weapons+tech:blaster-pistol", "evokes")]),
    ("kenney-digital", r"phaser_", "blaster", "Ion / droid weapon charge", "no",
     [("1-the-phantom-menace:weapons+tech:ion-blaster", "evokes")]),
    ("kenney-digital", r"zap", "blaster", "Ion cannon / electro zap", "no",
     [("5-the-empire-strikes-back:weapons+tech:ion-cannon", "evokes")]),
    ("kenney-digital", r"(pep_sound|tone_|two_tone|three_tone)", "droid", "Droid beeps / blips", "no",
     [("1-the-phantom-menace:driods:astromech-droid", "evokes")]),
    ("kenney-digital", r"phase_jump", "ship", "Hyperspace jump (short)", "no",
     [("1-the-phantom-menace:weapons+tech:hyperdrive", "evokes")]),
    ("kenney-digital", r"(power_up|high_|low_|space_trash)", "ui", "UI / pickup / menu", "no", []),
]


def main():
    rows, links = [], []
    for src in SOURCES:
        for f in sorted((SFX / src).glob("*.ogg")):
            stem = f.stem
            rule = next((r for r in RULES if r[0] == src and re.match(r[1], stem)), None)
            if rule is None:
                raise SystemExit(f"no rule for {src}/{f.name}")
            _, _, cat, analog, essential, ents = rule
            sid = f"sfx:{src}:{stem}"
            rows.append({
                "sfx_id": sid, "file": f"sfx/{src}/{f.name}", "category": cat,
                "star_wars_analog": analog, "essential": essential,
                "source": SOURCES[src][0], "license": SOURCES[src][1],
            })
            links += [{"sfx_id": sid, "entity_id": DB + e, "relationship": rel} for e, rel in ents]
    for name, cols, data in (("sfx.csv", list(rows[0]), rows),
                             ("sfx_entities.csv", ["sfx_id", "entity_id", "relationship"], links)):
        with (DATA / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(data)
    print(f"sfx={len(rows)} essential={sum(r['essential'] == 'yes' for r in rows)} links={len(links)}")


if __name__ == "__main__":
    main()
