"""Formatting helpers for paces, times and distances.

Every number the athlete reads passes through here, so the app never shows a
raw float. Paces are min/km, times are mm:ss or h:mm:ss.
"""

from __future__ import annotations

import math
import re

MIN_VALID_PACE = 120.0  # 2:00/km — faster than any human over a rep
MAX_VALID_PACE = 900.0  # 15:00/km — slower than walking


def fmt_time(seconds: float | None, force_hours: bool = False) -> str:
    """3725 -> '1:02:05', 1042 -> '17:22'."""
    if seconds is None or (isinstance(seconds, float) and math.isnan(seconds)):
        return "—"
    seconds = int(round(seconds))
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours or force_hours:
        return f"{sign}{hours}:{minutes:02d}:{secs:02d}"
    return f"{sign}{minutes}:{secs:02d}"


def fmt_pace(seconds_per_km: float | None, suffix: str = "/km") -> str:
    """203.4 -> '3:23/km'. Returns '—' for missing or nonsensical values."""
    if seconds_per_km is None or math.isnan(seconds_per_km) or seconds_per_km <= 0:
        return "—"
    if seconds_per_km > MAX_VALID_PACE * 2:
        return "—"
    total = int(round(seconds_per_km))
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}{suffix}"


def fmt_pace_range(low: float, high: float) -> str:
    """Both bounds in s/km, low is the faster one. -> '3:23–3:27/km'."""
    lo, hi = min(low, high), max(low, high)
    return f"{fmt_pace(lo, suffix='')}–{fmt_pace(hi)}"


def fmt_distance(meters: float | None) -> str:
    """Rounds to the nearest sensible unit: 400 -> '400 m', 12340 -> '12,3 km'."""
    if meters is None:
        return "—"
    if meters < 1000:
        return f"{int(round(meters / 5) * 5)} m"
    km = meters / 1000
    if abs(km - round(km)) < 0.05:
        return f"{round(km):g} km"
    return f"{km:.1f}".replace(".", ",") + " km"


def fmt_rep_distance(meters: float) -> str:
    """Snaps a rep to the label a runner would use: 397 m -> '400 m'."""
    return fmt_distance(snap_distance(meters))


def snap_distance(meters: float) -> float:
    """Rounds a measured rep to the nearest canonical track/road distance."""
    canonical = [
        100, 150, 200, 300, 400, 500, 600, 800, 1000, 1200, 1500, 1600,
        2000, 2400, 3000, 3200, 5000, 8000, 10000, 15000, 21097, 42195,
    ]
    best = min(canonical, key=lambda c: abs(c - meters))
    # Only snap when we are within 6% — otherwise it is a genuine odd distance.
    if abs(best - meters) / max(best, 1) <= 0.06:
        return float(best)
    return float(round(meters / 50) * 50)


def pace_of(distance_m: float, seconds: float) -> float:
    """Seconds per kilometre. Returns inf for degenerate inputs."""
    if distance_m <= 0 or seconds <= 0:
        return float("inf")
    return seconds / (distance_m / 1000.0)


def speed_of(distance_m: float, seconds: float) -> float:
    """Metres per second."""
    if seconds <= 0:
        return 0.0
    return distance_m / seconds


def parse_time(text: str) -> int | None:
    """'17:20' -> 1040, '1:02:05' -> 3725, '16:59.5' -> 1019. None if unparseable."""
    if not text:
        return None
    text = text.strip().replace(",", ".")
    if not re.fullmatch(r"(\d+:)?\d{1,2}:\d{1,2}(\.\d+)?|\d+(\.\d+)?", text):
        return None
    parts = text.split(":")
    try:
        values = [float(p) for p in parts]
    except ValueError:
        return None
    seconds = 0.0
    for value in values:
        seconds = seconds * 60 + value
    return int(round(seconds))


def fmt_delta(value: float, unit: str = "", decimals: int = 0) -> str:
    """Signed number for comparisons: +7 s, -1,2 %."""
    fmt = f"{{:+.{decimals}f}}"
    return fmt.format(value).replace(".", ",") + (f" {unit}" if unit else "")


def fmt_pct(value: float, decimals: int = 0) -> str:
    """0.0384 -> '3,8 %' (input is a fraction, not already multiplied)."""
    fmt = f"{{:.{decimals}f}}"
    return fmt.format(value * 100).replace(".", ",") + " %"


def fmt_num(value: float, decimals: int = 1) -> str:
    """Spanish decimal comma, no thousands separator noise."""
    fmt = f"{{:.{decimals}f}}"
    return fmt.format(value).replace(".", ",")


def plural(count: int, singular: str, many: str) -> str:
    return singular if count == 1 else many


# Spanish names, written out rather than taken from the system locale — the
# server this runs on will not have es_AR installed.
WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
WEEKDAYS_SHORT = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def fmt_day_long(day) -> str:
    """date -> 'martes 28 de julio'."""
    return f"{WEEKDAYS[day.weekday()]} {day.day} de {MONTHS[day.month - 1]}"


def fmt_day_short(day) -> str:
    """date -> 'Mar 28/07'."""
    return f"{WEEKDAYS_SHORT[day.weekday()]} {day.strftime('%d/%m')}"
