"""Integration tests for TCK-20260730-CLAUDE-EXECUTION-IDENTITY.

Drives `record_events.py`/`record_run.py`/`post_tool_hook.py` directly as black boxes — this repo
has no JS test runner for `.claude/workflows/*.js` (same precedent as
`test_current_run_sidecar_orchestrator.py`'s own module docstring), so a Claude
`implement-ticket` execution is simulated at the Python-writer-tool level using a
realistically-shaped `execution_id` (`claude-{tid}-{ts}-{hex}`, matching
`docs/ai/monitoring_writer_decision.md` §2's formula) and `provider="claude"`, matching the exact
shapes now produced by `writeSidecar`'s body and `writeMonitoring`'s prompt (both activated by
this ticket).

Covers:
- One execution's records share one `execution_id`; a second execution gets a different one (AC1,
  AC2).
- Pre-existing `agent-monitoring/{runs,events,tools}.jsonl` lines are never rewritten, only
  appended to (AC6, Part A).
- The newly appended lines themselves are well-formed: no duplicate/colliding identity keys, and
  `run_id`/`execution_id`/`provider`/`ticket_id` are each singular and correctly valued (AC6, Part
  B — a plain `json.loads` alone would silently hide a duplicate key, keeping only the last value;
  this uses a duplicate-key-sensitive `object_pairs_hook` plus a raw-text occurrence count instead).
"""
from __future__ import annotations

import hashlib
import json
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

_RECORD_EVENTS_PATH = _MONITORING_TOOLS_DIR / "record_events.py"
_RECORD_RUN_PATH = _MONITORING_TOOLS_DIR / "record_run.py"
_POST_TOOL_HOOK_PATH = _MONITORING_TOOLS_DIR / "post_tool_hook.py"


def _current_week_tools_file(agent_monitoring_dir: Path) -> Path:
    """Resolves the real tools-source write target, mirroring post_tool_hook.py's own
    `iso_week = now_dt.strftime("%G-W%V")` / `Path("agent-monitoring/tools") / f"tools-{iso_week}.jsonl"`
    (tools/agent-monitoring/post_tool_hook.py:56,159) — since TCK-20260902-MONITORING-SHARD-WRITE-PATH,
    the hook no longer writes a literal `tools.jsonl`. Keep this in sync if that format ever changes."""
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    return agent_monitoring_dir / "tools" / f"tools-{iso_week}.jsonl"


# ---------------------------------------------------------------------------
# Simulated-execution helpers
# ---------------------------------------------------------------------------


def _make_execution_id(provider: str, ticket_id: str) -> str:
    return f"{provider}-{ticket_id}-{int(time.time() * 1000)}-{secrets.token_hex(4)}"


