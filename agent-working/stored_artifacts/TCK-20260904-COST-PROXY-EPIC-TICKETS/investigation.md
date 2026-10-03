---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-COST-PROXY-EPIC-TICKETS
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation — TCK-20260904-COST-PROXY-EPIC-TICKETS

## Current Behavior

### `.claude/workflows/implement-epic.js` (403 lines total)
Real `agent()` call sites, verified by `grep -n "agent("` against the current file (not the
ticket's cited numbers):
- **L86** — `const discovery = await agent(...)`, label `'discover'`. Always runs (Discover phase).
- **L287** — `await agent(...)`, label `'batch-monitoring-write'`. Always runs after the
  sequential `workflow('implement-ticket', ...)` loop (L239-268) completes.
- **L316** — `await agent(...)`, label `'folder-cleanup'`. Conditional: `batchStatus === 'DONE' && folder`.
- **L353** — `const trackingDocResult = await agent(...)`, label `'tracking-doc-update'`.
  Conditional: `discovery.mode === 'folder' && discovery.tracking_doc`.

That is **4 real `agent()` call sites**, not 6. **Lines 796 and 818 do not exist in this file at
all** — the file is only 403 lines long. Those two line numbers are an exact match for
`create-tickets.js`'s own `write-sequence` (L796) and `link-epic` (L818) call sites (confirmed by
`grep -n "agent(" .claude/workflows/create-tickets.js`). This is not a case of the file having
shrunk since ticket creation (`git log --oneline -- .claude/workflows/implement-epic.js` shows the
last change was PR #88, well before this ticket) — it is a citation error in the ticket itself,
apparently produced by conflating the two files' line numbers during investigation/scoping.

The 2 non-standard fire-and-forget `record_events.py` calls (ticket cites ~189, ~215; confirmed at
these exact lines):
- **L184-193** (`request` mode early return, "Discover ran and created a real ticket"): writes a
  single hardcoded `seq:1` event via `bash()` directly (not via `agent()`), then a matching
  `record_run.py` call, then the workflow `return`s immediately with status `EPIC_CREATED`.
- **L209-219** (`ticketIds.length === 0` early return, "Discover found no tickets to implement"):
  identical shape — hardcoded `seq:1` event via `bash()`, `record_run.py` call, then `return` with
  status `NOTHING_TO_DO`.

Why these are "non-standard": both bypass `agent()` entirely — they are pure orchestrator-side
`bash()` calls writing a bookkeeping event for a run that terminates having made **zero** delegated
tool calls of its own (Discover's own `agent()` call at L86 already ran and returned before either
branch is reached; no further `agent()` call happens on these paths). Concretely, "individualized
handling" for these two sites means: **they should not be wired into the sidecar-writing pattern at
all.** There is no `(run_id, seq)` tool-call group to attribute here in the first place — no `agent()`
call follows the `bash()` write on either path, so there is nothing for a `.claude/current_run`
sidecar to capture. Once `compute_tool_stats()`'s filter widens (see below), these two `seq:1`
records will legitimately compute to `(0, 0.0)` from an all-fields-empty `tools.jsonl` group — which
is correct and requires no `writeSidecar()` call, unlike the ticket's Scope implies by lumping them
in with "add sidecar-writing calls at ~9 call sites."

### `.claude/workflows/create-tickets.js` (854 lines total)
Real `agent()` call sites, verified the same way:
- **L131** — `const result = await agent(...)`, inside the `writeMonitoring` helper (the
  bookkeeping-write function itself, mirroring `implement-ticket.js`'s own `writeMonitoring`).
  Called from 4 places: L202 (`NOTHING_TO_CREATE` after Comprehend), L343 (`NOTHING_TO_CREATE`
  after Investigate), L550 (`NOTHING_TO_CREATE` after Structure), L839 (`DONE`, end of workflow).
- **L156** — `const comprehension = await agent(...)`, label `'comprehend'`. Always runs.
- **L304** — `return agent(...)` inside a `pipeline(...)` callback, label
  ``` `investigate:${concern.id}` ```, `agentType: 'concern-investigator'`. Runs once per concern
  (fan-out).
- **L439** — `const structured = await agent(...)`, label `'structure'`. Always runs (if any
  concerns survive Investigate).
- **L659** — `return agent(...)` inside a `pipeline(...)` callback, label
  ``` `write:${task.short_scope}` ```, `agentType: 'ticket-scoper'`. Runs once per ticket to write
  (fan-out).
- **L796** — `await agent(...)`, label `'write-sequence'`. Conditional: `hasIntraDeps` (only when
  the batch has intra-batch ticket dependencies).
- **L818** — `const linkResult = await agent(...)`, label `'link-epic'`. Conditional:
  `epicId && ticketIds.length > 0`.

That is **7 real call-site locations** (2 of which fan out per-item), not the 3 the ticket cites
(131, 156, 439). The ticket's own citations for this file **omit L304 (investigate, fan-out), L659
(write, fan-out), L796 (write-sequence), and L818 (link-epic)** — the latter two are exactly the
line numbers the ticket mistakenly attributed to `implement-epic.js` instead (see above). Net
effect: the ticket's combined "~9 call sites across the two files" underclaims real, distinct
`await agent()`/`return agent()` locations (4 + 7 = 11) while also citing 2 line numbers that exist
in neither file's actual position.

**Important architectural finding on L131 specifically**: `implement-ticket.js` has the exact same
shape of call — its own `writeMonitoring`'s `agent()` call (labeled `'monitoring-write'`) — and that
call site is **deliberately, permanently excluded from sidecar tracking**, enforced by a passing
regression test: `tests/tools/test_current_run_sidecar_orchestrator.py::test_writeMonitoring_call_has_no_preceding_sidecar_write`
(asserts `"writeSidecar(" not in monitoring_write_region`) and documented in that same test file's
module docstring: *"`writeMonitoring`'s own `agent()` call remains permanently sidecar-*tracking*-free
(it never gets its own `(run_id, seq)`)"*. `create-tickets.js`'s L131 `writeMonitoring` call is
structurally identical (same role: writes the already-collected `events`/run record via
`record_events.py`/`record_run.py`, called from up to 4 return paths). **Adding sidecar coverage to
create-tickets.js's L131, as the ticket's Scope literally lists it, would contradict the
established, tested `implement-ticket.js` precedent for the same architectural role.** This is
flagged as an open question below — it should almost certainly be excluded from the sidecar-wiring
work, mirroring `writeMonitoring`'s exclusion, not wired up as the ticket's Scope bullet implies.

### `tools/agent-monitoring/record_events.py::compute_tool_stats()` (L34-74)
Confirmed current filter (L59): `infer_workflow(r.get("run_id", "")) == "implement-ticket"` — a
literal string-equality gate, exactly as the ticket describes. It also enumerates `(run_id, seq)`
pairs only for records passing this gate, reads the union of every ISO-week `tools.jsonl` (a
`TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY` change, unrelated to this ticket), and — critically
— for every `(run_id, seq)` key that passes the filter, it **unconditionally returns an entry**
`(len(rows), compute_cost_proxy_score(rows))` even if `rows` is empty (L74:
`{key: (len(rows_by_key[key]), ...) for key in wanted}`). This means once the filter widens to
include `implement-epic`/`create-tickets`, **every** matching-prefix `(run_id, seq)` in a batch
will get a non-null `(0, 0.0)` result even with zero matching `tools.jsonl` rows — this is exactly
why `test_implement_epic_and_create_tickets_records_unaffected_no_sidecar`'s current
`assert stats == {}` will break the moment the filter widens, independent of whether any sidecar
wiring lands at all (see Test Plan).

### `tools/agent-monitoring/vocabulary.py::infer_workflow()` (L80-101)
Confirmed: already recognizes `'EPIC-'`/`'FOLDER-'` → `'implement-epic'` (L95-96) and
`'CREATE-TICKETS-'` → `'create-tickets'` (L97-98), disjoint from `'TCK-'` → `'implement-ticket'`
(L99-100) and `'SIMQ-AUDIT-'` → `'simq-audit'` (L93-94). The ticket's assumption that this function
"already works correctly and just needs to be included in the `compute_tool_stats()` filter" is
accurate — no change needed here.

### `.claude/workflows/implement-ticket.js`'s `writeSidecar` pattern (L274-285) — the mirror target
```js
const writeSidecar = async (seq, phase, agent) => {
  await bash(
    `python3 -c "
import json, sys, os
data = json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': sys.argv[3], 'agent': sys.argv[4], 'execution_id': sys.argv[5], 'provider': sys.argv[6]})
open('.claude/current_run', 'w').write(data)
sid = os.environ.get('CLAUDE_CODE_SESSION_ID', '')
if sid:
    open('.claude/current_run.' + sid, 'w').write(data)
" "${tid}" "${seq}" "${phase}" "${agent}" "${executionId}" "${PROVIDER}" 2>/dev/null || true`
  )
}
```
This is the **post-`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`** shape: it writes both the unscoped
`.claude/current_run` file AND a session-scoped `.claude/current_run.<CLAUDE_CODE_SESSION_ID>` copy.
Any new `writeSidecar`-equivalent added to `implement-epic.js`/`create-tickets.js` **must mirror
this dual-write shape**, not the older single-file shape — confirmed necessary because
`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s own ticket body explicitly named these two files as a
known, deferred gap (see Prior Work below), and its cross-session collision fix logically applies
to any future sidecar writer in the repo, not just the one it directly touched.

