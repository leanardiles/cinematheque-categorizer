# Roadmap

Progress tracker for Cinematheque Categorizer. Checked items are done.

The first goal is **collections**: named groups of films from my library (for example French, Argentinian, LGBTQ), shown as rows in Stremio. A film can be in several collections or in none. Filters and other import sources come later.

## Milestone 1: Addon skeleton (done)

- [x] Repo, `.gitignore`, `.gitattributes`
- [x] Secrets in 1Password, loaded with `op run` via `.env.op`
- [x] Supabase project, TMDB API access, Vercel account
- [x] FastAPI app with token-protected `manifest.json` and a sample catalog
- [x] CORS for Stremio Web
- [x] Installed in Stremio Web through a Cloudflare quick tunnel
- [x] Dev script opening backend, tunnel and dev shell windows

## Milestone 2: Database and collection catalogs (done)

- [x] SQLAlchemy engine for the Supabase transaction pooler (prepared statements disabled, `NullPool`)
- [x] Alembic set up for migrations; initial migration applied
- [x] Models, all scoped by `user_id` for future multi-user support:
  - `users`: id, name (addon token stays in environment variables until multi-user support)
  - `titles`: user, IMDb ID, type, name, year, poster; unique on (user, IMDb ID)
  - `title_sources`: title, source (`manual` for now), first seen, last seen, still present
  - `collections`: user, name, description, position
  - `collection_titles`: collection, title, position, date added; indexed on title
- [x] Idempotent seed script to create collections and add films by IMDb ID (until the UI exists)
- [x] Manifest generated from the database: one catalog per collection and content type
- [x] Catalog names shown in Stremio as `<collection> Cinematheque` (Stremio appends the type on Board)
- [x] Catalog route returns a collection's films in their manual order
- [x] Parse and URL-decode `extraArgs`; support `skip` (pages of 100)
- [x] Short `Cache-Control` on catalog responses
- [x] Verify in Stremio: rows on Board, collections in Discover, playback through Torrentio, Stremio Web and TV app

## Milestone 3: Management API and web UI

- [ ] API endpoints (protected): list library, create, rename, reorder and delete collections, add, remove and reorder films
- [ ] Add a film to the library by IMDb ID
- [ ] React + Vite UI as a second Vercel project (root directory `frontend`): collections sidebar, library grid, add and remove films, drag to reorder
- [ ] TMDB attribution in the UI footer

## Milestone 4: Deployment (done)

- [x] Deploy FastAPI on Vercel (`cinematheque-api`, root directory `backend`, Python 3.12)
- [x] Environment variables in Vercel
- [x] Install the production manifest in Stremio; save the URL in 1Password
- [x] Test on Stremio Web and TV
- [ ] Check the Vercel function region is close to the Supabase region

## Milestone 5: Add to collection from inside Stremio

- [ ] Stream resource for `tt` IDs returning one entry per collection (Add to French, In LGBTQ (remove), and so on)
- [ ] Action endpoint that adds or removes the film and returns a short confirmation clip, so it works on TV
- [ ] Optional entry opening the web UI with the film selected (desktop and phone)
- [ ] Test on the Stremio TV app

## Milestone 6: Stremio library sync and Unsorted

- [ ] Research the unofficial Stremio library API; document findings in `docs/reference/stremio-library-api.md`
- [ ] Sync endpoint protected by `SYNC_SECRET`; upsert saved titles with source `stremio`
- [ ] Mark titles removed from the Stremio library instead of deleting them
- [ ] Unsorted catalog: library titles not in any collection
- [ ] Cinematheque All catalog: every library title, in collections or not
- [ ] GitHub Actions scheduled workflow calling the sync endpoint

## Later

- [ ] Letterboxd watchlist import (via the Letterboxd addon catalog, with CSV export as fallback)
- [ ] TMDB enrichment: directors, cast, countries, genres, year
- [ ] Filter catalogs by director, country, year and actor, with `search` syntax such as `director:almodovar year:1990-2005`
- [ ] Multi-user support: accounts and one addon token per user

## Housekeeping

- [ ] Save Stremio addon protocol docs in `docs/reference/stremio-addon-protocol/` (SDK commit `ec4e0a4`)
- [ ] Renormalize line endings (`git add --renormalize .`)
- [ ] Tests for catalog routes and collection ordering
- [ ] Delete the seed test films once real library data is in place
