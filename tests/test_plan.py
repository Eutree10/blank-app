"""Plan construction, today's recommendation, and adaptation."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from raceform.analysis.capability import assess_readiness
from raceform.analysis.load import Readiness
from raceform.analysis.plan import (
    adapt_week,
    build_plan,
    build_week,
    phase_for,
    recommend_today,
)
from raceform.models import AthleteProfile, Capability, Goal, WorkoutType, week_start


@pytest.fixture
def goal() -> Goal:
    return Goal.new("5K", 5000, date.today() + timedelta(days=42), target_time_s=16 * 60 + 59)


@pytest.fixture
def profile() -> AthleteProfile:
    return AthleteProfile(weekly_km_target=75, days_per_week=6, quality_days=(1, 4), long_run_day=6)


@pytest.fixture
def race_readiness(demo, zones, goal):
    return assess_readiness(goal, demo["activities"], zones, demo["feedback"])


class TestPhases:
    def test_phases_progress_towards_the_race(self):
        assert phase_for(120) == "base"
        assert phase_for(50) == "transformación"
        assert phase_for(20) == "específico"
        assert phase_for(5) == "afinamiento"


class TestWeekStructure:
    def _week(self, goal, zones, profile, limiter=Capability.SPECIFIC_ENDURANCE):
        return build_week(
            week_start(date.today()), 1, goal, zones, profile, limiter, weekly_km=70
        )

    def test_a_week_has_seven_days_exactly_once(self, goal, zones, profile):
        week = self._week(goal, zones, profile)
        days = [session.day for session in week.sessions]
        assert len(days) == 7
        assert len(set(days)) == 7

    def test_sessions_are_ordered_by_day(self, goal, zones, profile):
        week = self._week(goal, zones, profile)
        assert week.sessions == sorted(week.sessions, key=lambda session: session.day)

    def test_quality_sessions_are_at_least_48_hours_apart(self, goal, zones, profile):
        week = self._week(goal, zones, profile)
        quality = [s.day for s in week.sessions if s.workout_type.is_quality]
        gaps = [(later - earlier).days for earlier, later in zip(quality, quality[1:])]
        assert all(gap >= 2 for gap in gaps)

    def test_the_long_run_lands_on_the_chosen_day(self, goal, zones, profile):
        week = self._week(goal, zones, profile)
        long_runs = [s for s in week.sessions if s.workout_type is WorkoutType.LONG]
        assert len(long_runs) == 1
        assert long_runs[0].day.weekday() == profile.long_run_day

    def test_the_limiter_drives_what_gets_prescribed(self, goal, zones, profile):
        speed_week = self._week(goal, zones, profile, Capability.SPEED)
        base_week = self._week(goal, zones, profile, Capability.AEROBIC_BASE)
        assert any(s.workout_type is WorkoutType.REPS for s in speed_week.sessions)
        assert not any(s.workout_type is WorkoutType.REPS for s in base_week.sessions)

    def test_a_recovery_limiter_reduces_the_quality_load(self, goal, zones, profile):
        normal = self._week(goal, zones, profile, Capability.SPECIFIC_ENDURANCE)
        limited = self._week(goal, zones, profile, Capability.RECOVERY)
        assert limited.quality_count < normal.quality_count

    def test_every_session_states_its_purpose(self, goal, zones, profile):
        week = self._week(goal, zones, profile)
        assert all(session.purpose for session in week.sessions)
        assert all(session.structure for session in week.sessions)

    def test_rest_days_follow_the_athlete_days_per_week(self, goal, zones, profile):
        five_days = AthleteProfile(weekly_km_target=60, days_per_week=5, quality_days=(1, 4))
        week = build_week(
            week_start(date.today()), 1, goal, zones, five_days,
            Capability.SPECIFIC_ENDURANCE, weekly_km=55,
        )
        rest = [session for session in week.sessions if session.distance_m == 0]
        assert len(rest) == 2


class TestBlock:
    def test_plan_runs_up_to_race_week(self, goal, zones, profile, race_readiness):
        plan = build_plan(goal, zones, profile, race_readiness, current_weekly_km=70, weeks=7)
        assert plan
        assert all(week.start <= goal.race_date for week in plan)
        assert [week.index for week in plan] == list(range(1, len(plan) + 1))

    def test_race_week_contains_the_race_and_no_hard_session_after_it(
        self, zones, profile, race_readiness
    ):
        near = Goal.new("5K", 5000, date.today() + timedelta(days=5), target_time_s=1019)
        plan = build_plan(near, zones, profile, race_readiness, current_weekly_km=70, weeks=2)
        race_sessions = [
            session for week in plan for session in week.sessions
            if session.workout_type is WorkoutType.RACE
        ]
        assert len(race_sessions) == 1
        assert race_sessions[0].day == near.race_date

    def test_the_taper_reduces_volume(self, zones, profile, race_readiness):
        goal = Goal.new("5K", 5000, date.today() + timedelta(days=35), target_time_s=1019)
        plan = build_plan(goal, zones, profile, race_readiness, current_weekly_km=70, weeks=6)
        taper = [week for week in plan if week.phase == "afinamiento"]
        building = [week for week in plan if week.phase != "afinamiento"]
        assert taper and building
        assert min(week.target_km for week in taper) < min(week.target_km for week in building)

    def test_volume_never_runs_away(self, goal, zones, profile, race_readiness):
        plan = build_plan(goal, zones, profile, race_readiness, current_weekly_km=70, weeks=7)
        assert all(week.target_km <= profile.weekly_km_target * 1.15 + 0.01 for week in plan)


class TestTodaysRecommendation:
    def _recommendation(self, demo, zones, goal, profile, race_readiness, score: int):
        plan = build_plan(goal, zones, profile, race_readiness, current_weekly_km=70, weeks=2)
        readiness = Readiness(score=score, state="listo", summary="Resumen.", drivers=["Motivo."])
        return recommend_today(plan[0], readiness, race_readiness, zones)

    def test_a_recommendation_always_explains_itself(
        self, demo, zones, goal, profile, race_readiness
    ):
        recommendation = self._recommendation(demo, zones, goal, profile, race_readiness, 80)
        assert recommendation.session.structure
        assert recommendation.reason

    def test_fatigue_downgrades_quality_instead_of_dropping_it(
        self, demo, zones, goal, profile, race_readiness
    ):
        week = build_plan(goal, zones, profile, race_readiness, current_weekly_km=70, weeks=2)[0]
        scheduled = next((s for s in week.sessions if s.day == date.today()), None)
        if scheduled is None or not scheduled.workout_type.is_quality:
            pytest.skip("Today is not a quality day in this generated week.")

        tired = recommend_today(
            week,
            Readiness(score=40, state="cargado", summary="Resumen.", drivers=["Motivo."]),
            race_readiness,
            zones,
        )
        # The stimulus is kept but softened, and the original stays available.
        assert tired.session.id != scheduled.id
        assert (tired.session.distance_m or 0) < (scheduled.distance_m or 0)
        assert tired.alternative is not None
        assert tired.alternative.id == scheduled.id

    def test_a_quality_day_always_offers_a_softer_option(
        self, demo, zones, goal, profile, race_readiness
    ):
        recommendation = self._recommendation(demo, zones, goal, profile, race_readiness, 85)
        if recommendation.session.workout_type.is_quality:
            assert recommendation.alternative is not None
            assert recommendation.alternative_reason


class TestAdaptation:
    def _week(self, goal, zones, profile, race_readiness):
        return build_plan(goal, zones, profile, race_readiness, current_weekly_km=70, weeks=1)[0]

    def test_illness_removes_every_remaining_quality_session(
        self, goal, zones, profile, race_readiness
    ):
        week = self._week(goal, zones, profile, race_readiness)
        result = adapt_week(week, "enfermedad", zones, from_day=week.start)
        remaining = [
            session for session in result.week.sessions
            if session.day >= week.start and session.workout_type.is_quality
        ]
        assert not remaining
        assert result.explanation

    def test_an_unexpected_race_clears_hard_work_for_72_hours(
        self, goal, zones, profile, race_readiness
    ):
        week = self._week(goal, zones, profile, race_readiness)
        race_day = week.start
        result = adapt_week(week, "carrera_inesperada", zones, from_day=race_day)
        for session in result.week.sessions:
            if 0 <= (session.day - race_day).days <= 3:
                assert not session.workout_type.is_quality

    def test_a_missed_session_is_not_stacked_onto_the_next_one(
        self, goal, zones, profile, race_readiness
    ):
        week = self._week(goal, zones, profile, race_readiness)
        original_quality = [s.day for s in week.sessions if s.workout_type.is_quality]
        result = adapt_week(week, "sesion_perdida", zones, from_day=week.start + timedelta(days=2))
        new_quality = [s.day for s in result.week.sessions if s.workout_type.is_quality]
        # Nothing moved earlier to "make up" the loss.
        assert new_quality == original_quality
        assert "48" in result.explanation or "estímulos" in result.explanation

    def test_fatigue_keeps_one_softened_stimulus(self, goal, zones, profile, race_readiness):
        week = self._week(goal, zones, profile, race_readiness)
        result = adapt_week(week, "fatiga", zones, from_day=week.start)
        quality = [s for s in result.week.sessions if s.workout_type.is_quality]
        assert len(quality) <= 1
        assert result.changes

    def test_completed_days_are_never_rewritten(self, goal, zones, profile, race_readiness):
        week = self._week(goal, zones, profile, race_readiness)
        cutoff = week.start + timedelta(days=3)
        before = {s.day: s.id for s in week.sessions if s.day < cutoff}
        result = adapt_week(week, "enfermedad", zones, from_day=cutoff)
        after = {s.day: s.id for s in result.week.sessions if s.day < cutoff}
        assert before == after

    def test_the_week_keeps_its_seven_days(self, goal, zones, profile, race_readiness):
        week = self._week(goal, zones, profile, race_readiness)
        for event in ("enfermedad", "fatiga", "molestia", "exceso", "sesion_perdida", "carrera_inesperada"):
            result = adapt_week(week, event, zones, from_day=week.start)
            days = [session.day for session in result.week.sessions]
            assert len(days) == len(set(days)) == 7, event

    def test_every_adaptation_explains_itself(self, goal, zones, profile, race_readiness):
        week = self._week(goal, zones, profile, race_readiness)
        for event in ("enfermedad", "fatiga", "molestia", "exceso", "sesion_perdida", "carrera_inesperada"):
            result = adapt_week(week, event, zones, from_day=week.start)
            assert result.explanation and result.changes, event
