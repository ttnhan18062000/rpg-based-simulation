---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION
phase: open
date: 2026-09-17
tags: [architecture, schema, simulation-quality]
---

# TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION

## Title
Extend `implemented_by` coverage beyond 26 of 89 mechanisms — the unticketed precondition for both
queued detectors

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Peer review, closing out the mechanism-registry PR: extending `implemented_by` coverage beyond its
current 26 of 89 mechanisms isn't ticketed anywhere. It exists only as a stated intention across
several conversations, even though it is the hard precondition for both queued detectors
(`TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` reads registry state directly, but
`TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` reads `implemented_by` specifically —
and the state-caller-mismatch detector's own future re-runs need broader, less-biased coverage to
produce a meaningful assessment). This is the same orphan-knowledge failure shape this whole arc
exists to catch, just one level up: an intention scoped in conversation, never landed as a real,
findable ticket.

**Correction to the figure itself, found while filing this ticket**: prior reports in this epic
(including this session's own PR description) said "24 of 89." Direct recount says **26 of 89** —
`len(report.bound)` in `mechanism_registry_completeness_check.py`'s own output counts *bound
`src/domains/`/`src/systems/` targets*, not *mechanisms with a binding*; several mechanisms
(`fame`, `fidelity_drift`, `belief_institution`, `commitment_pressure_consequences`) bind multiple
files each, and two (`declared_cognition_schema`, `committed_intentions`) bind
`core/cognition.py`, outside that checker's own `src/domains/`/`src/systems/` scope entirely — so
target-count and mechanism-count diverge. Use `mechanisms_with_binding` (or a direct count of
mechanisms with a non-empty `implemented_by`) for "how many mechanisms are covered," not the
completeness checker's own target count, which answers a different, narrower question.

## Scope
1. Bind a real, meaningful batch of the remaining 63 unbound mechanisms with `implemented_by`
   (symbol-level where a file mixes unrelated symbols, file-level where a file's symbols are
   genuinely one concept — same discipline as every binding done so far in this epic).
2. Prioritize mechanisms that were NOT recently hand-verified by this session, since the existing
   26 are disproportionately the mechanisms already checked while fixing known defects — exactly
   the sample-bias phase 1 and the orphan batch both flagged. A useful next batch should include
   mechanisms nobody has looked at closely yet.
3. Apply the same verification rigor as every prior binding in this epic: real caller checks, not
   assumed from the atlas's own prior narrative — several prior "confirmed orphan" and "confirmed
   done" claims in this epic turned out wrong on direct re-check.
4. Any state correction found along the way gets the same treatment as `camp`/
   `demographic_cohort_cycle`/`succession`: a real `verified` block, propagated to every consumer
   artifact, not silently absorbed.

## Out of Scope
- Binding all remaining 63 mechanisms in one pass — this is deliberately incremental, ongoing
  work, not a single bounded task with a fixed completion count.
- Building either queued detector — both are explicitly sequenced after this ticket in
  `tickets/todos/mechanism-verification/SEQUENCE.md`.

## Acceptance Criteria
1. `implemented_by` coverage measurably increases beyond 26 of 89, with each new binding backed by
   a real, direct caller/symbol check.
2. The batch's own selection is biased toward NOT-recently-verified mechanisms, recorded
   explicitly, so the next false-positive-rate assessment isn't run against the same cleanest
   slice twice.
3. Any state correction found is propagated to every consumer artifact (atlas, capabilities,
   wiring map), not just the registry field.

## Related Tickets
- `TCK-20260917-EPIC-MECHANISM-VERIFICATION` — parent epic; this is the first child, a hard
  precondition for the other three.
- `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION`,
  `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` — both sequenced after this ticket.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` §7 Phasing — phase 1's own explicit
  statement that its result should decide whether phases 2/3 are worth building, which requires
  coverage broader than the current biased sample.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/mechanism_registry_completeness_check.py`,
  `mechanism_state_caller_check.py` — both read `implemented_by`; this ticket increases what they
  can check.

## Assumptions / Open Questions
No fixed target count set deliberately — "a real, meaningful batch" is intentionally left to
whoever picks this up, informed by how much the false-positive-rate assessment needs to move to be
trustworthy.

## Implementation Notes
To be completed during implementation.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Not yet started.
