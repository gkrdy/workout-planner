"""Storage layer.

For now workouts live in memory (lost when the server restarts or Render puts
it to sleep). The Supabase checkpoint replaces this file's internals; the
function names stay the same, so main.py and the MCP tools don't change.
"""
from datetime import date, timedelta

from .models import Exercise, Workout

_workouts: dict[date, Workout] = {}


def week_bounds(d: date) -> tuple[date, date]:
    """Monday..Sunday of the week containing d."""
    start = d - timedelta(days=d.weekday())
    return start, start + timedelta(days=6)


def list_workouts(start: date, end: date) -> list[Workout]:
    return sorted((w for d, w in _workouts.items() if start <= d <= end), key=lambda w: w.date)


def upsert_workout(workout: Workout) -> Workout:
    _workouts[workout.date] = workout
    return workout


def delete_workout(d: date) -> bool:
    return _workouts.pop(d, None) is not None


def clear() -> None:
    _workouts.clear()


def seed_sample_week(today: date | None = None) -> None:
    """Fill the current week with a simple push/pull/legs plan."""
    monday, _ = week_bounds(today or date.today())
    plan = {
        0: [("Bench Press", 4, "8"), ("Overhead Press", 3, "10"), ("Tricep Dips", 3, "12")],
        1: [("Deadlift", 4, "5"), ("Pull-ups", 3, "8"), ("Barbell Row", 3, "10")],
        2: [("Back Squat", 4, "6"), ("Romanian Deadlift", 3, "10"), ("Walking Lunges", 3, "12 each")],
        4: [("Incline Dumbbell Press", 3, "10"), ("Lat Pulldown", 3, "12"), ("Plank", 3, "45s")],
        5: [("Easy Run", 1, "30 min")],
    }
    for offset, items in plan.items():
        d = monday + timedelta(days=offset)
        upsert_workout(
            Workout(
                date=d,
                day=d.strftime("%A"),
                exercises=[Exercise(name=n, sets=s, reps=r) for n, s, r in items],
            )
        )
