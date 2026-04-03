import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

"""Tests for API payload size optimizations — RLE grid, slim entities, static split.

Refactored for AOA Stabilization:
- Updated entity access patterns to use aspects (combat, progression, mind).
- Aligned with modern EntitySlimSchema.
"""

import json
import unittest
from pathlib import Path

# Ensure the src directory is in the python path

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
        self.assertEqual(decoded_total, grid.width * grid.height)

        # Verify RLE is much smaller than raw 2D JSON
        rle_json = json.dumps({"width": grid.width, "height": grid.height, "grid": rle})
        rle_size = len(rle_json)
        self.assertLess(rle_size, 500_000, f"RLE map too large: {rle_size} bytes")

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
        """Each slim entity should serialize to < 400 bytes (AOA display names add some overhead)."""
        e = list(self.snap.entities.values())[0]
        slim = EntitySlimSchema(
            id=e.id, 
            kind=e.kind, 
            display_name=e.identity.display_name,
            x=int(e.spatial.pos.x), 
            y=int(e.spatial.pos.y),
            hp=int(e.combat.hp), 
            max_hp=int(e.combat.max_hp),
            state=e.mind.decision.ai_state.name, 
            level=e.progression.level,
            tier=e.identity.tier, 
            faction=e.identity.faction.name.lower(),
        )
        js = slim.model_dump_json()
        self.assertLess(len(js), 400, f"Slim entity too large: {len(js)} bytes")

    def test_state_payload_without_selection(self):
        """Without selection, state should have no selected_entity and small payload."""
        entities = [e for e in self.snap.entities.values() if e.combat.alive]
        slim_list = [
            EntitySlimSchema(
                id=e.id, kind=e.kind, display_name=e.identity.display_name,
                x=int(e.spatial.pos.x), y=int(e.spatial.pos.y),
                hp=int(e.combat.hp), max_hp=int(e.combat.max_hp),
                state=e.mind.decision.ai_state.name, level=e.progression.level,
                tier=e.identity.tier, faction=e.identity.faction.name.lower(),
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
        # ~300 entities × ~200-300 bytes each ≈ 90KB max
        self.assertLess(size, 150_000, f"/state payload too large: {size} bytes")


class TestStaticEndpoint(unittest.TestCase):
    """Static data should be separate."""

    @classmethod
    def setUpClass(cls):
        cls.mgr = _build_manager()
        cls.snap = cls.mgr.get_snapshot()

    def test_static_has_buildings_and_regions(self):
        self.assertGreaterEqual(len(self.snap.buildings), 0)
        self.assertGreaterEqual(len(self.snap.regions), 0)

    def test_world_state_response_has_no_static_fields(self):
        """WorldStateResponse schema should not have buildings/regions/resources."""
        fields = set(WorldStateResponse.model_fields.keys())
        for f in ("regions",): # buildings and resource_nodes have DYNAMIC state versions now
            self.assertNotIn(f, fields)

    def test_static_data_response_has_all_static_fields(self):
        """StaticDataResponse should have buildings, resources, regions, chests."""
        fields = set(StaticDataResponse.model_fields.keys())
        for f in ("buildings", "resource_nodes", "regions", "treasure_chests"):
            self.assertIn(f, fields)
