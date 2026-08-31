---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION
phase: done
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_WORLD_EMERGENCE` before deciding its default

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_WORLD_EMERGENCE` was kept
`OFF` by default -- real call site (`WorldEmergencePhase.execute`, `src/engine/pipeline.py:290`), 3
test files, but no corpus profile turns it on and no SHADOW-validation history exists. This
ticket's job is to produce real evidence.

## Scope
- Run a real corpus-profile trial with the flag `ON` against at least one world.
- Confirm no unexpected interaction with `ENABLE_WORLD_CAPABILITY_LAYER` (a related, also-OFF
  flag not in this ticket's scope, but worth a direct check given the naming proximity).
- Produce a real keep/flip recommendation with evidence.

## Out of Scope
- Actually flipping the flag's default.
- `ENABLE_WORLD_CAPABILITY_LAYER`'s own default -- not part of the original 8-flag review, out of
  scope here too.

## Acceptance Criteria
- [x] A real corpus-profile ON trial is run and documented
- [x] A keep/flip recommendation with evidence is produced

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md

## Related Code Areas
- src/engine/pipeline.py (world_emergence phase)
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
None yet -- to be surfaced during this ticket's own investigation.

## Implementation Notes
Ran a real 4-leg OFF/ON corpus trial (`.venv/bin/python3 tools/calibrate_simq.py` with
`ENABLE_WORLD_EMERGENCE=ON` env-var override, per the already-supported mechanism both sibling
tickets used) against `dungeon_crawl` (seed 42, 2000 ticks) and `resource_dense_basin` (seed 42,
1000 ticks, `--profile default`), per `plan.md` Steps 1-3. World-loading confirmed via each run's
own tick-0 `chunk_0000.json` `entity_count` fingerprint (32 for `dungeon_crawl`, matching
`corpus_registry.yaml`) and successful exit-0 load for `resource_dense_basin` (a failed `--name`
resolution raises `FileNotFoundError`, never silently falls back).

Extracted and tallied the 4 real signal groups (never `world_emergence_event`, confirmed a red
herring by investigation.md) directly from each run's `chunk_*.json` `REFINED_UPDATE` payloads:
run/skip counters (100%/0% clean split on every leg), phase telemetry (`world_emergence_ms`/
`aggregates_generated`, present and nonzero on both ON legs only), quest-registry growth (zero on
all 4 legs — see Honest Gap below), and entity `exposed_world_signals`/`force_route_reevaluation`
property-update exposure (present in volume, 33869 and 18518/6563 respectively, on both ON legs
only, absent on both OFF legs).

No-suppression check passed on both structural and empirical halves for both worlds: the phase
runs on 100% of eligible ON-leg ticks (no starvation), and no domain-independent signal in
`simulation_events.jsonl` collapsed toward zero on either ON leg relative to OFF (SOCIAL-domain
contract/cooperation counts shifted ±13% in `dungeon_crawl`, all domain-independent counts
*increased* in `resource_dense_basin`) — confirms `WorldEmergencePhase.execute()`'s
`dataclasses.replace(update, ...)` pattern really does carry forward prior phases' work in a real
run, matching investigation.md's static finding.

**Honest gap (disclosed, not fixed):** neither trial world produced a single
`RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` `WorldEvent` in any leg (only `COMBAT_LOSS`, which
`QuestOpportunityGenerator` does not read) — despite both worlds being the best available
candidates per `corpus_registry.yaml`'s own density/archetype metadata. This means quest-registry
growth (Signal 3) is genuinely untestable from this trial, not evidence of suppression or a broken
mechanism (its own parity-ledger tests already cover it independently and pass). Recorded in
`trial_evidence.md`'s own "Honest gap" section per the orchestrator's hard constraint — not
resolved here, no follow-up ticket filed (orchestrator's call).

Added `tests/architecture/test_world_capability_layer_flag_inert.py`, modeled directly on
`tests/architecture/test_adventure_routing_flag_inert.py`, pinning the static finding that
`ENABLE_WORLD_CAPABILITY_LAYER` has zero live gating call site anywhere in `src/` and that no
`WorldCapabilityLayer` class/module exists at all — confirmed again this session via fresh grep
(4 non-gating hits: registration, a test-scaffold dict entry, and 2 known-flag allowlists).

Updated `docs/architecture/rollout_flag_decisions_m1.md`: the `ENABLE_WORLD_EMERGENCE` table row
now reflects the real trial outcome, and a new `## ENABLE_WORLD_EMERGENCE — Validation Trial
Result (TCK-20260826)` section was added after the `## ENABLE_SELF_MODEL_COGNITION` section and
before `## RolloutProfileManager — Cut`, folding in the `ENABLE_WORLD_CAPABILITY_LAYER`
static-inertness finding, matching both prior sections' structure exactly.

**Recommendation: Keep OFF, deferred.** `ENABLE_WORLD_EMERGENCE` still has zero shipped
`config/simulation_quality/profiles/*.yaml` turning it on (`grep -rl "ENABLE_WORLD_EMERGENCE"
config/simulation_quality/profiles/` returns nothing, confirmed live this session) — the same
DEV-003 gap that kept both sibling flags at "keep OFF, deferred" despite each having its own clean
trial. No `docs/guidelines/intentional_divergences.md` entry added (a "keep OFF" outcome creates
no divergence from the Mechanics Bible). No default was flipped in
`src/domains/optimization/feature_flags.py` for either flag — recommendation only, per the hard
constraint. No `src/` file was touched outside read-only investigation. No plan.md deviations —
all steps executed exactly as planned; the only elaboration beyond the plan's own text is the
concrete real numbers Steps 4-6 called for.

## Test Summary
All 4 scoped pytest command blocks from `test_plan.md`'s "Scoped Pytest Commands" section were run
via `.venv/bin/python3 -m pytest ...` and passed in full:
1. `tests/unit/domains/world_emergence/ tests/integration/domains/world_emergence/
   tests/integration/scenarios/test_phase8_world_emergence_scenarios.py
   tests/integration/scenarios/test_resource_depletion.py
   tests/perf/test_phase8_world_emergence_budget.py -m "not slow"` → **40 passed, 1 deselected**
2. `tests/unit/quest/test_quest_generation.py tests/unit/quest/test_quest_lifecycle.py
   tests/unit/world/test_sovereignty_events.py
   tests/unit/observability/test_event_shapers_world_dynamics.py` → **73 passed**
3. `tests/unit/config/test_phase10_feature_flags.py
   tests/integration/test_scenario_feature_flag_defaults.py
   tests/certification/test_phase10_enhanced_determinism_parity.py
   tests/architecture/test_adventure_routing_flag_inert.py
   tests/architecture/test_world_capability_layer_flag_inert.py` → **59 passed**
4. `tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off` →
   **1 passed, 3 deselected**

Total: 173 passed, 0 failed. `ENABLE_WORLD_EMERGENCE` confirmed absent from every
`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist copy, as expected under the "keep OFF" outcome.

## Files Changed
- `staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/trial_evidence.md` (new)
- `staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/plan.md` (no Deviations section
  needed — see Implementation Notes; frontmatter unchanged)
- `staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/investigation.md` (pre-existing
  from this run's own Investigate phase, not modified further during Implement)
- `staging_artifacts/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION/test_plan.md` (pre-existing from
  this run's own Plan phase, not modified further during Implement)
- `tests/architecture/test_world_capability_layer_flag_inert.py` (new)
- `docs/architecture/rollout_flag_decisions_m1.md` (row update + new section)
- `tickets/inprogress/TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION.md` (this file)

## Completion Summary
Ran a real 4-leg (`dungeon_crawl` + `resource_dense_basin`, OFF/ON) corpus trial for
`ENABLE_WORLD_EMERGENCE` via its existing env-var override. No suppression regression: the phase
runs on 100% of eligible ticks when ON and no independent domain's signal collapsed relative to
OFF. Real phase execution/telemetry/entity-signal-bridging all confirmed working, but neither
trial world produced a `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` event, leaving
quest-registry growth specifically untested (disclosed honestly, not smoothed over).
`ENABLE_WORLD_CAPABILITY_LAYER`'s naming-proximity question was resolved via static analysis
(zero live gating call site, no class exists) and pinned with a new regression-guard test. Final
recommendation: keep `ENABLE_WORLD_EMERGENCE` OFF, deferred — no shipped profile turns it on;
documented in `docs/architecture/rollout_flag_decisions_m1.md`. Neither flag's default was
changed in `feature_flags.py`. All 4 scoped regression command blocks pass (173 passed, 0
failed).
