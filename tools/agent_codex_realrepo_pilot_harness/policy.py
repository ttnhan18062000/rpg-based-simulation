"""Immutable, scratch-root-contained expected-write policy."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("policy path must be a safe relative path")
    path = Path(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("policy path must be a safe relative path")
    return path.as_posix()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ExpectedWritePolicy:
    path: Path
    sha256: str
    candidate_ticket_id: str
    request_sha256: str
    baseline_sha256: str
    target_path: str
    target_transitions: Mapping[str, tuple[str, str]]
    allowed_paths: frozenset[str]
    monitoring_suffixes: Mapping[str, tuple[dict, ...]]
    bounded_tool_suffix: Mapping[str, object] | None = None

    def verify_unchanged(self) -> bool:
        return self.path.is_file() and _sha256(self.path.read_bytes()) == self.sha256


def load_policy_file(path: Path | str, candidate_ticket_id: str) -> ExpectedWritePolicy:
    policy_path = Path(path).resolve()
    raw = policy_path.read_bytes()
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("policy is not valid JSON") from exc
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("policy version is invalid")
    if data.get("candidate_ticket_id") != candidate_ticket_id:
        raise ValueError("policy candidate binding is invalid")
    transitions_raw = data.get("target_transitions")
    required = {"status", "phase", "body_status"}
    if not isinstance(transitions_raw, dict) or set(transitions_raw) != required:
        raise ValueError("policy must declare exactly the three target transitions")
    transitions: dict[str, tuple[str, str]] = {}
    for key, value in transitions_raw.items():
        if not isinstance(value, list) or len(value) != 2 or not all(isinstance(part, str) for part in value):
            raise ValueError("policy target transitions are invalid")
        transitions[key] = (value[0], value[1])
    allowed_raw = data.get("allowed_paths")
    if not isinstance(allowed_raw, list) or not allowed_raw:
        raise ValueError("policy allowlist is invalid")
    allowed = frozenset(_safe_relative_path(item) for item in allowed_raw)
    target = _safe_relative_path(data.get("target_path"))
    if target not in allowed:
        raise ValueError("policy target is not allowlisted")
    suffixes_raw = data.get("monitoring_suffixes")
    required_monitoring = {"runs.jsonl", "events.jsonl", "tools.jsonl"}
    if not isinstance(suffixes_raw, dict) or set(suffixes_raw) != required_monitoring:
        raise ValueError("policy monitoring suffix contract is invalid")
    suffixes: dict[str, tuple[dict, ...]] = {}
    for name, records in suffixes_raw.items():
        if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
            raise ValueError("policy monitoring suffix rows are invalid")
        suffixes[name] = tuple(records)
    hashes = (data.get("request_sha256"), data.get("baseline_sha256"))
    if not all(isinstance(item, str) and len(item) == 64 for item in hashes):
        raise ValueError("policy request/baseline hash binding is invalid")
    bounded = data.get("bounded_tool_suffix")
    if bounded is not None:
        required_bounded = {"execution_id", "ticket_id", "provider", "run_id", "max_tool_calls"}
        if not isinstance(bounded, dict) or set(bounded) != required_bounded:
            raise ValueError("policy bounded tool suffix contract is invalid")
        if not all(isinstance(bounded[name], str) and bounded[name] for name in required_bounded - {"max_tool_calls"}):
            raise ValueError("policy bounded tool identity is invalid")
        cap = bounded["max_tool_calls"]
        if not isinstance(cap, int) or isinstance(cap, bool) or cap < 0:
            raise ValueError("policy bounded tool cap is invalid")
    return ExpectedWritePolicy(policy_path, _sha256(raw), candidate_ticket_id, hashes[0], hashes[1], target,
                               transitions, allowed, suffixes, bounded)
