"""Within one tick, events of one kind are emitted in sorted order, whatever the process hash seed
(TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED).

The emit loops used to iterate a ``set`` of strings or enums, or a list built from one, so the order
followed ``PYTHONHASHSEED``. Equipment slots are covered by ``test_event_extractor_equipment_multislot.py``.
Each test feeds three or more ids in an order that is not sorted, asserts the element type, and asserts the
emitted order equals the sorted order. The last test runs the extractor in subprocesses at several hash seeds.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor
from src.observability.event_shapers import ProgressionShaper, WorldDynamicsShaper
from tests.unit.observability import test_event_extractor_progression as prog
from tests.unit.observability import test_event_shapers_progression as shp
from tests.unit.observability import test_event_shapers_world_dynamics as wd

REPO = Path(__file__).resolve().parents[3]
UNSORTED = ["zeta", "alpha", "mu", "beta"]


@pytest.fixture(autouse=True)
def _reset():
    EventExtractor.reset_run_state()
    ProgressionShaper.reset_run_state()
    yield
    EventExtractor.reset_run_state()
    ProgressionShaper.reset_run_state()


def _ids(events, event_type, key):
    return [e.payload[key] for e in events if e.event_type == event_type]


def test_progression_shaper_emits_skills_traits_and_breakthroughs_sorted():
    """Default path (PHASE2 ON): the update lists come from list(set(...)) so their order is a hash order."""
    iu = shp._identity_update(learned_skills=list(UNSORTED), traits_add=list(UNSORTED), breakthroughs_add=list(UNSORTED))
    assert all(isinstance(x, str) for x in iu.learned_skills + iu.traits_add + iu.breakthroughs_add)
    prior = shp._prior_state({1: shp._entity()})
    events = ProgressionShaper().shape(prior, shp._update({1: shp._entity_update(iu)}), tick=10)
    for event_type, key in (("skill_unlocked", "skill_id"), ("trait_expressed", "trait_id"), ("pillar_trait_unlocked", "trait_id")):
        assert _ids(events, event_type, key) == sorted(UNSORTED), event_type


def test_rollback_path_emits_skills_traits_and_breakthroughs_sorted():
    """PHASE2 OFF (rollback): set differences between the prior and current identity."""
    new = frozenset(UNSORTED)
    assert all(isinstance(x, str) for x in new)
    prior = prog._entity(identity=prog._identity())
    curr = prog._entity(identity=prog._identity(learned_skills=new, traits=new, active_breakthroughs=new))
    events = EventExtractor.extract(prog._state({1: prior}), prog._state({1: curr}), prog._update(1), ObservabilityMode.NORMAL)
    for event_type, key in (("skill_unlocked", "skill_id"), ("trait_expressed", "trait_id"), ("pillar_trait_unlocked", "trait_id")):
        assert _ids(events, event_type, key) == sorted(UNSORTED), event_type


def test_recipe_learned_emits_in_sorted_order():
    recipes = frozenset(["craft_iron_sword", "craft_bread", "craft_travel_ration", "craft_arrow"])
    prior = prog._entity()
    curr = prog._entity()
    prior.identity.known_recipes = frozenset()
    curr.identity.known_recipes = recipes
    events = EventExtractor.extract(prog._state({1: prior}), prog._state({1: curr}), prog._update(1), ObservabilityMode.NORMAL)
    assert _ids(events, "recipe_learned", "recipe_id") == sorted(recipes)


def test_demographic_mortality_emits_in_entity_id_order():
    removed = [9, 3, 7, 5]
    assert all(isinstance(x, int) for x in removed)
    prior = wd._prior_state(entities={i: wd._entity(i, kind="villager") for i in removed})
    upd = wd._update(entities_remove=list(removed), entity_updates={i: wd._entity_update(combat=None) for i in removed})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert [e.entity_id for e in events if e.event_type == "demographic_mortality"] == sorted(removed)


_CHILD = r"""
import json, sys
sys.path.insert(0, ".")
from dataclasses import replace
from src.core.models.inventory import EquipSlot
from src.observability.event_extractor import EventExtractor
from tests.unit.observability.test_event_extractor_equipment_multislot import _states
from tests.unit.observability import test_event_extractor_progression as prog
slots = {EquipSlot.HEAD: "helm", EquipSlot.TORSO: "mail", EquipSlot.LEGS: "greaves", EquipSlot.MAIN_HAND: "sword"}
prior, new = _states({}, slots, {}, {s: 50.0 for s in slots})
eq = [(e.event_type, e.payload["slot"]) for e in EventExtractor.extract(prior, new, None, mode=None)
      if e.event_type in ("item_equipped", "equipment_durability_changed")]
EventExtractor.reset_run_state()
names = frozenset(["zeta", "alpha", "mu", "beta", "kappa", "omega"])
p = prog._entity(identity=prog._identity())
c = prog._entity(identity=prog._identity(learned_skills=names, traits=names, active_breakthroughs=names))
c.identity.known_recipes = names
p.identity.known_recipes = frozenset()
pr = [(e.event_type, e.payload.get("skill_id") or e.payload.get("trait_id") or e.payload.get("recipe_id"))
      for e in EventExtractor.extract(prog._state({1: p}), prog._state({1: c}), prog._update(1), None)]
raw = [str(s) for s in set(names)]
print(json.dumps({"events": eq + pr, "raw_set_order": raw}))
"""


def _run_child(seed: int) -> dict:
    out = subprocess.run([sys.executable, "-c", _CHILD], cwd=REPO, capture_output=True, text=True, timeout=300,
                         env={**__import__("os").environ, "PYTHONHASHSEED": str(seed)})
    assert out.returncode == 0, out.stderr[-2000:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_event_streams_are_identical_across_hash_seeds():
    runs = {seed: _run_child(seed) for seed in (0, 1, 2, 3)}
    # Positive control: iterating the raw set in these processes does follow the seed, so a run whose
    # events came out in set order would differ between seeds.
    assert len({tuple(r["raw_set_order"]) for r in runs.values()}) > 1
    assert len({json.dumps(r["events"]) for r in runs.values()}) == 1
    assert len(runs[0]["events"]) > 8
