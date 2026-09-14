---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY
phase: done
date: 2026-09-14
tags: [world]
---

# TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY

## Title
`state.maturity >= 50` gates both Lair-occupant spawning and world-boss spawning behind a ~50,000-tick requirement, against a corpus whose runs are 200-5,000 ticks — the user has reversed the prior "accepted long-horizon divergence" disposition and wants this treated as a reachability defect

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
**Ordering conclusion, recorded here so a future reader cannot open the gate without hitting the
prerequisite: the maturity/trauma gate is not the first thing to fix here — it's the last.** A
real, previously-undiscovered defect was found waiting behind it (`difficulty_tier=5` silently
produces tier-1 stats for both world bosses and Lair occupants — see investigation.md's own Defect
1), and opening the gate before fixing that defect would make a rare, hard-won encounter into a
trivial one-shot kill — actively worse than the mechanism staying dormant. **Real sequencing: fix
the tier-5 stat defect first, verify a spawned boss/occupant is actually formidable, and only then
make the gate itself reachable.**

`docs/plans/deferred_tuning_decisions_register.md`'s own D-05 entry: `state.maturity` increments
+1 per 1000 ticks (`src/world/calamity.py::MATURITY_INTERVAL`), and both Lair-occupant spawning and
`BossService.check_for_boss_spawn()` (`src/world/boss.py::BOSS_SPAWN_THRESHOLD = 50.0`) require
`state.maturity >= 50` — confirmed via direct read, matching D-05's own claim exactly. That gate
needs ~50,000 ticks to ever open. `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` (done) originally
closed by accepting this as a disclosed long-horizon divergence — a deliberate design choice that
lairs/world bosses are late-game-only content.

**The user has reversed that disposition.** Per D-05's own "wiring-first rule" test ("if this number
stays exactly as it is, does the mechanism still execute in a real run? If no, it is not a deferred
tuning decision — it is a reachability defect"): the honest finding may be that lairs and world
bosses never spawn in any real run at all, which is a feature not delivering, not a number being
intentionally large. The user wants both feature families made reachable.

## Scope
- **Investigation first, no implementation until peer has reviewed what the gate actually needs.**
  (Investigation phase — complete.)
- Determine whether `state.maturity`'s threshold (`50.0`) or its increment rate
  (`MATURITY_INTERVAL = 1000` ticks) is the wrong half. (Answered: the threshold — see
  investigation.md and D-05.)
- **Build phase, per peer's explicit fix decision after investigation review**, in this order:
  1. Define `DIFFICULTY_TIERS[5]` (was undefined, silently falling back to tier 1).
  2. Register `ancient_core` (was unregistered, silently dropped on inventory add).
  3. Lower `BossService.BOSS_SPAWN_THRESHOLD`/add `BOSS_SPAWN_TRAUMA_THRESHOLD` — wiring, not
     tuning; values recorded as provisional.
  4. Prove the whole chain end to end in one real, unmodified-corpus-world run — not three
     isolated unit tests.
- See plan.md for the full build detail and test_plan.md for verification.

## Out of Scope
- The faction war declaration reachability question (D-06) — sequenced separately, own ticket
  (`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`), stays untouched until this ticket
  landed.
- Balance/tuning work generally — the new tier-5/threshold values are explicitly provisional
  wiring numbers, not a tuned late-game difficulty curve.
- `EntityGenerator.spawn_stronghold()`'s own `state.maturity`-scaled stat term (same root cause,
  found in the original `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` survey) — untouched.
- The Lair-occupant side's own region-specific trauma-accrual gap (the one corpus world with a
  real `LAIR`-kind Place has a region that records zero combat deaths ever) — the shared gate
  itself is fixed and proven reachable at the unit level, but not proven end-to-end for this path
  in a real run; tracked separately as `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`.
- The calamity-intensity system being inert, and the `ItemRegistry` dual-class divergence found
  along the way — filed as their own tickets, not investigated further or built here.

## Acceptance Criteria
- [x] A real, evidence-backed answer on whether the maturity threshold or increment rate (or both)
      is the actual blocker, with a concrete corrected value proposed if it's genuinely a one-value
      fix. (Threshold; `2.0`/`8.0`, provisional.)
