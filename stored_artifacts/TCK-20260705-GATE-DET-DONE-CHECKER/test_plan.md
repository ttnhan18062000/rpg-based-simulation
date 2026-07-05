---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-DONE-CHECKER
artifact_type: test_plan
tags: [ai, workflows, determinism]
---

# Test Plan — TCK-20260705-GATE-DET-DONE-CHECKER

## Regression Surface

- `tools/gate_checks/` is a brand-new subpackage — no existing tests reference it, so there is no direct
  regression risk to existing `tools/` tests from adding it. New tests are purely additive.
- `.claude/agents/done-checker.md` prompt text changes (instructing it to run the new script first) are not
  unit-testable in the traditional sense (it's a markdown prompt, not code) — verify by re-reading the
  rendered file for the new instruction, and by exercising a live `implement-ticket` run in Investigate/Plan
  phase discussion (not required for this ticket — prompt-text changes are validated by the existing
  `done-checker` agent behavior in the next real workflow run, per this repo's established pattern for
  agent-prompt-only changes).
- `DONE_SCHEMA` in `implement-ticket.js` gains a new optional-vs-required `verified_by` field — this is a
  JSON-schema literal object in a `.js` workflow file, not directly unit-testable by `pytest`; there is no
  existing JS test harness for `implement-ticket.js`'s phase schemas in this repo (confirmed — no
  `tests/**/*implement_ticket*` or `.claude/workflows/*.test.js` files found). Verification for this piece
  is manual/structural: confirm the schema object's `required` array and `properties` still parse as valid
  JS/JSON-schema-shaped object (no syntax regression) and that no *existing* required field was
  accidentally removed.
