"""Strava import.

OAuth authorisation-code flow plus the three endpoints the app needs:
athlete, activity list, and per-activity laps. Tokens are refreshed
transparently. Nothing here writes to Strava — Raceform is read-only against
the athlete's data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlencode

import requests

if TYPE_CHECKING:  # imported lazily at runtime to keep this module standalone
    from .models import Activity, Lap

API_BASE = "https://www.strava.com/api/v3"
AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
SCOPE = "read,activity:read_all"

REQUEST_TIMEOUT = 20


class StravaError(RuntimeError):
    """Any failure talking to Strava, with a message safe to show a user."""


@dataclass
class Tokens:
    access_token: str
    refresh_token: str
    expires_at: int  # unix seconds
    athlete_id: int | None = None

    @property
    def expired(self) -> bool:
        return time.time() > self.expires_at - 120  # refresh a little early

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tokens":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def authorize_url(client_id: str, redirect_uri: str, state: str = "raceform") -> str:
    """Where to send the athlete to grant access."""
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": SCOPE,
            "state": state,
        }
    )
    return f"{AUTH_URL}?{query}"


def exchange_code(client_id: str, client_secret: str, code: str) -> Tokens:
    """Trade the one-time code from the redirect for tokens."""
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=REQUEST_TIMEOUT,
    )
    payload = _json_or_raise(response, "No se pudo completar la autorización con Strava")
    return Tokens(
        access_token=payload["access_token"],
        refresh_token=payload["refresh_token"],
        expires_at=payload["expires_at"],
        athlete_id=(payload.get("athlete") or {}).get("id"),
    )


def refresh(client_id: str, client_secret: str, tokens: Tokens) -> Tokens:
    """Swap the refresh token for a fresh access token."""
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": tokens.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=REQUEST_TIMEOUT,
    )
    payload = _json_or_raise(response, "La sesión de Strava expiró y no se pudo renovar")
    return Tokens(
        access_token=payload["access_token"],
        refresh_token=payload["refresh_token"],
        expires_at=payload["expires_at"],
        athlete_id=tokens.athlete_id,
    )


def _json_or_raise(response: requests.Response, context: str) -> dict[str, Any]:
    if response.status_code == 429:
        raise StravaError(
            "Strava limitó temporalmente las consultas (límite de 100 cada 15 minutos). "
            "Probá de nuevo en unos minutos."
        )
    if not response.ok:
        detail = ""
        try:
            body = response.json()
            detail = body.get("message") or ""
            errors = body.get("errors") or []
            if errors:
                detail += f" ({errors[0].get('field', '')}: {errors[0].get('code', '')})"
        except ValueError:
            detail = response.text[:200]
        raise StravaError(f"{context}: {response.status_code} {detail}".strip())
    try:
        return response.json()
    except ValueError as error:
        raise StravaError(f"{context}: respuesta inesperada de Strava") from error


class StravaClient:
    """Authenticated client. Refreshes tokens on demand via `on_refresh`."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tokens: Tokens,
        on_refresh: Callable[[Tokens], None] | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens = tokens
        self.on_refresh = on_refresh

    def _headers(self) -> dict[str, str]:
        if self.tokens.expired:
            self.tokens = refresh(self.client_id, self.client_secret, self.tokens)
            if self.on_refresh:
                self.on_refresh(self.tokens)
        return {"Authorization": f"Bearer {self.tokens.access_token}"}

    def _get(self, path: str, **params: Any) -> Any:
        response = requests.get(
            f"{API_BASE}{path}", headers=self._headers(), params=params, timeout=REQUEST_TIMEOUT
        )
        return _json_or_raise(response, f"Error consultando {path}")

    def athlete(self) -> dict[str, Any]:
        return self._get("/athlete")

    def activities(self, after: datetime | None = None, limit: int = 200) -> list[dict[str, Any]]:
        """Recent runs, newest first, paging until `limit` or exhaustion."""
        collected: list[dict[str, Any]] = []
        page = 1
        while len(collected) < limit:
            params: dict[str, Any] = {"per_page": min(100, limit - len(collected)), "page": page}
            if after:
                params["after"] = int(after.replace(tzinfo=timezone.utc).timestamp())
            batch = self._get("/athlete/activities", **params)
            if not batch:
                break
            collected.extend(batch)
            if len(batch) < params["per_page"]:
                break
            page += 1
        return collected

    def laps(self, activity_id: int) -> list[dict[str, Any]]:
        return self._get(f"/activities/{activity_id}/laps")

    def activity_detail(self, activity_id: int) -> dict[str, Any]:
        return self._get(f"/activities/{activity_id}", include_all_efforts=False)


