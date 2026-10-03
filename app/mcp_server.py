"""MCP connector: the tools Claude calls to save and read workouts.

Claude talks to these over HTTP at /mcp. Each tool is a plain Python function;
the MCP library turns its signature and docstring into a tool Claude can see.
"""
import datetime as dt
import os
import secrets
from urllib.parse import parse_qs

from mcp.server.mcpserver import MCPServer

from . import store
from .models import Exercise, Workout

mcp = MCPServer(
    "Workout Planner",
    instructions=(
        "Saves and reads the user's workout plans. When the user agrees on a plan, "
        "call save_workout_plan with one entry per training day. Use real calendar "
        "dates (YYYY-MM-DD). Rest days can be left out."
    ),
)


def _as_dict(w: Workout) -> dict:
    return w.model_dump(mode="json")


@mcp.tool()
def save_workout_plan(workouts: list[Workout]) -> dict:
    """Save a plan of one or more workout days (for example a whole week).

    Each item has a date (YYYY-MM-DD), a day name like "Monday", and a list of
    exercises with name, sets and reps. Saving a date that already has a
    workout replaces it.
    """
    saved = [store.upsert_workout(w) for w in workouts]
    return {
        "saved": len(saved),
        "dates": [w.date.isoformat() for w in saved],
    }


@mcp.tool()
def get_workouts(start_date: dt.date, end_date: dt.date | None = None) -> list[dict]:
    """Get saved workouts from start_date to end_date (inclusive, YYYY-MM-DD).

    Leave end_date out to get a single day.
    """
    return [_as_dict(w) for w in store.list_workouts(start_date, end_date or start_date)]


@mcp.tool()
def update_workout(date: dt.date, exercises: list[Exercise], day: str | None = None) -> dict:
    """Replace the exercises for one date (creates the day if it doesn't exist).

    day defaults to the weekday name of the date.
    """
    w = store.upsert_workout(Workout(date=date, day=day or date.strftime("%A"), exercises=exercises))
    return _as_dict(w)


@mcp.tool()
def delete_workout(date: dt.date) -> dict:
    """Remove the workout saved for one date (YYYY-MM-DD)."""
    return {"deleted": store.delete_workout(date), "date": date.isoformat()}


class RequireKey:
    """ASGI wrapper: when API_KEY is set, require it as ?key=... or an X-API-Key header.

    Claude's custom connector form only takes a URL, so the key goes in the
    URL: https://<your-app>.onrender.com/mcp?key=<API_KEY>
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        expected = os.getenv("API_KEY")
        if scope["type"] == "http" and expected:
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            query = parse_qs(scope.get("query_string", b"").decode())
            supplied = headers.get("x-api-key") or (query.get("key") or [""])[0]
            if not secrets.compare_digest(supplied, expected):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body",
                            "body": b'{"detail":"Missing or wrong API key"}'})
                return
        await self.app(scope, receive, send)


def build_mcp_app():
    # stateless + JSON responses: simplest mode, survives server restarts.
    # host="0.0.0.0" stops the library from only accepting "localhost" requests,
    # which would block calls to the Render URL.
    return RequireKey(
        mcp.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0")
    )
