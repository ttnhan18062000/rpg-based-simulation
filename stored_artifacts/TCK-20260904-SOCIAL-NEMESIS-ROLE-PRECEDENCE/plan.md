---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE
artifact_type: plan
tags: [social, combat]
---

# Plan — TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE

1. `PartyCompositionScorer._candidate_role_value()`: check `candidate.id in actor.social.nemesis_ids`
   first, return `-1.0` if true, before falling through to the existing `bond.role` check.
2. `src/domains/adventure/generator.py`'s `FORM_PARTY` route: union `entity.social.nemesis_ids` into the
   existing `strategic.blockers`-derived nemesis set before computing `nemesis_in_candidates`.
3. Add tests: a `FRIEND`-bonded-but-nemesis candidate scores `-1.0` (not `+1.0`); existing non-conflicting
   cases (`FRIEND` alone, `RIVAL` alone, `NEUTRAL`, no bond) stay unchanged.
4. Run `tests/unit/social/`, `tests/unit/domains/adventure/` (or wherever FORM_PARTY route tests live).
5. Update the roadmap's Social/Relationship axis section to record the resolution.
6. Parity ledger entry.
