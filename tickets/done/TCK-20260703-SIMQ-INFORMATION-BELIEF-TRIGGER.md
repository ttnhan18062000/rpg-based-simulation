---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER
phase: done
date: 2026-07-03
tags: [simulation_quality, information, belief, cognition, self-model, deferred]
---

# TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER

## Title
Seed pending_information_responses compile-time plumbing for Branch A + fix the kernel tick-alignment bug blocking belief_assimilated (and calamity_spawned, GovernorModeChanged) from firing through the live loop

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260702-SIMQ-UPLIFT2-INFORMATION` shipped compile-time scaffolding for
`information_source_profiles`, but investigation found that scaffolding alone cannot produce any
INFORMATION-pillar events: `InformationBeliefPhase.apply()`'s two trigger branches are unreachable
independent of that fix.

Investigation for this ticket (2026-07-03) evaluated the idea doc's two options (Branch B / paid-info
path) and found both require new cross-phase event plumbing beyond this ticket's intended scope. A
third, lower-risk path was found instead: seed `AuthoritativeState.pending_information_responses` at
compile time (mirroring the parent ticket's `information_source_profiles` schema/compiler/resolver
pattern), reaching Branch A's already-implemented, already-tested assimilation logic
(`InformationResponseNormalizer`/`InformationAssimilationService`) without touching
`SelfModelUpdatePhase`, `InformationNeedDetector`, or `state.information_providers`.

**A second, separate, pre-existing bug was found during implementation and verified by a focused
follow-up investigation (2026-07-03):** `Kernel._phase_advancement()` calls
`EventExtractor.extract()` with `current_state` already advanced to `tick+1`
(`src/engine/kernel.py:702-736`), but `InformationBeliefPhase.apply()` stamps
`last_assimilated_tick = state.tick` using the pre-advance tick
(`src/domains/information/phase.py:77`). `EventExtractor.extract()`'s `== tick` check
(`event_extractor.py:286`) therefore never matches through the real `Kernel.tick_once()` loop —
confirmed by direct instrumented execution (0 `belief_assimilated` events across 5 real ticks, despite
the compile-time seed and assimilation logic working correctly). Two other event types share this bug
(`calamity_spawned`, `event_extractor.py:899`; `GovernorModeChanged`, `kernel.py:836`).

A focused follow-up investigation (2026-07-03) sized the fix: **3 one-line changes** (compare against
`prior_state.tick` instead of the shared post-advance `tick` variable, at `event_extractor.py:286`,
`event_extractor.py:899`, and `kernel.py:836`), zero existing tests break (every current
`EventExtractor.extract()` test uses the same-state-twice pattern, unaffected either way), and the
correct fix direction is supported by the codebase's own convention (`_phase_persistence`'s `TICK_END`
already uses post-advance tick for a different, still-correct purpose — this fix only touches the
three specific stamped-property comparisons, not the shared `tick` variable's broader meaning). The
real risk is not code risk but calibration-baseline risk: fixing it is a genuine first-time behavior
change to WORLD/INFORMATION pillar scoring (since `calamity_spawned`/`belief_assimilated` have never
fired through any real run before), so it needs targeted recalibration spot-checks, not a silent
drive-by change.

Per 2026-07-03 user direction: given the fix is confirmed small and low-code-risk, **this ticket's
scope is expanded to include the 3-line kernel/observability fix**, alongside the
`pending_information_responses` plumbing, plus targeted recalibration (not a full 30-scenario sweep)
covering `urban_political` (this ticket's target) and 1-2 spot-check scenarios with calamities and/or
governor-mode transitions to confirm the newly-unblocked `calamity_spawned`/`GovernorModeChanged`
events don't introduce unexpected grade movement elsewhere.

## Scope
1. Schema + compiler + resolver plumbing for `pending_information_responses` (mirrors the parent
   ticket's `information_source_profiles` pattern): `PendingInformationResponseSpec` on
   `WorldSpec`/`WorldCompositionSpec`/`NormalizedWorldComposition`, compiler resolution of
   `target_population_id` to a compiled `actor_id`, resolver passthrough.
2. World content: seed `urban_political/world.yaml` with one entry targeting `pop_0`
   (`bandit_road_danger`, `KNOWN_FACT`).
3. Direct-pipeline integration tests proving `belief_assimilated` fires correctly via
   `AuthoritativeApplyPipeline.refine()` and that the seed is single-fire (not carried forward past
   tick 0 by `ApplyPath.apply_generation()` — an accepted, documented, bounded outcome, not a bug).
4. Kernel tick-alignment fix: 3 one-line changes comparing against `prior_state.tick` instead of the
   shared post-advance `tick` variable at `event_extractor.py:286` (`belief_assimilated`/
   `belief_updated`), `event_extractor.py:899` (`calamity_spawned`), and `kernel.py:836`
   (`GovernorModeChanged`). Do not change `_phase_observability`'s `tick` assignment itself or any
   other use of the shared `tick` variable — surgical, per-callsite fixes only.
5. Recalibrate `urban_political_*` scenarios (this ticket's target) to confirm
   `belief_assimilated calibration_hits > 0` through the real live loop; spot-check 1-2 additional
   long-running scenarios with calamities/governor-mode transitions to confirm
   `calamity_spawned`/`GovernorModeChanged` now firing as expected, with no unintended grade
   regressions elsewhere; `make evaluate --dry-run` 0 regressions.
6. Update `docs/simulation_quality/event_type_coverage.md` and
   `docs/parity_ledger/infrastructure.yaml::INFRA-256`/new `INFRA-257` to reflect the pillar as
   genuinely active (not scaffolding-only); add/update parity entries for the kernel tick-alignment
   fix itself and for `calamity_spawned`/`GovernorModeChanged` becoming reachable.

## Out of Scope
- Re-litigating the schema/compiler/resolver plumbing already shipped by
  `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` (assume it is correct)
- A full information marketplace or NPC query-response loop
- Activating INFORMATION in any world other than `urban_political`
- Wiring Branch B (`self_model.knowledge.unknowns`/`SelfModelUpdatePhase`) or the paid-information
  path (`InformationNeedDetector`/`state.information_providers`) — this ticket only wires Branch A
- A full 30-scenario recalibration sweep — targeted spot-checks only (per Scope item 5); if the
  spot-checks surface unexpected regressions beyond `urban_political`/the checked scenarios, stop
  and surface to a human rather than expanding the sweep unilaterally

## Acceptance Criteria
- [x] `AuthoritativeState.pending_information_responses` contains 1 entry (`pop_0`,
      `bandit_road_danger`) after compilation of `urban_political`
- [x] Direct-pipeline integration test proves `belief_assimilated` fires and a real `KnowledgeFact`
      is assimilated via `AuthoritativeApplyPipeline.refine()`
- [x] Single-fire behavior confirmed and documented (not carried forward past tick 0) — confirmed
      (Step 6: exactly 1 fire at tick 0, 0 thereafter across 5 real ticks) and documented via
      plan.md's Step 9 as `docs/guidelines/intentional_divergences.md` §2.23 "Single-Fire
      Compile-Time-Seeded Response" (rationale class Bounded), added to the summary table too.
- [x] Kernel tick-alignment fix applied (3 one-line changes); `belief_assimilated`,
      `calamity_spawned`, and `GovernorModeChanged` all confirmed reachable through the real
      `Kernel.tick_once()` loop where applicable — mechanism verified for all 3 via dedicated unit
      tests (Step 8). `belief_assimilated`/`GovernorModeChanged` additionally confirmed firing
      naturally in real calibration/baseline runs (Step 10). `calamity_spawned`'s tick-gate
      comparison is verified fixed by its unit test, but natural firing was **not** observed in the
      one-off `dungeon_crawl_seed42_5200t` diagnostic run — CalamityService also requires
      `calamity_intensity > 0.3` in some region (hero-death-dependent), a separate, pre-existing
      content precondition not exercised in that run and not fixed by this kernel change. Documented
      honestly in `docs/parity_ledger/infrastructure.yaml::INFRA-258` and
      `docs/simulation_quality/event_type_coverage.md` — not claimed as "now producing
      calibration_hits > 0" for `calamity_spawned`.
- [x] At least one `urban_political_*` calibration run shows `belief_assimilated calibration_hits > 0`
      through the real live loop (not just the direct-pipeline test) — confirmed in all 7
      `urban_political_*` runs (calibration_hits == 1 each), via `calibrate_simq.py` through the real
      `Kernel.tick_once()` loop.
- [x] `make evaluate --dry-run` exits 0 (0 regressions on targeted spot-check scenarios) — confirmed:
      250 pillars checked, 0 regressions, 0 missing.
- [x] `docs/simulation_quality/event_type_coverage.md` and parity ledger updated to reflect the
      pillar as genuinely active, plus the kernel fix's own parity entry — done this pass (see
      Implementation Notes below).

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION — parent; shipped scaffolding, deferred this work
- TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO — original root-cause diagnosis (incomplete; this ticket
  and its parent correct/extend it)
- TCK-20260702-SIMQ-UPLIFT2-FACTION — sibling ticket; compiler-plumbing template already applied
  by the parent ticket

## Related Docs
- `docs/plans/idea_information_belief_trigger_wiring.md` — primary source; full investigation,
  options, and recommendation
- `docs/simulation_quality/event_type_coverage.md` — rows for `belief_assimilated`,
  `paid_information_transaction`, `lead_certainty_updated`, and sibling INFORMATION/COGNITION rows
  updated 2026-07-03 by the parent ticket to note the scaffolding-shipped/trigger-still-dead state
- `docs/parity_ledger/infrastructure.yaml::INFRA-256` — scaffolding-verified/pillar-inactive entry
  shipped by the parent ticket 2026-07-03; this ticket's completion should revise its `status`/
  `text`/`divergence_note`/`support_boundary` to reflect genuine activation (extends `INFRA-245`)
- `docs/mechanics/04_strategic_cognition.md` — has no chapter on `InformationSourceProfile` /
  `InformationBeliefPhase` at all; flagged as a Mechanics Bible coverage gap by the parent
  ticket's investigation, may need a new section depending on which option is chosen

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/investigation.md` — full file:line
  evidence for the dead trigger paths

