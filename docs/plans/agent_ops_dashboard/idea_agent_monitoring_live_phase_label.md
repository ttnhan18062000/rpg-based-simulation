---
status: idea
layer: observability
authority: P2
audience: developer
maturity: idea
date: 2026-07-16
tags: [idea, agent-infrastructure, observability, agent-monitoring, data-quality]
---

# Idea: Live phase/agent labeling for in-progress `tools.jsonl` rows

> **Maturity: IDEA** — Not scheduled. Found while investigating the Agent Ops Dashboard's real-time
> capability; deliberately kept as its own independent idea rather than folded into that dashboard's
> scope, since it touches production orchestration code
> (`.claude/workflows/implement-ticket.js`), which per this repo's rules cannot be modified inside
> an `experiments/` sandbox proposal. See
> [`idea_agent_ops_dashboard.md`](../archive/agent_ops_dashboard/idea_agent_ops_dashboard.md)
> (archived — shipped) and its companion
> `experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md` for the full investigation
> trail this doc distills.

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

None yet. Deliberately **independent** of
[`idea_agent_ops_dashboard.md`](../archive/agent_ops_dashboard/idea_agent_ops_dashboard.md)
(archived — shipped) — that dashboard's v1 scope does not depend on this fix landing first or at
all; both its Recent
Activity and Replay timeline views degrade gracefully to an honest "phase unknown" label for a
still-live run without it. Decided 2026-07-16 (with the user) that this should ship as an
independent sibling ticket, not a blocking dependency in either direction.

## Open Questions

- Exact `law_id`-style naming isn't applicable here, but the exact new field names (`phase`/`agent`
  vs. something else) haven't been bikeshedded against `schema.md`'s existing vocabulary.
- Whether the `_COVERED_SITE_ADJACENCY` regression test should be updated by hand per site, or
  whether its assertion strategy itself should change to be less brittle to signature changes like
  this one — not decided, a real implementation-time choice for whoever picks this up.
- Relative priority/timing against `idea_agent_ops_dashboard.md`'s own ticket (archived — shipped,
  see `docs/plans/archive/agent_ops_dashboard/idea_agent_ops_dashboard.md`) — this idea remains
  unscheduled; nothing here forces an order.

---

*Raised: 2026-07-16, distilled from `experiments/agent_ops_dashboard/MONITORING_INSTRUMENTATION_GAP.md`
— see that document for the full evidence chain and exact line citations this idea's claims are
drawn from. Sequencing decision (independent sibling ticket, non-blocking) confirmed with the user
on 2026-07-16.*
