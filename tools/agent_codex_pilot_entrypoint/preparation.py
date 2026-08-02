"""Just-in-time, policy-excluded baseline construction; never invokes a pilot."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from tools.agent_codex_realrepo_pilot_harness.proofs import capture_policy_baseline, tree_digest
from tools.agent_codex_realrepo_pilot_harness.preflight import PilotHarnessContext


_CANDIDATE = "TCK-20260801-MONITORING-WRITER-STATUS-STALE"
_REQUEST = f"pilot_requests/{_CANDIDATE}.yaml"
_TARGET = "tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md"
_DEFAULT_MAX_TOOL_CALLS = 200


@dataclass(frozen=True)
class PreparedPolicy:
    policy_path: Path
    baseline_sha256: str


def prepare_policy(repo_root: Path | str, execution_id: str) -> PreparedPolicy:
    """Write a fresh self-excluded policy for one fixed candidate attempt."""
    root = Path(repo_root).resolve()
    request = root / _REQUEST
    if not request.is_file():
        raise ValueError("fixed pilot request is missing")
    candidate = root / "tickets" / "inprogress" / f"{_CANDIDATE}.md"
    if not candidate.is_file():
        raise ValueError("fixed candidate is missing")
    evidence = root / "pilot_evidence" / _CANDIDATE
    evidence.mkdir(parents=True, exist_ok=True)
    policy_path = evidence / "policy.json"
    request_sha = hashlib.sha256(request.read_bytes()).hexdigest()
    common = {
        "version": 1, "candidate_ticket_id": _CANDIDATE, "request_sha256": request_sha,
        "target_path": _TARGET,
        "target_transitions": {"status": ["active", "historical"], "phase": ["open", "done"], "body_status": ["OPEN", "DONE"]},
        "allowed_paths": [
            _TARGET,
            f"tickets/inprogress/{_CANDIDATE}.md",
            f"tickets/done/{_CANDIDATE}.md",
            "tickets/working_log.csv",
            "docs/REGISTRY.yaml",
            ".codex/config.toml",
        ],
        "monitoring_suffixes": {"runs.jsonl": [], "events.jsonl": [], "tools.jsonl": []},
        "bounded_tool_suffix": {
            "execution_id": execution_id,
            "ticket_id": _CANDIDATE,
            "provider": "codex",
            "run_id": _CANDIDATE,
            "max_tool_calls": _DEFAULT_MAX_TOOL_CALLS,
        },
    }
    policy_path.write_text(json.dumps({**common, "baseline_sha256": "0" * 64}, separators=(",", ":")))
    baseline = tree_digest(capture_policy_baseline(root, policy_path))
    policy_path.write_text(json.dumps({**common, "baseline_sha256": baseline}, separators=(",", ":")))
    return PreparedPolicy(policy_path, baseline)


def prepare_context(repo_root: Path | str, execution_id: str) -> PilotHarnessContext:
    """Prepare fixed candidate evidence only; this function never invokes a pilot."""
    root = Path(repo_root).resolve()
    policy = prepare_policy(root, execution_id)
    return PilotHarnessContext(
        repo_root=root,
        ticket_id=_CANDIDATE,
        execution_id=execution_id,
        candidate_path=f"tickets/inprogress/{_CANDIDATE}.md",
        request_path=_REQUEST,
        policy_path=policy.policy_path.relative_to(root).as_posix(),
        enabled_hook_events=frozenset({"PostToolUse"}),
        enabled_writer_names=frozenset({"write_line", "write_lines"}),
        concurrent_runs=(),
    )
