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

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
