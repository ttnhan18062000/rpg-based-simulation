---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH
artifact_type: investigation
tags: [agent-monitoring, workflows, data-quality]
---

# Investigation — TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH

## Current Behavior

All line numbers below are re-derived fresh from the CURRENT post-sibling-ticket state of
`.claude/workflows/implement-ticket.js` (confirmed via `grep -n` on 2026-07-11) — the ticket's own
citation (lines 56, 91, 347, 390, 453, 524, 595, 658, 809, 903, 968, 1025) is stale.

### `.claude/workflows/implement-ticket.js` — 11 genuine "Step 0 `date -u`" sites (not 12)

| Phase / branch | Current line | Mechanism |
|---|---|---|
| Scope — load existing | 56 | `Step 0: run \`date -u ...\` — save result as TS` → schema field `ts` (TICKET_SCHEMA, **required**) |
| Scope — create new | 91 | same, schema field `ts` (TICKET_SCHEMA, **required**) |
| Investigate | 366 | `Step 0: ... Your response MUST begin with this exact line: PHASE_TS: <result>` — **free-text prefix**, no `schema` on this `agent()` call at all; parsed via `investigation.toString().match(/^PHASE_TS: (\S+)/m)` (line 396) |
| Plan | 408 | same free-text `PHASE_TS:` prefix convention (line 432) |
| Review | 470 | schema field `ts` (REVIEW_SCHEMA, optional — not in `required`) |
| Implement | 540 | schema field `ts` (IMPL_SCHEMA, optional) |
| Architecture-Verify | 610 | schema field `ts` (ARCH_VERIFY_SCHEMA, optional) |
| Test | 672 | schema field `ts` (TEST_SCHEMA, optional) |
| Parity | 822 | schema field `ts` (PARITY_SCHEMA, optional) |
| Security-Review | 915 | schema field `ts` (SECURITY_REVIEW_SCHEMA, optional) |
| Verify (done-check) | 979 | schema field `ts` (DONE_SCHEMA, optional) |

**Finalize has no Step 0 ts-capture site at all, and never did.** Sibling ticket
`TCK-20260710-CURRENT-RUN-SIDECAR-BASH` (C1)'s own investigation
(`stored_artifacts/TCK-20260710-CURRENT-RUN-SIDECAR-BASH/investigation.md`, line 32) documented that
Finalize's old line ~1025 "Step 0" was **purely the `.claude/current_run` sidecar write** — "this is
the file's only site where the sidecar write **is** 'Step 0' itself (no separate ts-capture line,
because Finalize's `pushEvent('Finalize', ...)` passes no `ts` argument and the call has no JSON
schema)." C1's plan explicitly left it that way ("do not insert a new 'Step 0' placeholder text").
Reading current Finalize code (lines 1032-1075) confirms: no `date -u` text anywhere in its prompt,
and all three `pushEvent('Finalize', ...)` calls (lines 1111, 1123, 1133) omit the `ts` argument
entirely — Finalize-phase event timestamps are backfilled from `writeMonitoring`'s own `END_TS`
capture (line 217, Step 3: `If "ts" is null or missing, set "ts" to END_TS`).

**This means the ticket's own scope enumeration ("12 sites... lines 56, 91, 347, 390, 453, 524, 595,
658, 809, 903, 968, 1025") was wrong even before the sibling ticket landed** — line 1025 (old
numbering) was always the Finalize sidecar-only site, not a ts-capture site. The true count in this
file is **11**, not 12. Combined with implement-epic.js (3) and create-tickets.js (1): **total is 15
genuine sites, not the AC's stated 16.** Flagged under Risks below — this is a correction the plan
phase must make explicitly, not silently absorb.

### `.claude/workflows/implement-epic.js` — 3 sites (unchanged by sibling ticket, matches ticket citation)

| Phase / branch | Current line | Mechanism |
|---|---|---|
| Discover — folder mode | 66 | `Step 0 — run \`date -u ...\`` → schema field `ts` (DISCOVER_SCHEMA, **required**) |
| Discover — epic_id mode | 99 | same, DISCOVER_SCHEMA **required** |
| Discover — request mode | 124 | same, DISCOVER_SCHEMA **required** |

