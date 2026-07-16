# Companion Investigation: live tool-call rows carry no phase/agent label

**Status:** confirmed gap, fix designed, NOT implemented — this is evidence for a future ticket, not a ticket itself
**Location:** `experiments/agent_ops_dashboard/` (companion to `PROPOSAL.md`'s §7/§8)
**Date:** 2026-07-16

---

## 1. Why this exists as its own document

`PROPOSAL.md` designs a "Recent Activity" cross-run timeline and a per-run "Replay" timeline for
the Agent Ops Dashboard. While investigating whether the current agent-monitoring recording
actually supports a genuinely *live* view (not just live-once-reparsed), a real, confirmed
instrumentation gap was found. Per direct instruction — identify features that block the epic's
goals, not just work around them — this is documented precisely, with exact evidence, as a
candidate for its own ticket. It is **not** built here: it touches production orchestration code
(`.claude/workflows/implement-ticket.js`), which per this repo's rules cannot be modified inside an
`experiments/` sandbox proposal.

---

## 2. The confirmed gap

**During a live/in-progress run, `agent-monitoring/tools.jsonl` rows carry a bare `seq` integer —
no `phase`, no `agent` name — anywhere on disk.**

Evidence chain, each step verified by direct read, not assumed:

1. `.claude/workflows/implement-ticket.js:202` — `writeSidecar(seq)` writes only
   `{'run_id': ..., 'seq': ...}` to `.claude/current_run`. No phase or agent field.
2. `tools/agent-monitoring/post_tool_hook.py` — reads `run_id`/`seq` from that sidecar file and
   copies only those two fields into each `tools.jsonl` record. No phase or agent field exists to
   copy.
3. `events.jsonl` **does** map `seq → phase, agent` (e.g. `pushEvent('Investigate', 'investigator',
   ...)` at `implement-ticket.js:453`) — but per `PROPOSAL.md` §7a, `events.jsonl` is only written
   once, in a single batch, when the run finishes (`writeMonitoring()`, `implement-ticket.js:258`,
   called at exit points only — L364, L376, L391, L490, L552, L683, L740, L787, L922, L980, L1060,
   L1157/L1169, L1179).

Net effect: **there is no point in time, before a run finishes, where any on-disk record answers
"which phase/agent is this tool call happening under."** A dashboard reading only currently-written
files can show "a tool call just happened, seq=5" but never "...during the Implement phase, run by
the implementer agent" until the whole run completes and the batch write lands.

---

## 3. Confirmed: a minimal fix is feasible, not just theorized

Checked every `writeSidecar` call site (10 total, `implement-ticket.js` lines 419, 460, 519, 588,
657, 718, 867, 959, 1022, 1076) to confirm the missing values are actually available as literals at
each site, not requiring new plumbing to obtain:

- **`phase` is already known** — every `writeSidecar` call is immediately preceded by a
  `phase('X')` call (e.g. `phase('Investigate')` right before line 419's site).
- **`agent` is already known** — not passed as a structured parameter at the call site itself, but
  hardcoded as a literal a few lines later in the paired `pushEvent(phase, agentName, ...)` call
  (e.g. `pushEvent('Investigate', 'investigator', ...)` at line 453) — the exact same string could
  be threaded into `writeSidecar` at the call site instead.

**Proposed change (design only, not implemented):**

1. `writeSidecar(seq)` → `writeSidecar(seq, phase, agent)`. Internals write
   `{'run_id': ..., 'seq': ..., 'phase': ..., 'agent': ...}` (two new fields, passed as additional
   individually-quoted argv elements, matching the existing convention documented at
   `implement-ticket.js:196-199` for why args are quoted argv elements rather than JSON-embedded in
   the `-c` string).
2. All 10 call sites updated to pass the already-known phase/agent literals.
3. `tools/agent-monitoring/post_tool_hook.py` gets one added block: read `phase`/`agent` from the
   sidecar (same `try/except`-wrapped read that already exists for `run_id`/`seq`) and include them
   in the `record` dict written to `tools.jsonl`.
4. Both new fields are **nullable, additive** — `null`/absent for every historical row and for tool
   calls outside a workflow run (`run_id: null`), exactly the same precedent already established for
   `tool_call_count`, `cost_proxy_score`, and `reason_code` (per `docs/agent-monitoring/schema.md`).
   No backfill, no breaking change to existing readers.

---

## 4. Real, non-zero cost — this is not a free change

- **Breaks an existing regression test.** `tests/tools/test_current_run_sidecar_orchestrator.py`
  asserts exact source text via its `_COVERED_SITE_ADJACENCY` list — 10 hardcoded strings like
  `"  await writeSidecar(events.length + 1)\n  investigation = await agent("`. Every one of these
  would need updating to match the new `writeSidecar(seq, phase, agent)` call signature. This is
  mechanical but must be done carefully — the test exists specifically to catch drift between the
  sidecar-write mechanism and the `await agent(...)` calls it's supposed to precede.
- **`docs/agent-monitoring/schema.md` needs updating** — two new nullable fields on `tools.jsonl`
  (`phase`, `agent`), documented alongside the existing field table, same pattern as when
  `tool_call_count`/`cost_proxy_score`/`reason_code` were added.
- **Touches production orchestration code**, not a sandbox script — `.claude/workflows/
  implement-ticket.js` is the pipeline every real ticket runs through. This is a "new feature," not
  a "bug fix," per this repo's tier definitions — it should go through the real ticket pipeline as
  its own `standard`-tier, `layer: observability` ticket, not be bundled into the dashboard
  prototype's own build.

---

## 5. What this fix would and would not unlock

**Would unlock:** the Agent Ops Dashboard's "Recent Activity" timeline could label an in-progress
run's live bar with its actual current phase/agent (e.g. "TCK-... — Implement (implementer)
running"), and the per-run Replay timeline's live edge (for a still-active run) could show the same
label in its tool-activity feed, instead of an unlabeled raw tool-call stream.

**Would NOT unlock:** phase/gate *history* (pass/fail per phase, final status) still would not
appear until the run completes or hits a gate failure — that's a separate, larger question (would
require changing `writeMonitoring()`'s call cadence itself, explicitly rejected for v1 in
`PROPOSAL.md` §7c as materially riskier and not required for either timeline view to function).

---

## Related

- `experiments/agent_ops_dashboard/PROPOSAL.md` §7-§8 — the dashboard design this gap was found investigating, and why the dashboard's v1 scope does not block on this fix
- `.claude/workflows/implement-ticket.js` — `writeSidecar()` (L202), all 10 call sites (L419, 460, 519, 588, 657, 718, 867, 959, 1022, 1076), `pushEvent()` (L180), `writeMonitoring()` (L258)
- `tools/agent-monitoring/post_tool_hook.py`, `pre_tool_hook.py` — the hooks that would need the added phase/agent copy logic
- `tests/tools/test_current_run_sidecar_orchestrator.py` — the regression test whose `_COVERED_SITE_ADJACENCY` list would need updating alongside this change
- `docs/agent-monitoring/schema.md` — the schema doc that documents `tool_call_count`/`cost_proxy_score`/`reason_code` as the existing precedent for adding nullable fields to `tools.jsonl` over time; would need a similar entry for `phase`/`agent`
