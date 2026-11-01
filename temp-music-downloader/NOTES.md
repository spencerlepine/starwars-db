# Notes

## Environment constraints (2026-10-31 session)

- The cloud sandbox cannot reach youtube.com directly (proxy denies the
  CONNECT), and the YouTube Data API needs an API key we do not have.
  yt-dlp therefore cannot run here.
- What works: web search restricted to youtube.com (finds watch URLs) and the
  public oEmbed endpoint via a fetch tool (verifies title + channel).
- oEmbed does not return duration. Durations recorded in the database are the
  official album durations; "- Topic" uploads match the album track exactly.
- Playlist pages (incl. official `OLAK5uy_…` album playlists) render as a JS
  shell, and Invidious/Piped mirrors were blocked or empty, so album playlists
  are recorded by URL only.

## Running locally later

With yt-dlp installed you can re-check durations without downloading:

    yt-dlp --skip-download --print "%(id)s|%(duration)s|%(channel)s|%(title)s" URL

## Phase one results (2026-11-01)

- 6 albums, 89 tracks, every track has one individual YouTube video.
- 83 tracks use the official `John Williams - Topic` auto-generated uploads
  (Walt Disney Records remasters of the original LSO recordings). 6 tracks fall
  back to fan uploads because no Topic upload surfaced in search: ANH "The
  Walls Converge" and "The Last Battle", ESB "The Magic Tree", AOTC "Anakin
  and Padmé", ROTS "Enter Lord Vader" and "Grievous Speaks to Lord Sidious".
  These are marked `source_type=fan_upload` in the database.
- Album playlists recorded for 5 of 6 albums (Attack of the Clones playlist
  not found).
- Rejected on purpose: "1 hour"/"10 hours" loops, extended edits, "Complete
  Score" uploads, covers, live concerts and re-recordings by other orchestras
  (Gerhardt/National Philharmonic, Vienna, Boston Pops, etc.).
- Ideas for later: film-only cues not on the albums (e.g. Binary Sunset,
  Force Theme), and sound effects (phase two).

## Phase two: downloading the music (2026-11-01)

The cloud sandbox cannot reach YouTube (proxy 403 on www.youtube.com, so
yt-dlp fails), so the download has to run on a machine with normal internet:

    pip install yt-dlp          # plus ffmpeg on PATH
    git clone .../starwars-db && git clone .../sw-music-sfx
    cd sw-music-sfx
    python3 tools/download_music.py ../starwars-db            # all 89 tracks, 128 kbps MP3
    python3 tools/download_music.py ../starwars-db --only essential   # just the 52 key cues

Files land in `starwars-db/database/music/<film>__<NN>.mp3` and the script
fills `audio_path`, `audio_duration_seconds`, `audio_bitrate_kbps`,
`audio_status` in `soundtrack_tracks.csv`, right next to `youtube_url`. It
checkpoints after every track and skips existing files, so it can be resumed.
Expect ~400 MB for everything at 128 kbps; consider Git LFS for `*.mp3`
before committing. Tested end to end against a stubbed yt-dlp only.
