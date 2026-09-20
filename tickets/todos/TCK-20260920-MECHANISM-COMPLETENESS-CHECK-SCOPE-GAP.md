---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP
phase: open
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP

## Title
`mechanism_registry_completeness_check.py` only scans `src/domains/` and `src/systems/` — sizing
how much other live code the registry might be missing

## Status
OPEN

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
(none yet — sizing-only ticket; criteria belong to whichever future ticket picks this up)

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
(none yet — not started)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)
