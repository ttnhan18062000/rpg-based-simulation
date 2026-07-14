"""Unit tests for tools/calibrate_simq.py world-loading fail-loud behavior.

Regression coverage for TCK-20260713-SIMQ-EVAL-PROFILE-BUG: a mistyped or
nonexistent `--name` used to silently fall back to a generic synthetic
scenario instead of erroring, letting a corrupted calibration result look
plausible instead of crashing obviously.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

from tools.calibrate_simq import _load_world_state


def test_generic_sentinel_returns_none_without_raising():
    state, report = _load_world_state("generic", seed=1)
    assert state is None
    assert report is None


def test_real_world_resolves_to_a_compiled_state():
    state, report = _load_world_state("dungeon_crawl", seed=1)
    assert state is not None
    assert report is not None


def test_unresolvable_name_raises_instead_of_falling_back():
    with pytest.raises(FileNotFoundError):
        _load_world_state("totally_unknown_world_xyz", seed=1)
