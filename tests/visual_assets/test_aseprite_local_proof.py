"""The committed proof of the last strict local run of the real-Aseprite tests (ADR D10, `TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD`).

CI never runs Aseprite. It recomputes a hash over the files those tests exercise (`tools/visual_assets_aseprite_proof.py`) and fails when one changed since
`docs/assets/aseprite_local_proof.json` was written. THE ONLY FIX IS A REAL `make visual-assets-aseprite-local` RUN on the licence holder's machine, which
rewrites the record. The record must never be edited by hand: it states what that run did, and a hand edit would state something nobody ran.
The rules are pure functions proven here on planted violations; no Aseprite is needed.
"""

from __future__ import annotations

import copy

import pytest

from tools import visual_assets_aseprite_local as runner
from tools import visual_assets_aseprite_proof as proof

FILES = [{"path": "visual_assets/store/a.py", "sha256": proof.file_sha256(b"a")}, {"path": "visual_assets/store/b.py", "sha256": proof.file_sha256(b"b")}]


def good_record() -> dict:
    return proof.build_record(
        run_commit="a" * 40, run_at_utc="2026-10-10T12:00:00Z", aseprite_version="Aseprite 1.3.18.6-x64",
        counts={"passed": 40, "failed": 0, "errors": 0, "skipped": 0, "total": 40},
        rebuild={"release": "pilot/rc-0008", "entries": 70, "identical": 70, "bytes_differ_pixels_match": 0}, files=FILES,
    )


# ---- the guarded set ----

def test_the_guarded_set_is_all_of_store_and_drawing_minus_docs_plus_the_marked_tests_and_their_support():
    tracked = [
        "visual_assets/store/pixels.py", "visual_assets/store/build/exporter.py", "visual_assets/drawing/sandbox.py", "visual_assets/catalog/build-config/export.toml",
        "visual_assets/store/README.md", "visual_assets/review/sets.py", "docs/assets/store_contract.md", "src/engine/x.py",
        "tests/visual_assets/test_marked.py", "tests/visual_assets/test_unmarked.py", "tests/visual_assets/conftest.py", "tools/visual_assets_aseprite_local.py",
        "tools/visual_assets_aseprite_proof.py", "tools/ci_aseprite_skip_line.py", "visual_assets/store/__pycache__/x.pyc", "docs/assets/aseprite_local_proof.json",
    ]
    assert proof.guarded_paths(tracked, ["tests/visual_assets/test_marked.py"]) == sorted([
        "visual_assets/store/pixels.py", "visual_assets/store/build/exporter.py", "visual_assets/drawing/sandbox.py", "visual_assets/catalog/build-config/export.toml",
        "tests/visual_assets/test_marked.py", "tests/visual_assets/conftest.py", "tools/visual_assets_aseprite_local.py", "tools/visual_assets_aseprite_proof.py",
    ])


def test_the_record_itself_the_docs_and_review_tooling_are_not_guarded():
    for path in ("docs/assets/aseprite_local_proof.json", "docs/assets/store_contract.md", "visual_assets/review/sets.py", "visual_assets/store/notes.md", "tools/ci_aseprite_skip_line.py"):
        assert not proof.is_guarded(path)


def test_a_new_marked_test_file_makes_the_record_stale():
    assert proof.guarded_paths(["tests/visual_assets/test_new.py"], []) == []
    assert proof.guarded_paths(["tests/visual_assets/test_new.py"], ["tests/visual_assets/test_new.py"]) == ["tests/visual_assets/test_new.py"]


def test_the_marker_is_found_in_a_file_that_contains_it_and_not_in_this_module(tmp_path):
    (tmp_path / "tests" / "visual_assets").mkdir(parents=True)
    (tmp_path / "tests" / "visual_assets" / "test_x.py").write_text(f"@pytest.mark.{proof.MARKER}\ndef test_x(): ...\n")
    (tmp_path / "tests" / "visual_assets" / "test_y.py").write_text("def test_y(): ...\n")
    paths = ["tests/visual_assets/test_x.py", "tests/visual_assets/test_y.py"]
    assert proof.marked_test_files(paths, tmp_path) == ["tests/visual_assets/test_x.py"]
    assert proof.MARKER not in open(proof.__file__).read().replace('"needs_" + "aseprite"', "")


# ---- hash and comparison ----

