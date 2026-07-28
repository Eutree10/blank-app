"""Training load, readiness, and the five-capability race breakdown."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from raceform.analysis.capability import (
    assess_readiness,
    cumulative_splits,
    race_strategy,
    weight_profile,
)
from raceform.analysis.load import (
    activity_load,
    build_load_state,
    compute_readiness,
    weekly_summaries,
)
from raceform.models import Capability, Feedback, Goal, HabitDay

from .conftest import continuous_activity, interval_activity


class TestLoad:
    def test_harder_sessions_carry_more_load(self, zones):
        easy = continuous_activity(10000, 300, name="Rodaje")
        tempo = continuous_activity(10000, 230, name="Tempo")
        assert activity_load(tempo, zones) > activity_load(easy, zones)

    def test_longer_sessions_carry_more_load(self, zones):
        short = continuous_activity(8000, 290)
        long_run = continuous_activity(24000, 290, name="Fondo")
        assert activity_load(long_run, zones) > activity_load(short, zones)

    def test_interval_load_is_computed_per_lap(self, zones):
        """Whole-activity averaging would rate a rep session as easy running."""
        session = interval_activity(reps=10, rep_m=1000, rep_pace=205)
        equivalent_easy = continuous_activity(
            session.distance_m, session.pace_s_km, name="Rodaje"
        )
        assert activity_load(session, zones) > activity_load(equivalent_easy, zones)

    def test_fitness_and_fatigue_build_and_decay(self, zones):
        activities = [
            continuous_activity(
                12000, 280, name=f"Rodaje {index}",
                when=datetime(2026, 5, 1) + timedelta(days=index),
            )
            for index in range(40)
        ]
        for index, activity in enumerate(activities):
            activity.id = f"load-{index}"
        # 40 days of daily running, then two weeks completely off.
        state = build_load_state(activities, zones, through=date(2026, 6, 24))
        assert state.fitness > 0
        # Fatigue responds faster than fitness while loading…
        mid = state.series[20]
        assert mid.fatigue > mid.fitness
        # …and decays faster than fitness once the load stops.
        assert state.series[-1].fatigue < state.series[-1].fitness
        assert state.series[-1].form > 0  # two weeks off leaves the athlete fresh

    def test_acwr_flags_a_volume_spike(self, zones):
        steady = [
            continuous_activity(
                8000, 290, name=f"R{index}", when=datetime(2026, 5, 1) + timedelta(days=index)
            )
            for index in range(28)
        ]
        spike = [
            continuous_activity(
                26000, 280, name=f"S{index}", when=datetime(2026, 5, 29) + timedelta(days=index)
            )
            for index in range(7)
        ]
        for index, activity in enumerate(steady + spike):
            activity.id = f"acwr-{index}"
        state = build_load_state(steady + spike, zones, through=date(2026, 6, 4))
        assert state.acwr() > 1.4

    def test_empty_history_is_safe(self, zones):
        state = build_load_state([], zones)
        assert state.series == []
        assert state.fitness == 0
        assert state.acwr() == 1.0

    def test_weekly_summaries_group_by_monday(self, demo, zones):
        weeks = weekly_summaries(demo["activities"], zones, weeks=8)
        assert weeks
        assert all(week.start.weekday() == 0 for week in weeks)
        assert all(week.km > 0 for week in weeks)
        assert weeks == sorted(weeks, key=lambda week: week.start)


class TestReadiness:
    def _state(self, zones, activities):
        return build_load_state(activities, zones)

    def test_demo_athlete_gets_a_coherent_readiness(self, demo, zones):
        state = self._state(zones, demo["activities"])
        readiness = compute_readiness(state, demo["activities"], demo["feedback"], demo["habits"])
        assert 0 <= readiness.score <= 100
        assert readiness.state in {"recuperado", "listo", "cargado", "fatigado"}
        assert readiness.summary and readiness.drivers

    def test_dead_legs_lower_the_score(self, demo, zones):
        state = self._state(zones, demo["activities"])
        recent = demo["activities"][-3:]
        good = {activity.id: Feedback(activity.id, rpe=6, legs=5) for activity in recent}
        bad = {activity.id: Feedback(activity.id, rpe=6, legs=1) for activity in recent}
        assert (
            compute_readiness(state, demo["activities"], bad, demo["habits"]).score
            < compute_readiness(state, demo["activities"], good, demo["habits"]).score
        )

    def test_an_active_niggle_lowers_the_score_and_is_reported(self, demo, zones):
        state = self._state(zones, demo["activities"])
        last = demo["activities"][-1]
        hurt = {last.id: Feedback(last.id, rpe=6, legs=3, niggle="Aquiles", niggle_severity=3)}
        readiness = compute_readiness(state, demo["activities"], hurt, demo["habits"])
        baseline = compute_readiness(state, demo["activities"], {}, demo["habits"])
        assert readiness.score < baseline.score
        assert any("Aquiles" in driver for driver in readiness.drivers)

    def test_short_sleep_lowers_the_score(self, demo, zones):
        state = self._state(zones, demo["activities"])
        today = date.today()
        rested = {
            today - timedelta(days=offset): HabitDay(today - timedelta(days=offset), sleep_hours=8.5)
            for offset in range(3)
        }
        tired = {
            today - timedelta(days=offset): HabitDay(today - timedelta(days=offset), sleep_hours=5.5)
            for offset in range(3)
        }
        assert (
            compute_readiness(state, demo["activities"], {}, tired).score
            < compute_readiness(state, demo["activities"], {}, rested).score
        )


class TestCapabilities:
    def _goal(self, distance=5000, target=16 * 60 + 59, days=42) -> Goal:
        return Goal.new("Objetivo", distance, date.today() + timedelta(days=days), target_time_s=target)

    def test_weights_change_with_race_distance(self):
        short = weight_profile(1500)
        long = weight_profile(5000)
        assert short[Capability.SPEED] > long[Capability.SPEED]
        assert long[Capability.AEROBIC_BASE] > short[Capability.AEROBIC_BASE]
        for profile in (short, long):
            assert sum(profile.values()) == pytest.approx(1.0)

    def test_all_five_capabilities_are_scored(self, demo, zones):
        readiness = assess_readiness(self._goal(), demo["activities"], zones, demo["feedback"])
        assert len(readiness.capabilities) == 5
        assert {score.capability for score in readiness.capabilities} == set(Capability)
        assert all(0 <= score.score <= 100 for score in readiness.capabilities)
        assert 0 <= readiness.overall <= 100

    def test_every_capability_shows_its_measurement(self, demo, zones):
        readiness = assess_readiness(self._goal(), demo["activities"], zones, demo["feedback"])
        assert all(score.detail for score in readiness.capabilities)

    def test_the_limiter_has_an_explanation(self, demo, zones):
        readiness = assess_readiness(self._goal(), demo["activities"], zones, demo["feedback"])
        assert readiness.limiter in readiness.capabilities
        assert readiness.summary

    def test_the_same_athlete_is_readier_for_a_realistic_target(self, demo, zones):
        """Readiness is measured against the goal, not in the abstract."""
        realistic = assess_readiness(
            self._goal(target=17 * 60 + 30), demo["activities"], zones, demo["feedback"]
        )
        ambitious = assess_readiness(
            self._goal(target=15 * 60 + 30), demo["activities"], zones, demo["feedback"]
        )
        assert realistic.overall > ambitious.overall

    def test_no_history_does_not_crash(self, zones):
        readiness = assess_readiness(self._goal(), [], zones, {})
        assert 0 <= readiness.overall <= 100


class TestRaceStrategy:
    def _goal(self):
        return Goal.new("5K", 5000, date.today() + timedelta(days=30), target_time_s=1019)

    def test_splits_cover_the_distance(self, demo, zones):
        goal = self._goal()
        readiness = assess_readiness(goal, demo["activities"], zones, demo["feedback"])
        splits, note = race_strategy(goal, 1030, readiness)
        assert len(splits) == 5  # one per kilometre
        assert note
        total = sum(seconds for _, seconds in splits)
        assert total == pytest.approx(goal.target_time_s, rel=0.02)

    def test_cumulative_splits_accumulate(self, demo, zones):
        goal = self._goal()
        readiness = assess_readiness(goal, demo["activities"], zones, demo["feedback"])
        rows = cumulative_splits(race_strategy(goal, 1030, readiness)[0])
        elapsed = [row[2] for row in rows]
        assert elapsed == sorted(elapsed)
        assert elapsed[-1] == pytest.approx(sum(row[1] for row in rows))

    def test_short_races_are_split_every_400(self, demo, zones):
        goal = Goal.new("1500", 1500, date.today() + timedelta(days=30), target_time_s=274)
        readiness = assess_readiness(goal, demo["activities"], zones, demo["feedback"])
        splits, _ = race_strategy(goal, 280, readiness)
        assert [label for label, _ in splits] == ["400 m", "800 m", "1200 m"]
