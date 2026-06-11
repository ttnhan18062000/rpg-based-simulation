"""
Tests for tools/add_frontmatter_archive.py

Groups:
  1. infer_layer — keyword coverage per category
  2. infer_layer — misc fallback
  3. extract_date — date present / absent
  4. has_frontmatter — detection
  5. build_frontmatter — correct output structure
  6. process_file — modifies bare files, skips files with existing frontmatter
  7. Idempotency — running process_file twice produces no duplication
"""

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.add_frontmatter_archive import (  # noqa: E402
    build_frontmatter,
    extract_date,
    has_frontmatter,
    infer_layer,
    process_file,
)


# ---------------------------------------------------------------------------
# Group 1: infer_layer — keyword coverage per category
# ---------------------------------------------------------------------------

class TestInferLayerKeywords:
    def test_combat_keyword(self):
        assert infer_layer("combat_movement_finalized.md") == "combat"

    def test_combat_battle_keyword(self):
        assert infer_layer("battle_system_design.md") == "combat"

    def test_combat_damage_keyword(self):
        assert infer_layer("damage_formula_v2.md") == "combat"

    def test_movement_keyword(self):
        assert infer_layer("movement_pathfinding_overview.md") == "movement"

    def test_economy_resource_keyword(self):
        assert infer_layer("resource_handbook.md") == "economy"

    def test_economy_crafting_keyword(self):
        assert infer_layer("crafting_system_spec.md") == "economy"

    def test_economy_trade_keyword(self):
        assert infer_layer("trade_routes_design.md") == "economy"

    def test_strategy_keyword(self):
        assert infer_layer("strategy_implementation_milestone_1.md") == "strategy"

    def test_strategy_strat_substring(self):
        # STRAT-KNOWLEDGE-UNIFICATION must resolve via 'strat' substring
        assert infer_layer("STRAT-KNOWLEDGE-UNIFICATION.md") == "strategy"

    def test_strategy_cognition_keyword(self):
        assert infer_layer("cognition_overview.md") == "strategy"

    def test_strategy_intel_keyword(self):
        assert infer_layer("intel_capacity_implementation.md") == "strategy"

    def test_world_keyword(self):
        assert infer_layer("world_phase_20_28.md") == "world"

    def test_world_region_keyword(self):
        assert infer_layer("region_sovereignty_spec.md") == "world"

    def test_world_ecology_keyword(self):
        assert infer_layer("ecology_biome_analysis.md") == "world"

    def test_core_entity_keyword(self):
        assert infer_layer("entity_enhance_phase1.md") == "core"

    def test_core_aspect_keyword(self):
        assert infer_layer("aspect_oriented_design.md") == "core"

    def test_observability_keyword(self):
        assert infer_layer("observability_memory_issue.md") == "observability"

    def test_observability_profiling_keyword(self):
        assert infer_layer("profiling_performance_overview.md") == "observability"

    def test_observability_monitor_keyword(self):
        assert infer_layer("monitor_worker_leak.md") == "observability"

    def test_performance_keyword(self):
        assert infer_layer("performance_benchmark_results.md") == "performance"

    def test_performance_perf_keyword(self):
        assert infer_layer("perf_optimization_notes.md") == "performance"

    def test_performance_optimiz_keyword(self):
        assert infer_layer("optimization_pass_3.md") == "performance"

    def test_testing_test_keyword(self):
        assert infer_layer("test_base_rework_plan.md") == "testing"

    def test_testing_coverage_keyword(self):
        assert infer_layer("coverage_gap_analysis.md") == "testing"

    def test_engine_engine_keyword(self):
        assert infer_layer("engine_design_overview.md") == "engine"

    def test_engine_kernel_keyword(self):
        assert infer_layer("kernel_loop_spec.md") == "engine"

    def test_engine_pipeline_keyword(self):
        assert infer_layer("pipeline_phase_contract.md") == "engine"

    def test_simulation_keyword(self):
        assert infer_layer("simulation_run_replay.md") == "simulation"

    def test_simulation_sim_keyword(self):
        # "sim" matches simulation; note that if "test" also appears it takes precedence
        # since testing is checked before simulation in the keyword map.
        assert infer_layer("sim_replay_overview.md") == "simulation"


# ---------------------------------------------------------------------------
# Group 2: infer_layer — misc fallback
# ---------------------------------------------------------------------------

class TestInferLayerMisc:
    def test_pitch_falls_to_misc(self):
        assert infer_layer("pitch.md") == "misc"

    def test_proposal_falls_to_misc(self):
        assert infer_layer("poposal.md") == "misc"

    def test_questions_falls_to_misc(self):
        assert infer_layer("questions.md") == "misc"

    def test_repair_falls_to_misc(self):
        assert infer_layer("repair_implementation.md") == "misc"

    def test_overhaul_falls_to_misc(self):
        assert infer_layer("overhaul_spec.md") == "misc"

    def test_empty_name_falls_to_misc(self):
        assert infer_layer("") == "misc"


# ---------------------------------------------------------------------------
# Group 3: extract_date — date present / absent
# ---------------------------------------------------------------------------

class TestExtractDate:
    def test_date_at_start_of_filename(self):
        assert extract_date("2026-03-20-aspect-oriented-modularization-design.md") == "2026-03-20"

    def test_date_at_start_no_trailing_dash(self):
        assert extract_date("2026-04-16-strategic-repair-design.md") == "2026-04-16"

    def test_no_date_returns_unknown(self):
        assert extract_date("combat_movement_finalized.md") == "unknown"

    def test_partial_date_no_match(self):
        # Only year present — no YYYY-MM-DD match
        assert extract_date("2026_overview.md") == "unknown"

    def test_date_embedded_mid_filename(self):
        # Only the leading YYYY-MM-DD pattern is matched (re.match anchors at start)
        assert extract_date("design_2026-04-01_notes.md") == "unknown"