def test_the_hash_ignores_input_order_and_changes_with_any_byte_or_name():
    base = proof.guarded_hash(FILES)
    assert proof.guarded_hash(list(reversed(FILES))) == base
    assert proof.guarded_hash([{**FILES[0], "sha256": proof.file_sha256(b"changed")}, FILES[1]]) != base
    assert proof.guarded_hash([{**FILES[0], "path": "visual_assets/store/c.py"}, FILES[1]]) != base


def test_compare_names_changed_added_and_removed_files():
    current = [{**FILES[0], "sha256": proof.file_sha256(b"changed")}, {"path": "visual_assets/store/new.py", "sha256": proof.file_sha256(b"n")}]
    changed, added, removed = proof.compare(FILES, current)
    assert (changed, added, removed) == (["visual_assets/store/a.py"], ["visual_assets/store/new.py"], ["visual_assets/store/b.py"])
    message = proof.staleness_message(changed, added, removed)
    assert "visual_assets/store/a.py" in message and "visual_assets/store/new.py" in message and "visual_assets/store/b.py" in message


def test_the_failure_message_names_the_only_fix_and_forbids_hand_edits():
    message = proof.staleness_message(["visual_assets/store/a.py"], [], [])
    assert "make visual-assets-aseprite-local" in message and "never edit that record by hand" in message and "the only fix is a real" in message


# ---- record validity, with planted violations ----

def test_a_good_record_has_no_problems():
    assert proof.record_problems(good_record()) == []


@pytest.mark.parametrize("name, mutate", [
    ("not strict", lambda r: r.update(strict=False)),
    ("a skipped test", lambda r: r["counts"].update(skipped=1)),
    ("a failure", lambda r: r["counts"].update(failed=1)),
    ("an error", lambda r: r["counts"].update(errors=1)),
    ("an empty run", lambda r: r["counts"].update(passed=0, total=0)),
    ("passed below total", lambda r: r["counts"].update(passed=39)),
    ("a missing count key", lambda r: r["counts"].pop("errors")),
    ("a string count", lambda r: r["counts"].update(passed="40")),
    ("a rebuild that loses an entry", lambda r: r["release_rebuild"].update(identical=69)),
    ("an empty rebuild", lambda r: r["release_rebuild"].update(entries=0, identical=0)),
    ("a wrong make target", lambda r: r.update(make_target="other")),
    ("a wrong record type", lambda r: r.update(record_type="x")),
    ("an extra key", lambda r: r.update(extra=1)),
    ("a blank commit", lambda r: r.update(run_commit=" ")),
    ("a hash that does not match the files", lambda r: r.update(guarded_hash="sha256:" + "0" * 64)),
    ("no files", lambda r: r.update(guarded_files=[])),
    ("unsorted files", lambda r: r["guarded_files"].reverse()),
])
def test_each_planted_violation_is_reported(name, mutate):
    record = copy.deepcopy(good_record())
    before = repr(record)
    mutate(record)
    assert repr(record) != before, "the mutant must change the record (applies at exactly one site)"
    assert proof.record_problems(record), name


def test_a_record_that_is_not_an_object_is_reported():
    assert proof.record_problems([]) and proof.record_problems(None)


# ---- a subset run never writes a record ----

@pytest.mark.parametrize("args, env", [
    (["-k", "licence"], {}), (["-m", "other"], {}), (["tests/visual_assets/drawing"], {}), (["tests/visual_assets/x.py::test_a"], {}), (["--deselect", "x"], {}),
    ([], {"PYTEST_ADDOPTS": "-k licence"}), ([], {"PYTEST_ADDOPTS": "-m other"}), ([], {"PYTEST_ADDOPTS": "tests/visual_assets/drawing"}), ([], {"PYTEST_ADDOPTS": "--lf"}),
    ([], {"PYTEST_ADDOPTS": "'unbalanced"}),
])
def test_any_selection_means_no_record_and_says_why(args, env):
    assert proof.selection_problem(args, env)


@pytest.mark.parametrize("args, env", [([], {}), (["-q"], {}), (["--tb=short"], {}), ([], {"PYTEST_ADDOPTS": "-q --tb=short"}), ([], {"PYTEST_ADDOPTS": ""})])
def test_the_full_target_is_not_a_selection(args, env):
    assert proof.selection_problem(args, env) is None


