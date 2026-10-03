# AI Workout Planner

Plan workouts by chatting with Claude, save them through my own Python API, and view them on my iPhone.

```
Claude  →  FastAPI /mcp       →  Supabase (Postgres)
iPhone  →  FastAPI /workouts  →  Supabase (Postgres)
```

## Checklist

- [x] **CP1: FastAPI app.** `/health` and `/workouts` (escaped HTML, API key). Your local test passed (6 tests).
- [x] **CP2: Claude → FastAPI connector.** MCP tools at `/mcp`: `save_workout_plan`, `get_workouts`, `update_workout`, `delete_workout` (8 tests pass)
  - Data is stored **in memory only** (the `_workouts` dict in `app/store.py`). It's lost when the server restarts, redeploys or Render puts it to sleep.
- [x] **Test:** deployed to Render (https://workout-planner-dj04.onrender.com), Claude connector added, workout saved via Claude and shown on `/workouts` (2026-10-03)
- [ ] **CP3: Supabase, permanent storage** ← *you are here*
  - [ ] You: create a free Supabase project; copy the Project URL and secret key
  - [ ] Me: SQL to create the `workouts` table
  - [ ] Me: `store.py` reads and writes Supabase (in-memory kept for tests)
  - [ ] You: add `SUPABASE_URL` and `SUPABASE_KEY` in Render, redeploy
  - [ ] Test: save a week via Claude, wait 20+ minutes for Render to sleep, data is still there
- [ ] **CP4: iPhone web app (PWA).** Home-screen app that loads `/workouts`
- [ ] **CP5 (optional):** Expo app and/or paid hosting

---

## Test it

Needs Python 3.10 or newer (`python3 --version`).

### 1. Run locally (Mac Terminal)

```bash
cd ~/projects/workout-planner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

pytest -q                          # expect: 8 passed
SEED_SAMPLE_DATA=true uvicorn app.main:app --reload
```

| URL | You should see |
| --- | --- |
| http://127.0.0.1:8000/health | `{"status":"ok"}` |
| http://127.0.0.1:8000/workouts | This week's demo workouts as cards |
| http://127.0.0.1:8000/workouts?date=2026-10-06 | Just that day |
| http://127.0.0.1:8000/docs | FastAPI's auto-generated docs |

Optional: try the connector locally with the MCP Inspector (`npx @modelcontextprotocol/inspector`),
transport **Streamable HTTP**, URL `http://127.0.0.1:8000/mcp`. Call `save_workout_plan`, then refresh `/workouts`.

### 2. Push to GitHub

Create an empty **private** repo on github.com named `workout-planner`, then:

```bash
git init
git add .
git commit -m "FastAPI app + Claude connector"
git branch -M main
git remote add origin https://github.com/<your-username>/workout-planner.git
git push -u origin main
```

### 3. Deploy to Render (free)

1. Sign in at https://dashboard.render.com with GitHub.
2. **New → Blueprint**, pick the `workout-planner` repo (Render reads `render.yaml`).
3. Wait for **Live**, then copy the generated `API_KEY` from the service's **Environment** tab.
4. Check `https://<your-app>.onrender.com/health` shows `{"status":"ok"}`.

### 4. Connect Claude

In Claude: **Settings → Connectors → Add custom connector**.

- Name: `Workout Planner`
- URL: `https://<your-app>.onrender.com/mcp?key=<API_KEY>`

Then in a new chat (with the connector turned on), try:

> Plan a 4-day strength week starting Monday Oct 5, 2026 and save it.

Claude should call `save_workout_plan`. Then ask "what's my Wednesday workout?" (it calls `get_workouts`)
and "swap Wednesday to legs" (it calls `update_workout`).

### 5. See it on the iPhone

Safari: `https://<your-app>.onrender.com/workouts?week=2026-10-05&key=<API_KEY>`

**Done when** the week Claude saved shows up on your phone.

### Things to know right now

- **Workouts are kept in memory.** Render's free tier sleeps after ~15 minutes idle, and that wipes them.
  Save and view in the same sitting for this test; CP3 (Supabase) makes them permanent.
- **First request after sleep takes 30 to 60 seconds.** If Claude says the connector failed, open `/health`
  in Safari to wake it, then ask Claude again.
- The key sits in the connector URL because Claude's connector form only takes a URL. Treat that URL like a password.

## Project layout

```
app/
  main.py        FastAPI routes + API key check, mounts the connector
  mcp_server.py  the tools Claude calls (save/get/update/delete)
  models.py      Exercise / Workout shapes (shared by API and tools)
  store.py       storage (in memory now, Supabase in CP3; same function names)
  render.py      data → HTML, every value escaped
tests/        pytest tests
render.yaml   Render deploy config
```
