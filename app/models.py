"""Data shapes shared by the REST API, the MCP tools (later) and the database layer."""
import datetime as dt

from pydantic import BaseModel, Field


class Exercise(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    sets: int = Field(ge=1, le=50)
    reps: str = Field(min_length=1, max_length=30, description='e.g. "10", "8-12", "30s"')


class Workout(BaseModel):
    date: dt.date
    day: str = Field(description='e.g. "Monday"')
    exercises: list[Exercise] = Field(default_factory=list)
