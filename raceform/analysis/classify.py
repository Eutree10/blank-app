"""Workout classification.

Strava tells us distance, time and laps. It does not tell us what the session
*was*. This module segments laps into work and recovery, then decides which of
the eight families the run belongs to — that decision drives every downstream
analysis, so it reports its own confidence and reasoning.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from ..formats import snap_distance
from ..models import Activity, Lap, WorkoutType
from .physiology import PaceZones, activity_pace, lap_pace

# Name keywords are a strong signal when present, but never the only one.
_RACE_WORDS = re.compile(
    r"\b(carrera|race|competencia|compet[ií]|10k|5k|cross|maratón|maraton|"
    r"media|campeonato|torneo|gp\b)", re.IGNORECASE
)
_TEST_WORDS = re.compile(r"\b(test|control|time ?trial|tt\b|contrarreloj)", re.IGNORECASE)
_LONG_WORDS = re.compile(r"\b(fondo|largo|long run|tirada)", re.IGNORECASE)
_TEMPO_WORDS = re.compile(r"\b(tempo|umbral|threshold|ritmo controlado)", re.IGNORECASE)
_HILL_WORDS = re.compile(r"\b(cuesta|cuestas|hill|subida|repechos?)", re.IGNORECASE)
_EASY_WORDS = re.compile(r"\b(rodaje|suave|regenerativo|recuperaci[óo]n|easy|trote)", re.IGNORECASE)

MIN_WORK_LAP_M = 150.0  # below this a lap is a jog-back or a GPS artefact
LONG_RUN_MIN_M = 15_000.0
HILL_GRADE = 0.035  # 3.5% average on the work reps


@dataclass
class Segmentation:
    """Laps split into the reps that mattered and the recoveries between them."""

    work: list[Lap] = field(default_factory=list)
    recovery: list[Lap] = field(default_factory=list)
    structured: bool = False

    @property
    def rep_count(self) -> int:
        return len(self.work)

    @property
    def work_distance_m(self) -> float:
        return sum(lap.distance_m for lap in self.work)

    @property
    def mean_rep_distance_m(self) -> float:
        if not self.work:
            return 0.0
        return self.work_distance_m / len(self.work)

    @property
    def nominal_rep_distance_m(self) -> float:
        """The rep distance a coach would write down, e.g. 400 rather than 397."""
        return snap_distance(self.mean_rep_distance_m) if self.work else 0.0


@dataclass
class Classification:
    workout_type: WorkoutType
    confidence: float  # 0–1
    reason: str
    segmentation: Segmentation


def _auto_splits(laps: list[Lap]) -> bool:
    """True when 'laps' are really just automatic 1 km splits, not a structure."""
    if len(laps) < 2:
        return False
    body = laps[:-1]  # the final split is almost always a partial kilometre
    if not body:
        return False
    return all(abs(lap.distance_m - 1000) < 60 for lap in body)


def segment(activity: Activity, zones: PaceZones) -> Segmentation:
    """Split laps into work and recovery.

    A lap is work when it is meaningfully faster than the session's own middle
    ground. Comparing against the session median rather than an absolute pace
    keeps this honest for both a 400 m session and a hill session.
    """
    laps = [lap for lap in activity.laps if lap.distance_m > 0 and lap.moving_time_s > 0]
    if len(laps) < 3 or _auto_splits(laps):
        return Segmentation(structured=False)

    paces = [lap_pace(lap) for lap in laps]
    median_pace = statistics.median(paces)
    spread = (max(paces) - min(paces)) / median_pace if median_pace else 0.0

    # A continuous run has laps that all sit within a few percent of each other.
    if spread < 0.12:
        return Segmentation(structured=False)

    work: list[Lap] = []
    work_positions: list[int] = []
    for position, (lap, pace) in enumerate(zip(laps, paces)):
        is_fast = pace < median_pace * 0.98
        long_enough = lap.distance_m >= MIN_WORK_LAP_M
        if is_fast and long_enough:
            work.append(lap)
            work_positions.append(position)

    if len(work) < 2:
        return Segmentation(structured=False)

    # Recovery is only what sits *between* reps. The slow laps before the first
    # rep and after the last one are warm-up and cool-down: counting them as
    # recovery would inflate every rest statistic and wreck fitness estimates.
    first, last = work_positions[0], work_positions[-1]
    work_ids = {id(lap) for lap in work}
    recovery = [
        lap for position, lap in enumerate(laps)
        if first < position < last and id(lap) not in work_ids
    ]
    return Segmentation(work=work, recovery=recovery, structured=True)


def classify(activity: Activity, zones: PaceZones) -> Classification:
    """Decide which of the eight session families this activity is."""
    name = f"{activity.name} {activity.description}"
    seg = segment(activity, zones)

    # Explicit competition or test beats everything else.
    if _RACE_WORDS.search(name) or activity.strava_workout_type == 1:
        return Classification(WorkoutType.RACE, 0.95, "Identificada por el nombre de la actividad.", seg)
    if _TEST_WORDS.search(name):
        return Classification(WorkoutType.TEST, 0.9, "Marcada como test o control.", seg)

    if seg.structured:
        return _classify_structured(activity, seg, name)
    return _classify_continuous(activity, seg, zones, name)


def _classify_structured(activity: Activity, seg: Segmentation, name: str) -> Classification:
    rep_m = seg.nominal_rep_distance_m
    mean_grade = statistics.mean(lap.grade for lap in seg.work) if seg.work else 0.0

    if mean_grade >= HILL_GRADE or _HILL_WORDS.search(name):
        return Classification(
            WorkoutType.HILLS,
            0.85,
            f"{seg.rep_count} repeticiones con {mean_grade * 100:.1f}% de pendiente media.",
            seg,
        )
    if rep_m >= 800:
        return Classification(
            WorkoutType.INTERVALS,
            0.9,
            f"{seg.rep_count} × {rep_m:.0f} m con recuperación entre repeticiones.",
            seg,
        )
    return Classification(
        WorkoutType.REPS,
        0.85,
        f"{seg.rep_count} × {rep_m:.0f} m — repeticiones cortas.",
        seg,
    )


def _classify_continuous(
    activity: Activity, seg: Segmentation, zones: PaceZones, name: str
) -> Classification:
    pace = activity_pace(activity)
    zone = zones.zone_of(pace)

    if _TEMPO_WORDS.search(name) or zone in {"threshold", "marathon"}:
        # A long run held at marathon effort is still a long run, not a tempo.
        if zone == "marathon" and activity.distance_m >= LONG_RUN_MIN_M:
            return Classification(
                WorkoutType.LONG,
                0.75,
                "Distancia de fondo sostenida a ritmo firme.",
                seg,
            )
        return Classification(
            WorkoutType.TEMPO,
            0.8,
            "Ritmo sostenido en zona de umbral.",
            seg,
        )
    if zone in {"interval", "repetition"} and activity.distance_m < 6000:
        # A short, very fast continuous effort with no laps: treat as a test.
        return Classification(
            WorkoutType.TEST,
            0.6,
            "Esfuerzo corto y muy rápido sin estructura de series.",
            seg,
        )
    if activity.distance_m >= LONG_RUN_MIN_M or _LONG_WORDS.search(name):
        return Classification(
            WorkoutType.LONG,
            0.85,
            f"{activity.km:.1f} km continuos en zona aeróbica.",
            seg,
        )
    confidence = 0.9 if _EASY_WORDS.search(name) else 0.75
    return Classification(
        WorkoutType.EASY,
        confidence,
        "Ritmo aeróbico continuo, sin estímulo de calidad.",
        seg,
    )
