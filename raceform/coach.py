"""The AI coach.

Two halves. `build_context` compresses the athlete's whole history into a
compact brief — the part that makes answers specific rather than generic. The
answering layer uses Claude when an API key is configured, and otherwise falls
back to a deterministic responder that handles the questions runners actually
ask. The fallback is not a stub: it reads the same context object.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from datetime import date
from typing import Any

from .analysis.capability import RaceReadiness
from .analysis.load import LoadState, Readiness
from .analysis.physiology import PaceZones, time_for_distance
from .analysis.plan import PlanWeek, Recommendation
from .analysis.predict import Prediction
from .analysis.session import SessionAnalysis
from .formats import fmt_num, fmt_pace, fmt_pace_range, fmt_time
from .models import Capability, Goal, WorkoutType

MODEL = "claude-sonnet-5"
MAX_TOKENS = 900


@dataclass
class CoachContext:
    """Everything the coach knows, in a form both Claude and the fallback read."""

    zones: PaceZones
    readiness: Readiness
    load: LoadState
    goal: Goal | None
    prediction: Prediction | None
    race_readiness: RaceReadiness | None
    recommendation: Recommendation | None
    week: PlanWeek | None
    recent: list[SessionAnalysis]
    weekly_km: list[float]

    def brief(self) -> str:
        """The context block handed to the model. Kept dense on purpose."""
        lines: list[str] = []
        zones = self.zones
        lines.append(f"VDOT actual estimado: {fmt_num(zones.vdot, 1)}")
        lines.append(
            "Ritmos de entrenamiento — "
            f"fácil {fmt_pace_range(*zones.easy)}; "
            f"maratón {fmt_pace_range(*zones.marathon)}; "
            f"umbral {fmt_pace_range(*zones.threshold)}; "
            f"intervalos {fmt_pace_range(*zones.interval)}; "
            f"repeticiones {fmt_pace_range(*zones.repetition)}"
        )
        lines.append(
            f"Estado de hoy: {self.readiness.state} ({self.readiness.score}/100). "
            f"{self.readiness.summary} Motivos: {'; '.join(self.readiness.drivers)}"
        )
        lines.append(
            f"Carga: forma {self.load.fitness:.0f}, fatiga {self.load.fatigue:.0f}, "
            f"balance {self.load.form:+.0f}, ratio agudo/crónico {self.load.acwr():.2f}"
        )
        if self.weekly_km:
            recent = ", ".join(f"{km:.0f}" for km in self.weekly_km[-6:])
            lines.append(f"Kilometraje de las últimas semanas: {recent} km")

        if self.goal and self.prediction:
            lines.append(
                f"Objetivo principal: {self.goal.name} ({self.goal.distance_m:.0f} m) "
                f"el {self.goal.race_date.strftime('%d/%m/%Y')}, en {self.goal.days_left} días. "
                f"Marca objetivo {fmt_time(self.goal.target_time_s)}. "
                f"Predicción actual {fmt_time(self.prediction.low_s)}–{fmt_time(self.prediction.high_s)} "
                f"(central {fmt_time(self.prediction.central_s)}, confianza {self.prediction.confidence:.0%})."
            )
        if self.race_readiness:
            scores = ", ".join(
                f"{score.capability.value} {score.score}%" for score in self.race_readiness.capabilities
            )
            lines.append(f"Preparación {self.race_readiness.overall}% — {scores}")
            lines.append(f"Limitación principal: {self.race_readiness.limiter.capability.value}. "
                         f"{self.race_readiness.limiter.gap or self.race_readiness.limiter.detail}")

        if self.recommendation:
            session = self.recommendation.session
            lines.append(
                f"Sesión recomendada para hoy: {session.title} — "
                f"{session.structure.replace(chr(10), ' · ')}. Motivo: {self.recommendation.reason}"
            )
        if self.week:
            plan = "; ".join(
                f"{session.day.strftime('%a %d/%m')} {session.title}" for session in self.week.sessions
            )
            lines.append(f"Semana en curso ({self.week.theme}): {plan}")

        if self.recent:
            lines.append("Últimas sesiones analizadas:")
            for analysis in self.recent[:8]:
                lines.append(
                    f"  - {analysis.activity.day.strftime('%d/%m')} {analysis.headline} "
                    f"[{analysis.workout_type.value}] {analysis.verdict} {analysis.comparison}".strip()
                )
        return "\n".join(lines)


SYSTEM_PROMPT = """Sos el entrenador personal de un corredor dentro de la app Raceform.