- [x] A real check (not assumption) of whether Lair-occupant/world-boss spawn logic itself is
      correct once the gate is passed — constructed or driven past the gate in a real test/run, not
      just traced statically. (Both defects found and fixed: tier-5 fallback, `ancient_core` drop.)
- [x] Findings brought to peer/user review before any implementation proceeds.
- [x] Fix built only after that review, in the peer-specified order.
- [x] Proven end to end in one real, unmodified corpus-world run: a `world_boss` spawns, is
      genuinely formidable, and carries loot that survives the real inventory-add path.

## Related Tickets
- `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` (done — the ticket that originally accepted
  this as a long-horizon divergence; disposition reversed by this ticket, see
  `docs/guidelines/intentional_divergences.md` §2.56/§2.57)
- `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` (filed alongside this one, from the same
  user decision — stays untouched until this ticket landed)
- `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` (filed, small follow-up, not built)
- `TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT` (filed, small follow-up, not built)
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (filed, standard-tier follow-up, not
  investigated further or built)
- `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (filed, standard-tier
  follow-up, not investigated further or built)
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (filed, the Lair-occupant side's own
  remaining reachability gap, not built)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` § D-05 (resolved by this ticket)
- `docs/world/raid_boss_camp_contract.md` § Boss (spawn conditions)
- `docs/guidelines/intentional_divergences.md` §2.56 (superseded for the boss/Lair gate) and §2.57
  (this ticket's own resolution entry)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY/` (investigation.md,
  plan.md, test_plan.md — all filled in)

## Related Code Areas
- `src/world/spawn_config.py` (`DIFFICULTY_TIERS[5]`, new)
- `src/world/boss.py` (`BossService.check_for_boss_spawn()`, `check_for_lair_spawn()`,
  `BOSS_SPAWN_THRESHOLD`, `BOSS_SPAWN_TRAUMA_THRESHOLD` — new named constant)
- `data/content/world/items.yaml`, `src/core/items.py` (`ancient_core` registration)
- `tests/unit/world/test_boss_gate_reachability.py` (new)

## Assumptions / Open Questions
- Whether "50" was ever actually tuned, or whether it's an arbitrary placeholder that was never
  revisited — answered: no evidence it was ever tuned against real run lengths; treated as a
  reachability defect per the user's own decision.

## Implementation Notes
**2026-09-14: investigation complete, no code changed — both peer-flagged gaps are now closed,
bringing the full picture back for the fix decision. Ticket stays BLOCKED pending that decision,
not yet ready to close.** Full detail in staging_artifacts/investigation.md. Summary:
- **Ordering conclusion**: fix the tier-5 stat defect first, verify formidability, only then open
  the gate — opening the gate first would ship a broken, anticlimactic encounter.
- **Defect 1**: `difficulty_tier=5` (used by both world-boss and Lair-occupant spawning) silently
  falls back to tier-1 stats — `DIFFICULTY_TIERS` only defines tiers 1-4. Verified empirically: a
  "world boss" spawns with `hp=50/atk=10/level=3`, weaker than an ordinary tier-4 monster
  (`hp=200/atk=30/level=11`). Named explicitly as the 4th instance this week of the same
  silence-as-failure-mode family (dead `spatial_grid` optimization, a bare-except lead-parse
  swallow, a trace recorder logging SUCCESS for a no-op).
- **Defect 2 (now chased to a definitive answer)**: the world boss's own signature loot
  (`item_id="ancient_core"`) does NOT crash — it is silently dropped during inventory add
  (`src/core/inventory.py::apply_update()`'s `if not defn: continue`, via the real, non-raising
  `src.core.items.ItemRegistry` that the actual inventory/equipment pipeline uses, not the
  raising `src.core.registries.ItemRegistry` initially assumed). A real second defect (a fixed,
  formidable world boss would still drop nothing today), but not a build prerequisite for Defect 1.
- **Defect 3**: both halves of the gate's own AND conjunction are independently unreached in a
  real 2000-tick run — `state.maturity` reached `1` (need `≥50`), `trauma_score` peaked at `9.92`
  (need `≥20.0`). Not "one large number."
