---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK
artifact_type: test_plan
tags: [ai, agent-monitoring, determinism]
---

# Test Plan — TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK

## Regression Surface

No existing test file imports anything from a `workflow_meta_conformance` module (confirmed: no such
file exists yet under `tools/gate_checks/` or `tests/tools/`). The regression surface is therefore
everything this new module sits next to and must not disturb:

**Unit — `tools/gate_checks/` siblings (must keep passing unchanged; new module must not modify any
of these files or their shared imports):**
- `tests/tools/test_parity_updater_static.py` — exercises `derive_mapping`,
  `expected_subsystems_for_files`, `cross_reference_touched` (the structural precedent this ticket
  mirrors; must remain untouched).
- `tests/tools/test_done_checker_static.py` — exercises `run_finalize_selfcheck`,
  `check_monitoring_write_recorded`, `classify_checklist_failure`, `_jsonl_rows_for_run_id` (the
  JSONL-by-run_id helper this ticket's module should reuse or mirror, not reimplement).
- `tests/tools/test_done_checker_audit.py`

**Unit — agent-monitoring vocabulary/validation (must keep passing; new module should *import*
`vocabulary.py`, never fork its own copy of `WORKFLOW_PHASES`/`infer_workflow`):**
- `tests/tools/test_validate_agent_monitoring.py` — includes
  `test_canonical_vocabulary_single_sourced`, which is the existing guard against exactly the kind of
  duplication this ticket must avoid (see investigation.md Anti-Drift Hazards).

**Integration — none.** This is a pure static-analysis tool with no simulation-state or engine
surface; there is no `tests/integration/` or `tests/arena-combat/`-style regression path affected.

## New Tests Required

New file: `tests/tools/test_workflow_meta_conformance.py`, mirroring
`test_parity_updater_static.py`'s coverage-honesty convention (every check function has ≥1 fixture
proving it catches a real violation it claims to catch, not just a happy-path run) and its
`_write_ledger`-style small-fixture-helper pattern (here: a `_write_workflow_js(tmp_path, meta_block)`
/ `_write_events_jsonl(tmp_path, run_id, phases)` helper pair instead).

Per (provisional) AC:

1. **`test_parses_meta_phases_from_implement_ticket_js`**
   - Category: unit
   - Verifies: the regex/AST-lite parser, run against the *real*
     `.claude/workflows/implement-ticket.js` file (not a fixture copy), extracts exactly the 11
     `title` values in declared order: Scope, Investigate, Plan, Review, Implement,
     Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize. Directly satisfies AC #1.
     Reading the real file (not a copy) means this test also doubles as a staleness guard — if
     `implement-ticket.js`'s `meta.phases` block is ever reshaped in a way the parser can't handle,
     this test fails immediately rather than silently.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

2. **`test_parses_meta_phases_from_create_tickets_js`** and
   **`test_parses_meta_phases_from_implement_epic_js`**
   - Category: unit
   - Verifies: the same parser generalizes correctly to the other 2 in-scope workflow files (5 and 3
     entries respectively) — guards against a parser that only works because it was written against
     one file's exact formatting.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

3. **`test_flags_declared_phase_with_zero_events`** (the core cross-reference — the
   coverage-honesty-required "catches a real violation" fixture)
   - Category: unit
   - Verifies: given a synthetic `events.jsonl` fixture (via `tmp_path`) for a run_id whose events
     cover only a strict subset of a workflow's declared phases (e.g. a 3-phase fixture workflow
     missing one), the aggregate check function returns that phase with a `FAIL`-equivalent status
     and non-empty evidence. Directly satisfies AC #2 ("cross-reference correctly flags a synthetic
     run missing an event for a declared phase").
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

4. **`test_does_not_flag_a_phase_with_only_skipped_status_events`**
   - Category: unit (anti-false-positive guard)
   - Verifies: a phase with events present but all `status == 'skipped'` (e.g. hotfix-tier
     Investigate/Plan/Review) is NOT flagged — only phases with literally zero matching events of any
     status are flagged. This is the investigation's Risk #2 finding encoded as a test — without it,
     a naive implementation would false-positive on every hotfix-tier run.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

5. **`test_does_not_flag_security_review_absent_when_ticket_untagged_security`**
   (or equivalently, a generic **`test_does_not_flag_a_phase_with_zero_events_when_conditional`** if
   the option-(a) allowlist design is chosen instead of option-(b) in Plan)
   - Category: unit (anti-false-positive guard, real fixture not synthetic)
   - Verifies: replaying the real `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` event shape (10 of 11
     `implement-ticket` phases present, `Security-Review` genuinely absent, ticket not
     `security`-tagged) produces zero findings, not one. This is a real historical run, not an
     invented fixture — directly answers investigation Risk #2's "100% false-positive rate on
     Security-Review" hazard.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

6. **`test_unknown_run_id_returns_empty_or_na_not_a_crash`**
   - Category: unit (failure mode)
   - Verifies: a `run_id` with zero rows in `events.jsonl` (e.g. a typo, or a run that crashed before
     `writeMonitoring` ever ran) does not raise — returns an explicit "no events found for this
     run_id" result the caller can distinguish from "all phases present." Mirrors
     `check_monitoring_write_recorded`'s explicit `("FAIL", "No row with run_id == ...")` shape for
     the same failure mode.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

