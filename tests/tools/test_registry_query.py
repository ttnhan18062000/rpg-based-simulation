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


# ---------------------------------------------------------------------------
# CLI entry point (TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT)
# ---------------------------------------------------------------------------

import subprocess

_MODULE_PATH = _TOOLS_DIR / "registry_query.py"


def test_cli_text_mode_prints_readable_output_and_exits_zero(tmp_path):
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--text", "combat and adventure routing"],
        capture_output=True, text=True, cwd=str(_TOOLS_DIR.parent),
    )
    assert result.stdout.strip(), "expected non-empty stdout -- silence is exactly the regression"
    assert result.returncode == 0
    assert "combat" in result.stdout
    assert "adventure" in result.stdout


def test_cli_layers_mode_prints_readable_output_and_exits_zero():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--layers", "observability"],
        capture_output=True, text=True, cwd=str(_TOOLS_DIR.parent),
    )
    assert result.stdout.strip()
    assert result.returncode == 0
    assert "Matched" in result.stdout


def test_cli_no_mode_selected_exits_nonzero_not_silently():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert result.stderr.strip(), "argparse error must be visible, not silent"


def test_cli_help_produces_usage_text_not_silence():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--help"], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_cli_missing_registry_file_exits_nonzero(tmp_path):
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--layers", "ai", "--registry", str(tmp_path / "nope.yaml")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert result.stderr.strip()


def test_cli_still_importable_and_callable_as_plain_functions():
    """Pins the Scope constraint: existing python3 -c call sites
    (candidate_tags_from_text/filter_registry) must keep working unchanged, not routed through
    the new CLI."""
    assert callable(candidate_tags_from_text)
    assert callable(filter_registry)
    result = filter_registry([{"type": "ticket", "path": "x", "layer": "ai", "tags": []}], layers=["ai"])
    assert isinstance(result, list)
