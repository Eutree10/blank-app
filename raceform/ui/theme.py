"""Visual system.

A warm off-white canvas, one orange accent reserved for the primary action and
the live state, and everything else on a neutral ramp. Data is set in a mono
face so digits align and stay scannable. Streamlit's chrome is stripped back so
the result reads as a native app rather than a dashboard.
"""

from __future__ import annotations

import streamlit as st

# Palette — warm light, one hue.
ACCENT = "#F2622A"
ACCENT_DARK = "#D44E1B"
ACCENT_SOFT = "#FDEDE4"
INK = "#111113"
BODY = "#2E2C2A"
MUTED = "#79746E"
FAINT = "#A8A29B"
LINE = "#EAE5DE"
SURFACE = "#FFFFFF"
CANVAS = "#FBF9F5"
DARK = "#141312"  # hero cards

# Semantic colours for data — deliberately not the brand accent.
GOOD = "#2E9E5B"
WARN = "#C98A12"
BAD = "#D0402F"
COOL = "#4A7CB8"

# Kept so older call sites keep working; the accent is no longer red.
RED = ACCENT
RED_DARK = ACCENT_DARK
RED_SOFT = ACCENT_SOFT

ZONE_COLORS = {
    "easy": "#8FB8DE",
    "marathon": "#5C9E6E",
    "threshold": "#D9A441",
    "interval": "#E2733A",
    "repetition": "#D0402F",
}

# One colour per workout family, used by the chips and the plan calendar.
WORKOUT_COLORS = {
    "rodaje": "#8FA6B5",
    "fondo": "#5C9E6E",
    "tempo": "#D9A441",
    "intervalos": "#E2733A",
    "repeticiones cortas": ACCENT,
    "cuestas": "#8C6BB1",
    "competencia": INK,
    "test": "#4A7CB8",
}

FONT_STACK = (
    "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', "
    "Inter, Roboto, Helvetica, Arial, sans-serif"
)
MONO_STACK = "'SF Mono', 'JetBrains Mono', 'Roboto Mono', ui-monospace, Menlo, Consolas, monospace"

NAV_ITEMS = [
    ("hoy", "Hoy", "home"),
    ("plan", "Plan", "calendar"),
    ("progreso", "Progreso", "chart"),
    ("carreras", "Carreras", "target"),
    ("perfil", "Perfil", "person"),
]
NAV_KEYS = [key for key, _, _ in NAV_ITEMS]


