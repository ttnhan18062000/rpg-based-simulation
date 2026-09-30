"""Tests for tools/test_architecture/core_rpg_report.py (report-only producer).

All fixtures are synthetic and built under tmp_path, so nothing depends on live repo content except
the one smoke test at the end.
"""

import datetime as dt
import hashlib
import json
import textwrap
from pathlib import Path

import pytest

from tools.test_architecture import core_rpg_report as report

AS_OF = dt.date(2026, 9, 30)
REPO_ROOT = Path(__file__).resolve().parents[3]


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def repo(tmp_path):
    """A minimal repo: 4 test files (one per classification), a workflow, registry, tickets, ledger."""
    root = tmp_path / "repo"
    # both signals -> classified
    _write(root / "tests/unit/combat/test_a.py", "from src.engine.combat import x\n")
    # directory signal only -> uncertain
    _write(root / "tests/unit/quest/test_b.py", "import os\n")
    # import signal only -> uncertain
    _write(root / "tests/unit/misc/test_c.py", "from src.economy import y\n")
    # neither -> not-core-rpg (substrate-only import)
    _write(root / "tests/unit/other/test_d.py", "from src.core.state import s\n")
    _write(root / ".github/workflows/test.yml", """\
        jobs:
          unit-gameplay:
            steps:
              - name: "Run"
                run: |
                  pytest tests/unit/combat \\
                         tests/unit/quest \\
                         -m "not slow and not extra_slow" -q \\
                         --junit-xml=reports/junit/unit-gameplay.xml
              - name: "Upload"
                uses: actions/upload-artifact@v4
                with:
                  name: j
                  path: reports/junit/unit-*.xml
          slow:
            steps:
              - name: "Slow"
                run: pytest tests/ -m "slow or extra_slow"
          base-diff:
            steps:
              - name: "Collect"
                run: pytest tests/unit/combat --collect-only -q
        """)
    _write(root / "registries/tag_registry.jsonl",
           '{"added_date": "2026-08-15", "category": "process-skill-signal", "note": "n", "tag": "escaped-defect"}\n')
    _write(root / "tickets/done/TCK-1.md",
           "---\nticket_id: TCK-1\ndate: 2026-09-10\ntags: [testing, escaped-defect]\n---\n\nFailure class: never-fires\n")
    _write(root / "tickets/done/TCK-2.md", "---\nticket_id: TCK-2\ndate: 2026-09-11\ntags: [testing]\n---\n")
    _write(root / "docs/parity_ledger/x.yaml", "- id: A\n  status: verified\n- id: B\n  status: missing\n")
    return root


def _junit(path: Path, cases) -> Path:
    body = "".join(
        f'<testcase classname="{c}" name="{n}">{extra}</testcase>' for c, n, extra in cases
    )
    path.write_text(f'<testsuites><testsuite name="pytest">{body}</testsuite></testsuites>', encoding="utf-8")
    return path


def _build(repo, junit=(), coverage=None):
    return report.build_report(repo, "abc123", AS_OF, junit, coverage)


# ── determinism ──
def test_same_inputs_give_byte_identical_json(repo, tmp_path):
    junit = _junit(tmp_path / "run.xml", [("tests.unit.combat.test_a", "test_x", "")])
    first = report.to_json(_build(repo, [junit]))
    second = report.to_json(_build(repo, [junit]))
    assert first == second
    assert first.encode().decode() == first  # plain, encodable text


def test_output_contains_no_absolute_paths(repo, tmp_path):
    junit = _junit(tmp_path / "run.xml", [("tests.unit.combat.test_a", "test_x", "")])
    text = report.to_json(_build(repo, [junit]))
    assert str(tmp_path) not in text
    assert str(repo) not in text


# ── classification ──
def test_classification_states_and_denominators(repo):
    layer = _build(repo)["layers"]["classification"]
    assert layer["denominator"] == {"test_files": 4}
    assert layer["counts"] == {"classified": 1, "uncertain": 2, "unowned-domain": 0, "not-core-rpg": 1,
                               "parse-error": 0}
    assert layer["signal_disagreement"] == {"directory_only": 1, "import_only": 1}
    assert layer["substrate_only_import_files"] == 1


