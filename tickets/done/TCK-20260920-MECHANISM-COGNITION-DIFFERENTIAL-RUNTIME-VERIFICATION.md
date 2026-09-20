---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION
phase: done
date: 2026-09-20
tags: [simulation-quality, testing, cognition]
---

# TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION

## Title
Runtime-evidence program, batch 1: the differential scenario harness, proven on 3 of the
`cognition` system's 20 `code_trace`-only mechanisms before scaling to the rest

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
New program approved after PR #229: make "verified" mean the simulation did the thing, not that
the code says it would. `cognition` is the target system — 20 mechanisms, all 20 `code_trace`,
0% runtime-backed (`runtime_verified_share` = 0.0 for this group), and the system where dormant
mechanisms have been hardest to see across this whole arc.

This is the harness-proving batch, not the full 20: 3 mechanisms, chosen deliberately (not
defaulted) per explicit criteria — one `done` mechanism that genuinely matters, one where a
contradiction is genuinely plausible (not a safe pick), and one known negative for calibration.
Every scenario must have real differential structure — a check that can't fail proves nothing.

**Governing constraint, explicit and absolute**: if an instrument contradicts a claim, record the
contradiction and stop. Do not fix the code to make a claim true in this pass.

## Scope
1. Build the differential scenario harness pattern (extends the one prior real use,
   `TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION`, to a second and third real
   mechanism, proving the pattern generalizes rather than being a one-off).
2. Verify `belief_cycle` (`done`, load-bearing) via a real differential scenario.
3. Verify `perception` (`done`, chosen as the "plausible contradiction" slot after direct
   investigation found a real, unexpected dead-chain risk, not picked as a safe pass).
4. Verify `quest_generation_sourcing` (known `orphan`/`contradicted`) as the calibration case — if
   the harness reports it as running, the harness itself is broken.
5. Record whatever verdicts the instrument actually produces, including a state correction if
   `perception`'s runtime result confirms it is unreached in production.
6. File (not fix) any real defect found.

## Out of Scope
- The remaining 17 `cognition` mechanisms — explicitly deferred until the harness design is
  reported to and reviewed by the peer session.
- `goal_hierarchy` — considered for the "matters" slot, not selected this batch (see
  `investigation.md` for the reasoning; larger surface, no added harness-proving value for batch 1).
- Fixing `PerceptionUpdatePhase`'s wiring gap, if confirmed — a separate ticket.
- Any SimQ corpus work — this program is verification infrastructure only, changes no simulation
  behavior, and does not collide with the roadmap session's own measurements.

## Acceptance Criteria
1. 3 new scenario test files under `tests/mechanic_scenarios/`, each with a real, differential
   assertion through a real compiled world and a real `Kernel.tick_once()` dispatch (or, for the two
   calibration/negative cases, a positive-control direct call alongside the real-dispatch zero-call
   assertion).
2. All 3 mechanisms carry a `verified` block with `instrument: scenario` (upgrading from
   `code_trace`), recording the actual verdict — not adjusted toward a favorable answer.
