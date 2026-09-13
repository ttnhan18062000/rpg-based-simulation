# Investigation — TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY

## Re-verified origin claim
`region_data`/`enemy_data` still empty at every real `CapabilityContext` construction site.
`travel_regions` still has zero production construction sites — unchanged since the origin ticket.

## Belief-source search (never world truth, per instruction)

Two real, live-code candidates found. Both confirmed unreachable in real runs today.

**Chain 1 — lead-belief path**: `GuildAction.visit()` → `entity.strategic.leads` →
`BeliefCycleSystem.process_observation()` (`src/systems/strategic_systems/intelligence.py:416`,
the sole real caller). Blocked twice:
1. `ENABLE_GUILD_QUEST_GENERATION`'s default doesn't propagate to `state.feature_flags`
   (`TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS`) — no lead is
   ever granted in a real run.
2. Even with a lead present, `process_observation()` sits after a `float()` parse on `lead.detail`
   that throws for every guild-produced lead's narrative-text format
   (`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`) — confirmed by reading the
   exact code path in `intelligence.py`.

**Chain 2 — combat-risk belief path**: `CombatEngagementPhase.apply()`
(`src/domains/combat_engagement/phase.py`) writes a real, tested `BeliefEntry`
(`id="combat_risk"`, `claim=<RiskLevel>`, `certainty=<death_risk>`) for the actor's own risk from
the nearest hostile. Gated `ENABLE_COMBAT_ENGAGEMENT`, default `OFF`
(`TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`, open, pre-existing, unrelated to this batch).
Shape mismatch even if the flag were on: single per-actor scalar, not the per-`enemy_id`/
per-`region_id` keyed dicts `enemy_data`/`region_data` need.

`KnowledgeFact` (origin ticket's own unproven third candidate): confirmed separately at zero real
writes.

## Disposition
Do not wire either source now — both would produce code that compiles, has real test coverage, and
never fires in a real run. Stays `BLOCKED` on the two named chains, not `DONE`.
