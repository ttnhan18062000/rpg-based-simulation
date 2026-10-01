---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS
artifact_type: test_plan
tags: [simulation-quality, progression]
---

# Test Plan

The central property is **value-neutrality**: the derivation must reproduce today's numbers exactly
at spawn and under hardening, and differ only where today's behaviour is the bug. T3 and T5 are the
two that must not be weakened — if either needs its expected value "adjusted" to pass, the
implementation is wrong, not the test.

## Normal flow

**T1 — spawn preserves the profile's declared stat, unchanged.**
A real `goblin_scout` spawns at `combat.max_hp == 35`, `atk == 8`, `def_stat == 2` — identical to
today. Asserts Step 2 added state without moving any spawned value. Repeat for one `LEGACY-EXPORT`
profile with an `attribute_bias` (`wolf_predator_base`) and one generic profile (`commoner_base`,
live at `entity_archetypes.yaml:98`), since the rule owner established the generic profiles are also
affected (`def 0 → 5`).

**T2 — the stored base is the residual, and the derivation inverts it.**
For a spawned `goblin_scout`: `base_hp == 23` and
`recalculate_combat_stats(attrs, base_hp=stored_base) == 35`. This is the arithmetic from
`investigation.md` §3 asserted directly, so a future reader can see why the base is not `35`.

**T3 — REGRESSION-CRITICAL: a `stats_dirty` trigger no longer erodes species bases.**
Satisfies ticket AC2. Take a real species-specific entity, fire a `stats_dirty` trigger (an
equipment change is the cleanest — it is a trigger with its own term in the formula), and assert
`max_hp` does **not** become `112` and does **not** become `47`. Assert the exact expected value.
**Both wrong answers must be excluded by name** — `112` is the original bug and `47` is the trap from
`investigation.md` §2, which a plausible "fix" produces.

## Edge cases

**T4 — attribute changes now propagate (the behaviour that was broken).**
Raise `vitality` by 2 on a `goblin_scout` and assert `max_hp` rises by exactly 4 per §2
(`base 23 + vit*2`), not by 20 and not at all. This is the capability the fix buys, and the
companion ticket `TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT` already proved
`strength → atk` has formula-exact purchase on real damage, so this is a real determinant.

**T5 — REGRESSION-CRITICAL: hardening still grants exactly +5, and it accumulates.**
A near-death survivor ends the tick at `max_hp + 5`, same as today. Then a second hardening event
gives `+10` total. Then fire an unrelated `stats_dirty` trigger and assert the accumulated grant
**survives** — that is the failure mode Step 4 exists to prevent and the one a base-only fix would
have shipped.

**T6 — the base is immutable, and the clamp holds.**
Attempt a mutation path and assert the base is unchanged after a recalc, a hardening grant and an
attribute change. Separately assert the residual clamps at `0` rather than going negative. If any
live profile actually clamps, that entity's spawn stat cannot be reproduced by the formula —
**report it rather than silently accepting it.**

**T7 — the formula and the residual cannot drift.**
If Step 2 uses a shared helper, assert both call sites use it. If it does not, this test is
mandatory: construct an entity, compute the residual, run the derivation, and assert round-trip
identity — so that changing one attribute term without the other fails here instead of silently
reintroducing the bug.

## Failure modes

**T8 — determinism and serialization.**
The new field round-trips through `to_canonical_dict()`; `CanonicalStateHasher.get_hash()` does not
raise and is stable across two identical runs. Run the existing replay/fingerprint and determinism
tests explicitly — a new canonical field changes state hashes, and `DEV-004`'s 2026-08-30 note
records a real hasher crash from a non-serializable value in exactly this area. Expect to update
recorded-hash fixtures; **do not** suppress the hasher to avoid it.

**T9 — the hardening event still reports the right number.**
`src/observability/event_shapers.py:1829` reconstructs `max_hp` as
`prior_max_hp + combat_upd.max_hp_delta`. Assert the near-death hardening event's reported `max_hp`
matches the entity's actual post-tick `max_hp`. Without this, Step 4 silently produces a stale event
value — the same shape of defect as `event_extractor.py:778` dropping `hazard_drain_applied`, which
the death batch hit.

**T10 — `PROG-030` still passes.**
It is P0 and is the dual-writer fix this change completes. Run its `test_path` by name, not as part of
a sweep.

**T11 — `ALLOCATE_AP` dormancy is undisturbed.**
`tests/integration/progression/test_allocate_ap_dormancy.py` and
`tests/unit/quest/test_progression_regression.py` still pass (4 tests, passing at HEAD). The plan
leaves `execute_allocate_ap` untouched; this proves it.

## Post-fix measurement (ticket AC3)

**T12 — re-measure `stats_dirty` firings in real corpus play.**
Step 3 makes the path reachable for the first time, so the 2026-09-30 zero is no longer the relevant
number. Re-run the same probe shape — production loader
(`WorldRepository.load_world_with_context`), real `Kernel` ticks, `PROD_SMALL`, seed 42, the same
three worlds (`frontier_living_world` 600 ticks, `crowded_frontier` 400, `quest_dense_frontier` 400)
— and record the new firing count and how many entities' derived stats moved.

**The probe must carry a positive control**, as the original did: assert through `apply.py`'s own
resolved name (`apply_mod.SkillScalingService is rpg_depth.SkillScalingService`, then invoke it) and
require the counter to increment by exactly 1 before the run starts. A zero without a positive
control is not a measurement. Record the result in the ticket even if the count is still low.

## Commands

Scope to the domain; **do not** run the full suite.

    .venv/bin/python -m pytest tests/unit/quest tests/integration/progression \
      tests/mechanic_scenarios -q
    .venv/bin/python -m pytest tests/ -q -m "not slow" -k "determinism or canonical or replay or fingerprint"

Note the venv lives at the **main checkout** (`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python`); there is none in the worktree.

Add the four named expected failures from the death batch to the Test Summary if any resurface, so
none reads as a flake.
