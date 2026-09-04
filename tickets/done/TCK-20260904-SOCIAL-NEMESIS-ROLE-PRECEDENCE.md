---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE
phase: done
date: 2026-09-04
tags: [social, combat]
---

# TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE

## Title
nemesis_ids does not gate FORM_PARTY or PartyCompositionScorer's role-affinity term — a confirmed
contradictory-signal bug, not the "no confirmed bug yet" the roadmap currently says

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s Social/Relationship axis section lists "which of
`RelationshipRole` (`FRIEND`/`RIVAL`) or `nemesis_ids` (grudge-promoted) should take precedence when both
are set for the same pair" as "a real unreconciled seam with no confirmed bug yet." Investigated directly
(2026-09-04): there is a confirmed bug, not just an open seam.

`SocialComponent.nemesis_ids` (`src/core/models/social.py`) is promoted independently from
`grudge_history` reaching `>= 3.0` (`SocialMemoryService.check_nemesis_promotion()`,
`src/systems/social_systems/memory.py`) — a real, sustained-harm signal. `SocialBond.role`
(`FRIEND`/`RIVAL`/`NEUTRAL`) is written on a completely separate path with zero coupling to
`nemesis_ids` (confirmed via direct grep: `check_nemesis_promotion()` never reads or writes `bond.role`,
and `RelationshipRole`'s own docstring already states "Independent of nemesis_ids/grudge_history"). This
means an entity pair can genuinely hold `bond.role == FRIEND` while the same target is also in
`nemesis_ids`, and nothing reconciles them.

Two real, live consumers read these fields independently, and neither catches the contradiction:
- `PartyCompositionScorer._candidate_role_value()` (`src/systems/social_systems/party_composition.py`)
  scores a `FRIEND`-bonded candidate `+1.0` regardless of `nemesis_ids` — a confirmed nemesis with a
  stale `FRIEND` tag contributes *positively* to party composition score.
- `src/domains/adventure/generator.py`'s `FORM_PARTY` route's own nemesis-block check
  (`# E43G: block FORM_PARTY if any candidate is a nemesis`) only reads a locally-derived proxy set from
  `entity.strategic.blockers` filtered by `BlockerKind.SOCIAL` — it never reads the canonical
  `SocialComponent.nemesis_ids` field at all. A confirmed nemesis with no matching strategic blocker is
  not blocked from party formation by this mechanism.

## Scope
- `PartyCompositionScorer._candidate_role_value()`: `nemesis_ids` takes precedence over `bond.role ==
  FRIEND` (return the same `-1.0` a `RIVAL` bond would). Rationale: `nemesis_ids` is promoted only from
  sustained real harm history, a stronger signal than the coarser, independently-written `bond.role` tag,
  which is never automatically downgraded when a bond later turns hostile.
- `src/domains/adventure/generator.py`'s `FORM_PARTY` nemesis-block check: also check the canonical
  `entity.social.nemesis_ids` field, unioned with the existing `strategic.blockers`-derived proxy set —
  do not replace the existing check, since the two may catch different real scenarios.
- Add regression tests locking in both fixes: a `FRIEND`-bonded candidate who is also a confirmed nemesis
  must score negatively (not positively) and must block `FORM_PARTY`.
- Update the roadmap's Social/Relationship axis section to record this as resolved (confirmed bug, fix
  landed), replacing the "no confirmed bug yet" framing.

## Out of Scope
- `PartyCompositionScorer._candidate_trust_value()`'s own separate, already-established precedent ("bond
  sentiment takes priority over trust_history") — a different precedence question, already resolved, not
  touched by this ticket.
- Any change to `nemesis_ids` promotion logic itself (the `>= 3.0` threshold) or to `RelationshipRole`'s
  own write paths — this ticket only changes how the two are reconciled when read together, not how
  either is produced.
- The `strategic.blockers`-derived nemesis proxy in `generator.py` — kept as-is (unioned with, not
  replaced by, the canonical field), since it may catch scenarios `nemesis_ids` alone does not.

