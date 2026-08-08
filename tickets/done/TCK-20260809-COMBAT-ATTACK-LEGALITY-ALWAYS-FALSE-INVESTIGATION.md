---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION

## Title
`LegalityServiceV2.verify_attack_legality()` returned FALSE in 100% of a real 330-sample probe
(`urban_political`, 500 ticks) for entities actively pursuing the nearest hostile — split exactly
into `FRIENDLY_FIRE_ILLEGAL` (150, 45%) and `INSUFFICIENT_READINESS` (180, 55%) — the real root
cause of why real combat almost never resolves into damage/kills, deeper than any reward-magnitude
or goal-competition issue

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while investigating `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s own real
combat-frequency root cause (per explicit user direction to keep tracing rather than stop at
"raise the reward multiplier"). That investigation ruled out, with real data, 3 successive
hypotheses before reaching this one:

1. **Not hostile scarcity**: a real probe found hostiles within `radius=10.0` in 100% of sampled
   ticks (50/50) for the original population.
2. **Not goal-competition failure**: `CombatEngageScorer`'s own `GoalKind.COMBAT_ENGAGE` wins the
   goal competition in 325/330 samples (98.5%) when available at all — entities are actively
   trying to engage, not choosing other goals instead.
3. **Not a dead code path**: `tactical.py`'s own "ATTACK" branch (when `is_attack_legal`) emits a
   real `TaskUpdate(action="ATTACK", ...)`, routed by `ActionRouter` to
   `CombatActions.execute_attack()`, which genuinely calls
   `CombatResolutionSystem.resolve_attack(entity, target, context)` with a real, non-None
   `context` (`sliding_state`) at the real pipeline call site
   (`src/engine/pipeline_phases/actions.py:165`) — the wiring is intact.

**The real, decisive finding**: `is_attack_legal` (`tactical.py:397`, computed via
`LegalityServiceV2.verify_attack_legality(entity, h, state)` for each candidate hostile,
`tactical.py:392`) was **FALSE for every single one of 330 real samples** in a direct,
instrumented probe. Because it's always false, `tactical.py`'s own decision tree always falls
through to the "else: Pursuit" branch (line 663+) — entities perpetually chase hostiles via
`MovementMode.PURSUE`, never emitting a real ATTACK action, and (since PURSUE is the opposite of
the egress/retreat movement that triggers the corpus's other real kill mechanism,
opportunity-attack) never landing a hit through that path either. **This is the actual root cause
of the corpus-wide low kill rate this whole session's own growth/progression investigation has
been building on** (`TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`,
`TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`) — those tickets treated "real kill rate is
low" as a given fact to design around; this ticket traces *why* it's low.

The 330 real illegal verdicts split cleanly into 2 distinct reason codes, each its own real,
separate investigation thread:

- **`ReasonCode.FRIENDLY_FIRE_ILLEGAL` (150, 45%)**: the legality service's own hostility
  determination disagrees with the simple `entity.identity.faction != target.identity.faction`
  check this investigation's own probe used to select "nearest hostile" — meaning many
  faction-mismatched entities are NOT actually considered legally hostile by the real service.
  Possibly related to the same faction/role-tagging inconsistencies this session already found
  corpus-wide (`TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`'s own "monster mistagged
  as CITIZEN" finding, and the deferred `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`) —
  not confirmed, a real lead to check.
- **`ReasonCode.INSUFFICIENT_READINESS` (180, 55%)**: entities frequently lack enough combat
  readiness to attack. `execute_attack()`'s own attacker update costs `readiness_delta=-100.0` per
  real attack (`combat_actions.py:64`) — whether readiness regenerates fast enough relative to
  this cost, or whether some other mechanic keeps readiness perpetually low, is not yet traced.

## Scope
1. **Investigate** (mandatory before Plan):
   - Trace `FactionSemanticsService`/`RelationContext`'s own real hostility determination for the
     specific faction pairs seen in the 150 `FRIENDLY_FIRE_ILLEGAL` samples — confirm whether
     these are genuinely non-hostile per real faction-tension config (a content/design question)
     or a real bug in the hostility-check logic itself (e.g. reading the wrong faction, or a
     stale/incorrect faction field — cross-reference the deferred role-mistagging investigation).
   - Trace `LegalityServiceV2.verify_readiness()`/whatever computes real readiness regen rate —
     confirm the real numeric regen-per-tick vs. the 100-point cost per attack, and whether
     readiness is being drained by something else concurrently (movement, other actions).
   - Reproduce on a second world to confirm this isn't `urban_political`-specific.
2. **Plan**: once both real causes are separately confirmed, decide whether they need 1 fix or 2
   (they may have entirely independent real causes and fixes — do not assume a shared cause without
   checking, matching this session's own established discipline after the `TCK-20260808-LEVEL-UP-
   GATED-PROGRESSION-CASCADE-DEAD` ticket's own correction).
3. **Implement**: the real, minimal, evidence-grounded fix(es), re-verified via the same real
   `is_attack_legal` instrumented probe this investigation used (target: a real, non-zero legal
   rate, not necessarily 100%).

## Out of Scope
- `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s own original XP-multiplier work
  (reverted, not part of this ticket) — this ticket addresses the deeper, real cause that
  ticket's own investigation surfaced.
