"""No-mutation snapshot test for tools/agent_replay/runner.py (TCK-20260721-CODEX-REPLAY-PROOF, AC #3).

Runs against the REAL repository tree — never a tmp_path copy, which would make the assertion
vacuously true (nothing real to mutate). Mirrors implement-ticket.js's own existing
`touchedOutput = await bash('git status --porcelain -- docs/parity_ledger/')` precedent.

This repo's actual working tree is routinely dirty in tickets/ and agent-monitoring/ during active
development (confirmed live via `git status --porcelain -- tickets/ agent-monitoring/` while
writing this test — modified agent-monitoring/*.jsonl, untracked tickets/inprogress/*.md from
sibling in-flight tickets). A "pre-snapshot must be clean" gate would skip on every real run in
this repo, which is a weaker guarantee than the plan calls for ("must not silently pass a
dirty-tree false-negative"). Instead: when the pre-snapshot is clean, assert it stays clean
(porcelain before == porcelain after == ""). When the pre-snapshot is already dirty (the common
real case here), fall back to a content-hash of every watched file taken immediately before and
immediately after `replay_slice()` runs, and assert those hashes are identical — this proves
`replay_slice()` itself introduced zero changes, independent of ambient dirty state.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.fixture_envelope import load_fixture  # noqa: E402
from agent_replay.runner import replay_slice  # noqa: E402

_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)
_WATCHED_GIT_PATHSPECS = ["tickets/", "agent-monitoring/data/"]


def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *_WATCHED_GIT_PATHSPECS],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _watched_files() -> list[Path]:
    files = [f for f in sorted((_REPO_ROOT / "tickets").rglob("*")) if f.is_file()]
    files += [f for f in sorted((_REPO_ROOT / "agent-monitoring" / "data").rglob("*")) if f.is_file()]
    return files


def _content_hash_snapshot() -> str:
    hasher = hashlib.sha256()
    for f in _watched_files():
        hasher.update(str(f.relative_to(_REPO_ROOT)).encode("utf-8"))
        hasher.update(f.read_bytes())
    return hasher.hexdigest()


def test_snapshot_targets_are_the_real_repo_directories_not_a_tmp_copy():
    tickets_dir = _REPO_ROOT / "tickets"
    monitoring_dir = _REPO_ROOT / "agent-monitoring"
    assert tickets_dir.is_dir()
    assert monitoring_dir.is_dir()
    assert tickets_dir.parent == _REPO_ROOT
    assert monitoring_dir.parent == _REPO_ROOT
    assert "tmp" not in str(tickets_dir).lower()
    assert "tmp" not in str(monitoring_dir).lower()


def test_replay_run_produces_zero_diff_in_tickets_and_monitoring_corpus():
    pre_porcelain = _porcelain_snapshot()

    if pre_porcelain == "":
        fixture = load_fixture(_REAL_FIXTURE_PATH)
        replay_slice(fixture)
        post_porcelain = _porcelain_snapshot()
        assert post_porcelain == "", (
            "replay_slice mutated tickets/ or agent-monitoring/*.jsonl (tree was clean before, "
            f"dirty after): {post_porcelain!r}"
        )
        return

    pre_hash = _content_hash_snapshot()
    assert _watched_files(), "no watched files found — snapshot would be vacuous"

    fixture = load_fixture(_REAL_FIXTURE_PATH)
    replay_slice(fixture)

    post_hash = _content_hash_snapshot()
    assert pre_hash == post_hash, (
        "replay_slice changed the content of one or more files under tickets/ or "
        "agent-monitoring/*.jsonl (ambient dirty state existed before the run, but its content "
        "hash must be unchanged after)"
    )


def test_watch_set_actually_detects_a_deliberate_mutation_under_agent_monitoring_data():
    """Regression guard for TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS.

    The prior `_WATCHED_GIT_PATHSPECS`/`_watched_files()` hardcoded the 3 retired monolithic
    `agent-monitoring/*.jsonl` paths, none of which exist any more now that real data lives under
    `agent-monitoring/data/<week>/`. That made the two assertions above pass vacuously — they were
    watching nothing under `agent-monitoring/`, so a real mutation there would go undetected. This
    proves the widened watch set (`agent-monitoring/data/`, recursive) actually fires on a
    deliberate mutation to a file in the real shard layout, not just that the snapshot helpers run
    without error.
    """
    probe_path = _REPO_ROOT / "agent-monitoring" / "data" / "unknown-week" / "_no_mutation_snapshot_probe.jsonl"
    assert not probe_path.exists(), "stale probe file from a previous failed run — clean it up first"

    pre_content_hash = _content_hash_snapshot()
    pre_porcelain = _porcelain_snapshot()
    try:
        probe_path.write_text('{"probe": true}\n', encoding="utf-8")

        post_content_hash = _content_hash_snapshot()
        post_porcelain = _porcelain_snapshot()

        assert post_content_hash != pre_content_hash, (
            "content-hash snapshot was unchanged after writing a file under agent-monitoring/data/ "
            "— _watched_files() is not covering the real shard layout"
        )
        assert post_porcelain != pre_porcelain, (
            "git porcelain snapshot was unchanged after writing a file under agent-monitoring/data/ "
            "— _WATCHED_GIT_PATHSPECS is not covering the real shard layout"
        )
    finally:
        probe_path.unlink(missing_ok=True)
