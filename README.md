# Cinematheque Categorizer

![Status: work in progress](https://img.shields.io/badge/status-work%20in%20progress-orange)

> **Work in progress.** This project is under active development. The addon, the management API, the web app and library sync are deployed and in daily use; polishing, a demo mode and tests are still to come. See the [roadmap](ROADMAP.md) for what is done and what comes next.

A personal Stremio addon and web app for organizing a movie and TV library into collections.

Stremio's library is a flat list with no way to group titles. This project lets me create collections (for example French, Argentinian, LGBTQ+) and add films to them, similar to collections on an e-reader. A film can belong to several collections or to none. Each collection appears in Stremio as its own row on the home screen and in Discover, on web and TV, and playback still works through whatever stream addons are installed.

**Live:** [cinematheque-categorizer.vercel.app](https://cinematheque-categorizer.vercel.app) (management app, private token required) · [cinematheque-api.vercel.app](https://cinematheque-api.vercel.app) (API)

## Features

Working now:

* Stremio addon serving one catalog per collection, in a manually arranged order, from a Postgres database
* Titles stored with their original title (English fallback for non-Latin scripts), English title and original language from TMDB
* Token-protected management API: collections (create, rename, delete, reorder), library (add by IMDb ID or TMDB search, rename, delete, unsorted filter) and collection contents (add, remove, reorder)
* React and TypeScript web app in a dark vintage cinema design: library (All and Unsorted), poster grids, a menu to file each film in collections, search, sorting, drag to reorder collections
* Sync from the Stremio library every 30 minutes (GitHub Actions), with Cinematheque All and Cinematheque Unsorted rows in Stremio
* Add to or remove from a collection inside Stremio, on web, desktop and TV: each collection appears as a source on the film's page, and selecting it files the film without playing anything
* Everything deployed on Vercel; every push to `main` redeploys

Planned:

* Demo mode for visitors, screenshots, tests

Later: Letterboxd watchlist import, and filters by director, country, year and actor.

## How it works

```
Stremio (web, TV)  ──manifest and catalogs──▶  FastAPI on Vercel  ◀──REST API──  React app on Vercel
                                                     │
                                          Supabase Postgres, TMDB
```

* **Addon:** Stremio addons are HTTP services that return JSON. Stremio reads the addon's `manifest.json` to learn which catalogs it provides, then requests those catalogs to fill rows in its interface. Titles are identified by IMDb ID, so stream addons such as Torrentio can provide playback for any title this addon lists. The addon URL includes a private token.
* **Management API:** the web app calls `/api/...` endpoints with a separate bearer token. Film data comes from TMDB, with Cinemeta (Stremio's metadata service) as a fallback.
* **Database:** one row per film per user, keyed by IMDb ID, so the same film from different sources is never duplicated. Every table is scoped by user, ready for multi-user support.

## Stack

* **Backend:** Python, FastAPI, SQLAlchemy, Alembic, httpx
* **Database:** Supabase Postgres (transaction pooler)
* **Frontend:** React, TypeScript, Vite, CSS Modules with design tokens
* **Hosting:** Vercel (two projects from one repo: `backend/` and `frontend/`)
* **Metadata:** TMDB API, Cinemeta
* **Secrets:** 1Password CLI

## API overview

All `/api` routes require `Authorization: Bearer <API_TOKEN>`. Interactive docs are at `/docs`.

| Area | Endpoints |
| --- | --- |
| Collections | `GET/POST /api/collections`, `PATCH/DELETE /api/collections/{id}`, `PUT /api/collections/order` |
| Collection contents | `GET/POST /api/collections/{id}/titles`, `DELETE /api/collections/{id}/titles/{title_id}`, `PUT /api/collections/{id}/titles/order` |
| Library | `GET/POST /api/titles`, `PATCH/DELETE /api/titles/{id}` |
| Search | `GET /api/search?q=...&type=movie` |
| Stremio addon | `GET /{addon_token}/manifest.json`, `GET /{addon_token}/catalog/{type}/{id}.json`, `GET /{addon_token}/stream/{type}/{id}.json` |
| Collection actions | `GET /{addon_token}/do/{add\|remove}/{collection_id}/{imdb_id}/catalog/...` (reached from the Stremio source links) |
| Sync | `POST /api/sync` |

## Local development

### Prerequisites

* Python 3.10+ (production runs 3.12)
* Node.js 20.19+ or 22.12+
* [1Password CLI](https://developer.1password.com/docs/cli/) with access to the project vault
* [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) (only for testing the local backend in Stremio)

### Setup

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
# source .venv/bin/activate     # Linux / macOS / WSL
pip install -r requirements.txt
op run --env-file=../.env.op -- alembic upgrade head

cd ../frontend
npm install
```

### Environment variables

Secrets are not stored in the repo. `.env.op` contains 1Password references that `op run` resolves at runtime:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase transaction pooler connection string |
| `TMDB_READ_TOKEN` | TMDB API read access token |
| `ADDON_TOKEN` | Private token in the addon URL |
| `API_TOKEN` | Bearer token for the management API |
| `SYNC_SECRET` | Protects the library sync endpoint |

The frontend reads `VITE_API_URL` (the API's base URL) from `frontend/.env.development` locally and from the Vercel project settings in production. It is not a secret.

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

### Database migrations

```bash
cd backend
op run --env-file=../.env.op -- alembic revision --autogenerate -m "describe the change"
op run --env-file=../.env.op -- alembic upgrade head
```

Review each generated file in `migrations/versions/` before applying it, and commit it with the model change.

## Project structure

```
cinematheque-categorizer/
├── backend/
│   ├── app/
│   │   ├── addon/          Stremio manifest and catalog routes
│   │   ├── api/            Management API: collections, titles, search, schemas
│   │   ├── cinemeta.py     Cinemeta client (fallback metadata)
│   │   ├── tmdb.py         TMDB client: lookup, search, original titles
│   │   ├── models.py       SQLAlchemy models
│   │   ├── db.py           Engine and sessions for the Supabase pooler
│   │   ├── deps.py         Shared auth and user dependencies
│   │   ├── config.py       Settings loaded from environment
│   │   ├── seed.py         Test data
│   │   ├── backfill_tmdb.py  One-off: fill TMDB fields for existing titles
│   │   └── main.py         FastAPI app and CORS
│   ├── migrations/         Alembic migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/            Typed API client and response types
│       ├── components/     Token screen, sidebar
│       └── styles/         Design tokens and global styles
├── scripts/
│   ├── dev.sh              Starts backend, frontend and optional tunnel, opens a dev shell
│   └── venv-shell.rc       Startup file for the dev shell
├── .env.op                 1Password secret references
└── ROADMAP.md              Milestones and progress
```

## Attribution

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Disclaimer

This addon only organizes metadata about titles in a personal library. It does not host, index, or provide any media content.
