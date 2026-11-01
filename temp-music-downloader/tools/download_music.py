#!/usr/bin/env python3
"""Download every soundtrack track's YouTube audio as MP3 into starwars-db.

usage:
  pip install yt-dlp            # ffmpeg must be on PATH
  python3 tools/download_music.py [path/to/starwars-db (default: the repo this folder lives in)] [--bitrate 128] [--only essential] [--force]

For each row of database/soundtrack_tracks.csv with a youtube_url it:
  1. downloads bestaudio with yt-dlp and converts to MP3 (default 128 kbps,
     a medium size: about 1 MB per minute, ~400 MB for all 89 tracks),
  2. saves it as database/music/<album>__<NN>.mp3 (e.g. new-hope__01.mp3),
  3. writes audio_path / audio_duration_seconds / audio_bitrate_kbps /
     audio_status back into the same row, next to youtube_url.

Re-running skips files that already exist (use --force to redo), so it can
be stopped and resumed. Failures are recorded as audio_status=error:<reason>
and the run continues. Warnings are printed when a video is much longer than
the album duration (a sign it is not the single track we expected).
"""
import csv, subprocess, sys, shutil, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_COLS = ["audio_path", "audio_duration_seconds", "audio_bitrate_kbps", "audio_status"]


def parse_args(argv):
    opts = {"db": ROOT.parent, "bitrate": "128", "only": None, "force": False}
    it = iter(argv)
    for a in it:
        if a == "--bitrate":
            opts["bitrate"] = next(it)
        elif a == "--only":
            opts["only"] = next(it)
        elif a == "--force":
            opts["force"] = True
        else:
            opts["db"] = Path(a)
    return opts


def probe_seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return str(round(float(out.stdout.strip())))
    except ValueError:
        return ""


def main():
    o = parse_args(sys.argv[1:])
    if not shutil.which("yt-dlp") or not shutil.which("ffmpeg"):
        sys.exit("need yt-dlp and ffmpeg on PATH (pip install yt-dlp; install ffmpeg)")
    db = Path(o["db"]) / "database"
    table = db / "soundtrack_tracks.csv"
    with table.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = list(reader.fieldnames)
        rows = list(reader)
    # keep audio columns right after youtube_url so file path and URL sit side by side
    cols = [c for c in cols if c not in AUDIO_COLS]
    at = cols.index("youtube_url") + 1
    cols[at:at] = AUDIO_COLS

    out_dir = db / "music"
    out_dir.mkdir(exist_ok=True)

    def save():
        tmp = table.with_suffix(".tmp")
        with tmp.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows({c: r.get(c, "") for c in cols} for r in rows)
        tmp.replace(table)

    done = failed = skipped = 0
    for i, r in enumerate(rows, 1):
        if not r.get("youtube_url") or (o["only"] == "essential" and r.get("essential") != "yes"):
            continue
        name = r["track_id"].removeprefix("soundtrack:").replace(":", "__") + ".mp3"
        dest = out_dir / name
        rel = f"music/{name}"
        if dest.exists() and not o["force"]:
            r.update(audio_path=rel, audio_duration_seconds=probe_seconds(dest),
                     audio_bitrate_kbps=o["bitrate"], audio_status="ok")
            skipped += 1
            continue
        print(f"[{i}/{len(rows)}] {r['track_id']} {r['title']}", flush=True)
        cmd = ["yt-dlp", "--no-playlist", "-f", "bestaudio/best", "-x",
               "--audio-format", "mp3", "--audio-quality", f"{o['bitrate']}K",
               "--no-progress", "-o", str(out_dir / (dest.stem + ".%(ext)s")), r["youtube_url"]]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not dest.exists():
            reason = (res.stderr.strip().splitlines() or ["unknown"])[-1][:160].replace(",", ";")
            r.update(audio_path="", audio_duration_seconds="", audio_bitrate_kbps="",
                     audio_status=f"error:{reason}")
            print("   FAILED:", reason, flush=True)
            failed += 1
        else:
            secs = probe_seconds(dest)
            r.update(audio_path=rel, audio_duration_seconds=secs,
                     audio_bitrate_kbps=o["bitrate"], audio_status="ok")
            expected = int(r.get("duration_seconds") or 0)
            if secs and expected and abs(int(secs) - expected) > max(30, expected * 0.25):
                print(f"   WARNING: {secs}s vs album {expected}s, check this video", flush=True)
            done += 1
        save()  # checkpoint after every track
        time.sleep(1.5)  # be gentle with YouTube
    save()
    print(f"downloaded={done} already_present={skipped} failed={failed} -> {out_dir}")


if __name__ == "__main__":
    main()
