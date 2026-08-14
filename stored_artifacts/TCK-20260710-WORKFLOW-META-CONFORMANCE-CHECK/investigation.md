---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK
artifact_type: investigation
tags: [ai, agent-monitoring, determinism]
---

# Investigation — TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK

## Current Behavior

### `.claude/workflows/*.js` — `meta.phases` declarations (re-verified fresh, not from the idea doc's description)

Read all four active-lifecycle workflow files directly. `meta.phases` is a plain array literal at
the top of each file — no nesting, no computed values, no template interpolation:

- `.claude/workflows/implement-ticket.js:1-17` — 11 entries: Scope, Investigate, Plan, Review,
  Implement, Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize.
- `.claude/workflows/create-tickets.js:1-10` — 5 entries: Comprehend, Investigate, Structure, Write,
  Link.
- `.claude/workflows/implement-epic.js:1-9` — 3 entries: Discover, Implement, Report.

Every entry is `{ title: '<Name>', detail: '<description>' }` — `title` is always a single-quoted
string literal on one physical line. A regex/AST-lite extraction (e.g.
`re.findall(r"title:\s*'([^']+)'", phases_block_text)` scoped to the text between `phases: [` and
the matching `]`) is sufficient — confirmed no entry uses double quotes, template literals, or
multi-line title strings in any of the three files. This matches the idea doc's constraint ("small
regex/AST-lite extraction... NOT a full JS parser").

### Actual phase-emitting call sites — cross-checked title-by-title, not assumed

- `implement-ticket.js`: every one of its 11 `meta.phases` entries has a matching `phase('<Name>')`
  call and at least one `pushEvent('<Name>', ...)` call site, confirmed by grep
  (`grep -n "^phase(\|pushEvent(" implement-ticket.js`). `Security-Review` (line 898) is
  conditionally executed — its `phase()`/`pushEvent()` calls only run inside the
  `if (ticketInfo.tags.includes('security') || ...)` block (lines 896-945) — confirmed consistent
  with `docs/agent-monitoring/schema.md:179-181`, which explicitly documents "absent entirely (not
  even a `skipped` event) for every other ticket." For hotfix tier, `Investigate`/`Plan`/`Review`
  (lines 512-517) and `Architecture-Verify` (line 646) still get explicit `pushEvent(..., 'skipped',
  ...)` calls — they are never silently absent, just status=`skipped`.
- `create-tickets.js`: all 5 `meta.phases` entries have matching `pushEvent` calls (grep-confirmed,
  lines 190/193, 321/324, 527/596, 696/700, 813). `Link` (line 813) is conditional on `epic_id` being
  provided, matching `schema.md:183` ("Link (only when `epic_id` is provided)") — same
  conditional-phase shape as `Security-Review`.
- **`implement-epic.js`: a real, live, always-firing discrepancy, not a synthetic example.**
  `meta.phases` declares 3 entries (Discover, Implement, Report) and the file does call
  `phase('Discover')` (line 39), `phase('Implement')` (line 177), `phase('Report')` (line 283) — but
  it **never calls `pushEvent` at all**. Instead, at lines 221-227, it builds `batchEvents` directly
  with a hardcoded literal: `phase: 'Implement'` for every single event, regardless of which
  `ticket_id` in the batch it represents. This means **every completed `implement-epic` run's
  `events.jsonl` slice has zero events with `phase == 'Discover'` and zero with `phase == 'Report'`**
  — both declared phases are permanently, silently absent from every run this workflow has ever
  produced. `tools/agent-monitoring/vocabulary.py:26` (`WORKFLOW_PHASES["implement-epic"] =
  {"Implement"}`) independently corroborates this: its own docstring says it was built "from each
  workflow's actual phase(...)/pushEvent(...) call sites (grepped directly)," and it only lists
  `"Implement"` — confirming this is the workflow's actual, long-standing behavior, not a fluke of
  one run. See Risks and Open Questions — this is directly relevant to how narrowly this ticket's
  first cut should be scoped.

### Existing precedent for the cross-reference shape

