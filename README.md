# Cinematheque Categorizer

![Status: work in progress](https://img.shields.io/badge/status-work%20in%20progress-orange)

> **Work in progress.** This project is under active development. The addon is deployed and serves collections from the database to Stremio; the management UI, in-app collection actions and library sync are still being built. See the [roadmap](ROADMAP.md) for what is done and what comes next.

A personal Stremio addon for organizing a saved movie and TV library into collections.

Stremio's library is a flat list with no way to group titles. This project lets me create collections (for example French, Argentinian, LGBTQ) and add films from my library to them, similar to collections on an e-reader. A film can belong to several collections or to none. Each collection appears in Stremio as its own row on the home screen and in Discover, and playback still works through whatever stream addons are installed.

## Status

Early development. Currently working:

* FastAPI backend deployed on Vercel, serving a token-protected Stremio manifest
* Supabase Postgres database with titles and collections, managed with Alembic migrations
* One Stremio catalog per collection, in a manually arranged order, working in Stremio Web and on TV
* Local development through a Cloudflare quick tunnel

Planned:

* React web UI to create collections and add, remove and reorder films
* Add to collection from inside Stremio, including the TV app
* Sync from the Stremio library, with an Unsorted row for films not yet in a collection

Later: Letterboxd watchlist import, TMDB metadata and filters by director, country, year and actor.

Detailed milestones are in [ROADMAP.md](ROADMAP.md).

## Stack

* **Backend:** Python, FastAPI, SQLAlchemy
* **Database:** Supabase Postgres
* **Frontend:** React + Vite (planned)
* **Hosting:** Vercel
* **Metadata:** TMDB API (planned, for filters)
* **Secrets:** 1Password CLI

## How it works

Stremio addons are HTTP services that return JSON. Stremio reads the addon's `manifest.json` to learn which catalogs it provides, then requests those catalogs to fill rows in its interface. Titles are identified by IMDb ID, so stream addons such as Torrentio can provide playback for any title this addon lists.

The addon URL includes a private token, so the catalogs are accessible only to whoever holds the URL.

## Local development

### Prerequisites

* Python 3.10+ (production runs 3.12)
* [1Password CLI](https://developer.1password.com/docs/cli/) with access to the project vault
* [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) (for testing in Stremio Web)

### Setup

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
# source .venv/bin/activate     # Linux / macOS / WSL
pip install -r requirements.txt
```

### Environment variables

Secrets are not stored in the repo. `.env.op` contains 1Password references that `op run` resolves at runtime:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase transaction pooler connection string |
| `TMDB_READ_TOKEN` | TMDB API read access token |
| `ADDON_TOKEN` | Private token in the addon URL |
| `SYNC_SECRET` | Protects the library sync endpoint |

### Run

Start the backend and the frontend together, and open a dev shell at the repo root with the venv active:

```bash
./scripts/dev.sh
```

Logs from both appear in the same window, labeled `[api]` and `[web]`. Ctrl+C stops everything.

* Frontend: http://localhost:5173
* Backend: http://localhost:8000 (API docs at `/docs`)

To test the local backend in Stremio, also start a Cloudflare quick tunnel:

```bash
./scripts/dev.sh --tunnel
```

Turn off any VPN first, since it can block the tunnel. Install the addon with the printed `https://<tunnel-subdomain>.trycloudflare.com/<ADDON_TOKEN>/manifest.json`. The deployed addon on Vercel doesn't need the tunnel.

## Project structure

```
cinematheque-categorizer/
├── backend/
│   ├── app/
│   │   ├── addon/        Stremio manifest and catalog routes
│   │   ├── config.py     Settings loaded from environment
│   │   └── main.py       FastAPI app and CORS
│   └── requirements.txt
├── scripts/
│   ├── dev.sh            Starts backend, frontend and optional tunnel, opens a dev shell
│   └── venv-shell.rc     Startup file for the dev shell
├── .env.op               1Password secret references
└── ROADMAP.md            Milestones and progress
```

## Attribution

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Disclaimer

This addon only organizes metadata about titles in a personal library. It does not host, index, or provide any media content.