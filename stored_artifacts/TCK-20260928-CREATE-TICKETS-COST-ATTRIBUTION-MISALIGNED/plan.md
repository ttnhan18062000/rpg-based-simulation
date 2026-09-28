---
status: active
layer: observability
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED
date: 2026-09-28
tags: [agent-monitoring, data-quality]
---

# Plan — TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED

Per investigation.md: anomaly 1 (09-13) is the known concurrent-session sidecar-sharing class,
recorded and not re-solved. Anomalies 2/3 (09-23) plus the independently-found write-sequence
missing-event gap are real, fixable defects in `.claude/workflows/create-tickets.js`.

## Steps

1. **`write-sequence` gets a matching event.** Capture the `write-sequence` `agent()` call's
   result and add a `pushEvent('Write', 'write-sequence', ...)` right after it, so its own
   tool-call rows have an event to attribute against.
2. **`writeMonitoring()` clears the sidecar first.** Add a "Step 0 — clear the tool-tracking
   sidecar" instruction to `create-tickets.js`'s own `writeMonitoring` agent prompt, mirroring
   `implement-ticket.js`'s own established wording/rationale exactly (`printf '{}' >
   .claude/current_run`, before Steps 1-3). Since every real exit path already calls
   `writeMonitoring()` immediately before its own `return`, this one change covers every exit path
   — no separate per-return reset logic needed.
3. **`writeSidecar()` surfaces failures instead of swallowing them.** Replace the blanket
   `2>/dev/null || true` with an explicit exit-code marker (`echo "WRITESIDECAR_EXIT:$?"`,
   unconditional, not gated behind `&&` — the shell command itself must still always exit 0, per
   the monitoring fail-open rule) and a `log()` WARNING when the marker isn't `WRITESIDECAR_EXIT:0`
   — mirrors this file's own existing WARNING conventions (e.g. failed write agents).
4. Update `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION`'s Implementation Notes with the
   outcome (already partially updated with the 2026-09-28 partial check that found this ticket;
   append a note that the fix has landed, but AC2 stays open until confirmed against the *next*
   real `create-tickets` run — this ticket's own fix cannot retroactively fix the two historical
   runs' already-recorded rows, per this ticket's own Out of Scope).

## Explicitly not done (per Out of Scope)

- Wiring sidecar coverage into the `investigate`/`write` `pipeline()` fan-out sites — deliberate,
  documented concurrency exclusion, unrelated to this ticket's fixes.
- Rewriting the historical W37/W39 event values.
- Root-causing anomaly 1's exact concurrent session/workflow — recorded as unconfirmable.
