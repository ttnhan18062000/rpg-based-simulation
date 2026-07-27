"""Typed pilot-request manifest + loader (TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 1).

Storage convention: one YAML file per candidate at pilot_requests/<ticket_id>.yaml — a new,
dedicated top-level directory, not stored_artifacts/{ticket_id}/ (that is the *pilot* ticket's own
build artifacts, migrated only after *that* ticket closes) or staging_artifacts/{ticket_id}/
(this ticket's own in-flight artifacts). A pilot request is a human's standing authorization
record about a candidate ticket, authored before pilot selection ever runs, independent of that
ticket's own phase — it needs its own stable location, lifecycle, and inspection visibility
(`ls pilot_requests/`). See pilot_requests/README.md for the schema.

Deliberately does not extend the universal ticket template/frontmatter schema (CLAUDE.md's Ticket
Format, tools/ticket_field_values.py) — that is a repo-wide change affecting every ticket and is
out of this ticket's scope.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import (
    MissingHumanOwnerError,
    MissingRollbackPlanError,
    PilotManifestValidationError,
)


@dataclass(frozen=True)
class PilotRequest:
    ticket_id: str
    human_owner: str
    rollback_plan_summary: str


def load_pilot_request(path: Path) -> PilotRequest:
    """Parse a pilot-request YAML file into a PilotRequest.

    Strict fail-clear check: no default/fallback value, no coercion of a missing field to "".
    Reads only the structured `ticket_id`/`human_owner`/`rollback_plan_summary` keys — free-text
    prose elsewhere in the file is never accepted as evidence.
    """
    if not path.exists():
        raise PilotManifestValidationError(f"pilot request file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise PilotManifestValidationError(f"{path}: pilot request YAML root must be a mapping")

    ticket_id = data.get("ticket_id")
    human_owner = data.get("human_owner")
    rollback_plan_summary = data.get("rollback_plan_summary")

    if not isinstance(human_owner, str) or not human_owner.strip():
        raise MissingHumanOwnerError(f"{path}: human_owner is missing or empty")
    if not isinstance(rollback_plan_summary, str) or not rollback_plan_summary.strip():
        raise MissingRollbackPlanError(f"{path}: rollback_plan_summary is missing or empty")
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise PilotManifestValidationError(f"{path}: ticket_id is missing or empty")

    return PilotRequest(
        ticket_id=ticket_id,
        human_owner=human_owner,
        rollback_plan_summary=rollback_plan_summary,
    )
