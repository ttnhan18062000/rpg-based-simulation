---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-SECURITY-GATE-FIRING-MONITOR
artifact_type: investigation
tags: [skills, agent-monitoring]
---

# Investigation — TCK-20260805-SECURITY-GATE-FIRING-MONITOR

## Context Search
- `mcp__knowledge-search__search_docs("security-tagged ticket Security-Review gate firing agent-monitoring events.jsonl")`
  surfaced `TCK-20260705-WORKFLOW-SECURITY-GATE` (built the gate), `docs/agent-monitoring/schema.md`
  (`phase` values / `SECURITY_BLOCKED` semantics), and `TCK-20260706-MONITORING-REASON-CODE`.
- `graphify query` on the same topic returned unrelated `PerceptionGate`/API-checklist nodes — the
  `tools/agent-monitoring/` module is thin on graph coverage for this specific cross-cutting
  concern, so direct reads of `retrieval_baseline_metrics.py` and `generate_retro.py` were the
  actual source of the house pattern (permitted follow-up per CLAUDE.md, after both semantic tools
  were tried first).

## House Pattern (from `retrieval_baseline_metrics.py`)
Confirmed by direct read: frozen module-level constant with a load-bearing comment explaining any
deliberate inclusion/exclusion choice; `build_*_section()` functions each returning a dict with a
`derivation`/`disclosure` string explaining exactly how the number was computed and its known
limits; no fabricated numbers — an "undefined: ..." string instead of a divide-by-zero or invented
placeholder when a computation is genuinely impossible; reuse of `generate_retro.py`'s private
helpers (`_load_runs_and_events`, `_resolve_status`, `_is_gate_fail`) via direct import rather than
reimplementing them — an established, accepted pattern in this codebase (private-name import
across `tools/agent-monitoring/*.py` files is not treated as an encapsulation violation here).

## Existing Adjacent Section — `generate_retro.py`'s Tag Breakdown (do not duplicate)
`compute_retro_metrics()`'s `tag_breakdown_skill` section (lines ~309-457) already cross-references
`security`-tagged runs against a `Security-Review` phase event or `SECURITY_BLOCKED` final_status,
via `_TAG_GATE_PHASE = {"security": "Security-Review"}`. But it only produces an **aggregate
count** (`{"runs": n, "gate_hits": hits}`) for the retro report — it does not identify *which*
specific ticket(s) are missing the hit. This ticket's checker is a different shape: a strict
pass/fail per-ticket flag list, suitable for a gate check, not a report metric. Per the ticket's
Out of Scope, `tag_breakdown_skill` itself is not touched.

## Ground-Truth Data Pull (real `agent-monitoring/*.jsonl`, not a fixture)
Ran `_collect_tagged_tickets()` directly: exactly 6 tickets are tagged `security` today.
Cross-referenced each against `runs.jsonl`/`events.jsonl`:

| Ticket | Resolved statuses (all runs.jsonl records) | `Security-Review` event ever? |
|---|---|---|
| `TCK-20260705-WORKFLOW-SECURITY-GATE` | `DONE` | No |
| `TCK-20260731-GATE-BYPASS-HARDENING` | `DONE` | No |
| `TCK-20260801-CODEX-LIVE-TRANSPORT` | `NEEDS_CHANGES`, `DONE` | Yes |
| `TCK-20260801-CODEX-PILOT-ORCHESTRATION` | `NEEDS_CHANGES` x4, `DONE` | Yes |
| `TCK-20260802-CODEX-PILOT-ENTRYPOINT` | `NEEDS_HUMAN_INPUT` (never DONE) | No |
| `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND` | (no `runs.jsonl` records at all) | No |

**Two real findings the ticket's own Request Summary did not anticipate:**

1. `TCK-20260705-WORKFLOW-SECURITY-GATE` is `DONE` with zero `Security-Review` events — but this
   is the ticket that *added* `phase('Security-Review')` to `implement-ticket.js` in the first
   place. Its own implementation ran under the *pre-gate* version of the JS (the gate did not
   exist yet in the orchestrator's own execution while writing it) — structurally impossible for
   this one run to have fired a gate that did not yet exist. This is a legitimate bootstrap
   exception, not a real miss, and must not be flagged as one (a checker that flags its own
   founding ticket as broken would be a credibility-destroying false positive on day one).
2. `TCK-20260802-CODEX-PILOT-ENTRYPOINT` (stuck at `NEEDS_HUMAN_INPUT`, never `DONE`) and
   `TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND` (zero run records) are not real misses either — a
   ticket that never reached `DONE` may simply not have reached the `Security-Review` phase yet
   (it comes late in the pipeline, step 11 of 13). Flagging these would conflate "still in
   progress / stalled" with "the gate silently didn't fire on a completed run" — a different,
   more serious failure class this checker exists to catch precisely.

**Conclusion:** the checker must only evaluate tickets with at least one `DONE`-resolved
`runs.jsonl` record, and must explicitly exclude the one bootstrap ticket that predates the gate's
own existence. Under that scoping, the real data cleanly reproduces exactly what the ticket cites:
1 confirmed miss (`GATE-BYPASS-HARDENING`) and 2 confirmed clean fires (`CODEX-LIVE-TRANSPORT`,
`CODEX-PILOT-ORCHESTRATION`).

## Unresolved Questions
None — scoping is fully grounded in the real corpus above.