## Related Code Areas
- `src/domains/information/phase.py:28-110` — `InformationBeliefPhase.apply()`, both dead branches
- `src/core/state.py:1144` — `AuthoritativeState.pending_information_responses` (never written)
- `src/core/self_model.py:179` — `self_model.knowledge.unknowns` (never populated)
- `src/cognition/self_model_phase.py:32-56` — `SelfModelUpdatePhase.apply()`, hardcoded `events=[]`
- `src/cognition/knowledge_model.py:93-101` — `KnowledgeModelService.assimilate()`
- `src/engine/domain/cognition_extras.py:36-98` — `InformationNeedDetector.detect_and_generate()` (orphaned)
- `src/town/guild.py:11-` — `GuildAction.visit()` (orphaned)
- `src/engine/pipeline_phases/paid_information.py:74-183` — `PaidInformationTransactionSystem.enforce()`
- `src/core/state.py:1150` — `AuthoritativeState.information_providers` (different field from
  `information_source_profiles` — do not conflate)
- `src/engine/kernel.py:702-736` — `Kernel._phase_advancement()`, calls `EventExtractor.extract()`
  with `current_state` already advanced to `tick+1`
- `src/engine/kernel.py:806-855` — `Kernel._phase_observability()`, `tick = self._state.tick`
  (post-advance)
