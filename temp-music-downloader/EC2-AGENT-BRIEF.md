# Brief for Claude Code on the EC2 box: download the Star Wars soundtrack MP3s

## Goal
Download the 89 soundtrack tracks listed in `database/soundtrack_tracks.csv`
(each row has a `youtube_url`) as 128 kbps MP3s into `database/music/`, fill in
the audio columns, and push everything to `main` with the MP3s in Git LFS.

## Rules (from the repo owner)
- Commit as `spencerlepine <60903378+spencerlepine@users.noreply.github.com>`.
  Never add Co-Authored-By or any other co-author line.
- Push directly to `main`. No branches, no pull requests.
- Commit and push in chunks as you go (e.g. one commit per film) so nothing is lost.
- Do not try to get around YouTube's bot check (no proxies, VPNs, PO-token
  hacks, rotating IPs, or cookies) unless spencer explicitly says so. If the run
  is blocked, stop and report.

## Setup
```bash
sudo dnf install -y git git-lfs python3-pip    # Amazon Linux 2023 (Ubuntu: sudo apt install -y git git-lfs python3-pip ffmpeg)
# ffmpeg on Amazon Linux: download a static build
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar xJ
sudo cp ffmpeg-*-static/ffmpeg ffmpeg-*-static/ffprobe /usr/local/bin/
pip3 install -U yt-dlp deno
git lfs install
git clone https://github.com/spencerlepine/starwars-db
cd starwars-db
git config user.name spencerlepine
git config user.email 60903378+spencerlepine@users.noreply.github.com
cat .gitattributes          # must contain: database/music/*.mp3 filter=lfs ...
```
Read `temp-music-downloader/README.md` first. It has the full background.

## Step 1: smoke test with one track
```bash
yt-dlp --skip-download --print "%(duration)s|%(title)s" https://www.youtube.com/watch?v=e9lapdvLSGw
```
If this says "Sign in to confirm you're not a bot" or "Video unavailable",
YouTube is blocking this server's IP (common on AWS). Stop and tell spencer.
Do not retry in a loop.

## Step 2: download
```bash
python3 temp-music-downloader/tools/download_music.py --only essential   # 46 key cues first
python3 temp-music-downloader/tools/download_music.py                    # then the rest; it skips files already done
```
The script checkpoints the CSV after each track, resumes when re-run, and
stops on its own after 3 bot-check failures in a row.

## Step 3: check and commit
```bash
grep -c ',ok,' database/soundtrack_tracks.csv     # expect 89
grep error: database/soundtrack_tracks.csv        # list anything that failed
du -sh database/music                             # ~400 MB
git add database/music database/soundtrack_tracks.csv
git lfs status                                    # MP3s must show as LFS objects, not plain git
git commit -m "Add soundtrack MP3s (Git LFS)"
git push origin main
```
Note any "WARNING: ... check this video" lines from the script (a duration
mismatch means the video may not be the single album track).

## Step 4: report back
Tell spencer: how many tracks are ok, which failed and why, any duration
warnings, total size, and the commit hash. Add a dated note to the
"Phase two" section of `temp-music-downloader/NOTES.md` with the same summary
and push it.
