"""The VDOT model. Everything downstream inherits these numbers."""

from __future__ import annotations

import pytest

from raceform.analysis.physiology import (
    effective_pace,
    equivalent_time,
    fraction_of_vdot,
    grade_adjusted_pace,
    pace_at_fraction,
    time_for_distance,
    vdot,
    velocity_of_vo2,
    vo2_of_velocity,
    zones_for,
)


def test_vdot_of_known_performance():
    # A 17:20 5K is a VDOT of roughly 58.5–59 in Daniels' tables.
    assert vdot(5000, 17 * 60 + 20) == pytest.approx(58.8, abs=0.6)


def test_vdot_and_time_are_inverses():
    for distance in (800, 1500, 3000, 5000, 10000):
        seconds = time_for_distance(distance, 55.0)
        assert vdot(distance, seconds) == pytest.approx(55.0, abs=0.05)


def test_equivalent_performances_are_ordered_and_plausible():
    seconds_5k = 17 * 60 + 20
    assert equivalent_time(5000, seconds_5k, 1500) == pytest.approx(280, abs=12)  # ~4:40
    assert equivalent_time(5000, seconds_5k, 10000) == pytest.approx(2157, abs=45)  # ~35:57
    # Longer distances are always slower per kilometre.
    pace_5k = seconds_5k / 5
    pace_10k = equivalent_time(5000, seconds_5k, 10000) / 10
    assert pace_10k > pace_5k


def test_vo2_velocity_roundtrip():
    for velocity in (200, 280, 340):
        assert velocity_of_vo2(vo2_of_velocity(velocity)) == pytest.approx(velocity, abs=0.01)


def test_zone_paces_are_ordered_fastest_to_slowest():
    zones = zones_for(58.8)
    assert zones.repetition[0] < zones.interval[0] < zones.threshold[0] < zones.marathon[0] < zones.easy[0]


def test_interval_pace_matches_the_prescription_in_the_brief():
    # The brief prescribes 5 × 1000 at 3:23–3:27 for a runner targeting sub-17:20.
    zones = zones_for(58.8)
    fast, slow = zones.interval
    assert 195 <= fast <= 210
    assert 200 <= slow <= 215


def test_zone_of_classifies_paces():
    zones = zones_for(58.8)
    assert zones.zone_of(190) == "repetition"
    assert zones.zone_of(206) == "interval"
    assert zones.zone_of(229) == "threshold"
    assert zones.zone_of(290) == "easy"


def test_fraction_of_vdot_inverts_pace_at_fraction():
    for fraction in (0.7, 0.86, 1.0):
        pace = pace_at_fraction(58.0, fraction)
        assert fraction_of_vdot(pace, 58.0) == pytest.approx(fraction, abs=0.001)


class TestElevation:
    def test_uphill_is_worth_a_faster_flat_pace(self):
        assert grade_adjusted_pace(240, 0.05) < 240

    def test_downhill_is_worth_a_slower_flat_pace(self):
        assert grade_adjusted_pace(240, -0.05) > 240

    def test_flat_is_a_no_op(self):
        assert grade_adjusted_pace(240, 0.0) == pytest.approx(240)

    def test_rolling_gain_barely_changes_the_pace(self):
        # 60 m of ascent over 10 km is a rolling loop, not a climb: the descent
        # pays the ascent back, so the adjustment must stay tiny.
        adjusted = effective_pace(240, elevation_gain_m=60, distance_m=10_000)
        assert adjusted == pytest.approx(240, rel=0.01)

    def test_sustained_climb_is_adjusted_properly(self):
        # 21 m over a 300 m rep is a 7% hill and genuinely much harder.
        adjusted = effective_pace(230, elevation_gain_m=21, distance_m=300)
        assert adjusted < 230 * 0.85

    def test_zero_distance_is_safe(self):
        assert effective_pace(240, 10, 0) == 240