3. Any state correction (e.g. `perception`'s `state`) is made only if the runtime evidence supports
   it, with the reasoning recorded in the entry's own note.
4. `registry.py::validate()` clean; consumer artifacts regenerated.
5. Harness design reported to the peer session before any further cognition mechanisms are
   attempted.

## Related Tickets
- `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` — the prior batch this program is a
  direct, more rigorous successor to (peer explicitly cited its own re-languaged `code_trace`-only
  shape as the failure mode this harness exists to avoid repeating).
- `TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION` — the one prior real use of the
  differential scenario component this ticket extends.
- `TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY` — the `runtime_verified_share`
  metric this batch's own verdicts will move (and are not being optimized to move).

## Related Docs
- `docs/plans/mechanic_verification_scenarios_proposal.md`
- `docs/plans/mechanism_claims_as_tests_initiative.md` (§3.3 — the selection-effect finding this
  batch's candidate selection was deliberately built not to repeat)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION/`

## Related Code Areas
- `src/systems/strategic_systems/belief.py::BeliefCycleSystem`
- `src/domains/perception/filter.py::PerceptionFilterService`,
  `src/domains/perception/phase.py::PerceptionUpdatePhase`
- `src/systems/world_systems/quests.py::QuestGenerationSystem`
- `src/engine/pipeline.py`
- `tests/mechanic_scenarios/`
- `registries/mechanisms.yaml`

## Assumptions / Open Questions
See `investigation.md` for the full candidate-selection reasoning and per-mechanism differential
design.

## Implementation Notes
Built 3 real differential scenario files under `tests/mechanic_scenarios/`, extending the one
prior real use of this component (`TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION`)
to a second and third mechanism, reusing `mechanic_scenario_combat_judgement_withdrawal` (already
real, compiled, catalog-driven) rather than authoring a new world.

- **`belief_cycle`**: `observed`. A lead staged `certainty=APPROXIMATE`/`discovered_tick=0`
  demotes to `VAGUE` through a real `Kernel.tick_once()` once `state.tick=50` clears
  `stale_threshold`, and stays unchanged at `state.tick=10`. Real, unconditional pipeline entry
  point (`pipeline.py:408`) confirmed at runtime, not just by code trace.
- **`perception`**: `contradicted`. Investigated as a candidate for the "matters" slot (peer named
  it as one of three equally valid options) and found, unexpectedly, that
  `PerceptionUpdatePhase` — the only thing that would call `PerceptionFilterService.filter()` from
  the real pipeline — is never instantiated anywhere in `src/` outside its own file. 5 real ticks
  against a world with an adjacent, alive, hostile entity produced zero `.filter()` calls and an
  empty `perceived_entities` on both entities; a positive control (direct call) proved the code
  itself works. `state` corrected `done` → `orphan`; a real, unexpected finding, not a manufactured
  one — moved into the "plausible contradiction" slot after the evidence pointed there, per the
  explicit instruction not to default to a safe pick. Filed, not fixed:
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`.
- **`quest_generation_sourcing`** (calibration): `contradicted`, confirmed correct. A region forced
  to `trauma_score=0.9` (clears `generate_from_scar()`'s own real trigger threshold) produced zero
  real calls to any of `QuestGenerationSystem`'s 3 methods across 5 ticks, with a positive control
  (direct call) confirming the code itself produces a real `QuestTemplate` when invoked. The
  harness correctly reported the known negative rather than a false positive — the calibration this
  batch needed before trusting the other two verdicts.

Consumer-artifact regeneration surfaced two real drifts from `perception`'s state correction (both
expected, both fixed): `docs/brainstorm/rpg_feature_atlas.html`'s badge (`mechanism-atlas-
regenerate`) and `docs/brainstorm/simulation_capabilities.html`'s tier (`mechanism-capabilities-
regenerate`, `live` → `built`, plain 3-tier language). `docs/brainstorm/rpg_simulation_wiring_map.html`'s
Entity Operating Loop diagram had no automated fix path (report-only script) — hand-edited PER's
node label and class assignment (`live` → `bug`) to match, following the diagram's own existing
convention for other dead/gap mechanisms (MEM/INT/MOT/CNV/TRD/TUP/COM already carry inline
`:::bug`/`:::gated`).

`mechanism_state_caller_check.py`'s own report (informational, "report not verdict") flagged
`perception` as `orphan_with_callers` — expected and correctly explained by the entry's own new
note: the checker sees `phase.py` as a real caller of `PerceptionFilterService` without checking
whether `phase.py`'s own class is itself ever reached, the exact one-level-deep blind spot this
runtime scenario exists to catch. Pinned in `test_mechanism_state_caller_check.py`'s own findings
set alongside the same-shape `commitment_betrayal`/`chronicle` cases.

## Test Summary
6 new tests across 3 files in `tests/mechanic_scenarios/`, all passing. Full scoped suite
(`tests/unit/tools/ tests/mechanic_scenarios/`): 273 passed (2 real fixes needed along the way —
one pinned-findings-set test updated for the new `perception` finding, one wiring-map classdef
drift test that needed the hand-edit above; both are real, understood, documented changes, not
loosened assertions). `registry.py::validate()`: clean, 93 mechanisms. All consumer-artifact checks
(`mechanism-atlas-check`, `mechanism-capabilities-check`, `mechanism-registry-html-check`,
`mechanism-wiring-map-classdef` script): clean after regeneration.

## Files Changed
- `tests/mechanic_scenarios/test_belief_cycle_lead_staleness.py` (new)
- `tests/mechanic_scenarios/test_perception_pipeline_wiring.py` (new)
- `tests/mechanic_scenarios/test_quest_generation_sourcing_orphan_calibration.py` (new)
- `registries/mechanisms.yaml` — `belief_cycle`/`quest_generation_sourcing` upgraded to
  `instrument: scenario`; `perception` state corrected `done` → `orphan`, verdict `observed` →
  `contradicted`
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_registry_view.md`,
  `mechanism_system_rollup_view.md`, `mechanism_registry.html` — regenerated
- `docs/brainstorm/rpg_feature_atlas.html` — badge regenerated (`mechanism-atlas-regenerate`)
- `docs/brainstorm/simulation_capabilities.html` — tier regenerated (`mechanism-capabilities-
  regenerate`)
- `docs/brainstorm/rpg_simulation_wiring_map.html` — PER node hand-edited (label + classdef)
- `tests/unit/tools/test_mechanism_state_caller_check.py` — pinned-findings set updated
- `docs/REGISTRY.yaml` — regenerated
- `tickets/todos/TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED.md` — filed, not fixed

## Completion Summary
DONE. Harness proven on 3 deliberately-chosen mechanisms, not defaulted: `belief_cycle` (done,
matters, confirmed genuinely working at runtime), `perception` (a real, unexpected contradiction
found by direct investigation rather than picked as a safe pass), `quest_generation_sourcing`
(known negative, harness correctly discriminates rather than false-positiving). All 3 now carry
`instrument: scenario` verdicts. One real state correction made (`perception`), the fix itself
deliberately not made, per this program's explicit governing constraint. `runtime_verified_share`
moved as a side effect of honest verdicts, not optimized for. Harness design (2 real signals
checked per calibration/negative case: field-state absence + call-counter; direct-call positive
controls throughout; real compiled worlds and real `Kernel.tick_once()` dispatch, never a synthetic
fixture) reported to the peer session for review before scaling to the remaining 17 `cognition`
mechanisms, per explicit instruction.

## Addendum — 2026-09-20, peer review of the harness design before scaling
Harness approved with one structural caveat, applied here rather than carried forward as debt:

1. **Codified two rules in `docs/plans/mechanic_verification_scenarios_proposal.md` §5** (items 3
   and 4, not just practiced as habit): every negative/calibration verdict must pair a direct-call
   positive control with the real-dispatch zero-result (already true of both this batch's
   contradicted verdicts, now a stated requirement); every `contradicted`/`orphan` verdict grounded
   in "zero calls observed" must declare which backing it rests on -- (a) a static
   never-instantiated fact independent of world choice, or (b) a demonstrated precondition (the
   scenario's own world shown, not assumed, to produce the real trigger).
2. **Added explicit "Backing:" statements** to `perception` ((a) static -- `PerceptionUpdatePhase`
   has zero constructors anywhere in `src/`, holds regardless of world) and
   `quest_generation_sourcing` (both (a) and (b) -- zero real callers independent of world, plus
   the scenario's own world demonstrated to clear the real trigger threshold).
3. **Investigated `perception`'s own zero-dependents shape**, per direct request, without editing
   `depends_on` edges: not an under-declared edge -- zero real code anywhere in `src/` reads any
   `PerceptionModel` field at all outside the dead chain itself, so there is no real functional
   dependency to have under-declared. `goal_hierarchy`'s own note already documents strategic
   cognition sourcing situational awareness through a separate real path instead
   (`SpatialQueryService.nearby_entities()`). Conclusion: `perception` genuinely was never
   load-bearing -- nothing downstream was ever built to consume its output either, so the
   zero-dependents shape is accurate, not a registry gap. Adjacent finding, not the same one: a
   real, live, unregistered `src/world/perception/gate.py::PerceptionGate` exists
   (`src/engine/tactical.py`), but answers a narrower question (raw sense-detection gating for
   `tactical_decision`'s targeting) than `perception`'s own concept -- not a misbinding risk.
4. **Runtime share before/after**, pulled from the regenerated rollup rather than left uncomputed:
   `cognition` system 0/20 (0.0%) -> 3/20 (15.0%); registry-wide baseline 9/82 verified (11.0%) ->
   12/82 verified (14.6%).

No registry verdicts changed in this addendum -- documentation and investigation only, per the
peer's own framing ("apply the caveat," not "re-verify"). Cleared to proceed to the remaining 17
`cognition` mechanisms under the same constraints.
