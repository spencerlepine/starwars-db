# Brief for Claude Code on the EC2 box: download the Star Wars soundtrack MP3s

## Goal
Download the 89 soundtrack tracks listed in `database/soundtrack_tracks.csv`
(each row has a `youtube_url`) as 128 kbps MP3s into `database/music/`, fill in
the audio columns, and push everything to `main` with the MP3s in Git LFS.
YouTube blocks AWS IPs, so the downloads go through Cloudflare WARP (free),
which spencer approved for this job.

## Rules (from the repo owner)
- Commit as `spencerlepine <60903378+spencerlepine@users.noreply.github.com>`.
  Never add Co-Authored-By or any other co-author line.
- Push directly to `main`. No branches, no pull requests.
- Commit and push in chunks as you go (e.g. one commit per film) so nothing is lost.
- Network: Cloudflare WARP in **proxy mode** is approved. Do not add other
  proxies, paid services, cookies or other workarounds without asking spencer.
  If the run is still blocked through WARP, stop and report.
- **Never run `warp-cli mode warp` (full tunnel) on this box.** It reroutes all
  traffic and can cut off the SSH session. Proxy mode only touches traffic
  sent to 127.0.0.1:40000.

## Instance
Ubuntu 24.04, t3.small (2 GB RAM), 20 GB gp3 disk. Ubuntu is used because
Cloudflare publishes an apt package for WARP.

## Setup
```bash
sudo apt update && sudo apt install -y git git-lfs python3-pip python3-venv ffmpeg curl gpg lsb-release
python3 -m venv ~/venv && . ~/venv/bin/activate
pip install -U yt-dlp deno
git lfs install
git clone https://github.com/spencerlepine/starwars-db
cd starwars-db
git config user.name spencerlepine
git config user.email 60903378+spencerlepine@users.noreply.github.com
cat .gitattributes          # must contain: database/music/*.mp3 filter=lfs ...
```
Read `temp-music-downloader/README.md` for the full background.

## Cloudflare WARP (proxy mode)
```bash
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
sudo apt update && sudo apt install -y cloudflare-warp

warp-cli --accept-tos registration new
warp-cli --accept-tos mode proxy          # SOCKS5 on 127.0.0.1:40000
warp-cli --accept-tos connect
warp-cli --accept-tos status              # expect: Connected

curl -s -x socks5h://127.0.0.1:40000 https://www.cloudflare.com/cdn-cgi/trace | grep warp   # expect warp=on
```
If `connect` hangs on "Connecting", run `warp-cli disconnect`, then
`warp-cli connect` again. If it never connects, stop and report.

## Step 1: smoke test with one track
```bash
yt-dlp --proxy socks5://127.0.0.1:40000 --skip-download \
  --print "%(duration)s|%(title)s" https://www.youtube.com/watch?v=e9lapdvLSGw
```
Expected: `320|Main Title`. If it says "Sign in to confirm you're not a bot"
or "Video unavailable", YouTube is blocking the WARP exit too (Cloudflare IPs
are sometimes flagged). Try once more after `warp-cli disconnect && warp-cli
connect`. If it still fails, stop and tell spencer. Do not retry in a loop.

## Step 2: download
```bash
P="--proxy socks5://127.0.0.1:40000"
python3 temp-music-downloader/tools/download_music.py $P --only essential   # 46 key cues first
python3 temp-music-downloader/tools/download_music.py $P                    # the rest; finished files are skipped
```
The script saves the CSV after every track, resumes when re-run, and stops
on its own after 3 bot-check failures in a row. Use `tmux` or `nohup` so an
SSH drop does not kill the run.

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
GitHub pushes go out directly, not through WARP. Note any "WARNING: ... check
this video" lines from the script. A duration mismatch means the video may
not be the single album track.

## Step 4: report back and clean up
Tell spencer how many tracks are ok, which failed and why, any duration
warnings, the total size and the commit hash. Add a dated note to the
"Phase two" section of `temp-music-downloader/NOTES.md` with the same summary
and push it. Then remind spencer to terminate the EC2 instance and to revoke
any credentials stored on it.