# ---------------------------------------------------------------------------
# Group 4: has_frontmatter — detection
# ---------------------------------------------------------------------------

class TestHasFrontmatter:
    def test_bare_content_returns_false(self):
        assert not has_frontmatter("# Some heading\n\nContent here.\n")

    def test_frontmatter_at_start_returns_true(self):
        assert has_frontmatter("---\nstatus: archive\n---\n\n# Heading\n")

    def test_frontmatter_not_at_start_returns_false(self):
        # dash block mid-file should not trigger
        assert not has_frontmatter("\n---\nstatus: archive\n---\n")

    def test_empty_content_returns_false(self):
        assert not has_frontmatter("")


# ---------------------------------------------------------------------------
# Group 5: build_frontmatter — output structure
# ---------------------------------------------------------------------------

class TestBuildFrontmatter:
    def test_includes_status_archive(self):
        fm = build_frontmatter("combat_movement_finalized.md")
        assert "status: archive" in fm

    def test_includes_authority_p2(self):
        fm = build_frontmatter("combat_movement_finalized.md")
        assert "authority: P2" in fm

    def test_includes_audience_historical(self):
        fm = build_frontmatter("combat_movement_finalized.md")
        assert "audience: historical" in fm

    def test_includes_inferred_layer(self):
        fm = build_frontmatter("combat_movement_finalized.md")
        assert "layer: combat" in fm

    def test_includes_original_date_when_present(self):
        fm = build_frontmatter("2026-03-20-centralized-logging-design.md")
        assert "original_date: 2026-03-20" in fm

    def test_includes_original_date_unknown_when_absent(self):
        fm = build_frontmatter("combat_movement_finalized.md")
        assert "original_date: unknown" in fm

    def test_starts_and_ends_with_fence(self):
        fm = build_frontmatter("pitch.md")
        assert fm.startswith("---\n")
        assert "---\n" in fm[4:]  # closing fence must exist

    def test_misc_layer_for_unknown_file(self):
        fm = build_frontmatter("pitch.md")
        assert "layer: misc" in fm


# ---------------------------------------------------------------------------
# Group 6: process_file — modifies bare file, skips file with frontmatter
# ---------------------------------------------------------------------------

class TestProcessFile:
    def test_prepends_frontmatter_to_bare_file(self, tmp_path):
        md = tmp_path / "resource_handbook.md"
        original = "# Resource Handbook\n\nSome content.\n"
        md.write_text(original, encoding="utf-8")

        result = process_file(md)

        assert result == "modified"
        content = md.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert "# Resource Handbook" in content
        assert "Some content." in content

    def test_skips_file_with_existing_frontmatter(self, tmp_path):
        md = tmp_path / "already_done.md"
        existing = "---\nstatus: archive\nlayer: misc\noriginal_date: 2026-01-01\n---\n\n# Doc\n"
        md.write_text(existing, encoding="utf-8")

        result = process_file(md)

        assert result == "skipped"
        # Content must be unchanged
        assert md.read_text(encoding="utf-8") == existing

    def test_original_content_preserved_after_modification(self, tmp_path):
        md = tmp_path / "world_phase_20_28.md"
        original = "# World Phase\n\nDetailed notes.\n"
        md.write_text(original, encoding="utf-8")

        process_file(md)

        content = md.read_text(encoding="utf-8")
        # Original content must be intact after the frontmatter block
        assert "# World Phase" in content
        assert "Detailed notes." in content

    def test_layer_inferred_from_filename(self, tmp_path):
        md = tmp_path / "strategy_implementation_milestone_1.md"
        md.write_text("# Strategy\n", encoding="utf-8")
        process_file(md)
        content = md.read_text(encoding="utf-8")
        assert "layer: strategy" in content

    def test_date_extracted_from_filename(self, tmp_path):
        md = tmp_path / "2026-04-16-strategic-repair-design.md"
        md.write_text("# Repair\n", encoding="utf-8")
        process_file(md)
        content = md.read_text(encoding="utf-8")
        assert "original_date: 2026-04-16" in content


# ---------------------------------------------------------------------------
# Group 7: Idempotency — running process_file twice produces no duplication
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_second_run_does_not_duplicate_frontmatter(self, tmp_path):
        md = tmp_path / "resource_phase4.md"
        original = "# Resource Phase 4\n\nContent.\n"
        md.write_text(original, encoding="utf-8")

        result_first = process_file(md)
        content_after_first = md.read_text(encoding="utf-8")

        result_second = process_file(md)
        content_after_second = md.read_text(encoding="utf-8")

        assert result_first == "modified"
        assert result_second == "skipped"
        assert content_after_first == content_after_second

    def test_second_run_result_is_skipped(self, tmp_path):
        md = tmp_path / "pitch.md"
        md.write_text("# Pitch\n", encoding="utf-8")
        process_file(md)
        assert process_file(md) == "skipped"

    def test_frontmatter_appears_exactly_once(self, tmp_path):
        md = tmp_path / "combat_movement_finalized.md"
        md.write_text("# Combat\n", encoding="utf-8")
        process_file(md)
        process_file(md)
        content = md.read_text(encoding="utf-8")
        assert content.count("status: archive") == 1
        assert content.count("---") == 2  # opening and closing fence only
