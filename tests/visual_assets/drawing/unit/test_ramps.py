"""Hue-shifted ramps (pure; no Aseprite)."""

from __future__ import annotations

import colorsys
import pytest

from visual_assets.drawing.colors import hex_to_rgba, luma
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.technique.ramps import make_ramp

def hsv(hexcolor):
    r, g, b, _ = hex_to_rgba(hexcolor)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s, v


# ============================================================ pure: ramps


def test_ramp_base_in_place_value_monotonic_and_hue_shifts_toward_blue_and_yellow():
    base = "#3ec96b"  # green, hue ~139
    ramp = make_ramp(base, 5)
    assert len(ramp) == 5 and ramp[2] == base
    lumas = [luma(hex_to_rgba(c)) for c in ramp]
    assert lumas == sorted(lumas) and len(set(lumas)) == 5
    h_base = hsv(base)[0]
    assert hsv(ramp[0])[0] > h_base  # shadow drifts toward 250 (blue/purple): hue increases from 139
    assert hsv(ramp[4])[0] < h_base  # highlight drifts toward 55 (yellow): hue decreases
    assert hsv(ramp[4])[1] < hsv(base)[1]  # saturation falls toward the light end


def test_ramp_hue_never_overshoots_target_and_zero_shift_keeps_hue():
    ramp = make_ramp("#3366cc", 9, hue_shift=60.0)  # base hue 220, already near the 250 shadow target
    shadows = [hsv(c)[0] for c in ramp[:4]]
    assert max(shadows) <= 251.0  # clamped at the 250 target, never past it
    assert shadows[0] >= hsv("#3366cc")[0]  # and it did move toward it
    base_h = hsv("#c0392b")[0]
    flat = make_ramp("#c0392b", 5, hue_shift=0.0)
    for c in flat:
        if hsv(c)[1] > 0.05:
            assert abs(hsv(c)[0] - base_h) <= 2.0  # only 8-bit RGB rounding noise


def test_ramp_neutral_base_gets_cool_shadow_warm_light():
    ramp = make_ramp("#808080", 5)
    dr, dg, db, _ = hex_to_rgba(ramp[0])
    lr, lg, lb, _ = hex_to_rgba(ramp[4])
    assert db > dr  # bluish shadow
    assert lr > lb  # yellowish highlight


@pytest.mark.parametrize("kwargs", [
    {"steps": 1}, {"steps": 10}, {"steps": True and "5"}, {"hue_shift": -1.0},
    {"hue_shift": 61.0}, {"base_index": 7},
])
def test_ramp_validation(kwargs):
    with pytest.raises(AdapterError):
        make_ramp("#336699", **kwargs)


def test_ramp_rejects_bad_colour():
    with pytest.raises(AdapterError):
        make_ramp("blue")


