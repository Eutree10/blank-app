"""Plan generation and adaptation.

The plan is derived, never stored as a fixed calendar: it is rebuilt from the
goal, the phase, the limiting capability and how the athlete is actually
responding. Adaptation therefore recalculates the remainder of the week rather
than shuffling sessions around, so two incompatible stimuli never end up
back to back.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta

from ..formats import fmt_num, fmt_pace, fmt_pace_range, fmt_time
from ..models import (
    AthleteProfile,
    Capability,
    Goal,
    PlannedSession,
    WorkoutType,
    week_start,
)
from .capability import RaceReadiness
from .load import Readiness
from .physiology import PaceZones

MIN_HOURS_BETWEEN_QUALITY = 48


@dataclass
class PlanWeek:
    start: date
    index: int  # 1-based week number in the block
    theme: str
    phase: str
    sessions: list[PlannedSession]
    target_km: float

    @property
    def quality_count(self) -> int:
        return sum(1 for session in self.sessions if session.workout_type.is_quality)


def phase_for(days_left: int) -> str:
    """Which block of the season the athlete is in."""
    if days_left <= 10:
        return "afinamiento"
    if days_left <= 28:
        return "específico"
    if days_left <= 70:
        return "transformación"
    return "base"


PHASE_THEMES = {
    "base": "Construir base aeróbica y tolerancia al volumen",
    "transformación": "Convertir velocidad en resistencia específica",
    "específico": "Sostener ritmo de carrera bajo fatiga",
    "afinamiento": "Bajar carga, mantener el estímulo y llegar fresco",
}


def _new_id() -> str:
    return uuid.uuid4().hex[:10]


# --- session builders --------------------------------------------------------

def easy_run(day: date, km: float, zones: PaceZones, strides: bool = False) -> PlannedSession:
    low, high = zones.easy
    structure = f"{fmt_num(km, 0)} km continuos"
    if strides:
        structure += " + 6 × 100 m progresivos"
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.EASY,
        title="Rodaje",
        structure=structure,
        purpose="Volumen aeróbico sin costo, para llegar entero a la próxima calidad.",
        target_pace_low=low,
        target_pace_high=high,
        distance_m=km * 1000,
    )


def long_run(day: date, km: float, zones: PaceZones, finish_fast: bool = False) -> PlannedSession:
    low, high = zones.easy
    structure = f"{fmt_num(km, 0)} km"
    purpose = "Resistencia aeróbica y economía de carrera."
    if finish_fast:
        structure += f", últimos 3 km a {fmt_pace_range(*zones.marathon)}"
        purpose = "Resistencia aeróbica con cierre firme: entrena terminar bien."
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.LONG,
        title="Fondo",
        structure=structure,
        purpose=purpose,
        target_pace_low=low,
        target_pace_high=high,
        distance_m=km * 1000,
        key=finish_fast,
    )


def tempo_run(day: date, km: float, zones: PaceZones) -> PlannedSession:
    low, high = zones.threshold
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.TEMPO,
        title=f"Tempo {fmt_num(km, 0)} km",
        structure=f"{fmt_num(km, 0)} km continuos a {fmt_pace_range(low, high)}",
        purpose="Elevar el umbral: el ritmo que podés sostener sin acumular fatiga.",
        target_pace_low=low,
        target_pace_high=high,
        distance_m=km * 1000,
        key=True,
    )


def vo2_intervals(day: date, reps: int, rep_m: int, zones: PaceZones, recovery_s: int = 150) -> PlannedSession:
    low, high = zones.interval
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.INTERVALS,
        title=f"{reps} × {rep_m} m",
        structure=f"{reps} × {rep_m} m a {fmt_pace_range(low, high)}\nRecuperación: {fmt_time(recovery_s)}",
        purpose="Resistencia específica de 3K–5K: sostener consumo alto repetidas veces.",
        target_pace_low=low,
        target_pace_high=high,
        distance_m=reps * rep_m,
        recovery_s=recovery_s,
        key=True,
    )


def cruise_intervals(day: date, reps: int, rep_m: int, zones: PaceZones, recovery_s: int = 60) -> PlannedSession:
    low, high = zones.threshold
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.INTERVALS,
        title=f"{reps} × {rep_m} m en umbral",
        structure=f"{reps} × {rep_m} m a {fmt_pace_range(low, high)}\nRecuperación: {fmt_time(recovery_s)}",
        purpose="Volumen de umbral fraccionado: más trabajo de calidad con menos desgaste.",
        target_pace_low=low,
        target_pace_high=high,
        distance_m=reps * rep_m,
        recovery_s=recovery_s,
        key=True,
    )


def short_reps(day: date, reps: int, rep_m: int, zones: PaceZones, recovery_s: int = 60) -> PlannedSession:
    low, high = zones.repetition
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.REPS,
        title=f"{reps} × {rep_m} m",
        structure=f"{reps} × {rep_m} m a {fmt_pace_range(low, high)}\nRecuperación: {fmt_time(recovery_s)}",
        purpose="Velocidad y economía: bajar el costo del ritmo de carrera.",
        target_pace_low=low,
        target_pace_high=high,
        distance_m=reps * rep_m,
        recovery_s=recovery_s,
        key=True,
    )


def hill_reps(day: date, reps: int, rep_m: int, zones: PaceZones) -> PlannedSession:
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.HILLS,
        title=f"Cuestas {reps} × {rep_m} m",
        structure=f"{reps} × {rep_m} m en subida al 5–7 %\nRecuperación: bajando al trote",
        purpose="Fuerza específica y potencia de zancada, con bajo impacto articular.",
        distance_m=reps * rep_m,
        key=True,
    )


def race_pace_session(day: date, goal: Goal, zones: PaceZones, reps: int, rep_m: int, recovery_s: int) -> PlannedSession:
    pace = goal.target_pace_s_km or sum(zones.interval) / 2
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.INTERVALS,
        title=f"{reps} × {rep_m} m a ritmo de {goal.name}",
        structure=(
            f"{reps} × {rep_m} m a {fmt_pace(pace)}\nRecuperación: {fmt_time(recovery_s)}"
        ),
        purpose=f"Automatizar el ritmo objetivo de {goal.name} y sostenerlo con fatiga.",
        target_pace_low=pace - 3,
        target_pace_high=pace + 3,
        distance_m=reps * rep_m,
        recovery_s=recovery_s,
        key=True,
    )


def rest_day(day: date) -> PlannedSession:
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.EASY,
        title="Descanso",
        structure="Sin carrera",
        purpose="La adaptación ocurre en el descanso, no en el estímulo.",
        distance_m=0,
    )


def race_day_session(day: date, goal: Goal, predicted_s: float | None = None) -> PlannedSession:
    target = goal.target_time_s or predicted_s
    return PlannedSession(
        id=_new_id(),
        day=day,
        workout_type=WorkoutType.RACE,
        title=goal.name,
        structure=f"{fmt_num(goal.distance_m / 1000, 1)} km · objetivo {fmt_time(target)}",
        purpose="Competencia.",
        distance_m=goal.distance_m,
        key=True,
    )


# --- weekly construction -----------------------------------------------------

def _quality_sessions_for(
    phase: str,
    limiter: Capability,
    week_index: int,
    goal: Goal,
    zones: PaceZones,
    days: list[date],
    reduced: bool,
) -> list[PlannedSession]:
    """Pick the week's quality work from the phase and the limiting capability."""
    first, second = days[0], days[1] if len(days) > 1 else days[0]
    rotation = week_index % 3

    if phase == "afinamiento":
        return [
            race_pace_session(first, goal, zones, reps=4, rep_m=400, recovery_s=90),
            short_reps(second, reps=6, rep_m=200, zones=zones, recovery_s=90),
        ][: 1 if reduced else 2]

    sessions: list[PlannedSession] = []
    if limiter is Capability.SPEED:
        sessions.append(short_reps(first, reps=10 + rotation * 2, rep_m=400, zones=zones))
        sessions.append(hill_reps(second, reps=8, rep_m=300, zones=zones) if rotation == 1
                        else tempo_run(second, km=6 + rotation, zones=zones))
    elif limiter is Capability.SPECIFIC_ENDURANCE:
        if phase in {"específico", "transformación"}:
            sessions.append(race_pace_session(first, goal, zones, reps=5, rep_m=1000, recovery_s=120))
        else:
            sessions.append(vo2_intervals(first, reps=5, rep_m=1000, zones=zones))
        sessions.append(tempo_run(second, km=6 + rotation, zones=zones))
    elif limiter is Capability.AEROBIC_BASE:
        sessions.append(cruise_intervals(first, reps=5, rep_m=1000, zones=zones))
        sessions.append(tempo_run(second, km=7 + rotation, zones=zones))
    elif limiter is Capability.CLOSING:
        sessions.append(vo2_intervals(first, reps=6, rep_m=800, zones=zones, recovery_s=120))
        sessions.append(race_pace_session(second, goal, zones, reps=3, rep_m=1600, recovery_s=150))
    else:  # recovery is the limiter — one quality session, and lower density
        sessions.append(cruise_intervals(first, reps=4, rep_m=1000, zones=zones))
        return sessions

    return sessions[:1] if reduced else sessions


