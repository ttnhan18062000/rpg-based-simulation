---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION

## Per-mechanism findings (see `registries/mechanisms.yaml`'s own `verified` blocks for full detail)

**World (12)**: `campaigns` → `CampaignOrchestrator` (real caller only in `tools/calibrate_simq.py`,
outside `src/` — a docstring usage example in `orchestrator.py` itself is not a real caller,
avoided that trap). `chronicle` → state corrected done→orphan, `ChronicleCompiler` (corroborated by
an independently-found, already-filed `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-
POPULATED-IN-PRODUCTION`). `opportunity_rumor_seeds` → `WorldOpportunityPressureService` +
`RumorSeedService`, both called from the same flag-gated phase. `calamity_intensity` → attempted
bind, reverted after independent re-check confirmed zero real callers for
`apply_calamity_consequences()` — a real contradiction with the entry's own pre-existing note,
flagged not resolved. `world_boss_spawn` → `BossService.check_for_boss_spawn()`. `world_generation`
→ `WorldCompiler` (static-method call pattern, not instantiation — an initial instantiation-style
grep found nothing). `equipment_scoring` → state corrected done→orphan, `EquipmentService` (real,
well-built, zero external callers anywhere). `inventory_trade_conservation` → `crafting` →
both share `ResourceTransactionResolver` (crafting is a judgement call: one branch inside a single
method, below current binding granularity). `buildings` → `BuildingState` (the data class, not
`BuildingRegistry`, itself found to be a separate unused orphan). `town_services` → `ShopSystem` +
`BlacksmithSystem` (both real; `InnAction` checked and found to have zero real callers, contradicting
this entry's own prior note — flagged). `building_sabotage` → `BuildingSabotageSystem`.

**Faction (5)**: `betrayal_siege_war` → state corrected done→partial, `MilitaryConflictPhase` (real);
the "betrayal" half (`Betrayal(FactionDirective)`) has zero real constructors — a possible Split
candidate, flagged not performed. `social_contracts` → `diplomatic_actions.py::handle()` +
`compute_common_enemy_pairs()` (the real diplomatic-transitions phase, distinct from
`FactionDecisionPhase`). `reputation` → `ReputationService` (faction-facing, distinct from the
commitment-specific reputation module). `cross_episode_grief_nemesis` → `grief_urgency.py`
(file-level; both `GriefUrgencyImporter` and `NemesisRelationImporter` are this one mechanism's own
concern). `country_lifecycle` → `FactionDecisionPhase` (this entry's own pre-existing citation,
independently re-verified).

**Region (4)**: `regional_trauma` → `RegionalConsequenceService` (the natural-decay half this
entry's own note already cites). `city` → `RegionState` (the data class, matching this entry's own
"City-state IS RegionState" claim). `camp` → `CampState` (matching this entry's own claim). `ruins_
mines_battlefields` → state corrected partial→gap, applying this entry's own already-stated
conclusion ("not a separately-coded mechanism... Gap"), no fresh investigation, left unbound.

**Group (2)**: `party_formation` → `GroupPhase` ("coordinating group formation, updates, and
removals" per its own docstring; internally dispatches to `GroupSystem`, several other files
reference `GroupSystem.update_groups()` only in comments — checking `GroupSystem` alone would have
wrongly concluded zero callers). `guilds` → `GuildAction` (real, `ENABLE_GUILD_QUEST_GENERATION`
defaults ON; sibling `GuildIntelSystem` checked and found to have zero real callers, flagged).

## The calamity_intensity self-correction, in detail

Attempted binding `calamity_intensity` to `CalamityService.apply_calamity_consequences()` on the
strength of its own pre-existing (2026-09-17) verified note's confident claim ("the sole real
producer of region.calamity_intensity"). Running `mechanism_state_caller_check.py` immediately
flagged `state_with_zero_callers`. Independently re-checked rather than trusted the checker blindly
either: `grep -rn "apply_calamity_consequences" src/` finds only its own definition and one
unrelated comment in `displacement.py`. `CalamityService.process_world_dynamics()` (the method
actually called, from `world_dynamics.py:133`) only reads `region.calamity_intensity`, never writes
it. Confirmed: the checker was right, the pre-existing note's framing ("correct, wired code, defeated
by real-world data never meeting its trigger precondition" — implying reachability) understates the
real finding (never called under any circumstances). Reverted the binding; flagged the contradiction
on the entry for the roadmap session rather than overwriting the pre-existing `verified` block
unilaterally.

## No forks dispatched this batch

Given batch 1's read-only-instruction violation and the resulting concurrent-write race, all 23
mechanisms were investigated directly rather than delegated, avoiding a repeat.