- `src/engine/kernel.py:836` — `GovernorModeChanged` emission, affected by the same tick-alignment bug
- `src/observability/event_extractor.py:70-81` — `EventExtractor.extract()`, `tick = current_state.tick`
- `src/observability/event_extractor.py:286` — `belief_assimilated`/`belief_updated` `== tick` check,
  affected
- `src/observability/event_extractor.py:899` — `calamity_spawned` `== tick` check, affected
- `src/world/calamity.py:56` — stamps `last_calamity_tick_set` using pre-advance `state.tick`
- `src/engine/apply.py:329,403` — `factions=new_factions` carried forward correctly (confirmed
  UNAFFECTED by the tick-alignment bug — different mechanism, direct diff not stamped-timestamp)

## Assumptions / Open Questions
- UQ-1 (resolved 2026-07-03): Branch A compile-time seed chosen over Branch B/paid-info path —
  lowest blast radius, reuses tested assimilation code, no shared cognition-pipeline changes.
- UQ-2 (resolved 2026-07-03): `ENABLE_SELF_MODEL_COGNITION` does NOT need to be ON — Branch A
  bypasses `SelfModelUpdatePhase` entirely.
- UQ-3 (resolved 2026-07-03): kernel tick-alignment fix is 3 one-line changes (compare against
  `prior_state.tick` at the three sites above), zero existing tests break, confirmed via focused
  investigation in `staging_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/tick_alignment_bug_investigation.md`.

## Implementation Notes
Implemented Steps 1-6 of `staging_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/plan.md`
exactly (schema/compiler/resolver plumbing for `pending_information_responses`, `urban_political`
content seed, and integration tests). Steps 7-9 (docs, recalibration) are explicitly deferred to a
follow-up implementation pass per this run's scope instruction.

- Step 1: added `PendingInformationResponseSpec` (frozen Pydantic model) to
  `src/worldbuilding/schema.py`, mirrored on `WorldCompositionSpec`/`NormalizedWorldComposition` in
  `src/worldassembly/schema.py`.
- Step 2: `WorldAssemblyResolver.assemble()` passes `pending_information_responses` through
  unmerged (no catalog contribution path exists, same as `information_source_profiles`).
- Step 3: `WorldCompiler.compile()` resolves `target_population_id` -> compiled `actor_id` via
  `entity.properties["population_id"]` matching (inserted after the entity-compilation loop,
  before the final `AuthoritativeState(...)` assembly); unmatched targets are skipped with a
  warning appended to the existing `warnings` list.
- Step 4: seeded `urban_political/world.yaml` with one entry (`pop_0`, subject
  `bandit_road_danger`, `KNOWN_FACT`, `town_notice_board`); regenerated
  `resolved/world.resolved.yaml` via `python -m src.worldbuilding.cli resolve urban_political`
  (not hand-edited). Diff confirmed only the new `pending_information_responses:` block changed in
  the resolved YAML; `assembly_report.json`/`validation_report.json`/`provenance_manifest.json`
  changed only in incidental fingerprint/timestamp/set-ordering noise, the same pre-existing class
  of regeneration noise documented by the FACTION/parent-INFORMATION tickets.
- Steps 5-6: added two integration tests to
  `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` that load the actual
  compiled `urban_political` state (not a hand-built fixture) and drive it through the real
  `AuthoritativeApplyPipeline.refine()` / `ApplyPath.apply_generation()` path:
  `test_compiled_urban_political_state_fires_belief_assimilated` (proves `belief_assimilated`
  fires with the expected payload and a real `KnowledgeFact` is assimilated) and
  `test_pending_information_response_fires_exactly_once_not_carried_forward` (drives 5 tick
  advancements, confirms exactly 1 `belief_assimilated` total and `pending_information_responses`
  is `[]` from the first `apply_generation()` onward).

