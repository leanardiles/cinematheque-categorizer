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

### Part A: Management API (done)

- [x] `API_TOKEN` bearer auth for `/api` routes, separate from the addon token
- [x] CORS for Stremio Web and the management UI
- [x] TMDB client: lookup by IMDb ID, search, original titles (English fallback for non-Latin scripts); Cinemeta as fallback
- [x] Titles store display name, original title, English name, original language and TMDB ID; existing titles backfilled
- [x] Collection endpoints: list, create, rename, delete, reorder
- [x] Library endpoints: list (search, unsorted), add by IMDb ID or TMDB result, rename, delete
- [x] Collection content endpoints: list, add, remove, reorder films
- [x] TMDB search endpoint marking titles already in the library
- [x] Deployed and tested on Vercel

### Part B: Frontend scaffold and deployment (done)

- [x] Decisions: TypeScript, CSS Modules with design tokens, visual direction C (Salle de projection: dark, cream text, gold accent, Playfair Display SC and Work Sans, film strip framing)
- [x] React + Vite + TypeScript app in `frontend/`, design tokens and fonts
- [x] Token screen that checks the API token and stores it in the browser
- [x] Typed API client using `VITE_API_URL`, sidebar listing collections
- [x] `dev.sh` runs backend and frontend in one labeled window, tunnel optional
- [x] Second Vercel project (`cinematheque-categorizer`, root directory `frontend`)

### Part C: UI features

- [x] Collection view: film strip poster grid, original-language posters, remove films with confirmation
- [x] Sidebar: All at the top (every film in the library), then collections
- [x] All view: every film, delete from the library with confirmation (lists the collections it leaves)
- [x] New collection button next to the Collections heading
- [x] Drag to reorder collections (dnd-kit, mouse, touch and keyboard)
- [x] Rename and delete collections (with confirmation)
- [ ] Add films to a collection: a + tile at the end of each collection opens a picker of library films
- [ ] Drag to reorder films in a collection (dnd-kit)
- [x] TMDB attribution in the UI footer

**Source of truth:** for now, films enter the library only through the Stremio library sync (Milestone 5). The app organizes them; it doesn't add new films. Adding films from the app is a future enhancement (see Later).

**How All and collections relate**

- All shows every film in the library, whether it is in a collection or not.
- Removing a film from a collection keeps it in All and in its other collections.
- Deleting a film from All deletes it from the library and from every collection it is in.

## Milestone 4: Deployment (done)

- [x] Deploy FastAPI on Vercel (`cinematheque-api`, root directory `backend`, Python 3.12)
- [x] Environment variables in Vercel
- [x] Install the production manifest in Stremio; save the URL in 1Password
- [x] Test on Stremio Web and TV
- [ ] Check the Vercel function region is close to the Supabase region

## Milestone 5: Stremio library sync

- [ ] Research the unofficial Stremio library API; document findings in `docs/reference/stremio-library-api.md`
- [ ] Sync endpoint protected by `SYNC_SECRET`; upsert saved titles with source `stremio`
- [ ] Films removed from the Stremio library are deleted here too, including their collection entries (same as deleting from All)
- [ ] Deleting from All: allowed for manually added films; for films synced from Stremio, show a message to remove them from the Stremio library instead (see open question below)
- [ ] GitHub Actions scheduled workflow calling the sync endpoint
- [ ] Stremio catalogs: Cinematheque All (always first) and Unsorted
- [ ] Library view in the UI: All and Unsorted, switch between original and English title

**Open question:** a film deleted from All but still saved in the Stremio library would come back on the next sync. Leaning towards the simplest option for now: the Stremio library is the source of truth for synced films, so the UI doesn't offer deleting them from All and instead says to remove the film from the Stremio library, and the next sync removes it here. Films added manually (not from Stremio) can still be deleted from All. Other options for later: remember deleted films and skip them during sync, or also remove them from the Stremio library.

## Milestone 6: Add to collection from inside Stremio

- [ ] Stream resource for `tt` IDs returning one entry per collection (Add to French, In LGBTQ+ (remove), and so on)
- [ ] Action endpoint that adds or removes the film and returns a short confirmation clip, so it works on TV
- [ ] Optional entry opening the web UI with the film selected (desktop and phone)
- [ ] Test on the Stremio TV app

## Milestone 7: Showcase

- [ ] Demo mode for visitors: an Explore demo button on the token screen that runs the UI on sample data, read-only, no token needed
- [ ] Screenshots or a short GIF of the app and the Stremio rows in the README

## Later

- [ ] Search bar at the top right of every screen, searching the library (All) to find and file films
- [ ] Decide whether the app can add films itself, and how: TMDB search adding films that aren't in the Stremio library (two kinds of films, different delete rules), or adding them here and to the Stremio library at the same time (one source of truth, but writes through the unofficial Stremio API)
- [ ] Letterboxd watchlist import (via the Letterboxd addon catalog, with CSV export as fallback)
- [ ] TMDB enrichment: directors, cast, countries, genres, year
- [ ] Filter catalogs by director, country, year and actor, with `search` syntax such as `director:almodovar year:1990-2005`
- [ ] Multi-user support: accounts and one addon token per user

## Housekeeping

- [ ] Save Stremio addon protocol docs in `docs/reference/stremio-addon-protocol/` (SDK commit `ec4e0a4`)
- [ ] Renormalize line endings (`git add --renormalize .`)
- [ ] Tests for catalog routes and collection ordering
- [ ] Delete the seed test films once real library data is in place
