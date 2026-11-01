# temp-music-downloader

Everything from the old `sw-music-sfx` repo (tools, working data, notes, CC0
and synthesized SFX), moved here on 2026-11-01 so `starwars-db` is the single
source of truth. `sw-music-sfx` can be deleted. Nothing in `wiki/` depends on
this folder.

**Unfinished job:** download every soundtrack track as a medium-quality MP3
and record its file path next to its YouTube URL in
`database/soundtrack_tracks.csv`. That has to run from a normal home network
(see "Why it was not done in the cloud").

## Run it on your laptop

```bash
git clone https://github.com/spencerlepine/starwars-db
cd starwars-db
pip install yt-dlp            # keep it current: pip install -U yt-dlp
# install ffmpeg (brew install ffmpeg / apt install ffmpeg / winget install ffmpeg)

python3 temp-music-downloader/tools/download_music.py               # all 89 tracks, 128 kbps
python3 temp-music-downloader/tools/download_music.py --only essential   # just the 46 key cues
```

The database path defaults to the repo this folder is in; pass a path to
override it. Options: `--bitrate 128` (kbps), `--only essential`, `--force`
(re-download files that already exist).

What it does, per row of `database/soundtrack_tracks.csv` with a `youtube_url`:

1. `yt-dlp -f bestaudio -x --audio-format mp3 --audio-quality 128K`
2. saves `database/music/<film>__<NN>.mp3` (e.g. `new-hope__01.mp3`)
3. inserts four columns right after `youtube_url`: `audio_path`
   (e.g. `music/new-hope__01.mp3`, relative to `database/`),
   `audio_duration_seconds`, `audio_bitrate_kbps`, `audio_status`
   (`ok` or `error:<reason>`)

It saves the CSV after every track and skips files already on disk, so it can
be stopped and re-run. It warns when a download is much longer than the album
duration (a sign the video is not the single track expected).

Then check and commit:

```bash
grep -c ',ok,' database/soundtrack_tracks.csv     # expect 89
grep error: database/soundtrack_tracks.csv        # anything to fix by hand
du -sh database/music                             # ~400 MB expected
git add database/music database/soundtrack_tracks.csv
git commit -m "Add soundtrack MP3s" && git push
```

Size: 128 kbps is about 1 MB per minute, so roughly 400 MB for all 89
tracks. That is under GitHub's 100 MB per-file limit, but the repo gets big.
Consider Git LFS first (`git lfs track "database/music/*.mp3"`), or
`--bitrate 96` for smaller files.

## Why it was not done in the cloud

Cloud session, 2026-11-01, yt-dlp 2026.10.26:

- The first attempts were blocked by the session's network policy:
  `www.google.com`, `*.googlevideo.com` (the audio host), `m.youtube.com`
  and `music.youtube.com` were denied.
- After network access was opened, YouTube itself refused the server's IP.
  Ordinary videos returned "Sign in to confirm you're not a bot". The
  `John Williams - Topic` tracks returned "Video unavailable" for every
  player client.
- That is YouTube's bot check on datacenter IPs. pytube/pytubefix hit the
  same endpoints, so they fail the same way. Running from a home connection
  avoids it.
- If a run on the laptop starts failing:
  - first upgrade with `pip install -U yt-dlp`, since YouTube changes often;
  - recent yt-dlp also wants a JavaScript runtime for YouTube (`deno`;
    `pip install deno` works).

## Download options compared (2026-11-01, second cloud session)

Tested from the cloud again with yt-dlp 2026.10.26:

| Route | Result from the cloud | Verdict |
|---|---|---|
| yt-dlp direct | 429 then "Video unavailable" / "Sign in to confirm you're not a bot" | Blocked by YouTube on datacenter IPs |
| Piped API instances | Every live instance returned `SignInConfirmNotBotException` (the instance's own IP is blocked too); most others are down (502/526) | Not reliable |
| Invidious API instances | 401/403 or down; public instances no longer serve video APIs | Not reliable |
| cobalt (api.cobalt.tools) | Public API now needs a Turnstile/JWT token tied to a browser | Not usable from scripts |
| Paid residential proxies | Not tried on purpose | Ruled out |

The front-ends all hit the same YouTube player endpoints from their own
servers, so they inherit the same IP block. The route that works is the
existing script on a home connection, where YouTube sees a normal user:

1. **Plain run on your own machine** (recommended). Nothing extra needed.
2. **Same, with `--cookies-from-browser firefox`** (or chrome/safari) if
   the plain run gets bot-checked at home. This uses your own signed-in
   browser session, so only do it on your machine. A throwaway Google
   account is safer than your main one.

The script now stops after 3 bot-check failures in a row (`--max-blocked`)
so a blocked run does not keep hitting YouTube; re-running resumes.

## What is already in the database (from phase one)

- `database/soundtrack_albums.csv`: the 6 saga soundtrack albums
  (Episodes I–VI), with album playlist URLs for 5 of them (Attack of the
  Clones playlist not found).
- `database/soundtrack_tracks.csv`: 89 album tracks. Each has `youtube_url`,
  `youtube_video_id`, `youtube_title`, `youtube_channel`, `source_type`, the
  official album duration, a `category` (`main_theme`, `character_theme`,
  `love_theme`, `action`, `source_music`, `finale`, `score`) and
  `essential=yes/no` (46 essential cues).
- `database/soundtrack_track_entities.csv`: tracks linked to characters,
  places and events.
- `database/sound_effects.csv`, `database/sound_effect_entities.csv`,
  `database/sounds/`: the SFX already exported (CC0 packs, synthesized,
  and original film clips for personal reference).

How the links were chosen:

- One individual video per album track; no compilations, "1 hour"/"10 hours"
  loops, extended edits, "Complete Score" uploads, covers, live concerts or
  other orchestras.
- 83 tracks are official `John Williams - Topic` uploads (Walt Disney Records
  2018 remasters of the LSO recordings), which match album durations exactly.
- 6 tracks are fan uploads (`source_type=fan_upload`), because no Topic
  upload was found:
  - ANH "The Walls Converge" and "The Last Battle"
  - ESB "The Magic Tree"
  - AOTC "Anakin and Padmé"
  - ROTS "Enter Lord Vader" and "Grievous Speaks to Lord Sidious"
- Every URL was verified through YouTube's oEmbed endpoint (it exists, can
  be embedded, and has the expected title and channel).

## Folder contents

| Path | What it is |
|---|---|
| `tools/download_music.py` | **The MP3 downloader** (above) |
| `tools/add.py`, `ingest_oembed.py`, `curate.py` | Phase-one link pipeline: record search hits, verify via oEmbed, rank and select one video per track |
| `tools/export_db.py` | Writes albums/tracks/entity links into `database/` |
| `tools/synth_sfx.py`, `build_sfx_manifest.py`, `export_sfx_db.py` | Make synthesized SFX, build the SFX manifest, export SFX tables + files into `database/` |
| `tools/collect_original_sfx.py` | Collects original film SFX clips into `database/sounds/` |
| `data/albums.csv`, `data/tracks.csv` | Official album track listings with category/essential tags |
| `data/candidates.csv`, `data/oembed.csv`, `data/selected.csv` | Every YouTube candidate found, its oEmbed check, and the final pick per track |
| `data/sfx*.csv` | SFX manifest and entity links |
| `sfx/` | CC0 Kenney packs and synthesized SFX sources |
| `NOTES.md` | Running notes and decisions from earlier sessions |
| `README-sw-music-sfx.md` | The old repo's README (pipeline description) |
| `HISTORY.md` | Commit log of the old `sw-music-sfx` repo |

Ideas for later: film-only cues that are not on the albums (e.g. "Binary
Sunset", the Force Theme suites) and the sequel/other-film soundtracks.
