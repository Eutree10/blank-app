"""Training load, freshness and injury risk.

Load is computed per lap when structure exists, so a 16 × 400 session is not
scored as if the whole hour was run at rep pace. From the daily load series we
derive chronic fitness, acute fatigue, form, and the acute:chronic ratio that
flags a volume spike.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, timedelta

from ..models import Activity, Feedback, HabitDay, week_start
from .physiology import PaceZones, activity_pace, lap_pace

CHRONIC_DAYS = 42
ACUTE_DAYS = 7


def activity_load(activity: Activity, zones: PaceZones) -> float:
    """A TSS-style load: hours × intensity² × 100, relative to threshold pace."""
    threshold_pace = statistics.mean(zones.threshold)
    if threshold_pace <= 0:
        return 0.0

    segments = activity.laps or activity.splits_km
    usable = [lap for lap in segments if lap.distance_m > 50 and lap.moving_time_s > 10]
    if not usable:
        gap = activity_pace(activity)
        intensity = threshold_pace / gap if gap else 0.0
        return (activity.moving_time_s / 3600.0) * intensity**2 * 100

    total = 0.0
    for lap in usable:
        gap = lap_pace(lap)
        if not math.isfinite(gap) or gap <= 0:
            continue
        intensity = threshold_pace / gap
        total += (lap.moving_time_s / 3600.0) * intensity**2 * 100
    return total


@dataclass
class LoadPoint:
    day: date
    load: float
    fitness: float  # chronic — what you have built
    fatigue: float  # acute — what you are carrying
    form: float  # fitness − fatigue


@dataclass
class LoadState:
    series: list[LoadPoint]

    @property
    def today(self) -> LoadPoint | None:
        return self.series[-1] if self.series else None

    @property
    def fitness(self) -> float:
        return self.today.fitness if self.today else 0.0

    @property
    def fatigue(self) -> float:
        return self.today.fatigue if self.today else 0.0

    @property
    def form(self) -> float:
        return self.today.form if self.today else 0.0

    def ramp_rate(self, days: int = 28) -> float:
        """Change in fitness over the window — positive means building."""
        if len(self.series) < days + 1:
            return 0.0
        return self.series[-1].fitness - self.series[-1 - days].fitness

    def acwr(self) -> float:
        """Acute:chronic workload ratio. Above ~1.4 is a spike worth flagging."""
        if len(self.series) < 28:
            return 1.0
        recent = self.series[-ACUTE_DAYS:]
        chronic_window = self.series[-28:]
        acute = sum(point.load for point in recent) / ACUTE_DAYS
        chronic = sum(point.load for point in chronic_window) / 28
        if chronic <= 0:
            return 1.0
        return acute / chronic


def build_load_state(
    activities: list[Activity], zones: PaceZones, through: date | None = None
) -> LoadState:
    """Daily fitness/fatigue/form series over the whole history."""
    if not activities:
        return LoadState(series=[])

    daily: dict[date, float] = {}
    for activity in activities:
        daily[activity.day] = daily.get(activity.day, 0.0) + activity_load(activity, zones)

    start = min(daily)
    end = through or max(max(daily), date.today())
    fitness = fatigue = 0.0
    chronic_alpha = 1 - math.exp(-1 / CHRONIC_DAYS)
    acute_alpha = 1 - math.exp(-1 / ACUTE_DAYS)

    series: list[LoadPoint] = []
    day = start
    while day <= end:
        load = daily.get(day, 0.0)
        fitness += (load - fitness) * chronic_alpha
        fatigue += (load - fatigue) * acute_alpha
        series.append(LoadPoint(day=day, load=load, fitness=fitness, fatigue=fatigue, form=fitness - fatigue))
        day += timedelta(days=1)
    return LoadState(series=series)


@dataclass
class WeekSummary:
    start: date
    km: float
    minutes: float
    load: float
    quality_sessions: int
    long_run_km: float
    sessions: int


def weekly_summaries(
    activities: list[Activity], zones: PaceZones, weeks: int = 16
) -> list[WeekSummary]:
    """Rolling week-by-week volume, ordered oldest first."""
    from .classify import classify  # local import keeps the module graph acyclic

    buckets: dict[date, WeekSummary] = {}
    for activity in activities:
        key = week_start(activity.day)
        summary = buckets.setdefault(
            key, WeekSummary(start=key, km=0, minutes=0, load=0, quality_sessions=0, long_run_km=0, sessions=0)
        )
        summary.km += activity.km
        summary.minutes += activity.duration_min
        summary.load += activity_load(activity, zones)
        summary.sessions += 1
        summary.long_run_km = max(summary.long_run_km, activity.km)
        if classify(activity, zones).workout_type.is_quality:
            summary.quality_sessions += 1

    ordered = sorted(buckets.values(), key=lambda summary: summary.start)
    return ordered[-weeks:]


@dataclass
class Readiness:
    """Today's answer to 'how am I?', with the reason attached."""

    score: int  # 0–100
    state: str  # recuperado | listo | cargado | fatigado
    summary: str
    drivers: list[str]


