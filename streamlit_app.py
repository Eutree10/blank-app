"""Sub-17 5k Training Plan — interactive coaching app.

A personalized plan for a 15 y/o runner targeting a sub-17:00 5k by end of 2026.
Built from race PBs + Garmin lifestyle data. See TRAINING_PLAN.md for the full write-up.
"""

import streamlit as st

st.set_page_config(page_title="Sub-17 5k Plan", page_icon="🏃", layout="wide")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt(seconds: float) -> str:
    """Seconds -> M:SS (per-km pace or short times)."""
    seconds = round(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def fmt_long(seconds: float) -> str:
    """Seconds -> M:SS for race times."""
    seconds = round(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def riegel(t_sec: float, d_from: float, d_to: float, exp: float = 1.06) -> float:
    """Predict race time over d_to (km) from a time over d_from (km)."""
    return t_sec * (d_to / d_from) ** exp


# ---------------------------------------------------------------------------
# Athlete profile (defaults from the user's data)
# ---------------------------------------------------------------------------
ATHLETE = {
    "age": 15,
    "weight": 65,
    "height": 170,
    "pb_5k": 18 * 60 + 0.3,   # 18:00.3
    "rhr": 53,
    "hrmax": 197,
    "weekly_km": "45–55",
    "easy_hr": "130–155",
}
GOAL_5K = 17 * 60  # 16:59 target -> 3:24/km

st.title("🏃 Sub-17 5k — Personal Training Plan")
st.caption(
    "15 y/o · 65 kg · 170 cm · 5k PB 18:00 · resting HR 53 · max HR 197 · "
    "**Goal: sub-17:00 (3:24/km) before the end of 2026**"
)

tab_overview, tab_calc, tab_sessions, tab_calendar, tab_lifestyle = st.tabs(
    ["📊 Assessment", "🧮 Paces & HR", "🎯 Your sessions", "🗓️ June plan", "🥗 Fuel & recovery"]
)

# ===========================================================================
# TAB 1 — ASSESSMENT
# ===========================================================================
with tab_overview:
    st.header("Honest assessment")

    c1, c2, c3 = st.columns(3)
    gap = ATHLETE["pb_5k"] - GOAL_5K
    c1.metric("Current 5k PB", "18:00", "benchmark")
    c2.metric("Goal", "16:59", f"-{round(gap)}s to go")
    c3.metric("Improvement needed", "5.6%", "over ~7 months")

    st.markdown(
        """
**You're a well-rounded, well-trained 18:00 runner with no glaring weakness in the data.**
- Easy days are genuinely easy (130–155 bpm) — most runners fail here; you've nailed it.
- Intensity count is right: 2 quality days/week on 45–55 km (~80/20).
- You're 15 and early in your training age, so natural improvement is on your side.

**The one clear lever:** both your group sessions are short, fast reps run *faster than 5k pace*.
You bank ~8,400 m/week of speed work and **essentially zero threshold**. Adding the threshold gear
is the highest-leverage change for sub-17 — see the **Your sessions** tab.
        """
    )

    st.subheader("Race-equivalent check (Riegel)")
    pb = ATHLETE["pb_5k"]
    d_21 = 2.1 * 1.609344
    t_21 = (3 * 60 + 23) * d_21
    rows = [
        ("5k race", "18:00.3", "3:36/km", "— benchmark", True),
        ("2.1 mi PB", fmt_long(t_21), "3:23/km", f"predicts {fmt_long(riegel(t_21, d_21, 5))} 5k", True),
        ("10k (95% humidity + rain)", "38:40", "3:52/km", "❌ discounted — conditions, not fitness", False),
        ("Goal", "16:59", "3:24/km", "— target", True),
    ]
    st.table(
        {
            "Performance": [r[0] for r in rows],
            "Time": [r[1] for r in rows],
            "Pace": [r[2] for r in rows],
            "Note": [r[3] for r in rows],
        }
    )
    st.info(
        "The 10k was run in 95% humidity + rain, which routinely costs 30–90+ s over 10k. "
        "It is **not** evidence of an endurance weakness, so it's excluded from the analysis."
    )

# ===========================================================================
# TAB 2 — PACES & HR CALCULATOR
# ===========================================================================
with tab_calc:
    st.header("Training paces & HR zones")
    st.write("Adjust these as you get fitter — re-enter your current 5k and everything recalculates.")

    colA, colB = st.columns(2)
    with colA:
        st.subheader("Current 5k time")
        mins = st.number_input("Minutes", 14, 25, 18, key="m5k")
        secs = st.number_input("Seconds", 0, 59, 0, key="s5k")
    with colB:
        st.subheader("Heart rate")
        rhr = st.number_input("Resting HR", 35, 90, ATHLETE["rhr"])
        hrmax = st.number_input("Max HR", 170, 220, ATHLETE["hrmax"])

    t5k = mins * 60 + secs
    pace5k = t5k / 5  # sec/km

    # Daniels-style training paces relative to current 5k pace (sec/km offsets)
    paces = {
        "Easy / recovery": (pace5k + 64, pace5k + 94),
        "Long run": (pace5k + 64, pace5k + 84),
        "Threshold (tempo)": (pace5k + 9, pace5k + 16),
        "5k goal pace": (GOAL_5K / 5, GOAL_5K / 5),
        "VO₂max (intervals)": (pace5k - 21, pace5k - 11),
        "Reps / strides": (pace5k - 35, pace5k - 25),
    }

    st.subheader("Paces (per km)")
    st.table(
        {
            "Zone": list(paces),
            "Pace range": [
                fmt(lo) if lo == hi else f"{fmt(lo)} – {fmt(hi)}" for lo, hi in paces.values()
            ],
        }
    )

    # Karvonen HR zones
    hrr = hrmax - rhr

    def zone(lo, hi):
        return f"{round(rhr + lo * hrr)} – {round(rhr + hi * hrr)} bpm"

    st.subheader("Heart-rate zones (Karvonen)")
    st.table(
        {
            "Zone": ["Easy / recovery", "Steady aerobic", "Threshold", "VO₂max", "Max"],
            "Heart rate": [
                zone(0.60, 0.74),
                zone(0.75, 0.84),
                zone(0.85, 0.88),
                zone(0.89, 0.95),
                zone(0.95, 1.00),
            ],
        }
    )
    st.success(
        f"Your easy runs at **{ATHLETE['easy_hr']} bpm** sit right in the easy zone — keep them there. "
        "That discipline is what makes the two hard days work."
    )

    with st.expander("Predicted race times at this fitness"):
        st.table(
            {
                "Distance": ["1500 m", "3 km", "5 km", "10 km"],
                "Predicted": [
                    fmt_long(riegel(t5k, 5, 1.5)),
                    fmt_long(riegel(t5k, 5, 3)),
                    fmt_long(t5k),
                    fmt_long(riegel(t5k, 5, 10)),
                ],
            }
        )

# ===========================================================================
# TAB 3 — SESSION ANALYSIS
# ===========================================================================
with tab_sessions:
    st.header("Your group sessions — analysed")

    st.markdown(
        """
| Day | What the group does | What it trains | Verdict |
|---|---|---|---|
| **Tue** | 1k · 800 · 600 · 3×400, **4 min rest** | VO₂max / speed (1500–3k specific) | Run faster than 5k pace, near-full recovery |
| **Thu** | **16 × 300 @ 3:03/km** (55 s), 1:30 jog, 4 min every 4 | Pure speed (~mile pace) | Great for top-end, but more speed |

**Total: ~8,400 m/week faster than 5k pace, and ~0 m of threshold.**
        """
    )
    st.warning(
        "You have plenty of speed (your 2.1-mile PB proves it). The missing gear is **threshold** — "
        "sustained 'comfortably hard' running at ~3:48/km (175–180 bpm) that builds your ability to "
        "hold pace for the full 5 km."
    )

    st.subheader("The recommended change")
    st.markdown(
        """
Keep **Thursday's 16×300** — it's a strong speed/economy session. Make **Tuesday your threshold day**.
How to fit it depends on your club:

1. **Best:** do a threshold workout on Tuesday (solo, or ask the coach — many will let you run tempo
   while the group does the ladder). e.g. **5 × 1 km @ 3:48/km, 75 s jog**.
2. **Keep both group days:** then inject threshold by finishing your **Sunday long run** with
   **15–20 min @ 3:50/km** every other week.
3. **Compromise:** run the Tuesday ladder at controlled **3 k effort (~3:12/km)** rather than all-out,
   so it leans more aerobic.

> Option 1 gets you to sub-17 fastest. Tell me which fits your club and I'll lock the calendar to it.
        """
    )

# ===========================================================================
# TAB 4 — JUNE CALENDAR
# ===========================================================================
with tab_calendar:
    st.header("June 2026 — week by week")
    st.caption(
        "Phase: aerobic base + introduce threshold. Volume ~50–55 km. "
        "Easy ≤160 bpm · Threshold 175–180 · Long run ≤165. Down week in week 4."
    )

    weeks = {
        "Week 1 · Jun 1–7": {
            "Tue (KEY threshold)": "4 × 1 km @ 3:50, 75 s jog  (or group ladder @ 3 k effort)",
            "Thu (KEY speed)": "16 × 300 @ 3:05–3:08, 1:30 jog, 4 min every 4",
            "Long run (Sun)": "12 km easy (≤165)",
        },
        "Week 2 · Jun 8–14": {
            "Tue (KEY threshold)": "5 × 1 km @ 3:48, 75 s jog",
            "Thu (KEY speed)": "16 × 300 @ 3:03–3:06, 1:30 jog, 4 min every 4",
            "Long run (Sun)": "13 km easy",
        },
        "Week 3 · Jun 15–21": {
            "Tue (KEY threshold)": "2 × 2 km @ 3:50 + 1 × 1 km @ 3:45, 2–2.5 min jog",
            "Thu (KEY speed)": "16 × 300 @ 3:03, 1:30 jog, 4 min every 4",
            "Long run (Sun)": "15 km easy",
        },
        "Week 4 · Jun 22–28 (DOWN)": {
            "Tue (KEY threshold)": "3 × 1 km @ 3:50, 90 s jog",
            "Thu (KEY speed)": "10 × 300 @ 3:05, 1:30 jog",
            "Long run (Sun)": "11 km easy",
        },
    }

    for wk, sessions in weeks.items():
        with st.expander(wk, expanded=wk.startswith("Week 1")):
            st.markdown(
                "**Mon** easy 6 km + 6×20 s strides &nbsp;·&nbsp; **Wed** easy 6–7 km "
                "&nbsp;·&nbsp; **Fri** rest or easy 4 km &nbsp;·&nbsp; **Sat** easy 6 km + strides"
            )
            st.divider()
            for day, work in sessions.items():
                st.markdown(f"- **{day}:** {work}")
            st.caption("All key sessions: 2–3 km warm-up + drills/strides before, 1–2 km cool-down after.")

    st.info(
        "Every key session: warm up 2–3 km easy + a few strides, cool down 1–2 km. "
        "Never two hard days back-to-back beyond Tue/Thu; if a session feels off, swap it for easy."
    )

# ===========================================================================
# TAB 5 — LIFESTYLE
# ===========================================================================
with tab_lifestyle:
    st.header("Fuel, recovery & red flags")

    st.subheader("Nutrition (15 y/o endurance athlete)")
    st.markdown(
        """
- **Don't chase weight** — 65 kg is a healthy racing weight. Under-fuelling (RED-S) stalls growth and performance.
- **Carbs are your main fuel** — base meals on rice, pasta, oats, potatoes, bread, fruit. Refuel within ~60 min of key sessions.
- **Protein** ~1.4–1.6 g/kg/day (~90–105 g) spread across the day.
- **Iron** — teen runners are highest-risk for low ferritin (mimics bad fitness). Iron-rich foods + vitamin C; consider a baseline **ferritin blood test** (via a doctor).
- **Calcium + vitamin D** for growing, loading bones.
        """
    )

    st.subheader("Recovery & monitoring")
    st.markdown(
        """
- **Sleep 8.5 h is excellent — protect it.** It's where adaptation happens at 15.
- Track **morning resting HR** (baseline 53). A sustained rise of ~7+ bpm = back off.
- Keep easy days genuinely easy (≤160 bpm). The talk test is your guide.
        """
    )

    st.subheader("Red flags")
    st.markdown(
        """
1. **No raw Garmin export** was parsed — this is built from your race PBs + numbers. Re-test paces as you improve.
2. **The humidity 10k is unusable** — for a real endurance read, race a 10k or hard tempo in cool conditions.
3. **Baseline ferritin test** is cheap insurance for a teen distance runner.
4. **You're 15 and growing** — hold volume at 45–55 km, take down weeks, do strength work. Durability first.
        """
    )

st.divider()
st.caption(
    "Coaching framework, not medical advice. Check with a doctor before ramping training or blood "
    "testing (you're a minor). Full write-up in TRAINING_PLAN.md."
)
