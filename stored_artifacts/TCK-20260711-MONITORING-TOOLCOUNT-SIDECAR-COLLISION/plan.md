---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
artifact_type: plan
tags: [agent-monitoring, data-quality, root-cause]
---

# Plan — TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

Scoping-level plan only — this ticket is opened and investigated, not implemented, in this session (explicit user choice). A future implementation session should treat this as the starting point, re-validate the open questions from `investigation.md` first, then execute.

## Direction

Two independent workstreams, both needed — one prevents future corruption, one detects it if prevention is imperfect:

### 1. Per-run-scoped sidecar (prevention)

Replace the single shared `.claude/current_run` path with a scheme that can't collide across runs:

- **Option A (favored, cheapest):** embed the `run_id` in the sidecar filename itself (e.g. `.claude/current_run.{run_id}`), and have `pre_tool_hook.py`/`post_tool_hook.py` resolve the active file via a small discovery step (most-recently-modified matching file, or an additional pointer file naming which run-scoped file is "current" — needs the discovery step designed carefully so it doesn't just reintroduce the same race one level up).
- **Option B:** add a monotonic nonce/write-timestamp to the sidecar's JSON content; the hook rejects a stale read if the nonce doesn't match what the orchestrator expects it to be at call time (requires the orchestrator to also verify its own write landed before proceeding, i.e. read-after-write check in `writeSidecar`).
- **Option C (largest change):** move attribution entirely server-side — the hook records raw `(session_id, ts, tool)` unconditionally, and `writeMonitoring`'s post-hoc join step reconstructs `(run_id, seq)` attribution using session_id + timestamp windows from `runs.jsonl`/`events.jsonl` instead of relying on any sidecar at all. Most robust to races, but a bigger rework of the join logic documented in `schema.md`.

Recommend starting design with Option A given it's the smallest change consistent with the existing architecture (sidecar-based, hook-read), and only escalating to B/C if A's discovery step turns out to be racy in practice too.

### 2. Drift-detection validation (detection)

Add a check — likely as a new function in `tools/agent-monitoring/validate.py`, following the existing pattern of that module's incomplete-run checks — that:
- Re-derives `tool_call_count` (and ideally `cost_proxy_score`) per `(run_id, seq)` directly from `tools.jsonl`
- Compares against the recorded value in `events.jsonl`
- Reports a drift count/list, the same shape as this investigation's ad hoc script, but as a maintained, re-runnable tool rather than a one-off

This should run on a cadence (the existing `agent-monitoring-retro` skill's cadence rule — weekly / after 5+ tickets — is a natural fit) so a future recurrence of Finding 1's pattern gets caught automatically instead of requiring another manual audit.

## Explicit non-goals for the fix

- No backfill of historical `tool_call_count`/`cost_proxy_score` — per append-only precedent, historical corruption is accepted, not repaired.
- No change to `cost_proxy.py`'s weighting formula — it's correct given its input; the input is what's corrupted.

## Sequencing recommendation

1. Confirm the open question (implement-epic same-session chaining vs. true concurrent sessions) first — it changes which of Option A/B/C is correct, so don't start implementation before this is resolved.
2. Build the drift-detection check (workstream 2) first regardless of workstream 1's outcome — it's independently useful, lower-risk, and gives a concrete before/after number to validate whichever prevention fix lands.
3. Implement the chosen prevention option (workstream 1).
4. Re-run drift-detection against a batch of new runs post-fix to confirm the mismatch rate actually drops, before closing the ticket.

---

## Addendum — resolution (superseding Options A/B/C above)

Resolving the open question (step 1) via direct code reading — not further speculation — found the mechanism is fully deterministic, not concurrency-dependent at all (see `investigation.md`'s addendum for the full trace). This eliminated Options A/B/C's premise (a race needing per-run isolation) and replaced it with two much smaller, surgical fixes:

1. **Scope-phase sidecar coverage** (net-new — the exact follow-up `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` itself recommended). In `.claude/workflows/implement-ticket.js`, right after `phase('Scope')`: if `ticketId` is provided (resuming), write the real `{run_id: ticketId, seq: 1}`; otherwise (creating a new ticket, `tid` not yet known), clear to `{}`. Can't reuse the `writeSidecar(seq)` helper — it closes over `tid`, which doesn't exist at this point in program order for the new-ticket branch.
2. **`writeMonitoring` self-pollution fix**. Moved the existing "Step 5 — clear the tool-tracking sidecar" instruction inside `writeMonitoring`'s own agent prompt to run as **Step 0** (first), before Steps 1-4. This was the dominant mechanism (not Scope) — every run's last tracked phase absorbed writeMonitoring's own bookkeeping calls before the clear ran.

Both are small, localized diffs (a ~20-line addition before Scope; a ~10-line move within `writeMonitoring`'s prompt text) — no new sidecar file scheme, no nonce, no session/timestamp reconstruction needed. `tests/tools/test_current_run_sidecar_orchestrator.py` (static text-parsing tests, no JS runtime exists for this file) was updated in place: the old "Scope/writeMonitoring must remain permanently sidecar-free" test was split into a new positive-coverage test for Scope, and the "Step 5 must stay last" anti-drift guard was rewritten to assert Step 0 now precedes Steps 1-4.

Workstream 2 (drift detection) was implemented as planned: `compute_tool_count_drift_report(events, tools)` added to `tools/agent-monitoring/validate.py`, wired into `main()` additively (never gates the exit code, matching `compute_drift_report`'s existing non-gating convention), with 6 new tests in `tests/tools/test_validate_agent_monitoring.py`. Run live against the current repo data, it reproduces the exact 433/1247 mismatch count from `investigation.md`'s manual audit — confirming the tool is correct and that historical corruption is (expectedly) still present, since it isn't backfilled.
