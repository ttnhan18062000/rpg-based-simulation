"""Tests for tools/gate_checks/tools_orphan_check.py (TCK-20260929-TOOLS-ORPHAN-FILE-CHECK,
child of TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC).
"""
import json
import sys
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from tools_orphan_check import (  # noqa: E402
    check_tools_orphans,
    is_codex_subtree,
)


def _write(root: Path, rel_path: str, content: str = "") -> None:
    p = root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _by_file(results, rel_path):
    for r in results:
        if r["file"] == rel_path:
            return r
    raise AssertionError(f"{rel_path!r} not found in results: {[r['file'] for r in results]}")


# ---------------------------------------------------------------------------
# tmp_path test (a): bare-stem sibling import -> LIVE
# ---------------------------------------------------------------------------


def test_bare_stem_sibling_import_classified_live(tmp_path):
    _write(tmp_path, "tools/perf/__init__.py", "")
    _write(tmp_path, "tools/perf/helper.py", "def do_thing():\n    return 1\n")
    _write(
        tmp_path,
        "tools/perf/caller.py",
        "from helper import do_thing\n\ndo_thing()\n",
    )
    tracked = [
        "tools/perf/__init__.py",
        "tools/perf/helper.py",
        "tools/perf/caller.py",
    ]
    results = check_tools_orphans(repo_root=tmp_path, tracked_files=tracked)
    helper = _by_file(results, "tools/perf/helper.py")
    assert helper["status"] == "LIVE"
    assert "tools/perf/caller.py" in helper["evidence"]


# ---------------------------------------------------------------------------
# tmp_path test (b): referenced only from tests/ -> TEST_ONLY
# ---------------------------------------------------------------------------


def test_referenced_only_from_tests_classified_test_only(tmp_path):
    _write(tmp_path, "tools/maintenance/widget.py", "def widget():\n    return 1\n")
    _write(
        tmp_path,
        "tests/tools/test_widget.py",
        "from widget import widget\n\ndef test_widget():\n    assert widget() == 1\n",
    )
    tracked = ["tools/maintenance/widget.py", "tests/tools/test_widget.py"]
    results = check_tools_orphans(repo_root=tmp_path, tracked_files=tracked)
    widget = _by_file(results, "tools/maintenance/widget.py")
    assert widget["status"] == "TEST_ONLY"
    assert widget["evidence"] == ["tests/tools/test_widget.py"]


# ---------------------------------------------------------------------------
# tmp_path test (c): word-boundary tokens, not substring matching
# ---------------------------------------------------------------------------


def test_word_boundary_tokens_not_substring_matched(tmp_path):
    _write(tmp_path, "tools/test_docker.py", "print('docker smoke run')\n")
    _write(
        tmp_path,
        "tests/tools/test_docker_compose_dependency_hygiene.py",
        "def test_docker_compose_dependency_hygiene():\n    assert True\n",
    )
    tracked = [
        "tools/test_docker.py",
        "tests/tools/test_docker_compose_dependency_hygiene.py",
    ]
    results = check_tools_orphans(repo_root=tmp_path, tracked_files=tracked)
    docker = _by_file(results, "tools/test_docker.py")
    # "test_docker" is not a substring-match hit against the longer identifier
    # "test_docker_compose_dependency_hygiene" -- IDENT_RE tokenizes that filename's own content
    # (the function name) as one whole token, never containing "test_docker" as a separate token.
    assert docker["status"] == "NO_REFERENCES"
    assert docker["evidence"] == []


# ---------------------------------------------------------------------------
# tmp_path test (d): references only in ignored historical paths -> NO_REFERENCES
# ---------------------------------------------------------------------------


def test_references_only_in_ignored_historical_paths_are_no_references(tmp_path):
    _write(tmp_path, "tools/maintenance/relic.py", "def relic():\n    return 1\n")
    _write(
        tmp_path,
        "tickets/done/TCK-EXAMPLE.md",
        "Built `relic.py` to do a thing.\n",
    )
    _write(
        tmp_path,
        "docs/archive/old_notes.md",
        "See relic.py for the old approach.\n",
    )
    _write(
        tmp_path,
        "stored_artifacts/TCK-EXAMPLE/plan.md",
        "relic.py implementation plan.\n",
    )
    tracked = [
        "tools/maintenance/relic.py",
        "tickets/done/TCK-EXAMPLE.md",
        "docs/archive/old_notes.md",
        "stored_artifacts/TCK-EXAMPLE/plan.md",
    ]
    results = check_tools_orphans(repo_root=tmp_path, tracked_files=tracked)
    relic = _by_file(results, "tools/maintenance/relic.py")
    assert relic["status"] == "NO_REFERENCES"
    assert relic["evidence"] == []


# ---------------------------------------------------------------------------
# tmp_path test (e): Makefile / .claude/settings.json entrypoint -> LIVE
# ---------------------------------------------------------------------------


def test_makefile_entrypoint_reference_classified_live(tmp_path):
    _write(tmp_path, "tools/release/gizmo.py", "def gizmo():\n    return 1\n")
    _write(
        tmp_path,
        "Makefile",
        "gizmo-run: ## run gizmo\n\tpython3 tools/release/gizmo.py\n",
    )
    tracked = ["tools/release/gizmo.py", "Makefile"]
    results = check_tools_orphans(repo_root=tmp_path, tracked_files=tracked)
    gizmo = _by_file(results, "tools/release/gizmo.py")
    assert gizmo["status"] == "LIVE"
    assert "Makefile" in gizmo["evidence"]


