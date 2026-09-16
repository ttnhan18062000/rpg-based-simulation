"""Tests for priority derivation and chart generation.

TCK-20260915-MECHANISM-PRIORITY-DERIVATION (child of TCK-20260915-EPIC-MECHANISM-REGISTRY, depends
on TCK-20260915-MECHANISM-REGISTRY-FOUNDATION and TCK-20260915-MECHANISM-VERIFICATION-AXIS).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.mechanism_registry import (
    DependencyCycleError,
    priority,
    transitive_dependencies_of,
    transitive_dependents,
    unverified_priority_ranking,
)
from tools.generate_mechanism_charts import (
    _MAX_CHART_NODES,
    render_ancestors_chart,
    render_layer_chart,
    render_top_n_chart,
    render_top_n_table,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"


@pytest.fixture(scope="module")
def registry_data():
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _count_mermaid_nodes(diagram: str) -> int:
    """Counts real node declarations (lines of the form `id["label"]...`), excluding classDef
    lines, edge lines, and comments."""
    count = 0
    for line in diagram.splitlines():
        stripped = line.strip()
        if stripped.startswith("classDef") or stripped.startswith("flowchart") or stripped.startswith("%%"):
            continue
        if "-->" in stripped:
            continue
        if '["' in stripped:
            count += 1
    return count


# ── Priority derivation ──────────────────────────────────────────────────────────────────────


def test_transitive_dependents_matches_real_data(registry_data):
    # Re-derived from the real committed registry every run, not a hardcoded assumption --
    # regenerate this if the registry's own edges genuinely change. 23 -> 24 after
    # TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION added party_formation -> movement (cited:
    # cooperation/services.py's real regroup-distance check) -- movement itself already depended on
    # action_pacing_readiness, so party_formation became a new transitive dependent.
    dep_map = {m["id"]: m.get("depends_on") or [] for m in registry_data["mechanisms"]}
    assert len(transitive_dependents("action_pacing_readiness", dep_map)) == 24


def test_transitive_dependents_raises_on_cycle():
    dep_map = {"a": ["b"], "b": ["a"]}
    with pytest.raises(DependencyCycleError):
        transitive_dependents("a", dep_map)


def test_transitive_dependents_raises_on_longer_cycle():
    dep_map = {"a": ["b"], "b": ["c"], "c": ["a"]}
    with pytest.raises(DependencyCycleError):
        transitive_dependents("a", dep_map)


def test_transitive_dependencies_of_raises_on_cycle():
    dep_map = {"a": ["b"], "b": ["a"]}
    with pytest.raises(DependencyCycleError):
        transitive_dependencies_of("a", dep_map)


def test_priority_is_weight_times_transitive_dependents():
    dep_map = {"hub": [], "leaf1": ["hub"], "leaf2": ["hub"]}
    layers = {"faction": {"cadence": "daily", "rank": 3, "weight": 3}}
    assert priority("hub", dep_map, "faction", layers) == 3 * 2  # weight 3 * 2 dependents


def test_priority_uses_weight_not_rank():
    """TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED regression: a layer with a HIGH rank
    (rare) but LOW weight must NOT out-prioritize a layer with a LOW rank (frequent) but HIGH
    weight -- proves the function reads `weight`, not `rank`, by giving them opposite orderings."""
    dep_map = {"hub": [], "leaf1": ["hub"], "leaf2": ["hub"], "leaf3": ["hub"]}
    layers = {
        "rare_but_light": {"cadence": "rare", "rank": 5, "weight": 1},
        "frequent_and_heavy": {"cadence": "per_tick", "rank": 1, "weight": 5},
    }
    rare_priority = priority("hub", dep_map, "rare_but_light", layers)
    frequent_priority = priority("hub", dep_map, "frequent_and_heavy", layers)
    assert frequent_priority > rare_priority
    assert rare_priority == 1 * 3
    assert frequent_priority == 5 * 3


def test_unverified_priority_ranking_excludes_verified_mechanisms():
    data = {
        "layers": {"entity": {"cadence": "per_tick", "rank": 1, "weight": 5}},
        "mechanisms": [
            {"id": "verified_one", "layer": "entity", "state": "done", "depends_on": [],
             "verified": {"instrument": "code_trace", "verdict": "observed", "date": "2026-09-16", "note": "x"}},
            {"id": "unverified_one", "layer": "entity", "state": "gap", "depends_on": []},
        ],
    }
    ranking = unverified_priority_ranking(data)
    ids = [r["id"] for r in ranking]
    assert "unverified_one" in ids
    assert "verified_one" not in ids


def test_unverified_priority_ranking_orders_by_priority_descending():
    data = {
        "layers": {
            "entity": {"cadence": "per_tick", "rank": 1, "weight": 5},
            "faction": {"cadence": "daily", "rank": 3, "weight": 3},
        },
        "mechanisms": [
            {"id": "hub", "layer": "faction", "state": "done", "depends_on": []},
            {"id": "leaf1", "layer": "entity", "state": "done", "depends_on": ["hub"]},
            {"id": "leaf2", "layer": "entity", "state": "done", "depends_on": ["hub"]},
        ],
    }
    ranking = unverified_priority_ranking(data)
    assert ranking[0]["id"] == "hub"  # weight 3 * 2 dependents = 6, beats the two leaves' 0 each


def test_real_registry_favors_frequent_layer_over_rare_layer(registry_data):
    """TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED regression, on real data. Computed via
    priority() directly (not unverified_priority_ranking()) so this test stays valid regardless of
    which mechanisms later get a verified block -- it must keep holding on the registry's raw
    state/layer/dependents shape, not on any two mechanisms' current verified status."""
    layers = registry_data["layers"]
    dep_map = {m["id"]: m.get("depends_on") or [] for m in registry_data["mechanisms"]}
    by_id = {m["id"]: m for m in registry_data["mechanisms"]}

    entity_mech = by_id["action_pacing_readiness"]  # entity layer, 23 transitive dependents
    faction_mech = by_id["betrayal_siege_war"]  # faction layer, 11 transitive dependents

    entity_priority = priority(entity_mech["id"], dep_map, entity_mech["layer"], layers)
    faction_priority = priority(faction_mech["id"], dep_map, faction_mech["layer"], layers)

    assert entity_priority > faction_priority, (
        "action_pacing_readiness (entity, per-tick, more dependents) must outrank "
        "betrayal_siege_war (faction, rare, fewer dependents) -- if it doesn't, the layer weight "
        "direction has regressed back to rewarding rare layers"
    )