7. **`test_unresolvable_workflow_source_file_does_not_crash`**
   - Category: unit (failure mode)
   - Verifies: if `.claude/workflows/{workflow_name}.js` doesn't exist for a given/inferred workflow
     name (e.g. `infer_workflow` returns `None`, or a future 5th workflow), the checker returns a
     clearly-labeled non-crashing result — never raises, per every other `gate_checks` module's
     "must never crash the calling workflow" convention.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

8. **`test_reuses_vocabulary_infer_workflow_not_a_reimplementation`** (architecture guard)
   - Category: architecture guard
   - Verifies: the new module imports `infer_workflow` (or `WORKFLOW_PHASES`) from
     `tools/agent-monitoring/vocabulary.py` rather than defining its own `run_id` → workflow-name
     mapping or its own copy of the phase-name sets. Concretely: assert the module's source contains
     `from vocabulary import` (or equivalent `sys.path`-qualified import), and/or assert
     `workflow_meta_conformance`'s own module namespace does not define a second dict shaped like
     `WORKFLOW_PHASES`. Directly enforces investigation Anti-Drift Hazard #6 and mirrors
     `test_canonical_vocabulary_single_sourced`'s intent for this new call site.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

9. **(If Plan decides on advisory wiring into `implement-ticket.js`, per the open question)
   `test_finalize_phase_writes_advisory_warning_never_blocks_status`**
   - Category: architecture guard (JS-side; no `*.test.js` harness exists per the idea doc's own C2
     finding — this can only be verified by a Python-side fixture exercising the same
     `MARKER:`-prefix parsing contract `implement-ticket.js` will consume, mirroring how
     `check_monitoring_write_recorded`'s output-shape is unit-tested from the Python side today, not
     by any JS test.)
   - Verifies: the Python function's return shape is exactly what a `MARKER:`-prefix +
     `JSON.parse`-in-JS caller expects (a JSON-serializable list of dicts, never a bare string,
     never an exception), so wiring it into `implement-ticket.js` cannot silently corrupt the
     established `indexOf` + `try/catch` convention.
   - Lives in: `tests/tools/test_workflow_meta_conformance.py`

## Scoped Pytest Commands

```bash
# New module's own tests
pytest tests/tools/test_workflow_meta_conformance.py -v

# Full regression surface (siblings + vocabulary single-source guard)
pytest tests/tools/test_workflow_meta_conformance.py \
       tests/tools/test_parity_updater_static.py \
       tests/tools/test_done_checker_static.py \
       tests/tools/test_done_checker_audit.py \
       tests/tools/test_validate_agent_monitoring.py -v
```

Never `pytest tests/` — scope stays inside `tests/tools/` (this ticket touches nothing under
`src/`, so no `tests/unit/`, `tests/integration/`, or `tests/architecture/` domain is implicated).

## Anti-Drift Test Guards

- **Test #4 and #5 above are the primary anti-drift guards** — they exist specifically to prevent
  the naive implementation (flag any declared phase with zero events, full stop) from shipping,
  which would immediately false-positive on every hotfix-tier run (missing-event-status distinction)
  and every non-security-tagged ticket (conditional-phase distinction) — i.e. the overwhelming
  majority of real runs. A future change to this module that silently drops either guard should fail
  these two tests immediately.
- **Test #8 is a structural anti-drift guard**, not a behavioral one: it exists to catch a future
  edit that "helpfully" inlines a copy of `WORKFLOW_PHASES` or the `run_id`-prefix-to-workflow-name
  mapping directly into `workflow_meta_conformance.py` instead of importing `vocabulary.py` — the
  same class of drift `test_canonical_vocabulary_single_sourced` already guards against for
  `record_events.py`/`validate.py`.
- **Test #1's use of the real, live `implement-ticket.js` file (not a fixture copy)** is itself an
  anti-drift guard against the parser silently becoming stale relative to the workflow file it's
  meant to check — if a future ticket reshapes `meta.phases`'s literal syntax in a way the
  regex/AST-lite parser can't follow, this test fails at parse time rather than the checker silently
  returning an empty/wrong phase list and reporting false negatives forever after.
- **If Plan chooses NOT to wire this into `implement-ticket.js` in this ticket** (i.e. ships the
  verifier as a standalone, manually-invoked tool only), test #9 should be dropped from this list
  entirely rather than left as a stale placeholder — do not let an unwired-but-tested integration
  path linger and mislead a future reader into thinking the gate is live when it is not.
- **Any test asserting on `implement-epic.js`'s Discover/Report phases must not silently start
  "fixing" that workflow's `pushEvent` gap as a side effect of testing the parser against it** — per
  investigation Risk #3, that gap's remediation (if any) is an explicit Plan-time scoping decision,
  not something a test should incidentally force by asserting a clean cross-reference result against
  the real `implement-epic.js` events shape.
