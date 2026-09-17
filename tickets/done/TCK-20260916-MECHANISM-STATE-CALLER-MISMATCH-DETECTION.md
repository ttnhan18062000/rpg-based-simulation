---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION

## Title
Claims-as-tests phase 1: detect declared-state-versus-real-caller-count mismatches

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Claims-as-tests phase 1, per peer review, scoped as **state-versus-caller-count mismatch
detection**, not presence/absence. Every one of the four real registry state errors found by hand
this epic (`camp`, `motivation_doctrine`, `causal_spatial_memory`, `commitment_betrayal`'s
mis-binding) was a WRONG state, never a missing entry. `orphan` and `gated` in particular are
opposite conclusions -- dead code versus working code switched off -- so a reader acting on the
wrong one does the opposite of the right thing. A detector that only answers "does this mechanism
exist in code" would have caught none of the four.

**Report the false-positive rate as the headline finding, not the defect count** -- per peer
review, if caller-count detection turns out unreliable in this codebase, the honest conclusion is
that phases 2/3 of the initiative need re-arguing. Four real errors found by hand before any
detector existed is the baseline this tool is measured against, not a target it is assumed to
beat.

## Scope
1. Four checks, in order of cheapest payoff: `orphan` with real callers; `done`/`partial` with
   zero real callers; `gated` with no feature-flag context near a caller; `skeleton` whose body
   looks substantial, not a stub.
2. Reuse `implemented_by` (the real, disk-validated code binding) as the only source of "what code
   implements this mechanism" -- no new lookup table, no prose search.
3. Report-only, same convention as every other detector in this corpus.
4. Investigate every raw finding directly before drawing any conclusion -- never trust the tool's
   own output at face value, matching this whole epic's standing discipline.

## Out of Scope
- Phases 2/3 of the initiative (whatever those turn out to be) -- explicitly gated on this phase's
  own false-positive rate, per the initiative document.
- Fixing the multi-symbol-aggregation limitation found during investigation (a single
  `implemented_by` file can define multiple loosely-related symbols; the detector currently
  aggregates callers across all of them) -- would need a schema change, recorded as a known
  limitation, not fixed here.
- Resolving `demographic_cohort_cycle`'s own surfaced taxonomy ambiguity (does "invoked but
  data-starved" belong under `orphan`, `gated`, or a state this taxonomy doesn't have yet) --
  flagged for peer/taxonomy-owner attention, not silently reclassified by this ticket.

## Acceptance Criteria
1. All four checks implemented and reusing `implemented_by`, never a second lookup structure.
2. Report-only -- verified never to return non-zero on detection alone.
3. Every raw finding from the tool's first real run against the committed registry is individually
   investigated and its disposition recorded (true finding / detector bug / heuristic limitation /
   taxonomy ambiguity) -- not a bare count.
4. A historical regression test proves the detector would have caught at least one of the four
   real defects this epic already found by hand.
5. Every mechanism the tool cannot check (no `implemented_by`) is a named, counted `unchecked`,
   never a silent skip.
6. Full scoped suite passes, including with `graphify-out/` genuinely moved aside and restored.

## Related Tickets
- `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` -- hard precondition; this detector can only
  check the 20 of 89 mechanisms with a real binding today.
- `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` -- source of the `causal_spatial_memory`
  historical defect used as this ticket's own load-bearing regression test.
- `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION`,
  `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` -- sibling report-only detectors, sequenced
  after this one per peer's own queue order.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` (peer's own planning doc, not in this
  worktree) -- the initiative this ticket is phase 1 of; phase 1's own result is meant to decide
  whether phases 2/3 are worth building.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION/investigation.md` --
  the full per-finding disposition, the headline false-positive analysis, and the multi-symbol
  aggregation limitation.

## Related Code Areas
- `tools/mechanism_registry/mechanism_state_caller_check.py` (new)
- `docs/brainstorm/mechanisms.yaml`
- `Makefile`

## Assumptions / Open Questions
`demographic_cohort_cycle`'s own surfaced taxonomy ambiguity (see investigation.md) is genuinely
open -- not resolved by this ticket, flagged for peer.

## Implementation Notes
See `stored_artifacts/TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION/investigation.md` for
the full method and per-finding disposition. Summary: first real run produced 4 raw findings; 2
were real bugs in the detector itself (fixed: function-only modules produced a false "zero
callers" reading; comment-text was counted as a real caller), 1 is a confirmed-unreliable
low-confidence heuristic (`skeleton_not_stub`, kept but explicitly flagged as needing a different
approach, not incremental tuning), and 1 is a genuine registry-taxonomy ambiguity, not a detector
or registry defect (`demographic_cohort_cycle`'s own "invoked but data-starved" shape doesn't
cleanly fit `orphan` or `gated` as currently defined).

**Net result: zero confirmed new registry defects, two real detector bugs found and fixed, one
heuristic confirmed unreliable, one genuine taxonomy question surfaced.** This is reported as the
headline finding per peer's own explicit instruction, not smoothed over into a bare "N findings"
count.

## Test Summary
See `stored_artifacts/TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION/test_plan.md`. 11 new
tests; 180 passing in the full scoped suite, both with `graphify-out/` present and with it
genuinely moved aside and restored.

## Files Changed
- `tools/mechanism_registry/mechanism_state_caller_check.py` -- new
- `tests/unit/tools/test_mechanism_state_caller_check.py` -- new, 11 tests
- `Makefile` -- `mechanism-state-caller-check` target

## Completion Summary
Closed. Built the first claims-as-tests detector, scoped exactly per peer review as state-versus-
caller-count mismatch detection rather than presence/absence. Its own first real run against the
committed registry became its own best validation: of 4 raw findings, investigating each one
directly (rather than trusting the tool) found 2 real bugs in the detector itself -- both fixed --
1 heuristic confirmed unreliable on contact with real data, and 1 genuine taxonomy ambiguity
surfaced rather than a registry defect found. Zero new registry defects confirmed. This is reported
honestly as the headline result, per peer's own explicit framing: a high false-positive rate on a
detector's first run is itself the finding, not a smoothed-over defect count, and the four real
state errors found by hand this epic remain the standard this tool is judged against. The
multi-symbol-aggregation limitation and the taxonomy ambiguity are both recorded, not silently
absorbed, for whoever scopes the initiative's next phase.
