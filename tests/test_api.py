from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.models import Exercise, Workout

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_store(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    store.clear()
    store.seed_sample_week(date(2026, 10, 5))  # a Monday
    yield
    store.clear()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_week_view():
    r = client.get("/workouts?week=2026-10-07")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Bench Press" in r.text and "Easy Run" in r.text
    assert r.text.count('class="workout"') == 5


def test_single_day_and_fragment():
    r = client.get("/workouts?date=2026-10-06&fragment=true")
    assert "Deadlift" in r.text and "Bench Press" not in r.text
    assert not r.text.startswith("<!doctype")


def test_empty_day():
    r = client.get("/workouts?date=2026-10-08")
    assert "No workouts planned" in r.text


def test_html_is_escaped():
    store.upsert_workout(
        Workout(
            date=date(2026, 10, 8),
            day="<b>Thursday</b>",
            exercises=[Exercise(name="<script>alert(1)</script>", sets=1, reps="5")],
        )
    )
    r = client.get("/workouts?date=2026-10-08")
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text and "&lt;b&gt;Thursday" in r.text


def test_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "s3cret")
    assert client.get("/workouts").status_code == 401
    assert client.get("/workouts?key=wrong").status_code == 401
    assert client.get("/workouts?key=s3cret").status_code == 200
    assert client.get("/workouts", headers={"X-API-Key": "s3cret"}).status_code == 200
    assert client.get("/health").status_code == 200  # health stays open


MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def _call(c, name, args, key=None):
    url = "/mcp" + (f"?key={key}" if key else "")
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}
    return c.post(url, json=body, headers=MCP_HEADERS)


@pytest.fixture(scope="module")
def mcp_client():
    # "with" runs the MCP lifespan, which can only start once per process,
    # so all MCP tests share this one client.
    with TestClient(app) as c:
        yield c


def test_mcp_save_then_view(mcp_client):
    store.clear()
    tools = mcp_client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, headers=MCP_HEADERS
    )
    names = {t["name"] for t in tools.json()["result"]["tools"]}
    assert names == {"save_workout_plan", "get_workouts", "update_workout", "delete_workout"}

    r = _call(mcp_client, "save_workout_plan", {"workouts": [
        {"date": "2026-10-12", "day": "Monday", "exercises": [{"name": "Squat", "sets": 5, "reps": "5"}]},
    ]})
    assert r.status_code == 200 and not r.json()["result"].get("isError")

    page = mcp_client.get("/workouts?date=2026-10-12")
    assert "Squat" in page.text


def test_mcp_requires_key(mcp_client, monkeypatch):
    monkeypatch.setenv("API_KEY", "s3cret")
    assert _call(mcp_client, "get_workouts", {"start_date": "2026-10-12"}).status_code == 401
    ok = _call(mcp_client, "get_workouts", {"start_date": "2026-10-12"}, key="s3cret")
    assert ok.status_code == 200
