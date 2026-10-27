---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
phase: done
date: 2026-09-30
tags: [core, bug]
---

# TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS

## Title
Same name, different referent: four mechanism-shaped classes exist twice in different modules, and one registry edge pointed at the wrong "social memory"; more instances need an audit and a guard

## Status
DONE

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
`agent-working/stored_artifacts/TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION/`.

**Fifth instance, at the concept level (found by rpg-feature-planning, 2026-09-30):** two things are
called "social memory": `campaign_state.faction_social_memories` (read by
`evaluate_social_consequence`, produced in `src/domains/campaigns/social_memory.py`) and the
`SocialMemoryService` class (0 runtime calls). The registry edge
`cross_episode_social_consequences -> social_memory` linked them; it was most likely written from the
comment "mirrors social_memory.py" in `consequence_events.py`, which means parallel structure, not
dependence. The edge is removed in `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`. The
audit here should therefore cover same-name-different-store as well as same-name-different-class
(compare the `owner_faction_id` overload).

**Sixth instance (also from rpg-feature-planning): three things named "social memory".** (1)
`src/systems/social_systems/memory.py::SocialMemoryService`, engine path, 0 runtime calls; (2)
`src/domains/campaigns/social_memory.py`, the `faction_social_memories` producer, campaign-only;
(3) `src/systems/social_memory.py`, a two-line re-export shim for (1). `from src.systems.social_memory
import SocialMemoryService` and `from src.systems.social_systems.memory import SocialMemoryService`
give the same class by different paths, while (2) is something else under a nearly identical module
name; a reader scanning imports cannot tell them apart.

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
- Audit for further same-name-different-referent instances (stores, concepts, registry edges), and beyond the mechanism-shaped suffix list (the scan found 24 names
  defined in more than one module; the other 20 are mostly data records and need only a quick look).
- Add an architecture guard test that fails when a new mechanism-shaped class name is defined in two
  `src/` modules without an allowlist entry that states why.

## Out of Scope
- Registering any of these as a mechanism (decided: no).
- Changing simulation behaviour: the live copy of each pair is unchanged.

## Acceptance Criteria
- [x] Each of the four pairs has a recorded decision (keep A, keep B, or keep both with a reason) and
      the dead copy is removed or explicitly kept with a stated reason.
- [x] A guard test enumerates same-name mechanism-shaped classes across `src/` and fails on an
      unlisted pair.
- [x] The remaining 20 duplicate names from the scan are each classified (data record, intentional,
      or defect).

## Related Tickets
- `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (first instance)
- `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP` (where the pairs surfaced)
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`

## Related Docs
None.

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION/` (runtime probe output).

## Related Code Areas
`src/core/items.py`, `src/core/recipes.py`, `src/core/registries.py`, `src/progression/skills.py`,
`src/engine/rpg_depth.py`, `src/strategy/capacity.py`, `src/strategy/cognition_capacity.py`.

## Assumptions / Open Questions
- Whether `engine.rpg_depth.SkillScalingService.get_effective_stats` is itself dead on the live path
  (planning's measurement says zero firings) is a separate question for whoever takes this.

## Implementation Notes
Rulings: rpg-planner (u24), relayed via lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu on 2026-10-27; word for word in `rpg_planner_rulings_2026-10-27.md` (staging, now stored). NOT owner approvals.
Cross-domain edit: agent-working-planner agreed on 2026-10-28, via rpg-planner-ubuntu, to the `tools/mechanism_registry/mechanism_registry_completeness_check.py` WIDER_PENDING edit as it stands, including the four extra pins in tests/unit/tools/test_mechanism_registry_completeness_check.py (they count them under their condition 2); the PR body names it a cross-domain edit with their agreement and they review it on the PR. They asked for that test file to be re-run after the last rebase onto origin/main (done at the sync before the push).
- DELETED `src/progression/skills.py::SkillScalingService` (zero src callers; every caller imports `src/engine/rpg_depth.py`). Removed its two cases from test_progression_v2.py and repointed 3 doc rows (attribute_progression_contract.md:341; docs/simulation/domains/progression_contract.md:27/168/198) to src/engine/rpg_depth.py. Its WIDER_PENDING row is removed; pins: len(WIDER_PENDING) 2->1, scope_files 345->344, unbound_files 249->248, candidates 69->68, wired 20->19, each with a dated comment.
- DELETED `src/core/governance.py::EnvironmentCapture` (no reader; `src/certification/models.py` is the live one).
- KEPT both `CapacityService` (capacity.py enforces; cognition_capacity.py derives, unwired: TCK-20261027-HUNGER-CAPACITY-DERIVATION-HAS-NO-LIVE-CALLER), both `ItemRegistry` (TCK-20260914), the legacy `RecipeRegistry` (TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED), each with an allowlist reason.
- Guard: tests/unit/core/test_same_name_class_guard.py (21 recorded names; unlisted, stale and reasonless rows fail). It sits under tests/unit only because testing-planner was not running; testing-planner may move it to tests/architecture.
- ObservabilityMode / HardwareClass / ErrorResponse: classified only, no renames.

## Test Summary
tests/unit/core/test_same_name_class_guard.py + test_progression_v2.py 26 passed; test_mechanism_registry_completeness_check.py 14 passed; completeness check script 0 undispositioned; tests/tools/test_agent_working_paths_guard*.py 11 passed; tests/unit/tools full run follows the last registry edit.

## Files Changed
src/progression/skills.py (deleted), src/core/governance.py, tools/mechanism_registry/mechanism_registry_completeness_check.py, tests/unit/core/test_same_name_class_guard.py (new), tests/unit/progression/test_progression_v2.py, tests/unit/tools/test_mechanism_registry_completeness_check.py, two doc contract files.

## Completion Summary
Two dead twins deleted, three pairs kept with stated reasons, all 21 remaining duplicate names classified and guarded.
