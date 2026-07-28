"""Shared fixtures and small builders for constructing activities in tests."""

from __future__ import annotations

from datetime import datetime

import pytest

from raceform.analysis.physiology import zones_for
from raceform.demo import build_demo_history
from raceform.models import Activity, Lap


def lap(index: int, distance_m: float, pace_s_km: float, **kwargs) -> Lap:
    """A lap defined by the pace a runner would quote, not by raw seconds."""
    return Lap(
        index=index,
        distance_m=distance_m,
        moving_time_s=pace_s_km * distance_m / 1000,
        elapsed_time_s=pace_s_km * distance_m / 1000,
        **kwargs,
    )


def interval_activity(
    reps: int,
    rep_m: float,
    rep_pace: float,
    recovery_s: float = 120,
    recovery_pace: float = 400,
    warmup_m: float = 3000,
    cooldown_m: float = 2000,
    easy_pace: float = 300,
    name: str = "Series",
    when: datetime | None = None,
    rep_paces: list[float] | None = None,
    elevation_per_rep: float = 0.0,
) -> Activity:
    """A structured session with warm-up, alternating work/recovery, cool-down."""
    laps: list[Lap] = []
    if warmup_m:
        laps.append(lap(0, warmup_m, easy_pace, name="Entrada en calor"))
    for index in range(reps):
        pace = rep_paces[index] if rep_paces else rep_pace
        laps.append(
            lap(
                len(laps), rep_m, pace,
                elevation_gain_m=elevation_per_rep,
                average_heartrate=178,
                max_heartrate=186,
                name=f"Rep {index + 1}",
            )
        )
        if index < reps - 1:
            recovery_distance = recovery_s / recovery_pace * 1000
            laps.append(
                lap(
                    len(laps), recovery_distance, recovery_pace,
                    average_heartrate=150, max_heartrate=160, name="Recuperación",
                )
            )
    if cooldown_m:
        laps.append(lap(len(laps), cooldown_m, easy_pace, name="Vuelta a la calma"))

    distance = sum(item.distance_m for item in laps)
    moving = sum(item.moving_time_s for item in laps)
    return Activity(
        id=f"test-{name}-{reps}x{rep_m:.0f}",
        name=name,
        start_date=when or datetime(2026, 7, 21, 7, 0),
        distance_m=distance,
        moving_time_s=moving,
        elevation_gain_m=elevation_per_rep * reps,
        average_heartrate=165,
        laps=laps,
    )


def continuous_activity(
    distance_m: float,
    pace_s_km: float,
    name: str = "Rodaje",
    when: datetime | None = None,
    elevation_gain_m: float = 0.0,
    hr_start: float | None = None,
    hr_drift: float = 0.0,
) -> Activity:
    """A run with automatic 1 km splits and no lap structure."""
    splits: list[Lap] = []
    covered = 0.0
    index = 0
    while covered < distance_m - 1:
        chunk = min(1000.0, distance_m - covered)
        heart_rate = (hr_start + hr_drift * index) if hr_start else None
        splits.append(
            lap(
                index, chunk, pace_s_km,
                average_heartrate=heart_rate,
                elevation_gain_m=elevation_gain_m * chunk / distance_m,
                name=f"km {index + 1}",
            )
        )
        covered += chunk
        index += 1

    return Activity(
        id=f"test-{name}-{distance_m:.0f}",
        name=name,
        start_date=when or datetime(2026, 7, 20, 7, 0),
        distance_m=distance_m,
        moving_time_s=pace_s_km * distance_m / 1000,
        elevation_gain_m=elevation_gain_m,
        average_heartrate=hr_start,
        splits_km=splits,
    )


@pytest.fixture(scope="session")
def demo():
    """The full demo athlete: activities, feedback, habits, goals, profile."""
    activities, feedback, habits, goals, profile = build_demo_history()
    return {
        "activities": activities,
        "feedback": feedback,
        "habits": habits,
        "goals": goals,
        "profile": profile,
    }


@pytest.fixture(scope="session")
def zones():
    """Zones for a 17:20 5K runner — the reference athlete across the tests."""
    return zones_for(58.8)
