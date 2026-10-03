"""Tests for tools/perf/phase_inventory.py (TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT).

The real pipeline is only checked for "parses, non-empty, duplicate-free ordinals": RPG-core changes
the phase count on purpose, so no test here may assert a fixed real count.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.perf import phase_inventory as pi

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "perf" / "phase_inventory.py"

SYNTHETIC = '''
class AuthoritativeApplyPipeline:
    @staticmethod
    def refine(state, update, cadence=None):
        if cadence is None:
            update = replace(update, force_full_scan=True)

        def run_phase(phase_name, upd, phase_fn, feature_flag=None):
            return phase_fn(upd)

        update = run_phase("alpha", update, lambda u: AlphaSystem.apply(state, u))
        update = run_phase("beta", update, lambda u: u.merge(BetaPhase.apply(state)), "ENABLE_BETA")
        if state.tick % 2 == 0:
            update = run_phase("gamma", update, lambda u: Pipeline._gamma(state, u))
        for region in state.regions:
            update = run_phase(f"region_{region}", update, helper_fn, feature_flag=FLAG_NAME)
        update = update.merge(DirectSystem.resolve(state, update))
        FaithService.derive(state)
        update = run_phase("delta", update, lambda u: DeltaSystem.run(state, u)[0])
        return update
'''


def _names(inv):
    return [c["name"] for c in inv["run_phase_calls"]]


class TestPipelineInventory:
    def test_calls_in_source_order_with_ordinals(self):
        inv = pi.inventory_pipeline(SYNTHETIC)
        assert inv["found"] is True
        assert _names(inv) == ["alpha", "beta", "gamma", None, "delta"]
        assert [c["ordinal"] for c in inv["run_phase_calls"]] == [1, 2, 3, 4, 5]

    def test_flag_dispatch_and_lambda_argument_methods_are_skipped(self):
        inv = pi.inventory_pipeline(SYNTHETIC)
        by = {c["ordinal"]: c for c in inv["run_phase_calls"]}
        assert by[1]["feature_flag"] is None
        assert by[1]["dispatch"] == "AlphaSystem.apply"
        assert by[2]["feature_flag"] == "ENABLE_BETA"
        assert by[2]["dispatch"] == "BetaPhase.apply"  # u.merge(...) is skipped, not reported
        assert by[3]["dispatch"] == "Pipeline._gamma"
        assert by[5]["dispatch"] == "DeltaSystem.run"  # subscript wrapper is looked through

    def test_conditional_and_loop_context(self):
        inv = pi.inventory_pipeline(SYNTHETIC)
        by = {c["ordinal"]: c for c in inv["run_phase_calls"]}
        assert by[1]["conditional_or_loop"] is False
        assert by[3]["conditional_or_loop"] is True and by[3]["context"][0].startswith("if@L")
        assert by[4]["context"][0].startswith("for@L")
        assert inv["summary"]["conditional_or_loop_calls"] == 2

    def test_dynamic_name_is_listed_with_its_expression(self):
        inv = pi.inventory_pipeline(SYNTHETIC)
        dyn = inv["run_phase_calls"][3]
        assert dyn["name"] is None and dyn["name_dynamic"] is True
        assert "region_" in dyn["name_expression"]
        assert dyn["feature_flag"] == "FLAG_NAME"  # keyword argument, non-literal expression
        assert dyn["dispatch"] == "helper_fn"      # bare name, not a lambda
        assert inv["summary"]["dynamic_name_calls"] == 1

    def test_direct_operations_are_a_separate_category(self):
        inv = pi.inventory_pipeline(SYNTHETIC)
        ops = [d["operation"] for d in inv["direct_operations"]]
        assert ops == ["replace", "update.merge"]  # FaithService.derive is a call, not an assignment to update
        assert inv["direct_operations"][0]["conditional_or_loop"] is True
        assert inv["direct_operations"][1]["conditional_or_loop"] is False
        assert inv["summary"]["direct_operations"] == 2
        # a run_phase assignment is never double counted as a direct operation
        assert "alpha" not in ops

    def test_direct_class_method_calls_exclude_run_phase_lambdas_and_nested_defs(self):
        inv = pi.inventory_pipeline(SYNTHETIC)
        calls = [d["call"] for d in inv["direct_calls"]]
        # DirectSystem.resolve and FaithService.derive are made by refine() itself; AlphaSystem.apply,
        # BetaPhase.apply, DeltaSystem.run sit inside lambdas and are dispatch targets, not direct calls.
        assert calls == ["DirectSystem.resolve", "FaithService.derive"]
        assert inv["summary"]["direct_calls"] == 2

    def test_duplicate_names_are_reported(self):
        src = SYNTHETIC.replace('"delta"', '"alpha"')
        assert pi.inventory_pipeline(src)["summary"]["duplicate_names"] == ["alpha"]

    def test_missing_method_reports_not_found(self):
        inv = pi.inventory_pipeline("class Other:\n    pass\n")
        assert inv["found"] is False and inv["run_phase_calls"] == []


class TestDocumentExtractors:
    def test_pipeline_doc_heading_and_table(self):
        text = (
            "## The 2 Phases of Refinement\n\n| # | Phase Name | x |\n| :-- | :-- | :-- |\n"
            "| 1 | `alpha` | a |\n| 2 | `beta` | b |\n"
        )
        got = pi.extract_pipeline_doc(text)
        assert got == {"stated_count": 2, "stated_in": "heading 'The N Phases of Refinement'", "entries": ["alpha", "beta"]}

    def test_pipeline_doc_without_heading_reports_no_count(self):
        got = pi.extract_pipeline_doc("| 1 | `alpha` | a |\n")
        assert got["stated_count"] is None and got["entries"] == ["alpha"]

    def test_d19_part_a_rows_and_summary_total(self):
        text = (
            "## Part A\n| PP-01 | `alpha` | X |\n| PP-02 | `beta` | X |\n"
            "## Part B\n| PP-03 | `ignored` | X |\n"
            "| `pipeline.py:refine()` | 38 | 30 |\n"
        )
        got = pi.extract_d19_doc(text)
        assert got["entries"] == ["alpha", "beta"] and got["stated_count"] == 38

    def test_generator_note_count_only(self):
        got = pi.extract_generator_note('_AUTHORITATIVE_PIPELINE_NOTE = "refined through the 39-phase pipeline"\n')
        assert got["stated_count"] == 39 and got["entries"] == []

    def test_epic_counts_mixed_and_single(self):
        assert pi.extract_epic_counts("the 37 sub-phases and 37 Resolution phases")["stated_count"] == 37
        mixed = pi.extract_epic_counts("37 sub-phases but 39 Resolution phases")
        assert mixed["stated_count"] is None and mixed["stated_counts_seen"] == [37, 39]

    def test_compare_source_names_the_difference(self):
        got = pi.compare_source(
            "doc", "doc.md",
            {"stated_count": 2, "stated_in": "x", "entries": ["alpha", "old"]},
            ["alpha", "beta"],
        )
        assert got["executable_phases_without_entry"] == ["beta"]
        assert got["entries_matching_no_executable_phase"] == ["old"]

    def test_unreadable_source_is_reported_not_guessed(self):
        got = pi.compare_source("doc", "missing.md", None, ["alpha"], "FileNotFoundError")
        assert got == {"id": "doc", "path": "missing.md", "readable": False, "read_error": "FileNotFoundError"}


class TestDeclarations:
    def test_graph_names_and_permission_keys_parse_without_import(self):
        graph = 'class PhaseDependencyGraph:\n    PHASES = {"alpha": 1, "compactor": 2}\n'
        perms = "PHASE_READ_DOMAINS = {TickPhase.INIT: 1, TickPhase.RESOLUTION: 2}\nPHASE_WRITE_DOMAINS = {TickPhase.INIT: 1}\n"
        assert pi.extract_dependency_graph_names(graph) == ["alpha", "compactor"]
        assert pi.extract_domain_permission_keys(perms) == ["INIT", "RESOLUTION"]

    def test_compare_declarations_both_directions(self):
        got = pi.compare_declarations(["alpha", "beta"], ["alpha", "compactor"], ["INIT"])
        assert got["dependency_graph"]["in_pipeline_not_in_graph"] == ["beta"]
        assert got["dependency_graph"]["in_graph_not_in_pipeline"] == ["compactor"]
        assert got["domain_permissions"]["pipeline_names_matching_a_key"] == []


def _swap_lines(src: str, first_marker: str, second_marker: str) -> str:
    """Swap the two source lines that contain the given markers."""
    lines = src.split("\n")
    i = next(n for n, line in enumerate(lines) if first_marker in line)
    j = next(n for n, line in enumerate(lines) if second_marker in line)
    lines[i], lines[j] = lines[j], lines[i]
    return "\n".join(lines)


def _make_repo(tmp_path: Path, pipeline_src: str) -> Path:
    (tmp_path / "src" / "engine").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "engine" / "pipeline.py").write_text(pipeline_src, encoding="utf-8")
    return tmp_path


class TestReportAndCheck:
    def test_output_is_deterministic_and_has_no_timestamp(self, tmp_path):
        root = _make_repo(tmp_path, SYNTHETIC)
        first = pi.to_json(pi.build_report(root))
        second = pi.to_json(pi.build_report(root))
        assert first == second
        assert "generated" not in first.lower() and "timestamp" not in first.lower()

    def test_missing_documents_are_reported_unreadable(self, tmp_path):
        report = pi.build_report(_make_repo(tmp_path, SYNTHETIC))
        assert all(s["readable"] is False for s in report["documented_sources"])

    def test_check_passes_on_unchanged_tree(self, tmp_path):
        root = _make_repo(tmp_path, SYNTHETIC)
        committed = tmp_path / "committed.json"
        committed.write_text(pi.to_json(pi.build_report(root)), encoding="utf-8")
        code, diff = pi.check_against(committed, pi.build_report(root))
        assert (code, diff) == (0, [])

    def test_check_ignores_pure_line_number_shifts(self, tmp_path):
        root = _make_repo(tmp_path, SYNTHETIC)
        committed = tmp_path / "committed.json"
        committed.write_text(pi.to_json(pi.build_report(root)), encoding="utf-8")
        _make_repo(tmp_path, "# a new leading comment\n\n" + SYNTHETIC)
        assert pi.check_against(committed, pi.build_report(tmp_path))[0] == 0

    @pytest.mark.parametrize(
        "mutate, expected",
        [
            (lambda s: s.replace('        update = run_phase("delta"', '        update = run_phase("epsilon", update, lambda u: E.run(u))\n        update = run_phase("delta"'),
             "phase added: epsilon"),
            (lambda s: s.replace('        update = run_phase("delta", update, lambda u: DeltaSystem.run(state, u)[0])\n', ""),
             "phase removed: delta"),
            (lambda s: _swap_lines(s, 'update = run_phase("alpha"', 'update = run_phase("beta"'),
             "phase reordered"),
        ],
    )
    def test_check_fails_naming_the_phase(self, tmp_path, mutate, expected):
        root = _make_repo(tmp_path, SYNTHETIC)
        committed = tmp_path / "committed.json"
        committed.write_text(pi.to_json(pi.build_report(root)), encoding="utf-8")
        _make_repo(tmp_path, mutate(SYNTHETIC))
        code, diff = pi.check_against(committed, pi.build_report(tmp_path))
        assert code == 1
        assert any(expected in line for line in diff), diff

    def test_check_with_unreadable_committed_file_is_an_error_not_a_pass(self, tmp_path):
        code, diff = pi.check_against(tmp_path / "nope.json", {})
        assert code == 2 and diff

    def test_markdown_header_states_commit_and_regeneration_command(self, tmp_path):
        report = pi.build_report(_make_repo(tmp_path, SYNTHETIC))
        md = pi.to_markdown(report, "abc1234")
        assert md.startswith("---\n") and "layer: performance" in md
        assert "commit `abc1234`" in md
        assert "python3 tools/perf/phase_inventory.py --format md" in md


class TestRealPipeline:
    def test_script_parses_real_pipeline_without_importing_src(self):
        # Run as a subprocess: if the tool imported engine code, `src` would appear in sys.modules.
        probe = (
            "import runpy, sys, json\n"
            "sys.argv = ['phase_inventory.py', '--format', 'json']\n"
            "import io, contextlib\n"
            "buf = io.StringIO()\n"
            "with contextlib.redirect_stdout(buf):\n"
            "    try:\n"
            "        runpy.run_path('tools/perf/phase_inventory.py', run_name='__main__')\n"
            "    except SystemExit:\n"
            "        pass\n"
            "assert not any(m == 'src' or m.startswith('src.') for m in sys.modules), 'engine code was imported'\n"
            "json.loads(buf.getvalue())\n"
        )
        done = subprocess.run([sys.executable, "-c", probe], cwd=REPO_ROOT, capture_output=True, text=True)
        assert done.returncode == 0, done.stderr

    def test_real_pipeline_has_nonempty_duplicate_free_ordinals(self):
        report = pi.build_report(REPO_ROOT)
        calls = report["pipeline"]["run_phase_calls"]
        assert report["pipeline"]["found"] is True
        assert calls, "no run_phase() calls found in refine"
        ordinals = [c["ordinal"] for c in calls]
        assert ordinals == list(range(1, len(calls) + 1))
        assert len(set(ordinals)) == len(ordinals)

    def test_cli_json_is_byte_identical_across_runs(self):
        cmd = [sys.executable, str(SCRIPT), "--format", "json"]
        a = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        b = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        assert a == b and json.loads(a)["pipeline"]["found"] is True

    def test_cli_check_exit_codes(self, tmp_path):
        good = tmp_path / "good.json"
        subprocess.run([sys.executable, str(SCRIPT), "--format", "json"], cwd=REPO_ROOT, check=True,
                       stdout=good.open("w"))
        ok = subprocess.run([sys.executable, str(SCRIPT), "--check", str(good)], cwd=REPO_ROOT, capture_output=True, text=True)
        assert ok.returncode == 0, ok.stderr
        data = json.loads(good.read_text())
        data["pipeline"]["run_phase_calls"].pop()
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        failed = subprocess.run([sys.executable, str(SCRIPT), "--check", str(bad)], cwd=REPO_ROOT, capture_output=True, text=True)
        assert failed.returncode == 1 and "phase added" in failed.stderr