def build_week(
    start: date,
    index: int,
    goal: Goal,
    zones: PaceZones,
    profile: AthleteProfile,
    limiter: Capability,
    weekly_km: float,
    reduced: bool = False,
) -> PlanWeek:
    """One microcycle: quality first, then volume distributed around it."""
    days_left = (goal.race_date - start).days
    phase = phase_for(max(days_left, 0))
    quality_days = [start + timedelta(days=offset) for offset in profile.quality_days]
    long_day = start + timedelta(days=profile.long_run_day)

    sessions: list[PlannedSession] = []
    race_this_week = start <= goal.race_date < start + timedelta(days=7)

    if race_this_week:
        # Race week: one sharpener early, everything else easy, race on the day.
        sessions.append(race_day_session(goal.race_date, goal))
        opener_day = goal.race_date - timedelta(days=3)
        if opener_day >= start:
            sessions.append(short_reps(opener_day, reps=4, rep_m=200, zones=zones, recovery_s=120))
    else:
        sessions.extend(
            _quality_sessions_for(phase, limiter, index, goal, zones, quality_days, reduced)
        )
        finish_fast = phase in {"transformación", "específico"} and index % 2 == 0
        long_km = _long_run_km(weekly_km, phase, goal)
        sessions.append(long_run(long_day, long_km, zones, finish_fast=finish_fast))

    used_days = {session.day for session in sessions}
    quality_volume = sum((session.distance_m or 0) for session in sessions) / 1000
    remaining_km = max(weekly_km - quality_volume - len(sessions) * 4, 12)
    filler_days = [
        start + timedelta(days=offset) for offset in range(7)
        if start + timedelta(days=offset) not in used_days
    ]
    rest_count = max(0, 7 - profile.days_per_week)
    # Rest goes the day after a hard session — that is when it does the most
    # good — falling back to whichever free day sits closest to one.
    previous_week_long = start - timedelta(days=1)  # last week's long run
    filler_days.sort(
        key=lambda day: (
            not _is_day_after_hard(day, sessions, previous_week_long),
            _distance_to_quality(day, sessions),
        )
    )
    for position, day in enumerate(filler_days):
        if position < rest_count:
            sessions.append(rest_day(day))
        else:
            share = remaining_km / max(len(filler_days) - rest_count, 1)
            strides = _is_day_before_quality(day, sessions)
            sessions.append(easy_run(day, round(share), zones, strides=strides))

    sessions.sort(key=lambda session: session.day)
    return PlanWeek(
        start=start,
        index=index,
        theme=PHASE_THEMES[phase],
        phase=phase,
        sessions=sessions,
        target_km=weekly_km,
    )