def score_color(score: float, best: float = 100, worst: float = 0) -> str:
    """Green / amber / red for a 0–100 style metric."""
    span = best - worst
    ratio = (score - worst) / span if span else 0.5
    if ratio >= 0.78:
        return GOOD
    if ratio >= 0.55:
        return WARN
    return BAD


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --rf-accent: {ACCENT};
            --rf-ink: {INK};
            --rf-body: {BODY};
            --rf-muted: {MUTED};
            --rf-line: {LINE};
            --rf-surface: {SURFACE};
            --rf-canvas: {CANVAS};
        }}

        .stApp {{
            background: {CANVAS};
            font-family: {FONT_STACK};
            color: {BODY};
        }}
        header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
        #MainMenu, footer {{ visibility: hidden; }}
        [data-testid="stSidebarCollapsedControl"] {{ display: none; }}

        .block-container {{
            padding: 1.5rem 1.15rem 8rem 1.15rem;
            max-width: 560px;
        }}

        h1, h2, h3, h4 {{
            font-family: {FONT_STACK};
            color: {INK};
            letter-spacing: -0.02em;
            font-weight: 640;
        }}

        /* --- screen header: large, tight display type --- */
        .rf-screen-title {{
            font-size: 2.35rem;
            font-weight: 700;
            letter-spacing: -0.045em;
            color: {INK};
            margin: 0 0 0.1rem 0;
            line-height: 1.02;
        }}
        .rf-screen-sub {{
            font-size: 0.88rem;
            color: {MUTED};
            margin: 0 0 1.4rem 0;
            letter-spacing: -0.005em;
        }}

        /* --- eyebrow labels --- */
        .rf-eyebrow {{
            font-size: 0.66rem;
            font-weight: 640;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {FAINT};
            margin: 0 0 0.5rem 0;
        }}

        /* --- the one card style --- */
        .rf-card {{
            background: {SURFACE};
            border: 1px solid {LINE};
            border-radius: 20px;
            padding: 1.15rem 1.2rem;
            margin-bottom: 0.8rem;
        }}
        .rf-card-accent {{
            border-left: 3px solid {ACCENT};
        }}
        /* Hero card: the one block per screen that carries the key number. */
        .rf-card-dark {{
            background: {DARK};
            border: none;
            color: #F4F1EC;
        }}
        .rf-card-dark .rf-eyebrow {{ color: #7C766E; }}
        .rf-card-dark .rf-hero, .rf-card-dark .rf-value {{ color: #FFFFFF; }}
        .rf-card-dark .rf-muted {{ color: #948D84; }}
        .rf-card-dark .rf-note {{ color: #E4DFD8; }}
        .rf-card-dark .rf-row {{ border-bottom-color: #2A2724; }}
        .rf-card-dark .rf-row-key {{ color: #948D84; }}
        .rf-card-dark .rf-row-val {{ color: #FFFFFF; }}

        /* --- the headline number on a screen --- */
        .rf-hero {{
            font-family: {MONO_STACK};
            font-size: 3rem;
            font-weight: 640;
            color: {INK};
            letter-spacing: -0.055em;
            line-height: 1;
            font-variant-numeric: tabular-nums;
        }}
        /* Uppercase micro-label that sits under a big number. */
        .rf-microlabel {{
            font-size: 0.62rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: {FAINT};
            margin-top: 0.2rem;
        }}
        .rf-hero-unit {{
            font-family: {FONT_STACK};
            font-size: 0.95rem;
            font-weight: 520;
            color: {MUTED};
            letter-spacing: -0.01em;
        }}

        .rf-value {{
            font-family: {MONO_STACK};
            font-variant-numeric: tabular-nums;
            font-weight: 560;
            color: {INK};
            letter-spacing: -0.02em;
        }}

        /* --- key/value rows --- */
        .rf-row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            padding: 0.5rem 0;
            border-bottom: 1px solid {LINE};
            gap: 1rem;
        }}
        .rf-row:last-child {{ border-bottom: none; }}
        .rf-row-key {{ font-size: 0.855rem; color: {MUTED}; }}
        .rf-row-val {{
            font-family: {MONO_STACK};
            font-variant-numeric: tabular-nums;
            font-size: 0.9rem;
            font-weight: 560;
            color: {INK};
            text-align: right;
        }}

        /* --- capability meters --- */
        .rf-meter-track {{
            height: 5px;
            background: #EEEEEB;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 0.35rem;
        }}
        .rf-meter-fill {{ height: 100%; border-radius: 3px; }}

        /* --- state pill --- */
        .rf-pill {{
            display: inline-block;
            padding: 0.2rem 0.62rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }}

        .rf-note {{
            font-size: 0.88rem;
            line-height: 1.5;
            color: {BODY};
        }}
        .rf-muted {{ color: {MUTED}; font-size: 0.82rem; line-height: 1.45; }}

        /* --- prescription block --- */
        .rf-prescription {{
            font-family: {MONO_STACK};
            font-size: 1.32rem;
            font-weight: 600;
            color: {INK};
            letter-spacing: -0.025em;
            line-height: 1.35;
            white-space: pre-line;
        }}

        /* --- buttons: one primary per screen --- */
        .stButton > button {{
            border-radius: 999px;
            border: 1px solid {LINE};
            background: {SURFACE};
            color: {INK};
            font-weight: 550;
            font-size: 0.875rem;
            padding: 0.58rem 1rem;
            transition: border-color 120ms ease, background 120ms ease;
        }}
        .stButton > button:hover {{
            border-color: {FAINT};
            background: {SURFACE};
            color: {INK};
        }}
        .stButton > button:focus:not(:active) {{
            border-color: {ACCENT};
            color: {INK};
            box-shadow: none;
        }}
        .stButton > button[kind="primary"] {{
            background: {ACCENT};
            border-color: {ACCENT};
            color: #FFFFFF;
            font-weight: 600;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {ACCENT_DARK};
            border-color: {ACCENT_DARK};
            color: #FFFFFF;
        }}

        /* --- bottom navigation: a floating pill, not a bar --- */
        .st-key-rf_nav {{
            position: fixed;
            bottom: 0.85rem;
            left: 50%;
            transform: translateX(-50%);
            width: min(94vw, 420px);
            z-index: 999;
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: saturate(180%) blur(18px);
            border: 1px solid {LINE};
            border-radius: 26px;
            box-shadow: 0 8px 28px rgba(30, 24, 16, 0.10),
                        0 2px 6px rgba(30, 24, 16, 0.05);
            padding: 0.5rem 0.55rem 0.45rem;
        }}
        /* The active destination gets a filled circle behind its icon. */
        .st-key-rf_nav .rf-nav-icon {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 34px;
            height: 34px;
            margin: 0 auto -0.1rem;
            border-radius: 50%;
            transition: background 140ms ease;
        }}
        .st-key-rf_nav .rf-nav-icon.rf-nav-on {{
            background: {ACCENT};
        }}
        .st-key-rf_nav [data-testid="stMarkdownContainer"] {{ line-height: 0; }}
        .st-key-rf_nav .stButton > button {{
            border: none;
            background: transparent;
            color: {FAINT};
            font-size: 0.7rem;
            font-weight: 560;
            padding: 0.1rem 0.1rem 0.15rem;
            width: 100%;
            letter-spacing: -0.01em;
            min-height: 0;
        }}
        .st-key-rf_nav [data-testid="stElementContainer"] {{ margin: 0; }}
        .st-key-rf_nav .stButton > button:hover {{
            background: transparent;
            color: {BODY};
        }}
        .st-key-rf_nav .stButton > button[kind="primary"] {{
            background: transparent;
            color: {ACCENT};
            font-weight: 650;
        }}
        .st-key-rf_nav .stButton > button[kind="primary"]:hover {{
            background: transparent;
            color: {ACCENT};
        }}
        /* Streamlit stacks columns on narrow viewports; a tab bar must not
           stack, and neither must the small inline button rows. */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: nowrap !important;
            gap: 0.5rem;
        }}
        [data-testid="stColumn"] {{
            min-width: 0 !important;
            flex: 1 1 0% !important;
        }}
        .st-key-rf_nav [data-testid="stHorizontalBlock"] {{ gap: 0.1rem; }}

        /* --- inputs --- */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {{
            border-radius: 10px;
            border-color: {LINE};
            font-size: 0.9rem;
        }}
        .stSelectbox div[data-baseweb="select"] > div {{
            border-radius: 10px;
            border-color: {LINE};
            font-size: 0.9rem;
        }}
        [data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] {{ color: {FAINT}; }}
        .stSlider [role="slider"] {{ background-color: {ACCENT} !important; }}

        [data-testid="stExpander"] {{
            border: 1px solid {LINE};
            border-radius: 12px;
            background: {SURFACE};
        }}
        [data-testid="stExpander"] summary {{ font-size: 0.86rem; font-weight: 560; }}

        [data-testid="stMetricValue"] {{
            font-family: {MONO_STACK};
            font-variant-numeric: tabular-nums;
            font-size: 1.5rem;
            color: {INK};
        }}
        [data-testid="stMetricLabel"] {{ color: {MUTED}; font-size: 0.78rem; }}

        div[data-testid="stChatInput"] textarea {{ font-size: 0.9rem; }}
        hr {{ border-color: {LINE}; margin: 1.1rem 0; }}

        /* --- tabs --- */
        .stTabs [data-baseweb="tab-list"] {{ gap: 1.15rem; border-bottom: 1px solid {LINE}; }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.85rem;
            font-weight: 560;
            color: {MUTED};
            padding: 0.35rem 0;
        }}
        .stTabs [aria-selected="true"] {{ color: {INK}; }}
        .stTabs [data-baseweb="tab-highlight"] {{ background-color: {ACCENT}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- small render helpers ----------------------------------------------------

def screen_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="rf-screen-title">{title}</div>'
        + (f'<div class="rf-screen-sub">{subtitle}</div>' if subtitle else '<div style="height:1rem"></div>'),
        unsafe_allow_html=True,
    )


def eyebrow(text: str) -> None:
    st.markdown(f'<div class="rf-eyebrow">{text}</div>', unsafe_allow_html=True)


def card(body_html: str, accent: bool = False, dark: bool = False) -> None:
    """The one card style. `dark` is the hero block — at most one per screen."""
    classes = "rf-card"
    if dark:
        classes += " rf-card-dark"
    elif accent:
        classes += " rf-card-accent"
    st.markdown(f'<div class="{classes}">{body_html}</div>', unsafe_allow_html=True)


def rows_html(pairs: list[tuple[str, str]]) -> str:
    return "".join(
        f'<div class="rf-row"><span class="rf-row-key">{key}</span>'
        f'<span class="rf-row-val">{value}</span></div>'
        for key, value in pairs
    )


def meter_html(label: str, value: int, color: str | None = None, caption: str = "") -> str:
    color = color or score_color(value)
    caption_html = f'<div class="rf-muted" style="margin-top:.3rem">{caption}</div>' if caption else ""
    return (
        f'<div style="margin-bottom:.85rem">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
        f'<span style="font-size:.87rem;color:{BODY};font-weight:520">{label}</span>'
        f'<span class="rf-value" style="font-size:.92rem">{value}%</span></div>'
        f'<div class="rf-meter-track"><div class="rf-meter-fill" '
        f'style="width:{max(2, min(100, value))}%;background:{color}"></div></div>'
        f"{caption_html}</div>"
    )


def pill(text: str, color: str = ACCENT, background: str = ACCENT_SOFT) -> str:
    return f'<span class="rf-pill" style="color:{color};background:{background}">{text}</span>'


def hero(value: str, unit: str = "", caption: str = "") -> str:
    unit_html = f' <span class="rf-hero-unit">{unit}</span>' if unit else ""
    caption_html = f'<div class="rf-muted" style="margin-top:.35rem">{caption}</div>' if caption else ""
    return f'<div class="rf-hero">{value}{unit_html}</div>{caption_html}'
