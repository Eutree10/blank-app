"""Life RPG — core game logic and persistence (offline-first).

This module is pure Python with no Streamlit dependency so the game rules
can be unit-tested and reused. State is persisted to a local JSON file,
which keeps the app fully offline-first for a single player.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import date, datetime
from typing import Any

# --- Constants -------------------------------------------------------------

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_rpg_data.json")

MAX_LEVEL = 46
BASE_XP = 100
XP_CURVE = 1.2
INITIAL_LIFE = 1000
DEFAULT_LIFE_PENALTY = 100
PUNISHMENT_TEXT = "100 flexiones (push-ups)"
SCHEMA_VERSION = 1


# --- Level math ------------------------------------------------------------

def xp_to_level(n: int) -> int:
    """XP required to advance FROM level ``n`` to ``n + 1``.

    Follows a 1.2x growth curve: xp_to_level(1) = 100.
    Returns a very large sentinel at the level cap so a maxed player
    never "needs" more XP.
    """
    if n >= MAX_LEVEL:
        return 10 ** 9
    return round(BASE_XP * (XP_CURVE ** (n - 1)))


# --- Defaults --------------------------------------------------------------

def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def default_habits() -> list[dict[str, Any]]:
    return [
        {"id": _new_id(), "name": "Hacer ejercicio", "type": "good",
         "xpReward": 50, "coinReward": 20, "lifePenalty": 0, "icon": "🏋️", "active": True},
        {"id": _new_id(), "name": "Leer 30 min", "type": "good",
         "xpReward": 30, "coinReward": 10, "lifePenalty": 0, "icon": "📚", "active": True},
        {"id": _new_id(), "name": "Beber agua", "type": "good",
         "xpReward": 15, "coinReward": 5, "lifePenalty": 0, "icon": "💧", "active": True},
        {"id": _new_id(), "name": "Meditar", "type": "good",
         "xpReward": 25, "coinReward": 10, "lifePenalty": 0, "icon": "🧘", "active": True},
        {"id": _new_id(), "name": "Comida chatarra", "type": "bad",
         "xpReward": 0, "coinReward": 0, "lifePenalty": 100, "icon": "🍔", "active": True},
        {"id": _new_id(), "name": "Fumar", "type": "bad",
         "xpReward": 0, "coinReward": 0, "lifePenalty": 150, "icon": "🚬", "active": True},
        {"id": _new_id(), "name": "Procrastinar", "type": "bad",
         "xpReward": 0, "coinReward": 0, "lifePenalty": 100, "icon": "📱", "active": True},
    ]


def default_shop_items() -> list[dict[str, Any]]:
    return [
        {"id": _new_id(), "name": "Vida +200", "price": 150, "effect": "life",
         "lifeAmount": 200, "icon": "❤️", "active": True},
        {"id": _new_id(), "name": "Vida +500", "price": 350, "effect": "life",
         "lifeAmount": 500, "icon": "💖", "active": True},
        {"id": _new_id(), "name": "Café premium", "price": 50, "effect": "none",
         "lifeAmount": 0, "icon": "☕", "active": True},
        {"id": _new_id(), "name": "Noche de películas", "price": 100, "effect": "none",
         "lifeAmount": 0, "icon": "🎬", "active": True},
        {"id": _new_id(), "name": "Compra especial", "price": 500, "effect": "none",
         "lifeAmount": 0, "icon": "🎁", "active": True},
    ]


def default_player() -> dict[str, Any]:
    return {
        "level": 1,
        "xp": 0,
        "coins": 0,
        "life": INITIAL_LIFE,
        "lastLifeBuyDate": None,
        "xpToNextLevel": xp_to_level(1),
    }


def default_state() -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "player": default_player(),
        "habits": default_habits(),
        "shop": default_shop_items(),
        "logs": [],
    }


# --- Persistence -----------------------------------------------------------

def load_state() -> dict[str, Any]:
    """Load state from disk, falling back to a fresh default state."""
    if not os.path.exists(DATA_FILE):
        return default_state()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return _migrate(data)
    except (json.JSONDecodeError, OSError, KeyError):
        return default_state()


def save_state(state: dict[str, Any]) -> None:
    """Atomically write state to disk."""
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def _migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Fill in any missing keys so older/partial save files still load."""
    base = default_state()
    base["schemaVersion"] = SCHEMA_VERSION
    if isinstance(data.get("player"), dict):
        base["player"].update(data["player"])
    for key in ("habits", "shop", "logs"):
        if isinstance(data.get(key), list):
            base[key] = data[key]
    # Recompute derived field defensively.
    base["player"]["xpToNextLevel"] = xp_to_level(base["player"].get("level", 1))
    return base