`tools/gate_checks/parity_updater_static.py:81-119` (`cross_reference_touched`) is the literal
structural analog the ticket cites: given `files_changed` (a list) and `touched_ledger_files` (a
list, from `git status --porcelain`), it derives an "expected" mapping (`expected_subsystems_for_files`,
line 64) and returns a list of `{"file", "status", "evidence"}` dicts with status one of
`PASS`/`FAIL`/`NA`. The two-call split (`expected_subsystems_for_files` runs before the agent call,
`cross_reference_touched` runs after) exists specifically so the "expected" list can be injected into
the agent's own prompt as context, and the "actual" comparison runs independently afterward via
`bash()` — not because the check itself needs two passes. `workflow_meta_conformance.py` has no
analogous "inject expected list into an agent prompt" need (there's no agent call whose prompt this
would improve — see Risks below), so a single aggregate function in the shape of
`done_checker_static.py:461-472`'s `run_finalize_selfcheck` (one function returning a list of
`{"condition"/"phase", "status", "evidence"}` dicts) is the better-fitting precedent, not the two-call
split.

`tools/gate_checks/done_checker_static.py:376-405` (`check_monitoring_write_recorded`) is the more
directly relevant precedent for *how a post-hoc, run_id-keyed finding gets wired into the workflow*:
it reads `agent-monitoring/runs.jsonl` and `events.jsonl` for a given `ticket_id`
(`_jsonl_rows_for_run_id`, line 59, a small helper that filters JSONL rows by `run_id`), returns a
`(status, evidence)` tuple, and its own docstring records that it was **deliberately wired in as a
separate, later call site in `implement-ticket.js` (lines 1143-1164) rather than as a 4th condition
inside `run_finalize_selfcheck`**, specifically because an earlier hard-block design for this exact
kind of finding was rejected at architecture review "for silently reversing the Hard Rule" (see
`stored_artifacts/TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING/plan.md`, Design Decision 2). This is
the single closest precedent in the repo for the advisory-vs-blocking question this ticket must
resolve (see Risks and Open Questions).

### `run_finalize_selfcheck` / gate call-site inventory in `implement-ticket.js`

Confirmed by re-reading the full file (1179 lines) end to end, not assumed from the idea doc:

1. `writeSidecar(seq)` (line 178) — orchestrator-run `bash()`, before every `agent()` call.
2. `run_static_precheck` (Verify phase, line 997) — agent-invoked, not orchestrator bash().
3. `run_finalize_selfcheck` (Finalize phase, line 1085-1131) — orchestrator `bash()`, **blocking**:
   any `FAIL` → `FINALIZE_INCOMPLETE`, workflow returns early.
4. `check_monitoring_write_recorded` (line 1143-1164) — orchestrator `bash()`, **runs immediately
   after `writeMonitoring('DONE')` and before the final `return`**, **non-blocking**: a `FAIL` only
   sets `monitoringWarning` and appends a `WARNING:` line to the final `message` field —
   `status` stays `'DONE'`.

Call site #4 is the exact shape this ticket's check should mirror: it already runs post-hoc, keyed
only by `tid` (== `run_id`), after every phase has already executed and after monitoring has already
been written — the same point at which a phase-vs-event cross-reference becomes possible at all
(the run's own `events.jsonl` slice isn't complete until `writeMonitoring` has run).

### `agent-monitoring/events.jsonl` — actual shape (read directly, not from schema.md alone)

