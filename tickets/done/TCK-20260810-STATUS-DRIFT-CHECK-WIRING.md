---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-STATUS-DRIFT-CHECK-WIRING
phase: done
date: 2026-08-10
tags: [ai, agent-monitoring, process-improvement, data-quality]
---

# TCK-20260810-STATUS-DRIFT-CHECK-WIRING

## Title
Wire `status_drift_check.py` into real enforcement/reporting and fix the real current
`## Status` drift instances it already found (3 originally cited, 7 confirmed real at
Investigate/Implement time)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`tools/ticket_field_values.py` hard-blocks `## Tier`/`## Priority` at ticket-close time
(`done_checker_static.py::run_static_precheck`), but `## Status`'s equivalent checker,
`tools/gate_checks/status_drift_check.py`, remains exactly what its own docstring says it is:
"ships unwired — no `Makefile` target, no `.claude/workflows/*.js` invocation... a future ticket
decides where/whether to call it." No such ticket existed before this one.

Running it live during a 2026-08-10 ticket-process audit found it is not merely theoretically
useful — it is catching **real, current** drift right now:

```
FAIL: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md: ## Status reads 'OPEN', expected DONE
FAIL: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md: ## Status reads 'OPEN', expected DONE
FAIL: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md: ## Status reads 'OPEN', expected DONE
```

All 3 sit in `tickets/done/` with frontmatter already correctly showing they're closed, but the
ticket-body `## Status` heading was never updated — `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC`
closed only 4 days before this audit. The checker's own docstring documents the real, non-cosmetic
consequence: this exact drift class previously caused `dashboard-frontend/src/components/GanttBar.tsx`'s
`classifyFinalStatus()` (exact string match on `'DONE'`) to render genuinely-successful runs in the
neutral/gray bucket instead of green.