- `tools/agent-monitoring/validate.py` is untouched by this ticket (Part C's own script is new/separate,
  per the ticket's explicit "reusing... pattern" language, not a modification) — its own existing test
  coverage (if any) should be re-run only to confirm this ticket didn't touch it. Search found no dedicated
  `tests/` file for `validate.py` itself — treat as "no existing regression suite to protect," not a gap to
  fix under this ticket.

## New Tests Required

Target location: `tests/tools/gate_checks/test_done_checker_static.py` (mirrors this repo's existing
`tests/tools/test_search_mcp.py`-style placement for `tools/` unit tests — confirm exact sibling directory
name at Implement time by checking `ls tests/tools/`).

1. **`check_staging_artifacts_complete` — positive control (coverage-honesty requirement)**
   - Fixture: a temp `staging_artifacts/{fake_id}/` with only `plan.md` and `investigation.md` (missing
     `test_plan.md`). Assert the function returns FAIL, citing `test_plan.md` by name as missing —
     not just "it ran."
   - Fixture: all 3 files present but one is empty (0 bytes / whitespace-only). Assert FAIL — "non-empty"
     is an explicit condition in the ticket AC, not just "exists."
   - Fixture: all 3 present and non-empty. Assert PASS.
   - Tier=`hotfix` case: assert the function reports N/A regardless of directory state (mirrors
     `done-checker.md` condition 4's tier rule) — do not silently PASS a hotfix ticket with a missing
     directory; N/A must be a distinguishable third outcome, not folded into PASS.

2. **`check_data_runs_clean` (mtime-based, per investigation's resolution of the open question)**
   - Fixture: empty `data/runs/`, empty `reports/release_proof/` → PASS.
   - Fixture: a file in `data/runs/` with mtime set (via `os.utime`) to *before* the supplied `start_ts` →
     PASS (treated as pre-existing/concurrent-session data, not this ticket's).
   - Fixture: a file with mtime *at or after* `start_ts` → FAIL, citing the specific file path.
   - This is the one check most likely to be implemented wrong (naive "just check empty" instead of the
     mtime-relative rule established in `implement-ticket.js:786`) — a dedicated test locking in the
     mtime comparison is the coverage-honesty control for this specific check.

3. **`check_ticket_location` (ticket file exists at `tickets/inprogress/{id}.md`, not yet moved)**
   - Fixture: ticket present in `tickets/inprogress/` → PASS.
   - Fixture: ticket absent from `tickets/inprogress/` (already moved, or never created) → FAIL.

4. **`check_working_log_no_row_yet`**
   - Fixture: a temp CSV without a row for the target ticket_id → PASS.
   - Fixture: a temp CSV with an existing row for the target ticket_id → FAIL, explicitly flagged (per the
     ticket's own wording) as "a pre-existing row at Verify time would indicate a duplicate/re-run issue
     worth flagging" — assert the evidence string names this as the concern, not a generic "found row."
   - Regression guard against the malformed-column-order bug documented in
     `stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/investigation.md` (Reason A: some historical rows
     have `ticket_id` in column 1 instead of column 2) — add a fixture row in that malformed shape and
     assert the check does NOT silently misparse it as "no row exists" when a row actually does exist under
     a different column arrangement. This directly matters here: a false PASS caused by the same
     `DictReader`-column-order bug would let done-checker wrongly clear a ticket that actually already has a
     working_log entry.

5. **`check_frontmatter_valid` (wraps `validate_frontmatter.py`)**
   - Fixture: valid ticket frontmatter + valid staging_artifacts frontmatter → PASS.
   - Fixture: staging_artifacts file with frontmatter missing a required `artifact` field (e.g. no
     `artifact_type`) → FAIL. This test also locks in the investigation's finding that `--content-type
     artifact` (or the equivalent `content_type_override` kwarg) must be passed explicitly for
     `staging_artifacts/` paths — write the test so it would fail (false PASS) if the implementation forgets
     this override, i.e. include a file whose frontmatter would satisfy `doc`'s validator but NOT
     `artifact`'s validator (e.g. missing `ticket_id` or `artifact_type`, both required by `_validate_artifact`
     but not by `_validate_doc`), proving the check is really using the `artifact` schema, not falling
     through to `doc`.

6. **Aggregate function (whatever wraps 1–5 into the single script the done-checker prompt is told to run
   and cite)**
   - Fixture combining one PASS-eligible ticket and asserting the aggregate reports all N/A-vs-PASS
     correctly per tier.
   - Fixture with at least one FAIL among the 5 checks — assert the aggregate's overall result surfaces
     that FAIL and does not get masked by the other PASSing checks (i.e., aggregate is not just "all
     truthy" but preserves per-check detail).

7. **Finalize migration self-check (Part B) — if implemented as a Python function alongside Part A's
   module** (`tools/gate_checks/done_checker_static.py` or a clearly-named sibling — Plan phase to decide
   exact placement):
   - Fixture: `stored_artifacts/{id}/` with all 3 files, `staging_artifacts/{id}/` absent,
     `tickets/done/{id}.md` present, `tickets/inprogress/{id}.md` absent, working_log has exactly 1 row →
     all-PASS.
   - Fixture: `stored_artifacts/{id}/` missing `plan.md` → FAIL naming the specific missing file (this is
     the fixture class directly modeled on the 101 real "incomplete" cases found in Part C's audit).
   - Fixture: `staging_artifacts/{id}/` still present alongside a complete `stored_artifacts/{id}/` → FAIL
     ("migration ran but source not cleaned") — a case not observed in the current 0/862 measured stale-
     staging count, but must still be tested since it's a distinct, plausible failure mode the check is
     specified to catch.
   - Fixture: working_log has 0 rows for the ticket → FAIL ("not zero, not more than one" — zero case).
   - Fixture: working_log has 2+ rows for the ticket (duplicate Finalize run) → FAIL (the "more than one"
     case) — this exercises the other half of the AC's explicit "(not zero, not more than one)" wording;
     without this fixture the natural implementation temptation (`if not any(...)`) would silently accept
     duplicates.

8. **`implement-ticket.js` Finalize-phase status change (JS-level, no Python test possible)** — since there
   is no JS test harness in this repo for workflow files, verify this piece by code inspection at Implement
   time: confirm the new post-Finalize `bash(...)` call's failure path returns a distinct status (e.g.
   `FINALIZE_INCOMPLETE`) rather than falling through to the unconditional `return { status: 'DONE', ... }`
   at line 797 (current numbering) — and confirm `implement-epic.js`'s batch loop (`result.status !==
   'DONE'` at its current line ~203) would correctly treat that new status as a batch-stopping failure
   without any change needed on the `implement-epic.js` side (it already treats *any* non-`'DONE'` status
   as a stop condition — this is existing behavior, not new coverage this ticket adds, but should be noted
   as confirmed-compatible in Implementation Notes).

## Scoped Pytest Commands

```
pytest tests/tools/gate_checks/ -v
pytest tests/tools/gate_checks/test_done_checker_static.py -v
```

Do not run the full suite. If a shared `tests/tools/` conftest or fixture directory already exists, reuse
it rather than duplicating fixture-creation boilerplate (check `ls tests/tools/` and any `conftest.py`
there before writing new fixture helpers).

## Anti-Drift Test Guards

- Every new check function must have at least one test proving it **catches a real violation** it claims
  to catch (coverage-honesty requirement from `SEQUENCE.md` decision 4) — a test that only exercises the
  all-PASS happy path is not sufficient for any of the 5 (Part A) + 5 (Part B) checks above; each needs at
  least one FAIL-triggering fixture.
- Do not let the `check_data_runs_clean` test suite degrade into "assert directory is empty" only — the
  mtime-relative behavior (the actual resolved design per this investigation) needs its own explicit
  before/after-`start_ts` fixture pair, or a future refactor could silently regress to the simpler (and
  wrong, per established Finalize-step-6 precedent) "must be fully empty" rule.
- Do not test `check_working_log_no_row_yet` only against well-formed CSV rows — the malformed-column-order
  fixture (item 4 above) is mandatory given the confirmed historical bug class in
  `TCK-20260705-WORKING-LOG-BACKFILL`'s own investigation; skipping it would leave a known-real parsing
  hazard uncovered in a brand-new check built specifically to read this same file.
- Do not assert `verified_by`/schema changes to `DONE_SCHEMA` via a Python test — there is no JS test
  runner in this repo for `.claude/workflows/*.js`; verification there is manual code inspection, not
  automated coverage. Do not fabricate a Python test that imports or `exec`s the `.js` file to satisfy a
  coverage checkbox — that would be testing something other than what actually runs.
