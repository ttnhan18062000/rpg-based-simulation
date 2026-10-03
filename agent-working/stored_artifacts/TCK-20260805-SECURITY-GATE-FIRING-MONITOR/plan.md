---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-SECURITY-GATE-FIRING-MONITOR
artifact_type: plan
tags: [skills, agent-monitoring]
---

# Plan — TCK-20260805-SECURITY-GATE-FIRING-MONITOR

## Decision: standalone script, not a `generate_retro.py` section
Per the ticket's own open question. `generate_retro.py`'s `tag_breakdown_skill` already covers the
*reporting* need (aggregate hit counts for the weekly retro). This ticket needs a strict
pass/fail *check* — a different consumer shape (a gate-style tool an agent or CI step can run and
get a definitive miss list from), matching `retrieval_baseline_metrics.py`'s own precedent of
being a separate, purpose-built script rather than folded into the retro's Markdown-rendering
concerns. Reuses `generate_retro.py`'s private helpers by import, per that same precedent.

## New File: `tools/agent-monitoring/security_gate_firing_check.py`

```
_BOOTSTRAP_EXCEPTION_TICKETS = frozenset({"TCK-20260705-WORKFLOW-SECURITY-GATE"})
# ^ the ticket that added phase('Security-Review') to implement-ticket.js itself — its own
#   implementation ran under the pre-gate JS, so it structurally could not have fired a gate
#   that did not yet exist when it ran. Excluded, not flagged, with this comment as the record
#   of why (mirrors _TAG_GATE_PHASE's own load-bearing-comment convention in generate_retro.py).

def check_security_gate_firing(tickets_root=None) -> dict:
    """Reads real runs.jsonl/events.jsonl (via generate_retro._load_runs_and_events) and
    tickets/done/ + tickets/inprogress/ frontmatter (via generate_retro._collect_tagged_tickets).
    For every ticket tagged `security` (excluding _BOOTSTRAP_EXCEPTION_TICKETS):
      - if the ticket has at least one DONE-resolved runs.jsonl record AND at least one
        Security-Review event (or SECURITY_BLOCKED final_status) anywhere in its run history:
        -> 'clean'
      - if the ticket has at least one DONE-resolved runs.jsonl record and NEITHER of the above:
        -> 'missed'
      - if the ticket has zero DONE-resolved runs.jsonl records (still in progress, blocked, or
        no run data at all): -> 'pending' (not yet evaluable, not silently dropped)
    Returns {"missed": [...], "clean": [...], "pending": [...], "excluded": [...],
             "derivation": "..."} — same disclosure-string convention as
    retrieval_baseline_metrics.py's build_*_section functions.
    """
```

Logic reuses `generate_retro._collect_tagged_tickets`, `generate_retro._load_runs_and_events`,
`generate_retro._resolve_status` by direct import (no reimplementation).

## Test File: `tests/tools/test_security_gate_firing_check.py`
- One test against the live corpus (per Test Plan's Normal Flow) — asserts today's real,
  known-correct classification.
- Two synthetic unit tests (per Test Plan's Failure Modes) with hand-built `runs`/`events` fixtures
  reproducing the miss shape and the clean-fire shape, independent of the live corpus so the logic
  itself is verified, not just today's data.
- One test confirming `_BOOTSTRAP_EXCEPTION_TICKETS` ticket never appears in `missed` or `clean`.
- One test confirming a zero-run-record ticket does not raise and lands in `pending`.

## Document-Update
Add a short section to `docs/agent-monitoring/README.md` (mirrors the existing "Baseline Metrics
Snapshot" section's shape) pointing at the new script, one sentence on what it checks and why it's
separate from the retro's aggregate tag breakdown.

## Parity
No `src/` files touched — `expected_subsystems_for_files()` on the new `tools/`/`tests/`/`docs/`
paths returns `{}`. No parity ledger entry needed, same precedent as this batch's earlier tickets.

## Acceptance-Criteria Map
- AC1 (new checker exists, follows house pattern) → `security_gate_firing_check.py`'s
  `_BOOTSTRAP_EXCEPTION_TICKETS` frozen constant + `derivation` string.
- AC2 (flags the known miss) → live-corpus test + synthetic miss-shape test.
- AC3 (passes clean for confirmed-good tickets) → live-corpus test + synthetic clean-shape test.
- AC4 (no duplication of RETRO-TAG-BREAKDOWN) → `generate_retro.py` not modified; its existing
  tests re-run unchanged as a regression check.
