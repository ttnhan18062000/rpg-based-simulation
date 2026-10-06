---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261005-LEGALITY-RAW-FACTION-EQUALITY-FALLBACK-IS-DEAD-BUT-LATENT
phase: open
date: 2026-10-05
tags: [engine, combat]
---

# TCK-20261005-LEGALITY-RAW-FACTION-EQUALITY-FALLBACK-IS-DEAD-BUT-LATENT

## Title
`legality.py`'s raw `identity.faction` equality fallback never fires on corpus content, but it would decide
hostility by a different predicate from tactics for any faction with no perspective and no relationship edge

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Residual from `TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE`, which was closed as
a measured non-defect: on four corpus worlds, each run twice (values), **0 entity pairs** had tactics and legality
disagree, and the `FRIENDLY_FIRE_ILLEGAL` verdicts are the opportunity-attack scan's routine filter.

That investigation also established **`has_clean` was never false on corpus content**. So
`legality.py:252-272`'s fallback, `if attacker.identity.faction == target.identity.faction: FRIENDLY_FIRE_ILLEGAL`,
taken only when no perspective and no relationship edge exists, is **dead code on the current corpus**.

**Why it is still a hazard.** Tactics (`tactical.py:249`) calls `is_hostile_compat` unconditionally, and that
function carries its own fallback. Legality would use raw enum equality instead. For any future faction with no
perspective and no edge, the two would answer "is this hostile?" by **different predicates**. That is exactly
the divergence the parent ticket set out to find, latent rather than live. It is also residue of the raw legacy
faction comparisons `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` (#333) was meant to remove.

**Why P3.** Nothing fires today. The spawn-path ticket
(`TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER`) will reduce the
legacy-bucket population further, so the trigger becomes rarer, not likelier.

## Scope
1. **Before any code: route "which predicate is authoritative" to `world-rule-catalog-design`.** It is a rule
   question, governed by the Mechanics Bible's hostility definition (`02_combat_laws` §7 noted by the parent
   ticket). Ask for a recommendation plus what would refute it.
2. Once ruled: remove the raw-equality branch so legality and tactics share one predicate, with a test that builds
   a faction with no perspective and no edge and asserts both sides agree.
3. Confirm with a corpus run that behaviour is unchanged (the branch is dead, so it must be).

## Out of Scope
- The opportunity-attack scan's cost: it asks legality about every adjacent neighbour each tick (583 refusals in
  4 x 2000 ticks). Cost, not correctness, and small. Recorded only.
- The spawn-path faction fix.

## Acceptance Criteria
- [ ] Predicate authority ruled via the designer before implementation.
- [ ] One hostility predicate shared by tactics and legality; a no-perspective, no-edge faction test agrees.
- [ ] Corpus behaviour unchanged, as values.

## Related Tickets
- `TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE` — parent, non-defect.
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` (#333) — the sweep this is residue of.
- `TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER`.

## Related Docs
- `docs/mechanics/02_combat_laws.md` §7 — hostility.

## Related Stored Artifacts
- The parent ticket's `investigation.md` and `ff_origin.py` probe.

## Related Code Areas
- `src/engine/legality.py:252-272`; `src/engine/tactical.py:249`; `src/content_semantics/faction.py:186`
  (`is_hostile_compat`, Lane B's hold).

## Assumptions / Open Questions
- **Lane.** Lane A, low priority. Needs a hold on `faction.py` only if the fix lands there.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
