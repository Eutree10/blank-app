"""Running physiology: VDOT, equivalent performances and training paces.

Daniels & Gilbert's running-economy model. It gives the app one number (VDOT)
that any performance maps onto, so a 400 m rep, a tempo run and a 5K race can
be compared on the same scale, and so target paces are derived rather than
guessed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

# Intensity anchors as a fraction of VDOT. These are the classic Daniels zones.
ZONE_FRACTIONS: dict[str, tuple[float, float]] = {
    "easy": (0.59, 0.74),
    "marathon": (0.75, 0.84),
    "threshold": (0.83, 0.88),
    "interval": (0.95, 1.00),
    "repetition": (1.05, 1.12),
}


def pct_vo2max(minutes: float) -> float:
    """Fraction of VO2max sustainable for `minutes` of racing."""
    minutes = max(minutes, 0.5)
    return (
        0.8
        + 0.1894393 * math.exp(-0.012778 * minutes)
        + 0.2989558 * math.exp(-0.1932605 * minutes)
    )


def vo2_of_velocity(meters_per_min: float) -> float:
    """Oxygen cost (ml/kg/min) of running at a given velocity."""
    return -4.60 + 0.182258 * meters_per_min + 0.000104 * meters_per_min**2


def velocity_of_vo2(vo2: float) -> float:
    """Inverse of `vo2_of_velocity` — metres per minute for an oxygen cost."""
    a, b, c = 0.000104, 0.182258, -4.60 - vo2
    disc = b**2 - 4 * a * c
    if disc <= 0:
        return 0.0
    return (-b + math.sqrt(disc)) / (2 * a)


def vdot(distance_m: float, seconds: float) -> float:
    """VDOT implied by a maximal performance over `distance_m`."""
    if distance_m <= 0 or seconds <= 0:
        return 0.0
    minutes = seconds / 60.0
    velocity = distance_m / minutes
    return vo2_of_velocity(velocity) / pct_vo2max(minutes)


def time_for_distance(distance_m: float, vdot_value: float) -> float:
    """Seconds to race `distance_m` at a given VDOT. Bisection on the model."""
    if distance_m <= 0 or vdot_value <= 0:
        return float("inf")

    def implied_vdot(seconds: float) -> float:
        return vdot(distance_m, seconds)

    # Bracket: a very fast and a very slow attempt at the distance.
    low, high = distance_m / 12.0, distance_m / 1.5  # 12 m/s … 1.5 m/s
    for _ in range(80):
        mid = (low + high) / 2
        if implied_vdot(mid) > vdot_value:
            low = mid  # too fast for this VDOT, slow down
        else:
            high = mid
    return (low + high) / 2


def equivalent_time(
    known_distance_m: float, known_seconds: float, target_distance_m: float
) -> float:
    """Equivalent performance over another distance, via VDOT."""
    return time_for_distance(target_distance_m, vdot(known_distance_m, known_seconds))


def pace_for_zone(vdot_value: float, zone: str) -> tuple[float, float]:
    """(fast, slow) bounds in s/km for a training zone at this VDOT."""
    low_frac, high_frac = ZONE_FRACTIONS[zone]
    fast = pace_at_fraction(vdot_value, high_frac)
    slow = pace_at_fraction(vdot_value, low_frac)
    return fast, slow


def pace_at_fraction(vdot_value: float, fraction: float) -> float:
    """s/km when running at `fraction` of VDOT."""
    velocity = velocity_of_vo2(vdot_value * fraction)  # m/min
    if velocity <= 0:
        return float("inf")
    return 60_000.0 / velocity


def fraction_of_vdot(pace_s_km: float, vdot_value: float) -> float:
    """How hard a given pace is, as a fraction of VDOT. The inverse lookup."""
    if pace_s_km <= 0 or vdot_value <= 0 or math.isinf(pace_s_km):
        return 0.0
    velocity = 60_000.0 / pace_s_km  # m/min
    return vo2_of_velocity(velocity) / vdot_value


@dataclass(frozen=True)
class PaceZones:
    """Training paces for one athlete, all in s/km."""

    vdot: float
    easy: tuple[float, float]
    marathon: tuple[float, float]
    threshold: tuple[float, float]
    interval: tuple[float, float]
    repetition: tuple[float, float]

    def zone_of(self, pace_s_km: float) -> str:
        """Which zone a measured pace falls in — used to classify sessions."""
        fraction = fraction_of_vdot(pace_s_km, self.vdot)
        if fraction >= 1.03:
            return "repetition"
        if fraction >= 0.93:
            return "interval"
        if fraction >= 0.825:
            return "threshold"
        if fraction >= 0.75:
            return "marathon"
        return "easy"

    def bounds(self, zone: str) -> tuple[float, float]:
        return getattr(self, zone)


def zones_for(vdot_value: float) -> PaceZones:
    return PaceZones(
        vdot=vdot_value,
        easy=pace_for_zone(vdot_value, "easy"),
        marathon=pace_for_zone(vdot_value, "marathon"),
        threshold=pace_for_zone(vdot_value, "threshold"),
        interval=pace_for_zone(vdot_value, "interval"),
        repetition=pace_for_zone(vdot_value, "repetition"),
    )


def grade_adjusted_pace(pace_s_km: float, grade: float) -> float:
    """Flat-equivalent pace for a climb or descent.

    Minetti's cost-of-running curve, normalised so grade 0 is a no-op. Uphill
    reps and rolling long runs would otherwise look like bad sessions.
    """
    return pace_s_km * (3.6 / _minetti_cost(grade))


SUSTAINED_GRADE = 0.025  # above this, treat the elevation as one real climb


def effective_pace(pace_s_km: float, elevation_gain_m: float, distance_m: float) -> float:
    """Flat-equivalent pace for a run or lap, from its total elevation gain.

    Strava reports total ascent, not net grade. On a loop that ascent is paid
    back as descent, so treating it as a constant climb makes every rolling run
    look faster than it was. Below `SUSTAINED_GRADE` the segment is modelled as
    half up and half down at twice the average grade — which nearly cancels.
    Above it, the climb is real and adjusted directly.
    """
    if distance_m <= 0 or pace_s_km <= 0:
        return pace_s_km
    grade = elevation_gain_m / distance_m
    if grade >= SUSTAINED_GRADE:
        return grade_adjusted_pace(pace_s_km, grade)

    rolling_grade = min(2 * grade, 0.15)
    up = _minetti_cost(rolling_grade)
    down = _minetti_cost(-rolling_grade)
    mean_cost = (up + down) / 2
    if mean_cost <= 0:
        return pace_s_km
    return pace_s_km * (3.6 / mean_cost)


def lap_pace(lap: "Any") -> float:
    """Flat-equivalent pace of a lap. Duck-typed so it also takes splits."""
    return effective_pace(lap.pace_s_km, lap.elevation_gain_m, lap.distance_m)


def activity_pace(activity: "Any") -> float:
    """Flat-equivalent average pace of a whole activity."""
    return effective_pace(activity.pace_s_km, activity.elevation_gain_m, activity.distance_m)


def _minetti_cost(grade: float) -> float:
    """Energy cost of running at a gradient, J/kg/m. 3.6 on the flat."""
    grade = max(min(grade, 0.30), -0.30)
    return (
        155.4 * grade**5
        - 30.4 * grade**4
        - 43.3 * grade**3
        + 46.3 * grade**2
        + 19.5 * grade
        + 3.6
    )


def hr_reserve_fraction(hr: float, hr_rest: float, hr_max: float) -> float:
    """Karvonen fraction — how hard a heart rate is for this athlete."""
    if not hr or hr_max <= hr_rest:
        return 0.0
    return max(0.0, min(1.2, (hr - hr_rest) / (hr_max - hr_rest)))
