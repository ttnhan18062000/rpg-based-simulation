"""
Tests for tools/add_frontmatter_live.py

Groups:
  1. classify_engine — historical pattern matching
  2. classify_engine — active (no historical pattern)
  3. classify_combat — m7 active, m1-m6 historical, matrix historical
  4. classify_observability — known active stems, phase docs historical
  5. classify_performance — known active stems, date-prefixed historical
  6. classify_test_coverage — all historical
  7. has_frontmatter — detection
  8. build_frontmatter — output structure
  9. process_file — skips existing, modifies new, preserves content
  10. Idempotency — second call returns skipped, no duplication
  11. get_fields — directory routing
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

from tools.add_frontmatter_live import (  # noqa: E402
    build_frontmatter,
    classify_combat,
    classify_engine,
    classify_observability,
    classify_performance,
    classify_test_coverage,
    get_fields,
    has_frontmatter,
    process_file,
)


# ---------------------------------------------------------------------------
# Group 1: classify_engine — historical pattern
# ---------------------------------------------------------------------------

class TestClassifyEngineHistorical:
    def test_phase_entry_package(self):
        r = classify_engine("phase7_entry_package.md")
        assert r["status"] == "historical"
        assert r["authority"] == "P2"
        assert r["layer"] == "engine"

    def test_phase_exit_package(self):
        r = classify_engine("phase11_exit_package.md")
        assert r["status"] == "historical"

    def test_phase_proof_bundle(self):
        r = classify_engine("phase5_proof_bundle.md")
        assert r["status"] == "historical"

    def test_phase_closure_report(self):
        r = classify_engine("phase10_closure_report.md")
        assert r["status"] == "historical"

    def test_phase_readiness_gate(self):
        r = classify_engine("phase5_readiness_gate.md")
        assert r["status"] == "historical"

    def test_phase_backlog(self):
        r = classify_engine("phase7_backlog.md")
        assert r["status"] == "historical"

    def test_mx_test_matrix(self):
        r = classify_engine("m4_test_matrix.md")
        assert r["status"] == "historical"

    def test_ma_test_matrix(self):
        r = classify_engine("ma_test_matrix.md")
        assert r["status"] == "historical"

    def test_me_test_matrix(self):
        r = classify_engine("me_test_matrix.md")
        assert r["status"] == "historical"

    def test_m4_work_model_matrix(self):
        r = classify_engine("m4_work_model_matrix.md")
        assert r["status"] == "historical"

    def test_m3_retention_matrix(self):
        r = classify_engine("m3_retention_matrix.md")
        assert r["status"] == "historical"

    def test_legacy_replacement_ledger(self):
        r = classify_engine("legacy_replacement_ledger.md")
        assert r["status"] == "historical"

    def test_remaining_replacement_scope(self):
        r = classify_engine("remaining_replacement_scope.md")
        assert r["status"] == "historical"

    def test_unsupported_register(self):
        r = classify_engine("unsupported_register.md")
        assert r["status"] == "historical"

    def test_src_v2_inventory(self):
        r = classify_engine("src_v2_inventory.md")
        assert r["status"] == "historical"

    def test_sweep_configuration(self):
        r = classify_engine("sweep_configuration.md")
        assert r["status"] == "historical"

    def test_attach_gate(self):
        r = classify_engine("attach_gate1_movement_scope.md")
        assert r["status"] == "historical"

    def test_differential_gap_report(self):
        r = classify_engine("phase6_differential_gap_report.md")
        assert r["status"] == "historical"

    def test_phase13_retirement_manifest(self):
        r = classify_engine("phase13_retirement_manifest.md")
        assert r["status"] == "historical"

    def test_phase11_non_preserved_baseline(self):
        r = classify_engine("phase11_non_preserved_baseline.md")
        assert r["status"] == "historical"

    def test_boundary_notes(self):
        r = classify_engine("phase10_boundary_notes.md")
        assert r["status"] == "historical"


# ---------------------------------------------------------------------------
# Group 2: classify_engine — active
# ---------------------------------------------------------------------------

class TestClassifyEngineActive:
    def test_kernel(self):
        r = classify_engine("kernel.md")
        assert r["status"] == "active"
        assert r["authority"] == "P1"
        assert r["layer"] == "engine"

    def test_authoritative_pipeline(self):
        r = classify_engine("authoritative_pipeline.md")
        assert r["status"] == "active"

    def test_governance_logic(self):
        r = classify_engine("governance_logic.md")
        assert r["status"] == "active"

    def test_performance_contract(self):
        r = classify_engine("performance_contract.md")
        assert r["status"] == "active"

    def test_known_limitations(self):
        r = classify_engine("known_limitations.md")
        assert r["status"] == "active"

    def test_project_lawbook_m10(self):
        r = classify_engine("project_lawbook_m10.md")
        assert r["status"] == "active"

    def test_engineering_playbook_m10(self):
        r = classify_engine("engineering_playbook_m10.md")
        assert r["status"] == "active"

    def test_minimal_kernel_m2(self):
        # Contains "m2" but is a spec doc — no _matrix or phase prefix
        r = classify_engine("minimal_kernel_m2.md")
        assert r["status"] == "active"

    def test_simulation_kernel_contract_m1(self):
        # m1 appears mid-name as a suffix — not a matrix pattern
        r = classify_engine("simulation_kernel_contract_m1.md")
        assert r["status"] == "active"

    def test_scheduler_contract_m4(self):
        r = classify_engine("scheduler_contract_m4.md")
        assert r["status"] == "active"

    def test_certification_contract_m9(self):
        r = classify_engine("certification_contract_m9.md")
        assert r["status"] == "active"

    def test_combat_contract(self):
        r = classify_engine("combat_contract.md")
        assert r["status"] == "active"

    def test_tactical_contract(self):
        r = classify_engine("tactical_contract.md")
        assert r["status"] == "active"

    def test_readme(self):
        r = classify_engine("README.md")
        assert r["status"] == "active"

    def test_v2_verification_design(self):
        r = classify_engine("v2_verification_design.md")
        assert r["status"] == "active"

    def test_phase_dependency_map(self):
        # Contains "phase_" but no digit suffix — not caught by historical pattern
        r = classify_engine("phase_dependency_map.md")
        assert r["status"] == "active"
        assert r["layer"] == "engine"

    def test_phase_allocation_map(self):
        r = classify_engine("phase_allocation_map.md")
        assert r["status"] == "active"


# ---------------------------------------------------------------------------
# Group 3: classify_combat
# ---------------------------------------------------------------------------

class TestClassifyCombat:
    def test_m7_observability_rulebook_active(self):
        r = classify_combat("observability_rulebook_m7.md")
        assert r["status"] == "active"
        assert r["authority"] == "P1"
        assert r["layer"] == "combat"

    def test_m7_rollout_hardening_active(self):
        r = classify_combat("rollout_hardening_rulebook_m7.md")
        assert r["status"] == "active"

    def test_overhaul_spec_active(self):
        r = classify_combat("combat_movement_overhaul_spec.md")
        assert r["status"] == "active"

    def test_m1_rulebook_historical(self):
        r = classify_combat("combat_movement_rulebook_m1.md")
        assert r["status"] == "historical"
        assert r["authority"] == "P2"

    def test_m1_test_matrix_historical(self):
        r = classify_combat("combat_movement_m1_test_matrix.md")
        assert r["status"] == "historical"

    def test_m4_tactical_historical(self):
        r = classify_combat("tactical_behavior_rulebook_m4.md")
        assert r["status"] == "historical"

    def test_m6_arena_harness_historical(self):
        r = classify_combat("arena_harness_rulebook_m6.md")
        assert r["status"] == "historical"

    def test_m6_regression_matrix_historical(self):
        r = classify_combat("arena_regression_m6_test_matrix.md")
        assert r["status"] == "historical"

    def test_m6_scenario_matrix_historical(self):
        r = classify_combat("arena_scenario_matrix_m6.md")
        assert r["status"] == "historical"


# ---------------------------------------------------------------------------
# Group 4: classify_observability
# ---------------------------------------------------------------------------

class TestClassifyObservability:
    def test_hard_law_monitor_active(self):
        r = classify_observability("hard_law_monitor.md")
        assert r["status"] == "active"
        assert r["authority"] == "P1"
        assert r["layer"] == "observability"

    def test_how_to_run_simulation_active(self):
        r = classify_observability("how_to_run_simulation.md")
        assert r["status"] == "active"

    def test_loki_label_policy_active(self):
        r = classify_observability("loki_label_policy.md")
        assert r["status"] == "active"

    def test_prometheus_metrics_active(self):
        r = classify_observability("prometheus_metrics.md")
        assert r["status"] == "active"

    def test_phase_1_historical(self):
        r = classify_observability("phase_1.md")
        assert r["status"] == "historical"
        assert r["authority"] == "P2"

    def test_phase_9_usage_historical(self):
        r = classify_observability("phase_9_usage.md")
        assert r["status"] == "historical"

    def test_phase_14_agentic_lab_historical(self):
        r = classify_observability("phase_14_agentic_lab.md")
        assert r["status"] == "historical"

    def test_phase_3_historical(self):
        r = classify_observability("phase_3.md")
        assert r["status"] == "historical"


# ---------------------------------------------------------------------------
# Group 5: classify_performance
# ---------------------------------------------------------------------------

class TestClassifyPerformance:
    def test_optimization_architecture_active(self):
        r = classify_performance("optimization_architecture.md")
        assert r["status"] == "active"
        assert r["authority"] == "P1"
        assert r["layer"] == "performance"

    def test_optimization_invariants_active(self):
        r = classify_performance("optimization_invariants.md")
        assert r["status"] == "active"

    def test_perf_baseline_policy_active(self):
        r = classify_performance("perf_baseline_policy.md")
        assert r["status"] == "active"

    def test_date_prefixed_report_historical(self):
        r = classify_performance("2026-05-13-v2-performance-hardening-report.md")
        assert r["status"] == "historical"
        assert r["authority"] == "P2"

    def test_date_prefixed_phase6_historical(self):
        r = classify_performance("2026-05-14-v2-performance-hardening-report-phase6.md")
        assert r["status"] == "historical"

    def test_date_prefixed_milestone10_historical(self):
        r = classify_performance("2026-05-15-v2-performance-hardening-report-milestone10.md")
        assert r["status"] == "historical"

    def test_date_prefixed_milestones_1_14_historical(self):
        r = classify_performance("2026-05-18-v2-performance-hardening-report-milestones-1-14.md")
        assert r["status"] == "historical"

    def test_performance_report_api_historical(self):
        r = classify_performance("performance-report-api-payload.md")
        assert r["status"] == "historical"

    def test_performance_report_epic16_historical(self):
        r = classify_performance("performance-report-epic16.md")
        assert r["status"] == "historical"

    def test_performance_report_rendering_historical(self):
        r = classify_performance("performance-report-rendering.md")
        assert r["status"] == "historical"


# ---------------------------------------------------------------------------
# Group 6: classify_test_coverage — all historical
# ---------------------------------------------------------------------------

class TestClassifyTestCoverage:
    def test_phase10_coverage_historical(self):
        r = classify_test_coverage("phase10_optimization_scaling_coverage.md")
        assert r["status"] == "historical"
        assert r["authority"] == "P2"
        assert r["layer"] == "testing"

    def test_phase2_self_model_coverage_historical(self):
        r = classify_test_coverage("phase2_self_model_coverage.md")
        assert r["status"] == "historical"

    def test_phase19_28_observability_coverage_historical(self):
        r = classify_test_coverage("phase19_28_observability_coverage.md")
        assert r["status"] == "historical"

    def test_any_file_historical(self):
        r = classify_test_coverage("some_future_coverage_report.md")
        assert r["status"] == "historical"


# ---------------------------------------------------------------------------
# Group 7: has_frontmatter
# ---------------------------------------------------------------------------

class TestHasFrontmatter:
    def test_bare_content_returns_false(self):
        assert not has_frontmatter("# Heading\n\nContent.\n")

    def test_frontmatter_at_start_returns_true(self):
        assert has_frontmatter("---\nstatus: active\n---\n\n# Heading\n")

    def test_frontmatter_not_at_start_returns_false(self):
        assert not has_frontmatter("\n---\nstatus: active\n---\n")

    def test_empty_string_returns_false(self):
        assert not has_frontmatter("")


# ---------------------------------------------------------------------------
# Group 8: build_frontmatter
# ---------------------------------------------------------------------------

class TestBuildFrontmatter:
    def test_active_doc_structure(self):
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        fm = build_frontmatter(fields)
        assert fm.startswith("---\n")
        assert "status: active" in fm
        assert "layer: engine" in fm
        assert "authority: P1" in fm
        assert "audience: developer" in fm
        assert fm.strip().endswith("---")

    def test_authoritative_includes_last_verified(self):
        fields = dict(status="authoritative", authority="P0", layer="mechanics",
                      audience="developer", last_verified="2026-06-06")
        fm = build_frontmatter(fields)
        assert "last_verified: 2026-06-06" in fm

    def test_active_does_not_include_last_verified(self):
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        fm = build_frontmatter(fields)
        assert "last_verified" not in fm

    def test_historical_does_not_include_last_verified(self):
        fields = dict(status="historical", authority="P2", layer="engine", audience="developer")
        fm = build_frontmatter(fields)
        assert "last_verified" not in fm

    def test_ends_with_fence_newline(self):
        fields = dict(status="active", authority="P1", layer="misc", audience="developer")
        fm = build_frontmatter(fields)
        assert fm.endswith("---\n")

    def test_fence_count(self):
        fields = dict(status="active", authority="P1", layer="misc", audience="developer")
        fm = build_frontmatter(fields)
        assert fm.count("---") == 2


# ---------------------------------------------------------------------------
# Group 9: process_file
# ---------------------------------------------------------------------------

class TestProcessFile:
    def test_modifies_bare_file(self, tmp_path):
        md = tmp_path / "kernel.md"
        md.write_text("# Kernel\n\nContent.\n", encoding="utf-8")
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        result = process_file(md, fields)
        assert result == "modified"

    def test_modified_file_starts_with_fence(self, tmp_path):
        md = tmp_path / "kernel.md"
        md.write_text("# Kernel\n", encoding="utf-8")
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        process_file(md, fields)
        assert md.read_text(encoding="utf-8").startswith("---\n")

    def test_original_content_preserved(self, tmp_path):
        md = tmp_path / "governance_logic.md"
        original = "# Governance\n\nLaw content.\n"
        md.write_text(original, encoding="utf-8")
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        process_file(md, fields)
        content = md.read_text(encoding="utf-8")
        assert "# Governance" in content
        assert "Law content." in content

    def test_skips_file_with_frontmatter(self, tmp_path):
        md = tmp_path / "already_done.md"
        existing = "---\nstatus: active\nlayer: engine\n---\n\n# Doc\n"
        md.write_text(existing, encoding="utf-8")
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        result = process_file(md, fields)
        assert result == "skipped"
        assert md.read_text(encoding="utf-8") == existing

    def test_authoritative_frontmatter_has_last_verified(self, tmp_path):
        md = tmp_path / "01_entity_anatomy.md"
        md.write_text("# Entity Anatomy\n", encoding="utf-8")
        fields = dict(status="authoritative", authority="P0", layer="mechanics",
                      audience="developer", last_verified="2026-06-06")
        process_file(md, fields)
        content = md.read_text(encoding="utf-8")
        assert "last_verified: 2026-06-06" in content
        assert "status: authoritative" in content
        assert "authority: P0" in content


# ---------------------------------------------------------------------------
# Group 10: Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_second_run_returns_skipped(self, tmp_path):
        md = tmp_path / "kernel.md"
        md.write_text("# Kernel\n", encoding="utf-8")
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        first = process_file(md, fields)
        second = process_file(md, fields)
        assert first == "modified"
        assert second == "skipped"

    def test_content_unchanged_after_second_run(self, tmp_path):
        md = tmp_path / "governance_logic.md"
        md.write_text("# Governance\n", encoding="utf-8")
        fields = dict(status="active", authority="P1", layer="engine", audience="developer")
        process_file(md, fields)
        after_first = md.read_text(encoding="utf-8")
        process_file(md, fields)
        after_second = md.read_text(encoding="utf-8")
        assert after_first == after_second

    def test_fence_appears_exactly_once(self, tmp_path):
        md = tmp_path / "01_entity_anatomy.md"
        md.write_text("# Entity Anatomy\n", encoding="utf-8")
        fields = dict(status="authoritative", authority="P0", layer="mechanics",
                      audience="developer", last_verified="2026-06-06")
        process_file(md, fields)
        process_file(md, fields)
        content = md.read_text(encoding="utf-8")
        assert content.count("status: authoritative") == 1
        assert content.count("---") == 2

    def test_idempotency_on_authoritative_file(self, tmp_path):
        md = tmp_path / "state.md"
        md.write_text("# State\n", encoding="utf-8")
        fields = dict(status="authoritative", authority="P0", layer="core",
                      audience="developer", last_verified="2026-06-06")
        process_file(md, fields)
        process_file(md, fields)
        content = md.read_text(encoding="utf-8")
        assert content.count("last_verified") == 1


# ---------------------------------------------------------------------------
# Group 11: get_fields — directory routing
# ---------------------------------------------------------------------------

class TestGetFields:
    def test_mechanics_dir_authoritative_p0(self):
        f = get_fields(Path("docs/mechanics/01_entity_anatomy.md"))
        assert f["status"] == "authoritative"
        assert f["authority"] == "P0"
        assert f["layer"] == "mechanics"
        assert f["last_verified"] == "2026-06-06"

    def test_core_dir_authoritative_p0(self):
        f = get_fields(Path("docs/core/state.md"))
        assert f["status"] == "authoritative"
        assert f["authority"] == "P0"
        assert f["layer"] == "core"

    def test_architecture_dir_active_p1(self):
        f = get_fields(Path("docs/architecture/adr-004.md"))
        assert f["status"] == "active"
        assert f["authority"] == "P1"
        assert f["layer"] == "architecture"

    def test_systems_dir_active(self):
        f = get_fields(Path("docs/systems/combat_and_progression.md"))
        assert f["status"] == "active"
        assert f["layer"] == "systems"

    def test_strategy_dir_active(self):
        f = get_fields(Path("docs/strategy/bounded_cognition.md"))
        assert f["layer"] == "strategy"

    def test_compliance_dir_active(self):
        f = get_fields(Path("docs/compliance/checklist.md"))
        assert f["layer"] == "compliance"

    def test_ai_dir_active(self):
        f = get_fields(Path("docs/ai/agents.md"))
        assert f["layer"] == "ai"

    def test_guidelines_dir_active(self):
        f = get_fields(Path("docs/guidelines/design_patterns.md"))
        assert f["layer"] == "guidelines"

    def test_testing_dir_active(self):
        f = get_fields(Path("docs/testing/v2_test_taxonomy.md"))
        assert f["layer"] == "testing"
        assert f["status"] == "active"

    def test_engine_heuristic_active_contract(self):
        f = get_fields(Path("docs/engine/kernel.md"))
        assert f["status"] == "active"
        assert f["layer"] == "engine"

    def test_engine_heuristic_historical_phase(self):
        f = get_fields(Path("docs/engine/phase7_entry_package.md"))
        assert f["status"] == "historical"
        assert f["layer"] == "engine"

    def test_combat_heuristic_m7_active(self):
        f = get_fields(Path("docs/combat/observability_rulebook_m7.md"))
        assert f["status"] == "active"
        assert f["layer"] == "combat"

    def test_combat_heuristic_m1_historical(self):
        f = get_fields(Path("docs/combat/combat_movement_rulebook_m1.md"))
        assert f["status"] == "historical"

    def test_observability_heuristic_active(self):
        f = get_fields(Path("docs/observability/hard_law_monitor.md"))
        assert f["status"] == "active"
        assert f["layer"] == "observability"

    def test_observability_heuristic_historical(self):
        f = get_fields(Path("docs/observability/phase_1.md"))
        assert f["status"] == "historical"

    def test_performance_heuristic_active(self):
        f = get_fields(Path("docs/performance/optimization_architecture.md"))
        assert f["status"] == "active"
        assert f["layer"] == "performance"

    def test_performance_heuristic_historical(self):
        f = get_fields(Path("docs/performance/2026-05-13-v2-performance-hardening-report.md"))
        assert f["status"] == "historical"

    def test_test_coverage_always_historical(self):
        f = get_fields(Path("docs/test_coverage/phase10_optimization_scaling_coverage.md"))
        assert f["status"] == "historical"
        assert f["layer"] == "testing"

    def test_loose_readme(self):
        f = get_fields(Path("docs/README.md"))
        assert f["status"] == "active"
        assert f["layer"] == "misc"

    def test_loose_optimization_audit_ledger(self):
        f = get_fields(Path("docs/optimization_audit_ledger.md"))
        assert f["layer"] == "performance"
