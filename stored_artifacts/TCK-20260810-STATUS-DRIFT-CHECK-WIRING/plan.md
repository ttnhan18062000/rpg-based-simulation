---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-STATUS-DRIFT-CHECK-WIRING
artifact_type: plan
tags: [ai, agent-monitoring, process-improvement, data-quality]
---

# Implementation Plan — TCK-20260810-STATUS-DRIFT-CHECK-WIRING

## Summary

This plan repairs all 7 real `## Status` body-text drift instances confirmed live today (the
ticket's originally-cited 3, plus 4 additional real instances the investigation independently
confirmed via `working_log.csv`/`stored_artifacts/` evidence — not the 2 known false positives,
which are left untouched), wires `tools/gate_checks/status_drift_check.py` into a new standalone,
report-only Makefile target (`status-drift-check`) that mirrors the existing
`agent-monitoring-epic-staleness` precedent exactly — not a blocking gate in
`done_checker_static.py::run_static_precheck` — because the investigation's own evidence shows a
per-ticket blocking gate would have caught none of today's 7 real cases (none of those tickets are
being re-closed right now), while a corpus-wide recurring report is the exact mechanism that found
them. Because no blocking gate is added, the forward-only-enforcement date-exemption question (AC5)
is explicitly answered as not applicable today — documented as a deliberate, revisitable choice, not
a silent omission. The plan also corrects `docs/parity_ledger/infrastructure.yaml`'s INFRA-277 entry,
which is stale on two counts: it still says "ships unwired" (this ticket wires it) and still cites a
dead consequence chain (`GanttBar.tsx`'s `classifyFinalStatus()`, deleted 2026-07-30 by
TCK-20260720-PROGRESS-TIMELINE-VIEW, confirmed absent from the working tree today) instead of the
real, live consumer: `src/api/agent_ops_dashboard/ingest.py:137`'s `workflow_status` extraction and
its `:586` filter comparison, rendered in `dashboard-frontend/src/views/TicketsView.tsx:39-46`. The
separate, larger frontmatter `status:`/`phase:` drift class (173/191 files corpus-wide) found during
investigation is explicitly out of scope and not touched — noted here only as a deferred future
finding, per this ticket's own Out of Scope guard against corpus-wide sweeps.

## Steps

### Step 1 — Fix all 7 confirmed real `## Status` drift instances to `DONE`
**Files:**
- `tickets/done/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md`
- `tickets/done/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`
- `tickets/done/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md`
- `tickets/done/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION.md`
- `tickets/done/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS.md`
- `tickets/done/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION.md`
- `tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md`

**Change:** Each file's `## Status` heading is immediately followed by a single-line value with no
trailing content (confirmed by direct read of each file today: the first 3 plus
`PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` read exactly `OPEN`; the 3 `TCK-20260810-*` files read exactly
`INPROGRESS`). Replace that single line with `DONE` in each file, leaving every other line
byte-identical (frontmatter, all other body sections, and any blank-line spacing around the heading
untouched). This is a direct text edit to already-closed ticket files, not a new mechanism — it
matches the exact repair pattern `TCK-20260718-STATUS-DRIFT-REPAIR` used for the original 71 files
(see `docs/parity_ledger/infrastructure.yaml:5119-5141`, INFRA-277's `text` field, for that
precedent's description).

**Scope-decision note (resolves AC2's literal wording vs. today's corpus state):** AC2 as written in
the ticket names only "the 3 real drift instances." `investigation.md`'s Risk #1 (live run,
2026-08-14/15) independently confirmed 4 additional real, non-false-positive drift instances exist
today with the identical fix mechanism, and confirmed via `working_log.csv` DONE rows and
`stored_artifacts/` references that all 4 are genuinely completed work, not misplaced in-progress
tickets — one `working_log.csv` entry
(`TCK-20260810-D22-DORMANT-WIRING-AUDIT`) even self-disclosed
`PROJECT-SWITCH-BYPASS-GENERALIZATION`'s stale body Status as a known, undischarged gap. AC1's own
wording ("or documents if the corpus has moved") anticipates exactly this situation. Leaving 4
already-found, already-confirmed real drift cases unfixed while reporting this ticket's fix as
complete would misrepresent the corpus state this ticket itself surfaced. This is a bounded decision
about fixing every instance already found in today's one live run — not a proactive corpus-wide
search for more instances, which stays out of scope (see Scope Guards).

