#!/usr/bin/env python3
"""Append search hits to data/candidates.csv.

usage: tools/add.py ALBUM_ID TRACK_NUMBER "query" < hits.txt
hits.txt: one hit per line, "URL | title". Playlist, search and /shorts/ URLs
are ignored (we only want individual watch pages).
"""
import csv, re, sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

CAND = Path(__file__).resolve().parent.parent / "data" / "candidates.csv"


def video_id(url):
    u = urlparse(url.strip())
    if "/shorts/" in u.path:
        return None
    if u.netloc.endswith("youtu.be"):
        vid = u.path.lstrip("/")
    else:
        vid = (parse_qs(u.query).get("v") or [""])[0]
    return vid if re.fullmatch(r"[A-Za-z0-9_-]{11}", vid) else None


def main():
    album, track, query = sys.argv[1:4]
    existing = set()
    with CAND.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            existing.add((r["album_id"], r["track_number"], r["video_id"]))
    added = 0
    with CAND.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for line in sys.stdin:
            if "|" not in line:
                continue
            url, title = (p.strip() for p in line.split("|", 1))
            vid = video_id(url)
            if not vid or (album, track, vid) in existing:
                continue
            existing.add((album, track, vid))
            w.writerow([album, track, vid, title, query])
            added += 1
    print(f"{album} #{track}: +{added}")


if __name__ == "__main__":
    main()