def _distance_to_quality(day: date, sessions: list[PlannedSession]) -> int:
    quality_days = [session.day for session in sessions if session.workout_type.is_quality]
    if not quality_days:
        return 99
    return min(abs((day - quality).days) for quality in quality_days)


def _is_day_after_hard(day: date, sessions: list[PlannedSession], previous_long: date) -> bool:
    """True when the previous day was quality work, or last week's long run."""
    if day - timedelta(days=1) == previous_long:
        return True
    return any(
        session.workout_type.is_quality and session.day == day - timedelta(days=1)
        for session in sessions
    )


def _is_day_before_quality(day: date, sessions: list[PlannedSession]) -> bool:
    return any(
        session.workout_type.is_quality and session.day == day + timedelta(days=1)
        for session in sessions
    )


def _long_run_km(weekly_km: float, phase: str, goal: Goal) -> float:
    share = 0.28 if phase == "base" else 0.25 if phase == "transformación" else 0.22
    if phase == "afinamiento":
        share = 0.18
    ceiling = 34 if goal.distance_m >= 5000 else 26
    return round(min(weekly_km * share, ceiling))


def build_plan(
    goal: Goal,
    zones: PaceZones,
    profile: AthleteProfile,
    readiness: RaceReadiness,
    current_weekly_km: float,
    weeks: int = 6,
    from_day: date | None = None,
) -> list[PlanWeek]:
    """The block from this week to race week."""
    start = week_start(from_day or date.today())
    limiter = readiness.limiter.capability
    plan: list[PlanWeek] = []

    for index in range(weeks):
        week_monday = start + timedelta(weeks=index)
        if week_monday > goal.race_date:
            break
        days_left = (goal.race_date - week_monday).days
        phase = phase_for(max(days_left, 0))

        # Volume builds ~4% a week, drops every fourth week, and tapers in.
        growth = 1 + 0.04 * index
        if (index + 1) % 4 == 0:
            growth *= 0.80
        if phase == "afinamiento":
            growth *= 0.62
        weekly_km = min(current_weekly_km * growth, profile.weekly_km_target * 1.15)
        reduced = phase == "afinamiento" or (index + 1) % 4 == 0

        plan.append(
            build_week(week_monday, index + 1, goal, zones, profile, limiter, weekly_km, reduced)
        )
    return plan