## Mechanics / Engine Constraints
Not applicable — this is an `.claude/`/`tools/agent-monitoring/` infrastructure ticket with no
`docs/mechanics/` or `docs/engine/` law surface. No Mechanics Bible chapter or engine contract
constrains this work.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: multiple locations state, as current fact, that
  `implement-epic`/`create-tickets` never register a sidecar and that `tool_call_count`/
  `cost_proxy_score` are therefore always null for them — specifically L180, L182, L289, and the
  "How tool calls are attributed to agent events" prose block (~L424-446, including the explicit
  line *"Records for implement-epic/create-tickets (neither registers a per-agent-call ...)"* type
  language mirrored from `docs/parity_ledger/infrastructure.yaml`'s INFRA-282 entry). All of these
  must be corrected once sidecar coverage + the filter widening ship, or the doc will actively
  misdescribe the new behavior (not merely be stale-but-harmless).

The `docs/parity_ledger/infrastructure.yaml` INFRA-282 entry (path:
`docs/parity_ledger/infrastructure.yaml`, under `docs/`) is considered but not marked Format-1 here:
its `text` field currently states *"Records for implement-epic/create-tickets (neither registers a
per-agent-call sidecar) ... stay untouched"* as a description of `TCK-20260719-COST-PROXY-WRITE-PATH`'s
own historical implementation, not a live assertion about current filter behavior post-this-ticket.
Whether it needs a new/updated entry is an implementation-time call for whoever lands this (parity
entries describing behavior changes are normally added by `parity-updater` during Implement) — flagging
it here as a likely target rather than asserting it with certainty, since the parity ledger's own
convention is per-status-change entries, and this ticket has not yet decided the exact final shape
of the widened filter.

