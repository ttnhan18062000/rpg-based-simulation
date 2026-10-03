# TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW — Test Plan

**Date:** 2026-07-04
**Ticket:** TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW

---

## Regression Surface (existing tests that must keep passing)

| Test | Why it's in scope |
|---|---|
| `tests/simulation_quality/test_grade_regression.py` (fast tier, `-m "not slow"`) | The new `make simq-full-audit` target invokes this directly — must still pass unmodified against current `grade_anchors.json` |
| `tests/simulation_quality/test_grade_regression.py` (full, slow tier included) | Invoked by `make simq-full-audit-slow` — confirms the slow-tier keys are untouched by this ticket's changes |
| `tests/unit/agent-monitoring/*` (if present) or manual inspection of `agent-monitoring/tools.jsonl`/`runs.jsonl` schema | `simq-audit.js`'s `writeMonitoring` reuses `record_run.py`/`record_events.py` with a new `workflow: "simq-audit"` value — must confirm these scripts accept an arbitrary workflow string without schema rejection |
| Any existing test that imports `tools.evaluate_simq` or `tools.calibrate_simq` as a module (e.g. `evaluate_simq.py::_run_calibration` imports `tools.calibrate_simq`) | New `tools/simq_audit_gaps.py` must not break these import paths (e.g. must not introduce a circular import or side-effecting module-level code) |

## New Tests Required

This ticket is process/tooling work (`chore`), not a simulation-behavior change — no Mechanics Bible
formula, engine phase, or parity-ledger-governed behavior is modified. New tests are scoped to the new
`tools/simq_audit_gaps.py` script only:

1. **`tests/unit/tools/test_simq_audit_gaps.py`** (new file):
   - `test_flags_uncovered_anchor_key` — given a fixture `grade_anchors.json`-shaped dict with a key not
     present in either `FAST_ANCHOR_KEYS` or `SLOW_ANCHOR_KEYS`, confirm the tool reports it as UNCOVERED.
   - `test_no_false_positive_for_covered_keys` — every real key currently in
     `tests/simulation_quality/fixtures/grade_anchors.json` must NOT be flagged as uncovered (this is the
     live regression check — run it against the actual fixture, not a synthetic one, so it catches the
     next batch's version of the exact gap this ticket found: a new anchor key added to the JSON but
     never added to the test file's key lists).
   - `test_parity_ledger_candidate_scan_finds_known_entries` — given the real `docs/parity_ledger/`
     directory, confirm the scan surfaces `INFRA-251`, `INFRA-258`, `SOC-237`, `SOC-238` (all confirmed
     present and SimQ-related per the investigation) as candidates. This is a content-coupled test (breaks
     if those IDs are ever renumbered) — acceptable because it directly encodes "the tool must find the
     ledger entries we know are SimQ-relevant," which is the tool's entire purpose.
   - `test_exit_code_always_zero` — confirm the script is informational-only (never blocks `make
     simq-full-audit` on its own; the pytest step is the actual gate) per §4 of investigation.md.

2. **Makefile target smoke test** (manual, not pytest — Makefiles aren't unit-tested in this repo): confirm
   `make simq-full-audit` runs to completion (exit 0 when no regressions) against the current repo state as
   part of the dry-run required by ticket Scope item 4. This is covered by the dry-run/smoke-test itself,
   not a separate automated test.

No new tests are needed for `.claude/workflows/simq-audit.js` or its skill wrapper — this repo does not
unit-test the JS workflow files themselves (confirmed: no test files reference `implement-ticket.js` or
`implement-epic.js` directly); their correctness is validated by dry-running the pipeline end-to-end, same
as this ticket's Acceptance Criteria requires.

## Scoped Pytest Commands

```bash
# Existing regression surface (must still pass, unmodified by this ticket)
python3 -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q
python3 -m pytest tests/simulation_quality/test_grade_regression.py -q          # slow tier included

# New tool's own tests (once implemented)
python3 -m pytest tests/unit/tools/test_simq_audit_gaps.py -q

# Combined scoped run for this ticket
python3 -m pytest tests/simulation_quality/test_grade_regression.py tests/unit/tools/test_simq_audit_gaps.py -m "not slow" -q
```

Do not run bare `pytest tests/` — scope stays within `tests/simulation_quality/` and the new
`tests/unit/tools/` file per this repo's Testing Rule.

## Anti-Drift Test Guards

- **Anchor-coverage guard** (`test_no_false_positive_for_covered_keys` above): this is the direct
  regression test for the exact gap this ticket's investigation found (new anchor keys silently missing
  from `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`). Any future SimQ batch that adds anchor keys without
  updating the key lists will fail this test the next time `make simq-full-audit` runs — closing the loop
  the ticket was opened to close.
- **No silent anchor mutation**: any implementation of `tools/simq_audit_gaps.py` must be read-only
  (never writes to `grade_anchors.json` or `test_grade_regression.py` itself) — only the agent-orchestrated
  workflow's "Update Anchors" phase (a human-in-the-loop-reviewable `agent()` call) should perform those
  edits. A test asserting the script performs no filesystem writes (e.g. via `tmp_path` + checking no
  unexpected files/mtimes change) should guard this boundary if the implementation risks blurring it.
- **`data/calibration/` non-tracked assumption**: if the implementer adds any test that depends on
  pre-existing `data/calibration/*/quality_report.json` fixtures, it must generate them within the test
  (or use a committed fixture under `tests/simulation_quality/fixtures/`) rather than assuming a prior
  `calibrate_simq.py` run happened in CI — `data/calibration/` is confirmed not git-tracked (investigation
  §1.2), so CI/fresh-checkout runs will not have it populated.
- **Dry-run acceptance evidence**: per ticket Scope item 4 ("dry-run it against the current post-Batch-3
  state"), the implementation phase must capture and report actual `make simq-full-audit` output (REGRESS
  count, UNCOVERED count) run against the real repo post-`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` state as
  evidence in the ticket's Test Summary — not a synthetic/mocked demonstration.
