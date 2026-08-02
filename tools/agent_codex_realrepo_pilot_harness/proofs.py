"""Captured-policy post-run proofs for injected scratch repositories."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .preflight import PreflightResult


def capture_tree(root: Path | str, *, excluded_paths: set[str] | None = None) -> dict[str, bytes]:
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError("scratch root must exist before a baseline is captured")
    result: dict[str, bytes] = {}
    excluded_paths = excluded_paths or set()
    for path in base.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed in scratch proof tree: {path}")
        if path.is_file():
            relative = path.relative_to(base).as_posix()
            if relative not in excluded_paths:
                result[relative] = path.read_bytes()
    return result


def capture_policy_baseline(root: Path | str, policy_path: Path | str) -> dict[str, bytes]:
    """Capture the judged tree while excluding the self-referential policy bytes.

    Canonical evidence order is: write policy, capture this baseline excluding
    only that policy's relative path, then compare the policy's declared digest.
    """
    base = Path(root).resolve()
    policy = Path(policy_path).resolve()
    try:
        relative = policy.relative_to(base).as_posix()
    except ValueError as exc:
        raise ValueError("policy path must be contained by baseline root") from exc
    return capture_tree(base, excluded_paths={relative})


def tree_digest(tree: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(tree):
        digest.update(path.encode("utf-8") + b"\0" + hashlib.sha256(tree[path]).digest())
    return digest.hexdigest()


def assert_expected_changes(before: dict[str, bytes], after: dict[str, bytes], allowed_paths: set[str]) -> None:
    changed = {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}
    unallowed = changed - allowed_paths
    if unallowed:
        raise ValueError(f"changed paths are not allowlisted: {sorted(unallowed)}")


def assert_monitoring_prefixes(before: dict[str, list[bytes]], after: dict[str, list[bytes]]) -> None:
    for filename, prefix in before.items():
        if after.get(filename, [])[:len(prefix)] != prefix:
            raise ValueError(f"{filename}: monitoring prefix was rewritten, deleted, or reordered")


def _lines(tree: dict[str, bytes], name: str) -> list[bytes]:
    return tree.get(f"agent-monitoring/{name}", b"").splitlines(keepends=True)


def _parse_iso8601(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO-8601 string")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601") from exc


def assert_bounded_tool_suffix(
    before_lines: list[bytes],
    after_lines: list[bytes],
    expected_identity: dict[str, str],
    *,
    max_tool_calls: int,
    run_start_iso: str,
    run_end_iso: str,
) -> None:
    """Check live PostToolUse rows without weakening static exact-suffix proofs.

    Hooks can legitimately produce an unknown number of rows and their timestamps are produced
    at callback time.  This narrow post-hoc proof instead binds every knowable field exactly and
    rejects rows outside a reviewed count and transport-time window.
    """
    if after_lines[: len(before_lines)] != before_lines:
        raise ValueError("tools.jsonl: monitoring prefix was rewritten, deleted, or reordered")
    if not isinstance(max_tool_calls, int) or isinstance(max_tool_calls, bool) or max_tool_calls < 0:
        raise ValueError("max tool-call count is invalid")
    start, end = _parse_iso8601(run_start_iso), _parse_iso8601(run_end_iso)
    if end < start:
        raise ValueError("timestamp window is invalid")
    suffix = after_lines[len(before_lines) :]
    if len(suffix) > max_tool_calls:
        raise ValueError("tool-call count exceeds policy cap")
    for expected_seq, raw in enumerate(suffix, start=1):
        try:
            row = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("tools.jsonl suffix is not valid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError("tools.jsonl suffix row is not an object")
        for field, value in expected_identity.items():
            if row.get(field) != value:
                raise ValueError(f"tools.jsonl {field} does not match captured identity")
        if row.get("seq") != expected_seq:
            raise ValueError("tools.jsonl seq is not contiguous from one")
        ts = _parse_iso8601(row.get("ts"))
        if ts < start or ts > end:
            raise ValueError("tools.jsonl timestamp is outside transport window")


def _assert_target_transition(result: "PreflightResult", after: dict[str, bytes]) -> None:
    policy = result.policy
    before = result.baseline_tree.get(policy.target_path)
    observed = after.get(policy.target_path)
    if before is None or observed is None:
        raise ValueError("historical target must remain present")
    text = before.decode("utf-8")
    expected = text
    for field, (old, new) in policy.target_transitions.items():
        if field == "body_status":
            needle, replacement = f"## Status\n{old}", f"## Status\n{new}"
        else:
            needle, replacement = f"{field}: {old}", f"{field}: {new}"
        if expected.count(needle) != 1:
            raise ValueError("historical target transition does not match exact policy")
        expected = expected.replace(needle, replacement, 1)
    if observed != expected.encode("utf-8"):
        raise ValueError("historical target did not change exactly as declared")


def _assert_suffixes(result: "PreflightResult", after: dict[str, bytes]) -> None:
    for name, rows in result.policy.monitoring_suffixes.items():
        before_lines = _lines(result.baseline_tree, name)
        after_lines = _lines(after, name)
        if after_lines[:len(before_lines)] != before_lines:
            raise ValueError(f"{name}: monitoring prefix was rewritten, deleted, or reordered")
        expected = [json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n" for row in rows]
        if after_lines[len(before_lines):] != expected:
            raise ValueError(f"{name}: monitoring suffix does not match captured policy")


def assert_post_run_proof(
    result: "PreflightResult",
    after: dict[str, bytes],
    *,
    run_start_iso: str | None = None,
    run_end_iso: str | None = None,
) -> None:
    """Verify against policy captured in preflight, never a caller allowlist/re-read."""
    if not result.policy.verify_unchanged():
        raise ValueError("captured expected-write policy was modified")
    monitoring = {f"agent-monitoring/{name}" for name in result.policy.monitoring_suffixes}
    policy_relative = result.policy.path.relative_to(result.root).as_posix()
    after = {path: value for path, value in after.items() if path != policy_relative}
    assert_expected_changes(result.baseline_tree, after, set(result.policy.allowed_paths) | monitoring)
    _assert_target_transition(result, after)
    bounded = result.policy.bounded_tool_suffix
    if bounded is None:
        _assert_suffixes(result, after)
        return
    static_policy = replace(
        result.policy,
        monitoring_suffixes={
            name: rows for name, rows in result.policy.monitoring_suffixes.items() if name != "tools.jsonl"
        },
    )
    static_result = replace(result, policy=static_policy)
    _assert_suffixes(static_result, after)
    if run_start_iso is None or run_end_iso is None:
        raise ValueError("bounded tool suffix requires captured transport time window")
    assert_bounded_tool_suffix(
        _lines(result.baseline_tree, "tools.jsonl"),
        _lines(after, "tools.jsonl"),
        {
            name: str(bounded[name])
            for name in ("execution_id", "ticket_id", "provider", "run_id")
        },
        max_tool_calls=int(bounded["max_tool_calls"]),
        run_start_iso=run_start_iso,
        run_end_iso=run_end_iso,
    )