def _recent_feedback(
    activities: list[Activity], feedback: dict[str, Feedback], days: int
) -> list[Feedback]:
    cutoff = date.today() - timedelta(days=days)
    recent = [act for act in activities if act.day >= cutoff]
    return [feedback[act.id] for act in recent if act.id in feedback]


def compute_readiness(
    load_state: LoadState,
    activities: list[Activity],
    feedback: dict[str, Feedback],
    habits: dict[date, HabitDay],
) -> Readiness:
    """Blend objective form with what the athlete reported.

    Objective load alone misses the athlete who is technically fresh but slept
    five hours and has a sore achilles, so subjective input can move the score
    as much as form does.
    """
    drivers: list[str] = []
    fitness = max(load_state.fitness, 1.0)
    form_ratio = load_state.form / fitness  # normalised so it works at any volume

    # Form: −0.30 (deep fatigue) … +0.15 (fresh) maps onto 25 … 90.
    form_component = 25 + (form_ratio + 0.30) / 0.45 * 65
    form_component = max(10.0, min(95.0, form_component))
    score = form_component

    if load_state.form < -0.18 * fitness:
        drivers.append("Carga aguda por encima de tu base crónica.")
    elif load_state.form > 0.05 * fitness:
        drivers.append("Vienes de días de carga baja: estás fresco.")

    legs = [fb.legs for fb in _recent_feedback(activities, feedback, 4) if fb.legs]
    if legs:
        mean_legs = statistics.mean(legs)
        score += (mean_legs - 3) * 7
        if mean_legs <= 2.2:
            drivers.append("Reportaste piernas pesadas en las últimas sesiones.")
        elif mean_legs >= 4:
            drivers.append("Sensación de piernas buena en los últimos días.")

    niggles = [fb for fb in _recent_feedback(activities, feedback, 10) if fb.niggle_severity >= 2]
    if niggles:
        score -= 12
        drivers.append(f"Molestia activa: {niggles[-1].niggle or 'sin detalle'}.")

    recent_days = [habits[day] for day in habits if day >= date.today() - timedelta(days=3)]
    sleep = [habit.sleep_hours for habit in recent_days if habit.sleep_hours]
    if sleep:
        mean_sleep = statistics.mean(sleep)
        score += (mean_sleep - 7.5) * 4
        if mean_sleep < 6.8:
            drivers.append(f"Promedio de sueño de {mean_sleep:.1f} h en los últimos días.")

    acwr = load_state.acwr()
    if acwr > 1.4:
        score -= 8
        drivers.append(f"Salto de volumen del {(acwr - 1) * 100:.0f} % sobre tu media de 4 semanas.")

    score = int(max(0, min(100, round(score))))
    if score >= 78:
        state, summary = "recuperado", "Estás recuperado y con margen para un estímulo fuerte."
    elif score >= 60:
        state, summary = "listo", "Estás en condiciones de entrenar calidad, sin excesos."
    elif score >= 42:
        state, summary = "cargado", "Acumulás fatiga: hoy conviene un estímulo controlado."
    else:
        state, summary = "fatigado", "La fatiga domina el cuadro: prioridad a recuperar."

    if not drivers:
        drivers.append("Carga y sensaciones dentro de lo esperado.")
    return Readiness(score=score, state=state, summary=summary, drivers=drivers)
