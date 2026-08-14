"""Tests for tools/registry_query.py."""

import json
import sys
from pathlib import Path

# Ensure tools/ is importable.
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from registry_query import candidate_tags_from_text, filter_registry  # noqa: E402
from tag_registry import load_registry  # noqa: E402


def _write_fixture_registry(tmp_path, entries):
    reg_dir = tmp_path / "registries"
    reg_dir.mkdir(parents=True, exist_ok=True)
    with (reg_dir / "tag_registry.jsonl").open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def test_candidate_tags_from_seed_vocabulary_matches_substring():
    # No root= passed — reads the real, live registries/tag_registry.jsonl. "faction" is a
    # confirmed-stable seed tag (registered 2026-07-06, append-only registry), so this assertion
    # survives the SEED_TAGS-tuple-to-live-registry swap unmodified; only the mechanism changed.
    tags = candidate_tags_from_text(
        "Extend faction diplomacy", "covers cross-cutting faction discovery", "ai"
    )
    assert "faction" in tags

    assert candidate_tags_from_text("nothing relevant here", "", "") == set()


def test_candidate_tags_from_text_reads_live_registry(tmp_path):
    # AC #2's literal wording: adding a new subsystem-topic tag via the CLI makes it queryable
    # with zero code change. "siege-warfare" is not one of the old SEED_TAGS words.
    _write_fixture_registry(tmp_path, [
        {
            "tag": "siege-warfare",
            "category": "subsystem-topic",
            "added_date": "2026-07-31",
            "note": "fixture",
        },
    ])

    tags = candidate_tags_from_text("a ticket about siege-warfare tactics", root=tmp_path)
    assert "siege-warfare" in tags


def test_candidate_tags_from_text_ignores_non_subsystem_topic_tags(tmp_path):
    # Guards against candidate_tags_from_text silently widening scope to match any registered
    # tag rather than staying scoped to the subsystem-topic seed vocabulary.
    _write_fixture_registry(tmp_path, [
        {
            "tag": "debugging",
            "category": "process-skill-signal",
            "added_date": "2026-07-31",
            "note": "fixture",
        },
        {
            "tag": "meta-review",
            "category": "meta-process",
            "added_date": "2026-07-31",
            "note": "fixture",
        },
    ])

    tags = candidate_tags_from_text("debugging and meta-review both mentioned here", root=tmp_path)
    assert tags == set()


def test_seed_words_still_registered_as_subsystem_topic():
    # TCK-20260720-TAG-TOUCHPOINT-CLEANUP coverage-preservation guard: only 4 of the original 10
    # hardcoded SEED_TAGS words (cognition, faction, social, world) were actually registered
    # before this ticket. The other 6 (combat, economy, resource, content, engine, strategy) were
    # registered as part of this ticket, specifically so removing the SEED_TAGS tuple does not
    # silently narrow prior-work-search coverage.
    registry = load_registry()
    for word in ("combat", "economy", "resource", "content", "engine", "strategy"):
        assert word in registry, f"{word!r} must be registered (was a SEED_TAGS word)"
        assert registry[word]["category"] == "subsystem-topic"


def test_registry_matches_union_layer_and_tags_not_intersection():
    # Ticket entries never carry a `layer` key (tools/generate_registry.py's collect_tickets()
    # never emits one — see investigation.md's Current Behavior section), so the layer-match
    # case below uses a doc entry, which does carry `layer` today.
    layer_match_doc = {"type": "doc", "path": "docs/a.md", "layer": "ai", "tags": []}
    tag_match_entry = {"type": "ticket", "path": "tickets/done/b.md", "tags": ["faction"]}
    no_match_entry = {"type": "ticket", "path": "tickets/done/c.md", "tags": ["unrelated"]}

    entries = [layer_match_doc, tag_match_entry, no_match_entry]

    result = filter_registry(entries, layers=["ai"], candidate_tags={"faction"})
    assert layer_match_doc in result
    assert tag_match_entry in result
    assert no_match_entry not in result

    tags_only_result = filter_registry(entries, layers=None, candidate_tags={"faction"})
    assert tag_match_entry in tags_only_result
    assert layer_match_doc not in tags_only_result


def test_faction_tag_query_surfaces_entries_layer_search_would_miss():
    ai_faction = {"type": "ticket", "path": "tickets/done/a.md", "layer": "ai", "tags": ["faction"]}
    social_faction = {
        "type": "ticket", "path": "tickets/done/b.md", "layer": "social", "tags": ["faction"],
    }
    ai_no_faction = {"type": "ticket", "path": "tickets/done/c.md", "layer": "ai", "tags": []}

    entries = [ai_faction, social_faction, ai_no_faction]

    layer_only_result = filter_registry(entries, layers=["ai"], candidate_tags=None)
    assert social_faction not in layer_only_result

    tag_augmented_result = filter_registry(entries, layers=["ai"], candidate_tags={"faction"})
    assert ai_faction in tag_augmented_result
    assert social_faction in tag_augmented_result
