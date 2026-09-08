---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION
phase: open
date: 2026-09-09
tags: [cognition, social, observability]
---

# TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION

## Title
Re-verify grief/nemesis event reachability in a real, populated campaign_life_arc episode

## Status
BLOCKED

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260824-GRIEF-NEMESIS-REACHABILITY` closed with a "reachable" claim that, per a 2026-09-08
addendum (added during `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`'s own root-cause
determination, not reopening that ticket), rests on two different kinds of evidence: (1)
`CampaignOrchestrator.run_episode()` being reachable from a real production entrypoint — genuinely
verified, unaffected by anything below; and (2) `grief_urgency_triggered`/`nemesis_relation_formed`
`SimulationEvent`s "are emitted from... paths" — verified only via a **synthetic** event envelope
fed directly into `SocialScorer` (`tests/simulation_quality/test_social_scorer.py`'s
`TestGriefNemesis` class), never via a real campaign episode.

That gap existed because `campaign_life_arc` has, until `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`
lands, run with **zero entities** for its entire episode — no entity has ever died in one, so no
grief/nemesis trigger could possibly have fired in a real run regardless of whether the underlying
emission code is correct. This ticket exists specifically so that gap doesn't depend on someone
remembering to re-check it once entities exist — user decision, 2026-09-09 (via peer review
`rpg-feature-planning`, confirmed directly).

## Scope
Explicitly blocked on `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` landing first; does not
start until that ticket closes with entities genuinely spawning in `campaign_life_arc`.

- Once `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` lands: run a real `campaign_life_arc`
  episode (or a real scenario with the same shape) for real, long enough for at least one entity
  death to plausibly occur (combat, passive decay, or any other real death path).
- Confirm, via real observed `SimulationEvent`s from that run (not synthetic construction), whether
  `grief_urgency_triggered`/`nemesis_relation_formed` events actually fire when a real entity dies
  in a real campaign episode.
- If they fire correctly: record this as the first genuine confirmation, update
  `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s own addendum to reflect the closed gap (a further
  addendum, not silently editing the original text).
- If they do NOT fire (a real bug in the emission wiring itself, previously masked by the
  zero-entity gap): this is a real, newly-discovered bug — do not silently patch it as an aside;
  treat it with the same rigor as any other confirmed bug in this batch (real test evidence,
  peer-routed fix decision if the fix isn't trivial).

## Out of Scope
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own entity-spawn correctness — this ticket
  assumes that ticket's own work is already verified and closed; not re-litigated here.
- Any other Campaign-mode subsystem's own reachability (war/siege/calamity, already covered by
  `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own addendum and
  `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`'s own remaining AC item) — this ticket
  is scoped to grief/nemesis specifically.

## Acceptance Criteria
- [ ] A real `campaign_life_arc` (or equivalent, now-populated) episode run produces at least one
      real entity death.
- [ ] Real observed evidence (not synthetic) confirms whether `grief_urgency_triggered`/
      `nemesis_relation_formed` events fire from that real death, through both the mid-episode and
      episode-boundary trigger paths named in the original ticket.
- [ ] `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s own 2026-09-08 addendum is updated with the real
      result (confirmed working, or confirmed a real bug with its own follow-up).

## Related Tickets
- `TCK-20260824-GRIEF-NEMESIS-REACHABILITY` (the ticket whose claim this re-verifies)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (hard blocker — must land first)
- `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` (origin of the zero-entity finding that
  created this gap)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — created when this ticket is actually picked up (currently blocked).

## Related Code Areas
- `src/domains/campaigns/orchestrator.py`
- Grief/nemesis emission paths named in the original ticket (`GriefUrgencyImporter`,
  `NemesisRelationImporter`, the mid-episode `entity_death` → `GriefUrgencyImporter.build_strategic_update()`
  route through `Kernel._phase_resolution` → `AuthoritativeApplyPipeline.refine()` → `ApplyPath`)

## Assumptions / Open Questions
None — scope is a straightforward re-verification once unblocked.

## Implementation Notes
_(blocked — not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
