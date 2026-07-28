"""Shared UI pieces used by more than one screen."""

from __future__ import annotations

import streamlit as st

from ..analysis.session import SessionAnalysis
from ..formats import fmt_num, fmt_pace
from ..models import Feedback
from ..store import AppState, save_state
from . import theme

# One source of truth for the family colours, shared with the chips.
WORKOUT_ACCENT = theme.WORKOUT_COLORS


def session_teaser(analysis: SessionAnalysis, show_score: bool = True) -> None:
    """A one-line summary card for a session."""
    accent = WORKOUT_ACCENT.get(analysis.workout_type.value, theme.MUTED)
    score_html = (
        f'<div class="rf-value" style="font-size:1.15rem;color:{theme.score_color(analysis.score * 10)}">'
        f"{fmt_num(analysis.score, 1)}<span style=\"font-size:.72rem;color:{theme.FAINT}\">/10</span></div>"
        if show_score
        else ""
    )
    theme.card(
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:.8rem">'
        f'<div style="flex:1">'
        f'<div style="font-size:.68rem;font-weight:620;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{accent}">{analysis.workout_type.value}</div>'
        f'<div style="font-size:1.02rem;font-weight:600;color:{theme.INK};margin-top:.15rem;'
        f'letter-spacing:-.02em">{analysis.title}</div>'
        f'<div class="rf-muted" style="margin-top:.3rem">'
        f'{analysis.activity.start_date.strftime("%d/%m")} · {fmt_num(analysis.activity.km, 1)} km · '
        f'{fmt_pace(analysis.activity.pace_s_km)}</div>'
        f"</div>{score_html}</div>"
    )


def feedback_form(activity_id: str, state: AppState, key: str = "feedback") -> bool:
    """The three post-session questions. Returns True when submitted."""
    existing = state.feedback.get(activity_id)
    with st.form(f"{key}_{activity_id}"):
        rpe = st.select_slider(
            "Esfuerzo percibido",
            options=list(range(1, 11)),
            value=existing.rpe if existing and existing.rpe else 6,
            format_func=lambda value: f"{value}",
        )
        legs = st.select_slider(
            "Sensación de piernas",
            options=[1, 2, 3, 4, 5],
            value=existing.legs if existing and existing.legs else 3,
            format_func=lambda value: {
                1: "Muertas", 2: "Pesadas", 3: "Normales", 4: "Buenas", 5: "Con resorte",
            }[value],
        )
        niggle = st.text_input(
            "Molestias",
            value=existing.niggle if existing else "",
            placeholder="Ninguna",
        )
        if st.form_submit_button("Guardar", type="primary", use_container_width=True):
            state.feedback[activity_id] = Feedback(
                activity_id=activity_id,
                rpe=rpe,
                legs=legs,
                niggle=niggle.strip(),
                niggle_severity=2 if niggle.strip() else 0,
            )
            save_state(state)
            st.toast("Registrado.")
            st.rerun()
    return False


def metric_rows(metrics: dict[str, str], limit: int | None = None) -> None:
    items = list(metrics.items())
    if limit:
        items = items[:limit]
    theme.card(theme.rows_html(items))


def empty_state(title: str, body: str, action_label: str = "", key: str = "") -> bool:
    theme.card(
        f'<div style="font-size:1rem;font-weight:600;color:{theme.INK};margin-bottom:.35rem">{title}</div>'
        f'<div class="rf-muted">{body}</div>'
    )
    if action_label:
        return st.button(action_label, type="primary", use_container_width=True, key=key or action_label)
    return False


def explanation(text: str) -> None:
    """The sentence that must accompany every chart."""
    st.markdown(
        f'<div class="rf-muted" style="margin:-.35rem 0 1.1rem 0">{text}</div>',
        unsafe_allow_html=True,
    )
