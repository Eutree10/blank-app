"""A deterministic demo athlete.

The app is useless without data, and Strava needs an API key. This generates
eighteen weeks of physiologically coherent training for a runner improving from
about 17:45 to about 17:15 over 5K, so every screen can be evaluated before a
single real activity is imported.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

from .analysis.physiology import fraction_of_vdot, zones_for
from .models import (
    Activity,
    AthleteProfile,
    Feedback,
    Goal,
    HabitDay,
    Lap,
)

HR_MAX = 192
HR_REST = 44
SEED = 20260728

WEEKS = 18
START_VDOT = 56.2
END_VDOT = 59.1


def _hr_for(fraction: float, rng: random.Random, drift: float = 0.0) -> float:
    """Heart rate for an intensity, anchored on easy≈73% and VO2≈96% of max."""
    pct = 0.73 + 0.767 * (fraction - 0.68) + drift
    pct = max(0.55, min(0.98, pct))
    return round(HR_MAX * pct + rng.uniform(-2.5, 2.5))


def _recovery_hr(previous_hr: float, seconds: float, rng: random.Random) -> float:
    """Heart rate during a jog recovery.

    It decays from the rep towards a floor rather than dropping to jogging
    level: after 60 s a runner is still well above 70% of max, which is what
    makes between-rep HR recovery a usable signal.
    """
    floor = HR_MAX * 0.70
    decay = 1 - 0.5 ** (seconds / 95.0)  # roughly halves the gap every 95 s
    return round(previous_hr - (previous_hr - floor) * decay + rng.uniform(-2, 2))


def _lap(
    index: int,
    distance_m: float,
    pace_s_km: float,
    vdot: float,
    rng: random.Random,
    elevation: float = 0.0,
    drift: float = 0.0,
    name: str = "",
    hr_override: float | None = None,
) -> Lap:
    time_s = pace_s_km * distance_m / 1000
    fraction = fraction_of_vdot(pace_s_km, vdot)
    hr = hr_override if hr_override is not None else _hr_for(fraction, rng, drift)
    return Lap(
        index=index,
        distance_m=round(distance_m, 1),
        moving_time_s=round(time_s, 1),
        elapsed_time_s=round(time_s, 1),
        average_heartrate=hr,
        max_heartrate=round(hr + rng.uniform(3, 8)),
        elevation_gain_m=elevation,
        # Both legs, matching how the Strava importer normalises cadence.
        average_cadence=round(rng.uniform(88, 94) * 2, 1),
        name=name,
    )


def _assemble(
    activity_id: str,
    name: str,
    when: datetime,
    laps: list[Lap],
    vdot: float,
    rng: random.Random,
    elevation: float = 0.0,
) -> Activity:
    distance = sum(lap.distance_m for lap in laps)
    moving = sum(lap.moving_time_s for lap in laps)
    hrs = [lap.average_heartrate for lap in laps if lap.average_heartrate]
    weighted_hr = (
        sum(lap.average_heartrate * lap.moving_time_s for lap in laps if lap.average_heartrate)
        / max(sum(lap.moving_time_s for lap in laps if lap.average_heartrate), 1)
    )
    return Activity(
        id=activity_id,
        name=name,
        start_date=when,
        distance_m=round(distance, 1),
        moving_time_s=round(moving, 1),
        elapsed_time_s=round(moving * 1.02, 1),
        elevation_gain_m=elevation or round(distance / 1000 * rng.uniform(3, 9), 1),
        average_heartrate=round(weighted_hr) if hrs else None,
        max_heartrate=max((lap.max_heartrate for lap in laps if lap.max_heartrate), default=None),
        average_cadence=round(rng.uniform(88, 93) * 2, 1),
        laps=laps,
        splits_km=_km_splits(laps, vdot, rng),
        source="demo",
    )


def _km_splits(laps: list[Lap], vdot: float, rng: random.Random) -> list[Lap]:
    """Rebuild automatic 1 km splits from the lap structure.

    Real Strava activities carry both; the decoupling calculation reads splits,
    so the demo has to provide them too.
    """
    total_distance = sum(lap.distance_m for lap in laps)
    splits: list[Lap] = []
    covered = 0.0
    index = 0
    while covered < total_distance - 200:
        target = min(1000.0, total_distance - covered)
        # The pace of this kilometre is the distance-weighted pace of every lap
        # that overlaps it.
        time_s = 0.0
        cursor = 0.0
        for lap in laps:
            lap_end = cursor + lap.distance_m
            overlap = max(0.0, min(lap_end, covered + target) - max(cursor, covered))
            if overlap > 0:
                time_s += lap.pace_s_km * overlap / 1000
            cursor = lap_end
        index += 1
        drift = 0.012 * index / max(total_distance / 1000, 1)
        pace = time_s / (target / 1000) if target else 0
        splits.append(
            _lap(index, target, pace, vdot, rng, drift=drift, name=f"km {index}")
        )
        covered += target
    return splits


def _interval_session(
    activity_id: str,
    when: datetime,
    reps: int,
    rep_m: float,
    rep_pace: float,
    recovery_s: float,
    vdot: float,
    rng: random.Random,
    name: str,
    shape: str = "consistent",
) -> Activity:
    zones = zones_for(vdot)
    easy_pace = sum(zones.easy) / 2
    laps: list[Lap] = [_lap(0, 3000, easy_pace + 12, vdot, rng, name="Entrada en calor")]

    for rep in range(reps):
        progress = rep / max(reps - 1, 1)
        if shape == "fade":
            factor = 1 + 0.045 * max(0.0, progress - 0.55) / 0.45
        elif shape == "surge_finish":
            factor = 1.0 if progress < 0.8 else 0.965
        elif shape == "progressive":
            factor = 1.018 - 0.032 * progress
        else:
            factor = 1.0
        pace = rep_pace * factor * rng.uniform(0.994, 1.006)
        rep_lap = _lap(len(laps), rep_m, pace, vdot, rng, drift=0.01 * progress, name=f"Rep {rep + 1}")
        laps.append(rep_lap)
        if rep < reps - 1:
            jog_distance = recovery_s / (easy_pace + 60) * 1000
            laps.append(
                _lap(
                    len(laps), jog_distance, easy_pace + 60, vdot, rng, name="Recuperación",
                    hr_override=_recovery_hr(rep_lap.max_heartrate, recovery_s, rng),
                )
            )

    laps.append(_lap(len(laps), 2000, easy_pace + 20, vdot, rng, name="Vuelta a la calma"))
    return _assemble(activity_id, name, when, laps, vdot, rng)


def _hill_session(
    activity_id: str, when: datetime, reps: int, rep_m: float, rep_pace: float, vdot: float, rng: random.Random
) -> Activity:
    zones = zones_for(vdot)
    easy_pace = sum(zones.easy) / 2
    laps = [_lap(0, 2500, easy_pace + 10, vdot, rng, name="Entrada en calor")]
    for rep in range(reps):
        pace = rep_pace * rng.uniform(0.99, 1.02)
        rep_lap = _lap(
            len(laps), rep_m, pace, vdot, rng, elevation=rep_m * 0.07, drift=0.015, name=f"Cuesta {rep + 1}"
        )
        laps.append(rep_lap)
        down_time = (easy_pace + 110) * rep_m / 1000
        laps.append(
            _lap(
                len(laps), rep_m, easy_pace + 110, vdot, rng, name="Bajada",
                hr_override=_recovery_hr(rep_lap.max_heartrate, down_time, rng),
            )
        )
    laps.append(_lap(len(laps), 2000, easy_pace + 20, vdot, rng, name="Vuelta a la calma"))
    return _assemble(
        activity_id, f"Cuestas {reps} × {rep_m:.0f} m", when, laps, vdot, rng,
        elevation=reps * rep_m * 0.07,
    )


def _continuous(
    activity_id: str,
    when: datetime,
    distance_m: float,
    pace: float,
    vdot: float,
    rng: random.Random,
    name: str,
    drift_per_km: float = 0.004,
) -> Activity:
    laps: list[Lap] = []
    covered = 0.0
    index = 0
    while covered < distance_m:
        chunk = min(1000.0, distance_m - covered)
        drift = drift_per_km * index
        laps.append(_lap(index, chunk, pace * rng.uniform(0.99, 1.01), vdot, rng, drift=drift, name=f"km {index + 1}"))
        covered += chunk
        index += 1
    activity = _assemble(activity_id, name, when, laps, vdot, rng)
    # A continuous run has no meaningful lap structure — only automatic splits.
    activity.splits_km = activity.laps
    activity.laps = []
    return activity


def _tempo(activity_id: str, when: datetime, distance_m: float, pace: float, vdot: float, rng: random.Random) -> Activity:
    return _continuous(
        activity_id, when, distance_m, pace, vdot, rng,
        f"Tempo {distance_m / 1000:.0f} km", drift_per_km=0.006,
    )


def _race(activity_id: str, when: datetime, distance_m: float, seconds: float, vdot: float, rng: random.Random, name: str) -> Activity:
    pace = seconds / (distance_m / 1000)
    activity = _continuous(activity_id, when, distance_m, pace, vdot, rng, name, drift_per_km=0.008)
    activity.strava_workout_type = 1
    return activity


def build_demo_history(today: date | None = None) -> tuple[
    list[Activity], dict[str, Feedback], dict[date, HabitDay], list[Goal], AthleteProfile
]:
    """Eighteen weeks of training ending yesterday."""
    rng = random.Random(SEED)
    today = today or date.today()
    activities: list[Activity] = []
    feedback: dict[str, Feedback] = {}
    habits: dict[date, HabitDay] = {}

    first_monday = today - timedelta(days=today.weekday()) - timedelta(weeks=WEEKS - 1)

    for week in range(WEEKS):
        progress = week / (WEEKS - 1)
        vdot = START_VDOT + (END_VDOT - START_VDOT) * progress
        zones = zones_for(vdot)
        easy_pace = sum(zones.easy) / 2 + 8
        week_monday = first_monday + timedelta(weeks=week)

        # Every fourth week is a down week — volume drops, quality stays sharp.
        down_week = (week + 1) % 4 == 0
        volume_factor = 0.78 if down_week else 1.0 + 0.008 * week

        for weekday in range(7):
            day = week_monday + timedelta(days=weekday)
            if day >= today:
                continue
            when = datetime.combine(day, time(hour=7, minute=rng.randint(0, 45)))
            activity_id = f"demo-{day.isoformat()}"

            if weekday == 1:  # Tuesday — VO2 / specific endurance
                shape = _shape_for(week, rng)
                if week % 3 == 0:
                    activity = _interval_session(
                        activity_id, when, reps=5 + (week // 6), rep_m=1000,
                        rep_pace=sum(zones.interval) / 2, recovery_s=150, vdot=vdot, rng=rng,
                        name=f"Series {5 + (week // 6)} × 1000 m", shape=shape,
                    )
                elif week % 3 == 1:
                    activity = _interval_session(
                        activity_id, when, reps=12 + (week // 4), rep_m=400,
                        rep_pace=sum(zones.repetition) / 2, recovery_s=60, vdot=vdot, rng=rng,
                        name=f"Series {12 + (week // 4)} × 400 m", shape=shape,
                    )
                else:
                    activity = _interval_session(
                        activity_id, when, reps=6, rep_m=800,
                        rep_pace=sum(zones.interval) / 2 - 2, recovery_s=120, vdot=vdot, rng=rng,
                        name="Series 6 × 800 m", shape=shape,
                    )
            elif weekday == 4:  # Friday — threshold or strength
                if week % 4 == 2:
                    activity = _hill_session(
                        activity_id, when, reps=8, rep_m=300,
                        rep_pace=sum(zones.interval) / 2 + 25, vdot=vdot, rng=rng,
                    )
                else:
                    activity = _tempo(
                        activity_id, when, distance_m=6000 + 200 * week,
                        pace=sum(zones.threshold) / 2, vdot=vdot, rng=rng,
                    )
            elif weekday == 6:  # Sunday — long run
                distance = (16_000 + 250 * week) * volume_factor
                activity = _continuous(
                    activity_id, when, distance, easy_pace - 6, vdot, rng,
                    "Fondo dominguero", drift_per_km=0.005,
                )
            elif weekday == 3 and down_week:
                continue  # rest day on down weeks
            else:
                distance = rng.choice([7000, 8000, 9000, 10_000]) * volume_factor
                activity = _continuous(
                    activity_id, when, distance, easy_pace + rng.uniform(-6, 10), vdot, rng,
                    "Rodaje suave" if weekday in {2, 5} else "Rodaje",
                )

            activities.append(activity)
            feedback[activity.id] = _feedback_for(activity, week, weekday, rng)

        habits.update(_habits_for_week(week_monday, today, rng))

    # Two competitive references inside the block.
    test_day = first_monday + timedelta(weeks=8, days=5)
    if test_day < today:
        test_vdot = START_VDOT + (END_VDOT - START_VDOT) * (8 / (WEEKS - 1))
        activities.append(
            _race(f"demo-test-{test_day.isoformat()}", datetime.combine(test_day, time(9, 30)),
                  3000, 10 * 60 + 24, test_vdot, rng, "Test 3000 m en pista")
        )
    race_day = first_monday + timedelta(weeks=13, days=6)
    if race_day < today:
        race_vdot = START_VDOT + (END_VDOT - START_VDOT) * (13 / (WEEKS - 1))
        activities.append(
            _race(f"demo-race-{race_day.isoformat()}", datetime.combine(race_day, time(9, 0)),
                  5000, 17 * 60 + 38, race_vdot, rng, "Carrera 5K de la ciudad")
        )

    activities.sort(key=lambda act: act.start_date)

    goals = [
        Goal.new("5K objetivo", 5000, today + timedelta(days=46), target_time_s=16 * 60 + 59,
                 priority="A", terrain="asfalto"),
        Goal.new("1500 m pista", 1500, today + timedelta(days=25), target_time_s=4 * 60 + 34,
                 priority="B", terrain="pista"),
        Goal.new("2400 m control", 2400, today + timedelta(days=12), target_time_s=7 * 60 + 55,
                 priority="C", terrain="pista"),
    ]
    profile = AthleteProfile(
        name="Corredor",
        hr_max=HR_MAX,
        hr_rest=HR_REST,
        weekly_km_target=72,
        days_per_week=6,
    )
    return activities, feedback, habits, goals, profile


def _shape_for(week: int, rng: random.Random) -> str:
    """Most sessions are controlled; the rest give the analysis something to say."""
    roll = rng.random()
    if week >= WEEKS - 2:
        return "surge_finish" if roll < 0.5 else "consistent"
    if roll < 0.15:
        return "fade"
    if roll < 0.30:
        return "progressive"
    if roll < 0.42:
        return "surge_finish"
    return "consistent"


def _feedback_for(activity: Activity, week: int, weekday: int, rng: random.Random) -> Feedback:
    hard = weekday in {1, 4}
    rpe = rng.choice([7, 8, 8, 9]) if hard else rng.choice([3, 4, 4, 5])
    legs = rng.choice([3, 4, 4, 5]) if not hard else rng.choice([2, 3, 3, 4])
    niggle, severity = "", 0
    if rng.random() < 0.06:
        niggle = rng.choice(["Tibial derecho", "Gemelo izquierdo", "Aquiles derecho"])
        severity = rng.choice([1, 1, 2])
    return Feedback(
        activity_id=activity.id,
        rpe=rpe,
        legs=legs,
        niggle=niggle,
        niggle_severity=severity,
    )


def _habits_for_week(monday: date, today: date, rng: random.Random) -> dict[date, HabitDay]:
    days: dict[date, HabitDay] = {}
    for offset in range(7):
        day = monday + timedelta(days=offset)
        if day >= today:
            continue
        # Short nights cluster mid-week, which is what makes the correlation
        # in the habits screen discoverable rather than random.
        base_sleep = 7.6 if offset in {4, 5, 6} else 7.0
        sleep = round(rng.gauss(base_sleep, 0.75), 1)
        days[day] = HabitDay(
            day=day,
            sleep_hours=max(4.5, min(9.5, sleep)),
            hydration=rng.choice([3, 3, 4, 4, 5]),
            mobility=rng.random() < 0.45,
            strength=offset in {2, 5} and rng.random() < 0.7,
            fueled_before=rng.random() < 0.8,
            soreness=rng.choice([1, 2, 2, 3]),
            fatigue=rng.choice([2, 2, 3, 3, 4]),
        )
    return days
