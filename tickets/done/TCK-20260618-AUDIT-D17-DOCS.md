---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D17-DOCS
phase: done
date: 2026-06-18
tags: [audit, documentation, currency, staleness, mechanics-bible, engine-contracts]
---

# TCK-20260618-AUDIT-D17-DOCS

## Title
Audit D17 — Documentation Currency

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Audit key documentation files against current source code to identify stale or
inaccurate claims. The Mechanics Bible and Engine Contracts are authoritative
references used by all agents — stale entries silently mislead implementation work.

## Scope
- `docs/engine/known_limitations.md`
- `docs/mechanics/01_entity_anatomy.md` through `06_worldbuilding_foundation.md`
- `docs/engine/kernel.md`
- `docs/engine/authoritative_pipeline.md`
- Sample 3–5 claims per doc against current source code
- Produce `docs/audits/D17_documentation_currency.md` with staleness table per file

## Out of Scope
- Fixing stale claims (create separate tickets for divergences)
- Auditing archived docs or history docs
- Auditing every claim in every file — sampled spot-check only

## Acceptance Criteria
- [x] Each target doc has 3–5 claims verified against source
- [x] Staleness status: `current`, `stale`, or `uncertain` per claim
- [x] `docs/audits/D17_documentation_currency.md` produced
- [x] `audit_dimensions.md` D17 state updated to `done`

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent epic)

## Related Docs
- `docs/engine/known_limitations.md`
- `docs/mechanics/` chapters 01–06
- `docs/engine/kernel.md`
- `docs/engine/authoritative_pipeline.md`

## Related Code Areas
- `src/engine/kernel.py`
- `src/engine/pipeline.py`
- `src/engine/apply.py`
- `src/engine/combat.py`
- `src/core/state.py`
- `src/engine/rpg_depth.py`
- `src/engine/town_resolution.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/engine/world_dynamics.py`

## Assumptions / Open Questions
- "Stale" = the doc makes a specific verifiable claim that contradicts current code
- "Uncertain" = claim is qualitative or hard to verify without running the sim
- D02 already noted known_limitations.md was stale (blacksmith-only towns claim)

## Implementation Notes
All 9 target documents read. Source code verified for specific numeric and structural claims.
Findings span 4 tiers by severity (see detail file).

Prior finding from D02 investigation confirmed: `docs/engine/known_limitations.md` blacksmith-only
claim is stale (resolved by TCK-20260425-PH7-M3-RECOVERY but doc not updated).

## Test Summary
N/A — audit produces documentation, not code.

## Files Changed
- `docs/audits/D17_documentation_currency.md` — created with full staleness table
- `docs/audits/audit_dimensions.md` — D17 state updated to `done`
- `tickets/done/TCK-20260618-AUDIT-D17-DOCS.md` — moved here

## Completion Summary

**Result:** 9 stale claims, 25 current, 7 uncertain across 9 target documentation files.

**P0 finding — `authoritative_pipeline.md` severely stale:**
The 17-phase table is an earlier version. Current `pipeline.py:refine()` has 30+ named phases.
Phase names, numbers, and ordering in the doc do not match code. Any agent implementing
against this doc will use wrong insertion points and wrong phase names.

**P1 findings:**
1. `kernel.md` contains two conflicting phase tables — the first (6-phase, wrong names) appears
   before the correct 7-phase table.
2. `mechanics/01` biological thresholds are numerically wrong:
   - Hunger: doc says threshold=100.0 / 5 dmg; code: threshold=95.0 / +2 dmg
   - Sleep debt: doc says threshold=80.0 / -50% ATK/DEF; code: threshold=98.0 / +1 HP dmg
3. `known_limitations.md` Blacksmith-Only claim is stale — `TownResolutionSystem` handles inn,
   home, and tavern building types.
4. `mechanics/04` interruption margin: doc says `Profile_Resistance * 30.0`; code uses
   `profile.interruption_resistance * profile.resistance_multiplier` (configurable, not 30.0).

**Best-maintained doc:** `mechanics/02_combat_laws.md` — all damage formula and tactical
modifier values verified current.

**Follow-up tickets recommended:** See "Recommended Follow-Up Tickets" section of D17 detail
file — 4 P1 corrections and 4 P2 confirmations identified.
