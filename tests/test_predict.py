"""Race prediction: reading fitness out of ordinary training."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from raceform.analysis.physiology import vdot, zones_for
from raceform.analysis.predict import (
    blended_vdot,
    collect_estimates,
    current_vdot,
    equivalent_performances,
    estimate_from_activity,
    predict_race,
    prediction_history,
    required_vdot,
    vdot_trend,
)
from raceform.models import Goal, WorkoutType

from .conftest import continuous_activity, interval_activity

TRUE_VDOT = 58.8


class TestEstimatesFromSessions:
    def test_a_race_gives_a_direct_estimate(self, zones):
        activity = continuous_activity(5000, 208, name="Carrera 5K")
        estimate = estimate_from_activity(activity, zones)
        assert estimate is not None
        assert estimate.source is WorkoutType.RACE
        assert estimate.confidence == 1.0
        assert estimate.vdot == pytest.approx(vdot(5000, 5 * 208), abs=0.2)

    def test_an_interval_session_estimates_race_fitness(self, zones):
        """5 × 1000 at interval pace should imply the fitness that produced it."""
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205, recovery_s=150)
        estimate = estimate_from_activity(activity, zones)
        assert estimate is not None
        assert estimate.vdot == pytest.approx(TRUE_VDOT, abs=2.5)

    def test_a_tempo_estimates_race_fitness(self, zones):
        activity = continuous_activity(8000, 229, name="Tempo")
        estimate = estimate_from_activity(activity, zones)
        assert estimate is not None
        assert estimate.vdot == pytest.approx(TRUE_VDOT, abs=2.5)

    def test_hill_sessions_are_not_used_as_evidence(self, zones):
        """Hill pace says nothing reliable about flat race fitness."""
        activity = interval_activity(
            reps=8, rep_m=300, rep_pace=235, elevation_per_rep=21, name="Repeticiones"
        )
        assert estimate_from_activity(activity, zones) is None

    def test_an_easy_run_carries_no_signal(self, zones):
        assert estimate_from_activity(continuous_activity(12000, 290), zones) is None

    def test_more_volume_earns_more_confidence(self, zones):
        small = estimate_from_activity(
            interval_activity(reps=3, rep_m=1000, rep_pace=205), zones
        )
        large = estimate_from_activity(
            interval_activity(reps=10, rep_m=1000, rep_pace=205, name="Series largas"), zones
        )
        assert large.confidence > small.confidence

    def test_short_reps_with_huge_rest_do_not_imply_elite_fitness(self, zones):
        """12 × 200 with 3 min rest is fast but says little about a 5K."""
        activity = interval_activity(
            reps=12, rep_m=200, rep_pace=170, recovery_s=180, name="Repeticiones"
        )
        estimate = estimate_from_activity(activity, zones)
        assert estimate is None or estimate.vdot < TRUE_VDOT + 6


class TestBlending:
    def test_recent_estimates_outweigh_old_ones(self, zones):
        activities = [
            continuous_activity(
                5000, 220, name="Carrera vieja", when=datetime(2026, 4, 1, 9, 0)
            ),
            continuous_activity(
                5000, 205, name="Carrera reciente", when=datetime(2026, 7, 20, 9, 0)
            ),
        ]
        estimates = collect_estimates(activities, zones, window_days=200)
        blended = blended_vdot(estimates)
        old, new = vdot(5000, 5 * 220), vdot(5000, 5 * 205)
        assert abs(blended - new) < abs(blended - old)

    def test_no_estimates_falls_back_to_a_default(self):
        assert blended_vdot([]) == pytest.approx(45.0)

    def test_improving_athlete_shows_a_positive_trend(self, demo, zones):
        estimates = collect_estimates(demo["activities"], zones)
        assert vdot_trend(estimates) > 0

    def test_trend_is_capped(self, zones):
        activities = [
            continuous_activity(
                3000, 240 - index * 25, name=f"Test {index}",
                when=datetime(2026, 7, 1, 9, 0) + timedelta(days=index * 4),
            )
            for index in range(6)
        ]
        estimates = collect_estimates(activities, zones)
        assert abs(vdot_trend(estimates)) <= 0.6


def test_current_vdot_recovers_the_demo_athletes_real_fitness(demo):
    """The whole point: read fitness from training, without needing a race."""
    estimated = current_vdot(demo["activities"])
    # The demo athlete finishes the block at a VDOT of 59.1 by construction.
    assert estimated == pytest.approx(59.1, abs=1.5)


def test_prediction_is_plausible_for_the_demo_athlete(demo, zones):
    goal = Goal.new("5K", 5000, date.today() + timedelta(days=42), target_time_s=16 * 60 + 59)
    prediction = predict_race(goal, demo["activities"], zones_for(current_vdot(demo["activities"])))
    assert 15 * 60 < prediction.central_s < 18 * 60
    assert prediction.low_s < prediction.central_s < prediction.high_s
    assert 0 < prediction.confidence <= 1
    assert prediction.basis


class TestPredictionAdjustments:
    def _goal(self, days: int = 42) -> Goal:
        return Goal.new("5K", 5000, date.today() + timedelta(days=days), target_time_s=1019)

    def test_freshness_makes_the_prediction_faster(self, demo, zones):
        goal = self._goal()
        tired = predict_race(goal, demo["activities"], zones, form_ratio=-0.25)
        fresh = predict_race(goal, demo["activities"], zones, form_ratio=0.10)
        assert fresh.central_s < tired.central_s

    def test_missing_specific_endurance_costs_time(self, demo, zones):
        goal = self._goal()
        ready = predict_race(goal, demo["activities"], zones, specific_readiness=95)
        short = predict_race(goal, demo["activities"], zones, specific_readiness=40)
        assert short.central_s > ready.central_s

    def test_trail_is_slower_than_track(self, demo, zones):
        track = Goal.new("5K", 5000, date.today() + timedelta(days=42), terrain="pista")
        trail = Goal.new("5K", 5000, date.today() + timedelta(days=42), terrain="trail")
        assert (
            predict_race(trail, demo["activities"], zones).central_s
            > predict_race(track, demo["activities"], zones).central_s
        )

    def test_a_distant_race_has_a_wider_range(self, demo, zones):
        near = predict_race(self._goal(days=5), demo["activities"], zones)
        far = predict_race(self._goal(days=120), demo["activities"], zones)
        near_width = near.high_s - near.low_s
        far_width = far.high_s - far.low_s
        assert far_width > near_width

    def test_no_activities_still_returns_a_prediction(self, zones):
        prediction = predict_race(self._goal(), [], zones)
        assert prediction.central_s > 0
        assert prediction.confidence < 0.5


def test_prediction_history_improves_over_the_block(demo, zones):
    goal = Goal.new("5K", 5000, date.today() + timedelta(days=42))
    points = prediction_history(goal, demo["activities"], zones, points=10)
    assert len(points) >= 4
    # An improving athlete's predicted time trends downwards.
    assert points[-1][1] < points[0][1]


def test_required_vdot_reflects_the_target():
    goal = Goal.new("5K", 5000, date.today(), target_time_s=16 * 60 + 59)
    assert required_vdot(goal) == pytest.approx(vdot(5000, 1019), abs=0.01)
    assert required_vdot(Goal.new("5K", 5000, date.today())) is None


def test_equivalent_performances_cover_track_distances():
    rows = equivalent_performances(58.8)
    labels = [label for label, _, _ in rows]
    assert "1500 m" in labels and "5000 m" in labels
    times = [seconds for _, _, seconds in rows]
    assert times == sorted(times)  # longer distances always take longer
