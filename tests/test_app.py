"""Formatting, storage, Strava mapping, the coach fallback and the engine."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import pytest

from raceform.coach import CoachContext, fallback_answer
from raceform.engine import build_dashboard
from raceform.formats import (
    fmt_day_long,
    fmt_distance,
    fmt_pace,
    fmt_pace_range,
    fmt_time,
    parse_time,
    snap_distance,
)
from raceform.models import Activity, Feedback, Goal, HabitDay, PlannedSession, WorkoutType
from raceform.store import AppState, merge_activities
from raceform.strava import activity_from_strava, authorize_url, is_run

from .conftest import continuous_activity


class TestFormats:
    @pytest.mark.parametrize(
        "seconds,expected",
        [(1042, "17:22"), (3725, "1:02:05"), (59, "0:59"), (0, "0:00"), (None, "—")],
    )
    def test_time(self, seconds, expected):
        assert fmt_time(seconds) == expected

    @pytest.mark.parametrize(
        "pace,expected", [(203.4, "3:23/km"), (300, "5:00/km"), (0, "—"), (None, "—")]
    )
    def test_pace(self, pace, expected):
        assert fmt_pace(pace) == expected

    def test_pace_range_puts_the_faster_bound_first(self):
        assert fmt_pace_range(207, 203) == "3:23–3:27/km"

    @pytest.mark.parametrize(
        "meters,expected", [(400, "400 m"), (5000, "5 km"), (12340, "12,3 km"), (None, "—")]
    )
    def test_distance(self, meters, expected):
        assert fmt_distance(meters) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [("17:20", 1040), ("1:02:05", 3725), ("16:59", 1019), ("", None), ("abc", None)],
    )
    def test_parse_time(self, text, expected):
        assert parse_time(text) == expected

    def test_parse_and_format_round_trip(self):
        assert fmt_time(parse_time("16:59")) == "16:59"

    @pytest.mark.parametrize(
        "measured,expected", [(397, 400), (1004, 1000), (1520, 1500), (2390, 2400)]
    )
    def test_snap_distance(self, measured, expected):
        assert snap_distance(measured) == expected

    def test_odd_distances_are_not_forced_onto_a_canonical_one(self):
        assert snap_distance(730) == 750

    def test_spanish_day_names(self):
        assert fmt_day_long(date(2026, 7, 28)) == "martes 28 de julio"


class TestStravaMapping:
    def _payload(self) -> dict:
        return {
            "id": 987654321,
            "name": "Series 5 × 1000",
            "start_date_local": "2026-07-21T07:12:00Z",
            "start_date": "2026-07-21T10:12:00Z",
            "distance": 12400.0,
            "moving_time": 3300,
            "elapsed_time": 3400,
            "total_elevation_gain": 42.0,
            "average_heartrate": 158.2,
            "max_heartrate": 189.0,
            "average_cadence": 88.5,
            "sport_type": "Run",
            "workout_type": 3,
            "splits_metric": [
                {"distance": 1000, "moving_time": 240, "elapsed_time": 241, "average_heartrate": 150}
            ],
        }

    def test_activity_is_mapped(self):
        activity = activity_from_strava(self._payload())
        assert activity.id == "987654321"
        assert activity.distance_m == 12400.0
        assert activity.source == "strava"
        assert activity.start_date == datetime(2026, 7, 21, 7, 12)
        assert len(activity.splits_km) == 1

    def test_cadence_is_doubled_to_both_legs(self):
        """Strava reports one leg; runners count both."""
        assert activity_from_strava(self._payload()).average_cadence == pytest.approx(177.0)

    def test_laps_are_attached_when_provided(self):
        laps = [
            {"distance": 1000, "moving_time": 205, "average_heartrate": 178, "total_elevation_gain": 2}
            for _ in range(5)
        ]
        activity = activity_from_strava(self._payload(), laps)
        assert len(activity.laps) == 5
        assert activity.laps[0].pace_s_km == pytest.approx(205)

    def test_missing_optional_fields_are_tolerated(self):
        minimal = {
            "id": 1,
            "name": "Rodaje",
            "start_date": "2026-07-21T10:12:00Z",
            "distance": 10000,
            "moving_time": 2900,
        }
        activity = activity_from_strava(minimal)
        assert activity.average_heartrate is None
        assert activity.elevation_gain_m == 0

    def test_only_runs_are_imported(self):
        assert is_run({"sport_type": "Run"})
        assert is_run({"type": "TrailRun"})
        assert not is_run({"sport_type": "Ride"})

    def test_authorize_url_requests_the_right_scope(self):
        url = authorize_url("12345", "http://localhost:8501")
        assert "client_id=12345" in url
        assert "activity%3Aread_all" in url
        assert "response_type=code" in url


class TestSerialisation:
    def test_activity_round_trips(self):
        activity = continuous_activity(10000, 285, name="Rodaje")
        restored = Activity.from_dict(json.loads(json.dumps(activity.to_dict())))
        assert restored.id == activity.id
        assert restored.start_date == activity.start_date
        assert len(restored.splits_km) == len(activity.splits_km)
        assert restored.pace_s_km == pytest.approx(activity.pace_s_km)

    def test_app_state_round_trips(self):
        state = AppState()
        state.goals = [Goal.new("5K", 5000, date(2026, 9, 8), target_time_s=1019)]
        state.feedback = {"a1": Feedback("a1", rpe=8, legs=3, niggle="Aquiles", niggle_severity=2)}
        state.habits = {date(2026, 7, 27): HabitDay(date(2026, 7, 27), sleep_hours=7.5)}
        state.plan_overrides = {
            "2026-07-28": PlannedSession(
                id="x", day=date(2026, 7, 28), workout_type=WorkoutType.EASY,
                title="Rodaje", structure="10 km", purpose="Volumen",
            )
        }

        restored = AppState.from_dict(json.loads(json.dumps(state.to_dict())))
        assert restored.goals[0].target_time_s == 1019
        assert restored.feedback["a1"].niggle == "Aquiles"
        assert restored.habits[date(2026, 7, 27)].sleep_hours == 7.5
        assert restored.plan_overrides["2026-07-28"].workout_type is WorkoutType.EASY

    def test_unknown_fields_are_ignored(self):
        """A newer file must not break an older build."""
        data = continuous_activity(10000, 285).to_dict()
        data["some_future_field"] = 42
        assert Activity.from_dict(data).distance_m == 10000

    def test_merge_prefers_the_incoming_activity(self):
        old = continuous_activity(10000, 285, name="Rodaje")
        new = continuous_activity(10000, 285, name="Rodaje")
        new.name = "Rodaje con vueltas"
        merged = merge_activities([old], [new])
        assert len(merged) == 1
        assert merged[0].name == "Rodaje con vueltas"

    def test_merge_sorts_by_date(self):
        first = continuous_activity(8000, 290, name="A", when=datetime(2026, 7, 1))
        second = continuous_activity(8000, 290, name="B", when=datetime(2026, 7, 5))
        merged = merge_activities([second], [first])
        assert [a.name for a in merged] == ["A", "B"]


class TestPrimaryGoal:
    def test_the_a_race_is_chosen_by_default(self):
        state = AppState()
        state.goals = [
            Goal.new("C", 2400, date.today() + timedelta(days=10), priority="C"),
            Goal.new("A", 5000, date.today() + timedelta(days=40), priority="A"),
        ]
        assert state.primary_goal().name == "A"

    def test_an_explicit_choice_wins(self):
        state = AppState()
        chosen = Goal.new("C", 2400, date.today() + timedelta(days=10), priority="C")
        state.goals = [chosen, Goal.new("A", 5000, date.today() + timedelta(days=40))]
        state.primary_goal_id = chosen.id
        assert state.primary_goal().id == chosen.id

    def test_no_goals_returns_none(self):
        assert AppState().primary_goal() is None


@pytest.fixture(scope="module")
def dashboard(demo):
    state = AppState()
    state.goals = demo["goals"]
    state.feedback = demo["feedback"]
    state.habits = demo["habits"]
    state.profile = demo["profile"]
    return build_dashboard(demo["activities"], state)


@pytest.fixture(scope="module")
def context(dashboard):
    primary = dashboard.primary
    return CoachContext(
        zones=dashboard.zones,
        readiness=dashboard.readiness,
        load=dashboard.load,
        goal=primary.goal,
        prediction=primary.prediction,
        race_readiness=primary.readiness,
        recommendation=dashboard.recommendation,
        week=dashboard.current_week,
        recent=dashboard.recent_analyses(10),
        weekly_km=[week.km for week in dashboard.weeks],
    )


class TestEngine:
    def test_the_dashboard_is_fully_populated(self, dashboard, demo):
        assert len(dashboard.analyses) == len(demo["activities"])
        assert dashboard.goals and dashboard.plan
        assert dashboard.recommendation is not None
        assert dashboard.weeks
        assert dashboard.load.series

    def test_the_primary_goal_leads(self, dashboard):
        assert dashboard.primary.goal.priority == "A"

    def test_every_goal_gets_a_prediction_and_a_readiness(self, dashboard):
        for view in dashboard.goals:
            assert view.prediction.central_s > 0
            assert 0 <= view.readiness.overall <= 100

    def test_the_current_week_is_this_week(self, dashboard):
        week = dashboard.current_week
        assert week is not None
        assert week.start <= date.today() < week.start + timedelta(days=7)

    def test_analysis_lookup_by_id(self, dashboard, demo):
        target = demo["activities"][-1]
        assert dashboard.analysis_for(target.id).activity.id == target.id
        assert dashboard.analysis_for("nope") is None

    def test_milestones_only_celebrate_quality_sessions(self, dashboard):
        """A 10/10 easy run means the athlete jogged correctly, not a milestone."""
        for milestone in dashboard.milestones:
            assert "Rodaje" not in milestone.headline

    def test_an_empty_history_does_not_crash(self):
        dashboard = build_dashboard([], AppState())
        assert dashboard.analyses == []
        assert dashboard.zones.vdot > 0


class TestCoachFallback:
    def test_capability_question_answers_with_a_real_time(self, context):
        answer = fallback_answer("¿Estoy para correr 2400 m debajo de 8 minutos?", context)
        assert "2400" in answer
        assert ":" in answer  # it quotes an actual time
        assert "8:00" in answer or "objetivo" in answer

    def test_tomorrow_question_names_the_session(self, context):
        answer = fallback_answer("¿Qué hago mañana después de este entrenamiento?", context)
        assert context.recommendation.session.title in answer

    def test_recovery_question_picks_a_side(self, context):
        answer = fallback_answer("¿Descanso 90 segundos o 2 minutos?", context)
        assert "90" in answer or "120" in answer

    def test_easy_pace_question_uses_the_athletes_own_runs(self, context):
        answer = fallback_answer("¿Estoy entrenando demasiado rápido los rodajes?", context)
        assert "/km" in answer
        assert answer.startswith("Sí") or answer.startswith("No")

    def test_strategy_question_returns_splits(self, context):
        answer = fallback_answer("¿Cómo debería correr el próximo 5K?", context)
        assert "Parciales" in answer or "ritmo" in answer.lower()

    def test_comparison_question_uses_a_real_comparison(self, context):
        answer = fallback_answer("¿Este entrenamiento fue mejor que el del mes pasado?", context)
        assert answer

    def test_an_unrecognised_question_still_says_something_useful(self, context):
        answer = fallback_answer("¿Cuál es el sentido de la vida?", context)
        assert context.readiness.summary in answer

    def test_the_brief_carries_the_numbers_the_model_needs(self, context):
        brief = context.brief()
        for expected in ("VDOT", "Ritmos de entrenamiento", "Estado de hoy", "Preparación", "Objetivo principal"):
            assert expected in brief
