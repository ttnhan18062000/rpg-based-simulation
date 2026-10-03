---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-GATE-DET-DONE-CHECKER
phase: done
date: 2026-07-05
tags: [ai, workflows, determinism]
---

# TCK-20260705-GATE-DET-DONE-CHECKER

## Title
Add a deterministic pre-check for done-checker's machine-verifiable DoD conditions, plus a Finalize-phase migration self-check

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/plans/agent_infrastructure/idea_agent_gate_determinism.md` (unscheduled idea, 2026-07-03) proposes
giving each LLM-judged gate a companion deterministic verifier. `done-checker` is the first of 4 gates
to receive one (see `tickets/todos/gate-determinism-followups/SEQUENCE.md` for the full 4-ticket plan
and shared design decisions). The user specifically flagged staging→stored artifact migration and
"other hard rules" as steps that have been observed to occasionally get skipped.

**Important correction to the idea doc's own framing** (see SEQUENCE.md for full detail): `done-checker`
runs during Verify, *before* Finalize — it cannot itself verify that `staging_artifacts/` was migrated
to `stored_artifacts/`, since that migration hasn't happened yet at Verify time. This ticket therefore
has two parts: (a) a `done-checker` static pre-check for the conditions that genuinely are checkable
before Finalize, and (b) a new Finalize-phase self-verification step confirming the migration it just
performed actually landed correctly.

## Scope
- **Part A — `done-checker` static pre-check** (`tools/gate_checks/done_checker_static.py`): script-
  verifiable subset of the DoD conditions, checkable *before* Finalize runs:
  - `staging_artifacts/{ticket_id}/` exists and contains all 3 required files (`plan.md`,
    `investigation.md`, `test_plan.md`), each non-empty (standard/epic tier only — N/A for hotfix).
  - `data/runs/` and `reports/release_proof/` are empty (or contain only pre-existing, unrelated
    artifacts — Investigate should determine how to distinguish "this ticket's run data" from
    "leftover from a concurrent session," referencing how prior tickets this session handled the same
    ambiguity).
  - The ticket file exists at `tickets/inprogress/{ticket_id}.md` (not yet moved).
  - `tickets/working_log.csv` does **not** yet contain a row for this ticket (Finalize adds it later —
    a pre-existing row at Verify time would indicate a duplicate/re-run issue worth flagging).
  - Frontmatter validates (`tools/validate_frontmatter.py` exit 0) for the ticket file and staging
    artifacts — already a manual done-checker step today; this makes it a scriptable pre-check instead.
  - Return `PASS`/`FAIL` per check; `done-checker`'s own LLM judgment call is instructed to run this
    script first and cite its output rather than re-deriving each check by hand.
- **Part B — Finalize migration self-check** (new step at the end of Finalize, in `implement-ticket.js`):
  immediately after Finalize's own `mv staging_artifacts/{id}/* stored_artifacts/{id}/` action, verify:
  `stored_artifacts/{ticket_id}/` exists with all 3 files, `staging_artifacts/{ticket_id}/` no longer
  exists, `tickets/done/{ticket_id}.md` exists, `tickets/inprogress/{ticket_id}.md` no longer exists,
  and a `working_log.csv` row now exists for this ticket. If any check fails, Finalize should report the
  discrepancy explicitly rather than silently returning `DONE`.
- **Part C — retrospective audit (size first, decide after)**: Investigate should count how many
  tickets in `tickets/done/*.md` today have no corresponding `stored_artifacts/{id}/` directory (or an
  incomplete one) despite being marked DONE — i.e., how many historical migration gaps actually exist.
  If the count is non-trivial, add a small audit function/script (reusing `tools/agent-monitoring/validate.py`'s
  established pattern of retrospective, non-blocking, disclose-don't-fix auditing) that reports them
  without attempting to backfill/move anything for historical tickets. If the count is zero or
  negligible, document that finding and skip building the audit tool — do not build speculative
  tooling for a problem confirmed not to exist at scale.
- Add a `verified_by` field to `done-checker`'s own return schema (`DONE_SCHEMA` in `implement-ticket.js`),
  per the shared design in SEQUENCE.md.
- Add at least one coverage-honesty test proving the static module actually catches a real violation
  (e.g., a fixture where `staging_artifacts/` is missing one of the 3 files) — not just that it runs.

## Out of Scope
- The other 3 gates' static verifiers (`architecture-reviewer`, `parity-updater`, `mechanics-auditor`) —
  separate sibling tickets, see SEQUENCE.md.
- Backfilling or moving any historical ticket's staging/stored artifacts as part of Part C's audit —
  disclose only, per this session's established append-only/disclose-don't-fix precedent for historical
  data gaps (matches `TCK-20260705-WORKING-LOG-BACKFILL`'s own resolution).
- Token/cost telemetry — explicitly a separate idea per the idea doc itself.
- Changing done-checker's actual judgment-based DoD conditions (e.g., "no material gap is left
  unstated") — those remain irreducibly LLM-judged, per the idea doc's own table.

## Acceptance Criteria
- [ ] `tools/gate_checks/done_checker_static.py` exists, exposing one function per pre-Finalize
      machine-checkable condition, each returning a clear PASS/FAIL + evidence.
- [ ] `.claude/agents/done-checker.md` and `.claude/workflows/implement-ticket.js`'s Verify-phase prompt
      instruct the agent to run this script first and cite its output.
- [ ] `DONE_SCHEMA` gains a `verified_by` field.
- [ ] Finalize gains a self-verification step confirming its own migration actually happened, reporting
      (not silently swallowing) any discrepancy.
- [ ] Part C's historical-orphan count is measured and reported in the ticket's own Implementation
      Notes, with an explicit build-or-skip decision justified by that count.
- [ ] At least one coverage-honesty test per static check function.
- [ ] `docs/ai/agents.md`'s `done-checker` section, `docs/ai/workflows.md`, `docs/ai/system_overview.md`,
      and `docs/ai/ticket-lifecycle.md` updated to describe the new static pre-check and Finalize
      self-check.

## Related Tickets
- TCK-20260705-GATE-DET-PARITY-UPDATER, TCK-20260705-GATE-DET-MECHANICS-AUDITOR,
  TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER (siblings, see SEQUENCE.md)
- TCK-20260705-WORKING-LOG-BACKFILL (established the disclose-don't-fix precedent for historical data gaps)
- TCK-20260705-WORKFLOW-SECURITY-GATE, TCK-20260705-WORKFLOW-PARITY-SKIP (established this session's
  pattern for adding new gate/check logic to `implement-ticket.js` with architecture-review scrutiny)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_gate_determinism.md (source idea)
- tickets/todos/gate-determinism-followups/SEQUENCE.md (shared design decisions)
- docs/ai/agents.md, docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md,
  docs/agent-monitoring/schema.md (all likely need updates — confirm during Investigate)

## Related Stored Artifacts
None yet — staging artifacts to be created under `staging_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/`
when implementation begins.

## Related Code Areas
- .claude/agents/done-checker.md
- .claude/workflows/implement-ticket.js (Verify phase, Finalize phase)
- tools/agent-monitoring/validate.py (reference — retrospective-audit precedent)

## Assumptions / Open Questions
- Exact mechanism for distinguishing "this ticket's run data" from "another concurrent session's" in
  `data/runs/`/`reports/release_proof/` — left for Investigate to resolve with evidence from how prior
  tickets handled this.
- Whether Part C's audit is worth building depends entirely on the measured historical-orphan count —
  explicitly not decided here.

## Implementation Notes

Implemented all 9 steps from the approved `plan.md` (2 rounds of architecture review) in dependency
order.

**Part A — `tools/gate_checks/done_checker_static.py`** (Steps 1-2): 5 pure functions
(`check_staging_artifacts_complete`, `check_data_runs_clean`, `check_ticket_location`,
`check_working_log_no_row_yet`, `check_frontmatter_valid`) each returning `(status, evidence)`, plus
`run_static_precheck(ticket_id, tier, start_ts)` aggregating all 5 into the checklist-item shape.
`check_frontmatter_valid` imports `validate_file`/`validate_directory` directly from
`tools/validate_frontmatter.py` (no subprocess) and passes `content_type_override="artifact"`
explicitly for the staging-artifacts half, per the investigation's finding #1 (staging_artifacts/
does not auto-detect as `artifact` type). `check_data_runs_clean` is mtime-relative against
`start_ts`, never a naive empty-check, and treats an unparsable/missing `start_ts` as
"flag anything found" rather than passing. `check_working_log_no_row_yet` scans every CSV column
(not `DictReader` keyed on the header) to catch the malformed-column-order rows documented in
`TCK-20260705-WORKING-LOG-BACKFILL`.

**Part B — same module** (Steps 3-4): `check_migration_complete`, `check_ticket_finalized`,
`check_working_log_exactly_one_row`, and `run_finalize_selfcheck` aggregate. `check_migration_complete`
and `check_working_log_exactly_one_row` reuse the private `_files_complete`/`_count_rows_for_ticket`
helpers shared with Part A rather than duplicating the file-presence/CSV-scan logic.

**Step 5 — Verify wiring**: `done-checker.md` gained a "Step 0" instructing the agent to run
`run_static_precheck` first and cite its output for conditions 3, 4, 7, 10, 12 (mapping table
included); `implement-ticket.js`'s Verify `agent()` prompt gained the equivalent instruction with
`${tid}`/`${tier}`/`${startTs}` substituted. Fixed the pre-existing stale "Condition 12 (agent
monitoring)" → "Condition 13 (agent monitoring)" off-by-one at the same line (confirmed by direct
read: condition 12 is frontmatter, condition 13 is agent monitoring). `DONE_SCHEMA` gained an
additive, optional `verified_by: string[]` property — `required` array unchanged
(`['verdict','failing_items','checklist','summary']`). A static `FAIL` still surfaces as a
`failing_items` entry leading to the existing `DOD_BLOCKED` status — no new status introduced here.

**Step 6 — Finalize wiring**: added a `bash()` call immediately after the (still-unassigned) Finalize
`agent()` call, running `run_finalize_selfcheck(tid, tier)` and printing its JSON prefixed with a
`FINALIZE_CHECK_JSON:` sentinel marker. The orchestrator extracts the substring after the marker and
`JSON.parse`s it inside a try/catch — never a bare `JSON.parse` on raw `bash()` output (no existing
precedent in this file guarantees that's safe; the only prior `bash()` call, `p0ScanOutput`, only
ever does a substring `.includes()` check). A missing marker or parse failure returns
`FINALIZE_INCOMPLETE` with `failing_items: ['finalize_selfcheck_unparseable']` rather than throwing
or silently falling through to `DONE`. Any parsed `FAIL` entry also returns `FINALIZE_INCOMPLETE`
with the specific failing conditions. `FINALIZE_INCOMPLETE` is the **one new status** this ticket
introduces. Confirmed (no code change): `implement-epic.js`'s batch loop (`result.status !== 'DONE'`)
already treats it as a batch-stopping status identically to `DOD_BLOCKED`.

**Step 7**: no separate change — `verified_by` is agent-self-reported, added in Step 5.

**Step 8 — Part C audit** (`tools/gate_checks/done_checker_audit.py`): `scan_done_tickets` walks
`tickets/done/*.md` and `tickets/done/*/*.md` (excluding README.md/SEQUENCE.md), extracting `## Tier`
via `parse_body_section` reused directly from `tools/generate_registry.py` (no new markdown-parsing
dependency). `audit_stored_artifacts_migration` classifies each standard/epic ticket as
ok/missing/incomplete (reusing `_files_complete` from `done_checker_static.py`), skips hotfix tickets
silently (not a gap), and skips/warns on any ticket with no parseable `## Tier` field — never
classifying, inferring, or investigating those 91 legacy tickets, per the explicit permanent scope
guard. Read-only throughout; `main()` always exits 0. Ran live against the current repo: 525 ok, 235
missing, 102 incomplete, 73 hotfix-skipped, 91 legacy-skipped — consistent with the investigation's
measured 39.2% historical gap (small count deltas vs. the investigation's 237/101 explained by
tickets finalized in the interim).

