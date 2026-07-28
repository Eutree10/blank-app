"""The coach chat.

Deliberately not the home screen: it is where you go with a question, and it
already knows the answer to most of them because it reads the same dashboard
every other screen does.
"""

from __future__ import annotations

import streamlit as st

from ...coach import SUGGESTED_QUESTIONS, CoachContext, ask, coach_available
from ...engine import Dashboard
from ...store import AppState
from .. import theme


def build_context(dashboard: Dashboard) -> CoachContext:
    primary = dashboard.primary
    return CoachContext(
        zones=dashboard.zones,
        readiness=dashboard.readiness,
        load=dashboard.load,
        goal=primary.goal if primary else None,
        prediction=primary.prediction if primary else None,
        race_readiness=primary.readiness if primary else None,
        recommendation=dashboard.recommendation,
        week=dashboard.current_week,
        recent=dashboard.recent_analyses(10),
        weekly_km=[week.km for week in dashboard.weeks],
    )


def render(dashboard: Dashboard, state: AppState) -> None:
    theme.screen_header("Entrenador", "Conoce todo tu historial")

    if not coach_available():
        theme.card(
            '<div class="rf-muted">Sin <code>ANTHROPIC_API_KEY</code> configurada, el entrenador '
            "responde con reglas sobre tus datos reales. Las respuestas siguen siendo específicas, "
            "pero no conversacionales.</div>"
        )

    history = st.session_state.setdefault("coach_history", [])
    context = build_context(dashboard)

    if not history:
        theme.eyebrow("Preguntas frecuentes")
        for index, question in enumerate(SUGGESTED_QUESTIONS[:4]):
            if st.button(question, key=f"suggested_{index}", use_container_width=True):
                _answer(question, context, history)
                st.rerun()

    for turn in history:
        with st.chat_message("user" if turn["role"] == "user" else "assistant"):
            st.markdown(turn["content"])

    question = st.chat_input("Preguntale a tu entrenador…")
    if question:
        _answer(question, context, history)
        st.rerun()

    if history and st.button("Limpiar conversación", use_container_width=True):
        st.session_state.coach_history = []
        st.rerun()


def _answer(question: str, context: CoachContext, history: list[dict[str, str]]) -> None:
    history.append({"role": "user", "content": question})
    with st.spinner("Pensando…"):
        answer = ask(question, context, history[:-1])
    history.append({"role": "assistant", "content": answer})
    st.session_state.coach_history = history