`batchStartTs = discovery.ts || null` (line 143) is the only consumer; it feeds
`record_run.py`'s `start_ts` for the batch run record (line 250), not a `pushEvent` `ts` (implement-
epic.js's own `batchEvents` array, lines 221-227, carries no `ts` key at all — one event per child
ticket result, not per `agent()` call, out of this ticket's `pushEvent`-wiring scope by construction).
implement-epic.js also has a `writeMonitoring`-analogous `Step 1 — get current timestamp` `date -u`
capture inside its batch-monitoring-write agent prompt (line 235) — this is the same category as
`implement-ticket.js`'s `writeMonitoring` END_TS capture (untitled "Step 0", labeled "Step 1", not
wired to any per-phase `pushEvent`) and is excluded from this ticket's scope for the same reason (see
Anti-Drift Hazards).

### `.claude/workflows/create-tickets.js` — 1 site (matches ticket citation)

| Phase | Current line | Mechanism |
|---|---|---|
| Comprehend | 157 | `Step 0: run \`date -u ...\` and return it as "ts" — captured before any other work.` → schema field `ts` (COMPREHEND_SCHEMA, optional — not in `required`); consumed as `startTs = comprehension.ts \|\| null` (line 187) and fed into `pushEvent('Comprehend', ...)` (line 190) |

One functionally-identical but **not literally "Step 0"-labeled** sibling site exists at line 651
(Write phase, per-task ticket-writer prompt: `2. Run: date -u +%Y-%m-%dT%H:%M:%SZ — save as TS.`),
whose `ts` return value (`w.ts`) is fed into `pushEvent('Write', 'ticket-scoper', 'ok', ..., w.ts)`
(line 696). This is the same underlying problem (agent self-reports a phase-start timestamp instead
of the orchestrator capturing it) but the ticket's own Scope section literally enumerates only
"Step 0" blocks and cites exactly 1 site for this file. Flagged as a Risk below — not silently
folded into scope, not silently ignored either.

### Established orchestrator-side `bash()` precedent this ticket must mirror

`.claude/workflows/implement-ticket.js` already has a directly-applicable precedent for "orchestrator
captures a value via `bash()` immediately before the paired `agent()` call": the sibling ticket's new
`writeSidecar(seq)` helper (lines 178-185), inserted immediately after `pushEvent`'s definition
(line 156-167) and invoked via `await writeSidecar(events.length + 1)` right before each of the 10
covered `await agent(...)` calls. A `ts`-capture equivalent (e.g. a `captureTs()` helper wrapping
`bash('date -u +%Y-%m-%dT%H:%M:%SZ')` and trimming its stdout) composes cleanly alongside
`writeSidecar` — both would be called back-to-back immediately before the same `await agent(...)`
call, e.g.:
```js
const ts = (await captureTs()).trim()
await writeSidecar(events.length + 1)
investigation = await agent(`...`, { label: 'investigate', agentType: 'investigator' })
pushEvent('Investigate', 'investigator', 'ok', investigationText.slice(0, 200), ts)
```
This also means the Investigate/Plan phases' `PHASE_TS: <result>` free-text-prefix convention and its
regex-strip logic (lines 396-397, 432-433) become entirely obsolete once ts is orchestrator-captured
— that parsing code should be removed, not left as dead logic.

### Schema `required` fields that force a companion change

Two schemas list `ts` as **required**, meaning simply deleting the Step 0 prompt text without also
editing the schema would make agent output fail JSON-schema validation on a field the agent is no
longer instructed to produce:
- `TICKET_SCHEMA` (implement-ticket.js:33, both Scope branches)
- `DISCOVER_SCHEMA` (implement-epic.js:43, all 3 Discover branches)

