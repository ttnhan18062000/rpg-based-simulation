---
status: active
layer: core
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH
date: 2026-09-07
---

# Investigation: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH

## Current Behavior
`RelationshipRole` (`src/core/models/social.py:7-11`) has exactly 3 real values: `NEUTRAL` (default),
`FRIEND`, `RIVAL`. `SocialBond.role` merge logic (`relationships.py:61`, pre-existing) is real; zero
real construction of `SocialBondUpdate(role_set=...)` exists anywhere in `src/` — confirmed via grep.

**Real live read consumer confirmed** (the ticket's own text doesn't establish this):
`PartyCompositionScorer._candidate_role_value()`/`score_role_affinity()`
(`party_composition.py:143-166`) reads `bond.role`, contributing `ROLE_AFFINITY_WEIGHT=0.10` to
`PartyCompositionScorer.score()`. Confirmed reachable from real production code:
`src/domains/adventure/generator.py:140` calls `PartyCompositionScorer.score(candidates[:8],
actor=entity)` inside the real `FORM_PARTY` adventure route — the only real call site that passes
`actor=`, without which `score_role_affinity()` never runs
(`src/systems/world_systems/groups.py:312` calls `score()` without `actor=`). This means the
`role_term` has been silently contributing exactly `0.0` to every real `FORM_PARTY` route score since
`TCK-20260824-RELATIONSHIP-ROLE-FIELD` shipped — a real, live-reachable, currently-inert scoring
term, not a hypothetical one.

## Correction — the ticket's own suggested precedent is itself dormant
The ticket's Scope suggests mirroring "the nemesis-promotion pattern ... the most obvious real
precedent already proven live." Direct verification found this is false:
`SocialMemoryService.check_nemesis_promotion()` (`memory.py:38-52`) has **zero real (non-test)
callers** anywhere in `src/` — confirmed via exhaustive grep for both the method name and its
containing service (`SocialMemoryService`, including the `src/systems/social_memory.py` re-export
shim `apply.py:46` imports, which is itself never actually invoked). `tick_place_attachment()`
(`memory.py:15-33`) is equally dead. Both are real, correct, already-unit-tested pure functions
(`tests/unit/social/test_social_memory_service.py`) with no live wiring into any per-tick phase.
`nemesis_ids` can only be non-empty today via `V2EntityBuilder`'s construction-time seed kwarg
(`builder.py:509-530`), never via real per-tick grudge-driven promotion.

This is a second, adjacent dormant-mechanism finding, out of this ticket's own scope (which is
`SocialBond.role` specifically) — disclosed in `docs/mechanics/07_social_political_dynamics.md` §3
(corrected in this same pass, since leaving §3 describing "per-tick" nemesis promotion while §2 now
discloses `role_set`'s own dormancy would be internally inconsistent within the same Certified Level 1
chapter) but not fixed. Flagged for a future ticket.

## Real design: derive role from sentiment inside `process_update()`, not a new upstream producer
Mirroring `check_nemesis_promotion()`'s shape (a separate producer function returning an `Update`,
requiring a real caller to invoke it every tick) would risk repeating the exact failure mode that left
it dead — a real, correct function with no live wiring. Chose instead to derive `role` directly inside
`RelationshipService.process_update()` (`relationships.py:16`), the confirmed real, live, per-update
apply-path (`src/engine/patches.py:558` is the real authoritative caller on every entity's social
update). This guarantees reachability by construction: any real event that already constructs a
`SocialBondUpdate(sentiment_delta=...)` (already real and live via `contracts.py`, `combat.py`,
`appraisal.py`, confirmed in Chapter 07 §1/§5/§7's own prior verification) automatically exercises the
new derivation, with no new caller needed anywhere.

**Threshold choice**: `FRIEND_SENTIMENT_THRESHOLD = 0.8` / `RIVAL_SENTIMENT_THRESHOLD = -0.8`, reusing
`appraisal.py`'s own real, already-established `bond.sentiment < -0.8` `TOTAL_DISTRUST` hard-reject
bound (`appraisal.py:73`) rather than inventing an unrelated number — an extreme sentiment swing is
already meaningful at this exact value elsewhere in the same codebase.

**Sticky/one-way-per-real-change semantics, required by an existing test**:
`tests/unit/social/test_relationships.py::test_process_update_role_set_none_preserves_existing_role`
(pre-existing, from `TCK-20260824-RELATIONSHIP-ROLE-FIELD`) asserts that a bond explicitly set to
`FRIEND` via `role_set`, followed by a familiarity-only update (`sentiment_delta` left at its `0.0`
default), must retain `role == FRIEND`. A naive "always re-derive role from current sentiment on every
`process_update()` call" design would break this test (mid-band sentiment → `NEUTRAL`). Fixed design:
only evaluate derivation when `b_upd.sentiment_delta != 0` (a real sentiment change actually
happened); a mid-band result leaves the existing `role` untouched rather than demoting it. Confirmed
this preserves both pre-existing role-related tests unmodified.

## Removal considered and rejected
Per the ticket's own alternative disposition (remove the dead field): rejected. A real, live,
already-shipped consumer exists (`PartyCompositionScorer` via the `FORM_PARTY` route) that has been
silently starved of real data since it shipped — removing the field would delete a real, intended
scoring dimension rather than fix its actual gap (the write path). Wiring is the evidence-supported
choice.

## Docs Requiring Update
- `docs/mechanics/07_social_political_dynamics.md` §2 (role write-path correction) and §3 (nemesis
  promotion dormancy disclosure, for internal consistency with §2's own new disclosure).

## Parity Ledger
New entry `SOC-248` (amends/extends `SOC-247`'s own scope — `SOC-247` documented the schema/merge
logic with zero real writers; `SOC-248` documents the new real writer). Added via
`tools/parity_ledger_writer.py::write_entry()`.

## Prior Work
- `TCK-20260824-RELATIONSHIP-ROLE-FIELD` — the ticket that added `SocialBond.role` and its one real
  consumer, explicitly scoped OUT any write-trigger and explicitly kept `role` independent of
  `nemesis_ids`/`grudge_history` by design — both constraints honored here.
- `tests/unit/social/test_relationships.py` — existing role tests (`test_social_bond_role_set_via_
  authoritative_update_only`, `test_process_update_role_set_none_preserves_existing_role`), both
  re-run and confirmed passing unmodified after this change.

## Risks and Open Questions
None outstanding — the wire-vs-remove decision is evidence-based (a real starved live consumer
exists), not a coin flip, per this ticket's own AC2.

## Anti-Drift Hazards
- Do not mirror `check_nemesis_promotion()`'s producer-function shape — it is itself dead code; derive
  inside the confirmed-live `process_update()` instead.
- Do not re-derive role unconditionally on every `process_update()` call — must gate on
  `sentiment_delta != 0` or the pre-existing `test_process_update_role_set_none_preserves_existing_
  role` test breaks.
- Do not touch `nemesis_ids`/`grudge_history`/`check_nemesis_promotion()`/`tick_place_attachment()` —
  a real, disclosed, but explicitly out-of-scope adjacent finding.
