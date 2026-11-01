#!/usr/bin/env python3
"""Collect original Star Wars film sound effects / voice clips from public
GitHub soundboard and fan projects into the PRIVATE starwars-db repo.

These are Lucasfilm-copyrighted sounds (Ben Burtt's effects, film dialogue).
They are for personal reference only: the audio is written only into
starwars-db (private) and never into this repo, and every row is marked
license=reference-only. Do not ship them in a released game.

usage: tools/collect_original_sfx.py [path/to/starwars-db] [--work DIR]

Steps: shallow/sparse-clone each source, take audio files (skipping music
tracks and anything over 40 s), de-duplicate by content hash, convert to
OGG (q4), categorise by filename, link to entities, and append/replace the
`sfx:original:*` rows in database/sound_effects.csv and
database/sound_effect_entities.csv.
"""
import csv, hashlib, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# repo, sparse path (or None for whole repo), short source name
SOURCES = [
    ("programacionmultimedia/SableLaser-iOS-App", None, "sablelaser"),
    ("karelhala/stor-wars-hackathon21", "/Stor Wars/Assets/Sounds/*", "storwars"),
    ("Jedi-Trainer/UnityProject", "/Assets/Sounds/Lightsaber/*", "jeditrainer"),
    ("Domz444/StarWarsSoundEffects", None, "domz444"),
    ("TomazMazej/star_wars_soundboard", None, "tomazmazej"),
    ("nicholasmclark/Star-Wars-Soundboard", None, "nmclark"),
    ("caleb-eades/StarWarsSoundboard", None, "calebeades"),
    ("perjansson/starwars-android", None, "perjansson"),
    ("MstrBlonde/StarWarsSoundboard", None, "mstrblonde"),
    ("mchorton4/soundboard", None, "mchorton4"),
    ("Futurooooo/StarWarsSoundboard", None, "futurooooo"),
    ("Girateus/TankGame", "/Assets/Audio/tie-fighter-fire-1.mp3", "girateus"),
    ("Prayrena/SD", "/Starship/Run/Data/StarWars/*", "prayrena"),
    ("neoRiley/XLSound_unity", "/Assets/Audio/sfx/xwing_engines_loop_0.wav", "neoriley"),
]
AUDIO = {".wav", ".mp3", ".ogg", ".m4a", ".caf", ".aiff"}
SKIP = re.compile(r"theme|music|cantina|imperialmarch|anthem|flute|jetpack|cicada|hadouryu|"
                  r"kidscheer|ohno|cannon \(1\)|turbine|fan_v|ambience|computer\d|tap|bang", re.I)
# Jedi-Trainer ships 40 near-identical activations; keep a handful
KEEP_LIMIT = {("jeditrainer", "activation"): 5}

# filename keyword -> (category, description)
CATS = [
    (r"sab|saber|light_?saber|espadazo|activation", "lightsaber"),
    (r"blaster|tie-fighter-fire|laser", "blaster"),
    (r"xwing|engine|tie_?fighter", "ship"),
    (r"breath", "vader_breathing"),
    (r"r2|droid", "droid"),
    (r"chew|wook", "wookiee"),
    (r"jabba", "creature"),
    (r"ewok", "creature"),
    (r"wilhelm|scream", "scream"),
    (r"(^|[_-])door", "environment"),
    (r"^force|the_force|_force$", "force"),
]
SABER_KIND = [(r"on|activation", "ignite"), (r"off", "retract"), (r"swg|swing|espadazo", "swing"),
              (r"hit|clash", "clash"), (r"hum|amb", "hum")]
# filename keyword -> entity ids (databank:...)
ENT = {
    r"vader|vbreath|breath|your_?father|dark_side": "3-revenge-of-the-sith:characters:darth-vader",
    r"yoda|do_or|dont_under|underestimate": "1-the-phantom-menace:characters:yoda",
    r"r2": "1-the-phantom-menace:characters:r2-d2",
    r"c3po|your_fault": "1-the-phantom-menace:characters:c-3po",
    r"chew|wook": "3-revenge-of-the-sith:characters:chewbacca",
    r"han": "4-a-new-hope:characters:han-solo",
    r"leia": "3-revenge-of-the-sith:characters:leia-organa",
    r"luke": "3-revenge-of-the-sith:characters:luke-skywalker",
    r"ben_|obiwan|obi_wan": "1-the-phantom-menace:characters:obi-wan-kenobi",
    r"emperor|palpatine": "1-the-phantom-menace:characters:emperor-palpatine-darth-sidious",
    r"anakin": "1-the-phantom-menace:characters:anakin-skywalker",
    r"jabba": "1-the-phantom-menace:characters:jabba-the-hutt",
    r"jarjar": "1-the-phantom-menace:characters:jar-jar-binks",
    r"boba": "2-attack-of-the-clones:characters:boba-fett",
    r"lando": "5-the-empire-strikes-back:characters:lando-calrissian",
    r"ewok": "6-return-of-the-jedi:species:ewok",
    r"sab|saber|espadazo|activation": "1-the-phantom-menace:weapons+tech:lightsaber",
    r"blaster": "4-a-new-hope:weapons+tech:e-11-blaster-rifle",
    r"tie-fighter": "4-a-new-hope:vehicles:tie-fighter",
    r"xwing": "4-a-new-hope:vehicles:x-wing-starfighter",
    r"force": "1-the-phantom-menace:organizations:jedi-order",
}


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def fetch(repo, sparse, dest):
    if dest.exists():
        return
    url = f"https://github.com/{repo}"
    if sparse:
        run("git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", url, str(dest))
        run("git", "-C", str(dest), "sparse-checkout", "set", "--no-cone", sparse)
    else:
        run("git", "clone", "-q", "--depth", "1", url, str(dest))


def duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


CHAR_LINE = re.compile(r"^(yoda|vader|darthvader|leia|luke|han|hansolo|ben|obiwan|c3po|emperor|anakin|lando)[_ -]"
                       r"|^forcestrong$|^your_|^dark_side|^do_or|^dont_")


def classify(stem):
    s = stem.lower()
    if CHAR_LINE.search(s):
        return "dialogue", "Film dialogue / voice clip"
    cat = next((c for pat, c in CATS if re.search(pat, s)), "dialogue")
    if cat == "lightsaber":
        kind = next((k for pat, k in SABER_KIND if re.search(pat, s)), "")
        return cat, f"Lightsaber {kind}".strip()
    desc = {"blaster": "Blaster shot", "ship": "Starfighter engine / cannon", "vader_breathing": "Darth Vader breathing",
            "droid": "R2-D2 / droid vocalisation", "wookiee": "Chewbacca / Wookiee roar", "creature": "Creature / alien voice",
            "scream": "Wilhelm scream", "environment": "Door / environment", "force": "Force sound / Force line"}.get(cat)
    return cat, desc or "Film dialogue / voice clip"


def main():
    args = sys.argv[1:]
    work = None
    if "--work" in args:
        i = args.index("--work")
        work = Path(args[i + 1])
        del args[i:i + 2]
    db = Path(args[0] if args else ROOT.parent) / "database"
    work = work or Path(tempfile.mkdtemp(prefix="swsfx-"))
    out = db / "sounds" / "original"
    out.mkdir(parents=True, exist_ok=True)

    seen, rows, links, counts = set(), [], [], {}
    for repo, sparse, short in SOURCES:
        src = work / repo.replace("/", "__")
        try:
            fetch(repo, sparse, src)
        except subprocess.CalledProcessError as e:
            print(f"skip {repo}: {e.stderr.strip()[:120]}")
            continue
        commit = run("git", "-C", str(src), "rev-parse", "--short", "HEAD").stdout.strip()
        for f in sorted(p for p in src.rglob("*") if p.suffix.lower() in AUDIO and ".git" not in p.parts):
            if SKIP.search(f.name):
                continue
            key = next((k for k in KEEP_LIMIT if k[0] == short and k[1] in f.stem.lower()), None)
            if key:
                counts[key] = counts.get(key, 0) + 1
                if counts[key] > KEEP_LIMIT[key]:
                    continue
            d = duration(f)
            if d is None or d > 40 or d < 0.05:
                continue
            h = hashlib.sha1(f.read_bytes()).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            stem = re.sub(r"[^a-z0-9]+", "-", f.stem.lower()).strip("-")
            name = f"sfx__original__{short}__{stem}.ogg"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-vn", "-c:a", "libvorbis",
                            "-q:a", "4", str(out / name)], check=True)
            cat, desc = classify(f.stem)
            sid = f"sfx:original:{short}-{stem}"
            rows.append({"sfx_id": sid, "title": f.stem.replace("_", " ").replace("-", " "), "category": cat,
                         "star_wars_analog": desc, "essential": "yes" if cat not in ("dialogue",) else "no",
                         "path": f"sounds/original/{name}", "format": "ogg",
                         "source": f"github.com/{repo}@{commit} ({f.relative_to(src)})",
                         "license": "reference-only (Lucasfilm copyright; do not ship)"})
            for pat, ent in ENT.items():
                if re.search(pat, f.stem.lower()):
                    links.append({"sfx_id": sid, "entity_id": "databank:" + ent,
                                  "relationship": "original_sound" if cat != "dialogue" else "voice_clip"})

    def merge(name, new, key_cols):
        p = db / name
        old = list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []
        cols = list(old[0].keys()) if old else key_cols
        keep = [r for r in old if not r["sfx_id"].startswith("sfx:original:")]
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(keep + new)

    merge("sound_effects.csv", rows, list(rows[0]))
    merge("sound_effect_entities.csv", links, ["sfx_id", "entity_id", "relationship"])
    by = {}
    for r in rows:
        by[r["category"]] = by.get(r["category"], 0) + 1
    print(f"original sounds={len(rows)} links={len(links)} by_category={by}")


if __name__ == "__main__":
    main()
