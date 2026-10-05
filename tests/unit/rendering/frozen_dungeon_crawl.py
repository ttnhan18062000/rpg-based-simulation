"""Loader for the frozen pre-balance-fix `dungeon_crawl` snapshot used by rendering-evidence tests.

See the header of tests/fixtures/rendering/dungeon_crawl_pre_balance_fix.resolved.yaml for why it is
frozen and what that costs.
"""
from pathlib import Path

from src.worldbuilding.schema import WorldSpec, load_world_spec_from_yaml

FROZEN_DUNGEON_CRAWL_PATH = (
    Path(__file__).resolve().parents[2] / "fixtures" / "rendering" / "dungeon_crawl_pre_balance_fix.resolved.yaml"
)


def load_frozen_dungeon_crawl() -> WorldSpec:
    return load_world_spec_from_yaml(FROZEN_DUNGEON_CRAWL_PATH)
