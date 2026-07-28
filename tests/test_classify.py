"""Workout classification and lap segmentation."""

from __future__ import annotations



from raceform.analysis.classify import classify, segment
from raceform.models import WorkoutType

from .conftest import continuous_activity, interval_activity


class TestSegmentation:
    def test_warmup_and_cooldown_are_not_counted_as_recovery(self, zones):
        """The bug that wrecks fitness estimates: a 3 km warm-up read as rest."""
        activity = interval_activity(reps=6, rep_m=800, rep_pace=205, recovery_s=120)
        seg = segment(activity, zones)

        assert seg.structured
        assert seg.rep_count == 6
        # Five recoveries between six reps — no warm-up, no cool-down.
        assert len(seg.recovery) == 5
        assert all(lap.name == "Recuperación" for lap in seg.recovery)

    def test_reps_are_identified_not_the_jogs(self, zones):
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205)
        seg = segment(activity, zones)
        assert [round(lap.distance_m) for lap in seg.work] == [1000] * 5

    def test_automatic_km_splits_are_not_a_structure(self, zones):
        activity = continuous_activity(12000, 285)
        activity.laps = activity.splits_km  # some devices report splits as laps
        assert not segment(activity, zones).structured

    def test_a_steady_run_with_few_laps_is_not_structured(self, zones):
        activity = continuous_activity(10000, 280)
        assert not segment(activity, zones).structured

    def test_nominal_distance_snaps_to_what_a_coach_would_write(self, zones):
        activity = interval_activity(reps=8, rep_m=397, rep_pace=190)
        seg = segment(activity, zones)
        assert seg.nominal_rep_distance_m == 400


class TestClassification:
    def test_long_reps_are_intervals(self, zones):
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205, name="Series")
        assert classify(activity, zones).workout_type is WorkoutType.INTERVALS

    def test_short_reps_are_reps(self, zones):
        activity = interval_activity(reps=12, rep_m=400, rep_pace=190, recovery_s=60)
        assert classify(activity, zones).workout_type is WorkoutType.REPS

    def test_uphill_reps_are_hills(self, zones):
        activity = interval_activity(
            reps=8, rep_m=300, rep_pace=235, elevation_per_rep=21, name="Repeticiones"
        )
        assert classify(activity, zones).workout_type is WorkoutType.HILLS

    def test_easy_run(self, zones):
        activity = continuous_activity(10000, 290, name="Rodaje")
        assert classify(activity, zones).workout_type is WorkoutType.EASY

    def test_long_run(self, zones):
        activity = continuous_activity(22000, 285, name="Fondo dominguero")
        assert classify(activity, zones).workout_type is WorkoutType.LONG

    def test_tempo_run(self, zones):
        activity = continuous_activity(8000, 229, name="Tempo")
        assert classify(activity, zones).workout_type is WorkoutType.TEMPO

    def test_race_detected_by_name(self, zones):
        activity = continuous_activity(5000, 208, name="Carrera 5K de la ciudad")
        assert classify(activity, zones).workout_type is WorkoutType.RACE

    def test_race_detected_by_strava_workout_type(self, zones):
        activity = continuous_activity(5000, 208, name="Domingo a full")
        activity.strava_workout_type = 1
        assert classify(activity, zones).workout_type is WorkoutType.RACE

    def test_test_detected_by_name(self, zones):
        activity = continuous_activity(3000, 210, name="Test 3000 m en pista")
        assert classify(activity, zones).workout_type is WorkoutType.TEST

    def test_long_run_at_firm_pace_is_still_a_long_run(self, zones):
        """A 20 km at marathon effort is a long run, not an hour-long tempo."""
        activity = continuous_activity(20000, 250, name="Fondo")
        assert classify(activity, zones).workout_type is WorkoutType.LONG

    def test_every_classification_explains_itself(self, zones):
        activity = interval_activity(reps=5, rep_m=1000, rep_pace=205)
        result = classify(activity, zones)
        assert result.reason
        assert 0 < result.confidence <= 1


def test_demo_history_is_classified_across_all_families(demo, zones):
    kinds = {classify(activity, zones).workout_type for activity in demo["activities"]}
    # A real block contains easy running, long runs, threshold and rep work.
    assert {
        WorkoutType.EASY, WorkoutType.LONG, WorkoutType.TEMPO, WorkoutType.INTERVALS
    } <= kinds
