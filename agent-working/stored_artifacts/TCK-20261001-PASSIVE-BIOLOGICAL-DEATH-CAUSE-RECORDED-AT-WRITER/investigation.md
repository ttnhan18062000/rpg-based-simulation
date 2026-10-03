---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# Investigation — TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER

Observed engine commit: `71c4aa321` (`origin/main` @ #273, 2026-10-01). This investigation is
**shared with the batch sibling** `TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`;
that ticket's own investigation cites this file for the common ground rather than restating it.

## Why these two tickets are one batch

Direction from `world-rule-catalog-design` (2026-10-01), user-confirmed: both tickets change the same
site — the passive HP/age gate in `ApplyPath._compute_entity_changes` — and editing that site twice from
two different premises is exactly the "two efforts edit the same ordering from different premises"
failure that C1's sequencing constraint (`docs/plans/systemic_world/first_wave_plan.md:176-181`) warns
about. They also sit at the bottom of the bottom-up order: succession, inheritance and vacancy all
depend on deaths being classified correctly. One architecture review covers both.

## The site, read exactly (`src/engine/apply.py:93-110`)

```python
if is_life_due:
    life = entity.lifecycle
    new_age = life.age_ticks + 1
    bio = changes.get("biological", entity.biological)
    total_passive_dmg = 0
    if bio.hunger >= 95.0: total_passive_dmg += 2
    if bio.sleep_debt >= 98.0: total_passive_dmg += 1

    if total_passive_dmg > 0 or new_age != life.age_ticks:
        comb = changes.get("combat", entity.combat)
        new_hp = max(0, comb.hp - total_passive_dmg)
        if new_hp != comb.hp:
            changes["combat"] = replace(comb, hp=new_hp, alive=(new_hp > 0))
        changes["lifecycle"] = replace(life,
            age_ticks=new_age,
            active=(new_hp > 0 and (life.active or new_age < life.max_age_ticks))
        )
```

Three facts follow from this that the plan depends on:

1. **No cause is persisted anywhere.** `alive` and `active` are both written as pure functions of
   `new_hp`. Nothing records *why* HP reached zero, so `resolve_lifecycle` downstream has nothing to
   read.
2. **The outer guard is effectively always true on a life-due tick.** `new_age = life.age_ticks + 1`, so
   `new_age != life.age_ticks` is unconditionally true. The branch is entered on every life-due tick
   regardless of passive damage. **A guard added only to the passive-damage path will not cover the age
   path** — this is the single most load-bearing detail for the sibling ticket.
3. **The `combat` replace is conditional but the `lifecycle` replace is not.** For an entity already at
   `hp == 0` with no passive damage, `new_hp == comb.hp == 0`, so `changes["combat"]` is skipped while
   `active=(0 > 0 and ...)` → `False` is still written. That is the sibling's silent-deactivation
   mechanism, and it arrives through the age path.

## Why the discriminant is `comb.hp > 0 and new_hp == 0`

The ticket's chosen discriminant is sound, and the reason is structural rather than heuristic: an entity
carrying a `DEFEAT` or `REBIRTH` leftover is **already** at `hp == 0` when this branch runs, because
combat set it there on a previous tick. So `comb.hp > 0` is false for exactly that population, with **no
role check and no outcome-kind check**. The positive-to-zero transition is observable only where the
passive drain itself did the killing.

This matters because all three alternative discriminants are ruled out by accepted rules:

- **Bio thresholds** (`hunger >= 95` / `sleep_debt >= 98`) — rejected. Being *at* a threshold is not the
  cause of death; `docs/world_rules/foundations/capacity.md` LIMIT-04 (Disposition: ACCEPT) forbids
  reading a limit as a cause, and CAUSE-01/HP-02/CAUSE-05 forbid fabricating a cause that was never
  recorded. A starving entity killed by a sword would be labelled `STARVATION`.
- **Role gating** — rejected. Both opportunity-attack sites force `is_lethal=False` for *any* role, so
  `DEFEAT` is not HERO-only and a role gate does not separate the populations.
- **Outcome-kind inspection at the writer** — rejected as an inversion: the writer would be reading a
  combat classification to decide a biological fact, which is the coupling this batch exists to remove.

## Downstream: what `resolve_lifecycle` can currently express

`src/systems/lifecycle_systems/lifecycle.py:191-204` is the whole classification surface:

```
death_reason = None
... death_reason = "OLD_AGE"                                     # age path
if ent_upd and ent_upd.combat and ent_upd.combat.outcome_kind in ("KILL", "PERMADEATH"):
    death_reason = "COMBAT"
```

Verified consequences:

- There is **no passive bio-death branch at all**, so `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`
  did indeed ship no classification.
- There is **no `EntityRole.HERO` exclusion anywhere on this path.** The sibling ticket's claim that "the
  passive biological-death scan deliberately excludes `EntityRole.HERO`" describes a scan that does not
  exist on `main`. Because this ticket's discriminant is role-blind, a starving HERO is covered **here**,
  and the sibling's AC3 has been removed so that one behaviour has one owner.
- `DEFEAT` is absent from the tuple, which is the sibling's recording gap.

## CORRECTION (architecture review, 2026-10-01): the phase order, and why this ticket is blocked

**An earlier version of this investigation stated that the cause is "written on one tick and read on a
later phase of the same tick". That is wrong, and it was load-bearing.** Verified at `71c4aa321`:

- `src/engine/kernel.py:776-781` calls `AuthoritativeApplyPipeline.refine(...)` — which contains the
  lifecycle phase (`src/engine/pipeline.py:414`) — and **then** `ApplyPath.apply_generation(...)`. The
  passive drain at `apply.py:93-110` therefore runs **after** `resolve_lifecycle` within a tick. A cause
  written at the writer is first readable on **tick N+1**.
- Worse, at tick N+1 the entity is no longer eligible. `apply.py:109` wrote
  `active=(new_hp > 0 and ...)` → `False` on the fatal tick, and `resolve_lifecycle` opens with
  `src/systems/lifecycle_systems/lifecycle.py:146-148`:
  ```python
  for e_id, entity in state.entities.items():
      if not entity.lifecycle.active:
          continue
  ```
  The entity is **skipped before any branch is reached**.

**So the classification branch can never execute for this population**, regardless of what it reads. The
current silence is already pinned on `main` by
`tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py:155::test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`,
which asserts `hp == 0`, `alive is False`, `active is False`, `death_reason is None`.

### The fix is on record, and it is the other half of a known dual-writer race

`docs/parity_ledger/progression.yaml` `PROG-030` (P0, `verified`), from
`TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`, records verbatim: "`resolve_lifecycle` is now the
sole declared authority for old-age deactivation; the passive branch's `active=` formula is
`active=(new_hp > 0 and (life.active or new_age < life.max_age_ticks))`, **keeping only its immediate
HP-death gate**" — and notes the death now lands "one tick later than the passive" writer did.

That ticket fixed the **age** half of this exact race and deliberately left the **HP** half in place,
filing `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` (this ticket's direct ancestor) with the
fix already described as "a new `resolve_lifecycle` HP/alive-based death-detection branch, wired through
the existing lineage-dispatch path". **The architecture answer was already decided: the writer must stop
deciding deactivation; the consumer must.** Completing it is accepted into this batch's scope by user
decision, 2026-10-01 (plan R1).

The alternative — relaxing the `continue` at `lifecycle.py:147` — is **rejected**: a
dead-and-deactivated entity would re-enter the death-detection loop every tick and re-dispatch
succession, and it contradicts the single-declared-authority contract `PROG-030` established.

## Durable-state obligations

The cause is durable state by the project's own test: it is written on one tick and read on the **next**
tick by a different system (above). Per the Durable State Rule it needs a typed model, a stable home in
entity state, a defined lifecycle, inspection/debug visibility, and serialization tests. It must **not**
live in a `reason` string or free-form metadata.

**Placement, ruled by the architecture review:**

- **A transient on an existing update type is architecturally impossible**, not merely undesirable: the
  fact must cross a tick boundary, and no `StateUpdate`/`CombatUpdate`/`LifecycleUpdate` survives one.
- **`CombatComponent` is rejected** — the fact is a lifecycle classification, not a combat statistic.
  "Where the write happens" is not an ownership argument; the apply path writes to every component.
- **`LifecycleComponent` is correct, with precedent**: `death_reason`, `death_tick`, `is_permadeath` and
  `active` all live there, and `death_reason` is already in `to_canonical_dict()` (`state.py:192`). This
  is additive to an established pattern.
- **The field must be a real enum** (`Optional[DeathCause]`), with `death_reason` populated from the same
  enum's value so the two cannot drift. A second bare `str` beside an existing bare `str` is not what
  "typed record" means.
- **Canonical inclusion is confirmed** — it is durable state read across a tick boundary, so omitting it
  from `to_canonical_dict()` would reproduce the silent-field-drop class already recorded in `COMB-298`.
  But the earlier claim that this "changes every canonical hash in the corpus" is **overstated**: most
  canonical-hash tests compare two runs for equality, which is unaffected. The real re-baseline surface
  must be **measured** (candidates: `tests/regression/baseline_5k.json`, `tests/perf/baselines/`,
  `tests/integration/lab_agent/test_golden_run_fixture.py`) and the actual before/after stated.

## Determinism

`is_life_due` is cadence-driven and the discriminant is a pure comparison of two integers already in
scope, so no new RNG draw and no new iteration order is introduced. The `determinism` tag on this ticket
is about not *losing* that property: the new field must be written inside the same `changes` dict in the
same position, not through a second pass over entities.

## Open questions carried to Plan

1. Field name and home (above).
2. Whether `STARVATION` and `SLEEP_DEPRIVATION` are two reasons or one reason with a sub-cause, when
   both thresholds are breached on the same tick and the combined drain (`2 + 1`) crosses zero. The
   current code sums the damage and loses the attribution; the plan must state a deterministic rule.
3. Whether a non-fatal positive-to-positive passive drain should also record anything. Assumed **no** —
   out of scope, and nothing downstream reads it.
