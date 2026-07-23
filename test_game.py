"""Unit tests for Life RPG core game logic."""

import importlib
from datetime import date

import pytest

import game


@pytest.fixture
def state(tmp_path, monkeypatch):
    """Fresh state backed by a temp data file so tests don't touch real saves."""
    monkeypatch.setattr(game, "DATA_FILE", str(tmp_path / "data.json"))
    return game.default_state()


# --- Level math ------------------------------------------------------------

def test_xp_curve():
    assert game.xp_to_level(1) == 100
    assert game.xp_to_level(2) == 120
    assert game.xp_to_level(3) == 144
    assert game.xp_to_level(5) == 207


def test_xp_to_level_caps_at_max():
    assert game.xp_to_level(game.MAX_LEVEL) == 10 ** 9
    assert game.xp_to_level(game.MAX_LEVEL + 5) == 10 ** 9


# --- Good habits -----------------------------------------------------------

def test_mark_good_habit_grants_xp_and_coins(state):
    habit = next(h for h in state["habits"] if h["type"] == "good")
    res = game.mark_habit(state, habit["id"])
    assert res["ok"]
    assert state["player"]["xp"] == habit["xpReward"]
    assert state["player"]["coins"] == habit["coinReward"]
    assert state["logs"][0]["category"] == "habit"


def test_level_up_consumes_xp(state):
    # Give a huge-reward habit to force a level up.
    state["habits"] = [{"id": "x1", "name": "big", "type": "good",
                        "xpReward": 250, "coinReward": 0, "lifePenalty": 0,
                        "icon": "⭐", "active": True}]
    res = game.mark_habit(state, "x1")
    # 250 xp: level 1->2 costs 100, 2->3 costs 120 => 2 level ups, 30 xp left.
    assert res["levels_gained"] == 2
    assert state["player"]["level"] == 3
    assert state["player"]["xp"] == 30
    assert state["player"]["xpToNextLevel"] == game.xp_to_level(3)


def test_level_never_exceeds_max(state):
    state["player"]["level"] = game.MAX_LEVEL - 1
    state["habits"] = [{"id": "x1", "name": "big", "type": "good",
                        "xpReward": 10 ** 8, "coinReward": 0, "lifePenalty": 0,
                        "icon": "⭐", "active": True}]
    game.mark_habit(state, "x1")
    assert state["player"]["level"] == game.MAX_LEVEL


# --- Bad habits ------------------------------------------------------------

def test_mark_bad_habit_costs_life(state):
    habit = next(h for h in state["habits"] if h["type"] == "bad")
    start = state["player"]["life"]
    res = game.mark_habit(state, habit["id"])
    assert state["player"]["life"] == start - habit["lifePenalty"]
    assert res["d_life"] == -habit["lifePenalty"]


def test_life_zero_flags_punishment(state):
    state["player"]["life"] = 50
    habit = next(h for h in state["habits"] if h["type"] == "bad")
    habit["lifePenalty"] = 100
    res = game.mark_habit(state, habit["id"])
    assert res["life_zero"]
    assert game.needs_punishment(state)


# --- Punishment ------------------------------------------------------------

def test_complete_punishment_restores_life(state):
    state["player"]["life"] = -20
    game.complete_punishment(state)
    assert state["player"]["life"] == game.INITIAL_LIFE
    assert state["logs"][0]["category"] == "punishment"
    assert not game.needs_punishment(state)


# --- Shop ------------------------------------------------------------------

def test_buy_item_without_coins_fails(state):
    item = state["shop"][0]
    state["player"]["coins"] = 0
    res = game.buy_item(state, item["id"])
    assert not res["ok"]
    assert res["reason"] == "no_coins"


def test_buy_life_item_adds_life_once_per_day(state):
    life_item = next(s for s in state["shop"] if s["effect"] == "life")
    state["player"]["coins"] = life_item["price"] * 3
    start_life = state["player"]["life"]

    res = game.buy_item(state, life_item["id"])
    assert res["ok"]
    assert state["player"]["life"] == start_life + life_item["lifeAmount"]
    assert state["player"]["lastLifeBuyDate"] == date.today().isoformat()

    # Second life purchase same day is blocked.
    res2 = game.buy_item(state, life_item["id"])
    assert not res2["ok"]
    assert res2["reason"] == "life_daily_limit"


def test_buy_non_life_item_not_daily_limited(state):
    item = next(s for s in state["shop"] if s["effect"] == "none")
    state["player"]["coins"] = item["price"] * 3
    assert game.buy_item(state, item["id"])["ok"]
    assert game.buy_item(state, item["id"])["ok"]  # again, fine
    assert state["player"]["coins"] == item["price"]


# --- Persistence -----------------------------------------------------------

def test_save_and_load_roundtrip(state):
    state["player"]["coins"] = 999
    game.save_state(state)
    loaded = game.load_state()
    assert loaded["player"]["coins"] == 999


def test_load_missing_file_returns_defaults(state):
    fresh = game.load_state()
    assert fresh["player"]["level"] == 1
    assert fresh["player"]["life"] == game.INITIAL_LIFE


def test_migrate_fills_missing_keys():
    partial = {"player": {"level": 5, "xp": 10}}
    migrated = game._migrate(partial)
    assert migrated["player"]["level"] == 5
    assert migrated["player"]["coins"] == 0  # default filled
    assert migrated["player"]["xpToNextLevel"] == game.xp_to_level(5)
    assert isinstance(migrated["habits"], list)


def test_reset_player_only_keeps_config(state):
    original_habits = state["habits"]
    state["player"]["coins"] = 500
    game.mark_habit(state, original_habits[0]["id"])
    reset = game.reset_player_only(state)
    assert reset["player"]["coins"] == 0
    assert reset["logs"] == []
    assert len(reset["habits"]) == len(original_habits)
