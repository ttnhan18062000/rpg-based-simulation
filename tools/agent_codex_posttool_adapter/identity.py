"""Execution identity validation: format-only ticket_id, execution_id shape, and a strict
provider=="codex" equality check (Step 3).

**Format-valid only — no filesystem existence check** against tickets/inprogress/ or
tickets/done/. See staging_artifacts/TCK-20260730-CODEX-POSTTOOL-ADAPTER/plan.md's "Resolution —
what makes a ticket_id 'known'": the parallel Claude convention
(.claude/workflows/implement-ticket.js's execution_id generation) performs no independent
filesystem check at the point of identity generation either — it trusts the ticket-scoper agent's
own prior validation. This module is pure and I/O-free by design; it does not import pathlib,
os.path, or anything from tickets/.
"""
from __future__ import annotations

import re

from .errors import IdentityValidationError

TICKET_ID_PATTERN = re.compile(r"^TCK-\d{8}-[A-Z][A-Z0-9-]*$")


def validate_identity(provider: str, execution_id: str, ticket_id: str) -> None:
    if provider != "codex":
        raise IdentityValidationError(f"provider must be exactly 'codex', got {provider!r}")

    if not TICKET_ID_PATTERN.fullmatch(ticket_id):
        raise IdentityValidationError(
            f"ticket_id {ticket_id!r} does not match {TICKET_ID_PATTERN.pattern!r}"
        )

    execution_id_pattern = re.compile(rf"^codex-{re.escape(ticket_id)}-\d+-[0-9a-f]{{8}}$")
    if not execution_id_pattern.fullmatch(execution_id):
        raise IdentityValidationError(
            f"execution_id {execution_id!r} does not match the expected shape for "
            f"ticket_id {ticket_id!r} (codex-{{ticket_id}}-{{unix_ts_ms}}-{{token_hex_8}})"
        )