Reglas:
- Respondé SIEMPRE con los datos concretos del corredor que aparecen en el contexto. Nada de consejos genéricos.
- Citá números reales (ritmos, fechas, porcentajes) cuando respalden lo que decís.
- Español rioplatense, tuteo con "vos". Directo y breve: 2 a 5 frases, sin listas largas salvo que pidan un entrenamiento.
- Si el dato necesario no está en el contexto, decilo con claridad en vez de inventarlo.
- No diagnostiques lesiones ni des indicaciones médicas: ante dolor persistente, sugerí consultar a un profesional.
- Nunca contradigas los números del contexto. Si el corredor cree algo que los datos no respaldan, mostrale el dato.
"""


def _api_key() -> str | None:
    from .config import secret

    return secret("ANTHROPIC_API_KEY")


def coach_available() -> bool:
    if not _api_key():
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def ask(question: str, context: CoachContext, history: list[dict[str, str]] | None = None) -> str:
    """Answer a question. Uses Claude when configured, the fallback otherwise."""
    if not coach_available():
        return fallback_answer(question, context)
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=_api_key())
        messages: list[dict[str, Any]] = []
        for turn in (history or [])[-6:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append(
            {
                "role": "user",
                "content": f"<contexto_del_corredor>\n{context.brief()}\n</contexto_del_corredor>\n\n{question}",
            }
        )
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()
    except Exception as error:  # the coach must never take the app down
        return (
            f"No pude consultar al entrenador de IA ({type(error).__name__}). "
            f"Respuesta con los datos locales:\n\n{fallback_answer(question, context)}"
        )


# --- deterministic fallback --------------------------------------------------

_INTENTS: list[tuple[str, re.Pattern[str]]] = [
    ("capacidad", re.compile(r"\b(estoy para|puedo (correr|bajar)|llego a|me da para|debajo de)\b", re.I)),
    ("mañana", re.compile(r"\b(mañana|qué hago|que hago|próxima sesión|proxima sesion|después de)\b", re.I)),
    ("recuperacion", re.compile(r"\b(descanso|recupero|recuperación|recuperacion|\d+\s*(s|seg|segundos|min|minutos))\b", re.I)),
    ("rodajes", re.compile(r"\b(rodaje|rodajes|suave|fácil|facil|demasiado rápido|demasiado rapido)\b", re.I)),
    ("estrategia", re.compile(r"\b(cómo (debería|deberia) correr|estrategia|parciales|salir|ritmo de carrera)\b", re.I)),
    ("comparacion", re.compile(r"\b(mejor que|peor que|comparad|mes pasado|comparación|comparacion)\b", re.I)),
    ("parcial", re.compile(r"\b(por qué|por que).*(lento|rápido|rapido|kilómetro|kilometro|parcial|repetición|repeticion)\b", re.I)),
    ("prediccion", re.compile(r"\b(predicción|prediccion|cuánto|cuanto).*(voy|corro|puedo)|\bpara cuánto\b", re.I)),
]


def _intent(question: str) -> str:
    for name, pattern in _INTENTS:
        if pattern.search(question):
            return name
    return "general"


def _parse_target_distance(question: str, context: CoachContext) -> float | None:
    """Pull a distance out of the question: '2400 m', '5k', '1500'."""
    match = re.search(r"(\d{3,5})\s*(m\b|metros)", question, re.I)
    if match:
        return float(match.group(1))
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*k(m|ilómetros|ilometros)?\b", question, re.I)
    if match:
        return float(match.group(1).replace(",", ".")) * 1000
    return None


def _parse_target_time(question: str) -> float | None:
    match = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", question)
    if match:
        parts = [int(part) for part in match.groups() if part is not None]
        seconds = 0
        for part in parts:
            seconds = seconds * 60 + part
        return float(seconds)
    match = re.search(r"(?:debajo de|bajo|menos de|sub)\s*(\d{1,2})\s*(?:minutos|min)\b", question, re.I)
    if match:
        return float(match.group(1)) * 60
    return None


def fallback_answer(question: str, context: CoachContext) -> str:
    """Answer from the context alone. Deterministic, and always data-anchored."""
    intent = _intent(question)
    zones = context.zones

    if intent == "capacidad":
        distance = _parse_target_distance(question, context)
        target = _parse_target_time(question)
        if distance:
            equivalent = time_for_distance(distance, zones.vdot)
            line = (
                f"Con tu nivel actual (VDOT {fmt_num(zones.vdot, 1)}), "
                f"{fmt_num(distance, 0)} m te dan {fmt_time(equivalent)} "
                f"a {fmt_pace(equivalent / (distance / 1000))}."
            )
            if target:
                margin = equivalent - target
                if margin <= 0:
                    line += f" Tu objetivo de {fmt_time(target)} está dentro de lo que ya podés hacer, con {fmt_time(abs(margin))} de margen."
                elif margin < 12:
                    line += f" Tu objetivo de {fmt_time(target)} está a {fmt_time(margin)}: es alcanzable en las próximas semanas."
                else:
                    line += f" Tu objetivo de {fmt_time(target)} pide {fmt_time(margin)} más: todavía no está."
            if context.race_readiness:
                line += f" La limitación a trabajar es {context.race_readiness.limiter.capability.value.lower()}."
            return line
        if context.prediction and context.goal:
            return (
                f"Para {context.goal.name} la predicción actual es "
                f"{fmt_time(context.prediction.low_s)}–{fmt_time(context.prediction.high_s)}. "
                f"{context.prediction.basis}"
            )

    if intent == "mañana":
        if context.recommendation:
            session = context.recommendation.session
            answer = (
                f"Hoy toca {session.title}: {session.structure.replace(chr(10), ', ')}. "
                f"{context.recommendation.reason}"
            )
            if context.week:
                following = [
                    entry for entry in context.week.sessions if entry.day > date.today()
                ]
                if following:
                    answer += f" Mañana: {following[0].title}."
            return answer

    if intent == "recuperacion":
        seconds = re.findall(r"(\d{2,3})\s*(?:s|seg|segundos)", question, re.I)
        minutes = re.findall(r"(\d)\s*(?:min|minutos)", question, re.I)
        options = [int(value) for value in seconds] + [int(value) * 60 for value in minutes]
        if context.race_readiness:
            limiter = context.race_readiness.limiter.capability
            if limiter is Capability.SPECIFIC_ENDURANCE and options:
                return (
                    f"Quedate con la recuperación más corta ({min(options)} s). "
                    f"Tu limitación es resistencia específica: recuperar menos obliga a sostener el "
                    f"ritmo con fatiga, que es exactamente lo que te falta."
                )
            if limiter is Capability.SPEED and options:
                return (
                    f"Usá la más larga ({max(options)} s). Estás trabajando velocidad, y la "
                    f"calidad de cada repetición importa más que la densidad de la sesión."
                )
        if options:
            return (
                f"Con tu estado de hoy ({context.readiness.state}), elegí {max(options)} s: "
                "priorizá la calidad de cada repetición."
            )

    if intent == "rodajes":
        easy_sessions = [
            analysis for analysis in context.recent
            if analysis.workout_type is WorkoutType.EASY
        ]
        if easy_sessions:
            mean_pace = statistics.mean(analysis.activity.pace_s_km for analysis in easy_sessions)
            easy_fast, easy_slow = zones.easy
            if mean_pace < easy_fast:
                return (
                    f"Sí. Tus últimos {len(easy_sessions)} rodajes promedian {fmt_pace(mean_pace)} "
                    f"y tu rango fácil es {fmt_pace_range(easy_fast, easy_slow)}. "
                    "Estás sumando fatiga en los días que deberían dejarte fresco."
                )
            return (
                f"No. Tus últimos {len(easy_sessions)} rodajes promedian {fmt_pace(mean_pace)}, "
                f"dentro del rango fácil ({fmt_pace_range(easy_fast, easy_slow)}). Está bien así."
            )

    if intent == "estrategia" and context.goal and context.prediction:
        from .analysis.capability import cumulative_splits, race_strategy

        if context.race_readiness:
            splits, note = race_strategy(context.goal, context.prediction.central_s, context.race_readiness)
            preview = ", ".join(
                f"{label} {fmt_time(elapsed)}" for label, _, elapsed in cumulative_splits(splits)[:3]
            )
            return f"{note} Parciales de referencia: {preview}…"

    if intent == "comparacion" and context.recent:
        with_comparison = [analysis for analysis in context.recent if analysis.comparison]
        if with_comparison:
            analysis = with_comparison[0]
            return (
                f"{analysis.headline} ({analysis.activity.day.strftime('%d/%m')}): "
                f"{analysis.comparison} {analysis.verdict}"
            )

    if intent == "parcial" and context.recent:
        analysis = context.recent[0]
        return f"{analysis.headline}. {analysis.verdict} {analysis.advice}"

    if intent == "prediccion" and context.prediction and context.goal:
        return (
            f"Para {context.goal.name}: {fmt_time(context.prediction.low_s)}–"
            f"{fmt_time(context.prediction.high_s)} "
            f"(confianza {context.prediction.confidence:.0%}). {context.prediction.basis}"
        )

    # Nothing matched: give the state of play rather than a non-answer.
    parts = [context.readiness.summary]
    if context.recommendation:
        parts.append(f"Hoy: {context.recommendation.session.title}.")
    if context.race_readiness and context.goal:
        parts.append(
            f"Para {context.goal.name} estás al {context.race_readiness.overall}% "
            f"y la limitación es {context.race_readiness.limiter.capability.value.lower()}."
        )
    parts.append(
        "Configurá ANTHROPIC_API_KEY para conversar con el entrenador de IA sobre cualquier tema."
        if not coach_available() else ""
    )
    return " ".join(part for part in parts if part)


SUGGESTED_QUESTIONS = [
    "¿Estoy para correr 2400 m debajo de 8 minutos?",
    "¿Qué hago mañana después de este entrenamiento?",
    "¿Descanso 90 segundos o 2 minutos?",
    "¿Estoy entrenando demasiado rápido los rodajes?",
    "¿Cómo debería correr el próximo 5K?",
    "¿Este entrenamiento fue mejor que el del mes pasado?",
]
