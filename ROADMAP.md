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
  - `users`: id, name (tokens lived in environment variables until accounts arrived in Milestone 7)
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
- [x] File films from All: a collections menu on each poster (tick to add, untick to remove), collection names under each title, and an Unsorted filter
- [x] Search bar at the top right of every screen: finds films across the library as you type (display, original and English titles, accents ignored), with the collections menu on each result
- [x] Sort by last added (Stremio's save date), title or year in All, Unsorted, Search and collections; collections also offer their own order (the default, and the order Stremio shows). The choice is remembered per browser
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
- [x] Function region next to the database: Supabase is in `us-west-2` (Oregon), so the API runs in `pdx1` (Portland), set in `backend/vercel.json` (it ran in the default `iad1`, Washington, before)

## Milestone 5: Stremio library sync (done)

- [x] Research the unofficial Stremio library API; document findings in `docs/reference/stremio-library-api.md`
- [x] Sync endpoint protected by `SYNC_SECRET`; upsert saved titles with source `stremio`, original titles from TMDB, Stremio's save date
- [x] Films removed from the Stremio library are deleted here too, including their collection entries (same as deleting from All)
- [x] Deleting from All: allowed for manually added films; hidden for films synced from Stremio (see open question below)
- [x] For synced films, a short hint in the collections menu that they're removed from the Stremio library instead
- [x] GitHub Actions scheduled workflow calling the sync endpoint every 30 minutes
- [x] Stremio catalogs: Cinematheque All and Cinematheque Unsorted, first in the manifest, most recently saved first
- [x] Library view in the UI: All and Unsorted
- [x] Switch a film's display name between its original and English title (in the collections menu)

**Open question:** a film deleted from All but still saved in the Stremio library would come back on the next sync. Leaning towards the simplest option for now: the Stremio library is the source of truth for synced films, so the UI doesn't offer deleting them from All and instead says to remove the film from the Stremio library, and the next sync removes it here. Films added manually (not from Stremio) can still be deleted from All. Other options for later: remember deleted films and skip them during sync, or also remove them from the Stremio library.

## Milestone 6: Add to collection from inside Stremio

Stremio lets addons add sources to a film's page, not buttons, so each collection appears as a source. Selecting one opens Stremio's Discover screen on an addon address that carries the action (`/do/add/{collection}/{imdb id}/manifest.json`). Stremio requests a catalog from that address, which files the film and answers with a confirmation card. Nothing plays, so the film isn't marked as watched.

- [x] Stream resource for `tt` IDs (series episodes map to the series): one entry per collection, ＋ Add to French or ✓ In LGBTQ+ (select to remove), for films in the library
- [x] Action address with explicit add or remove (safe to request twice), answering with a ✓ Added to or ✓ Removed from card
- [x] Per app links, chosen from the request's origin: a web.strem.io address for Stremio Web (stays in the browser), `stremio://` links for the other apps (the Android TV app opens externalUrl, not androidTvUrl)
- [x] Entry opening the web app with the film searched (desktop and phone)
- [x] Sync on the spot: a film saved in Stremio moments ago is brought in when its sources are opened, so the entries appear without waiting for the scheduled sync
- [x] Tested on Stremio Web, the Stremio desktop app and the Android TV app (Sony)
- [ ] The source list only refreshes when the film is reopened (Stremio loads it once)
- [ ] Stremio shows This addon is not installed on the confirmation screen, and the TV app falls back to another Discover catalog; look for a cleaner landing screen

Tried first and dropped: redirecting to a short confirmation clip (playing it marked films as watched and added them to Continue Watching), and passing the action as a search value (the TV app drops free-text values from Discover links).

## Milestone 7: Multiple users (done)

Invite only, for a few friends. Each user has their own library, collections, Stremio connection and addon address.

- [x] `user_tokens` table: web and addon tokens per user, stored as SHA-256 hashes, each with a label, last use and revocation
- [x] The single-user tokens and Stremio key moved into the first account (`import-env`), so the existing addon and sign-in kept working without reinstalling
- [x] Each user's Stremio auth key encrypted at rest (Fernet, `ENCRYPTION_KEY`)
- [x] Sync runs per user with their own key; one user's failure doesn't stop the others but still fails the scheduled job, so it gets noticed
- [x] Invite command and single-use invite links (the token travels after the `#`, so it never reaches server logs, and is removed from the address bar)
- [x] Email and password login: Argon2id hashes, the same answer and timing for a wrong email or a wrong password, a 15-minute pause after 5 failures, one session per device, sign-out ends that session
- [x] Forgotten password: `new-link` sends a link that lets the user choose a new password
- [x] Connect Stremio in the web app: email and password exchanged for an auth key once (never stored), or a pasted access key for Google, Facebook and Apple sign-ins
- [x] Personal addon address with one-click install for the Stremio app and Stremio Web
- [x] Account links in the sidebar: install in Stremio, set up or change the login, disconnect Stremio, sign out
- [x] Backend tests (pytest, in-memory SQLite) and a Tests workflow on GitHub Actions, including isolation between users

## Milestone 8: Notes on films (done)

A short personal note per film (who recommended it, why it's special), independent of collections.

- [x] Nullable `note` column on `titles`, up to 120 characters so it fits fully in Stremio; saved through the existing film update endpoint (an empty note clears it)
- [x] Note icon at the bottom right of each poster: gold and always visible when there's a note (hovering shows it), on hover otherwise, always visible on touch screens
- [x] Small editor over the poster to add, edit or delete the note, with a character count; Enter saves, Escape or a click outside closes
- [x] Search matches notes too (for example, every film recommended by Ana)
- [x] In Stremio, the note is the first Cinémathèque entry on the film's page (web, desktop and TV), broken into short lines because Stremio cuts long ones; selecting it just reopens the page
- [x] Tests: add, edit, clear, the 120 character limit, isolation between users, search, and the Stremio entry

Known limit: a film removed from the Stremio library is deleted by the sync, and its note with it.

## Later
- [ ] Drag a poster from All onto a collection in the sidebar to add it (dnd-kit, one shared drag context for posters and collection reordering; the menu stays as the accessible way)
- [ ] Decide whether the app can add films itself, and how: TMDB search adding films that aren't in the Stremio library (two kinds of films, different delete rules), or adding them here and to the Stremio library at the same time (one source of truth, but writes through the unofficial Stremio API)
- [ ] Letterboxd watchlist import (via the Letterboxd addon catalog, with CSV export as fallback)
- [ ] TMDB enrichment: directors, cast, countries, genres, year
- [ ] Filter catalogs by director, country, year and actor, with `search` syntax such as `director:almodovar year:1990-2005`
- [ ] Password reset by email (needs an email service; for now `new-link` covers it)
- [ ] More tests: catalog paging, collection ordering, sync edge cases
