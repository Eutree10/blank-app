"""Perfil — connection, athlete settings, habits and the data behind it all."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import streamlit as st

from ...coach import coach_available
from ...engine import Dashboard
from ...formats import fmt_num, fmt_pace_range
from ...models import HabitDay
from ...store import AppState, clear_all, merge_activities, save_activities, save_state
from .. import theme


def render(dashboard: Dashboard, state: AppState) -> None:
    theme.screen_header("Perfil", state.profile.name)

    _connection(state)
    _zones(dashboard)
    _habits(dashboard, state)
    _settings(state)
    _data(state)


def _connection(state: AppState) -> None:
    from ...config import strava_credentials
    from ...strava import StravaError, authorize_url, exchange_code

    client_id, client_secret, redirect = strava_credentials()
    connected = bool(state.tokens)

    theme.eyebrow("Strava")
    if connected:
        theme.card(
            f'<div class="rf-note">Conectado{" · atleta " + str(state.tokens.get("athlete_id")) if state.tokens.get("athlete_id") else ""}. '
            "Las actividades se importan con sus parciales y vueltas.</div>"
        )
    elif not (client_id and client_secret):
        theme.card(
            '<div class="rf-note">Para conectar Strava agregá tus credenciales de aplicación '
            "en <code>.streamlit/secrets.toml</code>:</div>"
            '<div class="rf-muted" style="margin-top:.5rem;font-family:monospace;font-size:.76rem">'
            'STRAVA_CLIENT_ID = "…"<br/>STRAVA_CLIENT_SECRET = "…"<br/>'
            'STRAVA_REDIRECT_URI = "http://localhost:8501"</div>'
            '<div class="rf-muted" style="margin-top:.5rem">Mientras tanto estás viendo un '
            "atleta de demostración con 18 semanas de entrenamiento real simulado.</div>"
        )
        return
    else:
        url = authorize_url(str(client_id), str(redirect))
        st.link_button("Conectar con Strava", url, type="primary", use_container_width=True)

    # Complete the OAuth round trip when Strava sends the athlete back.
    code = st.query_params.get("code")
    if code and not connected and client_id and client_secret:
        try:
            tokens = exchange_code(str(client_id), str(client_secret), code)
            state.tokens = tokens.to_dict()
            state.profile.strava_athlete_id = tokens.athlete_id
            save_state(state)
            st.query_params.clear()
            st.toast("Strava conectado.")
            st.rerun()
        except StravaError as error:
            st.error(str(error))

    if connected and client_id and client_secret:
        if st.button("Importar actividades", type="primary", use_container_width=True):
            _import(state, str(client_id), str(client_secret))
        if st.button("Desconectar", use_container_width=True):
            state.tokens = None
            save_state(state)
            st.rerun()


def _import(state: AppState, client_id: str, client_secret: str) -> None:
    from ...strava import StravaClient, StravaError, Tokens, import_activities
    from ...store import load_activities

    def remember(tokens: Tokens) -> None:
        state.tokens = tokens.to_dict()
        save_state(state)

    progress = st.progress(0.0, "Consultando Strava…")
    try:
        client = StravaClient(client_id, client_secret, Tokens.from_dict(state.tokens or {}), remember)
        imported = import_activities(
            client,
            after=datetime.now() - timedelta(days=180),
            limit=150,
            progress=lambda done, total: progress.progress(
                done / max(total, 1), f"Importando {done} de {total}…"
            ),
        )
    except StravaError as error:
        progress.empty()
        st.error(str(error))
        return

    merged = merge_activities(load_activities(), imported)
    save_activities(merged)
    progress.empty()
    st.session_state.pop("dashboard", None)
    st.session_state.use_demo = False
    st.toast(f"{len(imported)} actividades importadas.")
    st.rerun()


def _zones(dashboard: Dashboard) -> None:
    zones = dashboard.zones
    theme.eyebrow("Tus ritmos actuales")
    theme.card(
        theme.rows_html(
            [
                ("Nivel estimado (VDOT)", fmt_num(zones.vdot, 1)),
                ("Fácil", fmt_pace_range(*zones.easy)),
                ("Maratón", fmt_pace_range(*zones.marathon)),
                ("Umbral", fmt_pace_range(*zones.threshold)),
                ("Intervalos", fmt_pace_range(*zones.interval)),
                ("Repeticiones", fmt_pace_range(*zones.repetition)),
            ]
        )
        + '<div class="rf-muted" style="margin-top:.6rem">Se recalculan solos con cada '
        "sesión de calidad. No hace falta configurarlos.</div>"
    )


def _habits(dashboard: Dashboard, state: AppState) -> None:
    theme.eyebrow("Hábitos y recuperación")

    if dashboard.insights:
        for insight in dashboard.insights[:2]:
            theme.card(
                f'<div class="rf-note">{insight.headline}</div>'
                f'<div class="rf-muted" style="margin-top:.3rem">{insight.detail} '
                f"· relación {insight.strength}</div>",
                accent=True,
            )
    else:
        theme.card(
            '<div class="rf-muted">Todavía no hay suficientes datos para relacionar tus '
            "hábitos con el rendimiento. La app solo muestra relaciones que aparecen "
            "de verdad en tus sesiones.</div>"
        )

    today = date.today()
    existing = state.habits.get(today)
    with st.expander("Registrar el día de hoy"):
        with st.form("habits_form"):
            columns = st.columns(2)
            with columns[0]:
                sleep = st.number_input(
                    "Sueño (h)", min_value=0.0, max_value=14.0, step=0.5,
                    value=float(existing.sleep_hours) if existing and existing.sleep_hours else 7.5,
                )
            with columns[1]:
                hydration = st.select_slider(
                    "Hidratación", options=[1, 2, 3, 4, 5],
                    value=existing.hydration if existing and existing.hydration else 3,
                )
            columns = st.columns(2)
            with columns[0]:
                mobility = st.checkbox("Movilidad", value=existing.mobility if existing else False)
            with columns[1]:
                strength = st.checkbox("Fuerza", value=existing.strength if existing else False)
            columns = st.columns(2)
            with columns[0]:
                soreness = st.select_slider(
                    "Dolor muscular", options=[1, 2, 3, 4, 5],
                    value=existing.soreness if existing and existing.soreness else 2,
                )
            with columns[1]:
                fatigue = st.select_slider(
                    "Fatiga", options=[1, 2, 3, 4, 5],
                    value=existing.fatigue if existing and existing.fatigue else 2,
                )
            fueled = st.checkbox(
                "Comí antes de entrenar",
                value=existing.fueled_before if existing and existing.fueled_before is not None else True,
            )
            if st.form_submit_button("Guardar", type="primary", use_container_width=True):
                state.habits[today] = HabitDay(
                    day=today,
                    sleep_hours=sleep,
                    hydration=hydration,
                    mobility=mobility,
                    strength=strength,
                    fueled_before=fueled,
                    soreness=soreness,
                    fatigue=fatigue,
                )
                save_state(state)
                st.toast("Registrado.")
                st.rerun()


def _settings(state: AppState) -> None:
    with st.expander("Ajustes del atleta"):
        with st.form("profile_form"):
            name = st.text_input("Nombre", value=state.profile.name)
            columns = st.columns(2)
            with columns[0]:
                hr_max = st.number_input(
                    "FC máxima", min_value=0, max_value=230, value=int(state.profile.hr_max or 0)
                )
            with columns[1]:
                hr_rest = st.number_input(
                    "FC reposo", min_value=0, max_value=120, value=int(state.profile.hr_rest or 0)
                )
            columns = st.columns(2)
            with columns[0]:
                weekly = st.number_input(
                    "Volumen objetivo (km/sem)", min_value=10.0, max_value=250.0,
                    value=float(state.profile.weekly_km_target), step=5.0,
                )
            with columns[1]:
                days = st.number_input(
                    "Días por semana", min_value=3, max_value=7, value=int(state.profile.days_per_week)
                )
            if st.form_submit_button("Guardar", type="primary", use_container_width=True):
                state.profile.name = name
                state.profile.hr_max = int(hr_max) or None
                state.profile.hr_rest = int(hr_rest) or None
                state.profile.weekly_km_target = float(weekly)
                state.profile.days_per_week = int(days)
                save_state(state)
                st.toast("Ajustes guardados.")
                st.rerun()


def _data(state: AppState) -> None:
    with st.expander("Datos y entrenador de IA"):
        status = (
            "El entrenador de IA está activo."
            if coach_available()
            else "El entrenador responde con reglas sobre tus datos. Para conversación abierta, "
            "configurá <code>ANTHROPIC_API_KEY</code> en secrets o en el entorno."
        )
        st.markdown(f'<div class="rf-muted">{status}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:.7rem"></div>', unsafe_allow_html=True)

        demo = st.session_state.get("use_demo", True)
        if demo:
            st.markdown(
                '<div class="rf-muted">Estás viendo el atleta de demostración.</div>',
                unsafe_allow_html=True,
            )
        if st.button("Borrar todos mis datos locales", use_container_width=True):
            clear_all()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