All other `ts`-bearing schemas (REVIEW_SCHEMA, IMPL_SCHEMA, ARCH_VERIFY_SCHEMA, TEST_SCHEMA,
PARITY_SCHEMA, SECURITY_REVIEW_SCHEMA, DONE_SCHEMA in implement-ticket.js; COMPREHEND_SCHEMA,
WRITE_SCHEMA in create-tickets.js) already list `ts` as optional (present in `properties`, absent
from `required`) — removing the agent-side capture is schema-safe for those without any companion
edit.

### `tools/agent-monitoring/record_events.py`

`REQUIRED = {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}` (line 11) — `ts` remains
hard-required at write time regardless of where the value originates. `validate_record` treats a
`None`/absent `ts` identically (line 23) — this check is untouched by this ticket per its own Out of
Scope; it will continue to pass as long as `pushEvent` is always given a non-null `ts` string, which
an orchestrator-side `bash()` capture guarantees deterministically (never depends on agent prose
compliance).

### `tools/agent-monitoring/generate_retro.py`

Confirmed (per the ticket's own Request Summary, and independently verified by reading the file):
`avg_dur`/`slow_runs` (lines 181-182, 240) read `runs.jsonl`'s `duration_s`, never per-event `ts`.
`iso_week()` (line 46) parses `runs.jsonl`'s `start_ts`, also unrelated to `events.jsonl`'s `ts`. No
code in this file consumes `events.jsonl`'s `ts` field for any computation — it is carried through
only as passthrough display data in the Join Example (`docs/agent-monitoring/schema.md`). This
confirms the ticket's own risk framing ("lower risk today because ts is used for display/ordering
only") is accurate; no change to `generate_retro.py` is required.

## Mechanics / Engine Constraints

None. `layer: ai` — this is agent-monitoring/orchestration tooling (`.claude/workflows/*.js`,
`tools/agent-monitoring/`), not simulation mechanics. No chapter of `docs/mechanics/` or contract of
`docs/engine/` governs this code.

## Parity Ledger Overlap

None. Grepped all 8 subsystem YAML files plus `faction.yaml` for
`agent-monitoring|current_run|Step 0|ts_capture|orchestrator` — every hit is `src/domains/campaigns/
orchestrator.py` or `src/lab/orchestrator.py` (unrelated simulation-domain/lab orchestrator classes,
not `.claude/workflows/` agent orchestration). Confirms the sibling ticket's identical finding
("infrastructure.yaml's scope covers simulation-runtime observability, not this dev-tooling
agent-monitoring system"). No parity ledger entries require updating.

## Prior Work

- **`stored_artifacts/TCK-20260710-CURRENT-RUN-SIDECAR-BASH/`** (sibling, child 1, just landed) is the
  direct architectural precedent: same 3 files, same "agent-prompt Step-N mechanical instruction →
  orchestrator-side `bash()` call wired directly into `pushEvent`" pattern, applied to the sidecar
  registration instead of the ts capture. Its `writeSidecar(seq)` helper (implement-ticket.js:178-185)
  is the template this ticket's own ts-capture helper should mirror in shape (small async helper,
  inserted near `pushEvent`, invoked immediately before each paired `await agent(...)` call, fail-open
  per CLAUDE.md's monitoring hard rule). Its plan.md's "Decisions on Open Questions" section
  established the scope-boundary reasoning this ticket should reuse: relocate/replace only sites that
  *currently* have the literal Step 0 mechanism; treat "never had one" (line-651-style near-misses) and
  "structurally excluded by design" (writeMonitoring's own END_TS capture) as separate, undecided-here
  gaps, not silently expanded scope. Its regression suite,
  `tests/tools/test_current_run_sidecar_orchestrator.py`, is now **directly load-bearing for this
  ticket** — see Anti-Drift Hazards.
- **`tickets/done/TCK-20260709-AGENT-MONITORING-DURATION.md`** (hotfix) — the `duration_s` precedent
  both this ticket and its sibling cite as the "same failure shape, different mechanism" ancestor.
  Its resolved-open-question pattern ("computed value always wins over caller-supplied") is directly
  analogous here: once the orchestrator captures `ts` via `bash()`, that captured value should always
  be what `pushEvent` receives — there is no scenario where an agent-supplied `ts` should still be
  preferred, mirroring `duration_s`'s "computed value always overwrites" decision.
- **`tests/tools/test_tag_skill_mapping_check.py`** — the established raw-source-text-parsing pattern
  (read `.claude/workflows/*.js` as text via `Path.read_text()`, never execute) both this ticket and
  its sibling must reuse for any new/updated static regression test.

## Risks and Open Questions

1. **BLOCKING — the ticket's own AC #1 site count and line citations are stale/wrong, independent of
   the sibling-ticket line-shift.** The true count is 11 (not 12) in `implement-ticket.js` — the
   Finalize "Step 0" the ticket's original 12-site list implicitly counted was always a sidecar-only
   site with no separate ts capture, confirmed both by direct code reading and by C1's own
   investigation. Total across all 3 files is **15, not 16**. The planner must correct AC #1's site
   count and drop the stale line-1025 citation rather than hunt for a non-existent 12th
   `implement-ticket.js` site to "complete."
2. **BLOCKING — idea doc's open question must be answered before implementation, per the ticket's own
   Scope bullet 2.** `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`'s Open
   Questions section asks explicitly: *"Is there any Step 0/0b content that genuinely needs the
   agent's own timestamp... or can every current instance be replaced by an orchestrator-side capture
   without losing meaning?"* This investigation did not find any case where the captured `ts` is used
   for anything beyond display/ordering/`record_events.py`'s non-null check (confirmed via
   `generate_retro.py` above) — no downstream consumer distinguishes "the orchestrator's dispatch
   moment" from "the instant the agent itself began reasoning." Recommended answer: **no** — every
   site is safe to convert. This is a recommendation for the planner to formally confirm and record,
   not a decision investigation is authorized to make unilaterally per CLAUDE.md's Clarification Rule.
3. **Two different current mechanisms must both be replaced, not just one.** Investigate/Plan use a
   free-text `PHASE_TS: <result>` response-prefix convention with regex-strip logic in the orchestrator
   (no JSON `schema` on those two `agent()` calls at all) — structurally different from every other
   site's JSON-schema `ts` field. An implementation that only edits schema-based sites while leaving
   the `PHASE_TS:` convention untouched (or vice versa) would leave the fix incomplete. Both the prompt
   text AND the `investigation.toString().match(/^PHASE_TS: ...)/)` / `.replace(/^PHASE_TS: \S+\n?/, ...)`
   parsing logic (lines 396-397, 432-433) need removal once ts is orchestrator-captured.
4. **Schema `required`-field companion edits are mandatory at 2 sites, not optional cleanup.**
   `TICKET_SCHEMA` and `DISCOVER_SCHEMA` both list `ts` as `required` — simply deleting the Step 0
   prompt text without dropping `ts` from these two `required` arrays could make the agent's structured
   output fail schema validation (agent no longer instructed to produce a field the schema still
   demands). Every other `ts`-bearing schema already has it optional, so no equivalent edit is needed
   elsewhere.
5. **Non-blocking — the Write-phase per-task `ts` capture in `create-tickets.js` (line 651) is the
   same failure shape but is not literally "Step 0"-labeled and is outside the ticket's own literal AC
   wording (which cites exactly 1 site for this file).** Flag for planner: convert it under this
   ticket's broader intent (idea doc's "Broader ask: audit every Step 0/Step 0b block... for content
   that is pure mechanical side-effect") or explicitly leave it, documented, as a same-shape gap for a
   follow-up ticket — mirroring how the sibling ticket (C1) handled its own analogous near-miss sites
   (Decision 1/2 in its plan.md). Either choice is legitimate; silently doing neither is not.
6. **AC #3's "monotonically non-decreasing ts in seq order" claim cannot be verified by `pytest`
   alone**, same structural limitation the sibling ticket's investigation found for its own AC #2: no
   JS test runner exists for `.claude/workflows/*.js` in this repo. A static text-parsing test can
   prove the Step 0 prompt text is gone and that a ts-capture `bash()` call precedes each paired
   `agent()` call; it cannot execute the workflow to observe actual monotonic `ts` values in a real
   `events.jsonl`. Recommend the same resolution C1 used: static structural tests plus one documented
   live end-to-end run, result recorded in the ticket's Test Summary before Finalize.
7. **Naming collision risk (minor, doc-only).** `docs/ai/ticket-lifecycle.md` (lines 259, 323, 360)
   already uses "Step 0" to name an unrelated, pre-existing convention — the orchestrator-run static
   pre-check pattern for architecture-reviewer/parity-updater/done-checker (`archCheckOutput`,
   `expectedSubsystemsOutput`, `run_static_precheck`). This ticket's "Step 0 `date -u`" is a
   *different* "Step 0" convention in the same files. Implementation notes / doc updates for this
   ticket should be precise about which "Step 0" they mean to avoid conflating the two.

## Anti-Drift Hazards

- **`tests/tools/test_current_run_sidecar_orchestrator.py::test_step_0_ts_capture_lines_unchanged_at_all_nine_sites`
  (line 94) is a hard blocker that this ticket's implementation MUST intentionally update, not merely
  keep passing.** Its docstring states outright: "protects sibling ticket
  `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`'s adjacent scope from being accidentally touched here." It
  currently asserts `re.findall(r"Step 0: run \\\`date -u \+%Y-%m-%dT%H:%M:%SZ\\\`", source)` count is
  `>= 9` against the live file. Once this ticket removes those exact lines, this assertion will fail by
  design — the test's purpose (guard against C1 touching C2's scope) is now satisfied and its assertion
  must be rewritten to match the new expected shape (Step 0 `date -u` prompt text gone; a `ts`-capture
  `bash()` call precedes each paired `agent()` call instead). This is the single most important
  regression-surface item for this ticket — see test_plan.md.
- **Do not touch `.claude/current_run` sidecar-write logic (`writeSidecar`, its 10 call sites, or
  `writeMonitoring`'s tool-tracking Steps 1-5)** — that is C1's already-landed, separate mechanism.
  This ticket's own helper must compose alongside `writeSidecar` (called back-to-back before the same
  `agent()` calls), never replace or merge into it.
- **Do not implement `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT`'s (C3, not yet started) `verified_by`
  provenance scope** — unrelated mechanism, file-adjacent only, explicitly Out of Scope.
- **Do not touch `record_events.py`'s `REQUIRED` field validation** — `ts` stays hard-required at
  write time; this ticket only changes *where the value comes from*, never the write-time contract.
- **Do not touch any of the 4 "related, smaller ideas"** from the idea doc (asymmetric gate coverage,
  cross-retro trend detection, tag→skill mapping dedup, `working_log.csv` backfill) — explicitly named
  Out of Scope.
- **Investigate/Plan's `PHASE_TS:` free-text convention removal must not disturb the rest of those two
  agent()'s response-parsing** — `investigationText`/`planText` (the stripped body used later for
  `staging_artifacts/.../investigation.md` cross-referencing and the Plan-phase `unresolved question`
  substring check, line 435) must continue to work once the `PHASE_TS:` prefix requirement and its
  regex strip are removed; a careless edit could accidentally require investigator/planner subagents to
  still emit an unused prefix line, or break the unresolved-question detection.
- **Do not expand scope to `implement-epic.js`'s `Step 1 — get current timestamp` (batch END_TS,
  line 235) or `implement-ticket.js`'s `writeMonitoring` END_TS capture (line 217)** — both are
  structurally excluded, same reasoning as C1's Decision on `writeMonitoring`'s sidecar-free-by-design
  status: these captures happen *after* all per-phase events already exist and are used only to
  backfill missing `ts`/compute `end_ts`, not to feed a live `pushEvent` call at dispatch time.
- **Sequencing:** this ticket is child 2 of 3; C3 (`TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT`) has not
  started and touches the same 3 files — land and finalize this ticket's diff before C3 begins editing,
  per the epic's stated ordering (same rationale C1's plan.md documented for landing before C2).