## Acceptance Criteria
- [x] `PartyCompositionScorer._candidate_role_value()` returns `-1.0` for a candidate in `nemesis_ids`,
      regardless of `bond.role`.
- [x] `generator.py`'s `FORM_PARTY` nemesis-block check also considers the canonical `nemesis_ids` field.
- [x] New regression tests confirm both fixes (a `FRIEND`-bonded-but-nemesis candidate scores negatively
      and blocks `FORM_PARTY`). 5 new tests added.
- [x] Existing `tests/unit/social/test_party_composition.py` suite passes unchanged for every case that
      does not involve a `nemesis_ids`/`FRIEND`-bond conflict. 30/30 pass.
- [x] `rpg_design_roadmap.md`'s Social/Relationship axis section updated to record the resolution.

## Related Tickets
- TCK-20260902-SOCIAL-CANONICAL-HASH-GAP (the sibling Social-axis fix this ticket's precedence question
  was originally flagged alongside)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (Social/Relationship axis section)
- `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md`

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE/`)

## Related Code Areas
- `src/systems/social_systems/party_composition.py` (`_candidate_role_value`)
- `src/domains/adventure/generator.py` (`FORM_PARTY` route generation)
- `src/systems/social_systems/memory.py` (`check_nemesis_promotion`, for reference only — not modified)
- `tests/unit/social/test_party_composition.py`

## Assumptions / Open Questions
None beyond what's stated above — this is a well-bounded, evidence-confirmed fix, not an open design
question.

## Implementation Notes
Confirmed via direct code read that `nemesis_ids` and `bond.role` are written on fully independent
paths — `SocialMemoryService.check_nemesis_promotion()` never touches `bond.role`, and
`RelationshipRole`'s own docstring already states the independence. Fixed `_candidate_role_value()` to
check `nemesis_ids` first (returns `-1.0`, same as `RIVAL`) before falling through to the `bond.role`
check. Fixed `generator.py`'s `FORM_PARTY` nemesis-block check to union the canonical `nemesis_ids`
field with the existing `strategic.blockers`-derived proxy, rather than replacing it — the two may
catch different real scenarios, so both stay active.

## Test Summary
5 new tests in `tests/unit/social/test_party_composition.py` (nemesis-overrides-friend,
nemesis-without-bond, non-conflicting-cases-unchanged, end-to-end score comparison, `FORM_PARTY` block
via canonical field alone). Full scoped sweep: `pytest tests/unit/domains/adventure/ tests/unit/social/
tests/integration/domains/adventure/ tests/architecture/test_adventure_routing_flag_inert.py
tests/architecture/test_adventure_route_score_max_unchanged.py -m "not slow"` → 355 passed, 1
deselected, 0 failed.

## Files Changed
- `src/systems/social_systems/party_composition.py` — `_candidate_role_value()` nemesis precedence.
- `src/domains/adventure/generator.py` — `FORM_PARTY` nemesis-block check unions canonical field.
- `tests/unit/social/test_party_composition.py` — 5 new tests, `_entity()` helper gained `nemesis_ids`.
- `docs/parity_ledger/social_narrative.yaml` — new entry `SOC-265`.
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — Social/Relationship axis section updated.

## Completion Summary
Closed the Social/Relationship axis's flagged `RelationshipRole`/`nemesis_ids` precedence question —
confirmed a real, live bug (not just an unreconciled seam): a confirmed nemesis with a stale `FRIEND`
bond tag scored positively for party composition and was not blocked from `FORM_PARTY` unless an
unrelated strategic blocker happened to also exist. `nemesis_ids` now takes precedence, and the
`FORM_PARTY` block reads the canonical field. Full existing test suite passes unchanged; 5 new tests
lock in the fix. Parity ledger entry `SOC-265` added (originally written as `SOC-264`, renumbered
during a merge-conflict resolution against `origin/main`'s own concurrent `SOC-264`, the
`TCK-20260903-CLAN-LIFECYCLE-SUCCESSION` entry).
