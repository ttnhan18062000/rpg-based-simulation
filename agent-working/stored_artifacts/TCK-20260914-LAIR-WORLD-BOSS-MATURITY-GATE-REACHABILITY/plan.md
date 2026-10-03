# Plan — TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY

Peer/user decision (2026-09-14), after reviewing investigation.md's full findings: build in this
exact order, and do not skip to the gate.

## Step 1 — Define difficulty tier 5

`DIFFICULTY_TIERS` (`src/world/spawn_config.py`) only defined tiers 1-4; both boss/Lair spawn calls
request tier 5 and silently fell back to tier 1 via `EntityGenerator.spawn_monster()`'s
`DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])`.

Add `DIFFICULTY_TIERS[5]`, continuing tiers 1-4's own ~1.4-1.6x growth curve (matching
investigation.md's "illustrative data" estimate): `hp=6.5x, atk=4.5x, def_stat=3.5x, xp=8.0x,
gold=6.5x, level_min=14, level_max=22`. Recorded as a first-pass, provisional value in
`docs/plans/deferred_tuning_decisions_register.md` D-05 — not a tuned balance answer.

Do not touch the `.get(tier, DIFFICULTY_TIERS[1])` fallback pattern itself in this step — confirmed
via exhaustive grep that no other real call site anywhere in `src/` requests `difficulty_tier=5` or
higher, so the fallback bug is fully neutralized by defining tier 5; broadening the fix to raise
loudly on any future undefined tier is out of scope (YAGNI — no other call site is broken today).

## Step 2 — Register `ancient_core`

Two places, because the codebase has a real catalog-vs-hardcoded-default split
(`TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` tracks the broader
architecture question separately):
- `data/content/world/items.yaml` — the authoritative catalog. Confirmed via `seed_phase1_content()`
  (`src/core/registries.py`) that this is what actually seeds `src.core.items.ItemRegistry` in any
  real run where `data/content` is present (via `CoreItemRegistry.bootstrap(catalog_repo.items)`),
  which is every real run in this repo — editing only the hardcoded dict below would be silently
  overwritten at import time.
- `src/core/items.py`'s own default `_items` dict — kept in sync for any code path that runs
  without a catalog present (tests, stripped environments).

Category `["material", "artifact", "boss_trophy"]`, rarity `"LEGENDARY"`, `base_value=500` —
provisional, matching Step 1's framing.

## Step 3 — Make the gate reachable (wiring, not tuning)

Per peer's own reasoning: reaching `maturity >= 50` in a realistic run would need a ~25x accrual
increase, which points at the *threshold* being the wrong half, not the rate
(`MATURITY_INTERVAL` stays untouched).

- `BossService.BOSS_SPAWN_THRESHOLD`: `50.0` → `2.0` (`state.maturity` reaches 2 by roughly tick
  2000, well inside the corpus's 200-5,000 tick range).
- New named constant `BossService.BOSS_SPAWN_TRAUMA_THRESHOLD` (replacing an inline `20.0` literal
  duplicated at both `check_for_boss_spawn()`/`check_for_lair_spawn()` call sites): `20.0` → `8.0`
  (just below the empirically-measured real peak of `9.92` in the most combat-heavy region of a
  real 2000-tick run — reachable with margin, not trivially at tick 1).

Record both as provisional/reachability-only in `docs/plans/deferred_tuning_decisions_register.md`
D-05, explicitly distinct from a tuned balance pass.

## Step 4 — Prove it end to end in a real run

Acceptance bar (peer's own framing): one real run showing the whole chain, not three separate unit
tests in isolation — a boss spawns in an unmodified corpus world, is genuinely formidable, and
carries/drops its own loot.

Executed: a real, instrumented `Kernel.tick_once()` run (no `no_frame_pacing` shortcuts to the
gate logic itself) against `frontier_living_world` (seed=42, unmodified corpus world) to 3000 ticks.
Result: `world_boss` spawned at tick 2101 with `hp=325/atk=45/def=17/level=19` (vs. tier-4's
`hp=200/atk=30/level=11`), carrying `ancient_core` in its own inventory, and a direct
`InventoryService.apply_update()` check confirmed `ancient_core` survives the real loot-add path.

Also constructed unit-level regression coverage (`tests/unit/world/test_boss_gate_reachability.py`)
so the fix doesn't silently regress later — see test_plan.md.

**Not proven end to end**: the Lair-occupant side. The only corpus world with a real `LAIR`-kind
Place (`generated_frontier_3_42`) has its region (`moon_cave`) sitting at exactly `0.0`
`trauma_score` for a full 5000-tick run — a separate, region-specific defect (zero recorded combat
deaths there), not something this ticket's threshold change can fix. Filed as its own follow-up:
`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, out of this ticket's scope per the original
"Out of Scope: balance/tuning work generally" framing — this is a content/routing question, not a
threshold-number question.

## Explicitly not done in this batch

- `EntityGenerator.spawn_stronghold()`'s own `state.maturity`-scaled stat term (found in the
  original `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` survey, re-confirmed still real and
  reachable but always baseline in practice) — untouched, out of this ticket's scope.
- The two small follow-ups filed, not fixed: `CALAMITY_RANDOM_CHANCE` unused constant,
  `_BOSS_KINDS` observability drift.
- The calamity-intensity system being inert (`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`)
  and the `ItemRegistry` dual-class divergence
  (`TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS`) — filed, not investigated
  further or built, per explicit peer instruction.
- Faction war declaration (`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`) — explicitly
  deferred until this ticket landed.
