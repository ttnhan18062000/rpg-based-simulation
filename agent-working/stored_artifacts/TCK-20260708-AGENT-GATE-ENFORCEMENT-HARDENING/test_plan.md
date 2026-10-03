---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING
artifact_type: test_plan
tags: [hooks, determinism, process-improvement]
---

# Test Plan — TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING

## Regression Surface

No JS test harness exists in this repo (`package.json` has no test runner; confirmed by prior gate-determinism tickets' own investigation.md files) — `.claude/workflows/implement-ticket.js` changes are verified by manual/structural review only, consistent with how `GATE-DET-DONE-CHECKER` and `GATE-DET-PARITY-UPDATER` verified their own equivalent JS edits. The Python-side regression surface is `tests/tools/`:

**Unit (must keep passing unmodified):**
- `tests/tools/test_done_checker_static.py` — 38 tests covering Part A (`run_static_precheck`) and Part B (`run_finalize_selfcheck`) of the done-checker gate. This ticket adds a new check function to this same module (agent-monitoring-write verification) — every existing test in this file must still pass untouched; do not edit any existing test.
- `tests/tools/test_parity_updater_static.py` — 10 tests covering `derive_mapping`, `expected_subsystems_for_files`, `cross_reference_touched`. This ticket does not modify `parity_updater_static.py` itself (only how `implement-ticket.js` *acts on* its existing return value) — all 10 must keep passing unmodified, and no new test is needed in this file.
- `tests/tools/test_mechanics_auditor_static.py`, `tests/tools/test_architecture_reviewer_static.py` — unrelated to this ticket's scope; must keep passing (regression-only, confirms no cross-module import breakage from the done_checker_static.py edit).
- `tests/tools/test_done_checker_audit.py` — Part C retrospective audit tool; unrelated but shares `tools/gate_checks/` import surface — must keep passing.
- `tests/tools/test_record_run.py`, `tests/tools/test_record_events.py`, `tests/tools/test_validate_agent_monitoring.py` — the agent-monitoring schema/write-path tests. The new monitoring-write-verification check reads `agent-monitoring/runs.jsonl`/`events.jsonl` structure; these tests confirm that structure/schema is stable underneath the new check and must keep passing unmodified.
- `tests/tools/test_parity_ledger_scan.py` — `CANONICAL_LEDGER_FILES` source of truth; must keep passing (imported transitively via `parity_updater_static`).

**Integration / orchestration (manual-review only, no automated harness):**
- Manual re-read of the edited `implement-ticket.js` Parity phase (currently lines ~771-855) and Finalize phase (currently lines ~996-1110) after the change, confirming bracket/quote balance and that the skip-eligible Parity branch (`paritySkipEligible && !parityForceFullRun`, ~line 771) is untouched.

**Arena-combat:** none — this ticket touches no simulation/combat code; no arena-combat regression surface applies.

## New Tests Required

Per Acceptance Criteria:

1. **AC: "A ticket finalize step with no matching agent-monitoring write is hard-blocked, not just nudged"**
   - Test name: `test_check_monitoring_write_recorded_fails_when_run_missing`
   - Category: unit
   - Verifies: new check function (e.g. `check_monitoring_write_recorded(ticket_id, runs_path, events_path)` in `done_checker_static.py`) returns `("FAIL", ...)` when `agent-monitoring/runs.jsonl` has no row with `run_id == ticket_id`.
   - Location: `tests/tools/test_done_checker_static.py`

   - Test name: `test_check_monitoring_write_recorded_fails_when_events_missing`
   - Category: unit
   - Verifies: returns `("FAIL", ...)` when a matching `runs.jsonl` row exists but `events.jsonl` has zero rows with that `run_id` (positive control for the "run recorded but no events" sub-case, distinct from "nothing recorded at all").
   - Location: `tests/tools/test_done_checker_static.py`

   - Test name: `test_check_monitoring_write_recorded_passes_when_both_present`
   - Category: unit
   - Verifies: returns `("PASS", ...)` when both a `runs.jsonl` row and at least one `events.jsonl` row exist for `run_id == ticket_id` — false-positive guard (AC: "confirm no false-positive block on a normal compliant run").
   - Location: `tests/tools/test_done_checker_static.py`

   - **Superseded during Plan/Review**: item originally called for `check_monitoring_write_recorded` to be wired into `run_finalize_selfcheck`'s aggregator so `implement-ticket.js` would treat it as a `FINALIZE_INCOMPLETE` hard block. Plan's Design Decision 2 explicitly rejected this (`run_finalize_selfcheck` runs *before* `writeMonitoring` for the current attempt — a check there would always FAIL). Architecture-review then further required case (a) to be non-blocking entirely (an undisclosed CLAUDE.md Hard Rule reversal), so there is no aggregator-level or hard-block behavior to test here at all: `check_monitoring_write_recorded` is called directly via a separate `bash()` invocation in Finalize's DONE path (after `writeMonitoring('DONE')`), and a `FAIL` only produces a `pushEvent(..., 'failed', ...)` + a `WARNING` in the return `message` — `status` stays `'DONE'` unconditionally. This is verified by manual/structural review of the JS (see Regression Surface below and Architecture-Verify's confirmation), not by a Python-level aggregator test. No replacement unit test is needed for this specific item.

