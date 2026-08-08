---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION

## Context search (mandatory step, before any grep/file reads)
- `mcp__knowledge-search__search_docs` for "attack legality verify_attack_legality LegalityServiceV2
  friendly fire readiness combat" surfaced: `docs/engine/contracts/combat_contract.md`,
  `docs/guidelines/intentional_divergences.md` §2.9 (Legality Enforcement, LoS & Engagement),
  `docs/compliance/checklist.md` Z5, `TCK-20260430-PH5-COMBAT-LEGALITY-HARDENING` (historical).
- `graphify query` surfaced the real node graph around `LegalityServiceV2`, `CombatResolutionSystem`,
  `SimulationDomainLogic`, confirming `src/engine/legality.py:18` as the real service.
- Follow-up `search_docs` for readiness specifically surfaced `docs/engine/contracts/minimal_kernel.md`
  §5 ("Readiness Accumulation: Entities gain readiness based on their `readiness_speed` (passive)")
  and `docs/engine/contracts/simulation_kernel_contract.md` §5 — both real, active, P1 contracts.

## Methodology note (real probe, matching this session's established discipline)
All findings below are from live, instrumented `Kernel.tick_once()` runs against real compiled
worlds (`urban_political`, `dungeon_crawl`), never assumed or synthetic-only. Probe scripts lived
in the scratchpad, not the repo. `original_ids` (captured pre-tick) used throughout to avoid
conflating newly-spawned boss/elite entities with the real original population (a methodological
lesson carried over from `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`).

## Read `src/engine/legality.py` in full — the real decision surface
`LegalityServiceV2.verify_attack_legality()` (lines 187-288) checks, in order: state validity,
readiness (`>= 100.0` unless `is_opportunity_attack`), faction/friendly-fire, range, then LoS.
`verify_readiness()` (a separate, simpler helper) enforces the same `>= 100.0` law for generic
`ENTITY_ACT`. The scheduler (`src/engine/scheduler.py:71-74`) *also* gates non-brain work items
(including `ENTITY_MOVE`) at `readiness < 100.0 → skip`, per code comment "Action Readiness Law,
COMB-266" — though live tracing (below) shows ambient `WANDER` locomotion bypasses this gate via a
separate code path (`src/engine/movement.py`), draining readiness without needing it.

## Root cause 1 (dominant, ~55% of illegal verdicts in the original 330-sample probe): no readiness regeneration existed
Traced every `readiness_delta` assignment in `src/`: all were **negative** (movement `-move_cost *
terrain_cost`, attack `-100.0`, various skill/AoE actions `-10.0`/`-50.0`/`-100.0`, region
suppression `-5.0`) except one narrow, town-specific path: `REST` at an `inn`/`home` building
grants `+10.0` (`src/engine/town_resolution.py:96`). **No general per-tick passive regeneration
existed anywhere.**

This directly contradicts `docs/engine/contracts/minimal_kernel.md` §5's own documented law
("Readiness Accumulation... passive, based on `readiness_speed`") — the field `readiness_speed`
did not exist anywhere in `src/` (confirmed via grep), meaning the *code* had never implemented an
*already-documented, active, P1* contract. `docs/parity_ledger/combat_movement.yaml`'s own COMB-008
entry (P0, status `verified`) additionally and incorrectly claimed `ApplyPath.apply_generation`
"gains readiness" — false against real source. Both are now corrected (see Docs Requiring Update).