**Step 9 — docs**: updated `docs/ai/agents.md` (done-checker section: 13 conditions, Step 0 static
pre-check description), `docs/ai/workflows.md` (Verify/Finalize phase table rows +
`FINALIZE_INCOMPLETE` in the return-values table), `docs/ai/system_overview.md` (added a sentence
describing the static pre-check and Finalize self-check — see Deviations below re: the "12
substantive conditions" count), `docs/ai/ticket-lifecycle.md` (13-condition Verify table with
script-checked annotations, Finalize step list + self-verification step, `FINALIZE_INCOMPLETE` added
to both the ASCII pipeline diagram and the Failure Recovery Reference table, and the same stale
"DoD condition 12"→"13" agent-monitoring fix as Step 5). Ran `make knowledge-index-update` after docs
changes (5 files re-embedded). Ran `graphify update .` after `tools/`/`tests/` changes (24001 nodes,
50756 edges).

**Deviations**: see `staging_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/plan.md`'s new "Deviations"
section — `docs/ai/system_overview.md:106`'s "12 substantive... conditions" text was already accurate
at implement time (no fix needed, contrary to the plan's premise); two *other* stale 11/12-vs-13
references were found and fixed opportunistically in `docs/ai/agents.md` and
`docs/ai/ticket-lifecycle.md` since they live in the same done-checker/Verify/Finalize sections Step 9
already required touching.

## Test Summary

`pytest tests/tools/test_done_checker_static.py tests/tools/test_done_checker_audit.py -v` — 37/37
passed (31 in the former, 6 in the latter). Every check function has at least one FAIL-triggering
fixture (coverage-honesty requirement), including the malformed-CSV-column-order regression guard and
the `content_type_override="artifact"` regression guard. Ran the full `pytest tests/tools/ -q`
regression suite: 476 passed, 30 pre-existing failures in `test_knowledge_search.py` /
`test_search_mcp.py` (embedding-index and `.mcp.json`-config tests, both entirely unrelated to this
ticket's files — not introduced by this change). Steps 5/6 (`.claude/` prompt text and
`implement-ticket.js` control flow) are verified by manual code inspection only, per
`test_plan.md`'s explicit note that no JS test harness exists in this repo — confirmed
`node --check .claude/workflows/implement-ticket.js` passes with no syntax errors after both edits.

## Files Changed

- `tools/gate_checks/__init__.py` (new)
- `tools/gate_checks/done_checker_static.py` (new)
- `tools/gate_checks/done_checker_audit.py` (new)
- `tests/tools/test_done_checker_static.py` (new)
- `tests/tools/test_done_checker_audit.py` (new)
- `.claude/agents/done-checker.md` (Step 0 static pre-check instruction, verified_by output field, numbering fix)
- `.claude/workflows/implement-ticket.js` (DONE_SCHEMA.verified_by, Verify prompt script instruction + numbering fix, Finalize self-check + FINALIZE_INCOMPLETE)
- `docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`

## Completion Summary

Built `tools/gate_checks/done_checker_static.py` (Part A: 5 pre-Finalize static checks; Part B: 3
post-Finalize migration self-checks) and `tools/gate_checks/done_checker_audit.py` (Part C:
read-only historical audit — 39.2%-class gap confirmed still present: 235 missing + 102 incomplete
out of 862 standard/epic done tickets as of this session). Wired Part A into `done-checker.md` and
the Verify-phase prompt (existing `DOD_BLOCKED` vocabulary reused, no new status), added optional
`verified_by` to `DONE_SCHEMA`, and wired Part B into Finalize via a sentinel-marker/try-catch `bash()`
call that introduces the one new terminal status `FINALIZE_INCOMPLETE`. Fixed two instances of a
pre-existing "condition 12 vs. 13" numbering bug for agent monitoring (in `implement-ticket.js` and
`docs/ai/ticket-lifecycle.md`) discovered during this same edit. All new tests pass (37/37); full
`tests/tools/` regression suite shows no new failures (30 pre-existing, unrelated failures in
knowledge-search/MCP-config tests). No `src/` files touched — `behavior_changed=false`, no parity
ledger subsystem affected.
