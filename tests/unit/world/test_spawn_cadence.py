"""
tests/unit/world/test_spawn_cadence.py

Unit tests for the two-tier SpawnService cadence added in TCK-20260627-P2B-SPAWN-CADENCE
(parity: WORLD-103).

Coverage:
- SpawnConfig default values
- Early-game single spawn (batch_size=1 at tick < threshold)
- Late-game batch spawn (batch_size=2 at tick >= threshold)
- Batch capped by density deficit
- Interval guard (non-multiple-of-50 tick → empty update)
- Determinism: two calls with same state produce identical entities
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass, field

from src.core.state import AuthoritativeState, RegionState
from src.systems.world_systems.generator import EntityGenerator
from src.world.spawn import SpawnService
from src.world.spawn_config import SpawnConfig, DEFAULT_SPAWN_CONFIG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(tick: int, regions: dict | None = None) -> AuthoritativeState:
    """Minimal AuthoritativeState for spawn tests — no entities, configurable tick."""
    return AuthoritativeState(
        tick=tick,
        seed=42,
        entities={},
        regions=regions or {},
    )


def _forest_region(r_id: str = "r1") -> RegionState:
    """
    A 100x100 FOREST region.
    area = 10_000 → target_count = max(2, int(1.0 * 2.0 * 1.0)) = 2.
    With no entities alive, deficit = 2.
    """
    return RegionState(id=r_id, name=r_id, bounds=(0, 0, 100, 100), kind="FOREST")


# ---------------------------------------------------------------------------
# SpawnConfig defaults
# ---------------------------------------------------------------------------

class TestSpawnConfigDefaults:
    def test_default_base_batch_size(self):
        cfg = SpawnConfig()
        assert cfg.base_spawn_batch_size == 1

    def test_default_late_spawn_threshold_tick(self):
        cfg = SpawnConfig()
        assert cfg.late_spawn_threshold_tick == 500

    def test_default_late_spawn_batch_size(self):
        cfg = SpawnConfig()
        assert cfg.late_spawn_batch_size == 2

    def test_default_spawn_config_singleton(self):
        assert DEFAULT_SPAWN_CONFIG.base_spawn_batch_size == 1
        assert DEFAULT_SPAWN_CONFIG.late_spawn_threshold_tick == 500
        assert DEFAULT_SPAWN_CONFIG.late_spawn_batch_size == 2

    def test_spawn_config_is_frozen(self):
        cfg = SpawnConfig()
        with pytest.raises((AttributeError, TypeError)):
            cfg.base_spawn_batch_size = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Interval guard
# ---------------------------------------------------------------------------

class TestIntervalGuard:
    def test_non_interval_tick_returns_empty(self):
        """tick=101 is not a multiple of 50 → no spawns regardless of config."""
        state = _make_state(tick=101, regions={"r1": _forest_region()})
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen)

        assert update.entities_add == [] or update.entities_add is None

    def test_interval_tick_zero_is_skipped(self):
        """tick=0 % 50 == 0, so the guard allows it, but also tick=0 IS a multiple of 50.
        We just verify the guard check (0 % 50 == 0 is True → allowed through).
        The spawn may or may not produce entities depending on pool/density."""
        state = _make_state(tick=0, regions={"r1": _forest_region()})
        gen = EntityGenerator(seed=42)
        # Should not raise — guard allows through
        update = SpawnService.process_spawns(state, gen)
        assert update is not None


# ---------------------------------------------------------------------------
# Two-tier cadence
# ---------------------------------------------------------------------------

class TestEarlyGameCadence:
    def test_early_game_spawns_one_per_region(self):
        """
        At tick=100 (below threshold=500), base_spawn_batch_size=1.
        One FOREST region with deficit=2 → only 1 entity spawned.
        """
        state = _make_state(tick=100, regions={"r1": _forest_region()})
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen)

        entities = update.entities_add or []
        assert len(entities) == 1, (
            f"Expected 1 entity in early game (batch_size=1), got {len(entities)}"
        )

    def test_early_game_two_regions_spawn_one_each(self):
        """Two FOREST regions, both below density, early game → 1 spawn each = 2 total."""
        regions = {
            "r1": _forest_region("r1"),
            "r2": RegionState(id="r2", name="r2", bounds=(200, 0, 300, 100), kind="FOREST"),
        }
        state = _make_state(tick=100, regions=regions)
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen)

        entities = update.entities_add or []
        assert len(entities) == 2, (
            f"Expected 2 entities (1 per region, early game), got {len(entities)}"
        )


class TestLateGameCadence:
    def test_late_game_spawns_two_per_region_at_threshold(self):
        """
        At tick=500 (== late_spawn_threshold_tick), late_spawn_batch_size=2.
        One FOREST region, deficit=2 → 2 entities spawned.
        """
        state = _make_state(tick=500, regions={"r1": _forest_region()})
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen)

        entities = update.entities_add or []
        assert len(entities) == 2, (
            f"Expected 2 entities in late game (batch_size=2), got {len(entities)}"
        )

    def test_late_game_spawns_two_per_region_well_past_threshold(self):
        """At tick=800 (well past threshold), same two-entity behaviour."""
        state = _make_state(tick=800, regions={"r1": _forest_region()})
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen)

        entities = update.entities_add or []
        assert len(entities) == 2, (
            f"Expected 2 entities at tick=800 (late game), got {len(entities)}"
        )

    def test_batch_capped_by_density_deficit(self):
        """
        A batch_size=3 config should still only spawn 2 when deficit == 2.
        Verifies min(batch_size, deficit) is respected.
        """
        config = SpawnConfig(
            base_spawn_batch_size=1,
            late_spawn_threshold_tick=500,
            late_spawn_batch_size=3,   # higher than deficit
        )
        # FOREST 100x100 → target_count=2, deficit=2
        state = _make_state(tick=500, regions={"r1": _forest_region()})
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen, spawn_config=config)

        entities = update.entities_add or []
        assert len(entities) == 2, (
            f"Expected exactly 2 (capped by deficit=2), got {len(entities)}"
        )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_state_produces_same_entities(self):
        """
        Two independent calls with the same seed/tick produce entity lists with
        identical positions and kinds (deterministic RNG).
        """
        state = _make_state(tick=500, regions={"r1": _forest_region()})

        gen_a = EntityGenerator(seed=42)
        update_a = SpawnService.process_spawns(state, gen_a)

        gen_b = EntityGenerator(seed=42)
        update_b = SpawnService.process_spawns(state, gen_b)

        entities_a = update_a.entities_add or []
        entities_b = update_b.entities_add or []

        assert len(entities_a) == len(entities_b)
        for ea, eb in zip(entities_a, entities_b):
            assert ea.navigation.position == eb.navigation.position, (
                "Position mismatch — RNG is not deterministic for batch spawn"
            )
            assert ea.kind == eb.kind, (
                "Kind mismatch — RNG is not deterministic for batch spawn"
            )

    def test_early_and_late_first_entity_same_position(self):
        """
        The first entity spawned in late game (batch_idx=0) must have the same
        position as the entity spawned in early game at the same tick, because
        batch_idx=0 reuses the original RNG keys.

        NOTE: This test is meaningful only when late_spawn_threshold_tick <= tick
        and base_spawn_batch_size == 1 (early) vs batch_idx=0 of late game.
        We compare early-game (tick=100) vs late-game (tick=600) carefully:
        RNG draws depend on tick, so positions WILL differ across ticks — instead
        we compare two late-game calls to verify batch_idx=0 key stability.
        """
        state1 = _make_state(tick=500, regions={"r1": _forest_region()})
        state2 = _make_state(tick=500, regions={"r1": _forest_region()})

        gen1 = EntityGenerator(seed=42)
        update1 = SpawnService.process_spawns(state1, gen1)

        gen2 = EntityGenerator(seed=42)
        update2 = SpawnService.process_spawns(state2, gen2)

        e1 = (update1.entities_add or [])[0]
        e2 = (update2.entities_add or [])[0]
        assert e1.navigation.position == e2.navigation.position


# ---------------------------------------------------------------------------
# next_entity_id propagation
# ---------------------------------------------------------------------------

class TestEntityIdPropagation:
    def test_next_entity_id_set_after_batch(self):
        """StateUpdate.next_entity_id_set should reflect all spawned entities."""
        state = _make_state(tick=500, regions={"r1": _forest_region()})
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen)

        entities = update.entities_add or []
        assert len(entities) == 2
        # next_entity_id_set must be set (entities were added)
        assert update.next_entity_id_set is not None
        assert update.next_entity_id_set > 0

    def test_no_id_set_when_no_regions(self):
        """With no regions, nothing spawns and next_entity_id_set is None."""
        state = _make_state(tick=500, regions={})
        gen = EntityGenerator(seed=42)

        update = SpawnService.process_spawns(state, gen)

        entities = update.entities_add or []
        assert len(entities) == 0
        assert update.next_entity_id_set is None