**Material finding beyond the approved plan's scope (relevant to Step 8, not fixed here):**
while empirically verifying Step 5/6 against the real `Kernel.tick_once()` loop (the same path
`tools/calibrate_simq.py` drives), direct execution showed `EventExtractor.extract()` never
observes `belief_assimilated` when driven through `Kernel._phase_advancement()`
(`src/engine/kernel.py:702-736`): `_phase_observability(prior_state, update)` is called with
`self._state` already advanced to `tick+1` (`_phase_advancement` reassigns `self._state` via
`ApplyPath.apply_generation(..., next_tick=self._state.tick + 1, ...)` before calling
`_phase_observability`), while `InformationBeliefPhase.apply()` stamps
`property_updates["last_assimilated_tick"] = state.tick` using the **pre-advance** tick
(`src/domains/information/phase.py:77`). `EventExtractor.extract()`'s own `tick = current_state.tick`
(`event_extractor.py:81`) is therefore always one tick ahead of `last_assimilated_tick`, so the
`prop.get("last_assimilated_tick") == tick` check (`event_extractor.py:286`) never matches through
the live per-tick loop — confirmed via direct instrumented execution of
`Kernel(profile=PROD_SMALL, state=<compiled urban_political state>, rng=...).tick_once()` for 5
ticks: zero `belief_assimilated`/`belief_updated` events captured, even though
`state.pending_information_responses` and the resulting `self_model_bundle_set`/property_updates
were confirmed correctly populated at tick 0. This appears to be a **pre-existing, one-tick
misalignment in `Kernel._phase_advancement()`'s observability wiring**, not something introduced by
this ticket's schema/compiler/resolver work, and not unique to `belief_assimilated` — the only other
`== tick` comparison in `event_extractor.py` (`last_calamity_tick_set`, line 899) would have the same
exposure. Every existing `EventExtractor` unit test in the repo
(`tests/unit/observability/test_event_extractor_*.py`) calls
`EventExtractor.extract(state, state, update, mode)` with the **same** state object for both
`prior_state`/`current_state` — i.e. none of them exercise the live Kernel's actual N-vs-N+1
state pairing, so this discrepancy was not previously caught. Steps 5/6's tests above follow that
same established repo convention (matching `state.tick` on both sides of `extract()`), which is
internally consistent with `phase.py`'s own tick-stamping and accurately proves the compiled seed
processes through Branch A correctly — but it means **Step 8's recalibration (out of scope for this
implementation run) is likely to show `belief_assimilated`/`belief_updated` `calibration_hits == 0`
via `simulation_events.jsonl`, not `> 0`, unless this separate `Kernel._phase_advancement()`
tick-pairing issue is also fixed** — a fix explicitly out of this ticket's scope (no changes to
`kernel.py`/`apply.py` were authorized). This should be surfaced to a human/architecture-review
before anyone attempts Step 8, since Step 8's stated AC may not be achievable through the live
engine loop without that separate fix.

**Steps 7-8 (implemented this pass, per `staging_artifacts/.../plan.md` Steps 7-8, approved
2026-07-03):**

- Step 7 — kernel tick-alignment fix, exactly the 3 one-line changes specified in the plan (fix
  (b)+(b'), not the rejected fix (a) global relabel):
  - `src/observability/event_extractor.py:286` — `prop.get("last_assimilated_tick") == tick` ->
    `== prior_state.tick` (`belief_assimilated`/`belief_updated`).
  - `src/observability/event_extractor.py:899` — `getattr(update, "last_calamity_tick_set", None)
    == tick` -> `== prior_state.tick` (`calamity_spawned`).
  - `src/engine/kernel.py:836` — `getattr(self._status, "last_transition_tick", -1) == tick` ->
    `== prior_state.tick` (`GovernorModeChanged`).
  - No other `== tick` comparisons touched (verified each site's exact current text via direct
    read before editing, per this run's instruction — line numbers matched the plan's snapshot
    exactly, no drift). The shared `tick = current_state.tick` (`event_extractor.py:81`) and
    `tick = self._state.tick` (`kernel.py:815`) labels used for every `SimulationEvent.tick` field
    were left unchanged, as required.
- Step 8 — added 4 regression items:
  1. `test_belief_assimilated_fires_through_real_tick_once_loop` (new,
     `tests/integration/observability/test_kernel_event_recording.py`): builds the Kernel from the
     actual compiled `urban_political` state (reusing the Step 5/6 compile pattern), calls
     `kernel.tick_once()` once, asserts `belief_assimilated` for `pop_0` with
     `payload["subject"] == "bandit_road_danger"` in `kernel._event_recorder.events`.
  2. `test_calamity_spawned_fires_through_real_tick_once_loop` (new, same file): hand-built minimal
     `AuthoritativeState(tick=5000, last_calamity_tick=0, regions={one region with
     calamity_intensity=0.5})` — satisfies `CalamityService.CALAMITY_FORCE_INTERVAL` (5000) and
     `CALAMITY_MIN_INTERVAL` (2000) gates simultaneously, and `PROD_SMALL`'s
     `cadence.world_dynamics` (100) divides 5000 evenly so `WorldDynamicsSystem.resolve_dynamics()`
     (wired into `AuthoritativeApplyPipeline.refine()` at `src/engine/pipeline.py:277`, which calls
     `CalamityService.process_world_dynamics()` at `world_dynamics.py:133`) actually runs this tick.
     One `kernel.tick_once()` call fires `calamity_spawned` exactly once. Confirmed the event's own
     `tick`/`payload["tick"]` fields still use the post-advance tick (5001, i.e. `state.tick + 1`)
     — only the gating comparison was fixed, not the event's tick label, per the plan's explicit
     scope guard.
  3. `test_governor_mode_changed_fires_through_real_tick_once_loop` (new, same file): seeds
     `state.work_debt` above a small `profile.max_work_debt`, which makes
     `ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py:76`) return `SURVIVAL` on the
     very first `_phase_init()` call, escalating from `RuntimeStatus`'s default `NORMAL` and
     stamping `last_transition_tick` with the pre-advance tick via `reset_dwell()`. One
     `kernel.tick_once()` call fires `GovernorModeChanged` with `payload["current_mode"] ==
     "SURVIVAL"`.
  4. Regression-confirmation (no new test code): ran
     `tests/unit/observability/test_event_extractor_cognition.py` and
     `tests/unit/observability/test_event_extractor_world.py` in full after the Step 7 fix — all 31
     tests across both files still pass unmodified, confirming the fix is a true no-op for the
     repo's established `prior_state is current_state` test pattern, exactly as the
     `tick_alignment_bug_investigation.md` predicted.
- Broader regression sweep also run and green (see Test Summary below): `tests/unit/observability/`,
  `tests/integration/observability/`, `tests/integration/kernel/`,
  `tests/unit/world/test_calamity_pressure_propagator.py` + `test_calamity_raid.py` (no
  `test_calamity*.py` exists elsewhere in the repo), `tests/unit/resource/test_resource_governor_contract.py`
  (no `test_governor*.py` file exists under `tests/unit/engine/`; this is the actual governor
  contract test file), and Steps 1-6's own test files (re-run to confirm zero interaction with the
  Step 7 fix).
