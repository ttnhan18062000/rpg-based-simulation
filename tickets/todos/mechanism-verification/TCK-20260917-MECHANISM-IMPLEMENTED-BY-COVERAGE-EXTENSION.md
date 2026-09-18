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

### Coverage acceptance targets, per claim-type — added 2026-09-17, previously undeclared anywhere

Discussed but never landed in an artifact until now. **"Enough coverage" is declared per
claim-type, not as one global percentage** — a global target like "80% bound" invites binding the
easy mechanisms just to move the number, the same failure shape the claims-as-tests detectors'
exclusion lists exist to prevent, generalized one level up.

- **`orphan` → 100%, no exceptions.** `orphan` means zero callers — fully, mechanically decidable
  by a real caller check, nothing left to judgement. The measured error rate on this exact claim
  was **4 of 6** when the orphan-state batch actually checked it
  (`TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`) — a claim this cheap to verify and
  this often wrong has no honest reason to stay unchecked.
- **`gated` → 100%.** Same reasoning as `orphan`: a feature flag either exists on the entry path or
  it doesn't. Mechanically decidable, so fully bind it.
- **`done` / `partial` → no coverage target.** These are judgements about completeness, not
  mechanically decidable facts — `implemented_by` binding alone can't settle whether a `done`
  mechanism actually works; the `verified` axis (below) is what settles that, not binding coverage.
- **`verified` → no target at all.** 2 of 89 runtime-verified is the honest current state. Setting
  a target here would produce direct pressure to raise that number, which is exactly the shape of
  the fabricated/stale verdicts this whole axis exists to catch (`motivation_doctrine`'s own "still
  confirmed live" claim eight days after its code was deleted is the standing example).

This ticket's own scope (item 1, "a real, meaningful batch") is now sharpened by this: prioritize
binding every remaining `orphan` and `gated` mechanism toward their 100% targets first, since those
are the two claim-types where non-100% coverage is itself a stated gap rather than an accepted one.
`done`/`partial`/`verified` binding remains valuable (item 2's own de-biasing goal still applies)
but isn't held to a numeric target the way `orphan`/`gated` now are.

**Current state against these targets, checked 2026-09-17**: `orphan` is already at its 100%
target — all 7 `orphan`-state mechanisms are bound. `gated` is at 3 of 8 (`self_model`,
`information_trust_deception`, `knowledge_model`, `quest_generation_sourcing`,
`opportunity_rumor_seeds` remain unbound) — these 5 are this ticket's own concrete, prioritized
starting list, not an abstract "some gated mechanisms" instruction.

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
4. Every remaining `orphan` and `gated` mechanism is either bound (moving that claim-type toward
   its 100% target) or explicitly recorded as a known gap against that target, with a reason — not
   silently left unbound with no note that a target exists for it.

## Related Tickets
- `TCK-20260917-EPIC-MECHANISM-VERIFICATION` — parent epic; this ticket is second in
  `SEQUENCE.md`'s own order, after `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`
  (resequenced 2026-09-17 — a split from that ticket would otherwise divide a binding already done
  here, see that ticket's own reasoning).
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
