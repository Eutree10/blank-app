# PROJECT CONTEXT — Sub-17 5k Training App

> **Purpose of this file:** a complete handoff so any future chat session (which starts fresh from a
> clone of this repo) can pick up exactly where we left off. Read this first.

---

## 1. What this project is

An **interactive Streamlit app** + written plan that coaches a 15-year-old runner toward a
**sub-17:00 5k before the end of 2026**. Built from the athlete's real race PBs and Garmin lifestyle
data (no raw `.fit` file was ever provided — everything is derived from the numbers below).

**Repo:** `eutree10/blank-app`
**Working branch:** `claude/5k-training-plan-2026-AmKJF`
**Open PR:** #1 (draft) — https://github.com/Eutree10/blank-app/pull/1

### Files
| File | What it is |
|---|---|
| `streamlit_app.py` | The app (5 tabs). ~310 lines. Pure Streamlit, no external services. |
| `TRAINING_PLAN.md` | Full written coaching plan (the source of truth for the analysis). |
| `requirements.txt` | Just `streamlit`. |
| `README.md` | How to run/deploy. |
| `PROJECT_CONTEXT.md` | This handoff file. |

---

## 2. Athlete profile (all confirmed data)

| Field | Value |
|---|---|
| Age | 15 |
| Weight / height | 65 kg / 170 cm (BMI ~22.5) |
| Started running | April 2023 |
| 5k PB | **18:00.3** (3:36/km) — the valid benchmark |
| 2.1 mi PB | 3:23/km (~11:26) → Riegel-predicts a 17:19 5k |
| 10k | 38:40 — **DISCOUNTED** (run in 95% humidity + rain; not valid fitness data) |
| Resting HR | 53 bpm |
| Max HR | 197 (hit in 5k; matches age-predicted 197.5 → genuine max) |
| Easy-run HR | 130–155 bpm (confirmed genuinely easy — a strength) |
| Weekly volume | 45–55 km |
| Hard days | **Tuesday + Thursday only** (group sessions) |
| Sleep | ~8.5 h (excellent) |
| Injuries | None |
| Goal | **Sub-17:00 5k (3:24/km) before end of 2026** — needs ~61 s / 5.6% improvement |

### The two group sessions (key analysis input)
- **Tuesday:** 1k · 800 · 600 · 3×400, **4 min rest** each = 3,600 m of work, near-full recovery → VO₂max/speed (1500–3k specific).
- **Thursday:** **16 × 300 @ 3:03/km** (≈55 s), 1:30 jog, **4 min rest every 4 reps** = 4,800 m at ~mile pace → pure speed.
- **Total ≈ 8,400 m/week run faster than 5k pace, and essentially 0 m of threshold work.**

---

## 3. The diagnosis (final, round 3)

**A well-rounded, well-trained 18:00 runner with no glaring weakness in the valid data.**
- Easy days genuinely easy (130–155 bpm) ✅
- Intensity count correct (2 quality days, ~80/20) ✅
- Volume sound (45–55 km) ✅
- 15 y/o, early training age → natural improvement on his side ✅

**The ONE clear lever:** both group sessions are short fast reps faster than 5k pace; he does **zero
threshold**. Adding a threshold gear (~3:48/km, 175–180 bpm) is the highest-leverage change for sub-17.

> **History of the diagnosis (so we don't relitigate it):** Early drafts wrongly concluded "endurance
> weakness" from a slow 10k and "too much hard work" from 3–4 hard days. Both were corrected once the
> athlete clarified: only 2 hard days, easy runs at 130–155, and the 10k was in 95% humidity + rain.
> The current diagnosis above is the correct, final one.

---

## 4. Recommended change + plan

**Keep Thursday's 16×300 (good speed session). Make Tuesday a threshold day.** Three options offered,
in order of effectiveness:
1. **(Best)** Do a real threshold workout Tuesday — e.g. 5 × 1 km @ 3:48/km, 75 s jog (solo or ask coach).
2. Keep both group days; add 15–20 min @ 3:50/km to the end of the Sunday long run every other week.
3. Run the Tuesday ladder at controlled 3k effort (~3:12/km) instead of all-out.

**⏳ OPEN DECISION — athlete has NOT yet chosen between options 1/2/3.** The June calendar in the app
is currently built around **Option 1**. Once he picks, lock the calendar and extend through July.

### Training paces (at current 18:00 fitness — recalc as he improves)
- Easy: 4:40–5:10/km (≤160 bpm) · Long run: 4:40–5:00/km (≤165 bpm)
- Threshold: 3:45–3:52/km (175–180 bpm) ← the missing gear
- VO₂max: 3:15–3:25/km (181–190 bpm) · 5k goal pace: 3:24/km

### HR zones (Karvonen, RHR 53 / max 197)
Easy 139–160 · Steady 161–174 · Threshold 175–180 · VO₂max 181–190 · Max 190–197.

### Macrocycle (Jun→Dec 2026)
Base (Jun) → Threshold (Jul–Aug) → VO₂max+5k-specific (Sep–Oct) → Sharpen+tune-up races (Nov) →
Taper + **sub-17 attempt early–mid Dec** (cool weather) + backup race ~2 weeks later.

---

## 5. The app (`streamlit_app.py`) — structure

5 tabs:
1. **📊 Assessment** — metrics, narrative diagnosis, Riegel table (10k struck through).
2. **🧮 Paces & HR** — *live calculator*: input current 5k + RHR/max → recomputes all paces + Karvonen zones + predicted race times.
3. **🎯 Your sessions** — Tue/Thu analysis + the 3 recommended options.
4. **🗓️ June plan** — 4-week calendar (down week in week 4), built on Option 1.
5. **🥗 Fuel & recovery** — nutrition (carbs, protein 1.4–1.6 g/kg, iron/ferritin, don't chase weight/RED-S), recovery, red flags.

Key helper functions: `fmt()`, `fmt_long()`, `riegel()`. Athlete defaults in the `ATHLETE` dict and `GOAL_5K`.

---

## 6. How to run / deploy

**Local:** `pip install -r requirements.txt` then `streamlit run streamlit_app.py` → http://localhost:8501
**Deploy (free, public URL):** share.streamlit.io → sign in with GitHub → Create app →
repo `eutree10/blank-app`, branch `claude/5k-training-plan-2026-AmKJF`, file `streamlit_app.py` → Deploy.

> **Note:** the Claude sandbox cannot open a browser on the user's machine and cannot reach the user's
> `localhost`. It also (in at least one session) could not download a headless browser to screenshot.
> So the user must run/deploy the app themselves. Guide them to share.streamlit.io.

---

## 7. Open threads / next steps

- [ ] **Athlete to choose Option 1 / 2 / 3** for the Tuesday threshold change.
- [ ] Extend the calendar beyond June (July threshold block) once option chosen.
- [ ] Consider adding a **progress-tracker tab** (log runs, watch predicted 5k drop toward 17:00) — offered, not yet built.
- [ ] Suggest a **baseline ferritin blood test** (teen endurance runner — cheap insurance; not urgent).
- [ ] A **cool-weather 10k or hard tempo** would give a real endurance data point (the humid 10k is unusable).

---

## 8. Important guardrails (medical / age)

- 15 y/o and growing: hold volume 45–55 km, ≤10%/week build, down week every 4th week, strength work, protect 8.5 h sleep.
- **Do not chase weight** — 65 kg is healthy; under-fuelling (RED-S) is the main risk to a teen runner.
- This is a coaching framework, **not medical advice**; defer to a doctor, especially as the athlete is a minor.
