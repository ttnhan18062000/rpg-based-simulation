"""TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS.

`LegalityServiceV2.get_engaged_hostiles_at_pos()` has three internal implementations of the same
hostility test (occupancy-snapshot fast path, `SpatialQueryService` fallback, direct dict-
iteration fallback). Each is exercised here separately, in both directions, to prove the fix
(real catalog hostility via `is_hostile_compat()`, not the raw legacy `Faction` enum) landed in
all three, not just the one a default test run happens to hit.

Test pairs, chosen from real, previously-measured catalog data
(`data/content/social/factions.yaml`), not synthetic ids:
- `bandit_company` / `goblin_warband`: both `legacy_engine_bucket: MONSTER_HORDE` (the OLD code
  would never flag them as engaged), but a real, specifically authored catalog rivalry (both
  `alignment_bucket: invader`, with a real relationship/perspective entry between them) makes
  them genuinely hostile under `is_hostile_compat()`. Proves the fix catches a real rivalry the
  old code structurally could not see.
- `hero_guild` / `merchant_league`: different legacy buckets (`HERO_GUILD` / `NEUTRAL` — the OLD
  code WOULD flag them as engaged), but neither is `alignment_bucket: invader` and no catalog
  relationship exists between them, so `is_hostile_compat()` correctly says NOT hostile. Proves
  the fix removes a real false-positive engagement the old code produced.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, EntityRole
from src.core.state import AuthoritativeState
from src.engine.legality import LegalityServiceV2
from src.engine.occupancy_snapshot import OccupancySnapshot


def _entity(eid, faction_id, legacy_faction, pos):
    entity = (
        V2EntityBuilder(eid)
        .kind("actor")
        .identity(role=EntityRole.MONSTER, faction=legacy_faction, properties={"faction_id": faction_id})
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    return replace(entity, navigation=replace(entity.navigation, position=pos))


def _hostile_pair():
    """bandit_company / goblin_warband: same legacy bucket, real catalog rivalry."""
    a = _entity(1, "bandit_company", Faction.MONSTER_HORDE, (5.0, 5.0))
    b = _entity(2, "goblin_warband", Faction.MONSTER_HORDE, (5.0, 6.0))
    return a, b


def _non_hostile_pair():
    """hero_guild / merchant_league: different legacy buckets, no real catalog hostility."""
    a = _entity(1, "hero_guild", Faction.HERO_GUILD, (5.0, 5.0))
    b = _entity(2, "merchant_league", Faction.NEUTRAL, (5.0, 6.0))
    return a, b


# --- Path 1: occupancy_snapshot fast path (src/engine/legality.py:525-533) ---

def test_occupancy_snapshot_path_catches_same_bucket_catalog_rivalry():
    a, b = _hostile_pair()
    state = AuthoritativeState(tick=1, seed=1, entities={1: a, 2: b})
    snapshot = OccupancySnapshot.from_state(state)
    state = replace(state, occupancy_snapshot=snapshot)

    engaged = LegalityServiceV2.get_engaged_hostiles_at_pos(a.navigation.position, a, state)
    assert engaged == [2], "same-legacy-bucket real catalog rivalry must be caught by the fast path"


def test_occupancy_snapshot_path_clears_different_bucket_non_hostile_pair():
    a, b = _non_hostile_pair()
    state = AuthoritativeState(tick=1, seed=1, entities={1: a, 2: b})
    snapshot = OccupancySnapshot.from_state(state)
    state = replace(state, occupancy_snapshot=snapshot)

    engaged = LegalityServiceV2.get_engaged_hostiles_at_pos(a.navigation.position, a, state)
    assert engaged == [], "different-legacy-bucket non-hostile pair must NOT be flagged by the fast path"


# --- Path 2: SpatialQueryService.get_occupancy_map fallback (src/engine/legality.py:535-547) ---
# Reached when state.occupancy_snapshot is None (the default) but state is a real AuthoritativeState.

def test_spatial_query_fallback_path_catches_same_bucket_catalog_rivalry():
    a, b = _hostile_pair()
    state = AuthoritativeState(tick=1, seed=1, entities={1: a, 2: b})
    assert state.occupancy_snapshot is None

    engaged = LegalityServiceV2.get_engaged_hostiles_at_pos(a.navigation.position, a, state)
    assert engaged == [2], "same-legacy-bucket real catalog rivalry must be caught by the SpatialQueryService fallback"


def test_spatial_query_fallback_path_clears_different_bucket_non_hostile_pair():
    a, b = _non_hostile_pair()
    state = AuthoritativeState(tick=1, seed=1, entities={1: a, 2: b})
    assert state.occupancy_snapshot is None

    engaged = LegalityServiceV2.get_engaged_hostiles_at_pos(a.navigation.position, a, state)
    assert engaged == [], "different-legacy-bucket non-hostile pair must NOT be flagged by the SpatialQueryService fallback"


# --- Path 3: direct dict-iteration fallback (src/engine/legality.py:549-559) ---
# Reached when `state` is not a real AuthoritativeState (SpatialQueryService.get_occupancy_map
# raises AttributeError on state.entities), matching the except clause's own handling of a bare
# entities dict.

def test_dict_iteration_fallback_path_catches_same_bucket_catalog_rivalry():
    a, b = _hostile_pair()
    bare_state = {1: a, 2: b}

    engaged = LegalityServiceV2.get_engaged_hostiles_at_pos(a.navigation.position, a, bare_state)
    assert engaged == [2], "same-legacy-bucket real catalog rivalry must be caught by the dict-iteration fallback"


def test_dict_iteration_fallback_path_clears_different_bucket_non_hostile_pair():
    a, b = _non_hostile_pair()
    bare_state = {1: a, 2: b}

    engaged = LegalityServiceV2.get_engaged_hostiles_at_pos(a.navigation.position, a, bare_state)
    assert engaged == [], "different-legacy-bucket non-hostile pair must NOT be flagged by the dict-iteration fallback"