Two more flagged records — `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md`,
`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md` — are **not** real drift: their `## Status` line
legitimately reads `DONE` followed by real trailing prose (e.g. "DONE — GO verdict. Found and drove
the fix for 2 real bugs..."), which the checker's own documented, disclosed, exact-match limitation
flags as a false positive. Do not "fix" these by editing their real, accurate completion prose to
satisfy the checker.

**Corpus-moved update (Investigate/Implement, 2026-08-15):** a fresh live run confirmed the
original 3 still hold, but found 4 additional real drift instances that appeared in the corpus
between ticket authorship and Implement (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`, and
this session's `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`,
`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`,
`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`) — 7 real instances total, all fixed by this
ticket (see `investigation.md` Risk #1, `plan.md` Step 1). This is expected corpus churn, not an
investigation error. Also, the "real, non-cosmetic consequence" cited above (`GanttBar.tsx`'s
`classifyFinalStatus()`) is dead code — the file was deleted 2026-07-30 by
`TCK-20260720-PROGRESS-TIMELINE-VIEW`, 11 days before this ticket was authored. The real, live
consequence is `src/api/agent_ops_dashboard/ingest.py:137,586`'s `workflow_status` field and
`dashboard-frontend/src/views/TicketsView.tsx:39-46`'s status filter/display — corrected in
`docs/parity_ledger/infrastructure.yaml`'s INFRA-277 entry (see Implementation Notes).

## Scope
- **Investigate (mandatory before Plan):** confirm the 3 real drift cases and 2 false positives
  above still hold against current `tickets/done/` state (the corpus changes daily), and read
  `status_drift_check.py`'s full docstring (known limitations section) plus
  `tools/generate_registry.py::parse_body_section` (the shared extraction function it correctly
  reuses) before touching anything.
- Fix the 3 real drift instances: update each ticket's `## Status` body text to `DONE`, matching
  the pattern `implement-ticket.js`'s current Finalize phase already produces reliably for new
  tickets (per `status_drift_check.py`'s own docstring — this is a data-repair, not a new
  mechanism).
- Wire `status_drift_check.py` into a real path — decide (Plan phase) whether that's:
  (a) a new blocking condition in `done_checker_static.py::run_static_precheck`, mirroring
  `ticket_field_values.py`'s `## Tier`/`## Priority` precedent, or
  (b) a recurring `generate_retro.py`/Makefile-driven report-only check (lower blast radius, matches
  this module's own "ships unwired... future ticket decides" framing more literally).
  Either is acceptable; state the reasoning, matching this epic's evidence-driven-decision
  convention (see `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`'s per-skill gate-conversion
  precedent — not a blanket "wire everything to a hard gate" default).
- If wired as a blocking gate: confirm it does not retroactively block any of the 187
  pre-2026-07-04 legacy tickets `validate_frontmatter.py` already excludes on the same
  forward-only-enforcement principle (`docs/guidelines/tag_taxonomy.md`) — this checker has no such
  date exemption today; decide whether it needs one before going live as a blocking gate.
- Do not touch the 2 known false-positive records' real completion prose. If the exact-match
  limitation is itself worth loosening (e.g. prefix-match on `DONE`), that is a separate design
  decision to make explicitly, not a silent side effect of wiring.

## Out of Scope
- Rebuilding or modifying `status_drift_check.py`'s existing detection logic, its
  `parse_body_section` reuse, or its lowercase-`final_status` check in
  `agent-monitoring/runs.jsonl` (currently PASS, no known issue there).
- Revisiting the "6 files corpus-wide, same-line colon-suffixed `## Status: X`" exclusion —
  `TCK-20260718-STATUS-DRIFT-REPAIR`'s plan.md explicitly scoped that out and this ticket does not
  reopen it.
- A blanket sweep of all pre-2026-07-04 tickets for the same drift class — this ticket fixes the 3
  real current instances found; a corpus-wide legacy sweep (if warranted) is a separate,
  separately-scoped decision, matching `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s precedent of
  keeping legacy-debt sweeps report-only and separately ticketed.

## Acceptance Criteria
- [x] `investigation.md` re-confirms the 3 real drift cases (or documents if the corpus has moved)
      with real, current `status_drift_check.py` output, not the numbers cited in this ticket.
- [x] The 7 real drift instances (the ticket's originally-cited 3, plus 4 more the investigation
      independently confirmed real and live via `working_log.csv`/`stored_artifacts/` evidence —
      see `investigation.md` Risk #1 and `plan.md`'s Step 1 scope-decision note) have their
      `## Status` body text corrected to `DONE`. Originally worded "the 3 real drift instances";
      corrected here per Architecture Review's process note so the closed ticket does not read as
      contradicting its own completion — the evidence-based scope decision to fix all 7 (not just
      the 3 as literally worded when the ticket was authored) was made explicitly in Plan, not a
      silent expansion.
- [x] The 2 false-positive records are left untouched (verified by a diff check in Verify).
- [x] `status_drift_check.py` is wired into a real, decided path (blocking gate or recurring
      report), with the choice justified in `plan.md`.
- [x] If wired as a blocking gate: a forward-only-enforcement exemption question (per
      `tag_taxonomy.md`'s precedent) is explicitly answered, not left implicit. (Answered: not
      applicable — no blocking gate was added, so no enforcement point exists to need the
      exemption. See Implementation Notes.)
- [x] Scoped pytest run passes (`tests/tools/test_status_drift_check.py` plus any new tests for the
      wiring itself).

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260718-STATUS-DRIFT-REPAIR (DONE; original 71-file repair + built the checker)
- TCK-20260718-STATUS-MULTILINE-FIX (DONE; fixed the checker's own extraction to use
  `parse_body_section` instead of a first-token-only regex)
- TCK-20260718-STATUS-SUFFIX-TRIM (DONE; sibling drift-class fix, same investigation thread)
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (DONE; built `ticket_field_values.py` and the
  hard-blocking precedent this ticket's gate-wiring option (a) would extend to `## Status`)
- TCK-20260718-STATUS-FACET-CANONICAL (DONE; the dashboard-facet canonical set `## Status`'s
  real-world consequence traces back to)
- TCK-20260720-TAG-CORPUS-REPAIR-SWEEP (DONE; precedent for keeping legacy-debt sweeps report-only
  and separately scoped, referenced by this ticket's Out of Scope)

## Related Docs
- `tools/gate_checks/status_drift_check.py`'s own docstring (known limitations, real consequence
  class, exclusion precedent)
- CLAUDE.md's Definition of Done section

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/gate_checks/status_drift_check.py`
- `tools/generate_registry.py` (`parse_body_section`, reused not reimplemented)
- `tools/gate_checks/done_checker_static.py`
- `tools/ticket_field_values.py` (precedent for the blocking-gate wiring option, not used —
  report-only Makefile wiring was chosen instead)
- `Makefile` (new `status-drift-check` target)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-277, updated via `tools/parity_ledger_writer.py`)
- `src/api/agent_ops_dashboard/ingest.py:137,586` (`workflow_status`, the real live consumer of
  ticket-body `## Status` — corrects this ticket's original `GanttBar.tsx` citation, confirmed
  deleted 2026-07-30 and no longer a real code path)
- `dashboard-frontend/src/views/TicketsView.tsx:39-46` (renders/filters `workflow_status`)
- `tickets/done/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md`,
  `tickets/done/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`,
  `tickets/done/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md`,
  `tickets/done/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION.md`,
  `tickets/done/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS.md`,
  `tickets/done/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION.md`,
  `tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md` (the 7 real drift fixes)

## Assumptions / Open Questions
- Whether wiring should be a hard gate vs. a recurring report is explicitly left to
  Investigate/Plan — the epic's own evidence-driven-decision convention applies here, not a
  default toward maximal enforcement.
- Whether a forward-only-enforcement date exemption is needed for a blocking-gate wiring choice —
  not assumed; Plan must decide with reasoning if option (a) is chosen.

## Implementation Notes
Implemented `plan.md`'s 5 steps in order (2026-08-15).

**Step 1 — Fixed all 7 confirmed real `## Status` drift instances.** Live-corpus run before the
fix confirmed the exact 9 FAIL findings `investigation.md` documented (7 real + 2 known false
positives). Each of the 7 real files had its `## Status`-heading value (`OPEN` for the 4
`TCK-20260721`/`TCK-20260806` files, `INPROGRESS` for the 3 `TCK-20260810` files) replaced with
`DONE` via a scripted single-line regex substitution, leaving every other byte untouched. Verified
with `git diff --stat` per file: exactly 1 line changed in each of the 7 files, zero diff on the 2
false-positive files (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md`,
`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md`). Post-fix live run shows exactly 2 remaining FAIL
findings, both the known false positives, byte-identical evidence to the pre-fix run.

**Step 2 — Wired `status_drift_check.py` into a report-only `status-drift-check` Makefile target.**
Added immediately after `agent-monitoring-epic-staleness` (`Makefile`), mirroring its shape exactly
(no `.PHONY` entry — `agent-monitoring-epic-staleness` itself isn't in `.PHONY:` either, confirmed
by direct read before matching it). Recipe is exactly `python3
tools/gate_checks/status_drift_check.py` — no change to `check_status_drift()` or its `__main__`
block. `make status-drift-check` runs and exits non-zero (2 remaining FAIL) as expected — this is a
report, not a gate, so a non-zero `make` exit is expected/inert here (no CI or workflow phase
invokes this target automatically).

**Step 3 — Forward-only-enforcement decision (AC5), documented explicitly here per plan.md's Step
3.** The exemption question is **not applicable**, because no blocking gate was added. Step 2
chose a report-only Makefile target instead of a new condition in
`done_checker_static.py::run_static_precheck`, so there is no ticket-close-time enforcement point
for a legacy pre-2026-07-04 ticket to be blocked by — the exemption question `tag_taxonomy.md`'s
forward-only precedent exists to answer (avoiding blocking a legacy file that predates a rule) only
arises for a blocking gate, and this ticket does not add one. This is not merely "not needed today
because 0 of 9 FAIL findings are pre-2026-07-04" (a fact that could change with corpus drift) — it
is structurally not needed because the wiring itself never blocks anything. If a future ticket adds
a blocking gate (option (a), evaluated and rejected in `plan.md` Step 2) later, that ticket must
re-decide the exemption question fresh against corpus state at that time; no speculative
date-exemption code path was added anywhere in `status_drift_check.py` or `ticket_field_values.py`.

**Step 4 — Updated INFRA-277 (`docs/parity_ledger/infrastructure.yaml`) via
`tools/parity_ledger_writer.py::write_entry()`.** Appended new `v2_evidence` content (rather than
editing the historical `text` field, per this ledger's own convention) that: (1) states the wiring
decision made in Step 2 (report-only Makefile target, not a blocking gate) and why, superseding the
stale "Ships unwired... a future ticket decides" claim; (2) corrects the dead
`GanttBar.tsx`/`classifyFinalStatus()` consequence citation — confirmed absent from the working
tree (deleted 2026-07-30, `TCK-20260720-PROGRESS-TIMELINE-VIEW`) — to cite the real, live consumer:
`src/api/agent_ops_dashboard/ingest.py:137` (`workflow_status` extraction) and `:586` (the
Tickets-tab filter comparison), rendered in `dashboard-frontend/src/views/TicketsView.tsx:39-46`;
(3) states the real live-corpus numbers found (9 FAIL pre-fix: 7 real + 2 known false positives; 2
FAIL remain post-fix, both known false positives). `status` stayed `verified`, `priority` stayed
`P2` — documentation correction only, not a status reclassification. `write_entry()` validated the
entry and rebuilt the in-process derived index on success; a separate, visible `python3
tools/parity_index.py build` Bash call was then issued per `parity_ledger_writer.py`'s own
docstring guidance (the in-process rebuild alone is invisible to
`generate_retro.py`'s `parity_write_safety` metric, which only matches a distinct Bash call
literally containing "parity_index.py" and "build"). Confirmed the resulting YAML still parses and
that `write_entry()`'s fresh-read-then-write design preserved unrelated concurrent edits already
present in the working tree (INFRA-292, INFRA-315, and new entries INFRA-331/332/333, none touched
by this ticket) — those are from other in-progress work sharing this working tree, not part of this
ticket's diff.

**Step 5 — Tests.** Added `test_makefile_wires_status_drift_check` to
`tests/tools/test_status_drift_check.py`, a pure source-text/regex static check (no live `make`,
no subprocess) asserting the `status-drift-check:` target exists in `Makefile` with the exact
recipe line, mirroring `test_dashboard_makefile_targets.py`'s approach and matching
`test_epic_staleness_check.py`'s precedent of no subprocess test for a report-only corpus check.
Ran the scoped verification commands from `plan.md`'s Step 5:
- `tests/tools/test_status_drift_check.py` — 18 passed (17 pre-existing + the 1 new test; the
  pre-existing count was 17 in the current corpus, not the 16 `plan.md` cited from an earlier
  read — `test_bare_scoped_no_longer_exempt_after_tightening` was already present and untouched;
  no deviation in behavior, only in the plan's stated count, noted in `plan.md`'s Deviations).
- `tests/tools/test_ticket_field_values.py tests/tools/test_done_checker_static.py` — 102 passed.
- `tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — 58 passed, 1 pre-existing failure
  (`test_no_source_file_imports_full_echarts_bundle`, flagging a bare `echarts` import in
  `dashboard-frontend/src/views/ProgressTimelineView.tsx`) confirmed unrelated to this ticket: that
  file is byte-identical to `HEAD` (`git diff` empty, `git status` clean for it) and this ticket's
  scope guard explicitly forbids touching any `.tsx` file — pre-existing repo state, not introduced
  or masked by this work.
- Live-corpus command (`python3 tools/gate_checks/status_drift_check.py`) and `make
  status-drift-check` both re-run at the end — final state: exactly 2 FAIL (the 2 known false
  positives only), matching plan.md's Step 1 Verify expectation exactly.

No deviations from `plan.md`'s architecture or scope guards. No `.tsx` file was touched. No change
to `check_status_drift()`, `parse_body_section`, the colon-suffix exclusion, or
`done_checker_static.py::run_static_precheck` (still 7 conditions).

## Test Summary
- `tests/tools/test_status_drift_check.py` — 18 passed (`.venv/bin/python3 -m pytest
  tests/tools/test_status_drift_check.py -v`).
- `tests/tools/test_ticket_field_values.py`, `tests/tools/test_done_checker_static.py` — 102 passed.
- `tests/tools/test_agent_ops_dashboard_ingest.py`, `tests/tools/test_agent_ops_dashboard_api.py`,
  `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — 58 passed, 1 pre-existing failure
  unrelated to this ticket (see Implementation Notes).
- Live-corpus verification: `python3 tools/gate_checks/status_drift_check.py` and `make
  status-drift-check` both show exactly 2 FAIL post-fix (the 2 known false positives), matching the
  expected outcome.
- Repo-wide `pytest tests/` was not run, per `plan.md`'s explicit instruction and CLAUDE.md's
  scoped-testing rule.

## Files Changed
- `tickets/done/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md` (`## Status` OPEN → DONE)
- `tickets/done/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md` (`## Status` OPEN → DONE)
- `tickets/done/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md` (`## Status` OPEN → DONE)
- `tickets/done/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION.md` (`## Status` OPEN → DONE)
- `tickets/done/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS.md` (`## Status` INPROGRESS → DONE)
- `tickets/done/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION.md` (`## Status`
  INPROGRESS → DONE)
- `tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md` (`## Status` INPROGRESS →
  DONE)
- `Makefile` (new `status-drift-check` target)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-277 `v2_evidence` updated via
  `tools/parity_ledger_writer.py::write_entry()`)
- `tests/tools/test_status_drift_check.py` (added `test_makefile_wires_status_drift_check`)
- `tickets/inprogress/TCK-20260810-STATUS-DRIFT-CHECK-WIRING.md` (this file — AC2/Title/Request
  Summary/Related Code Areas wording corrections, Implementation Notes, Status)

Not changed, confirmed by diff: `tickets/done/TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md`,
`tickets/done/TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md` (the 2 false positives),
`tools/gate_checks/status_drift_check.py`, `tools/generate_registry.py`,
`tools/gate_checks/done_checker_static.py`, `tools/ticket_field_values.py`, any `.tsx` file.

## Completion Summary
Fixed all 7 confirmed-real `## Status` body-text drift instances in `tickets/done/*.md` (the
ticket's originally-cited 3 plus 4 more the investigation independently confirmed real and live),
wired `status_drift_check.py` into a new report-only `status-drift-check` Makefile target
mirroring `agent-monitoring-epic-staleness` (no blocking gate — a per-ticket gate would have caught
none of the 7 real cases found, since none of those tickets are being re-closed now; only a
corpus-wide recurring report can find already-existing drift), explicitly documented the
forward-only-enforcement question as structurally moot given no blocking gate exists, corrected
INFRA-277's stale "ships unwired" claim and dead `GanttBar.tsx` citation to the real live consumer
(`ingest.py`'s `workflow_status` field and `TicketsView.tsx`'s status filter) via the required
`parity_ledger_writer.py::write_entry()` path plus a separate visible `parity_index.py build` call,
and added a static Makefile-text regression test. Live-corpus verification after the fix shows
exactly 2 remaining FAIL findings (the 2 known false positives, confirmed untouched by diff),
matching the plan's expected outcome exactly.
