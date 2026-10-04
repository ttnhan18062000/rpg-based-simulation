"""Tests for codebase/gates/parity_ledger_schema.py (TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET).

The unit tests build small ledgers in `tmp_path` and validate them against the real `docs/parity_ledger/schema.json`. The
live test runs the gate over the real ledger and the committed baseline, and fails (never skips) when the gate cannot run:
a tool that cannot run is not a green result.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from codebase.gates import parity_ledger_schema as gate

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCHEMA = _REPO_ROOT / "docs" / "parity_ledger" / "schema.json"
_RULE_VERIFIED = "allOf/0/then/properties/test_path/type"
_RULE_P0 = "allOf/2/else/then/properties/test_path/type"


def _entry(entry_id="SUB-001", **overrides):
    entry = {"id": entry_id, "text": "x", "status": "missing", "priority": "P1"}
    entry.update(overrides)
    return entry


def _verified_without_test_path(entry_id):
    return _entry(entry_id, status="verified", v2_evidence="e", test_path=None)


def _ledger(tmp_path, shards, baseline=None):
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    for name, entries in shards.items():
        (ledger / name).write_text(yaml.safe_dump(entries), encoding="utf-8")
    base = tmp_path / "baseline.json"
    if baseline is not None:
        base.write_text(json.dumps({"version": 1, "counts": baseline}), encoding="utf-8")
    return ["--ledger-dir", str(ledger), "--schema", str(_SCHEMA), "--baseline", str(base)], ledger, base


def _run(argv, capsys):
    code = gate.main(argv)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def assert_gate_passes(argv):
    """The live-test wrapper: exit 0 or a failure that prints the gate's own output (exit 1 and exit 2 both fail)."""
    done = subprocess.run([sys.executable, "-m", "codebase.gates.parity_ledger_schema", *argv],
                          cwd=_REPO_ROOT, capture_output=True, text=True)
    assert done.returncode == 0, f"parity-ledger gate exit {done.returncode}:\n{done.stdout}{done.stderr}"
    return done.stdout


# ── counting ────────────────────────────────────────────────────────────────


def test_a_clean_ledger_has_no_errors(tmp_path):
    _, ledger, _ = _ledger(tmp_path, {"a.yaml": [_entry()]})
    assert gate.count_errors(ledger, gate.load_schema(_SCHEMA)).counts == {}


def test_errors_are_counted_per_file_and_rule_with_the_items_prefix_removed(tmp_path):
    p0 = _entry("SUB-003", priority="P0", status="verified", v2_evidence="e", test_path=None)
    _, ledger, _ = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002"), p0], "b.yaml": [_entry()]})
    scan = gate.count_errors(ledger, gate.load_schema(_SCHEMA))
    assert scan.counts == {"a.yaml": {_RULE_VERIFIED: 2, _RULE_P0: 1}}
    assert scan.labels[("a.yaml", _RULE_VERIFIED)] == ["SUB-002", "SUB-003"]


def test_an_entry_without_an_id_or_a_non_mapping_item_is_labelled_by_index_not_a_crash(tmp_path):
    no_id = {"text": "x", "status": "missing", "priority": "P1"}
    _, ledger, _ = _ledger(tmp_path, {"a.yaml": [_entry(), no_id, "just a string", {"id": 7, "text": "x", "status": "missing", "priority": "P1"}]})
    scan = gate.count_errors(ledger, gate.load_schema(_SCHEMA))
    assert scan.labels[("a.yaml", "required")] == ["#1"]
    assert scan.labels[("a.yaml", "type")] == ["#2"]
    assert scan.labels[("a.yaml", "properties/id/type")] == ["#3"]


def test_a_shard_that_is_not_a_list_is_counted_under_its_own_root_rule(tmp_path):
    _, ledger, _ = _ledger(tmp_path, {"a.yaml": {"not": "a list"}})
    scan = gate.count_errors(ledger, gate.load_schema(_SCHEMA))
    assert scan.counts == {"a.yaml": {"type": 1}}
    assert scan.labels[("a.yaml", "type")] == ["(root)"]


# ── compare ─────────────────────────────────────────────────────────────────


def test_compare_separates_rises_new_and_decreases_and_treats_equal_as_clean():
    result = gate.compare({"a.yaml": {"r1": 3, "r2": 1, "r4": 2}, "c.yaml": {"r1": 1}},
                          {"a.yaml": {"r1": 2, "r2": 1, "r3": 4, "r4": 5}})
    assert result.rises == [("a.yaml", "r1", 2, 3)]
    assert result.new == [("c.yaml", "r1", 1)]
    assert result.decreases == [("a.yaml", "r3", 4, 0), ("a.yaml", "r4", 5, 2)]
    assert result.failed