- **Finding 4/5 (now measured)**: a second, maturity-independent `world_boss` spawn path exists
  (`CalamityService`), correctly tiered, gated on `tick % 5000 == 0` AND some region's
  `calamity_intensity > 0.3`. A real, instrumented 5000-tick simulation (`frontier_living_world`,
  seed=42) found `calamity_intensity` never left `0.0` in any region for the entire run — this
  path is itself unreached in practice, independent of the maturity/trauma gate, and never spawns
  Lair occupants regardless. Also found (filed as two small follow-up tickets, not fixed here): an
  unused `CALAMITY_RANDOM_CHANCE` constant, and a real drift between two parallel `_BOSS_KINDS`
  observability constants.

**2026-09-14, build phase**: peer reviewed the investigation and gave an explicit fix decision —
build in order (tier 5 → `ancient_core` → gate thresholds → prove end to end), do not skip to the
gate. All four steps built; see plan.md for the full detail. Summary:
- `DIFFICULTY_TIERS[5]` added: `hp=6.5x, atk=4.5x, def_stat=3.5x, xp=8.0x, gold=6.5x, level 14-22`.
- `ancient_core` registered in both the authoritative catalog (`data/content/world/items.yaml`) and
  `src/core/items.py`'s default dict.
- `BossService.BOSS_SPAWN_THRESHOLD`: `50.0` → `2.0`. New named constant
  `BOSS_SPAWN_TRAUMA_THRESHOLD` (replacing a duplicated inline `20.0` literal): `8.0`.
- Proven end to end: real 3000-tick `Kernel.tick_once()` run on unmodified `frontier_living_world`
  (seed=42) — `world_boss` spawned at tick 2101, `hp=325/atk=45/def=17/level=19`, carrying
  `ancient_core`; a direct `InventoryService.apply_update()` check confirmed the loot survives the
  real add path.
- **Known remaining gap**: the Lair-occupant side wasn't proven end-to-end — the one corpus world
  with a real `LAIR`-kind Place has a region with `0.0` `trauma_score` across a full 5000-tick run
  (zero combat deaths there). Filed separately (`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`)
  rather than silently left unmentioned or force-fit into this ticket's own scope.
- `docs/plans/deferred_tuning_decisions_register.md` D-05 and
  `docs/guidelines/intentional_divergences.md` §2.56/§2.57 updated to record the resolution and the
  provisional-values framing.

## Test Summary
7 new tests in `tests/unit/world/test_boss_gate_reachability.py`, all passing. Existing
`tests/unit/world/test_difficulty_scaling.py` (15) and `tests/unit/world/test_world_dynamics.py`
boss/Lair tests confirmed still passing unchanged. Full scoped run (167 tests total, spanning the
new tests plus difficulty scaling, world dynamics, registry bridge/parity/cross-reference,
migration proof, runtime content mode, registry bootstrap modes, content-catalog integration, and
inventory serialization) — all green. See test_plan.md for the exact command and full breakdown,
including the real end-to-end simulation proof.

## Files Changed
- `src/world/spawn_config.py` — added `DIFFICULTY_TIERS[5]`.
- `src/world/boss.py` — lowered `BOSS_SPAWN_THRESHOLD`, added `BOSS_SPAWN_TRAUMA_THRESHOLD` named
  constant, replaced both inline `20.0` trauma literals with the new constant.
- `data/content/world/items.yaml` — registered `ancient_core`.
- `src/core/items.py` — registered `ancient_core` in the default dict.
- `tests/unit/world/test_boss_gate_reachability.py` — new, 7 tests.
- `docs/plans/deferred_tuning_decisions_register.md` — D-05 resolved.
- `docs/guidelines/intentional_divergences.md` — §2.56 marked superseded (boss/Lair gate only), new
  §2.57 recording the resolution.
- `tickets/todos/TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT.md`,
  `TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT.md`,
  `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES.md`,
  `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS.md`,
  `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES.md` — new follow-up tickets, filed not built.

## Completion Summary
Investigation found three real, compounding silent defects behind the maturity/trauma gate; peer
reviewed the findings and gave an explicit fix order. All three defects fixed (tier-5 stat
fallback, `ancient_core` loot registration, gate threshold values), and the whole chain proven end
to end in one real, unmodified-corpus-world simulation, per the peer-specified acceptance bar. The
Lair-occupant side of the same gate is fixed and unit-tested but not proven end-to-end in a real
run, due to a separate, region-specific trauma-accrual gap — filed as its own ticket rather than
silently left unresolved. Five other real findings surfaced along the way were filed as their own
tickets rather than fixed or investigated further here, per explicit instruction.
