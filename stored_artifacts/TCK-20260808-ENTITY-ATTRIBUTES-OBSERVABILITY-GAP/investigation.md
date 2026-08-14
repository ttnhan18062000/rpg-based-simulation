---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP
artifact_type: investigation
tags: [observability, world]
---

# Investigation — TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP

## Docs Requiring Update

- `docs/simulation_quality/event_type_coverage.md`: register `attribute_changed` (Implement phase)
- `docs/event_ledger/entity.yaml`: flip `ENTITY-008` to `observed` (Implement phase)

## Real mutation sources for `AttributeUpdate`

`grep -n "AttributeUpdate(" src/` returns 4 hits. Verified each for real, live reachability
(not just "constructs the type") — a repeated methodology this session, since a prior ticket
found `WorldProceduralGenerator` and `PerfRegressionGate` both looked real but were dead/unwired.

| Site | Verdict | Evidence |
|---|---|---|
| `src/engine/evolution.py:130` (non-hero level-up) | **LIVE** | `EvolutionSystem` is imported and used by `src/engine/pipeline.py:23` — part of the real tick pipeline. Fires whenever a non-hero entity (`entity.identity.role != EntityRole.HERO`) levels up: `vitality_delta`/`strength_delta`/`endurance_delta` scaled by the entity's own `aptitude` fields. |
| `src/engine/domain/core_actions.py:161` (`execute_allocate_ap`, strength/vitality only) | **WIRED BUT UNREACHABLE** | Routed via `action_router.py:49` on `action == "ALLOCATE_AP"`. But nothing in `src/ai/` ever selects `"ALLOCATE_AP"` as an action string. The one real gap→resolution pipeline that *could* drive it (`gaps.py`'s `level_gap` → `generator.py:79`'s `ConversionKind.ALLOCATE_AP` → `resolver.py:82`) resolves through a **different, cosmetic** path that only does `IdentityUpdate(unspent_ap_delta=-1)` — it never touches `AttributeUpdate` at all. So `core_actions.py`'s attribute-mutating AP-spend code is real, tested in isolation, but has no live AI driver — same reachability class as `wound_sustained` in the sibling vitals ticket (there: combat gated off; here: no goal/resolver ever emits this specific action). |
| `src/domains/demographics/cohort.py:98` (`compute_elder_attribute_update`) | **DEAD CODE** | `grep -rn "compute_elder_attribute_update" src/` returns exactly one hit — its own definition. Zero callers anywhere in `src/`. `DemographicCycleService.process_demographics` (the only live consumer of `cohort.py`, wired via `src/engine/world_dynamics.py:171`) operates purely on aggregate `PopulationCohort` counts per region — it never touches individual `EntityState.attributes`. This function is fully unwired, confirmed only referenced by `tests/unit/world/test_demographics.py`. |
| `src/actions/attributes.py:47` (`AllocateAttributeAction`, all 9 attrs) | **DEAD CODE** | `grep -rln "from src.actions.attributes"` returns exactly one hit: its own unit test (`tests/unit/progression/test_attribute_growth.py`). Never imported by `action_router.py` or anywhere in `src/`. The file's own inline comment ("I should probably update IdentityUpdate to officially include it... I'll add it to updates.py") reads as an abandoned draft superseded by `core_actions.py`'s `execute_allocate_ap`.

**Conclusion**: exactly 1 of the 4 grep hits is a genuinely live, naturally-firing producer in
current gameplay (`evolution.py`'s non-hero level-up). 1 more (`execute_allocate_ap`) is real,
tested, reachable code with no live AI trigger. 2 are dead code, never called.

## Tangential finding (disclosed, NOT fixed — out of scope)

`cohort.py`'s own docstring for `compute_elder_attribute_update` claims attributes are kept
"within the 1–99 mechanic range enforced by the apply pipeline." Checked the real apply site
(`src/engine/patches.py:557-570`, `AttributePatch.apply`): it clamps only an **upper** bound
(`min(100, new_att.X + delta)`) — there is no lower-bound clamp at all (no `max(0, ...)` or
`max(1, ...)` anywhere in that block). If elder decay (or any other negative-delta source) were
ever wired live, an attribute could go to 0 or negative with no floor. This is a real, pre-existing
mechanics-doc/code mismatch, not introduced by this ticket, and not fixed here — it's an
apply-pipeline correctness question, not an observability gap. Not spending further budget on it
since `compute_elder_attribute_update` is dead code and cannot currently trigger it; flagging for
a future ticket if elder decay is ever wired live.

## Event design

Post-tick STATE diffing (this repo's own established `event_extractor.py` methodology — diff
real `EntityState` component fields, not intent-object fields) works correctly regardless of
which of the above producers eventually fires, present or future: `entity.attributes` vs.
`prior_ent.attributes` (`AttributeComponent`: `strength`/`agility`/`vitality`/`endurance`/
`intelligence`/`spirit`/`wisdom`/`perception`/`charisma`, all `int`).

One event, `attribute_changed`, fires whenever ANY of the 9 fields differ — full coverage by
design, matching the standing instruction from `TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP`
("full cover every event from major to minor"), not a threshold-crossing subset. Payload carries
only the changed fields (`deltas: {field: int}`), keeping volume proportional to actual change.

**Severity**: direction-based, not magnitude-based — no existing numeric threshold for "how much
attribute change is significant" exists anywhere in the repo (unlike `StaminaComponent.
exhaustion_threshold` or `WoundState.severity`, reused directly in the sibling vitals ticket), and
the tangential finding above means an invented magnitude cutoff would be guessing against a
mechanic whose own floor behavior is undocumented/unenforced. Direction is a real, grounded
signal instead: `WARNING` if any delta is negative (a decline — narratively and mechanically
notable, matching how `wound_sustained` is inherently a "bad" signal distinct from `wound_healed`),
`INFO` otherwise (growth — training/leveling, the routine case).

## Real-verification (actual result, not the plan)

Attempted a real `Kernel.tick_once()` loop first, per the original plan below. Checked directly
during Implement (not assumed): `sandbox_world` has zero HERO-role entities (8 WORKER, 3 GUARD,
7 CITIZEN, all at `evolution_level == 1`), and none leveled up across a real, non-mocked
1500-tick loop. `evolution.py`'s non-hero level-up path is real and pipeline-wired (confirmed
above), just too rare in this small calibration world's timeframe to hit inside a unit test's
budget — the same reachability class as `wound_sustained` in the sibling vitals ticket (there:
combat gated off; here: leveling is real but slow). Fell back to this repo's own precedented
hand-built-state pattern (`test_information_intent_execution_fires_through_kernel_tick_once`):
real `AttributeComponent` objects constructed by hand and diffed through the real
`EventExtractor.extract()` function directly.

(Original plan, superseded by the above: attempt a real tick loop first on the theory that
non-hero entities exist in `sandbox_world` and gain XP/level through normal simulation, matching
`biological_state_changed`/`stamina_changed`'s verification style in the sibling ticket; fall back
to hand-built state only if that didn't pan out within a reasonable tick budget.)

## Classification (per explicit user direction — precise, not binary)

Currently: `docs/event_ledger/entity.yaml` `ENTITY-008` = `silent`. After this ticket: `observed`,
classified `unscored_intentional` (`docs/simulation_quality/event_type_coverage.md` §5) — emitted,
not wired to any SimQ pillar, a separate decision.
