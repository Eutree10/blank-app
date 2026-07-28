"""Domain model.

Everything downstream (analysis, planning, coach) reads these types, so the
Strava importer and the demo generator only have to agree on this shape.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from .formats import pace_of, speed_of


class WorkoutType(str, Enum):
    """The eight session families the app reasons about."""

    EASY = "rodaje"
    LONG = "fondo"
    TEMPO = "tempo"
    INTERVALS = "intervalos"
    REPS = "repeticiones cortas"
    HILLS = "cuestas"
    RACE = "competencia"
    TEST = "test"

    @property
    def label(self) -> str:
        return self.value.capitalize()

    @property
    def plural(self) -> str:
        """For sentences like 'tus últimos 6 rodajes'."""
        return {
            WorkoutType.EASY: "rodajes",
            WorkoutType.LONG: "fondos",
            WorkoutType.TEMPO: "tempos",
            WorkoutType.INTERVALS: "sesiones de intervalos",
            WorkoutType.REPS: "sesiones de repeticiones",
            WorkoutType.HILLS: "sesiones de cuestas",
            WorkoutType.RACE: "competencias",
            WorkoutType.TEST: "tests",
        }[self]

    @property
    def is_quality(self) -> bool:
        return self in {
            WorkoutType.TEMPO,
            WorkoutType.INTERVALS,
            WorkoutType.REPS,
            WorkoutType.HILLS,
            WorkoutType.RACE,
            WorkoutType.TEST,
        }

    @property
    def is_structured(self) -> bool:
        """Sessions built out of repetitions, where rep-level analysis applies."""
        return self in {WorkoutType.INTERVALS, WorkoutType.REPS, WorkoutType.HILLS}


class Capability(str, Enum):
    """The five qualities a race performance is decomposed into."""

    SPEED = "Velocidad"
    SPECIFIC_ENDURANCE = "Resistencia específica"
    AEROBIC_BASE = "Base aeróbica"
    CLOSING = "Capacidad de cierre"
    RECOVERY = "Recuperación"


@dataclass
class Lap:
    """A Strava lap or split. Distances in metres, times in seconds."""

    index: int
    distance_m: float
    moving_time_s: float
    elapsed_time_s: float | None = None
    average_heartrate: float | None = None
    max_heartrate: float | None = None
    elevation_gain_m: float = 0.0
    average_cadence: float | None = None
    name: str = ""

    @property
    def pace_s_km(self) -> float:
        return pace_of(self.distance_m, self.moving_time_s)

    @property
    def speed_ms(self) -> float:
        return speed_of(self.distance_m, self.moving_time_s)

    @property
    def grade(self) -> float:
        """Average gradient as a fraction (0.05 == 5%)."""
        if self.distance_m <= 0:
            return 0.0
        return self.elevation_gain_m / self.distance_m

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lap":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Activity:
    """One run. `laps` is empty when the source provided no structure."""

    id: str
    name: str
    start_date: datetime
    distance_m: float
    moving_time_s: float
    elapsed_time_s: float | None = None
    elevation_gain_m: float = 0.0
    average_heartrate: float | None = None
    max_heartrate: float | None = None
    average_cadence: float | None = None
    average_watts: float | None = None
    laps: list[Lap] = field(default_factory=list)
    splits_km: list[Lap] = field(default_factory=list)
    sport: str = "Run"
    strava_workout_type: int | None = None
    source: str = "demo"
    description: str = ""

    @property
    def day(self) -> date:
        return self.start_date.date()

    @property
    def km(self) -> float:
        return self.distance_m / 1000.0

    @property
    def pace_s_km(self) -> float:
        return pace_of(self.distance_m, self.moving_time_s)

    @property
    def duration_min(self) -> float:
        return self.moving_time_s / 60.0

    @property
    def has_hr(self) -> bool:
        return bool(self.average_heartrate)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["start_date"] = self.start_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Activity":
        data = dict(data)
        if isinstance(data.get("start_date"), str):
            data["start_date"] = datetime.fromisoformat(data["start_date"])
        data["laps"] = [Lap.from_dict(lap) for lap in data.get("laps", [])]
        data["splits_km"] = [Lap.from_dict(lap) for lap in data.get("splits_km", [])]
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Feedback:
    """The three questions asked after every session, plus optional notes."""

    activity_id: str
    rpe: int | None = None  # 1–10 perceived effort
    legs: int | None = None  # 1 dead … 5 springy
    niggle: str = ""  # free text, empty when nothing hurts
    niggle_severity: int = 0  # 0 none, 1 aware, 2 limiting, 3 stopping
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Feedback":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Goal:
    """A target race. `priority` A is the one the plan is built around."""

    id: str
    name: str
    distance_m: float
    race_date: date
    target_time_s: int | None = None
    priority: str = "A"
    terrain: str = "pista"  # pista | asfalto | trail
    notes: str = ""

    @property
    def days_left(self) -> int:
        return (self.race_date - date.today()).days

    @property
    def weeks_left(self) -> float:
        return self.days_left / 7.0

    @property
    def target_pace_s_km(self) -> float | None:
        if not self.target_time_s:
            return None
        return pace_of(self.distance_m, self.target_time_s)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["race_date"] = self.race_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Goal":
        data = dict(data)
        if isinstance(data.get("race_date"), str):
            data["race_date"] = date.fromisoformat(data["race_date"])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    @staticmethod
    def new(name: str, distance_m: float, race_date: date, **kwargs: Any) -> "Goal":
        return Goal(
            id=uuid.uuid4().hex[:8],
            name=name,
            distance_m=distance_m,
            race_date=race_date,
            **kwargs,
        )


@dataclass
class HabitDay:
    """Daily context that might explain a good or bad session."""

    day: date
    sleep_hours: float | None = None
    hydration: int | None = None  # 1–5
    mobility: bool = False
    strength: bool = False
    fueled_before: bool | None = None
    soreness: int | None = None  # 1–5, 5 is worst
    fatigue: int | None = None  # 1–5, 5 is worst

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["day"] = self.day.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HabitDay":
        data = dict(data)
        if isinstance(data.get("day"), str):
            data["day"] = date.fromisoformat(data["day"])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class PlannedSession:
    """One entry on the calendar. `structure` is the human-readable prescription."""

    id: str
    day: date
    workout_type: WorkoutType
    title: str
    structure: str
    purpose: str
    target_pace_low: float | None = None  # s/km, faster bound
    target_pace_high: float | None = None
    distance_m: float | None = None
    recovery_s: int | None = None
    key: bool = False  # a session the block depends on
    status: str = "pendiente"  # pendiente | hecho | saltado | movido
    completed_activity_id: str | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["day"] = self.day.isoformat()
        data["workout_type"] = self.workout_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlannedSession":
        data = dict(data)
        if isinstance(data.get("day"), str):
            data["day"] = date.fromisoformat(data["day"])
        if isinstance(data.get("workout_type"), str):
            data["workout_type"] = WorkoutType(data["workout_type"])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class AthleteProfile:
    """Static-ish athlete context. Everything else is derived from activities."""

    name: str = "Corredor"
    hr_max: int | None = None
    hr_rest: int | None = None
    birth_year: int | None = None
    weekly_km_target: float = 60.0
    days_per_week: int = 6
    long_run_day: int = 6  # 0 Monday … 6 Sunday
    quality_days: tuple[int, ...] = (1, 4)  # Tuesday and Friday
    strava_athlete_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["quality_days"] = list(self.quality_days)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AthleteProfile":
        data = dict(data)
        if "quality_days" in data:
            data["quality_days"] = tuple(data["quality_days"])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def week_start(day: date) -> date:
    """Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())
