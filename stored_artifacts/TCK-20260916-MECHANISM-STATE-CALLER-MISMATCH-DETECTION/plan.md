---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION

## Steps

1. Build `tools/mechanism_registry/mechanism_state_caller_check.py`: four checks
   (orphan-with-callers, done/partial-with-zero-callers, gated-without-flag-context,
   skeleton-not-stub), reusing `implemented_by` for the code binding and the completeness
   checker's own shim-exclusion discipline.
2. Run it against the real committed registry; investigate every raw finding directly rather than
   trusting the tool's own output (mirrors this whole epic's standing discipline).
3. Fix real detector bugs found during investigation (function-only modules, comment-text
   false-matches) before drawing any conclusion about the registry itself.
4. Write regression tests using the real historical defects this epic already found
   (`causal_spatial_memory`'s own buggy `orphan` state) as the load-bearing proof the detector
   would have caught a real, already-known case.
5. Report the false-positive rate as the headline finding, with each finding's disposition
   individually investigated and recorded — never a bare count.
6. Add the `mechanism-state-caller-check` Makefile target.
7. Run the full scoped suite, including with `graphify-out/` genuinely moved aside and restored.

## Scope guard

Report-only — this ticket does not act on `demographic_cohort_cycle`'s own surfaced taxonomy
ambiguity by silently reclassifying it; that decision belongs to whoever owns the state taxonomy,
not this detector.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| 1. Four checks implemented, reusing `implemented_by` | `mechanism_state_caller_check.py` |
| 2. Report-only, never fails the build | `main()` always returns 0 |
| 3. False-positive rate is the headline, not the count | investigation.md's own disposition of all 4 raw findings |
| 4. Historical regression proof | `test_check_mechanism_flags_causal_spatial_memory_historical_defect` |
| 5. Every unchecked mechanism named, not silently skipped | `Report.unchecked` count, printed explicitly |
