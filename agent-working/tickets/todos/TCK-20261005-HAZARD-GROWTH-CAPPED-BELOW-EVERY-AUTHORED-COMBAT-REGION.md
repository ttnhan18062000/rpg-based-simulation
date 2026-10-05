---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION
phase: open
date: 2026-10-05
tags: [world, investigation]
---

# TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION

## Title
Trauma-driven `hazard_level` growth is capped at `1.0` while authored hazard values are `2.0`-`4.0`,
so the growth path is dead for exactly the regions that accumulate trauma

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by `rpg-implementer-2` **from the code**, not from a run, while measuring trauma for owner
decision 10 / catalog Rule `ENV-06`, and reported to `rpg-planner` on 2026-10-05. Verified
independently by the planner at `src/engine/world_dynamics.py:119-123`:

```python
# Hazard scaling (LEG-RPG-139)
if current_trauma > 50.0:
    new_hazard = min(1.0, region.hazard_level + 0.01)
    if new_hazard > region.hazard_level:
        world_upd = replace(world_upd, hazard_level_set=new_hazard)
        changed = True
```

The growth is `min(1.0, hazard + 0.01)`, written only when it **exceeds** the current value. For any
region already at `hazard_level >= 1.0`, `min(1.0, x + 0.01)` is `1.0`, which is not greater than `x`,
so **nothing is ever written**. The branch is unreachable for those regions no matter how high their
trauma climbs.

**Authored hazard values exceed that cap.** On `frontier_living_world`, `bandit_road` is `2.0` and
`goblin_camp` is `3.0`; `moon_cave` is `4.0` on `generated_frontier_3_42`. These are precisely the
combat regions — the ones where trauma accumulates. Measured over 10000 ticks, seed 42, `PROD_SMALL`:
`goblin_camp` crosses trauma `50.0` at tick **5211** and `bandit_road` at tick **5217**, with
`bandit_road` reaching **111.0** by tick 10000 and no plateau. So the trigger condition
(`trauma > 50.0`) **is** met, repeatedly, from roughly tick 5200 — and the effect it guards can never
fire.

**Net result: trauma-driven hazard growth exists only for regions authored below `1.0`.** Whether any
corpus region is authored below `1.0` *and* accumulates trauma is unmeasured and is this ticket's
first question. If none is, the whole `LEG-RPG-139` growth path is dead in practice.

**The scale inconsistency is the underlying defect, not the dead branch.** A field whose authored
domain runs to `4.0` and whose growth function caps at `1.0` has two incompatible notions of what
`hazard_level` means. One of them is wrong, and which one is a semantics question rather than an
arithmetic one.

## Scope
1. Establish the intended domain of `hazard_level`. Is it `0.0`-`1.0` (making authored `2.0`-`4.0`
   out-of-range content) or open-ended (making the `min(1.0, ...)` cap wrong)? Cite Bible 05 and the
   content schema. **Do not pick by reading the code** — the code is what is in question.
2. Measure how many corpus regions are authored below `1.0`, and of those, how many ever exceed
   trauma `50.0` in a realistic run. This decides whether the branch is dead everywhere or only for
   the combat regions.
3. Check every **reader** of `hazard_level` for the same assumption. The retired hero-death calamity
   producer used `hazard_level > 0.5`; the lair gate reads `trauma_score` at `8.0`, not hazard. A
   reader that assumes a `0.0`-`1.0` range while content authors `4.0` is the same defect seen from the
   other side, and there may be several.
4. Fix in whichever direction Scope 1 establishes, and record it. If the authored values are wrong,
   that is a content change with measurement consequences for every world that uses them; if the cap is
   wrong, it is a one-line engine change with a parity-ledger entry.
5. Update `docs/parity_ledger/world_dynamics.yaml` and the Bible chapter whose text Scope 1 relies on.

## Out of Scope
- **Catalog Rule `ENV-06`.** It routes **trauma → calamity directly** and does **not** read
  `hazard_level`, so `ENV-06`'s implementation (`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`)
  is **not blocked by this ticket** and must not wait for it. Confirmed against the Rule's own text.
- The retired single-hero-death calamity producer and its `hazard_level > 0.5` trigger — retired by
  owner decision 10.
- The world-boss branch and the lair maturity gate. Deferred by the owner, and the lair gate reads
  trauma rather than hazard.