def test_settings_json_hook_entrypoint_reference_classified_live(tmp_path):
    _write(tmp_path, "tools/agent-monitoring/sprocket.py", "def sprocket():\n    return 1\n")
    _write(
        tmp_path,
        ".claude/settings.json",
        json.dumps({"hooks": {"PreToolUse": [{"command": "python3 tools/agent-monitoring/sprocket.py"}]}}),
    )
    tracked = ["tools/agent-monitoring/sprocket.py", ".claude/settings.json"]
    results = check_tools_orphans(repo_root=tmp_path, tracked_files=tracked)
    sprocket = _by_file(results, "tools/agent-monitoring/sprocket.py")
    assert sprocket["status"] == "LIVE"
    assert ".claude/settings.json" in sprocket["evidence"]


# ---------------------------------------------------------------------------
# __init__.py and __pycache__ are skipped; Codex subtree files are "excluded"
# ---------------------------------------------------------------------------


def test_init_py_and_pycache_skipped_codex_subtree_excluded(tmp_path):
    _write(tmp_path, "tools/perf/__init__.py", "")
    _write(tmp_path, "tools/perf/__pycache__/helper.cpython-312.pyc", "")
    _write(tmp_path, "tools/agent_codex_pilot_entrypoint/foo.py", "def foo():\n    return 1\n")
    tracked = [
        "tools/perf/__init__.py",
        "tools/perf/__pycache__/helper.cpython-312.pyc",
        "tools/agent_codex_pilot_entrypoint/foo.py",
    ]
    results = check_tools_orphans(repo_root=tmp_path, tracked_files=tracked)
    files = {r["file"] for r in results}
    assert "tools/perf/__init__.py" not in files
    assert "tools/perf/__pycache__/helper.cpython-312.pyc" not in files
    foo = _by_file(results, "tools/agent_codex_pilot_entrypoint/foo.py")
    assert foo["status"] == "excluded"
    assert foo["evidence"] == []
    assert is_codex_subtree("tools/agent_codex_pilot_entrypoint/foo.py")
    assert not is_codex_subtree("tools/perf/turbo_run.py")


# ---------------------------------------------------------------------------
# Determinism and side-effect freedom
# ---------------------------------------------------------------------------


def test_two_consecutive_runs_produce_byte_identical_json_and_no_side_effects(tmp_path):
    _write(tmp_path, "tools/perf/alpha.py", "def alpha():\n    return 1\n")
    _write(tmp_path, "tools/perf/beta.py", "from alpha import alpha\n\nalpha()\n")
    tracked = ["tools/perf/alpha.py", "tools/perf/beta.py"]

    before = {p: (tmp_path / p).read_bytes() for p in tracked}
    first = json.dumps(check_tools_orphans(repo_root=tmp_path, tracked_files=tracked))
    second = json.dumps(check_tools_orphans(repo_root=tmp_path, tracked_files=tracked))
    after = {p: (tmp_path / p).read_bytes() for p in tracked}

    assert first == second
    assert before == after


# ---------------------------------------------------------------------------
# Makefile wiring (pure text, mirrors test_makefile_wires_duplicate_run_record_check)
# ---------------------------------------------------------------------------


def test_makefile_wires_tools_orphan_check():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "tools-orphan-check:" in makefile_text
    assert "tools_orphan_check.py" in makefile_text
    assert "(on-demand only — not CI)" in makefile_text.split("tools-orphan-check:", 1)[1].split("\n", 1)[0]
    assert "tools-orphan-check" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )


def test_no_github_workflow_references_the_module():
    workflows_dir = _REPO_ROOT / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return
    for wf in workflows_dir.glob("*.yml"):
        assert "tools_orphan_check" not in wf.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Real-corpus test — structure only, never specific counts (they shift over time)
# ---------------------------------------------------------------------------


def test_real_corpus_run_completes_fast_with_correct_structure():
    start = time.monotonic()
    results = check_tools_orphans()
    elapsed = time.monotonic() - start
    assert elapsed < 60, f"real-corpus run took {elapsed:.1f}s -- should be seconds, not minutes"

    assert len(results) > 0
    valid_statuses = {"NO_REFERENCES", "DOC_ONLY", "TEST_ONLY", "LIVE", "excluded"}
    seen_files = set()
    for r in results:
        assert set(r.keys()) == {"file", "status", "evidence"}
        assert r["status"] in valid_statuses
        assert isinstance(r["evidence"], list)
        assert r["file"].startswith("tools/")
        assert not r["file"].endswith("__init__.py")
        assert "__pycache__" not in r["file"]
        if r["status"] == "excluded":
            assert is_codex_subtree(r["file"])
            assert r["evidence"] == []
        seen_files.add(r["file"])
    # no duplicates
    assert len(seen_files) == len(results)


@pytest.mark.parametrize(
    "path",
    [
        "tools/agent_codex_live_transport/invoker.py",
        "tools/agent_orchestration_claude_adapter/adapter.py",
        "tools/agent_replay/run_pilot.py",
    ],
)
def test_is_codex_subtree_matches_the_three_real_prefixes(path):
    is_replay_subtree = path.startswith("tools/agent_replay/")
    # agent_replay/ itself (no trailing *_ segment) is NOT one of the three excluded prefixes --
    # only agent_replay_<x>/ subdirs are. Confirms the prefix check is exact, not a loose "starts
    # with agent_replay" substring match.
    if is_replay_subtree:
        assert not is_codex_subtree(path)
    else:
        assert is_codex_subtree(path)