# --- Logging ---------------------------------------------------------------

def _add_log(state: dict[str, Any], category: str, ref_id: str,
             d_xp: int = 0, d_coins: int = 0, d_life: int = 0, note: str = "") -> None:
    state["logs"].insert(0, {
        "id": _new_id(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "refId": ref_id,
        "deltaXp": d_xp,
        "deltaCoins": d_coins,
        "deltaLife": d_life,
        "note": note,
    })


# --- Game rules ------------------------------------------------------------

def _apply_level_ups(player: dict[str, Any]) -> int:
    """Consume XP into levels while possible. Returns levels gained."""
    gained = 0
    while player["level"] < MAX_LEVEL:
        needed = xp_to_level(player["level"])
        if player["xp"] < needed:
            break
        player["xp"] -= needed
        player["level"] += 1
        gained += 1
    if player["level"] >= MAX_LEVEL:
        # Cap XP display once maxed.
        player["xp"] = min(player["xp"], 0) if player["xp"] < 0 else player["xp"]
    player["xpToNextLevel"] = xp_to_level(player["level"])
    return gained


def mark_habit(state: dict[str, Any], habit_id: str) -> dict[str, Any]:
    """Mark a habit as done. Returns a small result summary."""
    habit = next((h for h in state["habits"] if h["id"] == habit_id), None)
    if habit is None:
        return {"ok": False, "reason": "not_found"}

    result = {"ok": True, "name": habit["name"], "levels_gained": 0,
              "d_xp": 0, "d_coins": 0, "d_life": 0, "life_zero": False}
    player = state["player"]

    if habit["type"] == "good":
        d_xp = int(habit.get("xpReward", 0))
        d_coins = int(habit.get("coinReward", 0))
        player["xp"] += d_xp
        player["coins"] += d_coins
        result["d_xp"] = d_xp
        result["d_coins"] = d_coins
        result["levels_gained"] = _apply_level_ups(player)
        _add_log(state, "habit", habit_id, d_xp=d_xp, d_coins=d_coins, note=habit["name"])
    else:  # bad
        penalty = int(habit.get("lifePenalty", DEFAULT_LIFE_PENALTY))
        player["life"] -= penalty
        result["d_life"] = -penalty
        _add_log(state, "habit", habit_id, d_life=-penalty, note=habit["name"])

    result["life_zero"] = player["life"] <= 0
    save_state(state)
    return result


def buy_item(state: dict[str, Any], item_id: str) -> dict[str, Any]:
    """Purchase a shop item. Enforces coin cost and once-per-day life buys."""
    item = next((s for s in state["shop"] if s["id"] == item_id), None)
    if item is None:
        return {"ok": False, "reason": "not_found"}

    player = state["player"]
    price = int(item.get("price", 0))
    if player["coins"] < price:
        return {"ok": False, "reason": "no_coins", "name": item["name"]}

    is_life = item.get("effect") == "life"
    today = date.today().isoformat()
    if is_life and player.get("lastLifeBuyDate") == today:
        return {"ok": False, "reason": "life_daily_limit", "name": item["name"]}

    player["coins"] -= price
    d_life = 0
    if is_life:
        d_life = int(item.get("lifeAmount", 0))
        player["life"] += d_life
        player["lastLifeBuyDate"] = today

    _add_log(state, "shop", item_id, d_coins=-price, d_life=d_life, note=item["name"])
    save_state(state)
    return {"ok": True, "name": item["name"], "d_coins": -price, "d_life": d_life}


def complete_punishment(state: dict[str, Any]) -> None:
    """Player confirmed the punishment: restore life and log it."""
    state["player"]["life"] = INITIAL_LIFE
    _add_log(state, "punishment", "punishment",
             d_life=INITIAL_LIFE, note=PUNISHMENT_TEXT)
    save_state(state)


def needs_punishment(state: dict[str, Any]) -> bool:
    return state["player"]["life"] <= 0


def reset_progress(state: dict[str, Any]) -> dict[str, Any]:
    """Reset player, keeping habit/shop configuration is NOT desired here —
    a full reset returns fresh defaults."""
    fresh = default_state()
    save_state(fresh)
    return fresh


def reset_player_only(state: dict[str, Any]) -> dict[str, Any]:
    """Reset stats and history but keep the player's habit & shop config."""
    state["player"] = default_player()
    state["logs"] = []
    save_state(state)
    return state