2. **AC: "A commit touching a parity-ledger-mapped src/ path with no matching ledger touch is hard-blocked, not just nudged"**
   - No new unit test needed in `parity_updater_static.py`/`test_parity_updater_static.py` — `cross_reference_touched`'s `FAIL` semantics are already fully tested (`test_flags_untouched_mapped_subsystem`, `test_does_not_flag_when_mapped_subsystem_touched`, `test_any_of_candidate_subsystems_touched_clears_flag`). What's missing is *`implement-ticket.js` acting on the existing `FAIL` result* — untestable by pytest (no JS harness). Verification here is **manual/structural review only**: re-read the edited Parity phase and confirm the new hard-block branch (a) triggers only when `parityCrossRefFailures.length > 0` inside the full-call (`else`) branch, (b) does not fire inside the skip-eligible branch, (c) uses the vocabulary Plan decided on for AC #3, (d) does not regress the ANY-of-candidates semantics (still calling the existing `cross_reference_touched`, not a re-derived check).
   - If Plan introduces any *new* Python-side helper (e.g., a thin wrapper to classify `parityCrossRefFailures` into a reason code, mirroring `classify_checklist_failure`), it needs its own unit test in `tests/tools/test_parity_updater_static.py` or `test_done_checker_static.py` depending on placement — decide placement in Plan, not here.

3. **AC: "Both new hard blocks use the existing failure-status vocabulary (no new status string introduced) unless Investigate finds concrete evidence that's wrong"**
   - This investigation *did* find evidence the "no new status" default may not cleanly apply to case (b) (Parity has no verdict enum today) — see investigation.md Risk #1. No automated test can verify a documentation/design decision; this AC is satisfied by Plan's explicit written decision plus the manual-review checklist above confirming the implementation matches it.

4. **AC: "docs/ai/workflows.md or a new doc explicitly states lane-architecture's coverage boundary against the 4 gate-checker modules"**
   - No automated test — prose-only doc content, consistent with every other doc-update step in the 4 prior gate-determinism tickets (all verified by manual review, no doc-content test harness in this repo).
   - Anti-drift guard (see below): a lightweight architecture-guard-style test *could* assert none of `tests/tools/test_*_static.py` carry `@pytest.mark.architecture` (keeping the "two disjoint domains" fact mechanically enforced rather than only documented) — optional, include only if Plan sizes it as trivial; not required by the AC's literal text (which asks for documentation, not a new guard).

5. **AC: "idea_agent_gate_determinism.md and agent_infrastructure_audit.md both reflect current reality"**
   - No automated test — doc-content only.

6. **AC: "Tests cover: both new hard-block trigger conditions (positive control) and confirm no false-positive block on a normal compliant run"**
   - Covered by items 1's four new tests (positive control: `..._fails_when_run_missing`, `..._fails_when_events_missing`; false-positive guard: `..._passes_when_both_present`) plus the existing, already-passing `cross_reference_touched` test suite for case (b) (`test_does_not_flag_when_mapped_subsystem_touched`, `test_any_of_candidate_subsystems_touched_clears_flag` already cover the false-positive angle for case (b); no new Python test needed there, only the JS-side manual-review confirmation that a `PASS`/`NA`-only result does *not* trigger the new hard block).

## Scoped Pytest Commands

```
pytest tests/tools/test_done_checker_static.py -v
pytest tests/tools/test_parity_updater_static.py -v
pytest tests/tools/ -v
```

Never `pytest tests/`. `tests/tools/` is the complete regression surface for this ticket's Python-side changes (agent-workflow tooling, not simulation code) — no `src/`-domain test lane (`lane-architecture`, `lane-catalog`, etc.) is affected, since this ticket touches no `src/` file.

## Anti-Drift Test Guards

- **`test_any_of_candidate_subsystems_touched_clears_flag`** (existing, `test_parity_updater_static.py`) — must keep passing untouched. If case (b)'s new hard block is wired up carelessly (e.g., re-deriving its own stricter ALL-of-candidates check instead of reusing `cross_reference_touched`'s existing ANY-of-candidates result), this is the test that would have caught the semantic regression had it been touched — confirm it is not modified.
- **`test_run_finalize_selfcheck_all_pass` / `test_run_finalize_selfcheck_surfaces_incomplete_stored_artifacts`** (existing, `test_done_checker_static.py`) — must keep passing untouched and continue asserting exactly 3 conditions. `check_monitoring_write_recorded` is deliberately NOT added to `run_finalize_selfcheck`'s aggregator (Design Decision 2) — it is called separately, directly in `implement-ticket.js`'s Finalize DONE path. A future edit that adds it as a 4th aggregator condition would reintroduce the always-FAILs-before-any-write ordering bug Design Decision 2 identified; these two tests staying at "3 conditions" is the correct, permanent state, not a gap.
- **New test guarding against the "hotfix tier" gap** (Risk #5 in investigation.md): a test confirming the new monitoring-write check's behavior under `tier == "hotfix"` is a deliberate decision (either it applies identically, since CLAUDE.md's Hard Rule says monitoring is mandatory "including hotfix," or it's explicitly exempted with a stated reason) — do not let this be an untested implicit fallthrough the way `check_migration_complete`'s hotfix branch was explicitly tested (`test_migration_complete_hotfix_is_na`).
- **A test (or explicit manual-review checklist item) confirming the Parity skip-eligible branch is untouched** — no automated JS test exists, but the manual-review step must explicitly re-confirm `paritySkipEligible && !parityForceFullRun` still short-circuits before any new hard-block code, so a ticket with zero `src/` changes and `behavior_changed: false` never spuriously hard-blocks on Parity.
- **A test confirming `implement-epic.js`'s batch-stop condition (`result.status !== 'DONE'`) still catches whatever status string(s) this ticket introduces or reuses** — per investigation.md Risk #4, this should be explicitly re-confirmed (by reading `implement-epic.js`'s condition, which is string-string-agnostic) rather than silently inherited from the prior ticket's confirmation of a different status string.