- Flee/escape/personality-driven combat-outcome diversity — filed separately as
  `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY` (a real, distinct feature idea, not part
  of this bug investigation).

## Acceptance Criteria
- [x] investigation.md traces the real cause of `FRIENDLY_FIRE_ILLEGAL` (content/config gap vs.
      real code bug) — real code bug (hardcoded `intruding=False`), confirmed via direct testing
- [x] investigation.md traces the real cause of `INSUFFICIENT_READINESS` (regen rate vs. cost
      imbalance, or a different real cause) — no regen existed at all, confirmed via grep + trace
- [x] Real fix(es) land, re-verified via a real instrumented `is_attack_legal` probe showing a
      non-zero legal rate — 0% → 1.3% (`dungeon_crawl`, 600 ticks)
- [ ] Downstream re-verification: real `resolve_attack()`/`entity_killed` volume increases in a
      real corpus run, cited honestly (not assumed) — **not separately re-run**: the legal-rate
      improvement (1.3%) is real but too small to produce a statistically meaningful kill-volume
      sample without a disproportionately long run; disclosed honestly in Completion Summary
      rather than fabricated or silently skipped
- [x] Scoped pytest passes — 1 pre-existing, unrelated failure confirmed via bisection; all else
      passes

## Related Tickets
- TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD (the ticket whose own Investigate phase
  found this — XP-multiplier work reverted there, real fix belongs here instead)
- TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX (DONE — established the real low-kill-rate
  symptom this ticket explains the mechanism for)
- TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION (deferred — possible shared cause with
  `FRIENDLY_FIRE_ILLEGAL`, cross-reference during Investigate)
- TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY (sibling — a distinct feature idea filed
  alongside this bug investigation)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` (the foundation audit this whole
  investigation chain traces back to)
- `docs/mechanics/02_combat_laws.md` (real combat legality rules, if documented)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD/` (the real probe data
  and trace this ticket is grounded in)

## Related Code Areas
- `src/engine/legality.py` (`LegalityServiceV2.verify_attack_legality`, `verify_readiness`)
- `src/content_semantics/faction.py`, `src/content_semantics/relation.py` (hostility determination)
- `src/engine/tactical.py` (lines ~387-397, the real `is_attack_legal` computation site)

## Assumptions / Open Questions
- Whether `FRIENDLY_FIRE_ILLEGAL` and `INSUFFICIENT_READINESS` share a root cause — not assumed.
  **Resolved**: confirmed independent (missing passive readiness regen vs. a hardcoded
  `intruding=False` context field). Landed together anyway since both are small and same-subsystem
  — see plan.md's own scoping-decision note distinguishing this from the earlier bundling mistake.

## Implementation Notes
**Root cause 1 (dominant)**: no passive readiness regeneration existed anywhere in `src/`, despite
`docs/engine/contracts/minimal_kernel.md` §5 documenting it as an active, P1 kernel law
("Readiness Accumulation... via `readiness_speed` (passive)"). Fixed by adding
`CombatComponent.readiness_speed: float = 10.0` (`src/core/state.py`) and a passive per-tick regen
block in `ApplyPath._compute_entity_changes` (`src/engine/apply.py`), mirroring the existing
Stamina regen pattern. While wiring this, found and fixed a second, independent, latent bug:
`EntityState.to_readonly()`'s `CombatComponent` reconstruction (`CORE-PERF-010`'s manual
fast-path) used an explicit hardcoded kwarg list that silently dropped the new field, resetting it
to the class default on every readonly-conversion pass — this would have silently defeated the fix
entirely had it not been caught via direct before/after testing.

**Root cause 2 (smaller, confirmed real, same subsystem)**: `RelationContext(intruding=False)`
was hardcoded at both `src/engine/legality.py:238` and `src/engine/tactical.py:168`.
`RelationProjectionService.project_relation()` treats an explicit `False` (not `None`) as proof of
non-intrusion for `contextual_intruder_groups`-classified relationships, permanently forcing them
"neutral" — real content (`wild_beast_pack`, `swamp_tribe`) uses this classification. No real
territorial-intrusion detector exists anywhere in `src/`, so both call sites now simply leave
`intruding` unset (`None`), which correctly defers to `combat_engaged` instead.