def test_real_registry_top_unverified_row_is_not_faction_war(registry_data):
    """Companion regression check: whichever mechanism currently ranks #1 unverified, it must not
    be the deliberately deprioritized betrayal_siege_war -- checked by name explicitly, since a
    silent regression back to rank-based weighting would put it there again."""
    ranking = unverified_priority_ranking(registry_data)
    top_ids = [r["id"] for r in ranking[:3]]
    assert "betrayal_siege_war" not in top_ids, (
        "betrayal_siege_war (deliberately deprioritized faction war) must not rank in the top 3 "
        "unverified mechanisms -- if it does, the layer weight direction has regressed"
    )


# ── Chart generation ──────────────────────────────────────────────────────────────────────────


def test_chart_generator_single_layer_paginates_when_over_threshold(registry_data):
    pages = render_layer_chart(registry_data, "entity")
    assert len(pages) > 1, "entity layer (43 mechanisms) must paginate past the 40-node threshold"


def test_chart_generator_single_layer_no_pagination_for_small_layer(registry_data):
    pages = render_layer_chart(registry_data, "group")  # 2 mechanisms
    assert len(pages) == 1


def test_chart_generator_ancestors_of_produces_a_real_subgraph(registry_data):
    diagram = render_ancestors_chart(registry_data, "combat_resolution")
    assert "combat_resolution" in diagram
    assert "tactical_decision" in diagram
    assert "combat_engagement" in diagram
    assert "action_pacing_readiness" in diagram


def test_chart_generator_ancestors_of_unknown_mechanism_raises(registry_data):
    with pytest.raises(KeyError):
        render_ancestors_chart(registry_data, "nonexistent_mechanism_xyz")


def test_chart_generator_ancestors_of_fails_loudly_over_threshold():
    mechs = [
        {"id": f"m{i}", "layer": "entity", "state": "done",
         "depends_on": [f"m{i + 1}"] if i < 44 else []}
        for i in range(45)
    ]
    data = {"layers": {"entity": {"cadence": "per_tick", "rank": 1}}, "mechanisms": mechs}
    with pytest.raises(ValueError):
        render_ancestors_chart(data, "m0")


def test_chart_generator_never_emits_a_diagram_over_the_threshold(registry_data):
    for page in render_layer_chart(registry_data, "entity"):
        assert _count_mermaid_nodes(page) <= _MAX_CHART_NODES
    for layer in registry_data["layers"]:
        for page in render_layer_chart(registry_data, layer):
            assert _count_mermaid_nodes(page) <= _MAX_CHART_NODES
    top_n_diagram = render_top_n_chart(registry_data, n=100)  # deliberately over threshold
    assert _count_mermaid_nodes(top_n_diagram) <= _MAX_CHART_NODES


def test_direction_is_a_parameter_not_hardcoded(registry_data):
    diagram_bt = render_ancestors_chart(registry_data, "combat_resolution", direction="BT")
    diagram_tb = render_ancestors_chart(registry_data, "combat_resolution", direction="TB")
    assert "flowchart BT" in diagram_bt
    assert "flowchart TB" in diagram_tb


def test_top_n_table_matches_ranking(registry_data):
    table = render_top_n_table(registry_data, n=3)
    ranking = unverified_priority_ranking(registry_data)[:3]
    for row in ranking:
        assert row["id"] in table


def test_wiring_map_classdef_check_script_passes_on_real_files():
    result = subprocess.run(
        [sys.executable, "tools/mechanism_wiring_map_classdef.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_make_target_generates_priority_view():
    result = subprocess.run(
        ["make", "mechanism-priority-view"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    check = subprocess.run(
        [sys.executable, "tools/generate_mechanism_priority_view.py", "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert check.returncode == 0, check.stdout + check.stderr


def test_generator_check_mode_detects_staleness(tmp_path):
    stale_output = tmp_path / "stale_priority_view.md"
    stale_output.write_text("not the real generated content\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "tools/generate_mechanism_priority_view.py",
         "--output", str(stale_output), "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert "STALE" in result.stdout


def test_makefile_wires_priority_targets():
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "mechanism-priority-view:" in makefile_text
    assert "mechanism-wiring-map-classdef-check:" in makefile_text