# --- mapping into the domain model ------------------------------------------

def _parse_dt(value: str) -> datetime:
    """Strava returns ISO 8601 with a trailing Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def lap_from_strava(payload: dict[str, Any], index: int) -> "Lap":
    from .models import Lap

    return Lap(
        index=index,
        distance_m=float(payload.get("distance") or 0),
        moving_time_s=float(payload.get("moving_time") or 0),
        elapsed_time_s=float(payload.get("elapsed_time") or 0),
        average_heartrate=payload.get("average_heartrate"),
        max_heartrate=payload.get("max_heartrate"),
        elevation_gain_m=float(payload.get("total_elevation_gain") or 0),
        average_cadence=payload.get("average_cadence"),
        name=payload.get("name") or "",
    )


def activity_from_strava(
    payload: dict[str, Any],
    laps: list[dict[str, Any]] | None = None,
) -> "Activity":
    """Map one Strava activity (plus optional laps) onto the domain model."""
    from .models import Activity

    splits = [
        lap_from_strava(split, index)
        for index, split in enumerate(payload.get("splits_metric") or [])
    ]
    lap_objects = [lap_from_strava(lap, index) for index, lap in enumerate(laps or [])]

    cadence = payload.get("average_cadence")
    return Activity(
        id=str(payload["id"]),
        name=payload.get("name") or "Actividad",
        start_date=_parse_dt(payload.get("start_date_local") or payload["start_date"]),
        distance_m=float(payload.get("distance") or 0),
        moving_time_s=float(payload.get("moving_time") or 0),
        elapsed_time_s=float(payload.get("elapsed_time") or 0),
        elevation_gain_m=float(payload.get("total_elevation_gain") or 0),
        average_heartrate=payload.get("average_heartrate"),
        max_heartrate=payload.get("max_heartrate"),
        # Strava reports running cadence as one leg; runners think in both.
        average_cadence=cadence * 2 if cadence else None,
        average_watts=payload.get("average_watts"),
        laps=lap_objects,
        splits_km=splits,
        sport=payload.get("sport_type") or payload.get("type") or "Run",
        strava_workout_type=payload.get("workout_type"),
        source="strava",
        description=payload.get("description") or "",
    )


def is_run(payload: dict[str, Any]) -> bool:
    return (payload.get("sport_type") or payload.get("type") or "") in {
        "Run", "TrailRun", "VirtualRun", "Track",
    }


def import_activities(
    client: StravaClient,
    after: datetime | None = None,
    limit: int = 120,
    fetch_laps: bool = True,
    progress: Callable[[int, int], None] | None = None,
) -> list["Activity"]:
    """Import runs, fetching laps only where they can carry structure.

    Laps cost one API call each against a 100-per-15-minute limit, so they are
    only fetched for activities long enough to plausibly contain a workout.
    """
    raw = [payload for payload in client.activities(after=after, limit=limit) if is_run(payload)]
    activities: list["Activity"] = []

    lap_budget = 60 if fetch_laps else 0
    for position, payload in enumerate(raw):
        laps = None
        if lap_budget > 0 and (payload.get("moving_time") or 0) > 900:
            try:
                laps = client.laps(int(payload["id"]))
                lap_budget -= 1
            except StravaError:
                laps = None  # a missing lap list is not worth failing the import
        activities.append(activity_from_strava(payload, laps))
        if progress:
            progress(position + 1, len(raw))

    activities.sort(key=lambda activity: activity.start_date)
    return activities