- Steps 9-11 (docs: `intentional_divergences.md`, recalibration, `event_type_coverage.md` + parity
  ledger `INFRA-257`/`INFRA-258`) were completed in subsequent passes — see below.

**Step 10 — targeted recalibration, per `plan.md`'s Step 10 exactly:**

*Part A — `urban_political` (info-plumbing), all 7 anchor scenarios plus the `dungeon_crawl`
spot-check:*
- Ran `tools/calibrate_simq.py` for `urban_political_seed{42_200,42_500,123_500,456_500,
  42_1000,123_1000,456_1000}t` and `dungeon_crawl_seed42_200t` (profile `dungeon_crawl`) through
  the real `Kernel.tick_once()` live loop (not the direct-pipeline test path).
- **Confirmed `belief_assimilated` fires with exactly 1 hit in every one of the 7
  `urban_political_*` runs** (verified by grepping each run's fresh `simulation_events.jsonl` for
  `"event_type": "belief_assimilated"` — count is `1` in all 7, `0` in the `dungeon_crawl` spot-check).
  This is the first time this has been observed through the real live loop — the Step 7 kernel fix
  works as intended. `belief_updated` also fires exactly once per `urban_political_*` run (also
  confirmed via grep), `0` in `dungeon_crawl`. `lead_certainty_updated`/`paid_information_transaction`
  remain `0` everywhere, as expected (out of scope, not the chosen trigger path).
- Grade movement measured (not guessed): every `urban_political_*` anchor's `INFORMATION` pillar
  moved `C -> B` (the single `belief_assimilated` hit, weight-scaled by tick count, is enough to
  cross the C/B threshold in all 7 scenarios). `dungeon_crawl_seed42_200t`'s `INFORMATION` stayed
  `C` (0 events) — 0 leakage confirmed.
  **Additional finding beyond the plan's explicit verification bullets:** `belief_updated` is also
  in `CognitionScorer.EVENT_TYPES` (`src/simulation_quality/scorers/cognition.py:14-20`, tag
  `belief_active`) — a distinct scorer from `InformationScorer` (which only listens for
  `belief_assimilated`, not `belief_updated`). This means the same natural, plan-anticipated
  `belief_updated` single-fire ("expected... natural consequence" per plan.md Step 10 Part A) also
  moves the `COGNITION` pillar `C -> B` in 6 of the 7 scenarios (`urban_political_seed123_1000t`'s
  `COGNITION` anchor was already `B`, so no change there). Verified this is the *only* additional
  pillar affected — a full pillar-by-pillar diff of all 7 measured reports against their pre-existing
  anchors showed diffs limited to `{INFORMATION, COGNITION}` only, no other pillar moved on any
  `urban_political_*` scenario. Both moves are within `evaluate_simq.py`'s `±1` grade-band tolerance
  (`PASS`, not `REGRESS`), consistent in direction (improvement, not regression) and magnitude
  (single low-weight event) with the plan's own stated expectation for `belief_updated`, so this was
  treated as in-scope/expected rather than a stop-condition trigger — but is called out explicitly
  here since the plan's Step 10 write-up did not name `COGNITION` by pillar.
- `grade_anchors.json` updated for exactly the 7 `urban_political_*` entries, touching only the
  `INFORMATION` (all 7) and `COGNITION` (6 of 7) keys that actually changed grade; no other keys/
  entries touched.

*Part B — `calamity_spawned`/`GovernorModeChanged` spot-checks:*
- **`GovernorModeChanged`: confirmed present.** Regenerated fresh `simulation_events.jsonl` for the
  4 longest-duration existing baseline scenarios (`dungeon_crawl_seed{42,123,456}_2000t`,
  `sandbox_world_seed42_2000t` — their original run directories under `data/runs/` no longer existed,
  per this repo's standard `data/runs/` cleanup convention, so "inspect existing runs" required a
  fresh same-seed/same-tick regeneration rather than reading a stale artifact). All 4 regenerated
  quality reports match their `grade_anchors.json` entries exactly (0 diffs, confirming determinism
  held). `GovernorModeChanged` was found firing 63-73 times in each of the 4 runs (real runtime
  resource-governor transitions under sustained 2000-tick load) — confirms the event fires through
  the real loop as the kernel fix intended. Per the plan, this is infrastructure telemetry not scored
  by any SimQ pillar, so this has no grade implication either way.
