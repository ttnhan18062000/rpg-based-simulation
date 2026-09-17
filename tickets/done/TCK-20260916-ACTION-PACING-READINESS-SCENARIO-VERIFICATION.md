---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION
phase: done
date: 2026-09-16
tags: [simulation-quality, testing, architecture]
---

# TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION

## Title
First real use of the mechanic-verification scenario component: verify `action_pacing_readiness`
(priority 115, 23 transitive dependents, the largest blast radius in the registry)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`action_pacing_readiness` is now the #1 unverified-priority mechanism (per
`TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED`'s own fix), with 23 transitive dependents —
the largest blast radius in the 75-mechanism registry — and the only entry in the top six carrying
`state: partial` rather than `done`, meaning "which part actually works" is a real open question,
not a formality. This is also the first time the mechanism registry (which names the verification
target and its priority) and `docs/plans/mechanic_verification_scenarios_proposal.md`'s own
component (which produces a real runtime verdict) work together as designed — worth doing
carefully, since it sets the pattern the other 67 unverified mechanisms will eventually follow.

Per explicit instruction: **investigate first, build second.** No prior direct-code investigation
of this specific mechanism existed before this ticket beyond the atlas's own citation.

## Scope
1. Investigate what `action_pacing_readiness` actually is, what its `partial` state claims, and
   what observable, differential behavior would distinguish "working" from "not working."
2. Build a real, differential scenario (§3.3 of the proposal — mandatory, not optional) using the
   real compile path, not a synthetic fixture.
3. Record the resulting verdict in `docs/brainstorm/mechanisms.yaml`'s `verified` block, whatever
   it is — `observed`, `contradicted`, or `inconclusive` — never adjusted toward a favorable answer.
4. File, not fix, any real defect found along the way, unless trivial.

## Out of Scope
- Repairing anything found broken by this investigation (verification only, per explicit
  instruction — a `partial` mechanism with 23 dependents could be a large repair, and mixing the
  two would make it impossible to tell what the verification itself established).
- Building scenarios for any of the other 67 unverified mechanisms — this is the first, and the
  pattern-setting exercise, not a batch.