@pytest.mark.parametrize("import_line", [
    "from src.engine.pipeline import run",          # shared substrate (ownership map, section 3.1)
    "from src.engine.kernel import Kernel",
    "from src.engine.pipeline_phases.x import y",   # pipeline* stem
    "import src.platform.config",
])
def test_substrate_imports_are_not_a_gameplay_signal(repo, import_line):
    _write(repo / "tests/unit/misc/test_sub.py", import_line + "\n")
    rec = next(r for r in report.scan_tests(repo) if r["file"].endswith("test_sub.py"))
    assert rec["import_signal"] is False
    assert rec["class"] == "not-core-rpg"


@pytest.mark.parametrize("import_line", [
    "from src.systems.crafting import x",            # module name is `crafting`, not `craft`
    "from src.systems.harvest_system import x",      # `harvest_system` matches the `harvest*` stem
    "from src.systems.guild_system import x",
    "from src.systems.economy_systems.economy import x",
    "from src.engine.movement import x",
    "from src.domains.combat_engagement.x import y",
])
def test_gameplay_component_roots_match_by_module_stem(repo, import_line):
    _write(repo / "tests/unit/misc/test_gp.py", import_line + "\n")
    rec = next(r for r in report.scan_tests(repo) if r["file"].endswith("test_gp.py"))
    assert rec["import_signal"] is True
    assert rec["class"] == "uncertain"  # import signal only: no directory signal


def test_party_only_imports_are_unowned_domain_not_a_candidate(repo):
    _write(repo / "tests/unit/misc/test_party.py", "from src.systems.party import Party\n")
    layer = _build(repo)["layers"]
    assert layer["classification"]["counts"]["unowned-domain"] == 1
    assert "tests/unit/misc/test_party.py" not in {f["file"] for f in layer["execution"]["files"]}
    # party plus a real gameplay import is still judged on the gameplay signal
    _write(repo / "tests/unit/misc/test_both.py", "from src.systems.party import P\nfrom src.economy import e\n")
    rec = next(r for r in report.scan_tests(repo) if r["file"].endswith("test_both.py"))
    assert rec["class"] == "uncertain"


def test_unparseable_test_file_is_reported_not_dropped(repo):
    _write(repo / "tests/unit/combat/test_broken.py", "def (:\n")
    layer = _build(repo)["layers"]["classification"]
    assert layer["counts"]["parse-error"] == 1
    assert layer["denominator"]["test_files"] == 5


# ── execution: three distinct states ──
def test_no_junit_artifact_is_its_own_state(repo):
    layer = _build(repo)["layers"]["execution"]
    assert layer["state"] == "no-junit-artifact"
    assert {f["state"] for f in layer["files"]} == {"no-junit-artifact"}
    assert layer["runs"] == []


def test_not_run_and_outcome_states_are_distinct(repo, tmp_path):
    junit = _junit(tmp_path / "run.xml", [
        ("tests.unit.combat.test_a", "test_ok", ""),
        ("tests.unit.combat.test_a", "test_bad", "<failure>boom</failure>"),
    ])
    layer = _build(repo, [junit])["layers"]["execution"]
    assert layer["state"] == "junit-supplied"
    run_id = layer["runs"][0]["run_id"]
    by_file = {f["file"]: f["runs"][run_id]["state"] for f in layer["files"]}
    # test_a is in the JUnit (outcome), test_b/test_c are candidates absent from it (not-run)
    assert by_file["tests/unit/combat/test_a.py"] == "fail"
    assert by_file["tests/unit/quest/test_b.py"] == "not-run"
    assert by_file["tests/unit/misc/test_c.py"] == "not-run"
    assert layer["summary"][run_id] == {"pass": 0, "fail": 1, "skipped": 0, "not-run": 2, "denominator": 3}
    # the three states never collapse into one another
    assert len({"no-junit-artifact", "not-run", "fail"}) == 3


def test_separate_runs_keep_their_own_results_and_run_ids(repo, tmp_path):
    ok = _junit(tmp_path / "a.xml", [("tests.unit.combat.test_a", "t", "")])
    bad = _junit(tmp_path / "b.xml", [("tests.unit.combat.test_a", "t", "<failure/>")])
    layer = _build(repo, [ok, bad])["layers"]["execution"]
    ids = [r["run_id"] for r in layer["runs"]]
    assert len(set(ids)) == 2
    entry = next(f for f in layer["files"] if f["file"] == "tests/unit/combat/test_a.py")
    assert {entry["runs"][i]["state"] for i in ids} == {"pass", "fail"}