**Do NOT touch:** The 2 false-positive records' `## Status` text —
`tickets/done/TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md` (reads `DONE — GO verdict. Found and
drove the fix for 2 real bugs...`) and `tickets/done/TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md`
(reads `DONE (reopened once — see Implementation Notes' Reopen Notes...)`), confirmed today by direct
read — both are real, accurate completion prose that starts with `DONE` and is flagged only by the
checker's own documented exact-match limitation. Do not edit either file in any way. Also do not
touch any other `tickets/done/*.md` file not in the list above — this is not a sweep of the corpus,
only a fix of the 7 already-confirmed instances.

**Verify:** `python3 tools/gate_checks/status_drift_check.py` — live-corpus run. Before this step,
the `MARKER:` JSON payload contains 9 ticket-FAIL entries (7 real + 2 false positives). After this
step, expect exactly 2 ticket-FAIL entries remaining (the 2 known false positives, byte-identical to
before), and 0 for the 7 files above. Per `test_plan.md`'s explicit recommendation, do not add a new
pytest test hardcoding these 7 filenames (would go stale the moment corpus composition changes
again, the exact anti-pattern the checker's own value/pattern-based exemption design avoids) — the
live-run diff is Verify-phase evidence, matching this module's own read-only philosophy. A `git diff
--stat tickets/done/TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md
tickets/done/TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md` showing zero changes is the Verify-phase
proof for AC3.

### Step 2 — Wire `status_drift_check.py` into a recurring, report-only Makefile target
**Files:** `Makefile`

**Change:** Add a new `.PHONY`-eligible target immediately after the existing
`agent-monitoring-epic-staleness` target (`Makefile:281-282`, `python3
tools/agent-monitoring/epic_staleness_check.py`) — the closest real precedent in this codebase for
"a read-only, corpus-wide `tickets/` hygiene check, invoked via its own dedicated Makefile target,
never wired into `generate_retro.py` or any blocking gate":

```makefile
status-drift-check: ## Report ## Status body-text drift in tickets/done/ and lowercase final_status in runs.jsonl
	python3 tools/gate_checks/status_drift_check.py
```

No change to `status_drift_check.py` itself — `check_status_drift()` (current file:
`tools/gate_checks/status_drift_check.py:140-144`) is reused exactly as-is via its existing
`__main__` block (`:147-154`), which already implements the `MARKER:` + JSON stdout contract and
`sys.exit(1)` on any FAIL. This satisfies AC4 ("wired into a real, decided path") without touching
detection logic, matching Out of Scope's prohibition on rebuilding the checker.

**Why option (b), not option (a) (blocking gate in `done_checker_static.py::run_static_precheck`):**
`investigation.md`'s Risk #4 lays out both options; the deciding evidence is that
`run_static_precheck` (`tools/gate_checks/done_checker_static.py:466-483`, currently 7 Part A
conditions) validates only the single ticket currently at Verify/Finalize — mirrored from
`check_ticket_field_values_valid` (`:291-305`), which itself only calls
`check_ticket_field_values(ticket_path)` (`tools/ticket_field_values.py:67-86`) against one file. A
per-ticket gate of this shape would have caught **zero** of today's 7 real drift cases, because none
of those 7 files are being re-closed right now — a per-ticket gate only prevents *new* drift on
tickets closing after this wiring lands; it cannot detect drift already sitting in the corpus, which
is exactly what this ticket's own motivating evidence is. The recurring, corpus-wide report
(`check_ticket_status_drift(done_dir)`, unchanged, scans all of `tickets/done/*.md`) is the same
mechanism that surfaced this ticket's evidence in the first place, so it is the mechanism kept live
going forward.

**Why this is not the Out-of-Scope-prohibited "blanket corpus-wide legacy sweep":** The Out of Scope
section prohibits a one-time, exhaustive *repair* sweep of all pre-2026-07-04 tickets bundled into
this ticket's closure (matching `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s precedent of keeping such
sweeps report-only and separately ticketed). What this step adds is a standing, always-available
*report* mechanism — it performs no repair, fixes nothing on its own, and is invoked on-demand
(`make status-drift-check`), not on every ticket close or automatically on any cadence. This mirrors
`agent-monitoring-epic-staleness`'s identical shape (report-only, human/agent-invoked, no automatic
call site), which is not itself considered a "sweep."

**Do NOT touch:** `tools/gate_checks/done_checker_static.py::run_static_precheck` (stays at 7
conditions, unchanged — do not add an 8th `status_drift_valid` condition), `tools/ticket_field_values.py`
(no new `Status` validation function added there), `tools/agent-monitoring/generate_retro.py` (do not
add a status-drift section to the weekly agent-monitoring retro report — that module's own scope is
agent run/event/tag/skill-usage retrospectives, a different topic from ticket-body hygiene; the
closer, already-established precedent for this kind of check is `epic_staleness_check.py`'s own
dedicated target, not `generate_retro.py`), and `.claude/workflows/*.js` (no workflow phase calls
this check — it remains a manually/periodically invoked report, not part of the Verify/Finalize
agent prompt).

**Verify:** `make status-drift-check` runs and produces the expected `MARKER:` JSON payload with
`sys.exit` matching the FAIL count (2, after Step 1). New static test (Step 5) asserts the Makefile
target text exists and calls the correct script path.

### Step 3 — Explicitly document the forward-only-enforcement decision (AC5)
**Files:** `tickets/inprogress/TCK-20260810-STATUS-DRIFT-CHECK-WIRING.md` (`## Implementation Notes`
section, filled in by the implementer during Finalize per the standard ticket-close workflow — no
plan step produces a separate artifact for this)

**Change:** Record explicitly (not left implicit) that AC5's forward-only-enforcement exemption
question is answered as: **not applicable, because no blocking gate was added.** Because Step 2
chose a report-only Makefile target instead of a blocking condition in `run_static_precheck`, there
is no ticket-close-time enforcement point for a legacy pre-2026-07-04 ticket to be blocked by — the
exemption question `tag_taxonomy.md`'s forward-only precedent exists to answer (avoiding blocking a
legacy file that predates a rule) only arises for a blocking gate, and this ticket does not add one.
Document, per `investigation.md`'s Risk #5, that this is not merely "not needed today because 0 of 9
FAIL findings are pre-2026-07-04" (a fact that could change) — it is structurally not needed because
the wiring itself never blocks anything. If a future ticket adds a blocking gate (option (a)) later,
that ticket must re-decide the exemption question fresh against corpus state at that time; this
ticket does not pre-build an unused exemption mechanism now (a speculative mechanism that CLAUDE.md's
"do not create hidden or implicit durable behavior" guidance argues against building before it has a
caller).

**Do NOT touch:** Do not add a date-exemption code path to `status_drift_check.py` or
`ticket_field_values.py` — there is no blocking-gate caller for it to guard, so it would be dead code
introduced speculatively.

**Verify:** Manual read of the ticket's `## Implementation Notes` at Finalize time confirms this
reasoning is present in full (not a one-line "N/A").

### Step 4 — Update INFRA-277 (`docs/parity_ledger/infrastructure.yaml`)
**Files:** `docs/parity_ledger/infrastructure.yaml` (entry at line 5119, `id: INFRA-277`)

**Change:** Two stale claims in the current entry (read directly, lines 5119-5177) must be corrected
in `v2_evidence` (and `text` if the "Ships unwired" sentence at line 5129-5131 is retained verbatim
— it should be updated or superseded by new `v2_evidence`, following this ledger's own convention of
appending new `v2_evidence` rather than editing `text` retroactively, per past entries in this same
file):
1. **"Ships unwired... a future ticket decides where/whether to gate on it"** (`text` field, lines
   5129-5131) is no longer accurate after Step 2 — `status_drift_check.py` is now wired into
   `make status-drift-check` (`Makefile`, new target). New `v2_evidence` must state the wiring
   decision made (report-only Makefile target, not a blocking gate) and why (see Step 2's reasoning),
   citing `Makefile`'s new target and `tools/gate_checks/status_drift_check.py:140-154`
   (`check_status_drift`/`__main__`, unchanged).
2. **The dead `GanttBar.tsx`/`classifyFinalStatus()` consequence citation** (entry `text`, lines
   5137-5139: "dashboard-frontend's classifyFinalStatus() (GanttBar.tsx) is unmodified") is now
   doubly stale — confirmed today by direct filesystem check that
   `dashboard-frontend/src/components/GanttBar.tsx` does not exist (deleted 2026-07-30,
   `TCK-20260720-PROGRESS-TIMELINE-VIEW`, replaced by `ProgressTimelineView.tsx` +
   `dashboard-frontend/src/lib/toChartOption.ts`, which colors segments by
   `getPhaseSegmentColor(phase)`, never by a `final_status`/`## Status` classification). New
   `v2_evidence` must correct this to cite the real, confirmed-today live consumer:
   `src/api/agent_ops_dashboard/ingest.py:137` (`workflow_status = parse_body_section(body,
   "Status") or None`) and `:586` (`if status is not None and r["workflow_status"] != status:` — the
   Tickets-tab filter comparison), rendered in
   `dashboard-frontend/src/views/TicketsView.tsx:39-46` (confirmed by direct read: the file's own
   comment at lines 39-42 states `"status" here means TicketSummary.workflow_status (the body
   ## Status section)... not the frontmatter status field`).
3. Also update the live-corpus result count: the entry's `text`/`v2_evidence` should not continue to
   imply a clean corpus (`investigation.md` confirms a stale "confirmed clean" framing existed) —
   state the real numbers found today (9 FAIL findings pre-fix, 7 real + 2 known false positives; 2
   FAIL findings remain post-Step-1, both known false positives).

Do not change `status` (stays `verified`) or `priority` (stays `P2`) — only `v2_evidence` needs an
update per CLAUDE.md's Authoritative Mechanics Rule; this is a documentation correction, not a status
reclassification.

**Do NOT touch:** INFRA-278 (the `ticket_field_values.py` precedent entry) — its "6 blocking Part A
conditions" `text` only needs an update if option (a) were chosen; since Step 2 chose option (b),
`run_static_precheck` stays at 7 conditions and INFRA-278 is unaffected. Do not touch any other
parity ledger file — `investigation.md`'s Parity Ledger Overlap section confirmed via corpus-wide
grep that no other file references `status_drift_check`, `ticket_field_values`, or
`done_checker_static`.

**Verify:** Manual read confirming the entry no longer contains the string "Ships unwired" or an
uncorrected `GanttBar.tsx`/`classifyFinalStatus()` citation, and that `docs/parity_ledger/schema.json`
validation still passes for the file (via the standard parity-ledger write path, per CLAUDE.md's
parity-updater guidance — use `tools/parity_ledger_writer.py`'s validate/write path introduced by
TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL if available, rather than a raw YAML edit, to keep the
derived parity index from going stale).

### Step 5 — Tests and scoped verification
**Files:** `tests/tools/test_status_drift_check.py`

**Change:** Add one new static test, `test_makefile_wires_status_drift_check`, mirroring
`tests/tools/test_dashboard_makefile_targets.py`'s pure text/regex approach (no live `make`
invocation, no subprocess) — read `Makefile`'s raw text and assert the new `status-drift-check`
target exists and its recipe line is exactly `python3 tools/gate_checks/status_drift_check.py`. This
gives AC4's wiring decision a concrete regression guard. No test is added asserting a Makefile
*invocation* subprocess test (e.g. `test_epic_staleness_check.py` — the closest existing precedent
for a report-only corpus check wired via Makefile — has no such subprocess test either; a static
text guard matches established precedent and avoids a slow/flaky subprocess-based test).

No other test files change: `tests/tools/test_done_checker_static.py` needs no update since
`run_static_precheck`'s condition count/shape stays at 7 (option (a) not chosen);
`tests/tools/test_ticket_field_values.py` needs no update (module untouched);
`tests/tools/test_generate_registry.py` needs no update (`parse_body_section` untouched, per Out of
Scope). The 16 existing tests in `tests/tools/test_status_drift_check.py` must stay green unmodified
— they already cover `check_ticket_status_drift`, `check_runs_jsonl_final_status_drift`,
`check_status_drift`, the read-only guarantee, and the real-extraction-function guard; none of them
reference the 7 files fixed in Step 1 (all use synthetic `tmp_path` fixtures), so Step 1's edits to
real `tickets/done/*.md` files cannot affect them.

**Do NOT touch:** `tools/generate_registry.py`, its tests, or any existing test in
`test_status_drift_check.py` beyond the one addition above.

**Verify:**
```
python3 -m pytest tests/tools/test_status_drift_check.py -v
python3 -m pytest tests/tools/test_ticket_field_values.py tests/tools/test_done_checker_static.py -v
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v
```
Plus the live-corpus command from Step 1's Verify and `make status-drift-check` from Step 2's Verify.
Never run repo-wide `pytest tests/` — none of this ticket's scope touches `src/` simulation code.

## Scope Guards

- Do not edit `tickets/done/TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md` or
  `tickets/done/TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md` in any way — their `## Status` text is
  real, accurate completion prose, not drift.
- Do not modify `check_ticket_status_drift`'s existing exemption logic in
  `tools/gate_checks/status_drift_check.py` — the same-line colon-suffixed `## Status: X` exclusion,
  `EPIC_TIER_VALUES`, and the non-`TCK-`-prefixed-filename skip all stay exactly as they are.
- Do not modify `tools/generate_registry.py::parse_body_section` or `_strip_frontmatter` — reused,
  never reimplemented.
- Do not add a new blocking condition to `tools/gate_checks/done_checker_static.py::run_static_precheck`
  — option (a) was evaluated and rejected with reasoning in Step 2; do not silently build it anyway.
- Do not touch `tools/ticket_field_values.py` — no `## Status` validation function is added there.
- Do not add a status-drift section to `tools/agent-monitoring/generate_retro.py` — wrong topic for
  that module (agent run/event/tag/skill retrospectives, not ticket-body hygiene); `Makefile` is the
  wiring point per Step 2.
- Do not touch the frontmatter `status:`/`phase:` value-correctness drift class (173/191
  `tickets/done/*.md` files corpus-wide, found in `investigation.md` Risk #2) — a materially larger,
  differently-shaped problem (frontmatter field correctness vs. body-section text) this ticket's
  checker does not detect and was never scoped to fix. Explicitly deferred as a distinct future
  finding, not silently absorbed or fixed here.
- Do not perform a proactive, exhaustive scan of all pre-2026-07-04 `tickets/done/*.md` files
  looking for additional undiscovered drift instances beyond the 7 already confirmed in today's one
  live run (Step 1's scope). Fixing the 7 already-found-and-confirmed instances is not the same as
  the Out-of-Scope-prohibited "blanket sweep" — see Step 1's scope-decision note and Step 2's "why
  this is not a sweep" note for the precise line this plan draws.
- Do not recreate, reference as extant, or otherwise resurrect `dashboard-frontend/src/components/GanttBar.tsx`
  — confirmed deleted 2026-07-30. Only correct the stale citation in INFRA-277 (Step 4) to point at
  the real, current consumer.
- Do not add a date-exemption code path anywhere — Step 3 documents why none is needed given the
  report-only wiring choice; do not build one speculatively.
- Do not run `pytest tests/` repo-wide.

## Dependency Map

- Step 1 (data repair) — independent, can run first or in parallel with Step 2.
- Step 2 (Makefile wiring) — independent of Step 1.
- Step 3 (forward-only documentation) — depends on Step 2's decision (must know the wiring choice
  before documenting why the exemption question doesn't apply).
- Step 4 (INFRA-277 update) — depends on Step 1 (needs final FAIL-count numbers) and Step 2 (needs
  the wiring decision and its rationale to cite).
- Step 5 (tests) — depends on Step 2 (the Makefile test asserts the new target Step 2 adds) and
  benefits from Step 1 being complete first (so the live-corpus verify command in Step 1 shows the
  expected post-fix state before Step 5's scoped pytest run is treated as final).

Recommended execution order: Step 1 → Step 2 → Step 3 → Step 4 → Step 5.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: investigation.md re-confirms the 3 real drift cases (or documents if the corpus has moved) | Completed in `investigation.md` (pre-Plan, Risk #1) — no implementation step required | N/A (documentation artifact, already written) |
| AC2: the 3 real drift instances have `## Status` corrected to `DONE` (this plan implements all 7 confirmed-real instances, per the scope decision documented in Step 1) | Step 1 | `python3 tools/gate_checks/status_drift_check.py` live-corpus run (Step 1 Verify) |
| AC3: the 2 false-positive records are left untouched, verified by a diff check in Verify | Step 1 (scope guard) | `git diff --stat` on both false-positive files (Step 1 Verify) |
| AC4: `status_drift_check.py` wired into a real, decided path, choice justified in plan.md | Step 2 | `make status-drift-check` run + `test_makefile_wires_status_drift_check` (Step 5) |
| AC5: if wired as a blocking gate, forward-only-enforcement exemption explicitly answered | Step 3 (answered: not applicable — no blocking gate added) | Manual read of `## Implementation Notes` (Step 3 Verify) |
| AC6: scoped pytest run passes (`tests/tools/test_status_drift_check.py` plus any new wiring tests) | Step 5 | Commands listed in Step 5 Verify |

## Deviations

Implementation followed all 5 steps as written, with two small factual corrections surfaced during
Implement (neither changes scope, architecture, or the fix mechanism):

- **Step 5's "16 existing tests" count was off by one.** The live `tests/tools/test_status_drift_check.py`
  at Implement time had 17 pre-existing tests, not 16 (`test_bare_scoped_no_longer_exempt_after_tightening`,
  added by a later ticket, TCK-20260718-STATUS-FACET-CANONICAL, after this plan's Investigate pass
  apparently undercounted). All 17 pre-existing tests plus the 1 new `test_makefile_wires_status_drift_check`
  passed (18/18 total) — no test needed changing, only the plan's stated count was stale.
- **Step 4's INFRA-277 update, via `write_entry()`, rewrote the entire `infrastructure.yaml` shard's
  YAML formatting** (not just the INFRA-277 entry's bytes), because `write_entry()` re-serializes
  the whole shard with `yaml.safe_dump` on every write — this is the tool's existing, by-design
  behavior (confirmed by reading `tools/parity_ledger_writer.py` before use), not a defect
  introduced here. Verified via a structural (not textual) diff that only INFRA-277's data content
  changed among entries this ticket is responsible for; two other entries (INFRA-292, INFRA-315)
  and three new entries (INFRA-331/332/333) differed from the pre-session `HEAD` copy but were
  already present in the working-tree file before this ticket's `write_entry()` call — confirmed
  unrelated, from other in-progress work sharing this working tree, and preserved (not clobbered)
  by `write_entry()`'s fresh-read-before-write design.

## Anti-Drift Notes

- The ticket's own cited "real, non-cosmetic consequence" (`GanttBar.tsx`'s `classifyFinalStatus()`)
  is dead code, confirmed deleted 2026-07-30. Do not carry this citation forward uncorrected anywhere
  — not in commit messages, not in the ticket's `## Completion Summary`, not in INFRA-277 (Step 4
  corrects the ledger; the implementer must also avoid re-citing it fresh in the ticket body). The
  real, live consequence is `ingest.py`'s `workflow_status` field and `TicketsView.tsx`'s status
  filter — a drifted body `## Status` means the Tickets dashboard tab shows the wrong status text and
  a user filtering by `status=DONE` silently misses a genuinely-completed ticket.
- The corpus moved from the ticket's cited 3 real-drift cases to 7 between ticket authorship
  (2026-08-10) and Plan (today) — this is expected corpus churn, not an investigation error. Do not
  re-run the live check and treat any further movement as license to keep expanding this ticket's
  fix list indefinitely; Step 1's fix list is fixed to the 7 confirmed in `investigation.md`'s one
  live run. If the corpus has moved again by Implement time, that is new evidence for a future
  ticket, not silent scope creep on this one — flag it in Implementation Notes rather than
  auto-including it.
- `WORKFLOW_STATUS_VALUES` (`tools/ticket_field_values.py:46-48`) is the single canonical source for
  valid `## Status` values (`OPEN`, `INPROGRESS`, `BLOCKED`, `DONE`, `EPIC_SCOPED`) — already
  re-exported and shared correctly across `ingest.py`, `status_drift_check.py`'s `EPIC_TIER_VALUES`
  subset, and `ticket_field_values.py` itself. No step in this plan duplicates or redefines this
  enum; Step 1's fix values (`DONE`) are drawn from it correctly.
- Two independent developer-experience audits already exist as precedent for exactly this kind of
  gate-wiring decision: `TCK-20260720-GATE-CHECK-WIRING-DECISIONS` (wired `doc_staleness_check.py`,
  explicitly deferred others with reasons) and `TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM` (built the
  literal option (a) precedent this ticket evaluated and did not choose). Do not treat "a precedent
  for blocking gates exists" as pressure toward always choosing the blocking-gate option — the
  evidence for this specific checker points the other way, and Step 2 documents why.
