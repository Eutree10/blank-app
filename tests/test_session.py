"""Session analysis: shape detection, scoring, narrative and comparison."""

from __future__ import annotations

from datetime import datetime

import pytest

from raceform.analysis.session import (
    aerobic_decoupling,
    analyze_session,
    rep_shape,
)
from raceform.models import Capability, Feedback

from .conftest import continuous_activity, interval_activity


class TestRepShape:
    def test_even_reps_are_consistent(self):
        shape, stats = rep_shape([205, 206, 205, 204, 206, 205])
        assert shape == "consistent"
        assert stats["cv"] < 0.01

    def test_a_fast_finish_is_a_surge(self):
        shape, _ = rep_shape([205] * 13 + [196, 195, 194])
        assert shape == "surge_finish"

    def test_losing_pace_late_is_a_fade(self):
        shape, _ = rep_shape([205, 205, 206, 206, 214, 218])
        assert shape == "fade"

    def test_getting_faster_throughout_is_progressive(self):
        shape, _ = rep_shape([212, 210, 207, 205, 202, 200])
        assert shape == "progressive"

    def test_wild_variation_is_erratic(self):
        shape, _ = rep_shape([195, 220, 198, 225, 200, 218])
        assert shape == "erratic"

    def test_too_few_reps_defaults_to_consistent(self):
        assert rep_shape([205, 206])[0] == "consistent"


class TestScoring:
    def test_even_execution_scores_well(self, zones):
        activity = interval_activity(reps=6, rep_m=1000, rep_pace=205)
        analysis = analyze_session(activity, zones)
        assert analysis.score >= 8

    def test_fading_scores_worse_than_holding(self, zones):
        steady = interval_activity(
            reps=6, rep_m=1000, rep_pace=205, rep_paces=[205, 205, 206, 205, 206, 205]
        )
        fading = interval_activity(
            reps=6, rep_m=1000, rep_pace=205, rep_paces=[203, 205, 208, 213, 219, 226]
        )
        assert analyze_session(fading, zones).score < analyze_session(steady, zones).score

    def test_score_stays_in_range(self, zones):
        chaotic = interval_activity(
            reps=6, rep_m=1000, rep_pace=205, rep_paces=[180, 240, 190, 250, 195, 260]
        )
        assert 1.0 <= analyze_session(chaotic, zones).score <= 10.0

    def test_a_limiting_niggle_costs_the_session(self, zones):
        activity = interval_activity(reps=6, rep_m=1000, rep_pace=205)
        clean = analyze_session(activity, zones)
        hurt = analyze_session(
            activity, zones,
            feedback=Feedback(activity.id, rpe=8, legs=3, niggle="Aquiles", niggle_severity=2),
        )
        assert hurt.score < clean.score
        assert any("molestia" in flag.lower() for flag in hurt.flags)

    def test_an_easy_run_is_graded_on_restraint(self, zones):
        controlled = continuous_activity(10000, 290, name="Rodaje")
        too_fast = continuous_activity(10000, 245, name="Rodaje")
        assert analyze_session(controlled, zones).score > analyze_session(too_fast, zones).score


class TestNarrative:
    def test_surge_narrative_names_the_stable_block_and_the_change(self, zones):
        activity = interval_activity(
            reps=16, rep_m=400, rep_pace=190, recovery_s=60,
            rep_paces=[190] * 13 + [182, 181, 180],
        )
        analysis = analyze_session(activity, zones)
        assert analysis.shape == "surge_finish"
        assert "reserva" in analysis.verdict
        assert "13" in analysis.verdict  # the reps that were consistent
        assert analysis.title == "16 × 400 m"
        assert analysis.headline.startswith("16 × 400 m — ")

    def test_every_analysis_has_a_verdict_and_advice(self, zones):
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205)
        analysis = analyze_session(activity, zones)
        assert analysis.verdict
        assert analysis.advice

    def test_metrics_include_the_numbers_a_runner_asks_for(self, zones):
        activity = interval_activity(reps=6, rep_m=1000, rep_pace=205)
        metrics = analyze_session(activity, zones).metrics
        for key in ("Ritmo medio", "Dispersión", "Más rápida", "Más lenta", "Recuperación media"):
            assert key in metrics

    def test_reps_are_paired_with_the_recovery_that_followed(self, zones):
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205, recovery_s=120)
        reps = analyze_session(activity, zones).reps
        assert len(reps) == 5
        assert [rep.number for rep in reps] == [1, 2, 3, 4, 5]
        # The last rep has no recovery after it.
        assert reps[-1].recovery_s is None
        assert all(rep.recovery_s == pytest.approx(120, abs=1) for rep in reps[:-1])


class TestCapabilityAttribution:
    def test_reps_at_rep_pace_train_speed(self, zones):
        activity = interval_activity(reps=12, rep_m=400, rep_pace=188, recovery_s=60)
        assert analyze_session(activity, zones).capability is Capability.SPEED

    def test_long_reps_at_vo2_pace_train_specific_endurance(self, zones):
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205)
        assert analyze_session(activity, zones).capability is Capability.SPECIFIC_ENDURANCE

    def test_a_long_run_trains_the_aerobic_base(self, zones):
        activity = continuous_activity(22000, 285, name="Fondo")
        assert analyze_session(activity, zones).capability is Capability.AEROBIC_BASE

    def test_intervals_run_at_threshold_are_attributed_honestly(self, zones):
        """Called intervals, run at threshold: what it trained is what counts."""
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=232, recovery_s=60)
        analysis = analyze_session(activity, zones)
        assert analysis.capability is Capability.SPECIFIC_ENDURANCE
        assert "umbral" in analysis.capability_note.lower()


class TestComparison:
    def test_first_session_of_its_kind_says_so(self, zones):
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205)
        assert "Primera" in analyze_session(activity, zones).comparison

    def test_improvement_against_an_equivalent_session_is_reported(self, zones):
        older = interval_activity(
            reps=5, rep_m=1000, rep_pace=210, when=datetime(2026, 6, 16, 7, 0), name="Series A"
        )
        newer = interval_activity(
            reps=5, rep_m=1000, rep_pace=204, when=datetime(2026, 7, 21, 7, 0), name="Series B"
        )
        history = [analyze_session(older, zones)]
        analysis = analyze_session(newer, zones, history=history)
        assert "más rápido" in analysis.comparison
        assert "semanas" in analysis.comparison


class TestDecoupling:
    def test_rising_heart_rate_at_constant_pace_is_decoupling(self, zones):
        activity = continuous_activity(16000, 285, hr_start=145, hr_drift=1.6)
        assert aerobic_decoupling(activity) > 0.05

    def test_a_stable_run_shows_little_decoupling(self, zones):
        activity = continuous_activity(16000, 285, hr_start=145, hr_drift=0.0)
        assert abs(aerobic_decoupling(activity)) < 0.01

    def test_missing_heart_rate_returns_none(self, zones):
        activity = continuous_activity(16000, 285)
        assert aerobic_decoupling(activity) is None


def test_full_demo_history_analyses_without_error(demo, zones):
    analyses = []
    for activity in demo["activities"]:
        analyses.append(
            analyze_session(activity, zones, demo["feedback"].get(activity.id), history=analyses)
        )
    assert len(analyses) == len(demo["activities"])
    assert all(1.0 <= analysis.score <= 10.0 for analysis in analyses)
    assert all(analysis.verdict for analysis in analyses)