def test_failing_tests_are_listed_and_unmapped_cases_are_counted(repo, tmp_path):
    junit = _junit(tmp_path / "run.xml", [
        ("tests.unit.combat.test_a.TestC", "test_bad", "<error/>"),
        ("tests.unknown.test_z", "test_q", ""),
    ])
    run = _build(repo, [junit])["layers"]["execution"]["runs"][0]
    assert run["failing_tests"] == ["tests/unit/combat/test_a.py::TestC::test_bad"]
    assert run["unmapped_testcases"] == 1
    assert run["outcomes"]["errors"] == 1


# ── coverage ──
def test_no_coverage_artifact_when_none_supplied(repo):
    layer = _build(repo)["layers"]["coverage"]
    assert layer["state"] == "no-coverage-artifact"
    assert layer["package_coverage"] == {}
    assert layer["domain_coverage"]["state"] == "not-derived"


def test_supplied_coverage_is_package_level_and_provisional(repo, tmp_path):
    cov = tmp_path / "cov.json"
    cov.write_text(json.dumps({"files": {
        "src/core/a.py": {"summary": {"num_statements": 10, "covered_lines": 5}},
        "src/core/b.py": {"summary": {"num_statements": 10, "covered_lines": 10}},
        "src/engine/c.py": {"summary": {"num_statements": 4, "covered_lines": 1}},
    }}), encoding="utf-8")
    layer = _build(repo, coverage=cov)["layers"]["coverage"]
    assert layer["state"] == "provisional-local"
    assert layer["package_coverage"]["core"]["line_pct"] == 75.0
    assert layer["package_coverage"]["engine"]["line_pct"] == 25.0
    assert layer["package_coverage"]["core"]["branch_pct"] is None  # no branches recorded -> not 0
    assert layer["denominator"]["statements"] == 24
    assert layer["domain_coverage"]["state"] == "not-derived"


# ── lanes ──
def test_lanes_parse_paths_marker_junit_and_upload(repo):
    layer = _build(repo)["layers"]["lanes"]
    steps = {s["lane"]: s for s in layer["lane_steps"]}
    gameplay = steps["unit-gameplay/Run"]
    assert gameplay["paths"] == ["tests/unit/combat", "tests/unit/quest"]
    assert gameplay["fast"] and gameplay["junit_uploaded"]
    assert steps["slow/Slow"]["fast"] is False
    assert not any("base-diff" in lane for lane in steps)  # --collect-only commands are not lanes


def test_file_without_a_fast_lane_is_reported_as_such(repo):
    layer = _build(repo)["layers"]["lanes"]
    states = {f["file"]: f["state"] for f in layer["files"]}
    assert states["tests/unit/combat/test_a.py"] == "covered"
    assert states["tests/unit/misc/test_c.py"] == "no-fast-lane"
    assert layer["denominator"]["core_rpg_candidate_files"] == 3
    assert "triggers" in layer["not_derived"]


# ── mutation ──
def _mutation_record(repo: Path, started="2026-09-29T16:07:35Z", days=30, target_text="x = 1\n"):
    target = _write(repo / "src/core/conservation.py", target_text)
    record = {
        "target": {"path": "src/core/conservation.py", "sha256": _sha(target)},
        "run": {"kind": "real-target", "started_utc": started, "source_sha": "s"},
        "tool": {"name": "mutmut", "version": "2.5.1"},
        "tests": {"files": ["a", "b"], "count": 5},
        "counts": {"total": 4, "killed": 3, "survived": 1, "timeout": 0, "suspicious": 0,
                   "equivalent": "not-classified"},
        "stale_after": {"days": days},
        "survivors": [{"id": 1, "material_sample": "x"}],
    }
    _write(repo / "tests/mutation/baselines/t.json", json.dumps(record))
    return target


def test_mutation_not_run_without_a_record(repo):
    assert _build(repo)["layers"]["mutation"] == {"state": "not-run", "records": []}


def test_mutation_fresh_then_stale_by_target_change_and_by_age(repo):
    target = _mutation_record(repo)
    row = _build(repo)["layers"]["mutation"]["records"][0]
    assert row["state"] == "fresh"
    assert row["counts"]["equivalent"] == "not-classified"  # never invented as 0
    assert row["denominator"] == {"mutants": 4}
    assert row["material_survivors"] == 1

    target.write_text("x = 2\n", encoding="utf-8")
    row = _build(repo)["layers"]["mutation"]["records"][0]
    assert (row["state"], row["stale_reasons"]) == ("stale", ["target-changed"])

    _mutation_record(repo, started="2026-08-01T00:00:00Z")  # 60 days old, target unchanged
    row = _build(repo)["layers"]["mutation"]["records"][0]
    assert (row["state"], row["stale_reasons"]) == ("stale", ["older-than-stale-after-days"])


