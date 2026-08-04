---
status: historical
layer: observability
authority: P2
audience: developer
maturity: shipped
date: 2026-07-16
archived: 2026-07-19
tags: [idea, agent-infrastructure, observability, agent-monitoring, data-quality]
---

# Idea: Live phase/agent labeling for in-progress `tools.jsonl` rows

**Archived:** 2026-07-19 — **partially shipped**, not fully. `TCK-20260719-LIVE-PHASE-AGENT-LABEL`
(`tickets/done/`) shipped exactly the data-producing prerequisite this doc scoped: `writeSidecar`
now threads `phase`/`agent` through all 10 call sites plus the Scope-phase resume branch, and
`tools/agent-monitoring/post_tool_hook.py` persists both as new nullable, additive `tools.jsonl`
fields (no backfill — historical rows still lack them). **What remains unshipped is this doc's own
stated payoff**: the "Would unlock" section below describes a live dashboard's in-progress-run
indicator showing e.g. "TCK-... — Implement (implementer) running" — the Agent Ops Dashboard's own
`RawToolCall` Pydantic model (`src/api/agent_ops_dashboard/models.py`) and Replay Timeline view were
deliberately left untouched by that ticket (explicitly out of scope), so the dashboard still renders
the unconditional "phase unknown — run still in progress" caption for a live run today, unchanged
from before this ticket, even though the underlying data it would need now exists. Wiring the
dashboard to actually consume these new fields remains a real, undone follow-up — not yet ticketed.
This document is the historical design reference for the shipped half.

> **Maturity: SHIPPED (data half only).** Found while investigating the Agent Ops Dashboard's
> real-time capability; deliberately kept as its own independent idea rather than folded into that
> dashboard's scope, since it touches production orchestration code
> (`.claude/workflows/implement-ticket.js`), which per this repo's rules cannot be modified inside
> an `experiments/` sandbox proposal. See
> [`idea_agent_ops_dashboard.md`](idea_agent_ops_dashboard.md)
> (archived — shipped) and its companion `experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md`
> (deleted 2026-08-04, `TCK-20260804-PLANS-EXPERIMENTS-SWEEP`, as fully-shipped scaffolding) for
> the full investigation trail this doc distills.

## Problem

**During a live/in-progress workflow run, `agent-monitoring/tools.jsonl` rows carry a bare `seq`
integer — no `phase`, no `agent` name — anywhere on disk**, confirmed by direct read, not assumed:

1. `.claude/workflows/implement-ticket.js:202` — `writeSidecar(seq)` writes only
   `{'run_id': ..., 'seq': ...}` to `.claude/current_run`. No phase or agent field.
2. `tools/agent-monitoring/post_tool_hook.py` reads only `run_id`/`seq` from that sidecar and
   copies just those two fields into each `tools.jsonl` record.
3. `events.jsonl` **does** map `seq → phase, agent` (e.g. `pushEvent('Investigate', 'investigator',
   ...)` at `implement-ticket.js:453`) — but `events.jsonl` is written exactly once, in a single
   batch, at whichever exit point a run reaches (`writeMonitoring()`, `implement-ticket.js:258`,
   called only at gate-failure exits or the final `DONE`). For a ticket passing cleanly through all
   phases, zero phase-level data exists on disk until the very end.

Net effect: there is no point in time, before a run finishes, where any on-disk record answers
"which phase/agent is this tool call happening under." A dashboard reading only currently-written
files can show "a tool call just happened, seq=5" but never "...during the Implement phase, run by
the implementer agent" until the whole run completes.

## Idea

`phase` and `agent` are already known as literals at every `writeSidecar` call site — confirmed by
checking all 10 call sites (`implement-ticket.js` lines 419, 460, 519, 588, 657, 718, 867, 959,
1022, 1076): each is immediately preceded by a `phase('X')` call, and the agent name is hardcoded a
few lines later in the paired `pushEvent(phase, agentName, ...)` call. No new plumbing is needed to
obtain either value — only to thread them through.

**Proposed change:**

1. `writeSidecar(seq)` → `writeSidecar(seq, phase, agent)`, writing
   `{'run_id': ..., 'seq': ..., 'phase': ..., 'agent': ...}` as additional individually-quoted argv
   elements, matching the existing convention at `implement-ticket.js:196-199` for why args are
   quoted argv elements rather than JSON-embedded in the `-c` string.
