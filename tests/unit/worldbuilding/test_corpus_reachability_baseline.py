"""Standing regression baseline for WORLD-REACH-001 (src/worldbuilding/validator.py's
ParticipantReachabilityRule) against the full real world corpus (data/worlds/*/resolved/
world.resolved.yaml).

The baseline is expected to be non-empty: `RoleDefinition.compatible_traits` (the chosen
matching field, see staging_artifacts/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR/
plan.md) does not cover the `opportunistic` (goblin/bandit quests) or `beast` (wolf quests)
vocabulary used by real authored quest content, and a small number of `spiritual`/`undead`
quests reference archetypes whose actual role trait doesn't match the tag the quest author
chose. This is a documented, accepted content-authoring gap (TCK-20260822-WORLD-GRAMMAR-
REACHABILITY-VALIDATOR out of scope: backfilling catalog content), not a bug in the rule.
A change to this baseline must be a deliberate, reviewed diff -- either real quest-content
authoring fixed the gap, or new content introduced a new one.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.content.repository import CatalogRepository
from src.worldbuilding.schema import load_world_spec_from_yaml
from src.worldbuilding.validator import WorldValidator, ValidationContext

pytestmark = pytest.mark.worldassembly

REPO_ROOT = Path(__file__).resolve().parents[3]
WORLDS_ROOT = REPO_ROOT / "data" / "worlds"
BASELINE_PATH = REPO_ROOT / "tests" / "fixtures" / "world_grammar_reachability_baseline.json"


@pytest.fixture(scope="module")
def catalog_repo() -> CatalogRepository:
    repo = CatalogRepository(str(REPO_ROOT / "data" / "content"))
    repo.load_all()
    return repo


def _resolved_world_paths() -> list[Path]:
    return sorted(WORLDS_ROOT.glob("*/resolved/world.resolved.yaml"))


def test_full_corpus_reachability_regression(catalog_repo):
    world_paths = _resolved_world_paths()
    assert len(world_paths) >= 20, "Expected 20+ real composed worlds under data/worlds/*/resolved/"

    baseline = json.loads(BASELINE_PATH.read_text())

    actual: dict[str, list[str]] = {}
    for resolved_path in world_paths:
        world_id = resolved_path.parent.parent.name
        spec = load_world_spec_from_yaml(resolved_path)
        validator = WorldValidator(catalog_repo=catalog_repo)
        issues = validator.validate(spec, context=ValidationContext.WORLD)
        violating_quest_ids = sorted(
            issue.source_entity for issue in issues if issue.rule_id == "WORLD-REACH-001"
        )
        if violating_quest_ids:
            actual[world_id] = violating_quest_ids

    assert actual == baseline, (
        "WORLD-REACH-001 corpus violation set drifted from the committed baseline "
        f"({BASELINE_PATH}). If this is a deliberate content/catalog change, update the "
        "baseline file as a reviewed diff -- do not silently regenerate it."
    )
