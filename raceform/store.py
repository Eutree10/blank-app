"""Local persistence.

Subjective feedback, goals, habits and Strava tokens are written to a JSON
file next to the app so the athlete's answers survive a restart. Activities
are cached separately because they are large and immutable.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .models import Activity, AthleteProfile, Feedback, Goal, HabitDay, PlannedSession

DATA_DIR = Path(os.environ.get("RACEFORM_DATA_DIR", Path.home() / ".raceform"))
STATE_FILE = DATA_DIR / "state.json"
ACTIVITY_FILE = DATA_DIR / "activities.json"


@dataclass
class AppState:
    """Everything the athlete owns, independent of where activities came from."""

    profile: AthleteProfile = field(default_factory=AthleteProfile)
    goals: list[Goal] = field(default_factory=list)
    feedback: dict[str, Feedback] = field(default_factory=dict)
    habits: dict[date, HabitDay] = field(default_factory=dict)
    plan_overrides: dict[str, PlannedSession] = field(default_factory=dict)
    tokens: dict[str, Any] | None = None
    primary_goal_id: str | None = None

    def primary_goal(self) -> Goal | None:
        """The A-priority goal the plan is built around."""
        if not self.goals:
            return None
        if self.primary_goal_id:
            for goal in self.goals:
                if goal.id == self.primary_goal_id:
                    return goal
        upcoming = [goal for goal in self.goals if goal.days_left >= 0]
        pool = upcoming or self.goals
        pool.sort(key=lambda goal: (goal.priority, goal.days_left))
        return pool[0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "goals": [goal.to_dict() for goal in self.goals],
            "feedback": {key: value.to_dict() for key, value in self.feedback.items()},
            "habits": {day.isoformat(): habit.to_dict() for day, habit in self.habits.items()},
            "plan_overrides": {key: value.to_dict() for key, value in self.plan_overrides.items()},
            "tokens": self.tokens,
            "primary_goal_id": self.primary_goal_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppState":
        return cls(
            profile=AthleteProfile.from_dict(data.get("profile") or {}),
            goals=[Goal.from_dict(item) for item in data.get("goals") or []],
            feedback={
                key: Feedback.from_dict(value)
                for key, value in (data.get("feedback") or {}).items()
            },
            habits={
                date.fromisoformat(key): HabitDay.from_dict(value)
                for key, value in (data.get("habits") or {}).items()
            },
            plan_overrides={
                key: PlannedSession.from_dict(value)
                for key, value in (data.get("plan_overrides") or {}).items()
            },
            tokens=data.get("tokens"),
            primary_goal_id=data.get("primary_goal_id"),
        )


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, payload: Any) -> None:
    """Write via a temp file so a crash never leaves truncated JSON behind."""
    _ensure_dir()
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def load_state() -> AppState:
    if not STATE_FILE.exists():
        return AppState()
    try:
        return AppState.from_dict(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError):
        # A corrupt file must not lock the athlete out of the app.
        return AppState()


def save_state(state: AppState) -> None:
    _atomic_write(STATE_FILE, state.to_dict())


def load_activities() -> list[Activity]:
    if not ACTIVITY_FILE.exists():
        return []
    try:
        payload = json.loads(ACTIVITY_FILE.read_text(encoding="utf-8"))
        return [Activity.from_dict(item) for item in payload]
    except (ValueError, KeyError, TypeError):
        return []


def save_activities(activities: list[Activity]) -> None:
    _atomic_write(ACTIVITY_FILE, [activity.to_dict() for activity in activities])


def merge_activities(existing: list[Activity], incoming: list[Activity]) -> list[Activity]:
    """Union by id, with incoming winning — a re-import can add laps."""
    merged = {activity.id: activity for activity in existing}
    for activity in incoming:
        merged[activity.id] = activity
    return sorted(merged.values(), key=lambda activity: activity.start_date)


def clear_all() -> None:
    for path in (STATE_FILE, ACTIVITY_FILE):
        if path.exists():
            path.unlink()
