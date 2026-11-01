#!/usr/bin/env python3
"""Merge oEmbed check results into data/oembed.csv.

stdin: lines "VIDEO_ID|title|author_name|status" (status "ok" or an error).
Later results for the same id replace earlier ones.
"""
import csv, re, sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "data" / "oembed.csv"
rows = {}
if P.exists():
    with P.open(newline="", encoding="utf-8") as f:
        rows = {r["video_id"]: r for r in csv.DictReader(f)}
n = 0
for line in sys.stdin:
    parts = line.rstrip("\n").split("|")
    if len(parts) < 4 or not re.fullmatch(r"[A-Za-z0-9_-]{11}", parts[0].strip()):
        continue
    vid, title, author, status = parts[0].strip(), "|".join(parts[1:-2]), parts[-2], parts[-1].strip()
    rows[vid] = {"video_id": vid, "title": title.strip(), "author_name": author.strip(), "status": status}
    n += 1
with P.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["video_id", "title", "author_name", "status"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows.values())
print(f"ingested {n}, total {len(rows)}")
