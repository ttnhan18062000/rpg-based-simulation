---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Regional Sovereignty Runtime Contract

**Source:** `src/world/regions.py`, `src/engine/world_dynamics.py`, `src/world/influence.py`, `src/engine/town_resolution.py`, `src/engine/place_tax.py`; `src/world/regional_sovereignty.py` is an unwired orphan (see below)
**Related docs:** [docs/mechanics/regional_sovereignty.md](../mechanics/regional_sovereignty.md) (topology/build-time), [threat_and_consequences_contract.md](threat_and_consequences_contract.md) (influence thresholds), [docs/simulation/domains/adventure_contract.md](../simulation/domains/adventure_contract.md) (routing decisions)

---

## Purpose

Regional sovereignty governs faction control at runtime — who owns a region, what that ownership means for entities in the region, and how control changes. This document covers **runtime behavior only**. For the build-time topology (how region borders are defined, which regions can be adjacent, declarative sovereignty setup), see `docs/mechanics/regional_sovereignty.md`.

---

## What sovereignty means at runtime

A region is under faction sovereignty when one faction's influence ≥ +50 (player/hero faction) or ≤ −50 (monster/enemy faction). See [threat_and_consequences_contract.md](threat_and_consequences_contract.md) for the influence threshold mechanics.

Sovereignty has three runtime effects:

| Effect | Who it applies to | Mechanism |
|---|---|---|
| Taxation | A sale or a wage paid in a building the faction's region holds | A share of the transaction (EXCH-02), not a periodic levy |
| Sovereignty debuffs | Entities of another faction in a region with `suppression_active` | Stat modifiers applied by `town_resolution.py` |
| Town access lock | Entities of opposing faction | Structural gate on service opportunities |

---

## Two independent ownership writers (deliberate, deferred consolidation)

`owner_faction_id` is written by two separate code paths, not one:

- `FactionInfluenceService.process_influence_shift()` (`src/world/influence.py`) — triggered only
  when a death occurred this tick (`src/systems/lifecycle_systems/lifecycle.py:298`, gated on
  `if recent_deaths:` at `:294`).
- `WorldDynamicsSystem.resolve_dynamics()`'s own ownership block (`src/engine/world_dynamics.py`)
  — an unconditional sweep over every region, every tick, against final settled influence
  regardless of cause, running earlier in the same tick's pipeline
  (`world_dynamics` phase precedes `lifecycle`).

As of `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT`, both paths read the same
`CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD` constants from `src/world/influence.py`, so they can no
longer disagree numerically. **Consolidating onto one writer was investigated and deliberately
deferred** — the two paths differ in trigger and phase position, not just implementation, and
naively consolidating would delay death-driven flips by one tick (a determinism/ordering change
requiring its own investigation). Tracked separately:
`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`. Do not assume this is an oversight —
it is a scoped, documented decision.

### Precedence, resolved 2026-10-03 (`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`)

That ticket closed **decision-only**: two writers stay, consolidation stays deferred, and the
following four facts — previously undocumented — are now part of this contract.

1. **Precedence is writer-2-overrides-writer-1, and it is not a split-brain fact.** Both paths write
   *the same field of the same staged `WorldUpdate`*. `lifecycle.py:303-307` merges
   `process_influence_shift`'s update into the `world_dynamics` entry, and `WorldUpdate.merge`
   (`src/core/updates.py`) resolves `owner_faction_id_set` as **other-wins**, so the death-gated path
   silently overrides the sweep. The apply path then writes exactly one value. The accurate
   description is *an unordered, undocumented precedence between two producers of one field* — **not**
   "one durable fact held with two conflicting live values", a framing that was measured and found
   false.
2. **The unconditional sweep evaluates last tick's influence, not this tick's.**
   `src/world/influence.py` is the only producer of `WorldUpdate.influence_delta` in `src/`, and it
   runs at the `lifecycle` phase — 13 phases *after* its only consumer in
   `world_dynamics.py`. Measured at that exact read: 24,000 executions, **0 nonzero**. A death's
   influence therefore cannot reach the sweep in the same tick, so a sweep-driven flip always lags its
   causing death by at least one tick.
3. **The death-gated writer emits no `SOVEREIGNTY_SHIFT`.** Only the `world_dynamics` block emits it.
   Any ownership flip performed by `process_influence_shift` is therefore **invisible** to
   `WorldEmergencePhase` and to agent observability. This is latent rather than live only because that
   writer is measured never to write ownership (point 4) — which is also why `WORLD-107`'s
   observability claim is not currently false.
4. **The death-gated writer is measured inert for ownership.** Across ≈48,000 region-ticks in four
   corpus worlds it was called ~230 times, produced ~80 influence-delta updates, and made **zero**
   ownership writes; the sweep made 3. Both observed durable flips were sweep-only. **Scope limit:
   that is a true zero for this corpus, not a proof of impossibility** — a constructed scenario drives
   both writers in one tick, so the overlap path is live, merely unreached. Counts are
   order-of-magnitude: the runs predate the `audit_mode` discipline that `INFRA-273` requires.

Evidence: `agent-working/staging_artifacts/TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION/`
(`investigation.md` §3-§5b, `runtime_evidence_regional_sovereignty.md`). The contract review in §3
found **no** obstruction to moving settlement after `lifecycle` should consolidation ever be taken up:
Sovereignty-ordering is `action_routing`-local, no test pins the phase order, and no intervening phase
reads `owner_faction_id`.

