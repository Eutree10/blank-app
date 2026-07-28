"""One computation pass.

Every screen reads from the same `Dashboard`, so the number shown on Hoy is
by construction the number behind Carreras. Building it is a single function
call, which also makes the whole app testable without Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .analysis.capability import RaceReadiness, assess_readiness
from .analysis.insights import Insight, Milestone, collect_insights, detect_milestones
from .analysis.load import (
    LoadState,
    Readiness,
    WeekSummary,
    build_load_state,
    compute_readiness,
    weekly_summaries,
)
from .analysis.physiology import PaceZones, zones_for
from .analysis.plan import PlanWeek, Recommendation, build_plan, recommend_today
from .analysis.predict import Prediction, current_vdot, predict_race
from .analysis.session import SessionAnalysis, analyze_session
from .models import Activity, Capability, Goal, week_start
from .store import AppState


@dataclass
class GoalView:
    """A goal with everything derived from it."""

    goal: Goal
    readiness: RaceReadiness
    prediction: Prediction


@dataclass
class Dashboard:
    activities: list[Activity]
    zones: PaceZones
    load: LoadState
    readiness: Readiness
    weeks: list[WeekSummary]
    analyses: list[SessionAnalysis]
    goals: list[GoalView] = field(default_factory=list)
    plan: list[PlanWeek] = field(default_factory=list)
    recommendation: Recommendation | None = None
    insights: list[Insight] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)

    @property
    def primary(self) -> GoalView | None:
        return self.goals[0] if self.goals else None

    @property
    def current_week(self) -> PlanWeek | None:
        today = date.today()
        for week in self.plan:
            if week.start <= today < week.start + timedelta(days=7):
                return week
        return self.plan[0] if self.plan else None

    def analysis_for(self, activity_id: str) -> SessionAnalysis | None:
        for analysis in self.analyses:
            if analysis.activity.id == activity_id:
                return analysis
        return None

    def recent_analyses(self, count: int = 12) -> list[SessionAnalysis]:
        return list(reversed(self.analyses[-count:]))

    @property
    def form_ratio(self) -> float:
        return self.load.form / max(self.load.fitness, 1.0)


def _mean_recent_km(weeks: list[WeekSummary]) -> float:
    """Average of the last four *complete* weeks — the in-progress one lies."""
    if not weeks:
        return 40.0
    complete = [week for week in weeks if week.start < week_start(date.today())]
    pool = complete[-4:] or weeks[-1:]
    return sum(week.km for week in pool) / len(pool)


def build_dashboard(activities: list[Activity], state: AppState) -> Dashboard:
    """Everything, from a list of runs and the athlete's own inputs."""
    activities = sorted(activities, key=lambda activity: activity.start_date)
    vdot = current_vdot(activities) if activities else 45.0
    zones = zones_for(vdot)

    load = build_load_state(activities, zones)
    readiness = compute_readiness(load, activities, state.feedback, state.habits)
    weeks = weekly_summaries(activities, zones, weeks=18)

    analyses: list[SessionAnalysis] = []
    for activity in activities:
        analyses.append(
            analyze_session(
                activity,
                zones,
                feedback=state.feedback.get(activity.id),
                planned=None,
                history=analyses,
                hr_rest=state.profile.hr_rest,
                hr_max=state.profile.hr_max,
            )
        )

    form_ratio = load.form / max(load.fitness, 1.0)
    primary = state.primary_goal()
    ordered_goals = sorted(
        state.goals,
        key=lambda goal: (goal.id != (primary.id if primary else None), goal.priority, goal.days_left),
    )

    goal_views: list[GoalView] = []
    for goal in ordered_goals:
        race_readiness = assess_readiness(goal, activities, zones, state.feedback, form_ratio)
        prediction = predict_race(
            goal,
            activities,
            zones,
            form_ratio,
            race_readiness.by(Capability.SPECIFIC_ENDURANCE).score,
        )
        goal_views.append(GoalView(goal=goal, readiness=race_readiness, prediction=prediction))

    plan: list[PlanWeek] = []
    recommendation: Recommendation | None = None
    if goal_views:
        top = goal_views[0]
        weekly_km = _mean_recent_km(weeks)
        plan = build_plan(
            top.goal,
            zones,
            state.profile,
            top.readiness,
            current_weekly_km=weekly_km,
            weeks=max(1, min(8, (top.goal.days_left // 7) + 1)),
        )
        plan = [_apply_overrides(week, state) for week in plan]
        current = next(
            (week for week in plan if week.start <= date.today() < week.start + timedelta(days=7)),
            plan[0] if plan else None,
        )
        if current:
            recommendation = recommend_today(current, readiness, top.readiness, zones)

    insights = collect_insights(activities, analyses, state.feedback, state.habits, zones)
    milestones = detect_milestones(analyses)

    return Dashboard(
        activities=activities,
        zones=zones,
        load=load,
        readiness=readiness,
        weeks=weeks,
        analyses=analyses,
        goals=goal_views,
        plan=plan,
        recommendation=recommendation,
        insights=insights,
        milestones=milestones,
    )


def _apply_overrides(week: PlanWeek, state: AppState) -> PlanWeek:
    """Re-apply the athlete's manual edits on top of the regenerated plan."""
    if not state.plan_overrides:
        return week
    sessions = []
    for session in week.sessions:
        override = state.plan_overrides.get(session.day.isoformat())
        sessions.append(override if override else session)
    week.sessions = sessions
    return week