# ── escaped defects ──
def test_escaped_defects_count_per_month_and_zero_is_real(repo):
    layer = _build(repo)["layers"]["escaped_defects"]
    assert layer["state"] == "counting"
    assert layer["months"] == {"2026-08": 0, "2026-09": 1}
    assert layer["denominator"]["tickets_scanned"] == 2
    assert layer["tickets"] == [{"ticket_id": "TCK-1", "date": "2026-09-10", "failure_class": "never-fires"}]


def test_tag_not_registered_is_a_state_not_a_zero(repo):
    (repo / "registries/tag_registry.jsonl").write_text("", encoding="utf-8")
    layer = _build(repo)["layers"]["escaped_defects"]
    assert layer["state"] == "tag-not-registered"
    assert layer["months"] == {}


def test_unreadable_mutation_record_is_a_state_not_an_exception(repo):
    _write(repo / "tests/mutation/baselines/bad.json", "{not json")
    layer = _build(repo)["layers"]["mutation"]
    assert layer["state"] == "recorded"
    assert layer["records"][0]["state"] == "unreadable"


def test_escaped_defect_month_basis_is_stated(repo):
    assert "creation date" in _build(repo)["layers"]["escaped_defects"]["month_basis"]


# ── manifest: worktree_dirty ──
def _git(repo, *args):
    import subprocess
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


def test_worktree_dirty_is_unknown_outside_git(repo):
    manifest = _build(repo)["manifest"]
    assert manifest["worktree_dirty"] == "unknown"


def test_worktree_dirty_flags_uncommitted_scanned_inputs_only(repo):
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    assert _build(repo)["manifest"]["worktree_dirty"] is False
    _write(repo / "tests/unit/other/test_d.py", "import os\n")            # a scanned input
    _write(repo / "tickets/working_log.csv", "x\n")                        # not a scanned input (not .md)
    manifest = _build(repo)["manifest"]
    assert manifest["worktree_dirty"] is True
    assert manifest["dirty_input_paths"] == ["tests/unit/other/test_d.py"]


# ── parity, fixed states, limits ──
def test_parity_is_read_only_with_denominator(repo):
    layer = _build(repo)["layers"]["parity"]
    assert layer["denominator"] == {"entries": 2}
    assert layer["counts"] == {"missing": 1, "verified": 1}


def test_fixed_states_and_required_limits(repo):
    built = _build(repo)
    assert built["layers"]["simq"]["state"] == "skipped-no-data"
    assert built["layers"]["census"]["state"] == "unstable"
    limits = " ".join(built["limits"])
    for required in ("api-tools", "not a project dependency", "Equivalent mutants are not classified",
                     "`mutmut` 3.x", "not a gate", "unowned-domain", "worktree_dirty", "creation date"):
        assert required in limits


def test_markdown_renders_states_and_limits(repo):
    md = report.render_markdown(_build(repo))
    assert "no-junit-artifact" in md and "no-coverage-artifact" in md
    assert "## v0 limits" in md


# ── CLI and smoke ──
def test_cli_writes_json_and_markdown_and_exits_zero(repo, tmp_path):
    out = tmp_path / "out"
    code = report.main(["--repo-root", str(repo), "--sha", "abc", "--as-of", "2026-09-30", "--out-dir", str(out)])
    assert code == 0
    assert json.loads((out / "report.json").read_text())["manifest"]["sha"] == "abc"
    assert (out / "report.md").is_file()


def test_smoke_on_the_live_repo_has_every_layer_and_a_denominator(tmp_path):
    out = tmp_path / "live"
    report.main(["--repo-root", str(REPO_ROOT), "--sha", "smoke", "--as-of", "2026-09-30", "--out-dir", str(out)])
    layers = json.loads((out / "report.json").read_text())["layers"]
    assert set(layers) == {"classification", "lanes", "execution", "coverage", "parity", "simq", "census",
                           "mutation", "escaped_defects"}
    assert layers["classification"]["denominator"]["test_files"] > 0
    assert layers["execution"]["state"] == "no-junit-artifact"