---

## Taxation — a share of a sale or a wage (EXCH-02)

Corrected 2026-10-26 (TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS; main 3533fde71). This section used to attribute taxation to `regional_sovereignty.py`; that class is never called.

**Today's rule** (owner decisions 51 and 58, EXCH-02 in `docs/world_rules/material-economy/economy-exchange.md`; per-head levy removed in #536, divergence 2.108): when coin changes hands in a building, a tenth of the amount, rounded down per transaction, moves from the payer's purse to the treasury of the faction holding the building's region, in the same typed transfer. Someone who earns or sells nothing pays nothing; a region nobody holds taxes nothing. Source: `src/engine/place_tax.py` (`tax_on`), reached from `src/engine/shop_sale.py` (a sale) and `src/engine/work_shift.py` (a wage). A periodic levy on everyone present is not a tax this world uses.

**Unwired orphan:** `RegionalSovereigntyService.process_taxation` (`src/world/regional_sovereignty.py`) has zero callers in `src/`, `tests/` or `tools/`. It is registered as `regional_levy_and_conquest_debuffs` (`state: orphan`) in `registries/mechanisms.yaml`. What it *would* do if it were called, kept for the record: every **100 ticks**, tax a hero 2.0 gold and each functional building 10.0 gold, paid to the owning faction treasury through a `ResourceTransferIntent`, paying what they have with no debt. That is the retired per-head levy shape; it is not the live rule.

---

## Sovereignty debuffs

**Today's rule:** `src/engine/town_resolution.py` (`TownResolutionSystem.resolve`, wired in the `town_resolution` phase at `src/engine/pipeline.py:339`). In a region with `suppression_active`, an entity whose faction is not the region owner takes ATK -20%, DEF -20% and SPD -10% (`atk_delta`, `def_delta`, `speed_delta`).

**Unwired orphan:** `RegionalSovereigntyService.apply_sovereignty_debuffs` (`src/world/regional_sovereignty.py`) is never called, and returns an `EntityUpdate` without populating the debuff fields. What it declares, kept for the record: a monster-controlled region (influence ≤ −50), non-monster faction entities, ATK × 0.8, DEF × 0.8, SPD × 0.9 (`CONQUERED_ATK_DEF_MOD`, `CONQUERED_SPD_MOD`). Do not treat these constants as the live numbers.

---

## Movement and borders

**There is no runtime movement-blocking border gate.** Sovereignty does not prevent entities from crossing region borders at the movement level.

Hostile-region avoidance is a **routing decision** — entities avoid monster-controlled regions because:
1. `RegionThreatClassifier` labels them HIGH or EXTREME threat
2. The adventure domain applies a −2.0 blocker penalty to routes through high-threat regions
3. The entity may choose a different route based on its personality (caution bias)

An entity CAN cross into a hostile region if its routing scores it as worthwhile (e.g., a combat-seeking warrior with high bravery bias). Sovereignty does not hard-block this.

---

## Town access lock

When a region is conquered (influence ≤ −50):
- A stronghold structure is spawned at the region centre
- Town service opportunities are faction-filtered by `RequirementsFilter` (see [opportunity_providers_contract.md](opportunity_providers_contract.md))
- Entities of the opposing faction see no service opportunities in that region

Liberation (influence ≥ +50) removes the stronghold and restores open town access.

---

## Cross-region movement rules — `regions.py`

`regions.py` provides the runtime adjacency graph (which regions are reachable from which). Key rules:
- Movement between non-adjacent regions is not permitted (checked before movement resolution)
- Adjacency is symmetric (if A→B is valid, B→A is valid)
- Region graph is static at runtime (built at world generation, not modified during simulation)

---

## Regression tests

- `tests/unit/resource/test_tax_and_upkeep.py` — the live rule: a tenth of a sale or wage rounded down, nobody taxed where nobody holds the ground, no periodic levy (an idler in a held town is never taxed)
- `tests/unit/world/test_suppression.py`, `tests/unit/world/test_regional_consequences.py` — the suppression action-legality gate (`REGIONAL_SUPPRESSION`). No test found asserts the stat debuff of `town_resolution.py`.
- `tests/integration/world/test_long_run_stability.py` — long-run memory and population stability and determinism parity. It does not cover taxation, gold transfer or the faction lock (corrected 2026-10-26; this line used to cite it for "taxation cadence, gold transfer correctness, faction lock").
- `tests/unit/worldmodules/test_modules.py` — adjacency graph validity, cross-region movement gate
- Note: the stat debuff in `town_resolution.py` has no test of its own

---

## Extension rules

1. The live debuff is `town_resolution.py`'s `suppression_active` branch. `apply_sovereignty_debuffs()` in `regional_sovereignty.py` is an unwired orphan with different numbers; wiring it would revive or duplicate a rule, which is a behaviour change (document it in intentional_divergences.md first).
2. To add a new faction type: extend the faction alignment check in taxation and town access lock. The influence threshold (±50) is configurable per-region in the build config.
3. To add runtime border gating: add a movement pre-check in the movement resolution phase. This would be a significant behavior change — document in intentional_divergences.md and update the adventure routing contract.
4. Taxation amount (2.0 gold / 10.0 gold) is currently hardcoded. If configurable taxation is needed, move these constants to world config.
