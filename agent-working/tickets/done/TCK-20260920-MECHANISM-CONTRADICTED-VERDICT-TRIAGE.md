---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-CONTRADICTED-VERDICT-TRIAGE
phase: done
date: 2026-09-20
tags: [architecture, schema, world]
---

# TCK-20260920-MECHANISM-CONTRADICTED-VERDICT-TRIAGE

## Title
Batch 4 of the unbound-claims program: triage the 6 pre-existing `contradicted`-verdict
mechanisms into real, scoped, trackable tickets — fixes stay held for the roadmap session

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Batch 4 of the 4-batch unbound-claims program. Unlike batches 1-3 (bind, correct, or verify a
claim), this batch's own job is process, not registry data: confirm every mechanism whose
`verified.verdict` is `contradicted` has a real, dedicated ticket tracking the underlying finding
— filing one where none exists, updating one where new evidence changed the picture, and
confirming existing coverage where it already exists. **No code fixes.** Fixes are the roadmap
session's, per peer's own explicit framing.

6 mechanisms carried a `contradicted` verdict predating today's own batches: `tactical_decision`,
`readiness_speed_scaling`, `regional_trauma`, `demographic_cohort_cycle`, `calamity_intensity`,
`camp`. (Batches 1/2 also produced 6 *new* `contradicted`/state-corrected entries today —
`breakthrough_bonuses`, `commitment_betrayal`, `quest_generation_sourcing`, `betrayal_siege_war`,
`chronicle`, `equipment_scoring` — each of those is already fully resolved as part of its own
batch, with the finding itself already the correction; none needed further triage here.)

Also folded in, per peer's explicit mention: `information_trust_deception`'s own questionable
"flag-gated" `verified` note, a wrong-verdict-shaped finding from batch 1, routed here rather than
resolved in passing.

## Scope
Check each of the 6 pre-existing `contradicted` mechanisms for real, dedicated ticket coverage:
1. `tactical_decision` — already tracked via `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`'s
   own child `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`. Confirmed adequate,
   no new ticket.
2. `readiness_speed_scaling` — already tracked via the same epic's
   `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` (root cause) and
   `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (the shared-cause follow-up).
   Confirmed adequate, no new ticket.
3. `regional_trauma` — already tracked via `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`.
   Confirmed adequate, no new ticket.
4. `demographic_cohort_cycle` — **no dedicated ticket existed.** Filed
   `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED`.
5. `calamity_intensity` — tracked via `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`, but
   this session's own batch 2 found a *stronger* finding (zero real callers for the producer at
   all, not merely an unreachable trigger condition) that the existing ticket's own framing
   didn't cover. Updated that ticket with the new finding rather than filing a duplicate.
6. `camp` — **no dedicated ticket existed** (only a shared cross-reference doc). Filed
   `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`.

Plus: `information_trust_deception`'s own questionable verdict, filed as
`TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED`.

Plus: `docs/plans/world_composition_precondition_gap_finding.md` updated with `camp` and
`demographic_cohort_cycle` as instances 5 and 6 of its own already-established pattern.

## Out of Scope
- Fixing any of the underlying code/content gaps — every one of these stays a real, open,
  well-evidenced finding for the roadmap session, not fixed here.
- The `xp_leveling`/`evolution` identity investigation — its own separate ticket
  (`TCK-20260920-MECHANISM-XP-LEVELING-EVOLUTION-IDENTITY-INVESTIGATION`), landing in the same PR.

## Acceptance Criteria
1. Every one of the 6 pre-existing `contradicted` mechanisms has real, dedicated ticket coverage —
   confirmed if it already existed, filed if it didn't.
2. `information_trust_deception`'s own questionable verdict has a dedicated ticket.
3. No code fixed; every finding stays a real, open, reviewable ticket for the roadmap session.
4. The shared pattern doc reflects the two newly-tracked instances.

## Related Tickets
- `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`,
  `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED`,
  `TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED` — newly filed by this batch.
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — updated by this batch with a stronger
  finding.
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`,
  `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — confirmed already-adequate coverage, not
  touched.

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — extended with 2 new instances.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-CONTRADICTED-VERDICT-TRIAGE/`.

## Related Code Areas
None — this is a ticket-filing/tracking batch, no code touched.

## Assumptions / Open Questions
None open for this batch's own scope.

## Implementation Notes
The 6-vs-12 count reconciliation: `registries/mechanisms.yaml` shows 12 `contradicted`-verdict
mechanisms as of this batch's own start, but 6 of those are ones *this same day's* batches 1/2
produced (already fully resolved — the finding IS the correction, e.g. `equipment_scoring`'s own
state correction to `orphan` already reflects the contradiction it found). Only the 6 pre-existing
ones (dated 2026-09-16/17/19, from before today) needed triage — confirmed against peer's own
stated count.

## Test Summary
No test changes — pure ticket-filing/doc-update batch. Full `tests/unit/tools/` suite re-run for
safety: 260 passed (unchanged from batch 3, confirming no registry drift from this batch's own
ticket/doc work).

## Files Changed
- `tickets/todos/TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION.md` — new.
- `tickets/todos/TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED.md` — new.
- `tickets/todos/TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED.md` — new.
- `tickets/todos/TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES.md` — updated with the
  stronger 2026-09-20 finding.
- `docs/plans/world_composition_precondition_gap_finding.md` — 2 new instances added.

## Completion Summary
**Done.** All 6 pre-existing `contradicted`-verdict mechanisms now have real, dedicated ticket
coverage: 3 already adequate, 2 newly filed, 1 updated with a stronger finding. One additional
questionable-verdict finding (`information_trust_deception`) routed to its own ticket per peer's
explicit request. No code fixed anywhere in this batch — every finding stays open and reviewable.
