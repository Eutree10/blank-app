"""Raceform — turns your Strava activities into training decisions.

Run with:  streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from raceform.demo import build_demo_history
from raceform.engine import Dashboard, build_dashboard
from raceform.store import AppState, load_activities, load_state
from raceform.ui import theme, visuals
from raceform.ui.screens import coach_chat, plan, profile, progress, races, session, today

st.set_page_config(
    page_title="Raceform",
    page_icon="🏃",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SCREENS = {
    "hoy": today.render,
    "plan": plan.render,
    "progreso": progress.render,
    "carreras": races.render,
    "perfil": profile.render,
    "sesion": session.render,
    "entrenador": coach_chat.render,
}


def load_app_state() -> tuple[list, AppState, bool]:
    """Real data when it exists, the demo athlete otherwise."""
    state = load_state()
    activities = load_activities()
    using_demo = False

    if not activities:
        demo_activities, feedback, habits, goals, athlete = build_demo_history()
        activities = demo_activities
        using_demo = True
        # Only seed what the athlete has not already provided themselves.
        if not state.goals:
            state.goals = goals
        if not state.feedback:
            state.feedback = feedback
        if not state.habits:
            state.habits = habits
        if state.profile.hr_max is None:
            state.profile = athlete
    return activities, state, using_demo


@st.cache_data(show_spinner="Analizando tus entrenamientos…", max_entries=4)
def _cached_dashboard(activity_ids: tuple[str, ...], state_signature: str, _activities, _state):
    """Recompute only when the activities or the athlete's inputs change.

    The first two arguments are what the cache keys on; the leading-underscore
    ones carry the real objects past Streamlit's hashing.
    """
    return build_dashboard(_activities, _state)


def get_dashboard(activities: list, state: AppState) -> Dashboard:
    signature = repr(
        (
            sorted(state.feedback),
            len(state.habits),
            [goal.to_dict() for goal in state.goals],
            state.primary_goal_id,
            sorted(state.plan_overrides),
            state.profile.to_dict(),
        )
    )
    return _cached_dashboard(
        tuple(activity.id for activity in activities), signature, activities, state
    )


def bottom_nav(current: str) -> None:
    """Fixed tab bar: Hoy · Plan · Progreso · Carreras · Perfil."""
    with st.container(key="rf_nav"):
        columns = st.columns(len(theme.NAV_ITEMS))
        for column, (key, label, icon_name) in zip(columns, theme.NAV_ITEMS):
            with column:
                active = current == key
                st.markdown(
                    '<div class="rf-nav-icon">'
                    + visuals.icon(
                        icon_name,
                        size=19,
                        color=theme.RED if active else theme.FAINT,
                        stroke=1.9 if active else 1.6,
                    )
                    + "</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    label,
                    key=f"nav_{key}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                ):
                    st.session_state.screen = key
                    st.rerun()


def main() -> None:
    theme.inject_css()
    activities, state, using_demo = load_app_state()
    st.session_state.setdefault("use_demo", using_demo)
    st.session_state.setdefault("screen", "hoy")

    dashboard = get_dashboard(activities, state)
    screen = st.session_state.screen

    # An entry point to the coach, reachable from every screen.
    _, header_right = st.columns([3, 1.15])
    with header_right:
        if screen != "entrenador":
            if st.button("Entrenador", use_container_width=True, key="open_coach"):
                st.session_state.previous_screen = screen
                st.session_state.screen = "entrenador"
                st.rerun()
        elif st.button("‹ Volver", use_container_width=True, key="close_coach"):
            st.session_state.screen = st.session_state.get("previous_screen", "hoy")
            st.rerun()

    SCREENS.get(screen, today.render)(dashboard, state)
    bottom_nav(screen if screen in theme.NAV_KEYS else "")


if __name__ == "__main__":
    main()
