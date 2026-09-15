# Investigation — TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY

**Investigation only, per this ticket's own explicit instruction: no implementation until peer has
reviewed what the gate actually needs.**

## Ordering conclusion, stated first because it inverts the ticket's own original framing

**The maturity gate is not the first thing to fix — it's the last.** Two real defects were found
waiting behind the gate (below), and at least one of them (the tier-5 stat defect) would make
opening the gate actively harmful: a player who finally sees a world boss appear after tens of
thousands of ticks and one-shots it (because it silently spawns with weaker stats than an ordinary
mid-tier monster) has had a *worse* experience than the mechanism staying dormant. **The real
sequencing is: fix the tier-5 stat defect first, verify a spawned boss/lair-occupant is actually
formidable, and only then make the maturity/trauma gate itself reachable.** A future reader should
not be able to open the gate without hitting this prerequisite — recorded here explicitly so that
doesn't happen by accident.

## Defect 1 (fix first) — `difficulty_tier=5` silently falls back to the weakest defined tier

Both `check_for_boss_spawn()` (world boss) and `check_for_lair_spawn()` (Lair occupant, `dragonkin`)
— `src/world/boss.py` — call `generator.spawn_monster(..., difficulty_tier=5)`. `DIFFICULTY_TIERS`
(`src/world/spawn_config.py`) **only defines tiers 1 through 4** — confirmed via direct read, no
`5` key exists. `EntityGenerator.spawn_monster()`'s own tier lookup
(`DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])`) silently falls back to **tier 1**
(the weakest defined tier) for any unregistered tier number.

Verified empirically (constructed a real state past the gate and called both spawn methods
directly):

| Spawn | hp | atk | def | level |
|---|---|---|---|---|
| `world_boss` (requested tier 5) | 50 | 10 | 5 | 3 |
| `dragonkin` lair occupant (requested tier 5) | 50 | 10 | 5 | 1 |
| Real tier-1 monster (for comparison) | 50 | 10 | 5 | 3 |
| Real tier-4 monster (the strongest *defined* tier, for comparison) | 200 | 30 | 12 | 11 |

**A "world boss" and a Lair-occupant `dragonkin` both spawn with the exact same stats as the
weakest possible monster in the game** — 4x less HP and 3x less attack than an ordinary tier-4
monster, let alone anything befitting a "world boss."

**This is the same failure-mode family found repeatedly this week, and worth naming explicitly as
the reason it survived undetected**: a silent fallback converts a missing definition into a
plausible-looking wrong value, with nothing erroring. Same shape as the dead
`getattr(state, "spatial_grid", None)` optimization, a bare `except` swallowing a lead parse
failure, and a trace recorder logging `SUCCESS` for what was actually a no-op — four instances now,
all sharing the identical property that the failure mode is silence, not a crash. A tier lookup
that used `DIFFICULTY_TIERS[difficulty_tier]` (raising `KeyError` on an unregistered tier) instead
of `.get(..., DIFFICULTY_TIERS[1])` would have caught this the moment `difficulty_tier=5` was first
used, rather than requiring someone to notice a suspiciously weak "boss" after the fact.

**Illustrative data only, not a proposed value** (still investigation, not a decision): extrapolating
the existing tier 1→4 progression (~1.5-1.6x per tier in hp/atk/def), a tier 5 entry would land
roughly around hp≈6.0-6.5x, atk≈4.0-4.5x, def≈3.2-3.5x, level 12-20 — shown only to size the real gap
between "what tier 5 currently produces" and "what the existing progression would suggest," not to
propose the number.

## Defect 2 (chased to a definitive answer) — the world boss's own signature loot item is silently dropped, not a crash

Peer asked for this chased to a yes/no rather than left as "credible risk." Answer: **no, it does
not crash — it is silently dropped.**

Two parallel `ItemRegistry` classes exist in the codebase, and they behave differently:
- `src.core.registries.ItemRegistry` — content-catalog-backed, `.get()` raises `KeyError` for an
  unregistered id. This is the one I initially assumed was in the real pipeline. It is not: it's
  only imported by `src/world/providers/{information,services,resources}.py` and
  `src/engine/intent/action_intent.py`, none of which sit in the real loot/inventory path.