def test_compare_of_an_empty_ledger_and_an_empty_baseline_is_clean():
    assert not gate.compare({}, {}).failed


# ── check ───────────────────────────────────────────────────────────────────


def test_check_passes_when_the_counts_equal_the_baseline(tmp_path, capsys):
    argv, _, _ = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]}, {"a.yaml": {_RULE_VERIFIED: 1}})
    code, out = _run([*argv, "check"], capsys)
    assert code == 0 and "OK: 1 schema error(s)" in out


def test_adding_a_verified_entry_with_a_null_test_path_fails_and_names_the_file_rule_and_entry(tmp_path, capsys):
    argv, ledger, _ = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]}, {"a.yaml": {_RULE_VERIFIED: 1}})
    (ledger / "a.yaml").write_text(yaml.safe_dump([_verified_without_test_path("SUB-002"), _verified_without_test_path("SUB-009")]))
    code, out = _run([*argv, "check"], capsys)
    assert code == 1
    assert f"FAIL a.yaml: rule {_RULE_VERIFIED} rose from 1 to 2" in out and "SUB-009" in out


def test_removing_an_error_passes_and_reports_the_decrease(tmp_path, capsys):
    argv, ledger, _ = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]}, {"a.yaml": {_RULE_VERIFIED: 2}})
    code, out = _run([*argv, "check"], capsys)
    assert code == 0
    assert f"better a.yaml: rule {_RULE_VERIFIED} fell from 2 to 1" in out and "tighten --yes" in out


def test_a_rule_that_is_not_in_the_baseline_fails_even_when_the_total_is_unchanged(tmp_path, capsys):
    argv, _, _ = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]}, {"a.yaml": {"properties/proof_type/enum": 1}})
    code, out = _run([*argv, "check"], capsys)
    assert code == 1 and f"rule {_RULE_VERIFIED} is new" in out


def test_a_new_shard_with_errors_fails_and_a_vanished_shard_is_a_decrease(tmp_path, capsys):
    argv, _, _ = _ledger(tmp_path, {"a.yaml": [_entry()], "new.yaml": [_verified_without_test_path("SUB-002")]}, {"gone.yaml": {"r": 3}})
    code, out = _run([*argv, "check"], capsys)
    assert code == 1 and "FAIL new.yaml" in out and "better gone.yaml: rule r fell from 3 to 0" in out


def test_a_rise_lists_the_last_failing_entries_where_new_ones_are_appended_and_caps_the_list(tmp_path, capsys):
    entries = [_verified_without_test_path(f"SUB-{n:03d}") for n in range(1, 9)]
    argv, _, _ = _ledger(tmp_path, {"a.yaml": entries}, {"a.yaml": {_RULE_VERIFIED: 6}})
    _, out = _run([*argv, "check"], capsys)
    assert "rose from 6 to 8" in out and "most likely the last 2" in out and "SUB-007, SUB-008" in out
    assert "SUB-001" not in out and "8 fail in all" in out


def test_a_new_rule_lists_its_first_failing_entries_capped(tmp_path, capsys):
    entries = [_verified_without_test_path(f"SUB-{n:03d}") for n in range(1, 9)]
    argv, _, _ = _ledger(tmp_path, {"a.yaml": entries}, {"a.yaml": {"properties/proof_type/enum": 1}})
    _, out = _run([*argv, "check"], capsys)
    assert "SUB-005, ... (8 in all)" in out and "SUB-006" not in out


# ── cannot run: exit 2, never green ─────────────────────────────────────────


def test_a_shard_with_broken_yaml_exits_2_and_names_the_file(tmp_path, capsys):
    argv, ledger, _ = _ledger(tmp_path, {"a.yaml": [_entry()]}, {})
    (ledger / "broken.yaml").write_text("- id: [unclosed\n  text: x\n", encoding="utf-8")
    code, out = _run([*argv, "check"], capsys)
    assert code == 2 and "broken.yaml" in out and "could not run" in out


@pytest.mark.parametrize("baseline_text", [None, "{not json", '["a list"]', '{"version": 2, "counts": {}}',
                                           '{"version": 1, "counts": {"a.yaml": {"r": 0}}}',
                                           '{"version": 1, "counts": {"a.yaml": {"r": true}}}',
                                           '{"version": 1, "counts": {"a.yaml": []}}'])
def test_a_missing_or_invalid_baseline_exits_2(tmp_path, capsys, baseline_text):
    argv, _, base = _ledger(tmp_path, {"a.yaml": [_entry()]})
    if baseline_text is not None:
        base.write_text(baseline_text, encoding="utf-8")
    code, out = _run([*argv, "check"], capsys)
    assert code == 2 and "could not run" in out


