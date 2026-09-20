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

# Investigation — TCK-20260920-MECHANISM-CONTRADICTED-VERDICT-TRIAGE

## Enumeration

12 `contradicted`-verdict mechanisms found in `registries/mechanisms.yaml`. 6 dated 2026-09-16/17/
19 (pre-existing): `tactical_decision`, `readiness_speed_scaling`, `regional_trauma`,
`demographic_cohort_cycle`, `calamity_intensity`, `camp`. 6 dated 2026-09-20 (today's own batches
1/2, already resolved as part of their own batch): `breakthrough_bonuses`, `commitment_betrayal`,
`quest_generation_sourcing`, `betrayal_siege_war`, `chronicle`, `equipment_scoring`.

## Coverage check, per pre-existing mechanism

- `tactical_decision` → `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (done), child
  of `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`. Adequate.
- `readiness_speed_scaling` → `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`
  (done, root cause) + `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (open, shared
  cause follow-up), both children of the same epic. Adequate.
- `regional_trauma` → `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (open). Adequate.
- `demographic_cohort_cycle` → no dedicated ticket found anywhere in `tickets/todos/` or
  `tickets/done/`; only an informal cross-reference inside
  `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`'s own prose. **Gap. Filed.**
- `calamity_intensity` → `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (open), but its own
  framing (a reachable-but-starved trigger condition) is now known incomplete — batch 2 found the
  producer has zero real callers at all, a stronger, different-shaped defect. **Updated, not
  duplicated.**
- `camp` → no dedicated ticket found; only a shared cross-reference to
  `docs/plans/world_composition_precondition_gap_finding.md`, unlike its two siblings
  (`lair`-trauma, `calamity_intensity`) which each have their own ticket. **Gap. Filed.**

## `information_trust_deception`

Routed here per peer's explicit instruction: a `verified` note ("flag-gated off") whose best
real-candidate evidence (found in batch 1) doesn't match — a wrong-verdict shape, not a binding
gap. Filed as its own ticket rather than resolved in passing.

## Doc update

`docs/plans/world_composition_precondition_gap_finding.md` extended with `camp` (#5) and
`demographic_cohort_cycle` (#6) as confirmed instances of its own already-established pattern,
matching the 3 already-documented instances' own level of detail.