def _run_writer_tool(path: Path, args: list[str], cwd: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(path), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    assert result.returncode == 0, result.stderr


def _write_sidecar(
    cwd: Path, *, run_id, seq, phase, agent, execution_id, provider, ticket_id, session_id
) -> None:
    """Mirrors the REAL current writeSidecar() shape (TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE):
    writes both the unscoped `.claude/current_run` file and a per-session-scoped copy at
    `.claude/current_run.<session_id>`. The scoped copy is required as of
    TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION: post_tool_hook.py no longer falls back to the
    unscoped file when no scoped file exists for the calling session_id (it writes null
    attribution instead) — a caller must write the scoped file itself, same as real
    ticket-workflow sessions do."""
    claude_dir = cwd / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    data = json.dumps(
        {
            "run_id": run_id,
            "seq": seq,
            "phase": phase,
            "agent": agent,
            "execution_id": execution_id,
            "provider": provider,
            "ticket_id": ticket_id,
        }
    )
    (claude_dir / "current_run").write_text(data)
    (claude_dir / f"current_run.{session_id}").write_text(data)


def _run_post_tool_hook(cwd: Path, *, session_id: str, command: str) -> None:
    payload = {
        "session_id": session_id,
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": {},
    }
    result = subprocess.run(
        [sys.executable, str(_POST_TOOL_HOOK_PATH)],
        input=json.dumps(payload),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


def _perform_one_simulated_execution(cwd: Path, *, ticket_id: str, seq_start: int = 1) -> dict:
    """Writes 2 events + 1 run record + 1 tools.jsonl row for one simulated Claude execution,
    all sharing one execution_id — mirrors the exact shape writeSidecar's body (argv 5/6) and
    writeMonitoring's Step 2/Step 3 prompt now produce."""
    provider = "claude"
    execution_id = _make_execution_id(provider, ticket_id)
    ts = "2026-07-31T00:00:00Z"

    events = [
        {
            "run_id": ticket_id,
            "seq": seq_start,
            "ts": ts,
            "phase": "Implement",
            "agent": "implementer",
            "summary": "did a thing",
            "status": "ok",
            "execution_id": execution_id,
            "provider": provider,
            "ticket_id": ticket_id,
        },
        {
            "run_id": ticket_id,
            "seq": seq_start + 1,
            "ts": ts,
            "phase": "Verify",
            "agent": "done-checker",
            "summary": "did another thing",
            "status": "ok",
            "execution_id": execution_id,
            "provider": provider,
            "ticket_id": ticket_id,
        },
    ]
    _run_writer_tool(_RECORD_EVENTS_PATH, ["--data", json.dumps(events)], cwd=cwd)

    run_record = {
        "run_id": ticket_id,
        "execution_id": execution_id,
        "provider": provider,
        "ticket_id": ticket_id,
        "start_ts": ts,
        "end_ts": ts,
        "workflow": "implement-ticket",
        "tier": "standard",
        "final_status": "DONE",
        "agent_count": len(events),
    }
    _run_writer_tool(_RECORD_RUN_PATH, ["--data", json.dumps(run_record)], cwd=cwd)

    session_id = f"sess-{execution_id}"
    _write_sidecar(
        cwd,
        run_id=ticket_id,
        seq=seq_start,
        phase="Implement",
        agent="implementer",
        execution_id=execution_id,
        provider=provider,
        ticket_id=ticket_id,
        session_id=session_id,
    )
    _run_post_tool_hook(cwd, session_id=session_id, command="pytest tests/")

    return {"execution_id": execution_id, "provider": provider, "ticket_id": ticket_id}


# ---------------------------------------------------------------------------
# Duplicate-key-sensitive parse — a plain json.loads(line) would silently keep only the last
# value for a repeated key, hiding exactly the failure mode Part B exists to catch.
# ---------------------------------------------------------------------------


class DuplicateJsonKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise DuplicateJsonKeyError(f"duplicate key {key!r} found in JSON object")
        seen[key] = value
    return seen


def _parse_no_duplicate_keys(line: str) -> dict:
    return json.loads(line, object_pairs_hook=_reject_duplicate_keys)


def _seed_one_legacy_line_per_file(agent_monitoring_dir: Path) -> None:
    """Seeds both the now-inert legacy `tools.jsonl` (proves it is never resurrected by a stray
    write — the real hook has not touched it since TCK-20260902-MONITORING-SHARD-WRITE-PATH) and
    the real current-week sharded file the hook actually writes to (gives the prefix-unchanged /
    append-only assertions genuine pre-existing content on the real write target)."""
    legacy_event = {
        "run_id": "TCK-LEGACY", "seq": 1, "ts": "2026-01-01T00:00:00Z", "phase": "Implement",
        "agent": "implementer", "summary": "legacy row", "status": "ok",
    }
    legacy_run = {
        "run_id": "TCK-LEGACY", "start_ts": "2026-01-01T00:00:00Z", "workflow": "implement-ticket",
        "tier": "standard", "final_status": "DONE", "agent_count": 1,
    }
    legacy_tool = {
        "session_id": "sess-legacy", "run_id": "TCK-LEGACY", "seq": 1, "phase": "Implement",
        "agent": "implementer", "ts": "2026-01-01T00:00:00Z", "tool": "Bash",
        "input_summary": "legacy", "status": "ok", "duration_ms": 10,
        "execution_id": None, "provider": None, "ticket_id": None,
    }
    (agent_monitoring_dir / "events.jsonl").write_text(json.dumps(legacy_event) + "\n")
    (agent_monitoring_dir / "runs.jsonl").write_text(json.dumps(legacy_run) + "\n")
    (agent_monitoring_dir / "tools.jsonl").write_text(json.dumps(legacy_tool) + "\n")

    tools_shard_file = _current_week_tools_file(agent_monitoring_dir)
    tools_shard_file.parent.mkdir(parents=True, exist_ok=True)
    tools_shard_file.write_text(json.dumps(legacy_tool) + "\n")


# ---------------------------------------------------------------------------
# Step 5 (AC1, AC2): one execution shares one identity; a second execution differs.
# ---------------------------------------------------------------------------


def test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources(tmp_path):
    identity_1 = _perform_one_simulated_execution(tmp_path, ticket_id="TCK-EXEC-IDENTITY-ONE")

    events_file = tmp_path / "agent-monitoring" / "events.jsonl"
    runs_file = tmp_path / "agent-monitoring" / "runs.jsonl"
    tools_file = _current_week_tools_file(tmp_path / "agent-monitoring")

    events_lines = events_file.read_text().strip().splitlines()
    runs_lines = runs_file.read_text().strip().splitlines()
    tools_lines = tools_file.read_text().strip().splitlines()

    assert len(events_lines) == 2
    assert len(runs_lines) == 1
    assert len(tools_lines) == 1

    for line in events_lines + runs_lines + tools_lines:
        record = json.loads(line)
        assert record["execution_id"] == identity_1["execution_id"]
        assert record["provider"] == "claude"
        assert record["execution_id"]  # non-empty

    # A second, independent execution against the SAME ticket_id gets a DIFFERENT execution_id —
    # identity is per-execution, not per-ticket.
    identity_2 = _perform_one_simulated_execution(
        tmp_path, ticket_id="TCK-EXEC-IDENTITY-ONE", seq_start=3
    )
    assert identity_2["execution_id"] != identity_1["execution_id"]
    assert identity_2["ticket_id"] == identity_1["ticket_id"]

    events_lines_after = events_file.read_text().strip().splitlines()
    assert len(events_lines_after) == 4
    new_event_execution_ids = {json.loads(line)["execution_id"] for line in events_lines_after[2:]}
    assert new_event_execution_ids == {identity_2["execution_id"]}


# ---------------------------------------------------------------------------
# Step 6, Part A (AC6): pre-existing lines/bytes remain unchanged; only appends happen.
# ---------------------------------------------------------------------------


def test_baseline_prefix_unchanged_after_new_identity_writes(tmp_path):
    agent_monitoring_dir = tmp_path / "agent-monitoring"
    agent_monitoring_dir.mkdir(parents=True)
    _seed_one_legacy_line_per_file(agent_monitoring_dir)

    events_file = agent_monitoring_dir / "events.jsonl"
    runs_file = agent_monitoring_dir / "runs.jsonl"
    tools_file = _current_week_tools_file(agent_monitoring_dir)

    events_prefix_before = events_file.read_text()
    runs_prefix_before = runs_file.read_text()
    tools_prefix_before = tools_file.read_text()
    legacy_tools_prefix_before = (agent_monitoring_dir / "tools.jsonl").read_text()
    events_checksum_before = hashlib.sha256(events_prefix_before.encode("utf-8")).hexdigest()
    runs_checksum_before = hashlib.sha256(runs_prefix_before.encode("utf-8")).hexdigest()
    tools_checksum_before = hashlib.sha256(tools_prefix_before.encode("utf-8")).hexdigest()

    _perform_one_simulated_execution(tmp_path, ticket_id="TCK-NEW-IDENTITY", seq_start=1)

    events_after = events_file.read_text()
    runs_after = runs_file.read_text()
    tools_after = tools_file.read_text()

    # Pure append: the pre-existing prefix bytes are untouched — never rewritten.
    assert events_after.startswith(events_prefix_before)
    assert runs_after.startswith(runs_prefix_before)
    assert tools_after.startswith(tools_prefix_before)
    assert hashlib.sha256(events_after[: len(events_prefix_before)].encode("utf-8")).hexdigest() == events_checksum_before
    assert hashlib.sha256(runs_after[: len(runs_prefix_before)].encode("utf-8")).hexdigest() == runs_checksum_before
    assert hashlib.sha256(tools_after[: len(tools_prefix_before)].encode("utf-8")).hexdigest() == tools_checksum_before

    # Exactly N + appended-record-count lines — pure append, no drop, no in-place mutation.
    assert len(events_after.strip().splitlines()) == 1 + 2
    assert len(runs_after.strip().splitlines()) == 1 + 1
    assert len(tools_after.strip().splitlines()) == 1 + 1

    # The legacy literal `tools.jsonl` (pre-sharding write target) is never resurrected by a
    # stray write — the real hook writes only to the current-week shard.
    assert (agent_monitoring_dir / "tools.jsonl").read_text() == legacy_tools_prefix_before


# ---------------------------------------------------------------------------
# Step 6, Part B (AC6): the newly appended lines are themselves well-formed — no
# duplicate/colliding identity keys, run_id not clobbered, all four identity fields singular
# and correctly valued.
# ---------------------------------------------------------------------------


def test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values(tmp_path):
    agent_monitoring_dir = tmp_path / "agent-monitoring"
    agent_monitoring_dir.mkdir(parents=True)
    _seed_one_legacy_line_per_file(agent_monitoring_dir)

    events_file = agent_monitoring_dir / "events.jsonl"
    runs_file = agent_monitoring_dir / "runs.jsonl"
    tools_file = _current_week_tools_file(agent_monitoring_dir)

    identity = _perform_one_simulated_execution(tmp_path, ticket_id="TCK-CONTENT-CHECK", seq_start=1)

    new_event_lines = events_file.read_text().strip().splitlines()[1:]
    new_run_lines = runs_file.read_text().strip().splitlines()[1:]
    new_tool_lines = tools_file.read_text().strip().splitlines()[1:]

    assert len(new_event_lines) == 2
    assert len(new_run_lines) == 1
    assert len(new_tool_lines) == 1

    for line in new_event_lines + new_run_lines + new_tool_lines:
        # Raw-text occurrence count: catches a malformed-but-still-parseable duplicate that an
        # object_pairs_hook alone might not isolate (e.g. nested under an unexpected key).
        for field_marker in ('"execution_id":', '"provider":', '"ticket_id":', '"run_id":'):
            assert line.count(field_marker) == 1, (
                f"{field_marker} does not appear exactly once in appended line: {line}"
            )

        # Duplicate-key-sensitive parse: raises if any top-level key repeats (plain json.loads
        # would silently keep only the last value instead).
        record = _parse_no_duplicate_keys(line)

        assert record["run_id"] == "TCK-CONTENT-CHECK"
        assert record["execution_id"] == identity["execution_id"]
        assert record["provider"] == "claude"
        assert record["ticket_id"] == "TCK-CONTENT-CHECK"
        for key in ("run_id", "execution_id", "provider", "ticket_id"):
            assert record[key], f"{key} must be non-empty/non-null in {record}"
