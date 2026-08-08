---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [progression, simulation-quality]
---

# Plan — TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION

## Fix

`src/engine/combat.py::resolve_multi_attack()`: after the existing `classification =
CombatRewardClassificationService.classify_defeated_target(...)` call (line 391) and its existing
`xp_gain`/`gold_gain` computation, port `resolve_attack()`'s own rebirth/permadeath branch
verbatim (same condition, same semantics — `defender.lifecycle.generation < 4` → `gen_delta=1`,
`outcome="REBIRTH"`; else → `perma_set=True`, `outcome="PERMADEATH"`), and add
`generation_delta=gen_delta, is_permadeath_set=perma_set` to the function's own returned
`CombatUpdate` (currently omits both fields entirely).

No change to `combat_rewards.py`'s own classification logic — it already returns the correct
`rebirth_eligible` value; this fix only ports the *consumption* of that value into the path
that's actually exercised.

## Explicitly not touched (disclosed, not silently dropped)

`resolve_skill_usage()`/`resolve_aoe_attack()` have the identical gap but 0 real calls observed in
this session's own direct instrumentation — porting there too would be speculative (no real data
showing it matters) and is flagged as a residual, lower-priority gap for a future ticket if either
path becomes real corpus-active.

## Test

New unit test in `tests/unit/movement/test_tactical_movement.py` (or a new combat-specific test
file, decided during Implement based on the cleanest fit) — mirrors the existing
`test_opportunity_attack_lethal_grants_resource_transfers_to_attacker` pattern: a real
opportunity-attack scenario where the defeated defender is `EntityRole.HERO` with
`lifecycle.generation < 4`, asserting the resulting `CombatUpdate`/`LifecycleUpdate` carries
`generation_delta == 1` and `outcome_kind == "REBIRTH"` through the full pipeline.

Real re-verification: re-run `make simq-long-run-lifecycle-observation` on `hero_guild_routing`
(the one curated world with 3 real HERO entities) and check whether `life_arc_detector_reachable`
can now flip to `true` given enough real HERO deaths within 2000-5000 ticks — disclosed as a real,
run-dependent check, not guaranteed to flip within any single run given how rare a 4th-generation
HERO death still realistically is.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| Real trigger chain traced | investigation.md |
| Real reachability estimate given real rates | investigation.md — structurally unreachable pre-fix, independent of rate |
| Evidenced conclusion: gap vs. working-as-intended | Real gap (missing code path), fixed |
| Real fix lands, re-verified via long-run tier | This plan's Test section |
| Docs updated | `intentional_divergences.md` new entry |
| Scoped pytest passes | New test + existing movement/combat suites |
