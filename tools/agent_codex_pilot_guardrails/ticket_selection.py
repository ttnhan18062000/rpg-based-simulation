"""Ticket-selection step: owner/rollback-plan gate + concurrent-claim gate
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 2).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import pilot_manifest
from .errors import ConcurrentProviderClaimError, PilotManifestValidationError
from .pilot_manifest import PilotRequest


def select_pilot_candidate(ticket_id: str, pilot_requests_dir: Path) -> PilotRequest:
    """Load and validate the pilot request for ticket_id.

    pilot_requests_dir is an injected parameter (never hardcoded to the real pilot_requests/) so
    callers/tests can point it at a scratch directory.
    """
    request_path = pilot_requests_dir / f"{ticket_id}.yaml"
    if not request_path.exists():
        raise PilotManifestValidationError(
            f"no pilot request found for ticket_id={ticket_id!r} at {request_path}"
        )
    return pilot_manifest.load_pilot_request(request_path)


def assert_no_concurrent_claim(ticket_id: str, run_records: list[dict]) -> None:
    """Raise ConcurrentProviderClaimError if two or more in-progress records (end_ts absent/None)
    for ticket_id carry two different provider values.

    run_records is shaped like agent-monitoring/runs.jsonl records (each with at minimum
    ticket_id, provider, end_ts). This check is proven only against synthetic fixture lists
    constructed in-test — see provider_field_coverage's own docstring for why.
    """
    in_progress_providers: set[str] = set()
    for record in run_records:
        if record.get("ticket_id") != ticket_id:
            continue
        if record.get("end_ts"):
            continue
        provider = record.get("provider")
        if provider is not None:
            in_progress_providers.add(provider)
    if len(in_progress_providers) > 1:
        raise ConcurrentProviderClaimError(
            f"ticket_id={ticket_id!r} is concurrently claimed by multiple providers: "
            f"{sorted(in_progress_providers)}"
        )


def provider_field_coverage(agent_monitoring_dir: Path) -> int:
    """Stream agent-monitoring/runs.jsonl (line-lazy, mirroring manifest.py::_scan_file's own
    streaming technique — never a full read) and count records carrying a non-null provider key.

    Exists specifically so a test can assert the real corpus currently has zero provider-bearing
    records: .claude/workflows/implement-ticket.js does not construct one on any real run today
    (confirmed by investigation.md Risk #3). assert_no_concurrent_claim above is real, tested
    code that is currently unexercised by real production data — this function makes that gap
    visible rather than silently assumed away. Populating provider/execution_id on real writes is
    explicitly out of this ticket's scope.
    """
    runs_path = agent_monitoring_dir / "runs.jsonl"
    count = 0
    with open(runs_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            if record.get("provider") is not None:
                count += 1
    return count