Confirmed via `docs/agent-monitoring/schema.md:71-100` and by reading live rows (e.g.
`TCK-20260710-CURRENT-RUN-SIDECAR-BASH`'s 10 events in `agent-monitoring/events.jsonl`). Relevant
fields for this check: `run_id` (string, FK), `phase` (string), `status` (`ok`|`failed`|`blocked`|
`skipped`). A live example: that run's events cover exactly `Scope, Investigate, Plan, Review,
Implement, Architecture-Verify, Test, Parity(skipped), Verify, Finalize` — 10 of
`implement-ticket.js`'s 11 declared phases, `Security-Review` correctly absent (ticket had no
`security` tag) — this is a real "should NOT flag" fixture case, useful for a true-negative test.
`tools/agent-monitoring/vocabulary.py` is the single source of truth for the canonical phase-name
*set* per workflow (used by `record_events.py`'s warn-only check and `validate.py`'s drift report) —
but it answers a different question ("is this phase name ever legitimate for this workflow") than
this ticket's check ("for this one run, which declared phases have zero events").

## Mechanics / Engine Constraints

None. This ticket is agent-infrastructure tooling (`tools/gate_checks/`, `.claude/workflows/`,
`agent-monitoring/`) — it does not touch simulation state, the tick kernel, or any
`docs/mechanics/`/`docs/engine/` law. No chapter or contract constrains this work.

## Parity Ledger Overlap

**None.** Searched `docs/parity_ledger/infrastructure.yaml` (the subsystem file most likely to cover
agent-monitoring/observability) for `workflow`/`monitoring`/`phase` — every hit is either an
authoritative *engine tick phase* entry (`Kernel._phase_init`, `PHASE_READ_DOMAINS`,
`_phase_advancement`, etc. — a completely different "phase" concept: engine kernel phases, not
`.claude/workflows/*.js` orchestration phases) or CI/workflow-file (`.github/workflows/test.yml`)
references. None concern agent-orchestration `meta.phases` vs. `events.jsonl`. No entry ID applies;
none needs a status/evidence update as a result of this ticket, and no new entry should be added
(this is tooling behavior, not simulation-mechanics behavior — it does not belong in the parity
ledger at all, consistent with how `parity_updater_static.py`/`done_checker_static.py` themselves
have no parity ledger entries either).

## Prior Work

- `stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/` — established the
  `expected_subsystems_for_files`/`cross_reference_touched` two-call shape and its "visibility-only,
  no new blocking status" design decision, later **explicitly reversed** by
  `TCK-20260710-...` (see `implement-ticket.js:867-871`, the comment "Reverses
  TCK-20260705-GATE-DET-PARITY-UPDATER's explicit 'visibility-only, no new blocking status'
  decision... this ticket's own ACs ask for exactly the gate that decision declined to add"). This
  shows the repo has already flipped a similar advisory→blocking decision once, when a later
  ticket's ACs explicitly demanded it — relevant precedent that "advisory first" is not a permanent
  choice, just this ticket's starting recommendation (see Risks below).
- `stored_artifacts/TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING/` — added
  `check_monitoring_write_recorded` and `check_registry_entry_regenerated`; its plan.md's Design
  Decision 2 is the direct precedent for keeping a post-hoc, run_id-keyed finding **non-blocking**
  and wired in as a separate later call site rather than folded into the blocking
  `run_finalize_selfcheck` aggregate. This is the strongest piece of prior work for resolving this
  ticket's own open advisory-vs-blocking question.
- `tickets/done/TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT` — a *prior, human/LLM-caught*
  instance of exactly the drift class this ticket wants to automate detection of, but one layer
  different: that ticket found `SKILL.md`'s prose *summary* of the phase list had drifted from
  `meta.phases` (11 vs. 9 listed) — a docs-vs-code drift, not a declared-phase-vs-actual-event drift.
  Its own ticket text states the fix was "unlikely to cause a functional pipeline skip" because the
  SKILL.md's Action section tells the executing agent to read the live `.js` file directly — i.e.
  this prior ticket was about stale *documentation*, this ticket is about stale *execution*. Useful
  parallel, not a duplicate.
- No stored artifact or done ticket implements anything resembling `workflow_meta_conformance.py` —
  confirmed by grep across `tools/` for `meta.phases`/`workflow_meta` (zero hits) and by reading
  every file under `tools/gate_checks/` (`architecture_reviewer_static.py`, `done_checker_audit.py`,
  `done_checker_static.py`, `mechanics_auditor_static.py`, `parity_updater_static.py` — five files
  total, no sixth pre-existing file for this).

## Risks and Open Questions

1. **Advisory vs. hard block — RECOMMENDATION: advisory, mirroring `check_monitoring_write_recorded`
   exactly, not `run_finalize_selfcheck`.** Reasoning, grounded in this repo's own precedent rather
   than assumed: `run_finalize_selfcheck`'s 4 conditions (`migration_complete`, `ticket_finalized`,
   `working_log_exactly_one_row`, `registry_entry_regenerated`) are all things Finalize's own current
   invocation is directly responsible for and can be *fixed by retrying Finalize* — that's exactly
   why blocking there is actionable. A missing-phase-event finding is structurally different: by the
   time Finalize (or any later point) discovers e.g. Investigate silently had zero events, that
   phase's window has already closed for this run — there is no "retry" path in `implement-ticket.js`
   that re-executes an already-completed earlier phase (`ticket_id`-based resume starts from Scope
   and re-derives tier; it does not selectively re-run one named phase). Hard-blocking at Finalize
   would strand the ticket in a permanently-`BLOCKED` state with no in-workflow remedy, which is
   exactly the "silently reversing the Hard Rule" failure mode architecture review rejected for
   `check_monitoring_write_recorded`'s own earlier hard-block design. Advisory (log a `WARNING:` in
   the final `message`, never change `status` away from `'DONE'`) is therefore the better-fitting
   default — **but this ticket's own AC #3 explicitly requires this decision be made deliberately in
   Plan, not assumed here**, so Plan must still record it as a considered decision, not silently
   inherit this investigation's recommendation.
2. **Conditional phases are not a one-off (`Security-Review`) — they're a pattern, and the checker
   must model them as such, not hardcode one name.** Both `implement-ticket.js`'s `Security-Review`
   and `create-tickets.js`'s `Link` are declared in `meta.phases` but legitimately have zero events
   for most runs. A naive "flag any declared phase with zero events" implementation would produce a
   **100% false-positive rate** on `Security-Review` for every non-`security`-tagged ticket (the
   overwhelming majority) and on `Link` for every `create-tickets` run without `epic_id`. The checker
   needs either (a) a small conditional-phase allowlist keyed by workflow (mirroring
   `vocabulary.py`'s existing keyed-by-workflow dict shape) that suppresses the flag when a documented
   trigger condition wasn't met, or (b) to only ever flag phases that also have zero `skipped`-status
   events (since every confirmed-legitimate skip in this codebase — hotfix's
   Investigate/Plan/Review/Architecture-Verify — still emits an explicit `skipped` event; only the
   two truly-conditional phases emit literally nothing). Option (b) is simpler, requires no
   per-workflow allowlist maintenance, and is already sufficient to distinguish "legitimately absent"
   from "silently vanished" for every case found in this investigation — recommend it, but this
   should be confirmed/decided explicitly in Plan, not silently assumed.
3. **`implement-epic.js` is a real, always-firing true positive today, not a hypothetical or a
   synthetic-only test case — but AC #1 only requires `implement-ticket.js` parsing "at minimum."**
   Building the parser generically enough to also handle `implement-epic.js` would immediately
   surface a finding against literally every completed `implement-epic` run
   (`Discover`/`Report` always zero-event). Whether fixing that underlying gap in
   `implement-epic.js` itself is in scope for *this* ticket (which only asks for a verifier tool) or
   should be split into its own follow-up ticket once the verifier exists is an open scoping question
   that Plan must decide explicitly — do not silently expand scope to also patch
   `implement-epic.js`'s event-emission, and do not silently ignore that the tool, once built, will
   immediately have a real finding to report if pointed at that workflow.
4. **No agent-prompt injection point exists for this check, unlike `parity_updater_static.py`'s
   `expected_subsystems_for_files`.** The parity precedent's two-call split exists because its
   "expected" list is injected into the `parity-updater` agent's own prompt as context (`implement-
   ticket.js:828`, `Expected parity-ledger files per changed src/ file: ${expectedSubsystemsOutput}`).
   There is no analogous agent call this ticket's check could usefully feed context into — the
   finding is about phases that have *already run* (or not) by the time any check could execute. This
   confirms the single-aggregate-function shape (Risk/recommendation above) over the two-call split,
   but Plan should still explicitly decide this rather than assume it.
5. **Workflow-source-file resolution.** `meta.name` (e.g. `'implement-ticket'`) doesn't map 1:1 to a
   file path via any existing helper — it's simply `.claude/workflows/{meta.name}.js` in every case
   observed (3/3 files checked), but there is no existing registry/lookup for this; the checker will
   need either a trivial `f".claude/workflows/{workflow_name}.js"` convention (confirmed to hold for
   all 3 files today) or to derive `workflow_name` from `run_id` via
   `tools/agent-monitoring/vocabulary.py::infer_workflow` (already exists, already handles the 4
   disjoint `run_id` prefix conventions — `TCK-`, `EPIC-`/`FOLDER-`, `CREATE-TICKETS-`,
   `SIMQ-AUDIT-`). Reusing `infer_workflow` avoids a second, possibly-inconsistent `run_id` → workflow
   mapping (the same "don't duplicate this vocabulary" principle `vocabulary.py`'s own docstring
   states) — recommend importing it rather than re-deriving.
6. **`simq-audit.js` is out of this ticket's stated scope** (not listed in Related Code Areas) but
   exists as a 4th workflow with its own `meta.phases`-equivalent — not read in this investigation
   since it's out of scope; flagging only so Plan doesn't assume "all workflows" means "all 4."

## Anti-Drift Hazards

- **Do not let the conditional-phase handling (Risk #2) regress into a hardcoded
  `if phase == 'Security-Review'` special case.** The moment `Link` (already conditional today) or
  any future conditional phase is added, a hardcoded single-name check silently stops working for it.
  Use the "zero events of any status, including `skipped`" rule (recommended above) so it
  generalizes without per-phase maintenance.
- **Do not consume `bash()` output from the new check via a bare `JSON.parse()`.** Every existing
  call site in `implement-ticket.js` (`archCheckOutput`, `p0ScanOutput`, `expectedSubsystemsOutput`,
  `crossRefOutput`, `finalizeCheckOutput`, `monitoringCheckOutput`) uses a `MARKER:`-prefix +
  `indexOf` + `try/catch JSON.parse` guard, with an explicit "unparseable → treat as non-blocking,
  never silently pass as clean" fallback. A new call site that skips this guard would be the first to
  regress that established, load-bearing convention.
- **Do not embed `files_changed`/phase-list JSON directly inside a double-quoted `python3 -c "..."`
  string.** `implement-ticket.js`'s own comments (lines 174-177, 771-776) document that this
  corrupts the script on nested unescaped quotes and silently fails open — pass values as
  individually-quoted argv elements instead, per the file's own established pattern.
- **Do not read/parse `.claude/workflows/*.js` with a real JS parser or `node` subprocess** — the
  ticket's own idea-doc source is explicit this must stay "small regex/AST-lite," and no `node`/JS
  toolchain dependency exists anywhere else in `tools/` today (confirmed: every other gate check is
  pure Python + regex/yaml, no subprocess to a JS runtime).
- **Do not let this check silently fire against `implement-epic.js` batch-monitoring writes** (Risk
  #3) without an explicit Plan decision — those writes go through a different code path
  (`batchEvents` built inline, not `pushEvent`) and hardcode `phase: 'Implement'`, so pointing the
  checker at an `EPIC-*`/`FOLDER-*` run_id today would produce a same-shaped-but-different-root-cause
  finding (a workflow-authoring bug, not an LLM-narration skip) that the advisory message text should
  not conflate with the "narrating LLM silently skipped a phase" framing this ticket is built around.
- **Do not duplicate `vocabulary.py`'s phase-name knowledge.** `WORKFLOW_PHASES` is the existing
  single source of truth for "what phase names are ever legitimate for workflow X" — the new checker
  answers a different question (this run's actual coverage vs. this workflow's declared phases) and
  should import from `vocabulary.py` (e.g. `infer_workflow`) rather than re-deriving any part of that
  mapping.
