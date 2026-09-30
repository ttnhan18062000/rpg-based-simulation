"""Tests for tools/test_architecture/impact_report.py (recommendation-only). Synthetic tmp repos; the CI
workflow is copied from the real one so lane names and path filters are the real ones."""

import json
import shutil
import textwrap
from pathlib import Path

import pytest

from tools.test_architecture import impact_report as ir

REPO_ROOT = Path(__file__).resolve().parents[3]


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / ".github/workflows").mkdir(parents=True)
    shutil.copy(REPO_ROOT / ".github/workflows/test.yml", root / ".github/workflows/test.yml")
    _write(root / "src/core/state.py", "X = 1\n")
    _write(root / "src/progression/leveling.py", "from src.core.state import X\n")
    _write(root / "src/engine/combat.py", "from src.core.state import X\n")
    _write(root / "src/systems/economy_core.py", "from src.core.state import X\n")
    _write(root / "src/observability/mon.py", "Y = 1\n")
    _write(root / "tests/unit/progression/test_leveling.py", "from src.progression.leveling import X\n")
    _write(root / "tests/unit/combat/test_combat.py", "from src.engine.combat import X\n")
    _write(root / "tests/mechanic_scenarios/test_world_scn.py", 'WORLD = "scn_world_1"\n')
    return root


def _report(repo, *paths, junit=()):
    return ir.build_impact_report(repo, list(paths), junit)


def test_local_rule_change_maps_to_one_domain_with_reasons_and_shows_untriggered_scenario_lane(repo):
    rep = _report(repo, "src/progression/leveling.py")
    assert list(rep["domains"]) == ["progression"]
    assert rep["domains"]["progression"][0].startswith("src/progression/leveling.py:")
    assert [lv["level"] for lv in rep["levels"]] == ["unit", "kernel_integration", "mechanic_scenario"]
    assert [t["file"] for t in rep["recommended_tests"]] == ["tests/unit/progression/test_leveling.py"]
    lanes = {ln["lane"]: ln["lane_triggered"] for ln in rep["lanes"]["recommended"]}
    # the scenario lane is recommended but the CI path filter would NOT trigger it for src/progression/**
    assert lanes["perf-cert-arena"] == "not-triggered"
    assert lanes["unit-gameplay"] == "always-on"
    assert rep["impact_unknown"] == []
    assert not rep["cross_domain"]


def test_shared_substrate_change_names_dependent_domains(repo):
    rep = _report(repo, "src/core/state.py")
    assert set(rep["domains"]) == {"substrate", "progression", "combat", "economy"}
    assert any("imported by combat code" in r for r in rep["domains"]["combat"])
    assert rep["cross_domain"] is True
    assert "cross_domain_scenario" in [lv["level"] for lv in rep["levels"]]
    assert rep["impact_unknown"] == []


def test_cross_domain_change_recommends_cross_domain_level(repo):
    rep = _report(repo, "src/engine/combat.py", "src/progression/leveling.py")
    assert {"combat", "progression"} <= set(rep["domains"])
    assert rep["cross_domain"] is True
    assert {t["file"] for t in rep["recommended_tests"]} == {
        "tests/unit/combat/test_combat.py", "tests/unit/progression/test_leveling.py"}


def test_content_config_change_selects_scenario_tests_and_migration_lane(repo):
    rep = _report(repo, "data/worlds/scn_world_1/world.yaml")
    assert rep["domains"] == {}
    assert "domain not-derived" in rep["changes"][0]["reason"]
    assert [t["file"] for t in rep["recommended_tests"]] == ["tests/mechanic_scenarios/test_world_scn.py"]
    assert "mechanic_scenario" in [lv["level"] for lv in rep["levels"]]
    lanes = {ln["lane"] for ln in rep["lanes"]["recommended"]}
    assert {"perf-cert-arena", "migration-lanes"} <= lanes
    assert rep["impact_unknown"] == []


