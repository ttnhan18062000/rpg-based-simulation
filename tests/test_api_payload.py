"""Tests for API payload size optimizations — RLE grid, slim entities, static split."""

import json
import unittest

from src.api.engine_manager import EngineManager
from src.api.schemas import (
    EntitySlimSchema,
    MapResponse,
    StaticDataResponse,
    WorldStateResponse,
)
from src.config import SimulationConfig


def _build_manager():
    cfg = SimulationConfig()
    return EngineManager(cfg)


class TestRLEMapGrid(unittest.TestCase):
    """Map grid should be RLE-encoded."""

    @classmethod
    def setUpClass(cls):
        cls.mgr = _build_manager()

    def test_rle_encodes_correctly(self):
        grid = self.mgr.get_grid()
        tiles = grid._tiles
        total = grid.width * grid.height

        # Build RLE the same way the endpoint does
        rle: list[int] = []
        cur_val = int(tiles[0])
        cur_count = 1
        for i in range(1, total):
            v = int(tiles[i])
            if v == cur_val:
                cur_count += 1
            else:
                rle.append(cur_val)
                rle.append(cur_count)
                cur_val = v
                cur_count = 1
        rle.append(cur_val)
        rle.append(cur_count)

        # Verify total decoded count
        decoded_total = sum(rle[i + 1] for i in range(0, len(rle), 2))
        self.assertEqual(decoded_total, 512 * 512)

        # Verify RLE is much smaller than raw 2D JSON
        rle_json = json.dumps({"width": grid.width, "height": grid.height, "grid": rle})
        rle_size = len(rle_json)
        # Raw 2D was ~876KB; RLE should be significantly smaller
        self.assertLess(rle_size, 500_000, f"RLE map too large: {rle_size} bytes")
        print(f"  RLE map size: {rle_size:,} bytes ({rle_size // 1024} KB)")

    def test_rle_decodes_to_original(self):
        grid = self.mgr.get_grid()
        tiles = grid._tiles
        total = grid.width * grid.height

        rle: list[int] = []
        cur_val = int(tiles[0])
        cur_count = 1
        for i in range(1, total):
            v = int(tiles[i])
            if v == cur_val:
                cur_count += 1
            else:
                rle.append(cur_val)
                rle.append(cur_count)
                cur_val = v
                cur_count = 1
        rle.append(cur_val)
        rle.append(cur_count)

        # Decode back
        decoded = []
        for i in range(0, len(rle), 2):
            decoded.extend([rle[i]] * rle[i + 1])
        self.assertEqual(len(decoded), total)
        for i in range(total):
            self.assertEqual(decoded[i], int(tiles[i]))


class TestSlimEntities(unittest.TestCase):
    """State endpoint should return slim entities + optional full selected entity."""

    @classmethod
    def setUpClass(cls):
        cls.mgr = _build_manager()
        cls.snap = cls.mgr.get_snapshot()

    def test_slim_schema_fields(self):
        """EntitySlimSchema should only have minimal fields."""
        slim_fields = set(EntitySlimSchema.model_fields.keys())
        # Must have rendering fields
        for f in ("id", "kind", "x", "y", "hp", "max_hp", "state", "level",
                  "tier", "faction", "weapon_range", "combat_target_id",
                  "loot_progress", "loot_duration"):
            self.assertIn(f, slim_fields)
        # Must NOT have heavy fields
        for f in ("terrain_memory", "entity_memory", "goals", "skills",
                  "attributes", "inventory_items", "quests"):
            self.assertNotIn(f, slim_fields)

    def test_slim_entity_json_size(self):
        """Each slim entity should serialize to < 300 bytes."""
        e = list(self.snap.entities.values())[0]
        slim = EntitySlimSchema(
            id=e.id, kind=e.kind, x=e.pos.x, y=e.pos.y,
            hp=e.stats.hp, max_hp=e.stats.max_hp,
            state=e.ai_state.name, level=e.stats.level,
            tier=e.tier, faction=e.faction.name.lower(),
        )
        js = slim.model_dump_json()
        self.assertLess(len(js), 300, f"Slim entity too large: {len(js)} bytes")

    def test_state_payload_without_selection(self):
        """Without selection, state should have no selected_entity and small payload."""
        entities = [e for e in self.snap.entities.values() if e.alive]
        slim_list = [
            EntitySlimSchema(
                id=e.id, kind=e.kind, x=e.pos.x, y=e.pos.y,
                hp=e.stats.hp, max_hp=e.stats.max_hp,
                state=e.ai_state.name, level=e.stats.level,
                tier=e.tier, faction=e.faction.name.lower(),
            )
            for e in entities
        ]
        resp = WorldStateResponse(
            tick=self.snap.tick,
            alive_count=len(slim_list),
            entities=slim_list,
            selected_entity=None,
        )
        js = resp.model_dump_json()
        size = len(js)
        # ~300 entities × ~200 bytes each ≈ 60KB max
        self.assertLess(size, 100_000, f"/state payload too large: {size} bytes ({size // 1024} KB)")
        print(f"  /state (no selection): {size:,} bytes ({size // 1024} KB) for {len(slim_list)} entities")


class TestStaticEndpoint(unittest.TestCase):
    """Static data should be separate and under 50KB."""

    @classmethod
    def setUpClass(cls):
        cls.mgr = _build_manager()
        cls.snap = cls.mgr.get_snapshot()

    def test_static_has_buildings_and_regions(self):
        self.assertGreater(len(self.snap.buildings), 0)
        self.assertGreater(len(self.snap.regions), 0)
        self.assertGreater(len(self.snap.resource_nodes), 0)

    def test_world_state_response_has_no_static_fields(self):
        """WorldStateResponse schema should not have buildings/regions/resources."""
        fields = set(WorldStateResponse.model_fields.keys())
        for f in ("buildings", "resource_nodes", "regions", "treasure_chests"):
            self.assertNotIn(f, fields)

    def test_static_data_response_has_all_static_fields(self):
        """StaticDataResponse should have buildings, resources, regions, chests."""
        fields = set(StaticDataResponse.model_fields.keys())
        for f in ("buildings", "resource_nodes", "regions", "treasure_chests"):
            self.assertIn(f, fields)