def good_evidence() -> dict:
    return {"ok": True, "commit": "a" * 40, "utc_time": "2026-10-10T12:00:00Z", "aseprite_version": "Aseprite 1.3.18.6-x64", "passed": 40, "failed": 0, "errors": 0, "skipped": 0, "total": 40}


def test_the_runner_writes_nothing_for_a_subset_or_an_unclean_run(monkeypatch, tmp_path):
    monkeypatch.setattr(proof, "RECORD_PATH", tmp_path / "record.json")
    monkeypatch.setattr(runner.proof, "RECORD_PATH", tmp_path / "record.json")
    monkeypatch.setattr(runner, "dirty_guarded_files", lambda: [])
    monkeypatch.setattr(runner, "read_rebuild_verdict", lambda: {"release": "pilot/rc-0008", "entries": 70, "identical": 70, "bytes_differ_pixels_match": 0})
    assert "not the full make target" in runner.write_proof_record(good_evidence(), extra_args=["-k", "x"], env={})
    assert "not the full make target" in runner.write_proof_record(good_evidence(), extra_args=[], env={"PYTEST_ADDOPTS": "-m other"})
    assert "not clean and strict" in runner.write_proof_record({**good_evidence(), "ok": False}, extra_args=[], env={})
    assert not (tmp_path / "record.json").exists()


def test_the_runner_refuses_when_guarded_files_are_uncommitted_or_the_rebuild_verdict_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.proof, "RECORD_PATH", tmp_path / "record.json")
    monkeypatch.setattr(runner, "dirty_guarded_files", lambda: ["visual_assets/store/pixels.py"])
    assert "not committed" in runner.write_proof_record(good_evidence(), extra_args=[], env={})
    monkeypatch.setattr(runner, "dirty_guarded_files", lambda: [])
    monkeypatch.setattr(runner, "read_rebuild_verdict", lambda: None)
    assert "rebuild verdict is missing" in runner.write_proof_record(good_evidence(), extra_args=[], env={})
    assert not (tmp_path / "record.json").exists()


def test_the_runner_writes_a_valid_record_for_a_clean_full_run(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.proof, "RECORD_PATH", tmp_path / "record.json")
    monkeypatch.setattr(runner, "dirty_guarded_files", lambda: [])
    monkeypatch.setattr(runner, "read_rebuild_verdict", lambda: {"release": "pilot/rc-0008", "entries": 70, "identical": 70, "bytes_differ_pixels_match": 0})
    assert "proof record written" in runner.write_proof_record(good_evidence(), extra_args=[], env={})
    written = proof.load_record(tmp_path / "record.json")
    assert proof.record_problems(written) == [] and written["counts"]["total"] == 40 and written["guarded_files"]


# ---- the committed record (the only part that reads the repository) ----

def test_the_committed_record_is_valid():
    record = proof.load_record()
    assert record is not None, f"docs/assets/aseprite_local_proof.json is missing; {proof.REFRESH}"
    assert proof.record_problems(record) == [], proof.REFRESH


def test_the_guarded_files_still_match_the_committed_record():
    record = proof.load_record()
    assert record is not None, f"docs/assets/aseprite_local_proof.json is missing; {proof.REFRESH}"
    changed, added, removed = proof.compare(record["guarded_files"], proof.current_files())
    assert not (changed or added or removed), proof.staleness_message(changed, added, removed)


@pytest.mark.parametrize("kind", ["changed", "added", "removed"])
def test_mutant_a_guarded_file_that_changed_was_added_or_removed_fails_the_comparison_naming_it(kind):
    record = proof.load_record()
    assert record is not None
    files = copy.deepcopy(record["guarded_files"])
    current = copy.deepcopy(files)
    if kind == "changed":
        current[0]["sha256"] = proof.file_sha256(b"one byte different")
        expect = current[0]["path"]
    elif kind == "added":
        current.append({"path": "visual_assets/store/zz_new.py", "sha256": proof.file_sha256(b"x")})
        expect = "visual_assets/store/zz_new.py"
    else:
        expect = current.pop()["path"]
    changed, added, removed = proof.compare(files, current)
    assert len(changed) + len(added) + len(removed) == 1, "the mutant applies at exactly one site"
    assert expect in proof.staleness_message(changed, added, removed)