- Balance of the `0.01` step or the `50.0` threshold. `50.0` is a Bible-stated law; do not adjust it.

## Acceptance Criteria
- [ ] `hazard_level`'s intended domain is stated with a Bible or schema citation, not inferred from
      the code.
- [ ] Scope 2's counts are reported, including zero. "No corpus region is authored below 1.0" would
      mean the growth path is dead everywhere and is a complete answer.
- [ ] Every `hazard_level` reader is listed with the range it assumes.
- [ ] The fix direction is recorded with its rationale; if it is a content change, the affected worlds
      are named and the measurement consequence stated.
- [ ] A test asserts growth actually occurs for a region in the intended domain with trauma above
      threshold — the current code has no such test, which is why the dead branch survived.
- [ ] `docs/parity_ledger/world_dynamics.yaml` updated; determinism sweep green with any moved hash
      explained.

## Related Tickets
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — produced this finding. **Not blocked by
  this ticket** (see Out of Scope); `ENV-06` bypasses hazard.
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — adjacent; reads trauma, not hazard, so it is a
  different defect despite looking like the same family.
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` — the same measurement run found that
  overlap *shadows* a region's trauma via `get_region_at`'s first-match return. A shadowed region never
  reaches trauma `50.0` either, so the two defects can mask each other.
- `TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE` — same "declared range versus
  actual content" family.

## Related Docs
- `docs/mechanics/05_world_evolution.md` §2 — regional trauma and the `50.0` threshold
- `docs/world/ecology_and_calamity_contract.md` — hazard and calamity contract
- `docs/parity_ledger/world_dynamics.yaml`

## Related Stored Artifacts
_(`rpg-implementer-2`'s 10000-tick trauma probe is in its scratchpad and **not committed** — ask for it
before re-writing one)_

## Related Code Areas
- `src/engine/world_dynamics.py:119-123` — the capped growth (`LEG-RPG-139`). **Lane B's surface** per
  the 2026-10-05 lane ruling.
- `src/world/consequences.py:42` — trauma decay, `-0.0005/tick`
- `data/content/world/runtime_regions.yaml` and the world modules — authored `hazard_level` values

## Assumptions / Open Questions
- The planner verified the code and the arithmetic; **nobody has observed a run in which hazard grows**.
  `rpg-implementer-2` was explicit that it read this rather than measured it. So "the branch is
  unreachable for hazard >= 1.0" is a code-and-arithmetic claim; confirm it with a positive control
  (a region authored below `1.0` driven above trauma 50) rather than only by reading.
- `LEG-RPG-139` suggests a legacy-parity origin. **Check whether the `1.0` cap is inherited from legacy
  behaviour that the parity ledger already records** before treating it as a bug — it may be a
  deliberate, documented divergence, in which case the authored values are the defect.
- Line numbers are at `da064fe78`.

## Implementation Notes
_(not started)_

### 2026-10-05 — Scope 1-3 evidence by `rpg-implementer-2`: the documents conflict, so no single domain is established; nothing changed

Read-only. Scope 1 was answered from documents and the schema, not from the growth code.

**Scope 1 — what the sources say `hazard_level`'s domain is.**
| source | says |
|---|---|
| `docs/mechanics/05_world_evolution.md:74` (Hazard Impacts) | "As `Hazard Level` **(0.0 to 1.0)** increases, entities within the region suffer..." The only explicit domain statement found. |
| `docs/mechanics/04_strategic_cognition.md:48-50` | danger urgency is `0.0` at `hazard_level = 0.7` and `1.0` at `>= 1.0`: consistent with 0..1 as the meaningful span, but defines behaviour *above* 1.0 (saturation), so it contemplates values past 1.0. |
| `src/worldbuilding/schema.py:91` `RegionSpec.hazard_level`, `recipe.py:70` | `Optional[float]`, default `0.0`, **no `ge`/`le`**; descriptions "Hazard difficulty factor" / "rating". Unconstrained. |
| `docs/world/generator_contract.md:110-114` | the generator authors `1.2 x danger_level` and `1.5 x danger_level`, i.e. **above 1.0** at `danger_level = 1.0`, by contract. |
| `docs/guidelines/intentional_divergences.md` §2.20 (ratified) | cites `wolf_den` at `hazard_level: 2.0` as an ordinary authored value. |
| `docs/archive/engine_ledger/legacy_replacement_ledger.md:158` (`LEG-RPG-139`) | "Trauma-scaled hazards", `SUPPORTED`. **No cap is recorded**, and no parity-ledger or divergence entry documents `1.0` as intentional. |
So the Bible's one sentence says 0.0-1.0; the generator contract, the ratified divergence record, the schema, and 79 of 104 corpus region
instances (below) say otherwise, and only the growth cap agrees with the Bible sentence. **The `1.0` cap is NOT a recorded legacy-parity
divergence**, so the planner's "authored values are the defect" branch is not available on that ground either. Direction (amend the Bible
and drop the cap, or constrain authored hazard to 0..1) is a Bible-versus-content choice, **not made here**; `docs/mechanics/05` is a Bible chapter.

**Scope 2 — counts, 24 resolved worlds, 104 region instances.** Authored `< 1.0`: **25 (24%)**, all settlements: `hometown` 0.0 (x20),
`trading_hometown` 0.5 (x4), `survivor_outpost` 0.5 (x1). Authored `>= 1.0`: **79 (76%)**, range 1.0 to 4.0, and **every combat region** (`bandit_road` 2.0,
`goblin_camp` 3.0, `wolf_den` 2.0, `old_mine` 2.0, `orc_stronghold` 3.0, `moon_cave` 4.0, `haunted_battlefield` 3.5/4.0, ...). Of the 25 below 1.0, none exceeded
trauma 50 in the runs available: `hometown` peaked at 2.0 and `trading_hometown` at 0.0 (`frontier_living_world`, 10,000 ticks), `hometown` 1.9
(`generated_frontier_3_42`, 5,000 ticks). So the growth branch is dead in every measured region; **only two worlds were run**, the other 22 are
not measured for this.

**Scope 3 — readers of `hazard_level` and the range each assumes.**
| reader | use | assumed range |
|---|---|---|
| `world/environment.py:36` `calculate_hazard_drain` | `hazard_level * (1 + calamity_intensity)` HP drain | none; linear, so authored 2.0-4.0 multiplies drain 2-4x |
| `world/spawn.py:73` | `(area/10000) * BASE * (1 + hazard_level)` monster target | none; linear |
| `systems/world_systems/quests.py:74-81` | quest if `> 0.5`; reward `int(hazard * 150)` gold, `* 80` XP | none; linear, unbounded rewards |
| `domains/world_emergence/models.py:78` | `hazard_factor = hazard * 0.2`, then `min(1.0, max(0.0, ...))` | clamps the *sum*; a hazard of 4.0 adds 0.8 |
| `systems/world_systems/events.py:49-51` | danger urgency, `0` at 0.7, saturates at `>= 1.0` | 0..1 as the span; **every authored >= 1.0 region reads urgency 1.0** |
| `town/guild.py:98,116` | passes `hazard` into `QuestPressureProfile` | not determined here (not read past the call) |
| `engine/world_dynamics.py:121-123` | growth `min(1.0, h + 0.01)`, written only if greater | **0..1** (the defect: never greater for `h >= 1.0`) |
| `world/calamity.py:92` | `> 0.5`; the retired single-hero-death producer | n/a, retired by owner decision 10 |
| `api/presenters/state_presenter.py:168,281` | shaping only | none |
So most readers treat the field as an open-ended multiplier, and two (`events.py`, `world_dynamics.py`) assume 0..1. That is the same
scale inconsistency seen from the reader side.

**Measured consequence that bears on any content-side fix (arithmetic, not a re-simulation).** In `frontier_living_world`, 5,000 ticks, 98 of 141
deaths (70%) are `HAZARD` deaths, driven by the drain formula above on regions authored 2.0-4.0. Clamping authored hazard to 1.0 would cut that drain by
a factor of 2-4 in every combat region, so a content-side fix would move the dominant death cause in every corpus world.

**Not done:** no fix direction chosen; the Bible's `0.0 to 1.0` is a Bible-stated statement and not mine to change; `docs/parity_ledger/world_dynamics.yaml`,
the Bible and the test (Acceptance Criteria 4-6) are untouched until a direction exists. `ENV-06` does not read `hazard_level` and is not blocked by this.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
