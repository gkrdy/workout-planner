# AI Workout Planner (API)

Plan workouts by chatting with Claude, save them through my own Python API, and see them on my iPhone.

```
Claude (connector)  →  FastAPI /mcp           ┐
iPhone app (Expo)   →  FastAPI /api/workouts  ├→  store (in memory now, Supabase in CP3)
Safari              →  FastAPI /workouts      ┘
```

The iPhone app is a **separate project**: [`../workout-planner-app`](../workout-planner-app)
(github.com/gkrdy/workout-planner-app). Keep the two separate.

## Where things stand (2026-10-03)

| Piece | Status |
| --- | --- |
| API on Render | Live at https://workout-planner-dj04.onrender.com (free tier, sleeps after ~15 min idle) |
| Claude connector | Added in Claude as **Workout Planner**, URL `…/mcp?key=<API_KEY>` |
| iPhone app | Works in Expo Go, shows "Workout for Today" from `/api/workouts` |
| Storage | **In memory only**: wiped whenever Render sleeps, restarts or redeploys |
| Tests | 10 passing (`pytest -q`) |

The `API_KEY` lives in Render → service → **Environment**. It's never in the repo.

## Checklist

- [x] **CP1: FastAPI app.** `/health` and `/workouts` (escaped HTML, API key)
- [x] **CP2: Claude connector.** MCP tools at `/mcp`: `save_workout_plan`, `get_workouts`, `update_workout`, `delete_workout`
- [x] **Deploy + test:** on Render, connector added, workout saved via Claude and shown on `/workouts`
- [x] **CP4: iPhone app (Expo)** in `../workout-planner-app`, plus `GET /api/workouts` (JSON) here for it
- [ ] **CP3: Supabase, permanent storage** ← *next session* (chosen to do last)
  - [ ] You: create a free Supabase project; copy the Project URL and secret key
  - [ ] Me: SQL to create the `workouts` table
  - [ ] Me: `store.py` reads and writes Supabase (in-memory kept for tests)
  - [ ] You: add `SUPABASE_URL` and `SUPABASE_KEY` in Render, redeploy
  - [ ] Test: save via Claude, wait 20+ minutes for Render to sleep, data is still there (web + app)
- [ ] **CP5 (optional):** standalone iPhone app (Apple Developer account, EAS build) and/or paid hosting so Render never sleeps

## Starting the next session

1. If the Render service is **suspended**: dashboard.render.com → workout-planner → **Resume Web Service**.
2. Open `https://workout-planner-dj04.onrender.com/health` to wake it (30–60 s the first time).
3. Tell Claude: **"let's do checkpoint 3"** (Supabase).

## Run locally

Needs Python 3.10+.

```bash
cd ~/projects/workout-planner
python3 -m venv .venv            # first time only
source .venv/bin/activate
pip install -r requirements-dev.txt

pytest -q                        # expect: 10 passed
SEED_SAMPLE_DATA=true uvicorn app.main:app --reload
```

Without `API_KEY` set, nothing needs a key locally. To test with one:
`API_KEY=local-test-key uvicorn app.main:app --reload`.

## Endpoints

| Endpoint | What it returns | Key needed |
| --- | --- | --- |
| `GET /health` | `{"status":"ok"}` | no |
| `GET /workouts` | HTML for this week (`?date=YYYY-MM-DD` one day, `?week=YYYY-MM-DD` that week, `&fragment=true` cards only) | yes |
| `GET /api/workouts` | Same filters as JSON: `{"start","end","workouts":[…]}` (used by the iPhone app) | yes |
| `POST /mcp` | MCP connector for Claude | yes |
| `GET /docs` | FastAPI docs | no |

Key = `X-API-Key` header or `?key=` query parameter.

## Deploy

Render deploys automatically on every push to `main` (config in `render.yaml`).
A deploy wipes the in-memory workouts until CP3 is done.

## Things to know

- **First request after sleep takes 30–60 s.** If Claude says the connector failed, open `/health` to wake it and ask again.
- `SEED_SAMPLE_DATA` is `false` on Render, so `/workouts` is empty until Claude saves something.
- The key sits in the connector URL because Claude's connector form only takes a URL. Treat that URL like a password.

## Project layout

```
app/
  main.py        FastAPI routes (/health, /workouts, /api/workouts) + API key check, mounts the connector
  mcp_server.py  the tools Claude calls (save/get/update/delete)
  models.py      Exercise / Workout shapes (shared by API and tools)
  store.py       storage (in memory now, Supabase in CP3; same function names)
  render.py      data → HTML, every value escaped
tests/           pytest tests
render.yaml      Render deploy config
```
