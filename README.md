# Cinematheque Categorizer

A personal Stremio addon for organizing a saved movie and TV library with custom tags and filters.

Stremio's library has no tags or custom categories. This project adds catalogs to Stremio that show only titles from my own library, filterable by director, country, year, actors, and custom genres. Playback still works through whatever stream addons are installed in Stremio.

## Status

Early development. Currently working:

* FastAPI backend serving a token-protected Stremio manifest and a sample catalog
* Local testing in Stremio Web through a Cloudflare quick tunnel

Planned:

* Supabase Postgres database for titles, people, countries, and tags
* TMDB metadata enrichment (directors, cast, countries, year)
* Filter catalogs by director, country, year, actor, and custom genre
* Sync from the Stremio library
* React tagging UI
* Deployment on Vercel

## Stack

* **Backend:** Python, FastAPI, SQLAlchemy
* **Database:** Supabase Postgres
* **Frontend:** React + Vite (planned)
* **Hosting:** Vercel (planned)
* **Metadata:** TMDB API
* **Secrets:** 1Password CLI

## How it works

Stremio addons are HTTP services that return JSON. Stremio reads the addon's `manifest.json` to learn which catalogs it provides, then requests those catalogs to fill rows in its interface. Titles are identified by IMDb ID, so stream addons such as Torrentio can provide playback for any title this addon lists.

The addon URL includes a private token, so the catalogs are accessible only to whoever holds the URL.

## Local development

### Prerequisites

* Python 3.12+
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

Start the backend and a tunnel together, and open a dev shell at the repo root with the venv active:

```bash
./scripts/dev.sh
```

Turn off any VPN first, since it can block the tunnel from starting.

Or run the backend alone:

```bash
cd backend
op run --env-file=../.env.op -- uvicorn app.main:app --reload
```

Install the addon in Stremio with:

```
https://<tunnel-subdomain>.trycloudflare.com/<ADDON_TOKEN>/manifest.json
```

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
│   ├── dev.sh            Starts backend and tunnel, opens a dev shell
│   └── venv-shell.rc     Startup file for the dev shell
└── .env.op               1Password secret references
```

## Attribution

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Disclaimer

This addon only organizes metadata about titles in a personal library. It does not host, index, or provide any media content.