def test_unmapped_paths_are_impact_unknown_with_pr_eligible_fallback(repo):
    rep = _report(repo, "src/observability/mon.py", "src/tactical/nav.py", "Dockerfile")
    assert {u["path"] for u in rep["impact_unknown"]} == {
        "src/observability/mon.py", "src/tactical/nav.py", "Dockerfile"}
    assert {"perf-cert-arena", "unit-gameplay", "integration"} <= set(rep["lanes"]["pr_eligible_fallback"])
    assert "slow" in rep["lanes"]["nightly_or_main_only_reported_separately"]
    assert "slow" not in rep["lanes"]["pr_eligible_fallback"]
    assert any("tactical navigation" in g for g in rep["known_gaps"])


def test_docs_only_change_is_not_impact_unknown_and_recommends_nothing(repo):
    rep = _report(repo, "docs/x.md", "tickets/inprogress/T.md")
    assert {c["status"] for c in rep["changes"]} == {"no-runtime-impact-rule"}
    assert rep["impact_unknown"] == [] and rep["recommended_tests"] == [] and rep["levels"] == []


def test_selected_lane_triggered_and_executed_are_separate_facts(repo, tmp_path):
    junit = tmp_path / "run.xml"
    junit.write_text('<testsuites><testsuite><testcase classname="tests.unit.progression.test_leveling" '
                     'name="test_a"/></testsuite></testsuites>', encoding="utf-8")
    rep = _report(repo, "src/progression/leveling.py", junit=[junit])
    t = rep["recommended_tests"][0]
    assert t["selected"] is True
    assert set(t["lane_triggered"].values()) <= {"always-on", "triggered", "not-triggered"}
    (run_id, state), = t["executed"].items()
    assert state == "pass"
    assert _report(repo, "src/progression/leveling.py")["recommended_tests"][0]["executed"] == "not-run"


def test_report_never_removes_a_lane_and_has_no_skip_field(repo):
    rep = _report(repo, "src/progression/leveling.py", "docs/a.md")
    text = json.dumps(rep)
    assert "skip" not in text.replace("Never use this report to skip, remove or narrow", "")
    fast_jobs = {ln["lane"].split("/")[0] for ln in ir.report.parse_lanes(repo / ".github/workflows/test.yml") if ln["fast"]}
    # an impact-unknown change falls back to ALL parsed fast lanes, never fewer
    assert set(_report(repo, "Dockerfile")["lanes"]["pr_eligible_fallback"]) == fast_jobs


def test_module_docstring_states_the_no_skip_limit():
    assert "never be used to skip" in ir.__doc__


