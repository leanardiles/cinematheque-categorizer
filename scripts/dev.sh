#!/usr/bin/env bash
# Opens the local dev environment in three Git Bash windows:
#   Cinematheque Backend    -> uvicorn with auto reload
#   Cinematheque Tunnel     -> Cloudflare quick tunnel, with its full log
#   Cinematheque Dev Shell  -> repo root with the venv active
# This window prints the tunnel and manifest URLs when everything is up.
# To stop the backend or tunnel, press Ctrl+C in its window or close it.
# Usage: ./scripts/dev.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TUNNEL_LOG="$(mktemp)"

if [[ ! -x /usr/bin/mintty.exe ]]; then
  echo "mintty not found. This script opens Git Bash windows and needs Git for Windows."
  exit 1
fi

# Pick the venv activation script for Windows (Git Bash) or Linux/WSL
if [[ -f "$ROOT/backend/.venv/Scripts/activate" ]]; then
  ACTIVATE="$ROOT/backend/.venv/Scripts/activate"
else
  ACTIVATE="$ROOT/backend/.venv/bin/activate"
fi

echo "Opening backend window..."
(
  cd "$ROOT/backend"
  /usr/bin/mintty.exe -t "Cinematheque Backend" /usr/bin/bash -c \
    "source '$ACTIVATE' && op run --env-file=../.env.op -- uvicorn app.main:app --reload; echo; echo 'Backend stopped.'; exec bash" &
)

# Wait up to 60 seconds for the backend (op may ask you to unlock 1Password)
for _ in $(seq 1 60); do
  if curl -s http://localhost:8000/health > /dev/null; then
    echo "Backend is up at http://localhost:8000"
    break
  fi
  sleep 1
done

if ! curl -s http://localhost:8000/health > /dev/null; then
  echo "Backend did not start. Check the backend window for errors."
  exit 1
fi

echo "Opening tunnel window..."
# The tunnel window shows the full cloudflared log and also copies it to a
# temp file, so this script can read the tunnel URL from it.
(
  cd "$ROOT"
  /usr/bin/mintty.exe -t "Cinematheque Tunnel" /usr/bin/bash -c \
    "cloudflared tunnel --url http://localhost:8000 2>&1 | tee '$TUNNEL_LOG'; echo; echo 'Tunnel stopped.'; exec bash" &
)

# Wait up to 30 seconds for the tunnel URL to appear in the log
TUNNEL_URL=""
for _ in $(seq 1 30); do
  TUNNEL_URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -n 1 || true)"
  [[ -n "$TUNNEL_URL" ]] && break
  sleep 1
done

if [[ -z "$TUNNEL_URL" ]]; then
  echo "Tunnel URL not found. Check the tunnel window for errors (is a VPN on?)."
  exit 1
fi

echo "Opening dev shell..."
(
  cd "$ROOT"
  /usr/bin/mintty.exe -t "Cinematheque Dev Shell" /usr/bin/bash --init-file "$ROOT/scripts/venv-shell.rc" -i &
)

echo ""
echo "Tunnel: $TUNNEL_URL"
echo "Manifest: $TUNNEL_URL/<ADDON_TOKEN>/manifest.json"
echo "(It can take up to 30 seconds before the tunnel address resolves.)"
echo ""
echo "All set. You can close this window; the other windows keep running."