- `src.core.items.ItemRegistry` — a hardcoded ~10-item dict (`iron_ore`, `wood`, `WOOD`, `herb`,
  `bread`, `healing_potion`, etc.), `.get()` returns `Optional[ItemDefinition]`, safely `None` for
  an unknown id, **never raises**. This is the one actually used by the real pipeline:
  `src/core/inventory.py` and `src/core/equipment.py` both `from src.core.items import
  ItemRegistry` (the safe one).

Traced the real player-loots-corpse path end to end:
`src/systems/economy_systems/loot.py::LootSystem.update()` (on completion, builds a
`ResourceTransferIntent(source_kind="CORPSE", items_add=target.items, transfer_kind="LOOT")`) →
`src/engine/economy.py` (processes the intent, no direct `ItemRegistry` call) →
`src/core/inventory.py::apply_update()`, the real, authoritative inventory-mutation apply-path.
Lines 170-174 of that function, the definitive finding:

```python
# 2. Handle Additions
for add_stack in update.items_add:
    defn = ItemRegistry.get(add_stack.item_id)
    if not defn:
        continue
```

`ancient_core` is unregistered in `src.core.items.ItemRegistry` (confirmed, not among its ~10
entries) and `.get()` returns `None`, so this `continue`s — the item is silently omitted from the
add. **`ancient_core` does not crash anything. It just never ends up in inventory.** Killing a world
boss today, even leaving aside Defect 1's stat problem, yields zero actual reward for the one item
the encounter exists to grant.

This is a fifth instance of the same silence-as-failure-mode family named in Defect 1 — a
lookup/fallback silently converts "this doesn't exist" into a no-op, with nothing erroring. It does
**not** join Defect 1 as a build prerequisite (it was never a crash risk), but it does belong beside
it as a second real defect behind the gate: even a formidable, correctly-tiered world boss (once
Defect 1 is fixed) would currently drop nothing of its own signature loot.

## Defect 3 — the gate's own two halves are independently unreached in a realistic run

Not "a large number" in one place — both halves of the AND conjunction are unreached, independently,
confirmed by a real 2000-tick `Kernel.tick_once()` run against `frontier_living_world` (seed=42):

| Gate component | Real run result | Requirement |
|---|---|---|
| `state.maturity` | reached `1` | `>= 50` |
| `region.trauma_score` (max across all regions) | `goblin_camp`: 9.92, `bandit_road`: 7.92, `hometown`: 1.00 | `>= 20.0` |

