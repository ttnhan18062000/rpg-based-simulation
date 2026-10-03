---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP

## Title
`mechanism_registry_completeness_check.py` only scans `src/domains/` and `src/systems/` — sizing
how much other live code the registry might be missing

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found while investigating `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`'s
own `perception` finding: `src/world/perception/gate.py::PerceptionGate` is real, live, wired code
(`src/engine/tactical.py`) with no registry mechanism entry at all. Investigated per direct peer
request — **a sizing question, not a batch**: is this one isolated miss, or the visible edge of a
category the existing completeness checker can't see?

`tools/mechanism_registry/mechanism_registry_completeness_check.py`'s own enumeration is scoped
to exactly two roots: `src/domains/*` and `src/systems/{economy_systems,lifecycle_systems,
social_systems,strategic_systems,world_systems}/*.py`. `src/world/` (where `PerceptionGate` lives),
along with `src/engine/`, `src/cognition/`, `src/strategy/`, `src/ai/`, `src/entities/`,
`src/town/`, `src/quests/`, `src/progression/`, `src/economy/`, `src/actions/`, `src/content/`,
`src/worldassembly/`, `src/worldbuilding/`, `src/worldgeneration/`, `src/worldmodules/`,
`src/scenarios/`, `src/simulation_quality/`, `src/lab/`, `src/content_semantics/`, and `src/core/`
are entirely outside this tool's scanned scope.

**The real number (a one-off manual sizing pass for this ticket, not yet a repeatable check)**:
across those uncovered, non-infra directories (infra/tooling dirs — `api`, `cli`, `certification`,
`config`, `logging`, `observability`, `perf`, `platform`, `rendering`, `replay`, `runtime`,
`testing`, `views` — excluded by the same category-level judgment the existing tool already
applies to its own 3 confirmed-infrastructure exclusions), 295 real `.py` files exist outside
`__init__.py`/tests, of which 261 have no `implemented_by` citation anywhere in the registry.
Narrowing to files defining a class matching this repo's own established mechanism-naming
convention (`Service`/`System`/`Gate`/`Phase`/`Evaluator`/`Resolver`/`Manager` suffix, the same
pattern every currently-bound entry already uses): 85 candidates, of which **14 have a real
caller outside their own defining file, in `src/`** — the same "genuinely wired" bar
`PerceptionGate` itself clears. `PerceptionGate` is one of those 14, not the only one.

**Verdict on the sizing question: not isolated.** 14 wired, unregistered, mechanism-shaped
candidates is closer to "the registry's own coverage claim needs re-languaging" than to "one
overlooked file" (per the peer's own stated threshold: "if it's one, fine, if it's twenty, ..."). A
caveat in both directions: (a) this heuristic is a floor, not a ceiling — class-naming conventions
outside the checked suffix list (e.g. `Classifier`, `Filter`, `Builder`, `Detector`) would add more;
(b) "unbound ≠ gap" applies here exactly as it already does for the existing domains/systems
check — some of these 14 almost certainly already belong to an existing mechanism's own
multi-file implementation, just not yet re-cited by path, so 14 is not 14 new mechanisms, it is 14
unresolved cases needing the same one-at-a-time disposition (bind, exclude with a reason, or
register new) the domains/systems check already established a process for.

The 14 candidates found this pass (for reference, not yet individually investigated):
`RelationProjectionService`, `RoleSemanticsService`, `DefaultSemanticsService`,
`FactionSemanticsService` (`src/content_semantics/`); `ReplayManager`, `ScenarioRuntimeService`,
`WorkerManager` (`src/engine/`); `EntityIdentityResolver` (`src/entities/`); `ScenarioSetupResolver`
(`src/scenarios/`); `MotivationPressureResolver`, `PerceptionGate` (`src/world/`);
`WorldAssemblyResolver`, `CompileProfileResolver` (`src/worldassembly/`); `ModuleParameterEvaluator`
(`src/worldmodules/`).

