"""Tests for tools/registry_query.py."""

import sys
from pathlib import Path

# Ensure tools/ is importable.
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from registry_query import candidate_tags_from_text, filter_registry  # noqa: E402


def test_candidate_tags_from_seed_vocabulary_matches_substring():
    tags = candidate_tags_from_text(
        "Extend faction diplomacy", "covers cross-cutting faction discovery", "ai"
    )
    assert "faction" in tags

    assert candidate_tags_from_text("nothing relevant here", "", "") == set()


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
