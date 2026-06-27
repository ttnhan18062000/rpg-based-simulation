"""
Unit tests for PersonalitySnapshotRecorder (TCK-20260627-P2O-ENTITY-PERSONALITY-OBS).

Covers:
- LIGHT mode: emit on first observation and on project-kind change only.
- DEBUG mode: emit every tick.
- Record schema: all required fields present with correct types.
- Entity without strategic component: skipped silently.
- active_project_kind=None when entity has no active project.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.personality.recorder import PersonalitySnapshotRecorder


# ---------------------------------------------------------------------------
# Minimal stubs — avoid pulling in the full entity model for unit tests
# ---------------------------------------------------------------------------

@dataclass
class _Personality:
    greed: float = 0.3
    bravery: float = 0.7
    sociability: float = 0.5
    industry: float = 0.4

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "greed": self.greed,
            "bravery": self.bravery,
            "sociability": self.sociability,
            "industry": self.industry,
        }


@dataclass
class _Identity:
    role: Optional[int] = 0
    class_id: Optional[str] = "WARRIOR"
    personality: _Personality = field(default_factory=_Personality)


@dataclass
class _Project:
    kind: Any  # ProjectKind-like or plain object with .value


@dataclass
class _Strategic:
    current_project_id: Optional[str] = None
    projects: Dict[str, _Project] = field(default_factory=dict)


@dataclass
class _Entity:
    id: int
    identity: _Identity = field(default_factory=_Identity)
    strategic: Optional[_Strategic] = field(default_factory=_Strategic)


@dataclass
class _State:
    entities: Dict[int, _Entity]
    tick: int = 0
    seed: int = 42


class _ProjectKind:
    """Minimal enum-like for ProjectKind values."""
    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _ProjectKind):
            return self.value == other.value
        return NotImplemented


def _make_state(entities: Dict[int, _Entity], tick: int = 0) -> _State:
    return _State(entities=entities, tick=tick)


def _read_records(path: str):
    """Parse all JSONL lines from path; return list of dicts."""
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_obs_mode():
    """Ensure ObservabilityConfig is reset between tests."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    yield
    ObservabilityConfig.clear_all_overrides()


# ---------------------------------------------------------------------------
# TC-1: LIGHT mode emits on first observation and on project-kind change
# ---------------------------------------------------------------------------

def test_light_mode_emits_on_first_observation_and_change(tmp_path):
    """First tick always emits; second tick with same kind does not; third with different kind emits."""
    run_dir = str(tmp_path)
    recorder = PersonalitySnapshotRecorder(run_id="test-run", run_dir=run_dir)

    entity = _Entity(
        id=1,
        identity=_Identity(role=0, class_id="ARCHER", personality=_Personality()),
        strategic=_Strategic(
            current_project_id="proj-1",
            projects={"proj-1": _Project(kind=_ProjectKind("combat"))},
        ),
    )
    state = _make_state({1: entity})

    # Tick 1: first observation → emit
    recorder.record_tick(state, tick=1)
    records = _read_records(os.path.join(run_dir, "entity_personality_snapshots.jsonl"))
    assert len(records) == 1, "First tick must emit"
    assert records[0]["active_project_kind"] == "combat"

    # Tick 2: same project kind → no emit
    recorder.record_tick(state, tick=2)
    records = _read_records(os.path.join(run_dir, "entity_personality_snapshots.jsonl"))
    assert len(records) == 1, "Second tick with same kind must NOT emit"

    # Tick 3: project kind changes to 'exploration'
    entity2 = _Entity(
        id=1,
        identity=_Identity(role=0, class_id="ARCHER", personality=_Personality()),
        strategic=_Strategic(
            current_project_id="proj-2",
            projects={"proj-2": _Project(kind=_ProjectKind("exploration"))},
        ),
    )
    state2 = _make_state({1: entity2})
    recorder.record_tick(state2, tick=3)
    records = _read_records(os.path.join(run_dir, "entity_personality_snapshots.jsonl"))
    assert len(records) == 2, "Changed project kind must emit"
    assert records[1]["active_project_kind"] == "exploration"
    assert records[1]["tick"] == 3


# ---------------------------------------------------------------------------
# TC-2: LIGHT mode only emits once when kind is stable across multiple ticks
# ---------------------------------------------------------------------------

def test_light_mode_stable_kind_emits_once(tmp_path):
    """100 ticks of same project kind produces exactly 1 record per entity."""
    run_dir = str(tmp_path)
    recorder = PersonalitySnapshotRecorder(run_id="test-run-stable", run_dir=run_dir)

    entity = _Entity(
        id=5,
        identity=_Identity(role=1, class_id="MAGE"),
        strategic=_Strategic(
            current_project_id="p1",
            projects={"p1": _Project(kind=_ProjectKind("crafting"))},
        ),
    )
    state = _make_state({5: entity})

    for tick in range(1, 101):
        recorder.record_tick(state, tick=tick)

    records = _read_records(os.path.join(run_dir, "entity_personality_snapshots.jsonl"))
    assert len(records) == 1, "100 ticks with stable project kind must produce exactly 1 record"


