"""Adapter entrypoint: wires input parsing, identity validation, the live-append gate, record
construction, and the shared writer bridge into one fail-open call (Step 6).

Sequence, each stage short-circuiting to `return False` on any exception, with no call to
writer_bridge.write_line ever reached after a failure: (1) parse the raw stdin payload; (2)
validate execution identity; (3) check the live-append gate BEFORE any write; (4) build the
redacted record; (5) append via writer_bridge, itself wrapped in its own inner try/except as
defense-in-depth against write_line violating its own documented no-raise contract.

No separate diagnostic-write mechanism is added in this module: writer.py's own internal
_write_diagnostic sidecar (.writer_health.jsonl, triggered automatically on any write failure)
already satisfies hook-surface-policy.yaml's out_of_band_diagnostics prerequisite for this call
site — adding a second diagnostic writer here would reimplement writer.py's own machinery.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from . import identity, input_model, live_gate, record_builder, writer_bridge


def process_post_tool_use(
    raw_payload: dict,
    *,
    target_path: Path,
    execution_id: str,
    ticket_id: str,
    provider: str = "codex",
    run_id: str | None = None,
    seq: int | None = None,
    phase: str | None = None,
    agent: str | None = None,
    env: Mapping[str, str] | None = None,
    now: str | None = None,
) -> bool:
    try:
        payload = input_model.parse_payload(raw_payload)
        identity.validate_identity(provider, execution_id, ticket_id)
        live_gate.require_live_append(env)

        record = record_builder.build_record(
            payload,
            execution_id=execution_id,
            provider=provider,
            ticket_id=ticket_id,
            run_id=run_id,
            seq=seq,
            phase=phase,
            agent=agent,
            now=now,
        )

        try:
            ok = writer_bridge.write_line(target_path, json.dumps(record, separators=(",", ":")))
        except Exception:
            return False
        return bool(ok)
    except Exception:
        return False
