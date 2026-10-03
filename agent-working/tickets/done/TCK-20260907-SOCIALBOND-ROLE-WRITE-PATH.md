---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH
phase: done
date: 2026-09-07
tags: [social, architecture]
---

# TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH

## Title
Wire a real writer for SocialBond.role, or confirm and remove it as dead scaffolding

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 2 of 6.
`RelationshipRole` (`src/core/models/social.py:7`, real enum, `SocialBond.role` defaults to
`NEUTRAL`) has a real read/merge path (`src/systems/social_systems/relationships.py:61`:
`role=b_upd.role_set if b_upd.role_set is not None else bond.role`), confirmed 2026-09-07, but zero
real (non-test) construction anywhere in `src/` of a bond-update object with `role_set` set to
anything — every `SocialBond.role` in the live system is permanently `NEUTRAL`. This is a
foundational relationship field, not a narrow content gap — potentially every relationship in the
game is affected.

## Scope
- Determine the real, live-precedented trigger for setting `role_set`. The nemesis-promotion pattern
  (`grudge_history >= 3.0` → `nemesis_ids`, `src/systems/social_systems/memory.py`) is the most
  obvious real precedent already proven live — check whether `RelationshipRole` should mirror that
  same threshold-driven promotion pattern for its own values (confirm the real enum values first, not
  assumed here).
- If a real trigger is designed and wired: add it through the authoritative apply-path only
  (`role_set` on the typed bond-update object, following `bond.role`'s existing read/merge
  convention).
- If, after investigation, no real gameplay consumer would ever read `SocialBond.role` meaningfully
  (confirm this by checking all real read sites of `.role`, not just the merge logic): remove the
  field and its dead read/merge path instead of leaving it as silent scaffolding. This is a real
  decision this ticket must make explicitly, not defer further.

## Out of Scope
- Any other item from the Dormant Mechanism Closure epic's scope.
- Building a generic relationship-classification framework beyond what `RelationshipRole`'s existing
  enum already defines.

## Acceptance Criteria
- [x] Either: (a) a real, tested trigger sets `SocialBond.role` through the authoritative apply-path
      for at least one real enum value, confirmed via a test showing a bond transition; or (b) the
      field is confirmed dead and removed, with the removal itself tested (no regression). **Done —
      (a)**: `RelationshipService.process_update()` now derives `role` from real `sentiment_delta`
      changes; 7 new tests including a real bond-transition proof.
- [x] Whichever disposition is chosen, it's recorded with a real, evidenced reason — not a coin flip.
      **Done** — wiring chosen because a real, live, already-shipped consumer
      (`PartyCompositionScorer` via the `FORM_PARTY` route) has been silently starved of real data
      since `TCK-20260824-RELATIONSHIP-ROLE-FIELD` shipped; removal would have deleted a real,
      intended scoring dimension rather than fix its actual gap. See investigation.md.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/simulation/social_systems_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/models/social.py`
- `src/systems/social_systems/{relationships,memory}.py`

## Assumptions / Open Questions
- Whether wiring a real trigger or removing the field is the right call is not decided here — real
  investigation work for this ticket's own Investigate/Plan phases.

## Implementation Notes
Investigate found the ticket's own suggested precedent (mirror the nemesis-promotion pattern) is
itself dead code — `SocialMemoryService.check_nemesis_promotion()`/`tick_place_attachment()` have zero
real callers anywhere in `src/`, a second, adjacent dormant-mechanism finding disclosed in
`docs/mechanics/07_social_political_dynamics.md` §3 (corrected for internal consistency with §2's own
new disclosure) but not fixed here — out of this ticket's scope, flagged for a future ticket.

Chose to derive `role` directly inside `RelationshipService.process_update()` (the confirmed real,
live, per-update apply-path, called from `src/engine/patches.py:558`) rather than mirroring
`check_nemesis_promotion()`'s producer-function shape, which would have risked repeating the exact
"real function, no live caller" failure mode. `FRIEND_SENTIMENT_THRESHOLD=0.8`/
`RIVAL_SENTIMENT_THRESHOLD=-0.8` reuse `appraisal.py`'s own real `TOTAL_DISTRUST` bound
(`bond.sentiment < -0.8`) rather than an invented number. Derivation only fires when
`b_upd.sentiment_delta != 0` (a real sentiment change occurred) — required to preserve a pre-existing
test (`test_process_update_role_set_none_preserves_existing_role`) asserting a familiarity-only update
must not touch `role`. Confirmed a real, live-reachable consumer already existed and was silently
starved: `PartyCompositionScorer.score_role_affinity()`, reached via
`src/domains/adventure/generator.py:140`'s real `FORM_PARTY` route call (`actor=` passed), had always
contributed exactly `0.0` since it shipped.

## Test Summary
7 new tests in `tests/unit/social/test_relationships.py`, all passing: FRIEND/RIVAL derivation from a
real `sentiment_delta`, mid-band no-op, sticky-against-later-mid-band, cross-boundary flip, explicit
`role_set` override priority, and zero-`sentiment_delta` no-touch (re-asserting the pre-existing
guarantee). Both pre-existing role tests re-run unmodified and still passing (18/18 total in the
file). `tests/architecture/test_social_write_paths.py` — 3/3 passing (authoritative-write-path guard
unaffected). Broader sweep: `tests/unit/social/ tests/unit/domains/campaigns/
tests/integration/campaigns/` — 437 passed, 0 failed.

## Files Changed
- `src/systems/social_systems/relationships.py` (new derivation logic + 2 class constants)
- `tests/unit/social/test_relationships.py` (7 new tests)
- `docs/mechanics/07_social_political_dynamics.md` (§2 write-path correction, §3 nemesis/place-
  attachment dormancy disclosure)
- `docs/parity_ledger/social_narrative.yaml` (new `SOC-248` entry)
- `docs/REGISTRY.yaml` (regenerated)

## Completion Summary
Wired `SocialBond.role`'s first real, live production writer: `RelationshipService.process_update()`
now derives `role` from a bond's own real `sentiment` changes (`>= 0.8` → `FRIEND`, `<= -0.8` →
`RIVAL`, reusing `appraisal.py`'s own real `TOTAL_DISTRUST` bound), guaranteed reachable since it
lives inside the confirmed-live authoritative apply-path rather than a new, separately-callable
producer function. This activates a real, already-shipped consumer
(`PartyCompositionScorer.score_role_affinity()`) that had been silently contributing `0.0` in every
real `FORM_PARTY` adventure route since it shipped. Along the way, found and disclosed (but did not
fix, per this ticket's own narrow scope) that the ticket's own suggested nemesis-promotion precedent
is itself dead code — corrected the same Chapter 07 for internal consistency. No production behavior
outside `RelationshipRole` derivation changed; both pre-existing role tests pass unmodified.
