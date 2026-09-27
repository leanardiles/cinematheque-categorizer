# Roadmap

Progress tracker for Cinematheque Categorizer. Checked items are done.

## Milestone 1: Addon skeleton (done)

- [x] Repo, `.gitignore`, `.gitattributes`
- [x] Secrets in 1Password, loaded with `op run` via `.env.op`
- [x] Supabase project, TMDB API access, Vercel account
- [x] FastAPI app with token-protected `manifest.json` and a sample catalog
- [x] CORS for Stremio Web
- [x] Installed in Stremio Web through a Cloudflare quick tunnel
- [x] Dev script opening backend, tunnel and dev shell windows

## Milestone 2: Database

- [ ] Commit the current work (README, dev script, line ending rules)
- [ ] SQLAlchemy engine for the Supabase transaction pooler (disable prepared statements, use `NullPool`)
- [ ] Models: `titles`, `people`, `title_people` (role and order), `countries`, `title_countries`, `tags`, `title_tags`
- [ ] Migrations with Alembic
- [ ] Catalog route reads titles from the database instead of the hardcoded sample
- [ ] Verify the row still loads and plays in Stremio

## Milestone 3: TMDB enrichment

- [ ] TMDB client with httpx (lookup by IMDb ID via `/find`)
- [ ] Fetch directors, top billed cast, countries, year and poster; cache in the database
- [ ] Script or endpoint to add a title by IMDb ID and enrich it

## Milestone 4: Filter catalogs

- [ ] One catalog per dimension: director, custom genre, country, year, actor
- [ ] Dropdown options generated dynamically in the manifest from the database
- [ ] Movies and series catalogs
- [ ] `search` extra with a mini query language, for example `director:almodovar country:es year:1990-2005`
- [ ] Pagination with `skip`

## Milestone 5: Tagging API and UI

- [ ] API endpoints to list titles and add or remove tags (protected)
- [ ] React + Vite tagging UI
- [ ] TMDB attribution in the UI footer
- [ ] Optional stream entry in Stremio: Tag this title, linking to the UI

## Milestone 6: Stremio library sync

- [ ] Research the unofficial Stremio library API; document findings in `docs/reference/stremio-library-api.md`
- [ ] Sync endpoint protected by `SYNC_SECRET`; keep only titles saved on purpose
- [ ] GitHub Actions scheduled workflow calling the sync endpoint

## Milestone 7: Deployment

- [ ] Deploy FastAPI and the UI on Vercel
- [ ] Environment variables in Vercel
- [ ] Install the production manifest in Stremio; save the URL in 1Password

## Housekeeping

- [ ] Save Stremio addon protocol docs in `docs/reference/stremio-addon-protocol/` with source and commit noted
- [ ] Renormalize line endings (`git add --renormalize .`)
- [ ] Tests for catalog filtering and the query parser
