#!/usr/bin/env python3
"""Rank YouTube candidates per soundtrack track and pick the best one.

Inputs (all in data/):
  albums.csv      album metadata, one row per film soundtrack
  tracks.csv      official album track listing + our tags (category, essential)
  candidates.csv  raw search hits: album_id,track_number,video_id,search_title,query
  oembed.csv      verification: video_id,title,author_name,status (from YouTube oEmbed)

Output:
  data/selected.csv  one row per track with the chosen video (or blank + reason)
  stdout             a report of tracks with no acceptable candidate

Rules: individual track uploads only. Long compilations, loops, "1 hour" /
"10 hours" edits, covers, live concerts, and re-recordings by other
orchestras are rejected. Official auto-generated "- Topic" uploads of the
original John Williams / London Symphony Orchestra recordings win.
"""
import csv, re, sys
from difflib import SequenceMatcher
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

REJECT = re.compile(
    r"\b(\d+\s*(hour|hr|h)s?|hours?|loop(ed)?|extended|ambien(ce|t)|sleep|study|"
    r"cover|piano|guitar|violin|cello|remix|lo-?fi|reaction|live|concert|tutorial|"
    r"8.?bit|synth(esia)?|medley|ringtone|karaoke|slowed|reverb|instrumental cover|"
    r"full (album|soundtrack|score)|complete (score|soundtrack|album)|ost full|"
    r"all (songs|tracks|music)|compilation|suite|anthology|vs\.? ?game|lego|mashup|"
    r"epic version|trailer|minecraft|fortnite|kazoo|recorder|ukulele|marimba|band cover)\b",
    re.I,
)
OFFICIAL_AUTHORS = {
    "john williams - topic": 100,
    "london symphony orchestra - topic": 95,
    "star wars": 80,
    "walt disney records": 80,
    "disneymusicvevo": 70,
    "sony classical": 60,
}
OTHER_ORCHESTRA = re.compile(
    r"wiener|vienna|boston pops|berliner|hollywood bowl|city of prague|"
    r"philharmonic|skywalker symphony|royal philharmonic|lso live|cinematic|gerhardt|evil genius|hollywood sound stars|national philharmonic", re.I
)


def norm(s):
    s = s.lower().replace("’", "'").replace("é", "e")
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def read(name):
    p = DATA / name
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score(track_title, cand, oe):
    title = oe.get("title") or cand["search_title"]
    author = (oe.get("author_name") or "").strip()
    if oe.get("status", "ok") != "ok":
        return None, "oembed failed (deleted/private/embedding off)"
    if REJECT.search(title):
        return None, f"rejected title: {title}"
    if OTHER_ORCHESTRA.search(author) or OTHER_ORCHESTRA.search(title):
        return None, f"other recording: {author} / {title}"
    sim = SequenceMatcher(None, norm(track_title), norm(title)).ratio()
    if norm(track_title) in norm(title):
        sim = max(sim, 0.9)
    if sim < 0.45:
        return None, f"title mismatch ({sim:.2f}): {title}"
    s = sim * 50
    s += OFFICIAL_AUTHORS.get(author.lower(), 0)
    if author.lower().endswith(" - topic") and author.lower() not in OFFICIAL_AUTHORS:
        s += 20  # some other auto-generated label upload
    return s, ""


def main():
    tracks = read("tracks.csv")
    cands = read("candidates.csv")
    oembed = {r["video_id"]: r for r in read("oembed.csv")}
    by_track = {}
    for c in cands:
        by_track.setdefault((c["album_id"], c["track_number"]), []).append(c)

    out, missing = [], []
    for t in tracks:
        key = (t["album_id"], t["track_number"])
        best, reasons = None, []
        seen = set()
        for c in by_track.get(key, []):
            if c["video_id"] in seen:
                continue
            seen.add(c["video_id"])
            oe = oembed.get(c["video_id"])
            if oe is None:
                reasons.append(f"{c['video_id']}: not verified yet")
                continue
            s, why = score(t["title"], c, oe)
            if s is None:
                reasons.append(f"{c['video_id']}: {why}")
            elif best is None or s > best[0]:
                best = (s, c, oe)
        row = dict(t)
        if best:
            s, c, oe = best
            row.update(
                video_id=c["video_id"],
                youtube_url=f"https://www.youtube.com/watch?v={c['video_id']}",
                youtube_title=oe["title"],
                youtube_channel=oe["author_name"],
                score=f"{s:.1f}",
            )
        else:
            row.update(video_id="", youtube_url="", youtube_title="", youtube_channel="", score="")
            missing.append((key, t["title"], reasons))
        out.append(row)

    cols = list(tracks[0].keys()) + ["video_id", "youtube_url", "youtube_title", "youtube_channel", "score"]
    with (DATA / "selected.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    print(f"selected {len(out) - len(missing)}/{len(out)} tracks")
    for key, title, reasons in missing:
        print(f"MISSING {key[0]} #{key[1]} {title}")
        for r in reasons:
            print(f"    {r}")


if __name__ == "__main__":
    sys.exit(main())
