# sw-music-sfx

Notes, tools and prototypes for collecting Star Wars music (and later SFX)
as concept/reference material for a personal game project. Curated results
are published into the `starwars-db` CSV database.

## Phase one: soundtrack YouTube links

Goal: one individual YouTube video per official soundtrack album track for the
six saga films (Episodes I–VI), focused on the themes and main score cues.
No long compilations, loops or "10 hours" edits. Nothing is downloaded.

### Pipeline

1. `data/albums.csv` / `data/tracks.csv` — the official album track listings
   (from the Wikipedia soundtrack pages), tagged with `category`
   (`main_theme`, `character_theme`, `love_theme`, `action`, `source_music`,
   `finale`, `score`) and `essential` (`yes` = the nostalgic, instantly
   recognisable cues).
2. Web search (restricted to youtube.com) per track; hits are appended to
   `data/candidates.csv` with `tools/add.py`.
3. Every candidate is verified through YouTube's public oEmbed endpoint
   (`https://www.youtube.com/oembed?url=...&format=json`), which confirms the
   video exists and is embeddable and gives its real title and channel.
   Results go to `data/oembed.csv`.
4. `tools/curate.py` ranks candidates per track and writes `data/selected.csv`.
   It rejects compilations/loops/covers/live/other orchestras and prefers the
   official auto-generated `John Williams - Topic` uploads (Walt Disney Records
   2018 remasters of the original London Symphony Orchestra recordings).
5. `tools/export_db.py` writes the result into `starwars-db/database/`.

See `NOTES.md` for environment constraints and decisions.