**Live trace, confirming mechanism** (`urban_political`, single tracked entity, WANDER mode):
readiness dropped 100→80→60→40→20→0 over 5 consecutive move ticks (moving through 2x-terrain-cost
tiles), then **stayed at exactly 0.0 for the rest of the 300-tick trace** while the entity
continued moving every few ticks (ambient WANDER locomotion does not require `readiness >= 100`
to execute, but still drains readiness as a side effect of each move — an inconsistency between the
"eligibility" framing in the docs and the real ambient-movement code path, noted but not
independently re-architected here; out of this ticket's own proportionate scope).

**Real probe result** (330 samples, `urban_political`, pre-fix): `verify_attack_legality()` FALSE
100% of the time, `INSUFFICIENT_READINESS` 55% (180/330), `FRIENDLY_FIRE_ILLEGAL` 45% (150/330).

## Root cause 2 (smaller, confirmed real bug, same subsystem): `intruding=False` hardcode
`RelationContext(intruding=False)` was hardcoded at both `src/engine/legality.py:238` and
`src/engine/tactical.py:168` (the tactical hostile-detection loop feeding target selection).
`RelationProjectionService.project_relation()` (`src/content_semantics/relation.py:100-104`)
treats an *explicit* `False` (not `None`) as proof of non-intrusion for
`contextual_intruder_groups`-classified relationships, forcing the label to `"neutral"`
**unconditionally**, regardless of real combat engagement:
```python
elif group_name == "contextual_intruder_groups":
    if context is not None and context.intruding is False:
        label = "neutral"
    else:
        label = "intruder"
```
Real content (`data/content/social/perspectives.yaml`) confirms this group is used:
`wild_beast_pack`'s perspective lists `contextual_intruder_groups:
[town_council, hero_guild, goblin_warband, bandit_company, orc_clan]`; `swamp_tribe`'s lists
`[hero_guild, town_council, merchant_league]`. Both factions were **structurally unable to ever
legally attack these targets**, independent of engagement state, before this fix. No real
territorial-intrusion detector exists anywhere in `src/` (confirmed via grep) — `intruding` was
never computed from real state at either call site, only ever hardcoded `False`.

**Not confirmed as the dominant real-corpus driver**: `urban_political`'s own original population
(town_council/merchant_league/hero_guild/bandit_company) contains no `wild_beast_pack`/
`swamp_tribe` entities, so this specific bug did not explain the observed 45%
`FRIENDLY_FIRE_ILLEGAL` samples in that world (0/4 explained by direct re-test with real content
faction pairs). It remains a real, confirmed, reproducible bug via direct code testing
(`RelationContext(intruding=False)` vs `intruding=None`/omitted for a
`wild_beast_pack`→`hero_guild` pair, mutually engaged: `"neutral"` vs `"intruder"`→hostile) —
landed alongside the readiness fix because it is small, same-subsystem, and discovered during the
same investigation, not a separate scope expansion.

## Ruled out (with real data, not assumed) before reaching the above
1. **Not hostile scarcity**: 100% hostile-presence-within-radius-10 in a naive probe — later found
   to be an *overcount* artifact of comparing raw `entity.identity.faction` enum values rather
   than real `faction_id` semantics (many allied entities carry different legacy enum values). A
   corrected probe (using `FactionSemanticsService.is_hostile_compat`) found only 8-27% of samples
   actually had a real hostile within radius 10, varying by world — a much smaller, honestly
   reported figure. This correction is disclosed for the record but does not change the ticket's
   own conclusion, since readiness/friendly-fire remained the dominant real blocker among the
   samples that *did* have a real hostile present.
2. **Not goal-competition loss**: `GoalKind.COMBAT_ENGAGE` wins the real goal competition in 325/330
   (98.5%) samples when available.
3. **Not a dead ATTACK code path**: `tactical.py`'s real ATTACK branch → `ActionRouter` →
   `CombatActions.execute_attack()` → `CombatResolutionSystem.resolve_attack()` confirmed intact
   with a real, non-None `context` at the real pipeline call site.
4. **Not `task.payload["target_id"]` never being set (methodological correction)**: confirmed via
   direct trace that `task.payload.get("target_id")` is never set for the real original population
   in either `urban_political` or `dungeon_crawl` across 600-tick runs — meaning `combat_engaged`
   (as computed at both `intruding`-hardcode call sites) is effectively always `False` in real
   gameplay. This is disclosed honestly as a genuine, further-reaching observation (the real
   targeting-state mechanism apparently does not use this field the way `legality.py`/`tactical.py`
   assume) but investigating *why* is a separate, deeper lead outside this ticket's own scope —
   not collapsed into a fix here per the Uncertainty Rule.

## Real fix implemented and re-verified
1. Added `CombatComponent.readiness_speed: float = 10.0` (`src/core/state.py`) and a passive
   per-tick regen block in `ApplyPath._compute_entity_changes` (`src/engine/apply.py`), mirroring
   the existing Stamina regen block.
2. **Found and fixed a latent, independent bug while wiring the above**: `EntityState.
   to_readonly()`'s `CombatComponent` reconstruction (`CORE-PERF-010`'s manual fast-path,
   `src/core/state.py`) used an explicit hardcoded kwarg list that omitted the new field, silently
   resetting any non-default `readiness_speed` back to the class default on every readonly-
   conversion pass — confirmed via direct before/after test; this would have silently defeated the
   whole fix (and will silently defeat any *future* `CombatComponent` field addition unless this
   pattern is remembered) had it not been caught here.
3. Removed the `intruding=False` hardcode at both call sites (Root Cause 2).
4. **Real re-verification** (`dungeon_crawl`, 600-tick run, same `is_attack_legal` probe
   methodology used to find the original 0% baseline): legal rate moved from confirmed 0% to a
   real, non-zero **1.3%** (2/159 real-hostile samples). A `readiness_speed` parameter sweep
   (10/20/30/50) showed no clearly superior single value — `INSUFFICIENT_READINESS` remained
   dominant at every tested value, since movement and attack draw from the same pool and an
   entity approaching a target can still arrive readiness-depleted even with passive regen active.
   **This is honestly disclosed as genuine, measurable progress, not a full resolution** — closing
   the remaining gap is a broader combat-pacing question (e.g. decoupling movement cost from
   attack-readiness cost) explicitly out of this ticket's own proportionate scope.

## Docs Requiring Update
- `docs/mechanics/02_combat_laws.md`: added §7 "Action Legality & the Readiness Gate" documenting
  the real, now-fixed mechanism (was previously entirely undocumented in the Mechanics Bible).
- `docs/parity_ledger/combat_movement.yaml`: corrected COMB-008's false "gains readiness" claim;
  added COMB-298 (readiness regen fix) and COMB-299 (`intruding` fix).
- `docs/guidelines/intentional_divergences.md`: added §2.36 (Bug Fix rationale class).