- Re-litigating `TCK-20260915-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED`'s own fix — this ticket
  consumes its corrected output (the #1 ranking) as a given.

## Acceptance Criteria
1. A real investigation (code read, not just the atlas's own citation) establishes exactly what
   `action_pacing_readiness` claims and what `partial` means for it specifically.
2. A real, differential scenario exists (`tests/mechanic_scenarios/`), reusing the real compile
   path per the proposal's own §3.2, staging the mechanism's precondition present vs. absent on the
   same forced dispatch, per §3.3's mandatory requirement.
3. Both differential conditions pass, and the failure reason in the blocking condition is confirmed
   to be specifically attributable to this mechanism, not a coincidental rejection elsewhere.
4. A `verified` block is recorded on `action_pacing_readiness` in `mechanisms.yaml`, with the real
   verdict — not adjusted toward a favorable answer if the evidence doesn't support one.
5. Any real defect found is filed as its own ticket, not repaired in this pass, unless trivial.

## Related Tickets
- `TCK-20260915-MECHANISM-VERIFICATION-AXIS` — owns the `verified` schema this ticket populates
- `TCK-20260915-MECHANISM-PRIORITY-DERIVATION` / `TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED`
  — why this mechanism is the first target
- `TCK-20260831-READINESS-SPEED-FORMULA` — the separate, already-closed, already-fixed claim about
  `readiness_speed` varying by agility (a different code path from the gate this ticket verifies;
  investigated as part of due diligence, not re-litigated as broken)

## Related Docs
- `docs/plans/mechanic_verification_scenarios_proposal.md` — the component this ticket is the
  first real user of, especially §3.2 (real compile path) and §3.3 (mandatory differential design)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-VERIFICATION-AXIS/` — the `verified` schema's own design

## Related Code Areas
- `src/engine/legality.py::LegalityServiceV2.verify_readiness`
- `src/engine/domain/action_router.py` (the dispatch checkpoint, "0. Readiness Check")
- `src/progression/leveling.py`, `src/engine/apply.py` (the separate agility-derived
  `readiness_speed` path, investigated not repaired)
- `tests/mechanic_scenarios/test_action_pacing_readiness_gate.py` (new)
- `docs/brainstorm/mechanisms.yaml`

## Assumptions / Open Questions
None outstanding — resolved during investigation (see Implementation Notes).

## Implementation Notes

### What `action_pacing_readiness` actually is
Two genuinely separate claims live under one mechanism id, both real code, confirmed by direct
read (`src/engine/legality.py:143`, `src/engine/domain/action_router.py:20-44`,
`src/progression/leveling.py:104`, `src/engine/apply.py:593-635`), not the atlas's citation alone:
1. **The gate**: `ENTITY_ACT` requires `entity.combat.readiness >= 100.0`
   (`LegalityServiceV2.verify_readiness`, dispatched from `ActionRouter.execute_action`'s "0.
   Readiness Check", ahead of every non-survival action). Readiness accumulates by
   `readiness_speed` each tick (`engine/apply.py:127-128`). This is the load-bearing half — the
   thing all 23 transitive dependents actually need to be real.
2. **The pacing-by-build claim**: `readiness_speed` should vary by agility, so faster characters
   act more often. This is the atlas's own cited `partial` claim ("Live, but uniform... every
   entity paces identically regardless of build").

### What `partial` means, and whether it's still accurate
Direct investigation, not assumed from the atlas's own text: `TCK-20260831-READINESS-SPEED-FORMULA`
(closed 2026-08-31, **before** this session's own Foundation seed on 2026-09-15) already added a
real agility-derived formula (`max(1.0, 10.0 + (agility - 5) * 1.0)`,
`src/progression/leveling.py:104`) and fixed a real wiring bug so the derived value survives into
the live `CombatComponent`. This raised a real question: is the atlas's "flat 10.0 for everyone"
citation now stale (a fourth stale-badge instance), the way `camp`'s own registry state was found
stale in T4?

**Checked directly, not assumed either way**: `WorldCompiler` (`src/worldbuilding/*.py`) never
calls the agility-derived formula anywhere — confirmed by grep, zero references. The formula only
runs via `apply.py`'s `stats_dirty` path (`engine/apply.py:593-608`), triggered by an
attribute/equipment/skill/trait/breakthrough/class/evolution/wound-changing update during live
simulation — **not** at world compile/spawn time. So every entity's `readiness_speed` is still
exactly the catalog/dataclass default (uniformly `10.0` in practice, confirmed on the real compiled
scenario world used below) until that entity's stats are first dirtied by some other event.
**Conclusion: `state: partial` remains accurate, for a more precise reason than the atlas's own
text states** — not "flat forever," but "flat at spawn, individually varying only after a
stat-recalculation event." This is a real nuance worth recording, not a stale badge; no registry
`state` correction is warranted, and this is NOT filed as a new defect since the ticket that built
the formula already knows and accepted this shape (its own Completion Summary already records that
the formula's real-world effect is corpus-unobservable for a related reason — combat structurally
ceasing before tick 1000).

### The scenario
`tests/mechanic_scenarios/test_action_pacing_readiness_gate.py` — reuses
`data/worlds/mechanic_scenario_combat_judgement_withdrawal/` as-is (real, compiled, catalog-driven
`goblin_scout` vs `orc_warchief`), confirmed by direct compile that both entities spawn with
`combat.readiness == 100.0` and no `last_combat_posture` recorded for this pairing — so the
already-verified posture gate (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`)
cannot interfere; only `readiness` is varied. Same staging/dispatch shape as
`test_combat_judgement_withdrawal.py` (forced `ENTITY_ACT`/`ATTACK` task, one real `Kernel.tick_once()`,
counting `CombatActions.execute_attack` calls for the goblin) — reused deliberately, not
reinvented, since it already solves real-world staging correctly.

Two conditions, per §3.3's mandatory differential requirement:
- **Mechanism present** (`combat.readiness = 50.0`, below threshold): the attack must be withheld.
- **Mechanism absent** (`combat.readiness = 100.0`, meets threshold, the compiled default): the
  attack must proceed.

Both pass. Verified the blocking reason is specifically attributable to the readiness gate, not a
coincidental rejection elsewhere: calling `ActionRouter.execute_action` directly in the blocking
condition returns `EntityUpdate(..., failure_reason=ReasonCode.INSUFFICIENT_READINESS, ...)` —
the exact reason code `verify_readiness` returns, confirmed by direct inspection of the real
returned object, not inferred from the attack simply not happening.

### Verdict
`instrument: scenario` (a real, differential, catalog-driven Kernel run — the strongest of the four
instruments per `mechanisms.yaml`'s own static-vs-runtime distinction), `verdict: observed`. The
gate genuinely withholds and permits actions exactly as its own code claims, through the real
dispatch path, in a real compiled world — not just reachable-and-called (a code trace alone could
never rule out the combat-judgement-scenario's own first-attempt failure mode: correct-looking code
that silently doesn't have its claimed effect).

## Test Summary
2 new tests in `tests/mechanic_scenarios/test_action_pacing_readiness_gate.py`, both passing:
- `test_readiness_gate_withholds_a_real_action_when_readiness_is_below_threshold`
- `test_readiness_gate_does_not_withhold_when_readiness_meets_the_threshold`
Full scoped suite (`tests/unit/tools/ tests/unit/engine/test_capability_registry.py
tests/mechanic_scenarios/`) re-verified passing, `graphify-out/` genuinely moved aside and restored.

## Files Changed
- `tests/mechanic_scenarios/test_action_pacing_readiness_gate.py` (new)
- `docs/brainstorm/mechanisms.yaml` — `action_pacing_readiness` gains a `verified` block
  (`instrument: scenario, verdict: observed`); `state` unchanged (`partial` remains accurate)
- `docs/brainstorm/mechanism_verification_view.md`, `docs/brainstorm/mechanism_priority_view.md` —
  regenerated
- `tests/unit/tools/test_mechanism_registry.py` — swapped the "real, unverified id" fixture example
  from `action_pacing_readiness` to `tactical_decision`
- `tests/unit/tools/test_mechanism_priority_derivation.py` — the prior ticket's own real-data
  regression test rewritten to compute `priority()` directly rather than depend on any specific
  mechanism's verified status
- `docs/REGISTRY.yaml` — regenerated (Finalize's own post-migration self-check)

## Completion Summary
DONE. The first real use of the mechanic-verification scenario component against a mechanism the
registry named as its own top priority. `action_pacing_readiness`'s readiness gate is confirmed
`observed` via a real differential scenario (readiness below threshold withholds a staged action
with the specific `INSUFFICIENT_READINESS` reason; at threshold, it proceeds) through a real
compiled world and the real `Kernel` dispatch path — not a code trace, which could never have ruled
out the same silent-non-effect failure mode the combat-judgement scenario's own first attempt hit.

`state` stays `partial`, correctly — investigated directly rather than assumed: the separate
agility-scaling half of this mechanism (`readiness_speed`) has a real, already-shipped formula
(`TCK-20260831-READINESS-SPEED-FORMULA`), but it only takes effect after an entity's first
stat-recalculation event, never at world-compile/spawn time (confirmed by grep — `WorldCompiler`
never calls it). This is not a stale atlas badge and not a new defect; it is the same accurate
`partial` for a more precise reason than the atlas's own text states.

Verified count is now 8 of 75 (67 unverified, was 68); `action_pacing_readiness` correctly drops
out of the priority view's unverified ranking, promoting `tactical_decision` to #1 — confirmed
directly by regenerating the view, not assumed.

No repair performed and no new defect filed, per this ticket's own explicit scope: the one
candidate finding (whether the flat-readiness-speed claim is stale) was investigated to a
confident, checked "no" — it wasn't broken or stale, so there was nothing to file.

Fixed two tests in the existing suite that had hardcoded `action_pacing_readiness` as a
"real, currently-unverified" fixture id (one in `test_mechanism_registry.py`, one this session's
own prior ticket wrote in `test_mechanism_priority_derivation.py`) — the latter rewritten to
compute `priority()` directly against the registry's raw shape rather than depending on any two
mechanisms' current verified status, so it won't need fixing again the next time a top-ranked
mechanism gets verified. 139/139 tests passing, re-verified with `graphify-out/` genuinely moved
aside and restored.

This sets the pattern for the other 67: investigate the real claim first (not the atlas's citation
alone), build a genuinely differential scenario reusing existing compile-path infrastructure where
possible, record the honest verdict, and treat "is the state still accurate" as part of the
investigation rather than an assumption to carry through unchecked.

## Addendum — 2026-09-16, per peer review, before this session moved to the next target

**"Nothing to file" above was a conclusion this ticket had not actually measured.** Peer's own
question — how soon does a typical entity get its first `stats_dirty` recalculation event — was
answered with reasoning ("the formula self-corrects after the first event"), not a real number.
Measured directly, not assumed: instrumented `SkillScalingService.get_effective_stats` with a call
counter (validated against a positive control first) and ran three real corpus worlds
(`crowded_frontier`, `quest_dense_frontier`, `hero_guild_routing`) for 1000 ticks each, seed 42.
**Zero of 75 tested entities, across all three worlds, ever triggered the recalculation path**, and
separately, zero showed any change to `evolution_level`/`attributes`/`equipment`/`learned_skills`
at all in that window — broader than the already-recorded `COMB-318` finding (which only measured
combat-damage timing, not whether any entity's derived stats were ever recalculated).

Filed `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` (not fixed here) and
corrected `action_pacing_readiness`'s own `verified.note` in `mechanisms.yaml` to stop asserting
"not a new defect" — that claim was exactly what turned out to be unmeasured. `state`/`verdict`
themselves are unaffected: the readiness GATE this ticket verified is still genuinely `observed`
working; only the trailing explanatory note about the separate agility-scaling claim needed
correcting once the deeper measurement was actually taken.
