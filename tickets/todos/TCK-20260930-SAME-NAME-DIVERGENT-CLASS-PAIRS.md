---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
phase: open
date: 2026-09-30
tags: [core, bug]
---

# TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS

## Title
Four mechanism-shaped classes exist twice under one name in different modules, one copy live and one dead or diverged; the fifth-and-later instances need an audit and a guard

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found while dispositioning the wider-scope completeness sweep
(`TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`), and raised by `rpg-feature-planning`
(2026-09-30): the same class name is defined in two modules, callers import one of them, and which
class you get depends on which module you imported. `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-
FAILURE-SEMANTICS` is the first instance (an implementer is fixing it). A deterministic scan of
`src/` (top-level class definitions, name ending `Service`/`System`/`Gate`/`Phase`/`Evaluator`/
`Resolver`/`Manager`/`Registry`) finds **four pairs**:

| Class | Module A | Module B | Evidence |
|---|---|---|---|
| `ItemRegistry` | `src/core/items.py` | `src/core/registries.py` | the first instance, own ticket |
| `RecipeRegistry` | `src/core/recipes.py` (legacy, 3 entries) | `src/core/registries.py` (catalog-bootstrapped, 25 entries) | `world/providers/*` import `registries`; `domains/progression/material_predicate.py` documents having read the legacy one |
| `SkillScalingService` | `src/progression/skills.py` | `src/engine/rpg_depth.py` | every caller (`engine/apply.py`, `engine/domain/skill_actions.py`, `domains/campaigns/orchestrator.py`) imports the rpg_depth class; the progression class has **no caller anywhere in `src/`** and recorded 0 calls at runtime |
| `CapacityService` | `src/strategy/cognition_capacity.py` | `src/strategy/capacity.py` | `capacity.py` is live (`CapacityEnforcementPhase`, 6517 `trim_dict` calls in a 2-world probe); `cognition_capacity.py`'s only caller is recorded as never-called by `cognition_capacity_fatigue`'s own note, 0 runtime calls |

Runtime probe (positive-controlled per-method counters, `Kernel.tick_once()` over
`crowded_frontier` / `quest_dense_frontier` / `frontier_living_world`, seed 42, 1000 ticks each):
`progression.skills.SkillScalingService` 0 calls, `engine.rpg_depth.SkillScalingService` 0 calls too
(planning's own instrumented run measured zero `get_effective_stats` firings as well, so the
surviving class may itself be partly dead on that path), `strategy.cognition_capacity.CapacityService`
0 calls. Probe output:
`stored_artifacts/TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION/`.

This is the same "dual-class divergent semantics" family for each pair: the registry does not
register the dead twin as a mechanism (`WIDER_PENDING` in
`tools/mechanism_registry/mechanism_registry_completeness_check.py` records the decision), because
minting a mechanism for dead code is the failure the completeness checker exists to prevent.

## Scope
- Decide per pair which copy is authoritative, and delete or re-export the other (deleting dead code
  follows the `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION` precedent: confirm zero callers,
  including tests, first).
- For `RecipeRegistry` and `ItemRegistry`, check whether the legacy copy still has readers and align
  failure semantics (the first instance's ticket already covers `ItemRegistry`; coordinate, do not
  duplicate).
- Audit for further instances beyond the mechanism-shaped suffix list (the scan found 24 names
  defined in more than one module; the other 20 are mostly data records and need only a quick look).
- Add an architecture guard test that fails when a new mechanism-shaped class name is defined in two
  `src/` modules without an allowlist entry that states why.

## Out of Scope
- Registering any of these as a mechanism (decided: no).
- Changing simulation behaviour: the live copy of each pair is unchanged.

## Acceptance Criteria
- [ ] Each of the four pairs has a recorded decision (keep A, keep B, or keep both with a reason) and
      the dead copy is removed or explicitly kept with a stated reason.
- [ ] A guard test enumerates same-name mechanism-shaped classes across `src/` and fails on an
      unlisted pair.
- [ ] The remaining 20 duplicate names from the scan are each classified (data record, intentional,
      or defect).

## Related Tickets
- `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (first instance)
- `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP` (where the pairs surfaced)
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`

## Related Docs
None.

## Related Stored Artifacts
`stored_artifacts/TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION/` (runtime probe output).

## Related Code Areas
`src/core/items.py`, `src/core/recipes.py`, `src/core/registries.py`, `src/progression/skills.py`,
`src/engine/rpg_depth.py`, `src/strategy/capacity.py`, `src/strategy/cognition_capacity.py`.

## Assumptions / Open Questions
- Whether `engine.rpg_depth.SkillScalingService.get_effective_stats` is itself dead on the live path
  (planning's measurement says zero firings) is a separate question for whoever takes this.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
