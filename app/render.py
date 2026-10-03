"""Turns workout data into HTML. Every value from the data is escaped."""
from datetime import date
from html import escape

from .models import Workout

PAGE_STYLE = """
body{font-family:-apple-system,system-ui,sans-serif;margin:0;padding:16px;background:#f6f6f4;color:#1d1d1b}
h1{font-size:1.4rem;margin:0 0 12px}
.workout{background:#fff;border-radius:12px;padding:12px 16px;margin-bottom:12px;box-shadow:0 1px 2px rgba(0,0,0,.06)}
.workout h2{font-size:1.05rem;margin:0 0 8px}
.workout h2 small{color:#777;font-weight:400}
.workout ul{margin:0;padding-left:18px}
.workout li{margin:4px 0}
.sr{color:#555}
.empty{color:#777}
@media (prefers-color-scheme:dark){body{background:#121212;color:#eee}.workout{background:#1e1e1e}.sr,.workout h2 small,.empty{color:#aaa}}
"""


def render_workout(w: Workout) -> str:
    if w.exercises:
        items = "".join(
            f'<li>{escape(e.name)} <span class="sr">{e.sets} × {escape(e.reps)}</span></li>'
            for e in w.exercises
        )
        body = f"<ul>{items}</ul>"
    else:
        body = '<p class="empty">Rest day</p>'
    return (
        f'<section class="workout" data-date="{w.date.isoformat()}">'
        f"<h2>{escape(w.day)} <small>{w.date.strftime('%b %d')}</small></h2>{body}</section>"
    )


def render_fragment(workouts: list[Workout]) -> str:
    if not workouts:
        return '<p class="empty">No workouts planned for this period.</p>'
    return "".join(render_workout(w) for w in workouts)


def render_page(workouts: list[Workout], start: date, end: date) -> str:
    title = (
        f"Workouts · {start.strftime('%b %d')}"
        if start == end
        else f"Workouts · {start.strftime('%b %d')} – {end.strftime('%b %d')}"
    )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{escape(title)}</title><style>{PAGE_STYLE}</style></head>"
        f"<body><h1>{escape(title)}</h1>{render_fragment(workouts)}</body></html>"
    )
