# Deployment (free tier)

This is a guide to do together when ready to go live - it needs accounts and credentials that
belong to the project owner, so it isn't something to run unattended. Everything below is free at
the traffic levels this app expects (~10k users, first year).

## What you'll need

- A GitHub account, with this repo (`TSP Solutions/`) pushed to it.
- A [Vercel](https://vercel.com) or [Netlify](https://netlify.com) account (frontend hosting).
- A [Render](https://render.com) or [Fly.io](https://fly.io) account (backend hosting).
- A [Neon](https://neon.tech) or [Supabase](https://supabase.com) account (free Postgres) - **not
  optional in production**: Render/Fly's free-tier filesystem is ephemeral, so the local SQLite
  file (`workspace/app.db`) would be wiped on every redeploy or restart if you didn't switch to a
  real database first.

## 1. Database: Neon or Supabase (free Postgres)

1. Create a project, grab the connection string it gives you (`postgres://user:pass@host/dbname`).
2. Set that as `DATABASE_URL` wherever the backend runs (step 2 below). `app/config.py`'s
   `sqlalchemy_url` property normalizes `postgres://`/`postgresql://` into the
   `postgresql+psycopg://` form SQLAlchemy needs automatically - just set the plain connection
   string, nothing else to translate by hand.
3. From your machine, with `DATABASE_URL` set to that connection string, run the ETL once against
   it to populate the tables:
   ```bash
   cd backend
   DATABASE_URL="postgres://..." ./.venv/Scripts/python -m app.etl.run_all
   ```
   (On Windows PowerShell: `$env:DATABASE_URL="postgres://..."; ./.venv/Scripts/python -m app.etl.run_all`)

## 2. Backend: Render or Fly.io

Render's free web service is the simpler of the two (no CLI/Dockerfile required):

1. New Web Service -> connect the GitHub repo -> root directory `backend/`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment variables:
   - `DATABASE_URL` - the Neon/Supabase connection string from step 1.
   - `APP_PASSWORD` - a real password (auth is a no-op if this is unset - don't leave it unset in
     production).
   - `SESSION_SECRET` - a random string (`python -c "import secrets; print(secrets.token_hex(32))"`).
5. Note the URL Render gives you (e.g. `https://tsp-solutions-backend.onrender.com`) - the frontend
   needs it next.

Render's free tier spins the service down after inactivity and takes ~30-60s to wake back up on
the next request - fine for an internal sales tool that isn't hit constantly, worth knowing about
if the first request of the day feels slow.

## 3. Frontend: Vercel or Netlify

1. New Project -> connect the same GitHub repo -> root directory `frontend/`.
2. Build command: `npm run build`. Output directory: `dist`.
3. Before deploying, point the frontend at the deployed backend instead of `127.0.0.1:8000` - edit
   `BASE_URL` in `frontend/src/api/client.ts` to the Render URL from step 2, or (cleaner) change it
   to read `import.meta.env.VITE_API_BASE_URL` and set that env var in Vercel/Netlify's project
   settings, so the same code works locally and deployed without an edit each time.
4. Deploy. Vercel/Netlify give you an HTTPS URL immediately.

## 4. Connect them

Update `backend/app/main.py`'s CORS `allow_origins` list to include the deployed frontend URL
(alongside the existing `localhost:5173` for local dev), redeploy the backend, and confirm the
deployed frontend can reach `/api/health`.

## When to revisit these choices

- **OSRM** (`app/routing.py`) - the public demo server is fine for occasional route lookups but
  isn't meant for sustained production traffic. If route-planning gets used heavily, self-host
  OSRM (there's an official Docker image) or switch to a paid routing API.
- **SQLite -> Postgres** - already covered above; do this before any real deployment, not after.
- **Shared-password auth -> real accounts** - fine for a small internal team; once more than a
  handful of people use this, per-user accounts (e.g. Supabase Auth, which you'd already have a
  project for if you picked Supabase over Neon for the database) let you track who did what and
  revoke access individually instead of everyone sharing one password.
- **Snowflake / Databricks / Kubernetes** - the brief mentioned these; genuinely not needed at this
  project's data volume (tens of thousands of rows) or user count (10k/year). Revisit if the
  customer dataset grows to genuinely large scale (millions of transactions) or multiple services
  need independent scaling - see `05-future-work.md`.