- **`calamity_spawned`: did NOT fire — diagnostic run at `dungeon_crawl_seed42_5200t` shows 0 hits,
  contradicting the plan's stated expectation.** Ran the exact one-off diagnostic specified in the
  plan (`--ticks 5200 --seed 42 --name dungeon_crawl --profile dungeon_crawl`). `WORLD` pillar
  graded `B` (no regression, no unexpected movement — consistent with 0 `calamity_spawned`
  contribution). Root-caused via direct inspection: the tick-alignment fix (Step 7) is necessary but
  **not sufficient** — `CalamityService.process_world_dynamics()` (`src/world/calamity.py:32-56`)
  gates the actual spawn (and therefore `last_calamity_tick_set`, which
  `event_extractor.py:899`'s now-fixed comparison depends on) behind `high_intensity_regions = [r
  for r in state.regions.values() if r.calamity_intensity > 0.3]` — and `calamity_intensity` is only
  ever raised by `CalamityService.apply_calamity_consequences()` when a `kind == "hero"` entity dies
  in a region with `hazard_level > 0.5`. The 5200-tick run's `simulation_events.jsonl` shows
  `combat_kill` events (monsters) and `near_death_survival` events (entities reduced to 0 HP but
  surviving) but no hero-death signal, and `calamity_intensity` never crosses 0.3 in any region, so
  `should_spawn` is satisfied by the tick-interval math at tick 5000 but the `high_intensity_regions`
  gate is never met, and no `calamity_spawned` event is ever emitted — independent of, and
  unaffected by, the Step 7 fix. This is corroborated by Step 8's own dedicated unit test
  (`test_calamity_spawned_fires_through_real_tick_once_loop`), which had to hand-construct a state
  with `calamity_intensity=0.5` directly rather than relying on natural gameplay to reach that
  threshold — i.e., the test suite already implicitly assumed this precondition would not arise
  naturally. **This is a content/mechanics-level gap in the `calamity_intensity` accumulation path
  (hero-death-dependent), separate from and not closed by this ticket's kernel tick-alignment fix.**
  Per this run's explicit instruction, did not expand the sweep to other worlds/seeds or attempt to
  manufacture a hero death to force the event — surfacing this finding for a human decision instead
  (e.g., whether a follow-up ticket should investigate why heroes appear not to die under
  `near_death_survival`, or whether a different diagnostic scenario with an intentionally fragile
  hero would exercise this path). Per this ticket's stop-condition guidance, this does not itself
  constitute an "unexpected grade regression" (no pillar moved further than expected; `WORLD` stayed
  at the same grade family as the existing 2000t baselines) — it is instead a **confirmation
  shortfall**: Part B's `calamity_spawned` spot-check could not be positively confirmed. Not added to
  `grade_anchors.json` (one-off diagnostic only, per the plan's explicit scope guard); its
  `data/calibration/dungeon_crawl_seed42_5200t/quality_report.json` output was left in place
  (gitignored, non-authoritative) for traceability.
- `python3 tools/evaluate_simq.py --dry-run`: exit 0, **250 pillars checked, 0 regressions, 0
  missing** across the full anchor file (all `urban_political_*` movements landed within the ±1
  grade-band tolerance as `PASS`, every other world/scenario's grades were unchanged).
- `data/runs/*` and `reports/release_proof/*` cleaned after extracting the needed event counts
  (both gitignored, ephemeral).

**Net assessment:** Part A (this ticket's actual scope — `belief_assimilated`/`belief_updated` via
`pending_information_responses`) is fully confirmed working end-to-end through the real live loop,
with 0 unintended regressions. Part B's `GovernorModeChanged` spot-check also confirms cleanly.
Part B's `calamity_spawned` spot-check surfaced a **new, previously-undocumented residual gap**
(the `calamity_intensity` hero-death precondition) that is outside this ticket's approved scope to
fix — flagged here rather than silently absorbed, per the project's traceability rule. Steps 9 and
11 (docs/parity ledger updates) were completed in a subsequent pass, reflecting this Part B finding
precisely: `calamity_spawned` is documented as kernel-fix-verified-correct (unit test) but NOT
claimed as unconditionally reachable through the live loop — the content-gate half (hero-death
precondition) remains a separate, unfixed observation, stated honestly in `INFRA-258` and
`event_type_coverage.md`.

## Test Summary
- `tests/unit/worldbuilding/test_worldspec_schema.py` (unmodified, still passes — regression guard)
- `tests/unit/worldbuilding/test_world_compiler.py`: added
  `test_compiler_seeds_pending_information_responses_from_spec`,
  `test_compiler_pending_information_response_unmatched_population_is_skipped_with_warning`,
  `test_compiler_no_pending_information_responses_declared_yields_empty_list`,
  `test_urban_political_resolved_world_seeds_one_pending_information_response`
- `tests/unit/worldassembly/test_assembly.py`: added
  `test_resolver_passes_pending_information_responses_from_composition`,
  `test_resolver_no_pending_information_responses_declared_yields_empty_list`, and a mirrored-field
  assertion block (6) inside `test_composition_normalization_shorthand_and_mixed`
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`: added
  `test_compiled_urban_political_state_fires_belief_assimilated`,
  `test_pending_information_response_fires_exactly_once_not_carried_forward`
- Full run: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/integration/domains/
  tests/integration/scenarios/test_phase5_information_belief_scenarios.py
  tests/unit/domains/information/ tests/unit/observability/` — 953 passed, 1 skipped, 0 failures.
- No regression sweep across other calibration worlds needed for this run: change is confined to
  `urban_political`'s composition-level content plus schema/compiler/resolver code paths that are
  no-ops (empty list) for every world with no `pending_information_responses` key, verified by the
  explicit "no key declared -> empty list" regression tests at each layer.

**Steps 7-8 test run (this pass):**
- `tests/integration/observability/test_kernel_event_recording.py`: added
  `test_belief_assimilated_fires_through_real_tick_once_loop`,
  `test_calamity_spawned_fires_through_real_tick_once_loop`,
  `test_governor_mode_changed_fires_through_real_tick_once_loop` — all pass (4 passed total in this
  file, including the pre-existing `test_kernel_observability_event_recording`).
- `pytest tests/unit/observability/test_event_extractor_cognition.py
  tests/unit/observability/test_event_extractor_world.py` — 31 passed, 0 failed (confirms the
  Step 7 fix is a no-op for the existing `prior_state is current_state` test pattern).
- `pytest tests/unit/observability/ -m "not slow"` — 745 passed, 1 skipped.
- `pytest tests/integration/observability/ -m "not slow"` — 94 passed, 3 skipped.
- `pytest tests/integration/kernel/ -m "not slow"` — 91 passed, 3 deselected.
- `pytest tests/unit/world/test_calamity_pressure_propagator.py tests/unit/world/test_calamity_raid.py`
  — 11 passed.
- `pytest tests/unit/resource/test_resource_governor_contract.py` — 2 passed.
- `pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py
  tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldassembly/test_assembly.py` — 58
  passed (Steps 1-6 regression re-confirmed unaffected by the Step 7 fix).

## Files Changed
- `src/worldbuilding/schema.py` — `PendingInformationResponseSpec`, `WorldSpec.pending_information_responses`
- `src/worldassembly/schema.py` — `WorldCompositionSpec`/`NormalizedWorldComposition.pending_information_responses` + import
- `src/worldassembly/resolver.py` — `WorldAssemblyResolver.assemble()` passthrough
- `src/worldbuilding/compiler.py` — `target_population_id` -> `actor_id` resolution + `AuthoritativeState(pending_information_responses=...)` seeding
- `data/worlds/urban_political/world.yaml` — seeded 1 entry (`pop_0`, `bandit_road_danger`, `KNOWN_FACT`)
- `data/worlds/urban_political/resolved/world.resolved.yaml` — regenerated via CLI (not hand-edited)
- `data/worlds/urban_political/resolved/{assembly_report.json,validation_report.json,provenance_manifest.json}` — regenerated (incidental fingerprint/timestamp/ordering noise only)
- `tests/unit/worldbuilding/test_world_compiler.py` — new compiler tests
- `tests/unit/worldassembly/test_assembly.py` — new resolver/normalizer tests
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` — new end-to-end + single-fire tests
- `src/observability/event_extractor.py` — Step 7 fix: 2 sites (`:286` `belief_assimilated`/
  `belief_updated`, `:899` `calamity_spawned`) now compare against `prior_state.tick` instead of
  the shared post-advance `tick` local
- `src/engine/kernel.py` — Step 7 fix: 1 site (`_phase_observability`, `GovernorModeChanged`) now
  compares against `prior_state.tick`
- `tests/integration/observability/test_kernel_event_recording.py` — Step 8: 3 new tests proving
  `belief_assimilated`, `calamity_spawned`, and `GovernorModeChanged` now fire through the real
  `Kernel.tick_once()` loop
- `docs/simulation_quality/event_type_coverage.md` — header last/previously-updated rotation;
  `belief_assimilated`/`belief_updated` rows (`calibration_hits` 0→1, notes rewritten);
  `calamity_spawned` row (note rewritten, `calibration_hits` left at 0); `GovernorModeChanged`
  row (§5, note added)
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-256` revised in place (pillar genuinely
  active via Branch A); new `INFRA-257` (info-plumbing) and `INFRA-258` (kernel tick-alignment
  fix, with honestly-qualified `calamity_spawned` language); `INFRA-246` `divergence_note`
  cross-reference to `INFRA-258` added
- `docs/guidelines/intentional_divergences.md` — new entry 2.22 "Kernel Tick-Alignment Fix"
  (rationale class Bug Fix) + new entry 2.23 "Single-Fire Compile-Time-Seeded Response"
  (rationale class Bounded) + both summary table rows
- `tests/simulation_quality/fixtures/grade_anchors.json` — `INFORMATION` grade `C→B` for all 7
  `urban_political_*` entries; `COGNITION` grade `C→B` for 6 of 7 (one already `B`), a natural
  side-effect of `belief_updated` also being scored by `CognitionScorer`; no other pillar/scenario
  entries touched

## Completion Summary
Steps 1-6 of the approved plan are implemented and tested: `pending_information_responses` is now
a typed, compile-time-seedable field flowing schema -> composition -> resolver -> compiler ->
`AuthoritativeState`, seeded once for `urban_political`'s `pop_0`, and proven (via tests against the
real compiled state and pipeline) to fire `belief_assimilated` exactly once at tick 0 with no
carry-forward.

Steps 7-8 are now also implemented and tested this pass: the `Kernel._phase_advancement()`
tick-alignment bug flagged above (and sized in
`staging_artifacts/.../tick_alignment_bug_investigation.md`) is fixed via the recommended surgical
option (3 one-line comparisons switched to `prior_state.tick`, already an in-scope parameter at
each site; the shared post-advance `tick` label used for every `SimulationEvent.tick` field is
unchanged). `belief_assimilated`/`belief_updated`, `calamity_spawned`, and `GovernorModeChanged` are
now all confirmed reachable through the real `Kernel.tick_once()` loop for the first time in the
codebase's history, via 3 new dedicated tests plus a full existing-suite regression sweep (0
failures, 0 modified assertions needed).

Steps 9-11 (docs: `intentional_divergences.md`, recalibration measuring actual `calibration_hits`,
`event_type_coverage.md` + parity ledger `INFRA-257`/`INFRA-258` + `INFRA-246` cross-reference)
were completed in subsequent passes, detailed below.

**Step 11 — docs: `event_type_coverage.md` + parity ledger revision/new entries +
kernel-fix divergence note:**

- `docs/simulation_quality/event_type_coverage.md`:
  - Header "Last updated"/"Previously updated" rotated to record this ticket's shipped fix.
  - `belief_assimilated`/`belief_updated` rows (§1.1): `calibration_hits` column updated `0 → 1`
    (the confirmed exactly-1-per-run count across all 7 `urban_political_*` calibration runs);
    notes rewritten to cite the `prior_state.tick` comparison (kernel fix, `INFRA-258`), the
    `pending_information_responses` seed (`INFRA-257`), the confirmed single-fire-at-tick-0
    mechanism, the `dungeon_crawl` 0-leakage spot-check, and the INFORMATION (all 7) / COGNITION
    (6 of 7) `C→B` grade movement.
  - `calamity_spawned` row (§1.1): `calibration_hits` left at `0` (honest — no calibrated scenario
    shows it firing); note explains the kernel fix's tick-gate comparison is unit-test-verified
    correct, but the one-off `dungeon_crawl_seed42_5200t` diagnostic run (not anchored) still shows
    0 hits due to a separate, pre-existing `calamity_intensity > 0.3` / hero-death precondition —
    explicitly not claimed as "now reachable in calibration."
  - `GovernorModeChanged` row (§5, unscored intentional): note added citing the kernel fix and the
    confirmed 63-73 natural occurrences in the existing `dungeon_crawl_seed{42,123,456}_2000t` /
    `sandbox_world_seed42_2000t` baselines (infrastructure telemetry, not SimQ-scored).
- `docs/parity_ledger/infrastructure.yaml`:
  - `INFRA-256` revised in place: "Pillar is NOT active"/"pillar remains functionally inactive"
    language removed; `text`/`divergence_note`/`support_boundary` rewritten to state Branch A
    (`pending_information_responses`, `INFRA-257`) is genuinely reachable — `belief_assimilated`/
    `belief_updated` calibration_hits confirmed `> 0` (exactly 1/run) for `urban_political`; Branch
    B and the paid-info path remain the documented residual gap. `test_path` extended to include
    this ticket's tests.
  - New `INFRA-257` added (info-plumbing entry, confirmed next-free ID by re-grepping the file
    before editing — highest existing ID was `INFRA-256`) per plan.md's template, verbatim except
    for cross-linking to `INFRA-258` for the calibration-observability dependency.
  - New `INFRA-258` added (kernel tick-alignment fix entry, next-free after `INFRA-257`) per
    plan.md's template, **with the `calamity_spawned` language deliberately adjusted** from the
    plan's draft (which read as unconditionally "un-blocked") to precisely state: the tick-gate
    comparison fix is verified correct by its dedicated unit test
    (`test_calamity_spawned_fires_through_real_tick_once_loop`, which constructs the spawn-gate
    state directly), but natural firing was not observed in the one-off diagnostic run due to a
    separate, pre-existing `calamity_intensity` hero-death precondition — `support_boundary` and
    `text` both make this distinction explicit ("mechanism verified" vs. "not fixed by this entry").
  - `INFRA-246` (`WorldDynamicsScorer`/`calamity_spawned` ownership entry): added a
    cross-reference in its (previously `null`) `divergence_note` pointing to `INFRA-258` for the
    historical unreachability, the fix, and the residual content precondition. Confirmed via grep
    that no other `docs/parity_ledger/*.yaml` entry references `calamity_spawned` or
    `GovernorModeChanged` by name.
  - Validated the full YAML parses (`python3 -c "import yaml; yaml.safe_load(...)"`, 263 entries,
    0 duplicate `id`s, `INFRA-257`/`INFRA-258` both present) after editing.
- `docs/guidelines/intentional_divergences.md`: added new entry "2.22 Kernel Tick-Alignment Fix
  (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)", rationale class **Bug Fix**, documenting what
  the fix was, why the pre-advance-vs-post-advance comparison mismatch is a straightforward defect
  (not a design tradeoff), which 3 event types it un-blocks, and precisely qualifying the
  `calamity_spawned` finding (mechanism verified via unit test; natural firing not observed in the
  diagnostic run due to the separate content precondition) rather than overclaiming. Also added
  new entry "2.23 Single-Fire Compile-Time-Seeded Response" (rationale class **Bounded**) covering
  plan.md's Step 9 — the single-fire compile-vs-apply seed lifecycle — with its own verification
  path and cross-reference to `INFRA-257`. Both entries have corresponding rows in the §1
  Divergence Summary Table.
- Ran `make knowledge-index-update` after the doc changes.

No source/test code was touched in this documentation pass.