# --- today's recommendation --------------------------------------------------

@dataclass
class Recommendation:
    """What to do today, why, and the softer option if the athlete is tired."""

    session: PlannedSession
    reason: str
    alternative: PlannedSession | None
    alternative_reason: str


def recommend_today(
    plan_week: PlanWeek,
    readiness: Readiness,
    race_readiness: RaceReadiness,
    zones: PaceZones,
    today: date | None = None,
) -> Recommendation:
    """Today's session, adjusted for how the athlete actually is.

    The plan proposes; readiness disposes. A quality session on a fatigued day
    is downgraded rather than dropped, so the week keeps its shape.
    """
    today = today or date.today()
    scheduled = next((session for session in plan_week.sessions if session.day == today), None)
    if scheduled is None:
        scheduled = easy_run(today, 10, zones)

    reason = _reason_for(scheduled, race_readiness, readiness)

    if scheduled.workout_type.is_quality and readiness.score < 55:
        downgraded = _downgrade(scheduled, zones, today)
        return Recommendation(
            session=downgraded,
            reason=(
                f"{readiness.summary} Por eso hoy la sesión de calidad baja de intensidad "
                f"en lugar de suspenderse: mantenés el estímulo sin profundizar la fatiga."
            ),
            alternative=scheduled,
            alternative_reason="Si al empezar te sentís bien, la sesión original sigue disponible.",
        )

    alternative = None
    alternative_reason = ""
    if scheduled.workout_type.is_quality:
        alternative = _downgrade(scheduled, zones, today)
        alternative_reason = "Alternativa más suave si llegás cansado a la entrada en calor."
    return Recommendation(scheduled, reason, alternative, alternative_reason)


def _reason_for(session: PlannedSession, race_readiness: RaceReadiness, readiness: Readiness) -> str:
    limiter = race_readiness.limiter
    if session.workout_type.is_quality and limiter.gap:
        return limiter.gap
    if session.workout_type is WorkoutType.EASY and session.distance_m == 0:
        return "Venís de acumular carga y el descanso es parte del estímulo."
    if session.workout_type is WorkoutType.EASY:
        return (
            "El objetivo de hoy es llegar entero a la próxima sesión de calidad, "
            "no sumar velocidad."
        )
    if session.workout_type is WorkoutType.LONG:
        return race_readiness.by(Capability.AEROBIC_BASE).gap or (
            "La tirada larga sostiene el resto del plan: es donde se construye la base."
        )
    return race_readiness.summary