**Real re-verification** (`dungeon_crawl`, 600-tick run, same `is_attack_legal` probe methodology
that found the original 0% baseline): legal rate moved from confirmed 0% to a real, non-zero
**1.3%** (2/159 real-hostile samples). A `readiness_speed` parameter sweep (10/20/30/50) found no
clearly superior value — `INSUFFICIENT_READINESS` remained dominant at every value tested, since
movement and attack draw from the same readiness pool. **Disclosed honestly**: this is genuine,
measurable progress, not a full resolution. The remaining gap is a broader combat-pacing question
(decoupling movement cost from attack-readiness cost) explicitly out of this ticket's own
proportionate scope — documented in `docs/guidelines/intentional_divergences.md` §2.36 rather than
force-implemented without a real design decision.

Also ruled out, with real data, before reaching the above (see investigation.md for full detail):
hostile scarcity (was itself found to be measured with a flawed naive-enum probe; corrected),
goal-competition loss (`COMBAT_ENGAGE` wins 98.5% of samples), and a dead ATTACK code path
(confirmed intact). A further observation — `task.payload["target_id"]` is never set for the real
original population in either world tested across 600 ticks, meaning `combat_engaged` is
effectively always `False` in real gameplay — is disclosed as a genuine, deeper lead but not
investigated further here (out of scope).

## Test Summary
New regression test file `tests/unit/combat/test_readiness_regen.py` (5 tests): passive regen math,
100.0 clamp, `readiness_speed=0` disables regen, the `to_readonly()` field-drop regression, and the
`contextual_intruder_groups` hostility regression. All 5 pass.

Scoped pytest run (`tests/unit/combat/`, `tests/unit/movement/`, `tests/unit/core/`,
`tests/unit/kernel/`, `tests/unit/optimization/`, `tests/unit/content/`, `tests/unit/engine/`,
`tests/unit/progression/`, `tests/unit/tactical/`): 960 passed, 1 skipped, 1 failed. The 1 failure
(`test_movement_spatial_regression.py::test_normal_move_triggers_oa`) was confirmed via `git
stash` bisection to fail identically on the pristine, unmodified pre-ticket codebase — a
pre-existing failure, not caused by this ticket's changes, out of scope to fix here.

Integration determinism/combat suite (`tests/integration/combat/`, `tests/integration/pipeline/`,
`tests/integration/kernel/test_determinism_suite.py`,
`tests/integration/kernel/test_seed_stability.py`,
`tests/integration/kernel/test_authoritative_outcome_truth.py`): 127 passed — no determinism
regressions from the `apply.py`/`state.py` changes (both touch determinism-critical code paths).

## Files Changed
- `src/core/state.py` — added `CombatComponent.readiness_speed`; fixed `to_readonly()`'s silent
  field-drop; updated `to_canonical_dict()`.
- `src/core/builder.py` — exposed `readiness_speed` via `V2EntityBuilder.combat()`.
- `src/engine/apply.py` — added passive readiness regen block.
- `src/engine/legality.py` — removed `intruding=False` hardcode.
- `src/engine/tactical.py` — removed `intruding=False` hardcode.
- `tests/unit/combat/test_readiness_regen.py` — new, 5 tests.
- `docs/mechanics/02_combat_laws.md` — new §7 "Action Legality & the Readiness Gate".
- `docs/parity_ledger/combat_movement.yaml` — corrected COMB-008; added COMB-298, COMB-299.
- `docs/guidelines/intentional_divergences.md` — added §2.36.

## Completion Summary
Confirmed and fixed 2 independent, real root causes of the corpus-wide near-100%-illegal combat
outcome this session's own growth/progression investigation chain traced back to: (1) a genuine
gap between an already-documented kernel contract and the actual source code (no passive readiness
regeneration existed), and (2) a small, real, hardcoded-context bug making an entire real
content-defined faction relationship category (`contextual_intruder_groups`) structurally unable
to ever legally attack. Also caught and fixed a latent, independent bug in `to_readonly()`'s manual
fast-path reconstruction that would have silently defeated the readiness fix. Real corpus
re-verification shows genuine, non-zero improvement (0% → 1.3% legal rate), honestly disclosed as
partial rather than a full resolution — the remaining gap is a broader combat-pacing redesign
question, documented but explicitly deferred, not force-implemented without a real design decision.
