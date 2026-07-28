"""Session analysis — the "what actually happened" engine.

Charts show the numbers. This module reads them: how even the reps were, where
the session tipped, what quality it really trained, and what to change next
time. Every sentence it produces is anchored to a number it computed.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from ..formats import (
    fmt_delta,
    fmt_num,
    fmt_pace,
    fmt_rep_distance,
    fmt_time,
)
from ..models import Activity, Capability, Feedback, PlannedSession, WorkoutType
from .classify import Classification, classify
from .physiology import (
    PaceZones,
    fraction_of_vdot,
    activity_pace,
    lap_pace,
    hr_reserve_fraction,
)


@dataclass
class RepRow:
    """One work repetition, ready for both the table and the chart."""

    number: int
    distance_m: float
    time_s: float
    pace_s_km: float
    gap_s_km: float
    hr: float | None
    recovery_s: float | None
    recovery_hr_drop: float | None


@dataclass
class SessionAnalysis:
    activity: Activity
    classification: Classification
    score: float
    headline: str
    verdict: str  # one or two sentences: what happened
    reps: list[RepRow] = field(default_factory=list)
    metrics: dict[str, str] = field(default_factory=dict)
    shape: str = "consistent"
    capability: Capability | None = None
    capability_note: str = ""
    comparison: str = ""
    advice: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def workout_type(self) -> WorkoutType:
        return self.classification.workout_type

    @property
    def title(self) -> str:
        seg = self.classification.segmentation
        if seg.structured and seg.rep_count:
            return f"{seg.rep_count} × {fmt_rep_distance(seg.mean_rep_distance_m)}"
        return f"{self.workout_type.label} · {fmt_num(self.activity.km, 1)} km"


# --- shape detection ---------------------------------------------------------

SHAPE_LABELS = {
    "consistent": "Ritmo consistente",
    "surge_finish": "Cierre más rápido",
    "fade": "Caída sobre el final",
    "progressive": "Progresivo",
    "erratic": "Irregular",
    "front_loaded": "Salida demasiado rápida",
}


def rep_shape(paces: list[float]) -> tuple[str, dict[str, float]]:
    """Classify the shape of a rep series and return the numbers behind it.

    `paces` are grade-adjusted s/km in session order. Lower is faster.
    """
    stats: dict[str, float] = {}
    if len(paces) < 3:
        return "consistent", stats

    mean_pace = statistics.mean(paces)
    cv = statistics.pstdev(paces) / mean_pace if mean_pace else 0.0
    stats["cv"] = cv

    split = _stable_block(paces)
    body, tail = paces[:split], paces[split:]
    body_mean = statistics.mean(body)
    tail_mean = statistics.mean(tail) if tail else body_mean
    tail_delta = (tail_mean - body_mean) / body_mean if body_mean else 0.0
    stats["tail_delta"] = tail_delta
    stats["body_cv"] = statistics.pstdev(body) / body_mean if body_mean and len(body) > 1 else 0.0
    stats["stable_reps"] = float(split)

    drift = _half_drift(paces)
    stats["drift"] = drift
    stats["body_drift"] = _half_drift(body) if len(body) >= 4 else 0.0

    # Order matters. Dispersion is checked first: when the reps are all over
    # the place, the drift and tail numbers describe noise, not a pattern.
    if cv > 0.045:
        return "erratic", stats
    # A progression declines through the whole session; a surge is a flat block
    # followed by a step change, so the body has to be flat for it to count.
    if drift <= -0.02 and stats["body_drift"] <= -0.01:
        return "progressive", stats
    if tail_delta <= -0.025 and stats["body_cv"] <= 0.025:
        return "surge_finish", stats
    if drift <= -0.02:
        return "progressive", stats
    if tail_delta >= 0.03 or drift >= 0.03:
        return "fade", stats
    if len(paces) >= 4 and paces[0] < mean_pace * 0.965:
        return "front_loaded", stats
    return "consistent", stats


def _half_drift(paces: list[float]) -> float:
    """Change from the first half to the second. Positive means slowing down."""
    half = len(paces) // 2
    if half == 0:
        return 0.0
    first = statistics.mean(paces[:half])
    second = statistics.mean(paces[half:])
    return (second - first) / first if first else 0.0


def _stable_block(paces: list[float]) -> int:
    """How many reps were run to the session's own baseline before it changed.

    Walks back from the last rep while it sits more than 2% off the median, so
    the narrative can say "the first 13" instead of a fixed fraction.
    """
    baseline = statistics.median(paces)
    if baseline <= 0:
        return len(paces)
    split = len(paces)
    while split > 2 and abs(paces[split - 1] - baseline) / baseline > 0.02:
        split -= 1
    return split


# --- scoring -----------------------------------------------------------------

def _band(value: float, best: float, worst: float) -> float:
    """Map a metric onto 0–1 where `best` scores 1 and `worst` scores 0."""
    if best == worst:
        return 1.0
    raw = (worst - value) / (worst - best)
    return max(0.0, min(1.0, raw))


def _score_structured(
    reps: list[RepRow],
    stats: dict[str, float],
    planned: PlannedSession | None,
    feedback: Feedback | None,
) -> tuple[float, list[str]]:
    """Score a rep session out of 10, and note what pulled it up or down."""
    notes: list[str] = []
    paces = [rep.gap_s_km for rep in reps]
    mean_pace = statistics.mean(paces)

    # Even pacing is the single clearest sign a session was controlled.
    consistency = _band(stats.get("cv", 0.0), best=0.008, worst=0.055)
    # Holding pace to the end (or improving) is durability.
    durability = _band(stats.get("drift", 0.0), best=-0.02, worst=0.045)
    components = [(consistency, 0.35), (durability, 0.30)]

    if planned and planned.target_pace_low and planned.target_pace_high:
        centre = (planned.target_pace_low + planned.target_pace_high) / 2
        tolerance = max((planned.target_pace_high - planned.target_pace_low) / 2, 3.0)
        miss = abs(mean_pace - centre) / tolerance
        execution = _band(miss, best=0.6, worst=3.0)
        components.append((execution, 0.25))
        if mean_pace < planned.target_pace_low - tolerance:
            notes.append("Corriste más rápido que el objetivo prescrito.")
        elif mean_pace > planned.target_pace_high + tolerance:
            notes.append("No alcanzaste el rango de ritmo objetivo.")
    else:
        components.append((consistency, 0.25))  # no target: pacing carries the weight

    if feedback and feedback.rpe:
        # Getting the work done at a lower perceived cost is a better session.
        efficiency = _band(feedback.rpe, best=6.0, worst=10.0)
        components.append((efficiency, 0.10))
        if feedback.rpe >= 9:
            notes.append("El esfuerzo percibido fue muy alto para el estímulo buscado.")
    else:
        components.append((durability, 0.10))

    total_weight = sum(weight for _, weight in components)
    score = 10.0 * sum(value * weight for value, weight in components) / total_weight

    if feedback and feedback.niggle_severity >= 2:
        score -= 1.0
        notes.append("Reportaste una molestia que limitó la sesión.")
    return max(1.0, min(10.0, score)), notes


def _score_continuous(
    activity: Activity,
    workout_type: WorkoutType,
    zones: PaceZones,
    decoupling: float | None,
    feedback: Feedback | None,
) -> tuple[float, list[str]]:
    notes: list[str] = []
    gap = activity_pace(activity)
    fraction = fraction_of_vdot(gap, zones.vdot)
    components: list[tuple[float, float]] = []

    if workout_type is WorkoutType.EASY:
        # An easy run is graded on restraint, not on speed.
        easy_fast, easy_slow = zones.easy
        if gap < easy_fast:
            overshoot = (easy_fast - gap) / easy_fast
            discipline = _band(overshoot, best=0.0, worst=0.10)
            notes.append("Rodaje corrido por encima de la zona aeróbica fácil.")
        else:
            discipline = 1.0
        components.append((discipline, 0.7))
    elif workout_type is WorkoutType.LONG:
        components.append((_band(abs(fraction - 0.76), best=0.02, worst=0.14), 0.4))
        if decoupling is not None:
            components.append((_band(decoupling, best=0.02, worst=0.10), 0.35))
            if decoupling > 0.08:
                notes.append("La frecuencia cardíaca se desacopló del ritmo en la segunda mitad.")
    else:  # tempo, race, test
        components.append((_band(abs(fraction - 0.86), best=0.01, worst=0.12), 0.5))
        if decoupling is not None:
            components.append((_band(decoupling, best=0.02, worst=0.09), 0.25))

    if feedback and feedback.rpe:
        expected_rpe = 3 if workout_type is WorkoutType.EASY else 6 if workout_type is WorkoutType.LONG else 8
        components.append((_band(abs(feedback.rpe - expected_rpe), best=0.5, worst=4.0), 0.25))
    if not components:
        components.append((0.7, 1.0))

    total_weight = sum(weight for _, weight in components)
    score = 10.0 * sum(value * weight for value, weight in components) / total_weight
    if feedback and feedback.niggle_severity >= 2:
        score -= 1.0
        notes.append("Reportaste una molestia que limitó la sesión.")
    return max(1.0, min(10.0, score)), notes


# --- capability attribution --------------------------------------------------

def attributed_capability(
    workout_type: WorkoutType, reps: list[RepRow], zones: PaceZones
) -> tuple[Capability | None, str]:
    """What the session actually trained — which is not always what it was called."""
    if workout_type is WorkoutType.EASY:
        return Capability.AEROBIC_BASE, "Volumen aeróbico y recuperación activa."
    if workout_type is WorkoutType.LONG:
        return Capability.AEROBIC_BASE, "Resistencia aeróbica y economía a ritmo bajo."
    if workout_type is WorkoutType.TEMPO:
        return Capability.SPECIFIC_ENDURANCE, "Tolerancia al umbral: sostener ritmo sin acumular lactato."
    if workout_type is WorkoutType.HILLS:
        return Capability.SPEED, "Fuerza específica y potencia de zancada."
    if workout_type in {WorkoutType.RACE, WorkoutType.TEST}:
        return Capability.SPECIFIC_ENDURANCE, "Estímulo competitivo completo."

    if not reps:
        return None, ""
    mean_pace = statistics.mean(rep.gap_s_km for rep in reps)
    fraction = fraction_of_vdot(mean_pace, zones.vdot)
    mean_distance = statistics.mean(rep.distance_m for rep in reps)

    # The zone the reps were actually run in decides what was trained, not the
    # label on the session.
    if fraction >= 1.03:
        return Capability.SPEED, "Velocidad pura y economía neuromuscular."
    if fraction >= 0.93:
        if mean_distance >= 800:
            return Capability.SPECIFIC_ENDURANCE, "Consumo máximo y resistencia específica de 3K–5K."
        return Capability.SPEED, "Velocidad con soporte aeróbico."
    if fraction >= 0.825:
        return Capability.SPECIFIC_ENDURANCE, "Umbral fraccionado: ritmo sostenible sin desgaste."
    return Capability.AEROBIC_BASE, "Estímulo aeróbico moderado."


# --- narrative ---------------------------------------------------------------

def _verdict_structured(
    seg_count: int, rep_label: str, shape: str, stats: dict[str, float], reps: list[RepRow]
) -> str:
    stable = int(stats.get("stable_reps", seg_count))
    tail_count = max(seg_count - stable, 1)
    tail_pct = abs(stats.get("tail_delta", 0.0)) * 100
    cv_pct = stats.get("cv", 0.0) * 100
    drift_pct = stats.get("drift", 0.0) * 100

    if shape == "surge_finish":
        return (
            f"Ritmo consistente durante las primeras {stable} repeticiones. "
            f"Las últimas {tail_count} fueron {fmt_num(tail_pct, 1)} % más rápidas, "
            "lo que demuestra reserva, aunque el cambio fue demasiado brusco para "
            "mantener el objetivo original de la sesión."
        )
    if shape == "fade":
        slowest = max(reps, key=lambda rep: rep.gap_s_km)
        return (
            f"Sostuviste el ritmo hasta la repetición {stable}, y a partir de ahí "
            f"perdiste {fmt_num(tail_pct, 1)} %. La más lenta fue la número "
            f"{slowest.number} ({fmt_pace(slowest.pace_s_km)}). El estímulo se cortó "
            "antes de completarse."
        )
    if shape == "progressive":
        return (
            f"Sesión progresiva: la segunda mitad fue {fmt_num(abs(drift_pct), 1)} % "
            "más rápida que la primera, con control en todo momento. Es la forma "
            "de ejecución que mejor traslada a competencia."
        )
    if shape == "erratic":
        fastest = min(reps, key=lambda rep: rep.gap_s_km)
        slowest = max(reps, key=lambda rep: rep.gap_s_km)
        return (
            f"Variación alta entre repeticiones ({fmt_num(cv_pct, 1)} % de dispersión): "
            f"desde {fmt_pace(fastest.pace_s_km)} hasta {fmt_pace(slowest.pace_s_km)}. "
            "El estímulo fue irregular y difícil de repetir."
        )
    if shape == "front_loaded":
        return (
            f"Arrancaste por encima del ritmo objetivo y después te acomodaste. "
            f"La deriva total fue de {fmt_num(drift_pct, 1)} %. La sesión funcionó, "
            "pero costó más de lo necesario."
        )
    return (
        f"Ejecución pareja en las {seg_count} repeticiones "
        f"({fmt_num(cv_pct, 1)} % de dispersión, {fmt_delta(drift_pct, '%', 1)} entre mitades). "
        "El estímulo se completó tal como estaba planteado."
    )


def _verdict_continuous(
    activity: Activity, workout_type: WorkoutType, zones: PaceZones, decoupling: float | None
) -> str:
    gap = activity_pace(activity)
    zone = zones.zone_of(gap)
    parts: list[str] = []

    if workout_type is WorkoutType.EASY:
        easy_fast, _ = zones.easy
        if gap < easy_fast:
            parts.append(
                f"Rodaje a {fmt_pace(activity.pace_s_km)}, más rápido que el techo "
                f"aeróbico fácil ({fmt_pace(easy_fast)}). Suma fatiga sin sumar estímulo."
            )
        else:
            parts.append(
                f"Rodaje controlado a {fmt_pace(activity.pace_s_km)}, dentro de la zona fácil. "
                "Cumple su función: acumular volumen sin costo."
            )
    elif workout_type is WorkoutType.LONG:
        parts.append(
            f"{fmt_num(activity.km, 1)} km continuos a {fmt_pace(activity.pace_s_km)} "
            f"en zona {_zone_es(zone)}."
        )
    else:
        parts.append(
            f"{fmt_num(activity.km, 1)} km sostenidos a {fmt_pace(activity.pace_s_km)} "
            f"en zona {_zone_es(zone)}."
        )

    if decoupling is not None:
        if decoupling > 0.06:
            parts.append(
                f"La frecuencia cardíaca subió {fmt_num(decoupling * 100, 1)} % respecto al ritmo "
                "en la segunda mitad: el desgaste apareció antes del final."
            )
        elif decoupling < 0.03:
            parts.append("El pulso se mantuvo acoplado al ritmo de principio a fin.")
    return " ".join(parts)


def _zone_es(zone: str) -> str:
    return {
        "easy": "aeróbica fácil",
        "marathon": "de maratón",
        "threshold": "de umbral",
        "interval": "de VO2 máx",
        "repetition": "de velocidad",
    }.get(zone, zone)


def _advice(
    workout_type: WorkoutType, shape: str, stats: dict[str, float], score: float, notes: list[str]
) -> str:
    if notes:
        base = notes[0]
    else:
        base = ""
    tips = {
        "surge_finish": "La próxima vez repartí esa reserva desde la mitad de la serie en lugar de gastarla al final.",
        "fade": "Bajá una o dos repeticiones, o arrancá 2 s/km más lento: el objetivo es terminar la serie completa al mismo ritmo.",
        "progressive": "Mantené esta ejecución y subí el ritmo de arranque 1–2 s/km en la próxima.",
        "erratic": "Fijá el ritmo objetivo antes de arrancar y controlá cada repetición en el primer parcial.",
        "front_loaded": "Usá las dos primeras repeticiones como calibración, no como referencia máxima.",
        "consistent": "Estás listo para subir el estímulo: sumá una repetición o acortá 15 s la recuperación.",
    }
    tip = tips.get(shape, "")
    if workout_type is WorkoutType.EASY and "más rápido" in base:
        tip = "Bajá el rodaje al rango fácil: la ganancia está en llegar entero a la próxima sesión de calidad."
    if score < 5 and workout_type.is_quality:
        tip = "Antes de repetir esta sesión, priorizá un día fácil: la ejecución sugiere fatiga acumulada."
    return " ".join(part for part in [base, tip] if part).strip()


# --- decoupling --------------------------------------------------------------

def aerobic_decoupling(activity: Activity) -> float | None:
    """How much HR drifted relative to pace between the two halves of a run.

    Positive means the same pace cost more heartbeats late in the run.
    """
    splits = activity.splits_km or activity.laps
    usable = [
        lap for lap in splits
        if lap.average_heartrate and lap.distance_m > 400 and lap.moving_time_s > 0
    ]
    if len(usable) < 4:
        return None
    half = len(usable) // 2
    first, second = usable[:half], usable[half:]

    def efficiency(laps: list) -> float:
        speeds = [lap.speed_ms for lap in laps]
        hrs = [lap.average_heartrate for lap in laps]
        mean_hr = statistics.mean(hrs)
        return statistics.mean(speeds) / mean_hr if mean_hr else 0.0

    first_eff, second_eff = efficiency(first), efficiency(second)
    if not first_eff:
        return None
    return (first_eff - second_eff) / first_eff


# --- entry point -------------------------------------------------------------

def build_reps(classification: Classification, hr_rest: float | None, hr_max: float | None) -> list[RepRow]:
    """Pair each work rep with the recovery that followed it."""
    seg = classification.segmentation
    if not seg.structured:
        return []
    work_ids = {id(lap) for lap in seg.work}
    ordered = sorted(seg.work + seg.recovery, key=lambda lap: lap.index)

    rows: list[RepRow] = []
    number = 0
    for position, lap in enumerate(ordered):
        if id(lap) not in work_ids:
            continue
        number += 1
        following = ordered[position + 1] if position + 1 < len(ordered) else None
        recovery_s = None
        recovery_drop = None
        if following is not None and id(following) not in work_ids:
            recovery_s = following.moving_time_s
            if lap.max_heartrate and following.average_heartrate:
                recovery_drop = lap.max_heartrate - following.average_heartrate
        rows.append(
            RepRow(
                number=number,
                distance_m=lap.distance_m,
                time_s=lap.moving_time_s,
                pace_s_km=lap.pace_s_km,
                gap_s_km=lap_pace(lap),
                hr=lap.average_heartrate,
                recovery_s=recovery_s,
                recovery_hr_drop=recovery_drop,
            )
        )
    return rows


def analyze_session(
    activity: Activity,
    zones: PaceZones,
    feedback: Feedback | None = None,
    planned: PlannedSession | None = None,
    history: list["SessionAnalysis"] | None = None,
    hr_rest: float | None = None,
    hr_max: float | None = None,
) -> SessionAnalysis:
    """Full read of one activity: score, verdict, metrics, comparison, advice."""
    classification = classify(activity, zones)
    workout_type = classification.workout_type
    reps = build_reps(classification, hr_rest, hr_max)
    decoupling = aerobic_decoupling(activity)
    metrics: dict[str, str] = {}
    flags: list[str] = []

    if reps:
        paces = [rep.gap_s_km for rep in reps]
        shape, stats = rep_shape(paces)
        score, notes = _score_structured(reps, stats, planned, feedback)
        fastest = min(reps, key=lambda rep: rep.gap_s_km)
        slowest = max(reps, key=lambda rep: rep.gap_s_km)
        metrics = {
            "Ritmo medio": fmt_pace(statistics.mean(rep.pace_s_km for rep in reps)),
            "Dispersión": fmt_num(stats.get("cv", 0.0) * 100, 1) + " %",
            "Más rápida": f"#{fastest.number} · {fmt_pace(fastest.pace_s_km)}",
            "Más lenta": f"#{slowest.number} · {fmt_pace(slowest.pace_s_km)}",
            "Deriva 1ª/2ª mitad": fmt_delta(stats.get("drift", 0.0) * 100, "%", 1),
            "Volumen de calidad": f"{fmt_num(sum(rep.distance_m for rep in reps) / 1000, 1)} km",
        }
        recoveries = [rep.recovery_s for rep in reps if rep.recovery_s]
        if recoveries:
            metrics["Recuperación media"] = fmt_time(statistics.mean(recoveries))
        drops = [rep.recovery_hr_drop for rep in reps if rep.recovery_hr_drop]
        if drops:
            metrics["Caída de pulso"] = f"−{fmt_num(statistics.mean(drops), 0)} ppm"
        verdict = _verdict_structured(
            len(reps), fmt_rep_distance(statistics.mean(rep.distance_m for rep in reps)), shape, stats, reps
        )
    else:
        shape, stats = "consistent", {}
        score, notes = _score_continuous(activity, workout_type, zones, decoupling, feedback)
        metrics = {
            "Ritmo medio": fmt_pace(activity.pace_s_km),
            "Distancia": f"{fmt_num(activity.km, 1)} km",
            "Tiempo": fmt_time(activity.moving_time_s),
        }
        if activity.elevation_gain_m:
            metrics["Desnivel"] = f"{activity.elevation_gain_m:.0f} m"
        if activity.average_heartrate:
            metrics["Pulso medio"] = f"{activity.average_heartrate:.0f} ppm"
        if decoupling is not None:
            metrics["Desacople aeróbico"] = fmt_delta(decoupling * 100, "%", 1)
        verdict = _verdict_continuous(activity, workout_type, zones, decoupling)

    capability, capability_note = attributed_capability(workout_type, reps, zones)
    if hr_rest and hr_max and activity.average_heartrate:
        fraction = hr_reserve_fraction(activity.average_heartrate, hr_rest, hr_max)
        metrics["Intensidad cardíaca"] = f"{fraction * 100:.0f} % FCR"

    if feedback and feedback.niggle_severity >= 2:
        flags.append(f"Molestia reportada: {feedback.niggle or 'sin detalle'}")
    if decoupling is not None and decoupling > 0.09:
        flags.append("Desacople alto: revisar hidratación, calor o fatiga previa")

    analysis = SessionAnalysis(
        activity=activity,
        classification=classification,
        score=round(score, 1),
        headline="",
        verdict=verdict,
        reps=reps,
        metrics=metrics,
        shape=shape,
        capability=capability,
        capability_note=capability_note,
        advice=_advice(workout_type, shape, stats, score, notes),
        flags=flags,
    )
    analysis.headline = f"{analysis.title} — {fmt_num(analysis.score, 1)}/10"
    analysis.comparison = compare_with_history(analysis, history or [])
    return analysis


def compare_with_history(current: SessionAnalysis, history: list[SessionAnalysis]) -> str:
    """Find the closest comparable past session and say whether this beat it."""
    if not current.reps:
        return _compare_continuous(current, history)

    target_distance = statistics.mean(rep.distance_m for rep in current.reps)
    candidates = [
        past for past in history
        if past.activity.id != current.activity.id
        and past.reps
        and past.workout_type is current.workout_type
        and abs(statistics.mean(rep.distance_m for rep in past.reps) - target_distance) / target_distance < 0.2
    ]
    if not candidates:
        return "Primera sesión de este tipo registrada: queda como referencia."

    candidates.sort(key=lambda past: past.activity.start_date, reverse=True)
    reference = candidates[0]
    current_pace = statistics.mean(rep.gap_s_km for rep in current.reps)
    reference_pace = statistics.mean(rep.gap_s_km for rep in reference.reps)
    delta = current_pace - reference_pace
    weeks = (current.activity.start_date.date() - reference.activity.start_date.date()).days / 7
    when = f"hace {weeks:.0f} semanas" if weeks >= 1 else "esta misma semana"

    rep_delta = len(current.reps) - len(reference.reps)
    volume_note = ""
    if rep_delta > 0:
        volume_note = f" con {rep_delta} repetición(es) más"
    elif rep_delta < 0:
        volume_note = f" con {abs(rep_delta)} repetición(es) menos"

    if abs(delta) < 1.0:
        return f"Mismo ritmo que la sesión equivalente de {when}{volume_note}."
    direction = "más rápido" if delta < 0 else "más lento"
    return (
        f"{fmt_num(abs(delta), 1)} s/km {direction} que la sesión equivalente de {when}"
        f"{volume_note}."
    )


def _compare_continuous(current: SessionAnalysis, history: list[SessionAnalysis]) -> str:
    peers = [
        past for past in history
        if past.activity.id != current.activity.id
        and past.workout_type is current.workout_type
        and abs(past.activity.distance_m - current.activity.distance_m) / max(current.activity.distance_m, 1) < 0.25
    ]
    if len(peers) < 2:
        return ""
    recent = sorted(peers, key=lambda past: past.activity.start_date, reverse=True)[:6]
    mean_pace = statistics.mean(past.activity.pace_s_km for past in recent)
    delta = current.activity.pace_s_km - mean_pace
    if abs(delta) < 2:
        return (
            f"En línea con tus últimos {len(recent)} {current.workout_type.plural} "
            "de distancia similar."
        )
    direction = "más rápido" if delta < 0 else "más lento"
    return (
        f"{fmt_num(abs(delta), 0)} s/km {direction} que el promedio de tus últimos "
        f"{len(recent)} {current.workout_type.plural} de distancia similar."
    )