def _downgrade(session: PlannedSession, zones: PaceZones, today: date) -> PlannedSession:
    """A softer version of a session that keeps its purpose."""
    if session.workout_type is WorkoutType.INTERVALS and session.distance_m:
        reps = max(3, int(session.distance_m // 1000) - 2)
        return cruise_intervals(today, reps=reps, rep_m=1000, zones=zones, recovery_s=90)
    if session.workout_type is WorkoutType.REPS:
        return short_reps(today, reps=6, rep_m=200, zones=zones, recovery_s=90)
    if session.workout_type is WorkoutType.TEMPO:
        return tempo_run(today, km=4, zones=zones)
    if session.workout_type is WorkoutType.LONG and session.distance_m:
        return long_run(today, round(session.distance_m / 1000 * 0.7), zones)
    return easy_run(today, 8, zones, strides=True)


# --- adaptation --------------------------------------------------------------

@dataclass
class Adaptation:
    week: PlanWeek
    changes: list[str]
    explanation: str


def adapt_week(
    week: PlanWeek,
    event: str,
    zones: PaceZones,
    from_day: date | None = None,
    detail: str = "",
) -> Adaptation:
    """Rebuild the rest of the week after something changed.

    `event` is one of: enfermedad, sesion_perdida, carrera_inesperada, fatiga,
    molestia, exceso. Sessions already completed are never touched.
    """
    from_day = from_day or date.today()
    changes: list[str] = []
    kept = [session for session in week.sessions if session.day < from_day]
    upcoming = [session for session in week.sessions if session.day >= from_day]
    rebuilt: list[PlannedSession] = []

    if event == "enfermedad":
        for session in upcoming:
            if session.workout_type.is_quality:
                replacement = easy_run(session.day, 6, zones)
                replacement.note = "Reemplaza calidad por enfermedad"
                rebuilt.append(replacement)
                changes.append(f"{_day_name(session.day)}: {session.title} → rodaje corto")
            elif session.workout_type is WorkoutType.LONG and session.distance_m:
                replacement = easy_run(session.day, round(session.distance_m / 1000 * 0.5), zones)
                rebuilt.append(replacement)
                changes.append(f"{_day_name(session.day)}: fondo reducido a la mitad")
            else:
                rebuilt.append(session)
        explanation = (
            "Con síntomas activos no se recupera carga perdida: la semana pasa a "
            "sostenimiento y el bloque se reanuda cuando estés sano dos días seguidos."
        )

    elif event == "carrera_inesperada":
        # A race is a maximal stimulus. Everything hard within 72 h goes.
        race_day = from_day
        for session in upcoming:
            gap = (session.day - race_day).days
            if session.workout_type.is_quality and 0 <= gap <= 3:
                replacement = easy_run(session.day, 8, zones, strides=gap >= 3)
                replacement.note = "Reemplazada por competencia reciente"
                rebuilt.append(replacement)
                changes.append(f"{_day_name(session.day)}: {session.title} → rodaje suave")
            else:
                rebuilt.append(session)
        explanation = (
            "La competencia ya cubrió el estímulo intenso de la semana. Encadenar otra "
            "sesión dura en 72 h suma fatiga sin sumar adaptación."
        )

    elif event == "sesion_perdida":
        # Do not stack the missed session on top of the next one: keep spacing
        # and let the week end with one quality session instead of three.
        quality = [session for session in upcoming if session.workout_type.is_quality]
        rebuilt = list(upcoming)
        if quality:
            changes.append(
                f"Se mantiene {quality[0].title} el {_day_name(quality[0].day)} sin adelantarlo."
            )
        explanation = (
            "La sesión perdida no se recupera. Moverla hacia adelante juntaría dos "
            "estímulos fuertes con menos de 48 h de separación y el segundo saldría peor."
        )

    elif event in {"fatiga", "molestia"}:
        first_quality = True
        for session in upcoming:
            if session.workout_type.is_quality and first_quality:
                replacement = _downgrade(session, zones, session.day)
                replacement.note = f"Ajustada por {event}"
                rebuilt.append(replacement)
                changes.append(f"{_day_name(session.day)}: {session.title} → {replacement.title}")
                first_quality = False
            elif session.workout_type.is_quality:
                replacement = easy_run(session.day, 10, zones)
                rebuilt.append(replacement)
                changes.append(f"{_day_name(session.day)}: {session.title} → rodaje")
            else:
                rebuilt.append(session)
        explanation = (
            "Se conserva un solo estímulo de calidad, con menor intensidad. "
            "Entrenar a través de la fatiga acumulada baja la calidad de las dos sesiones."
        ) if event == "fatiga" else (
            "Con molestia activa el objetivo es mantener el gesto sin agravarla: "
            "menos volumen a intensidad, y reevaluar en 48 h."
        )

    elif event == "exceso":
        # The extra intensity already banked this week's hard stimulus, so the
        # next quality session becomes easy running. Later ones stand.
        replaced = False
        for session in upcoming:
            if session.workout_type.is_quality and not replaced:
                replacement = easy_run(session.day, 10, zones)
                replacement.note = "Compensa exceso previo"
                rebuilt.append(replacement)
                changes.append(f"{_day_name(session.day)}: {session.title} → rodaje")
                replaced = True
            else:
                rebuilt.append(session)
        explanation = (
            "El entrenamiento anterior fue más intenso de lo previsto, así que ya cubrió "
            "parte del estímulo de la semana. Se libera espacio para absorberlo."
        )
    else:
        rebuilt = list(upcoming)
        explanation = "Sin cambios."

    # Deduplicate by day, keeping the rebuilt version.
    by_day: dict[date, PlannedSession] = {}
    for session in kept + rebuilt:
        by_day[session.day] = session
    sessions = sorted(by_day.values(), key=lambda session: session.day)

    new_week = PlanWeek(
        start=week.start,
        index=week.index,
        theme=week.theme,
        phase=week.phase,
        sessions=sessions,
        target_km=week.target_km,
    )
    if not changes:
        changes.append("Sin cambios necesarios en las sesiones restantes.")
    return Adaptation(week=new_week, changes=changes, explanation=explanation)


DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _day_name(day: date) -> str:
    return DAY_NAMES[day.weekday()]
