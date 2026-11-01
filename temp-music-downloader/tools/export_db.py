#!/usr/bin/env python3
"""Publish curated soundtrack data into the starwars-db CSV database.

usage: tools/export_db.py [path/to/starwars-db] [--albums a,b,...]

Writes (into <db>/database/):
  soundtrack_albums.csv          one row per film soundtrack album
  soundtrack_tracks.csv          one row per album track + chosen YouTube video
  soundtrack_track_entities.csv  track -> entity links (leitmotifs, scenes)

--albums limits which albums are (re)written, so the database can be filled
in chunk by chunk; rows for other albums already in the database are kept.
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def read(p):
    p = Path(p)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(p, cols, rows):
    with Path(p).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def secs(d):
    m, s = d.split(":")
    return str(int(m) * 60 + int(s))


def main():
    args = sys.argv[1:]
    only = None
    if "--albums" in args:
        i = args.index("--albums")
        only = set(args[i + 1].split(","))
        del args[i : i + 2]
    db = Path(args[0] if args else ROOT.parent) / "database"
    assert db.is_dir(), db

    albums = {a["album_id"]: a for a in read(DATA / "albums.csv")}
    sel = read(DATA / "selected.csv")
    links = read(DATA / "track_entities.csv")
    keep = lambda aid: only is None or aid in only
    sid = lambda a: f"soundtrack:{albums[a]['event_id']}"

    acols = ["album_id", "event_id", "title", "composer", "performer", "original_label",
             "original_release_year", "reissue", "track_count", "youtube_playlist_url"]
    kept_albums = {sid(k) for k in albums if not keep(k)}
    arows = [r for r in read(db / "soundtrack_albums.csv") if r["album_id"] in kept_albums]
    for k, a in albums.items():
        if keep(k):
            arows.append({
                "album_id": sid(k), "event_id": a["event_id"], "title": a["album_title"],
                "composer": a["composer"], "performer": a["performer"],
                "original_label": a["original_label"],
                "original_release_year": a["original_release_year"],
                "reissue": a["reissue"], "track_count": a["track_count"],
                "youtube_playlist_url": a.get("youtube_playlist_url", ""),
            })
    order = {sid(k): i for i, k in enumerate(albums)}
    arows.sort(key=lambda r: order.get(r["album_id"], 99))

    tcols = ["track_id", "album_id", "event_id", "track_number", "title", "duration",
             "duration_seconds", "category", "essential", "youtube_video_id", "youtube_url",
             "youtube_title", "youtube_channel", "source_type"]
    audio_cols = ["audio_path", "audio_duration_seconds", "audio_bitrate_kbps", "audio_status"]
    existing = {r["track_id"]: r for r in read(db / "soundtrack_tracks.csv")}
    if any("audio_path" in r for r in existing.values()):
        at = tcols.index("youtube_url") + 1
        tcols[at:at] = audio_cols
    trows = [r for r in read(db / "soundtrack_tracks.csv") if r["album_id"] in kept_albums]
    for r in sel:
        if not keep(r["album_id"]):
            continue
        a = albums[r["album_id"]]
        ch = r["youtube_channel"]
        trows.append({
            "track_id": f"{sid(r['album_id'])}:{int(r['track_number']):02d}",
            "album_id": sid(r["album_id"]), "event_id": a["event_id"],
            "track_number": r["track_number"], "title": r["title"],
            "duration": r["album_duration"], "duration_seconds": secs(r["album_duration"]),
            "category": r["category"], "essential": r["essential"],
            "youtube_video_id": r["video_id"], "youtube_url": r["youtube_url"],
            "youtube_title": r["youtube_title"], "youtube_channel": ch,
            "source_type": ("official" if ch.endswith(" - Topic") or ch in ("Star Wars", "Walt Disney Records")
                            else "fan_upload" if ch else ""),
        })
    for r in trows:  # carry over downloaded-audio fields when the video is unchanged
        old = existing.get(r["track_id"], {})
        for c in audio_cols:
            if c in tcols:
                r[c] = old.get(c, "") if old.get("youtube_video_id") == r["youtube_video_id"] else ""
    trows.sort(key=lambda r: (order.get(r["album_id"], 99), int(r["track_number"])))

    lcols = ["track_id", "entity_id", "relationship"]
    lrows = [r for r in read(db / "soundtrack_track_entities.csv")
             if r["track_id"].rsplit(":", 1)[0] in kept_albums]
    for l in links:
        if keep(l["album_id"]):
            lrows.append({"track_id": f"{sid(l['album_id'])}:{int(l['track_number']):02d}",
                          "entity_id": l["entity_id"], "relationship": l["relationship"]})
    lrows.sort(key=lambda r: (order.get(r["track_id"].rsplit(":", 1)[0], 99), r["track_id"]))

    write(db / "soundtrack_albums.csv", acols, arows)
    write(db / "soundtrack_tracks.csv", tcols, trows)
    write(db / "soundtrack_track_entities.csv", lcols, lrows)
    print(f"albums={len(arows)} tracks={len(trows)} "
          f"with_video={sum(1 for r in trows if r['youtube_video_id'])} links={len(lrows)}")


if __name__ == "__main__":
    main()