## Scope
Not scoped here — this ticket records the sizing finding per explicit instruction ("a sizing
question, not a batch, I want a number, not a fix"). A future ticket would decide whether to:
1. Extend `mechanism_registry_completeness_check.py`'s own enumeration to cover the remaining
   non-infra `src/` directories (the tool's own docstring already documents its current
   `domains`/`systems`-only scope as deliberate, not yet as complete).
2. One-at-a-time disposition of the 14 (and any more a wider check surfaces) via the domains/
   systems check's own established pattern: bind, exclude with a recorded reason, or register as a
   new mechanism.

## Out of Scope
- Extending the checker itself.
- Resolving any of the 14 candidates individually.
- `perception`'s own design-decision ticket (`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-
  INSTANTIATED`) — related, filed separately, not the same question.

## Acceptance Criteria
The ticket recorded none ("sizing-only ticket"); criteria used at implementation, set by the request that
scheduled it into this batch:
1. The sizing is a repeatable check with an explicit rule, not a one-off number.
2. Every candidate the check surfaces has a recorded disposition, and a new one fails a test.
3. The registry, its generated views, and the atlas/capabilities mappings stay consistent.

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — where this was found
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — the specific `PerceptionGate` case
- `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` — the original completeness pass this
  checker's own domains/systems scope came from

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/mechanism_registry/mechanism_registry_completeness_check.py`

## Assumptions / Open Questions
The 261/85/14 numbers are from a one-off manual pass, not a re-runnable check — if this ticket is
picked up later, re-derive rather than trust these numbers as still-current (the registry keeps
changing every batch this arc runs).

## Implementation Notes
**Premise re-verified, and partly stale.** The ticket's 261 / 85 / 14 did not reproduce. Under an explicit
rule the start-of-batch figures were 295 files in scope, 260 uncited, 102 unbound mechanism-shaped
classes, 49 wired (referenced from a different top-level package). The "14" matches no rule tried (any
reference gives 73; cross-package at file level gives 40). The ticket's own instruction ("re-derive rather
than trust these numbers") was followed, and the rule is now in the code.

**What was built.** `mechanism_registry_completeness_check.py` has a second tier (`enumerate_wider_
candidates`, `WIDER_EXCLUSIONS`, `WIDER_PENDING`, report section, JSON keys), report-only like the first.
`test_mechanism_registry_completeness_check.py` fails on any wired candidate without a disposition.

**Dispositions of the 49** (read-only triage by three investigators, identity calls by
rpg-feature-planning 2026-09-30, who declined two and held two):
- 16 bound at class level (WorldAssemblyResolver, CompileProfileResolver, ModuleParameterEvaluator ->
  `world_generation`; InventoryService; LifeStageService; CapabilityEstimateService; CampService and
  CreatureTerritoryService -> `camp`; ThreatService -> `regional_trauma`; ShopService -> `town_services`;
  live CapacityService -> `cognition_capacity_fatigue`; MotivationPressureResolver -> `tactical_decision`;
  LeadRoutingSystem and ScoreModifierSystem -> `strategic_intelligence_core`; AppraisalSystem ->
  `emotion`; CalamityService's producer method -> `calamity_intensity`, in the residue ticket).
- 12 registered as new mechanisms: `regional_monster_spawn`, `resource_ecology_regrowth`,
  `regional_transformation`, `production_role_vacancy`, `veterancy_rank`, `quest_lifecycle_resolution`,
  `intent_requirement_gating`, `regional_hazard_drain`, `humanoid_reproduction` (gated),
  `role_model_imitation` (gated), `faction_raid`, `refugee_displacement` (partial; depends on the dead
  `calamity_intensity` producer, recorded in the entry). Each carries a runtime `verified` block from a
  positive-controlled call counter; the 4 that recorded 0 calls are `inconclusive`, not claims of
  absence or of working (short horizon), and the 2 flag-gated ones are `observed` consistent with
  their OFF flag.
- 18 recorded as infrastructure exclusions (9 catalog resolvers, catalog-semantics services, metrics,
  scenario runtime, spatial query, identity resolver, a dataclass false positive).
- 3 pending, with reasons in `WIDER_PENDING`: `PerceptionGate` (held until the planner's perception
  contract relabelling lands), and two dead same-name twins (`progression/skills.py::SkillScalingService`,
  `strategy/cognition_capacity.py::CapacityService`) that are NOT registered because that would mint a
  mechanism for dead code; filed as `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`, which found four such
  pairs in `src/`.

Propagation: generated views and `mechanism_registry.html` regenerated; atlas badges fixed by the
surgical `mechanism_atlas_regenerate.py`; the wiring/atlas/capabilities mappings and pinned tests
updated; `docs/plans/mechanism_claims_as_tests_initiative.md` §3.4 updated. Not done: `PerceptionGate`
registration (waiting on the planner), and the heuristic still misses other naming conventions.

## Test Summary
`.venv/bin/python -m pytest tests/unit/tools -q` -> 438 passed (mechanism registry, completeness,
state-caller, atlas/capabilities, views, convergence). New tests: gap mechanisms reported separately,
no non-gap mechanism unbound, gap rule on a synthetic registry, every wider candidate dispositioned,
wider numbers pinned, exclusions/pending point at real candidates and carry reasons. Updated pins:
completeness (bound 36, unbound 25), atlas unmapped set (+12) and mapped count (73 -> 72), state-caller
findings (+`social_memory`, an import counted as a caller; runtime shows 0 calls), verification-view seed.

## Files Changed
- `tools/mechanism_registry/mechanism_registry_completeness_check.py`
- `registries/mechanisms.yaml` (12 new entries, 8+ bindings, see the residue ticket for the rest)
- generated: `docs/brainstorm/mechanism_{registry,verification,priority,system_rollup}_view.md`, `mechanism_registry.html`, `rpg_feature_atlas.html` (3 badge classes)
- `docs/plans/mechanism_claims_as_tests_initiative.md`
- tests: `tests/unit/tools/test_mechanism_{registry_completeness_check,atlas_regenerate,registry,state_caller_check}.py`
- `tickets/todos/TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS.md` (new), this ticket and its artifacts

## Completion Summary
Done, with three items left visible rather than forced: `PerceptionGate` (pending the planner's batch),
the two dead same-name twins (defect ticket). The wider sweep is a repeatable check with a stated rule; the
ticket's original "14" did not reproduce and the rule-based number was 49 wired candidates, every one now
bound, registered, excluded with a reason, or pending with a reason.