## Parity Ledger Overlap
`INFRA-282` (`docs/parity_ledger/infrastructure.yaml`, status: presumably `verified` — not directly
re-read for status field, only its `text`) documents `TCK-20260719-COST-PROXY-WRITE-PATH`'s original
implementation, including the explicit "implement-epic/create-tickets stay untouched" behavior this
ticket reverses. It is `P2`-adjacent infrastructure (not found tagged P0 in the excerpt read) — no
P0 test_path obligation identified, but should be revisited/updated by `parity-updater` once this
ticket's actual filter shape is implemented, since its `text` will otherwise describe now-obsolete
behavior.

## Prior Work
- **`TCK-20260719-COST-PROXY-WRITE-PATH`** (`tickets/done/`): the ticket this one explicitly
  reverses. Read in full. Its actual "Out of Scope" bullet: *"implement-epic/create-tickets — 100%
  missing for both fields by documented, deliberate design (no sidecar registered); this is not a
  bug and stays out of scope."* Its own Implementation Notes clarify the real reason: this was a
  **scope-discipline decision for a narrowly-framed bug-fix ticket** (root-caused and fixed a
  36.7%/29.5% null-rate regression specifically in `implement-ticket` events by moving an existing
  LLM-computed step into deterministic code) — **not** a considered architectural judgment that
  epic/create-tickets workflows should never get cost tracking. The ticket even flags a parallel,
  still-unfixed instance of the same underlying anti-pattern in `simq-audit.js` as "worth a future
  ticket," reinforcing that the exclusion was about scope size, not principle. **Conclusion: this
  new ticket's reversal does not conflict with any technical rationale in the original exclusion —
  it is closing a scope gap the original ticket explicitly deferred, not overturning a deliberate
  technical constraint.** No real conflict found; the reversal's justification is sound.
- **`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`** (`tickets/done/`): explicitly names this exact gap
  as deferred follow-up work: *"Note (do not fix) that implement-epic.js and create-tickets.js
  currently register no sidecar at all — call this out as a related but distinct gap for a possible
  follow-up ticket"* and *"Adding sidecar coverage to implement-epic.js/create-tickets.js — a
  related but separate gap; only note it in this ticket, do not implement it here unless a follow-up
  ticket is warranted."* This ticket (`TCK-20260904-COST-PROXY-EPIC-TICKETS`) is that follow-up. Its
  dual-write (unscoped + session-scoped `.claude/current_run.<SESSION_ID>`) fix must be mirrored by
  whatever `writeSidecar`-equivalent this ticket adds — see Current Behavior above.
- **`tests/tools/test_current_run_sidecar_orchestrator.py`**: contains the precedent test
  (`test_writeMonitoring_call_has_no_preceding_sidecar_write`) that directly informs how L131 of
  `create-tickets.js` should likely be treated (excluded, not wired) — see Anti-Drift Hazards.

