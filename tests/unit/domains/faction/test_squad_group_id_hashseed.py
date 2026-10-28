"""FACTION_SQUAD group_id and the canonical state hash do not depend on PYTHONHASHSEED.

TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID. No shipped gate world
forms a squad in the measured runs, so this hand-built WAR state is the behaviour evidence:
two factions at WAR, a contested defender region and 3 GUARD entities, so
MilitaryConflictPhase commits a squad. Each hash seed runs in two fresh processes, so the
test also shows the result is repeatable within a seed.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]

_SCRIPT = r'''
import json
from src.core.enums import DiplomaticState as DS, EntityRole
from src.core.stable_hash import stable_int31
from src.core.state import (
    AuthoritativeState, EntityState, FactionState, IdentityComponent,
    NavigationComponent, RegionState,
)
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.military_conflict import MilitaryConflictPhase

tick = 3
state = AuthoritativeState(
    tick=tick,
    seed=42,
    entities={
        eid: EntityState(
            id=eid,
            kind="npc",
            identity=IdentityComponent(role=EntityRole.GUARD),
            navigation=NavigationComponent(region_id="r2"),
        )
        for eid in (101, 102, 103)
    },
    factions={
        "fa": FactionState(faction_id="fa", diplomatic_relations={"fb": DS.WAR}),
        "fb": FactionState(faction_id="fb", territory=("r2",), diplomatic_relations={"fa": DS.WAR}),
    },
    regions={"r2": RegionState(id="r2", name="r2", bounds=(0, 0, 10, 10))},
)
update = MilitaryConflictPhase.execute(state)
new_state = ApplyPath.apply_generation(state, update)
print(json.dumps({
    "group_ids": [g.id for g in update.groups_add_or_update],
    "expected_id": stable_int31("r2", "fa", tick),
    "state_group_ids": sorted(new_state.groups),
    "state_hash": CanonicalStateHasher.get_hash(new_state),
    "legacy_salted_id": abs(hash(("r2", "fa", tick))) % (2 ** 31),
}))
'''


def _run(hashseed: str) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": hashseed}
    out = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_REPO_ROOT, env=env, capture_output=True, text=True, check=True, timeout=120,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def runs() -> dict:
    return {seed: [_run(seed), _run(seed)] for seed in ("0", "1")}


def test_squad_forms_and_uses_stable_id(runs):
    for seed_runs in runs.values():
        for r in seed_runs:
            assert len(r["group_ids"]) == 1
            assert r["group_ids"] == [r["expected_id"]]
            assert r["state_group_ids"] == [r["expected_id"]]


def test_group_id_and_state_hash_equal_across_and_within_hashseeds(runs):
    all_runs = runs["0"] + runs["1"]
    assert len({tuple(r["group_ids"]) for r in all_runs}) == 1
    assert len({r["state_hash"] for r in all_runs}) == 1


def test_legacy_salted_id_would_differ_across_hashseeds(runs):
    """Sensitivity check: the pre-fix formula is salted, so this setup would have caught it."""
    assert runs["0"][0]["legacy_salted_id"] == runs["0"][1]["legacy_salted_id"]
    assert runs["0"][0]["legacy_salted_id"] != runs["1"][0]["legacy_salted_id"]
