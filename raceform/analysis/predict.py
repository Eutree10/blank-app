"""Race prediction.

Most predictors take one recent race and apply Riegel. Runners rarely race.
So this module extracts a fitness estimate from *every* kind of quality
session — races, tests, interval sets, tempos — each with its own confidence,
then blends them with recency weighting and projects the trend to race day.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, timedelta

from ..models import Activity, Goal, WorkoutType
from .classify import classify
from .physiology import (
    PaceZones,
    activity_pace,
    lap_pace,
    time_for_distance,
    vdot,
    vo2_of_velocity,
    zones_for,
)

DEFAULT_VDOT = 45.0
# Terrain multipliers applied to the predicted time.
TERRAIN_FACTOR = {"pista": 0.995, "asfalto": 1.0, "trail": 1.06}


@dataclass
class FitnessEstimate:
    """One session's opinion about the athlete's current VDOT."""

    day: date
    vdot: float
    confidence: float  # 0–1: how much this session is worth as evidence
    source: WorkoutType
    detail: str
    activity_id: str


def _interval_vdot(work_distance: float, work_time: float, rest_time: float, rep_time: float) -> float:
    """VDOT implied by a rep set.

    A rep set is converted into the continuous effort it is worth: the
    recovery is partly "paid back" into the time, and short reps pay back more
    because their pace leans on anaerobic support that does not extend to a
    race.
    """
    if work_distance <= 0 or work_time <= 0:
        return 0.0
    alpha = 0.26 * math.exp(-rep_time / 95.0)
    alpha = max(0.02, min(0.30, alpha))
    # Very long recoveries stop being informative — a session with five minutes
    # between reps says little more than one with three.
    rest_time = min(rest_time, 1.5 * work_time)
    effective_time = work_time + alpha * rest_time
    return vdot(work_distance, effective_time)


def _tempo_vdot(distance_m: float, seconds: float) -> float:
    """VDOT implied by a sustained threshold effort.

    A tempo is not maximal, so its pace is read as a fraction of VDOT that
    depends on how long it was held.
    """
    minutes = seconds / 60.0
    fraction = max(0.80, min(0.92, 0.94 - 0.0028 * minutes))
    velocity = distance_m / minutes if minutes else 0.0
    if velocity <= 0:
        return 0.0
    return vo2_of_velocity(velocity) / fraction


def estimate_from_activity(activity: Activity, zones: PaceZones) -> FitnessEstimate | None:
    """Read a fitness estimate out of one activity, if it carries signal."""
    classification = classify(activity, zones)
    workout_type = classification.workout_type

    if workout_type in {WorkoutType.RACE, WorkoutType.TEST}:
        gap_pace = activity_pace(activity)
        adjusted_time = gap_pace * activity.km
        value = vdot(activity.distance_m, adjusted_time)
        confidence = 1.0 if workout_type is WorkoutType.RACE else 0.85
        return FitnessEstimate(
            day=activity.day,
            vdot=value,
            confidence=confidence,
            source=workout_type,
            detail=f"{workout_type.label} de {activity.km:.1f} km",
            activity_id=activity.id,
        )

    if workout_type is WorkoutType.HILLS:
        # Hill reps train force, not race pace. Their times say nothing
        # reliable about flat fitness, so they are left out of the estimate.
        return None

    seg = classification.segmentation
    if seg.structured and seg.rep_count >= 3:
        work_distance = sum(lap.distance_m for lap in seg.work)
        # Grade-adjusted work time, so hill reps are not read as flat speed.
        work_time = sum(
            lap_pace(lap) * (lap.distance_m / 1000) for lap in seg.work
        )
        rest_time = sum(lap.moving_time_s for lap in seg.recovery)
        rep_time = work_time / seg.rep_count
        value = _interval_vdot(work_distance, work_time, rest_time, rep_time)
        if value <= 0:
            return None
        # Short, low-volume sets are weak evidence about race fitness.
        confidence = 0.45 + min(0.30, work_distance / 20_000)
        if seg.nominal_rep_distance_m < 400:
            confidence *= 0.6
        return FitnessEstimate(
            day=activity.day,
            vdot=value,
            confidence=round(confidence, 2),
            source=workout_type,
            detail=f"{seg.rep_count} × {seg.nominal_rep_distance_m:.0f} m",
            activity_id=activity.id,
        )

    if workout_type is WorkoutType.TEMPO and activity.moving_time_s >= 600:
        gap_pace = activity_pace(activity)
        value = _tempo_vdot(activity.distance_m, gap_pace * activity.km)
        return FitnessEstimate(
            day=activity.day,
            vdot=value,
            confidence=0.55,
            source=workout_type,
            detail=f"Tempo de {activity.km:.1f} km",
            activity_id=activity.id,
        )
    return None


def collect_estimates(
    activities: list[Activity], zones: PaceZones, window_days: int = 70
) -> list[FitnessEstimate]:
    """All usable fitness estimates inside the recent window, newest first."""
    if not activities:
        return []
    latest = max(act.day for act in activities)
    cutoff = latest - timedelta(days=window_days)
    estimates = []
    for activity in activities:
        if activity.day < cutoff:
            continue
        estimate = estimate_from_activity(activity, zones)
        if estimate and 25 < estimate.vdot < 90:
            estimates.append(estimate)
    return sorted(estimates, key=lambda est: est.day, reverse=True)


def blended_vdot(estimates: list[FitnessEstimate], half_life_days: int = 21) -> float:
    """Recency- and confidence-weighted VDOT, with outliers trimmed."""
    if not estimates:
        return DEFAULT_VDOT
    values = [est.vdot for est in estimates]
    if len(values) >= 5:
        median = statistics.median(values)
        spread = statistics.pstdev(values) or 1.0
        estimates = [est for est in estimates if abs(est.vdot - median) <= 2.2 * spread] or estimates

    latest = max(est.day for est in estimates)
    numerator = denominator = 0.0
    for est in estimates:
        age = (latest - est.day).days
        weight = est.confidence * 0.5 ** (age / half_life_days)
        numerator += est.vdot * weight
        denominator += weight
    return numerator / denominator if denominator else DEFAULT_VDOT


def current_vdot(activities: list[Activity], seed_vdot: float = DEFAULT_VDOT) -> float:
    """Two-pass estimate: seed zones, classify, re-estimate with better zones."""
    zones = zones_for(seed_vdot)
    for _ in range(3):
        estimates = collect_estimates(activities, zones)
        value = blended_vdot(estimates)
        if abs(value - zones.vdot) < 0.15:
            return value
        zones = zones_for(value)
    return zones.vdot


def vdot_trend(estimates: list[FitnessEstimate], weeks: int = 8) -> float:
    """VDOT change per week over the recent window. Positive means improving."""
    if len(estimates) < 4:
        return 0.0
    latest = max(est.day for est in estimates)
    points = [
        ((est.day - latest).days / 7.0, est.vdot, est.confidence)
        for est in estimates
        if (latest - est.day).days <= weeks * 7
    ]
    if len(points) < 4:
        return 0.0
    weight_sum = sum(w for _, _, w in points)
    mean_x = sum(x * w for x, _, w in points) / weight_sum
    mean_y = sum(y * w for _, y, w in points) / weight_sum
    numerator = sum(w * (x - mean_x) * (y - mean_y) for x, y, w in points)
    denominator = sum(w * (x - mean_x) ** 2 for x, _, w in points)
    if denominator == 0:
        return 0.0
    slope = numerator / denominator
    return max(-0.6, min(0.6, slope))  # cap: nobody gains 0.6 VDOT/week for long


@dataclass
class Prediction:
    distance_m: float
    central_s: float
    low_s: float  # optimistic bound (faster)
    high_s: float  # conservative bound (slower)
    vdot: float
    race_day_vdot: float
    confidence: float  # 0–1
    basis: str

    @property
    def pace_s_km(self) -> float:
        return self.central_s / (self.distance_m / 1000)


def predict_race(
    goal: Goal,
    activities: list[Activity],
    zones: PaceZones,
    form_ratio: float = 0.0,
    specific_readiness: float | None = None,
) -> Prediction:
    """Predicted time range for a goal, projected to race day.

    Three things move the prediction off the raw VDOT number: the trend in
    recent fitness, the freshness the athlete will bring, and whether the
    specific endurance for that distance has actually been trained.
    """
    estimates = collect_estimates(activities, zones)
    base_vdot = blended_vdot(estimates) if estimates else zones.vdot
    trend = vdot_trend(estimates)

    days_left = max(0, goal.days_left)
    # Trend is only extrapolated over the weeks that remain, and decays: nobody
    # keeps improving linearly for three months.
    weeks_left = min(days_left / 7.0, 10.0)
    projected_gain = trend * weeks_left * (0.75 if weeks_left > 4 else 1.0)
    race_day_vdot = base_vdot + projected_gain

    # A taper is worth roughly 1–2% of performance; deep fatigue costs more.
    freshness_bonus = max(-0.035, min(0.02, form_ratio * 0.12))
    effective_vdot = race_day_vdot * (1 + freshness_bonus)

    central = time_for_distance(goal.distance_m, effective_vdot)
    central *= TERRAIN_FACTOR.get(goal.terrain, 1.0)

    if specific_readiness is not None and specific_readiness < 80:
        # Missing specific endurance costs more the longer the race is.
        gap = (80 - specific_readiness) / 100
        penalty = gap * 0.035 * min(1.6, goal.distance_m / 5000)
        central *= 1 + penalty

    spread = _prediction_spread(estimates, days_left)
    return Prediction(
        distance_m=goal.distance_m,
        central_s=central,
        low_s=central * (1 - spread),
        high_s=central * (1 + spread),
        vdot=base_vdot,
        race_day_vdot=race_day_vdot,
        confidence=_prediction_confidence(estimates, days_left),
        basis=_basis_text(estimates),
    )


def _prediction_spread(estimates: list[FitnessEstimate], days_left: int) -> float:
    """Half-width of the range as a fraction of the central time."""
    if not estimates:
        return 0.05
    values = [est.vdot for est in estimates[:10]]
    dispersion = (statistics.pstdev(values) / statistics.mean(values)) if len(values) > 2 else 0.03
    horizon = min(0.02, days_left / 120 * 0.02)  # further out, wider
    quality = 0.012 if any(est.source is WorkoutType.RACE for est in estimates[:6]) else 0.02
    return max(0.008, min(0.055, dispersion * 0.6 + horizon + quality))


def _prediction_confidence(estimates: list[FitnessEstimate], days_left: int) -> float:
    if not estimates:
        return 0.2
    evidence = min(1.0, sum(est.confidence for est in estimates[:8]) / 4.0)
    has_race = any(est.source in {WorkoutType.RACE, WorkoutType.TEST} for est in estimates[:8])
    horizon_penalty = min(0.25, days_left / 180 * 0.25)
    return round(max(0.15, min(0.95, evidence * (0.85 + 0.15 * has_race) - horizon_penalty)), 2)


def _basis_text(estimates: list[FitnessEstimate]) -> str:
    if not estimates:
        return "Sin sesiones de calidad recientes: predicción provisional."
    top = estimates[:3]
    parts = [f"{est.detail} ({est.day.strftime('%d/%m')})" for est in top]
    return "Basado en " + ", ".join(parts) + "."


def prediction_history(
    goal: Goal, activities: list[Activity], zones: PaceZones, points: int = 14
) -> list[tuple[date, float]]:
    """How the prediction for this goal evolved, one point per training week."""
    if not activities:
        return []
    ordered = sorted(activities, key=lambda act: act.start_date)
    latest = ordered[-1].day
    earliest = ordered[0].day
    series: list[tuple[date, float]] = []

    for index in range(points):
        as_of = latest - timedelta(days=7 * (points - 1 - index))
        if as_of < earliest + timedelta(days=14):
            continue
        window = [act for act in ordered if act.day <= as_of]
        estimates = collect_estimates(window, zones)
        if not estimates:
            continue
        value = blended_vdot(estimates)
        series.append((as_of, time_for_distance(goal.distance_m, value)))
    return series


def equivalent_performances(vdot_value: float) -> list[tuple[str, float, float]]:
    """(label, distance_m, seconds) across the distances a track runner cares about."""
    distances = [
        ("800 m", 800.0),
        ("1500 m", 1500.0),
        ("2400 m", 2400.0),
        ("3000 m", 3000.0),
        ("5000 m", 5000.0),
        ("10 km", 10000.0),
    ]
    return [(label, dist, time_for_distance(dist, vdot_value)) for label, dist in distances]


def required_vdot(goal: Goal) -> float | None:
    """The VDOT the athlete needs to hit the target time."""
    if not goal.target_time_s:
        return None
    return vdot(goal.distance_m, goal.target_time_s)