def test_cli_exits_zero_and_emits_json(repo, capsys):
    rc = ir.main(["--repo-root", str(repo), "--paths", "src/progression/leveling.py", "--format", "json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["report"] == "impact-report-v0"


def test_doc_read_by_a_test_selects_that_test_though_status_stays_informational(repo):
    _write(repo / "docs/testing/test_taxonomy.md", "vocabulary\n")
    _write(repo / "tools/test_architecture/marker_check.py", 'TAXONOMY_DOC = "docs/testing/test_taxonomy.md"\n')
    _write(repo / "tests/unit/tools/test_marker_vocabulary.py", "from tools.test_architecture import marker_check\n")
    rep = _report(repo, "docs/testing/test_taxonomy.md")
    assert rep["changes"][0]["status"] == "no-runtime-impact-rule"
    assert "test(s) read this path" in rep["changes"][0]["reason"]
    assert [t["file"] for t in rep["recommended_tests"]] == ["tests/unit/tools/test_marker_vocabulary.py"]
    assert rep["recommended_tests"][0]["reasons"] == ["reads docs/testing/test_taxonomy.md"]
    assert rep["impact_unknown"] == []


def test_registry_file_named_directly_by_a_test_selects_it(repo):
    _write(repo / "registries/tag_registry.jsonl", "{}\n")
    _write(repo / "tests/unit/tools/test_tags.py", 'P = "registries/tag_registry.jsonl"\n')
    rep = _report(repo, "registries/tag_registry.jsonl")
    assert [t["file"] for t in rep["recommended_tests"]] == ["tests/unit/tools/test_tags.py"]


def test_parsed_path_filters_add_no_unparsed_gap(repo):
    assert not any("path filters unparsed" in g for g in _report(repo, "src/progression/leveling.py")["known_gaps"])


def test_unparsed_path_filters_are_reported_as_a_known_gap(repo):
    wf = repo / ".github/workflows/test.yml"
    wf.write_text(wf.read_text(encoding="utf-8").replace("_RE=", "_XX="), encoding="utf-8")
    rep = _report(repo, "src/progression/leveling.py")
    assert any("path filters unparsed" in g for g in rep["known_gaps"])


# ── ownership by the law a module implements, and declared markers (core-RPG pilot findings) ──
def test_conservation_module_maps_to_economy_and_substrate_and_recommends_scenario_level(repo):
    """Sample case 6: src/core/conservation.py is the ch03 economic law living in a substrate root. The pilot
    (docs/testing/core_rpg_test_pilot_2026-09-30.md) first saw substrate only, with no scenario level."""
    _write(repo / "src/core/conservation.py", "X = 1\n")
    _write(repo / "src/core/inventory.py", "Y = 1\n")
    _write(repo / "tests/unit/resource/test_conservation.py", "from src.core.conservation import X\n")
    rep = _report(repo, "src/core/conservation.py")
    assert {"economy", "substrate"} <= set(rep["domains"])
    assert rep["changes"][0]["domains"] == ["economy", "substrate"]
    assert "mechanic_scenario" in [lv["level"] for lv in rep["levels"]]
    assert [t["file"] for t in rep["recommended_tests"]] == ["tests/unit/resource/test_conservation.py"]
    inventory = _report(repo, "src/core/inventory.py")
    assert inventory["changes"][0]["domains"] == ["economy", "substrate"]
    # a plain substrate module is unchanged: substrate only, no scenario level
    plain = _report(repo, "src/core/state.py")
    assert plain["changes"][0]["domains"] == ["substrate"]
    assert "mechanic_scenario" not in [lv["level"] for lv in plain["levels"]]


def test_changed_test_declared_markers_add_domain_and_level_beside_other_rules(repo):
    _write(repo / "tests/unit/resource/test_marked.py",
           'import pytest\npytestmark = [pytest.mark.domain("economy"), pytest.mark.level("kernel_integration")]\n')
    rep = _report(repo, "tests/unit/resource/test_marked.py")
    assert rep["changes"][0]["rule"] == "changed-test"
    assert rep["changes"][0]["declared_markers"] == {"domains": ["economy"], "levels": ["kernel_integration"]}
    assert any("declared-marker" in r for r in rep["domains"]["economy"])
    assert [lv["level"] for lv in rep["levels"]] == ["kernel_integration"]
    assert rep["levels"][0]["reason"].startswith("declared-marker:")


def test_declared_markers_never_override_or_duplicate_another_rules_result(repo):
    _write(repo / "src/progression/leveling2.py", "X = 1\n")
    _write(repo / "tests/unit/progression/test_marked2.py",
           'import pytest\npytestmark = [pytest.mark.domain("progression"), pytest.mark.level("unit")]\n')
    rep = _report(repo, "src/progression/leveling2.py", "tests/unit/progression/test_marked2.py")
    assert [lv["level"] for lv in rep["levels"]].count("unit") == 1
    unit = next(lv for lv in rep["levels"] if lv["level"] == "unit")
    assert unit["reason"] == "src component changed"  # the src rule's reason stays
    assert list(rep["domains"]) == ["progression"]


def test_changed_test_without_markers_is_unchanged(repo):
    rep = _report(repo, "tests/unit/progression/test_leveling.py")
    assert "declared_markers" not in rep["changes"][0]
    assert rep["domains"] == {} and rep["levels"] == []