# ---------------------------------------------------------------------------
# TC-3: DEBUG mode emits every tick
# ---------------------------------------------------------------------------

def test_debug_mode_emits_every_tick(tmp_path):
    """DEBUG mode must emit one record per entity per tick."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
    run_dir = str(tmp_path)
    recorder = PersonalitySnapshotRecorder(run_id="test-run-debug", run_dir=run_dir)

    entity = _Entity(
        id=7,
        identity=_Identity(role=2, class_id="ROGUE"),
        strategic=_Strategic(
            current_project_id="p99",
            projects={"p99": _Project(kind=_ProjectKind("social"))},
        ),
    )
    state = _make_state({7: entity})

    for tick in range(1, 6):
        recorder.record_tick(state, tick=tick)

    records = _read_records(os.path.join(run_dir, "entity_personality_snapshots.jsonl"))
    assert len(records) == 5, "DEBUG mode must emit every tick"
    ticks_seen = [r["tick"] for r in records]
    assert ticks_seen == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# TC-4: Record schema — all required fields with correct types
# ---------------------------------------------------------------------------

def test_record_schema_correct_fields(tmp_path):
    """Each emitted record must contain all required keys with correct types."""
    run_dir = str(tmp_path)
    recorder = PersonalitySnapshotRecorder(run_id="schema-run", run_dir=run_dir)

    pers = _Personality(greed=0.8, bravery=0.3, sociability=0.5, industry=0.9)
    entity = _Entity(
        id=3,
        identity=_Identity(role=0, class_id="PALADIN", personality=pers),
        strategic=_Strategic(
            current_project_id="q1",
            projects={"q1": _Project(kind=_ProjectKind("quest"))},
        ),
    )
    state = _make_state({3: entity})
    recorder.record_tick(state, tick=42)

    records = _read_records(os.path.join(run_dir, "entity_personality_snapshots.jsonl"))
    assert len(records) == 1
    rec = records[0]

    # Top-level keys
    for key in ("run_id", "entity_id", "tick", "role", "class_id", "personality", "active_project_kind"):
        assert key in rec, f"Key '{key}' missing from record"

    assert rec["run_id"] == "schema-run"
    assert rec["entity_id"] == 3
    assert rec["tick"] == 42
    assert rec["role"] == 0
    assert rec["class_id"] == "PALADIN"
    assert rec["active_project_kind"] == "quest"

    # Personality sub-keys
    p = rec["personality"]
    assert isinstance(p, dict)
    for sub_key in ("greed", "bravery", "sociability", "industry"):
        assert sub_key in p, f"Personality sub-key '{sub_key}' missing"
        assert isinstance(p[sub_key], float), f"Personality['{sub_key}'] must be float"

    assert p["greed"] == pytest.approx(0.8)
    assert p["bravery"] == pytest.approx(0.3)
    assert p["sociability"] == pytest.approx(0.5)
    assert p["industry"] == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# TC-5: Entity without strategic component is skipped
# ---------------------------------------------------------------------------

def test_entity_without_strategic_skipped(tmp_path):
    """Entity with strategic=None must not produce any snapshot record."""
    run_dir = str(tmp_path)
    recorder = PersonalitySnapshotRecorder(run_id="no-strat-run", run_dir=run_dir)

    entity = _Entity(id=10, identity=_Identity(), strategic=None)
    state = _make_state({10: entity})

    recorder.record_tick(state, tick=1)

    output_file = os.path.join(run_dir, "entity_personality_snapshots.jsonl")
    assert not os.path.exists(output_file), "No file should be created when all entities lack strategic"


# ---------------------------------------------------------------------------
# TC-6: active_project_kind is None when entity has no active project
# ---------------------------------------------------------------------------

def test_no_active_project_emits_none_kind(tmp_path):
    """Entity with current_project_id=None must emit active_project_kind=None."""
    run_dir = str(tmp_path)
    recorder = PersonalitySnapshotRecorder(run_id="null-kind-run", run_dir=run_dir)

    entity = _Entity(
        id=2,
        identity=_Identity(role=0, class_id="NOVICE"),
        strategic=_Strategic(current_project_id=None, projects={}),
    )
    state = _make_state({2: entity})
    recorder.record_tick(state, tick=1)

    records = _read_records(os.path.join(run_dir, "entity_personality_snapshots.jsonl"))
    assert len(records) == 1
    assert records[0]["active_project_kind"] is None


# ---------------------------------------------------------------------------
# TC-7: OFF mode emits nothing
# ---------------------------------------------------------------------------

def test_off_mode_emits_nothing(tmp_path):
    """ObservabilityMode.OFF must suppress all writes."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    run_dir = str(tmp_path)
    recorder = PersonalitySnapshotRecorder(run_id="off-run", run_dir=run_dir)

    entity = _Entity(
        id=4,
        identity=_Identity(),
        strategic=_Strategic(
            current_project_id="p",
            projects={"p": _Project(kind=_ProjectKind("combat"))},
        ),
    )
    state = _make_state({4: entity})
    recorder.record_tick(state, tick=1)

    output_file = os.path.join(run_dir, "entity_personality_snapshots.jsonl")
    assert not os.path.exists(output_file), "OFF mode must not create the output file"