2. All 10 call sites updated to pass the already-known phase/agent literals.
3. `tools/agent-monitoring/post_tool_hook.py` gets one added block: read `phase`/`agent` from the
   sidecar (same `try/except`-wrapped read pattern already used for `run_id`/`seq`) and include them
   in the `tools.jsonl` record.
4. Both new fields are **nullable, additive** — `null`/absent for every historical row and for tool
   calls outside a workflow run (`run_id: null`), the same precedent already established for
   `tool_call_count`, `cost_proxy_score`, and `reason_code`. No backfill, no breaking change to
   existing readers.

## What this would and would not unlock

**Would unlock:** a live dashboard's in-progress-run indicator could label its current phase/agent
(e.g. "TCK-... — Implement (implementer) running") instead of an unlabeled raw tool-call stream.

**Would NOT unlock:** phase/gate *history* (pass/fail per phase, final status) still would not
appear until the run completes or hits a gate failure — that would require changing
`writeMonitoring()`'s call cadence itself (flushing after every phase instead of once per run), a
materially riskier change to the core orchestration script every ticket runs through. Explicitly out
of scope for this idea.

## Architecture Constraints

- Touches production orchestration code (`.claude/workflows/implement-ticket.js`), not a sandbox
  script — must go through the real ticket pipeline as its own `standard`-tier,
  `layer: observability` ticket, not be bundled into any dashboard-prototype build.
- **Breaks an existing regression test.** `tests/tools/test_current_run_sidecar_orchestrator.py`
  asserts exact source text via its `_COVERED_SITE_ADJACENCY` list — 10 hardcoded strings like
  `"  await writeSidecar(events.length + 1)\n  investigation = await agent("`. Every one needs
  updating to match the new `writeSidecar(seq, phase, agent)` signature — mechanical but must be
  done carefully, since this test exists specifically to catch drift between the sidecar-write
  mechanism and the `await agent(...)` calls it's supposed to precede.
- `docs/agent-monitoring/schema.md` needs updating: two new nullable fields on `tools.jsonl`
  (`phase`, `agent`), documented alongside the existing field table, following the same pattern used
  when `tool_call_count`/`cost_proxy_score`/`reason_code` were added.
- New fields must stay nullable/additive — no backfill of historical rows, consistent with this
  repo's append-only precedent for `tools.jsonl`.

## Relationship to Planned Tickets

Shipped (data half only) by `TCK-20260719-LIVE-PHASE-AGENT-LABEL` (`tickets/done/`), created via
`/create-tickets` on 2026-07-19 and implemented the same day. Ran as its own independent sibling
ticket, not blocking or blocked by
[`idea_agent_ops_dashboard.md`](idea_agent_ops_dashboard.md) (archived — shipped), exactly as
decided on 2026-07-16 — that dashboard's v1 (and every subsequent dashboard epic through
2026-07-18) shipped and degraded gracefully to "phase unknown" the entire time this fix was
pending, confirming the non-blocking call was correct. **No follow-up ticket yet exists** for the
remaining dashboard-consumption half (see the Archived note above) — this is real, identified,
unticketed work, not a closed loop.

## Open Questions — resolved during implementation

- Field names: `phase`/`agent` were used as-is, matching `events.jsonl`'s existing vocabulary — no
  bikeshedding needed, confirmed compatible during Investigate.
- `_COVERED_SITE_ADJACENCY` was updated by hand, per-site — its assertion strategy was not changed
  to be less brittle; that remains a real, undecided future call if a similar signature change ever
  recurs.
- Sequencing against `idea_agent_ops_dashboard.md` (archived — shipped): confirmed non-blocking in
  both directions, as decided 2026-07-16 — see Relationship to Planned Tickets above.

---

*Raised: 2026-07-16, distilled from `experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md`
(deleted 2026-08-04, `TCK-20260804-PLANS-EXPERIMENTS-SWEEP`, as fully-shipped scaffolding) — this
doc preserves the evidence chain and exact line citations this idea's claims were drawn from.
Sequencing decision (independent sibling ticket, non-blocking) confirmed with the user
on 2026-07-16.*
