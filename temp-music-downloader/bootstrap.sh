#!/usr/bin/env bash
# Bootstrap a fresh Ubuntu EC2 box for the soundtrack download job.
# Installs git, gh, Claude Code, the downloader's tools (ffmpeg, yt-dlp, deno,
# yt-dlp-ejs) and Cloudflare WARP. It does not log in or connect anything:
# the interactive steps are printed at the end.
#
# usage:  curl -fsSL https://raw.githubusercontent.com/spencerlepine/starwars-db/main/temp-music-downloader/bootstrap.sh | bash
#    or:  bash temp-music-downloader/bootstrap.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "== apt packages"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y git curl wget gnupg gpg lsb-release tmux ffmpeg python3-pip python3-venv

echo "== GitHub CLI"
sudo mkdir -p -m 0755 /etc/apt/keyrings
wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

echo "== Cloudflare WARP"
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
  | sudo gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflare-client.list > /dev/null

sudo apt-get update
sudo apt-get install -y gh cloudflare-warp

echo "== Python venv: yt-dlp (with EJS challenge solver) + deno"
python3 -m venv ~/venv
~/venv/bin/pip install -q -U "yt-dlp[default]" deno

echo "== Claude Code"
curl -fsSL https://claude.ai/install.sh | bash
export PATH="$HOME/.local/bin:$PATH"

echo "== versions"
git --version
gh --version | head -1
warp-cli --version | head -1
ffmpeg -version | head -1
~/venv/bin/yt-dlp --version
claude --version

cat <<'EOF'

== Done. Human steps:

  source ~/.bashrc                 # pick up ~/.local/bin for `claude`
  gh auth login                    # GitHub (HTTPS, browser/device code)
  gh auth setup-git
  git clone https://github.com/spencerlepine/starwars-db && cd starwars-db
  git config user.name spencerlepine
  git config user.email 60903378+spencerlepine@users.noreply.github.com
  claude                           # log in, then paste temp-music-downloader/EC2-AGENT-BRIEF.md

WARP is installed but not registered or connected; the brief covers that
(proxy mode only, never `warp-cli mode warp`).
When finished: terminate the instance and revoke the gh token.
EOF