`trauma_score` is a real, live-accumulating stat (`src/engine/world_dynamics.py`'s own
"Death-triggered Trauma" block adds `+1.0` per real entity death in that death's own region — not
another dead-code path like the sibling ticket's scar-creation finding this week), but even in the
most combat-heavy region observed it reached under half of what's needed within 2000 ticks.
`state.maturity`'s own math (`MATURITY_INTERVAL=1000` ticks per `+1`, threshold `50`) needs ~50,000
ticks, matching D-05's original claim. **These two measurements are the first real evidence that
neither half is approachable in practice, not just that the maturity number alone is large.**

## Already-surveyed context (re-verified, not re-derived from scratch)

`TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` (done) already ran a full `state.maturity`
consumer survey (`docs/guidelines/intentional_divergences.md` §2.56), including a prior user
decision (2026-09-08) to accept this as a disclosed divergence — **now reversed by this batch's own
user decision**, not re-litigated here. That survey's own findings, re-verified directly:
- `RaidService.spawn_raid()`'s own `raid_size = 3 + state.maturity` scaling is a no-op in practice,
  tracked separately (`TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH`), not this ticket's concern.
- `EntityGenerator.spawn_stronghold()`'s own maturity-scaled HP/DEF term shares this exact root
  cause (real and reachable via region conquest, but always produces baseline stats in practice) —
  flagged for peer's awareness since it's the same underlying fix target, not built here.
- `EntityGenerator.spawn_calamity()` has zero callers anywhere — a third confirmed dead path, noted
  for completeness, already disclosed by the prior ticket, out of this ticket's own scope.
- Confirmed no other real call site anywhere in `src/` requests `difficulty_tier=5` or higher
  besides the two in `boss.py` — Defect 1's own blast radius is scoped exactly to world boss/Lair
  occupant spawning, not a wider systemic gap.

## Defect/finding 4 — a SECOND, maturity-independent world_boss spawn path exists, at the edge of the corpus's own run range

Per peer's explicit request to check whether anything *else* is waiting behind the gates: found a
completely separate producer of `kind="world_boss"` entities, unrelated to
`BossService.check_for_boss_spawn()`. `CalamityService.process_world_dynamics()`
(`src/world/calamity.py`) spawns a `world_boss` (correctly `difficulty_tier=4` — no tier-5 bug at
this call site) when `state.tick - state.last_calamity_tick >= CALAMITY_MIN_INTERVAL (2000)` AND
`state.tick % CALAMITY_FORCE_INTERVAL (5000) == 0` AND a region exists with
`calamity_intensity > 0.3`.

This path does **not** depend on `state.maturity` at all — but its own `CALAMITY_FORCE_INTERVAL`
requires the run to reach at least **tick 5000**, which is the extreme top edge of the corpus's own
stated 200-5,000 tick range, and only for `world_boss` (this path never spawns Lair occupants). Real
producers of `calamity_intensity` exist (confirmed: region-level accumulation with a real
`intensity_delta`, plus seasonal propagation) — this is not dead code.

### Finding 5 (peer-requested follow-up, now measured) — the calamity path does not fire in a real run, and the reason is stronger than "never crosses 0.3"

Peer asked this be resolved empirically rather than left as an untested inference, since the "world
bosses never spawn" claim is now written into three artifacts. Ran a real, instrumented 5000-tick
`Kernel.tick_once()` simulation against `frontier_living_world` (seed=42), tracking every region's
`calamity_intensity` on every tick and watching for any `kind="world_boss"` entity appearing.

**Result: `calamity_intensity` never left `0.0` in any region for the entire 5000-tick run.** Not
"never crossed 0.3" — it never moved at all. Correspondingly, no `world_boss` entity ever appeared
via this path (or any path) across the whole run. `state.maturity` reached `4` by tick 5000 (roughly
matching the `+1`-per-1000-ticks math, off by one likely from tick-budget throttling visible in the
run's own watchdog log, not investigated further as immaterial to this question).

This falsifies my own earlier framing (`intensity might realistically approach 0.3 by the top of the
corpus range`) more thoroughly than expected — it's not close, it's exactly zero the entire time.
Reading the two real producers explains why, without further chasing being necessary:
- `apply_calamity_consequences()` only adds intensity on `entity.kind == "hero"` death specifically
  inside a `region.hazard_level > 0.5` region — a narrow, specific trigger. If no hero died in a
  high-hazard region during this run (not separately confirmed, but consistent with the observed
  zero), this producer never fires even once.
- `CalamityPressurePropagator.propagate_seasonal()` only spreads intensity that already exists
  (`PROPAGATION_THRESHOLD = 0.10`) to adjacent regions — it cannot create intensity from nothing. If
  the first producer never seeds any region above zero, propagation has nothing to spread, no matter
  how many `SEASONAL_PROPAGATION_INTERVAL` cycles (500 ticks) pass.

So this is the same shape as Defect 3 (`trauma_score` peaking at 9.92 against a 20.0 requirement) —
a real, live mechanism that simply never accumulates enough in practice — but more extreme: trauma
at least moves. Calamity intensity, in this real run, did not move once. **The calamity-triggered
world_boss path is not a viable "it already works, just check timing" answer to this ticket — it is
itself unreached in practice**, for a different and independent reason than the maturity/trauma gate
(Defect 3).

**Also found while checking this path, for completeness**: `CalamityService.CALAMITY_RANDOM_CHANCE
= 0.005` is declared but has **zero real usages anywhere** — confirmed via exhaustive grep, only its
own declaration line matches. `should_spawn` is driven entirely by the deterministic interval check
above, not any random chance, despite a random-chance-shaped constant existing in the same class.
Another declared-but-unwired value, in the same file as the real maturity-increment logic this
ticket investigates — flagged for awareness, not chased further (it doesn't gate anything; it's
simply inert).

**Also found, smaller and observability-only**: `event_shapers.py`'s own `_BOSS_KINDS =
frozenset(("world_boss", "ancient_sentinel"))` does not include `"dragonkin"`, while
`event_extractor.py`'s own separate `_BOSS_KINDS` constant does. Two supposedly-parallel constants
have silently drifted apart — Lair-occupant kills may not be classified as "boss" events by one of
the two observability code paths. Lower stakes than the gameplay-facing defects above (affects
event classification, not the encounter itself), noted for completeness.

## What a corrected gate would need (data, not a decision)

For a target run length of `N` ticks, `state.maturity`'s own math requires either lowering the
threshold (`threshold ≈ N/1000`, e.g. `≈2` for `N=2000`) or raising the increment rate
(`MATURITY_INTERVAL ≈ N/50`, e.g. `≈40` for `N=2000`, ~25x faster than today), or some mix, or a
redesigned trigger entirely. `trauma_score`'s own threshold/accumulation/decay balance needs a
similar real number chosen. Neither is decided here — design intent (how far into a run a world
boss should reasonably become possible) is not this investigation's call.

## Summary for peer review

Both gaps peer flagged as blocking a fix decision are now closed. Full picture:

1. **Ordering matters more than any single number**: fix Defect 1 (tier-5 fallback) first, verify a
   spawned boss/lair-occupant is actually formidable, only then address gate reachability — opening
   the gate before fixing Defect 1 would make the feature actively worse than its current dormant
   state.
2. Defect 1 (previously-undiscovered): `difficulty_tier=5` silently produces tier-1 stats for both
   world bosses and Lair occupants. Same silence-as-failure-mode family as 3 other instances found
   this week.
3. Defect 2 (**now chased to a definitive answer**): the unregistered `ancient_core` loot item does
   **not** crash — it is silently dropped during inventory add (`inventory.py::apply_update()`'s
   `if not defn: continue`, via the real, non-raising `src.core.items.ItemRegistry`, not the
   raising `src.core.registries.ItemRegistry` I first assumed was in the pipeline). It does not
   join Defect 1 as a build prerequisite. It is still a real second defect: even a fixed, formidable
   world boss currently drops none of its own signature loot.
4. Defect 3: the maturity/trauma gate's own two halves are BOTH independently unreached in a real
   2000-tick run, not just "one large number" — `state.maturity` reached only `1` (need `≥50`),
   `trauma_score` peaked at `9.92` (need `≥20.0`).
5. Finding 4/5 (**now measured**): a second, maturity-independent `world_boss` spawn path exists
   (`CalamityService.process_world_dynamics()`), correctly using `difficulty_tier=4`, gated to only
   ever fire at `tick % 5000 == 0` and only when some region's `calamity_intensity > 0.3` — and only
   for world bosses, never Lair occupants. A real 5000-tick instrumented run against
   `frontier_living_world` (seed=42) found `calamity_intensity` never left `0.0` in any region for
   the entire run — not "never crossed 0.3," never moved at all — so no world boss spawned via this
   path either. This is not a viable "already works" answer for this ticket; it is itself unreached,
   for a reason independent of the maturity/trauma gate (its real producers — hero death in a
   high-hazard region, and seasonal propagation of existing intensity — never fired in this run).
   Also found in the same investigation, filed as two small follow-up tickets rather than fixed
   here: an unused `CALAMITY_RANDOM_CHANCE` constant (declared, zero real usages), and a real drift
   between two supposedly-parallel `_BOSS_KINDS` observability constants (one includes
   `"dragonkin"`, the other doesn't).
6. No implementation proceeds from this investigation — per explicit instruction. Bringing this
   complete picture back for the fix decision now that both gaps are closed.
