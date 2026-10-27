---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS
artifact_type: investigation
tags: [architecture, documentation]
---

# Investigation — TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS

## Sources read (main 3533fde71)
- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` — the temporal axis proposal (the ticket's "docs/brainstorm/*temporal-axis-proposal.md").
- `agent-working/stored_artifacts/TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION/investigation.md`, "Axis test case" — the earlier test: the proposal's concerns (succession, aging/lifecycle horizons, demographic cohort cycling, institutional/commitment continuity) map to `succession`, `aging_death`, `demographic_cohort_cycle`, `commitment_betrayal`.
- `docs/plans/mechanism_tier_model_initiative.md` status block, which already states the conclusion without the evidence.

## Re-check against today's registry
The four mechanisms all exist in `registries/mechanisms.yaml`. Their declared `systems:` values:

| mechanism | layer | systems | depends_on |
|---|---|---|---|
| `succession` | entity | progression | aging_death |
| `aging_death` | entity | progression | none |
| `demographic_cohort_cycle` | region | world | none |
| `commitment_betrayal` | entity | social | none |

Three different declared `systems` (progression, world, social). I also recomputed the feasibility
investigation's four derived candidate sets (roots `combat_resolution`; `breakthrough_bonuses` and `xp_leveling`;
`crafting` and `equipment_scoring`; `reputation`, `commitment_pressure_consequences` and `goal_hierarchy`) with
`tools.mechanism_registry.registry.transitive_dependencies_of`: none of the four mechanisms is in any derived
set. So the investigation's wording "spread across the progression, social, and world candidate systems derived
above" is imprecise: there was no derived `world` set, and the four are outside all derived sets. The claim that
survives is the declared one above.

## Corrections to the ticket's own wording
The ticket names the three groupings "combat-adjacent, progression-adjacent, world/economy-adjacent". The
evidence names progression, social and world; none of the four is combat- or economy-adjacent.

## Conclusion
One axis (temporal) lands concerns on mechanisms declared under three different systems. Attaching the axis to
systems would need three entries for one axis (defeating "fewer declarations") or an arbitrary choice of one;
attaching to the mechanism is the level at which the concerns actually differ. This holds with or without a
`system` tier.