@pytest.mark.parametrize("schema_text", [None, "{not json", '{"type": 12}'])
def test_a_missing_or_broken_schema_exits_2_not_a_traceback(tmp_path, capsys, schema_text):
    argv, ledger, _ = _ledger(tmp_path, {"a.yaml": [_entry()]}, {})
    schema = tmp_path / "schema.json"
    if schema_text is not None:
        schema.write_text(schema_text, encoding="utf-8")
    argv[argv.index("--schema") + 1] = str(schema)
    code, out = _run([*argv, "check"], capsys)
    assert code == 2 and "could not run" in out


def test_a_ledger_directory_with_no_shards_exits_2(tmp_path, capsys):
    argv, _, _ = _ledger(tmp_path, {}, {})
    code, _ = _run([*argv, "check"], capsys)
    assert code == 2


# ── tighten and seed ────────────────────────────────────────────────────────


def test_tighten_is_a_dry_run_without_yes_and_writes_the_decreases_with_it(tmp_path, capsys):
    argv, _, base = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]}, {"a.yaml": {_RULE_VERIFIED: 3}, "b.yaml": {"r": 2}})
    before = base.read_bytes()
    code, out = _run([*argv, "tighten"], capsys)
    assert code == 0 and "dry run" in out and base.read_bytes() == before
    code, _ = _run([*argv, "tighten", "--yes"], capsys)
    assert code == 0
    assert json.loads(base.read_text()) == {"version": 1, "counts": {"a.yaml": {_RULE_VERIFIED: 1}}}
    assert base.read_text().endswith("\n")


def test_tighten_refuses_and_writes_nothing_when_a_count_rose_or_is_new(tmp_path, capsys):
    argv, _, base = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-001"), _verified_without_test_path("SUB-002")]},
                            {"a.yaml": {_RULE_VERIFIED: 1}})
    before = base.read_bytes()
    code, out = _run([*argv, "tighten", "--yes"], capsys)
    assert code == 1 and "tighten refused" in out and base.read_bytes() == before


def test_tighten_output_is_byte_stable_and_says_when_there_is_nothing_to_do(tmp_path, capsys):
    argv, _, base = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]}, {"a.yaml": {_RULE_VERIFIED: 2}})
    _run([*argv, "tighten", "--yes"], capsys)
    first = base.read_bytes()
    code, out = _run([*argv, "tighten", "--yes"], capsys)
    assert code == 0 and "already tight" in out and base.read_bytes() == first


def test_seed_writes_the_counts_and_refuses_to_overwrite_without_force(tmp_path, capsys):
    argv, _, base = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]})
    code, _ = _run([*argv, "seed"], capsys)
    assert code == 0 and json.loads(base.read_text())["counts"] == {"a.yaml": {_RULE_VERIFIED: 1}}
    base.write_text("keep me", encoding="utf-8")
    code, out = _run([*argv, "seed"], capsys)
    assert code == 1 and base.read_text() == "keep me" and "--force" in out
    code, _ = _run([*argv, "seed", "--force"], capsys)
    assert code == 0 and base.read_text() != "keep me"


# ── the live wrapper must fail, not skip or pass, when the gate cannot run ──


def test_the_live_wrapper_fails_when_the_gate_cannot_run_exit_2(tmp_path):
    argv, ledger, _ = _ledger(tmp_path, {"a.yaml": [_entry()]}, {})
    (ledger / "broken.yaml").write_text("- id: [unclosed\n", encoding="utf-8")
    with pytest.raises(AssertionError, match=r"exit 2[\s\S]*broken\.yaml"):
        assert_gate_passes([*argv, "check"])


def test_the_live_wrapper_fails_when_the_gate_reports_a_rise_exit_1(tmp_path):
    argv, ledger, _ = _ledger(tmp_path, {"a.yaml": [_verified_without_test_path("SUB-002")]}, {"a.yaml": {_RULE_VERIFIED: 1}})
    (ledger / "a.yaml").write_text(yaml.safe_dump([_verified_without_test_path("SUB-002"), _verified_without_test_path("SUB-003")]))
    with pytest.raises(AssertionError, match=r"exit 1[\s\S]*rose from 1 to 2"):
        assert_gate_passes([*argv, "check"])


# ── live: the real ledger against the committed baseline ────────────────────


def test_the_real_ledger_has_no_schema_error_beyond_the_committed_baseline():
    out = assert_gate_passes(["check"])
    assert out.rstrip().splitlines()[-1].startswith("OK: ")


def test_the_committed_baseline_is_well_formed_and_uses_only_known_rule_keys():
    counts = gate.load_baseline(_REPO_ROOT / gate.BASELINE_REL)
    rules = {rule for per_file in counts.values() for rule in per_file}
    assert rules <= {_RULE_VERIFIED, _RULE_P0, "properties/proof_type/enum"}, rules
