"""FastAPI app.

Endpoints
  GET  /health                         -> {"status": "ok"}  (no key needed, for uptime pings)
  GET  /workouts                       -> HTML for the current week
  GET  /workouts?date=YYYY-MM-DD       -> HTML for that one day
  GET  /workouts?week=YYYY-MM-DD       -> HTML for the week containing that date
       add &fragment=true to get just the workout cards
  GET  /api/workouts?week=|date=       -> same filters, as JSON (used by the Expo app)
  POST /mcp                            -> MCP connector for Claude (see mcp_server.py)

Auth: if the API_KEY env var is set, /workouts, /api/workouts and /mcp need it either as an
`X-API-Key` header or a `?key=` query parameter.
"""
import os
import secrets
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from . import store
from .mcp_server import build_mcp_app, mcp
from .render import render_fragment, render_page

mcp_app = build_mcp_app()  # must be built before the lifespan runs


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():  # the MCP library needs this running
        yield


app = FastAPI(title="AI Workout Planner", lifespan=lifespan)

# Optional demo data so /workouts isn't empty before Claude saves anything.
if os.getenv("SEED_SAMPLE_DATA", "false").lower() == "true":
    store.seed_sample_week()


def require_key(
    x_api_key: str | None = Header(default=None),
    key: str | None = Query(default=None),
) -> None:
    expected = os.getenv("API_KEY")
    if not expected:  # no key configured -> open (local development)
        return
    supplied = x_api_key or key or ""
    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Missing or wrong API key")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/workouts", response_class=HTMLResponse, dependencies=[Depends(require_key)])
def get_workouts(
    date_: date | None = Query(default=None, alias="date"),
    week: date | None = None,
    fragment: bool = False,
) -> HTMLResponse:
    if date_:
        start = end = date_
    else:
        start, end = store.week_bounds(week or date.today())
    workouts = store.list_workouts(start, end)
    html = render_fragment(workouts) if fragment else render_page(workouts, start, end)
    return HTMLResponse(html)


@app.get("/api/workouts", dependencies=[Depends(require_key)])
def get_workouts_json(
    date_: date | None = Query(default=None, alias="date"),
    week: date | None = None,
) -> dict:
    """Same filters as /workouts, as JSON (used by the Expo app)."""
    if date_:
        start = end = date_
    else:
        start, end = store.week_bounds(week or date.today())
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "workouts": [w.model_dump(mode="json") for w in store.list_workouts(start, end)],
    }


# Mounted last so the routes above win; the MCP app answers at /mcp.
app.mount("/", mcp_app)
