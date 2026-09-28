#!/usr/bin/env bash
# Local development environment.
#
#   this window  -> backend [api], frontend [web] and, optionally, a tunnel [tunnel],
#                   with their logs combined and labeled
#   new window   -> dev shell at the repo root with the venv active
#
# Usage:
#   ./scripts/dev.sh            backend + frontend
#   ./scripts/dev.sh --tunnel   also a Cloudflare quick tunnel, to test the local
#                               backend in Stremio (production uses Vercel instead)
#
# Ctrl+C stops everything started from this window.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WITH_TUNNEL=false
[[ "${1:-}" == "--tunnel" ]] && WITH_TUNNEL=true

PIDS=()
TUNNEL_LOG="$(mktemp)"

# Stop a process and everything it started. On Git Bash, taskkill /T removes the
# whole Windows process tree (op -> uvicorn -> reloader worker), so nothing lingers.
stop_tree() {
  local pid="$1" winpid=""
  [[ -r "/proc/$pid/winpid" ]] && winpid="$(cat "/proc/$pid/winpid")"
  if [[ -n "$winpid" ]] && command -v taskkill > /dev/null; then
    taskkill //F //T //PID "$winpid" > /dev/null 2>&1
  else
    kill "$pid" 2> /dev/null
  fi
}

cleanup() {
  trap - INT TERM EXIT
  echo ""
  echo "Stopping..."
  for pid in "${PIDS[@]}"; do stop_tree "$pid"; done
  rm -f "$TUNNEL_LOG"
  echo "Stopped."
}
trap cleanup INT TERM EXIT

# Prefix each line of output with a colored label, e.g. [api]
label() {
  local name="$1" color="$2" line
  while IFS= read -r line; do
    printf '\033[%sm[%s]\033[0m %s\n' "$color" "$name" "$line"
  done
}

# Pick the venv activation script for Windows (Git Bash) or Linux/WSL
if [[ -f "$ROOT/backend/.venv/Scripts/activate" ]]; then
  ACTIVATE="$ROOT/backend/.venv/Scripts/activate"
else
  ACTIVATE="$ROOT/backend/.venv/bin/activate"
fi

echo "Starting backend..."
(
  cd "$ROOT/backend"
  source "$ACTIVATE"
  exec op run --env-file=../.env.op -- uvicorn app.main:app --reload
) > >(label api 36) 2>&1 &
PIDS+=($!)

echo "Starting frontend..."
(
  cd "$ROOT/frontend"
  [[ -d node_modules ]] || npm install
  exec npm run dev
) > >(label web 35) 2>&1 &
PIDS+=($!)

# Wait up to 60 seconds for the backend (op may ask you to unlock 1Password)
BACKEND_UP=false
for _ in $(seq 1 60); do
  if curl -s http://localhost:8000/health > /dev/null; then
    BACKEND_UP=true
    break
  fi
  sleep 1
done

if [[ "$BACKEND_UP" == false ]]; then
  echo "Backend did not start. Check the [api] lines above."
  exit 1
fi

TUNNEL_URL=""
if [[ "$WITH_TUNNEL" == true ]]; then
  echo "Starting tunnel..."
  cloudflared tunnel --url http://localhost:8000 > >(tee "$TUNNEL_LOG" | label tunnel 33) 2>&1 &
  PIDS+=($!)
  for _ in $(seq 1 30); do
    TUNNEL_URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2> /dev/null | head -n 1 || true)"
    [[ -n "$TUNNEL_URL" ]] && break
    sleep 1
  done
  [[ -z "$TUNNEL_URL" ]] && echo "Tunnel URL not found. Check the [tunnel] lines (is a VPN on?)."
fi

# Open the dev shell in its own window
if [[ -x /usr/bin/mintty.exe ]]; then
  (
    cd "$ROOT"
    /usr/bin/mintty.exe -t "Cinematheque Dev Shell" /usr/bin/bash --init-file "$ROOT/scripts/venv-shell.rc" -i &
  )
fi

printf '\n\033[1m%s\033[0m\n' "Cinematheque dev environment"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000   (API docs: /docs)"
if [[ -n "$TUNNEL_URL" ]]; then
  echo "  Tunnel:    $TUNNEL_URL"
  echo "  Manifest:  $TUNNEL_URL/<ADDON_TOKEN>/manifest.json"
fi
echo "  Press Ctrl+C to stop everything."
echo ""

wait