## Risks and Open Questions
1. **Open question, blocks a clean implementation**: should `create-tickets.js`'s L131
   `writeMonitoring` call site get sidecar coverage at all? The ticket's Scope explicitly lists line
   131 as one of the "9 call sites," but the structurally-identical call in `implement-ticket.js`
   (`writeMonitoring`'s own `agent()` call) is deliberately excluded and test-enforced. Implementing
   the ticket's literal scope on this point would introduce an inconsistency with the established
   pattern for the same architectural role. Recommend excluding L131 from sidecar wiring, mirroring
   `implement-ticket.js`'s precedent — but this is a real scope decision the implementer/planner
   should make explicitly, not silently assume either way.
2. **The ticket's own "~9 call sites" count and specific line citations for implement-epic.js are
   wrong** (see Current Behavior) — 796/818 do not exist in that file. The planner must use the
   corrected site list from this investigation (4 in implement-epic.js: 86, 287, 316, 353; up to 7
   locations in create-tickets.js: 131 (contested, see above), 156, 304 (fan-out), 439, 659
   (fan-out), 796, 818), not the ticket body's literal line numbers.
3. **Concurrency between implement-epic.js's own sidecar and its nested `implement-ticket` runs**:
   `implement-epic.js`'s loop (L239-268) calls `workflow('implement-ticket', ticketArgs)`
   sequentially per ticket — during that loop, `implement-epic.js` itself makes no `agent()` calls of
   its own; all 4 of its real call sites (86, 287, 316, 353) sit strictly before or after the loop.
   Since the harness runs `await`-sequenced JS single-threaded, there is no observed race between
   implement-epic's own sidecar writes and the nested implement-ticket run's sidecar writes — but
   this should be explicitly verified by a new test once implemented (see Test Plan), not just
   asserted from code reading.
4. **The two fan-out call sites** (create-tickets.js L304 `investigate:${concern.id}` and L659
   `write:${task.short_scope}`) run via `pipeline(...)`, i.e. potentially with real parallelism
   across concerns/tasks within one batch. If sidecar coverage is added here, each fan-out
   invocation needs its own distinct `seq` value else concurrent iterations will collide writing
   `.claude/current_run` — this is a materially different problem than `implement-ticket.js`'s
   strictly-sequential `writeSidecar(seq)` sites, and needs explicit design (e.g., whether `pipeline`
   is actually concurrent or effectively sequential in this harness) before code is written. Flag as
   an open question for planning, not resolved here.
5. **`compute_tool_stats()`'s unconditional-entry-per-wanted-key behav's interaction with the 2
   fire-and-forget bash-only sites** (implement-epic.js L184-193/L209-219): once the filter widens,
   these will get `(0, 0.0)` tuples written even though no sidecar/agent() call happened for them —
   this is correct (there genuinely were zero tool calls on those paths) but should be verified with
   an explicit test rather than assumed, since it's a slightly different code path than the
   fan-out/dual-write cases.

## Anti-Drift Hazards
- Do not literally implement the ticket's line-number list for `implement-epic.js` — lines 796/818
  do not exist there. Use the corrected site list (86, 287, 316, 353) from this investigation.
- Do not silently add `writeSidecar()` coverage to `create-tickets.js`'s L131 `writeMonitoring` call
  without an explicit decision — it directly parallels `implement-ticket.js`'s own excluded
  `writeMonitoring` call, and adding it without justification risks re-introducing the exact
  attribution-inflation bug `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` fixed (a
  bookkeeping call's own tool calls silently attributed to whatever sidecar state was last set).
- Any new `writeSidecar`-equivalent must use the **dual-write** (unscoped + session-scoped) shape
  from `implement-ticket.js`'s current `writeSidecar` (L274-285), not an older single-file shape —
  copying stale code from before `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` would reintroduce the
  cross-session collision that ticket fixed.
- `compute_tool_stats()`'s widened filter must remain a **membership check** (e.g. against
  `{"implement-ticket", "implement-epic", "create-tickets"}`), not simply flip to "not `None`" —
  `simq-audit` (`SIMQ-AUDIT-` prefix) is a real, distinct workflow recognized by `infer_workflow()`
  that must stay excluded (it has its own separate, still-unfixed inline TOOL_STATS-compute
  anti-pattern per `TCK-20260719-COST-PROXY-WRITE-PATH`'s "Found but explicitly out of scope" note —
  accidentally including it here would silently overwrite whatever `simq-audit.js` computes itself
  with new record_events.py-computed values, an unrelated and unintended behavior change).
- Do not conflate `create-tickets.js`'s 2 fan-out call sites (L304, L659) with its 5 non-fan-out
  sites when designing `seq` allocation — a naive shared `seq` counter risks collisions across
  concurrent `pipeline()` iterations in a way `implement-ticket.js`'s strictly sequential sites never
  had to handle.
- The `Out of Scope` bullet "Backfilling already-written null rows" must be respected literally —
  do not be tempted to write a one-off backfill script for historical `implement-epic`/
  `create-tickets` events even though the mechanism to compute them will now exist.
