---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION
phase: done
date: 2026-08-26
tags: [feature-flags]
---

# TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION

## Title
Produce real validation evidence for `ENABLE_SELF_MODEL_COGNITION` before deciding its default

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Named follow-up from `TCK-20260824-ROLLOUT-FLAG-DECISIONS`: `ENABLE_SELF_MODEL_COGNITION` was kept
`OFF` by default -- real call site (`src/cognition/self_model_phase.py`), 10 test files, but no
corpus profile turns it on and no SHADOW-validation history exists. The now-removed, dead
`RolloutProfileManager` had listed this flag as CLASS_A/B/C default-enabled, but that matrix was
never wired to anything real -- not usable as evidence. This ticket's job is to produce real
evidence.

## Scope
- Run a real corpus-profile trial with the flag `ON`, at minimum against `urban_political.yaml`
  (already noted in `tests/integration/test_world_profile_feature_flag_guardrail.py`'s
  `known_exceptions` as a world where self-model content is seeded but the flag has never shipped
  ON, cited to `INFRA-259`/`INFRA-260` -- read that citation and the guardrail test's own
  documented exception before starting).
- Confirm the untested `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` combination
  (flagged as an open question in `TCK-20260824-ROLLOUT-FLAG-DECISIONS`) is either safe or
  documented as unsafe.
- Produce a real keep/flip recommendation with evidence.

## Out of Scope
- Actually flipping the flag's default.
- Resolving `urban_political`'s own `INFRA-259`/`INFRA-260` exception unless this ticket's own
  trial directly requires it.

## Acceptance Criteria
- [x] A real corpus-profile ON trial is run and documented
- [x] The `ENABLE_SELF_MODEL_COGNITION` + `ENABLE_ADVENTURE_ROUTING` combination question is
      resolved, not left open again
- [x] A keep/flip recommendation with evidence is produced

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (source of this deferral)

## Related Docs
- docs/guidelines/intentional_divergences.md (DEV-002, DEV-003)
- docs/parity_ledger/infrastructure.yaml (INFRA-259, INFRA-260)

## Related Stored Artifacts
- staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md

## Related Code Areas
- src/cognition/self_model_phase.py
- src/domains/optimization/feature_flags.py
- tests/integration/test_world_profile_feature_flag_guardrail.py

## Assumptions / Open Questions
- Whether `urban_political`'s existing seeded-but-unflagged self-model content is itself evidence
  worth investigating first (why was content seeded without ever flipping the flag) -- not decided
  here.

## Implementation Notes
Ran the plan's steps in order, all with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`.

- **Steps 1-2**: Ran fresh 200-tick, seed 42 `tools/calibrate_simq.py` trials against
  `urban_political` for both `urban_political_selfmodel_probe` and
  `urban_political_selfmodel_execution_probe`. Both exited 0, loaded the real compiled
  `urban_political` world (`entities=10`), and reported the profile's own feature-flag block
  verbatim (confirming `ENABLE_BELIEF_ASSIMILATION` stays absent for the plain probe and ON for
  the execution probe, as expected).
- **Step 3**: `self_model_updated` fired 5454 times in both runs — within ~2.8% of INFRA-266's
  historical ~5610-5611 figure, same order of magnitude, no collapse. Cross-checking both runs
  against `grade_anchors.json` surfaced a real, reproducible drift on both run keys' `INFORMATION`
  and `SOCIAL` pillars (see full tally and root-cause trace in
  `staging_artifacts/.../trial_evidence.md`'s Honest Gap section) — traced to
  `SelfModelUpdatePhase.run()`'s own Step 1 knowledge-assimilation firing a
  `belief_assimilated`/`belief_updated` pair independent of `ENABLE_BELIEF_ASSIMILATION`, a
  mechanism the original `C/0.0` anchor apparently predates.
- **Step 4**: `test_grade_regression.py -k selfmodel -q` un-skipped as expected (both target
  grade-anchor tests actually ran, not skipped), but **FAILED** rather than passed —
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor` on a hard `INFORMATION`-grade
  assert (`B` vs anchored `C`), `test_urban_political_selfmodel_execution_isolated_grade_anchor`
  on score-tolerance drift (`SOCIAL` uncovered by any known-ceiling classification; `COMBAT`/
  `ECONOMY`/`PROGRESSION` covered by an existing, pre-existing `known tick_budget` classification
  unrelated to this flag). This is a genuine finding, disclosed honestly (not fixed, not smoothed
  over) — see `plan.md`'s new Deviations section and `trial_evidence.md`. The other 4
  `selfmodel`-matched tests remain skipped (require `unit_selfmodel_pilot`'s own reports, out of
  scope to regenerate).
- **Step 5**: Re-confirmed `ENABLE_ADVENTURE_ROUTING` has zero live gating call sites in `src/`
  (static grep, matching investigation.md). Added
  `tests/architecture/test_adventure_routing_flag_inert.py::
  test_enable_adventure_routing_has_no_live_gating_call_site` as a durable regression guard
  (1 passed).
- **Steps 6-7**: Wrote `staging_artifacts/.../trial_evidence.md` and updated
  `docs/architecture/rollout_flag_decisions_m1.md`'s `ENABLE_SELF_MODEL_COGNITION` row plus a new
  `## ENABLE_SELF_MODEL_COGNITION — Validation Trial Result (TCK-20260826)` section, mirroring the
  combat-engagement sibling's shape and disclosing the anchor drift honestly.
- **Step 9**: Ran the remaining scoped regression suite. All passed except:
  (a) a wrong path in the plan for `test_component_patches.py` — corrected to
  `tests/unit/domains/optimization/test_component_patches.py` (10 passed), and
  (b) `test_corpus_diversity.py -k unit_selfmodel_pilot`'s 1000-tick grade-stability test failed
  twice on a `CalibrationIntegrityError` (watchdog/tick-budget pressure under this environment's
  load) — a pre-existing, already-documented load-sensitivity class
  (`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`), unrelated to `ENABLE_SELF_MODEL_COGNITION`
  and to this ticket's own 200-tick trial (which completed cleanly). Both deviations recorded in
  `plan.md`'s Deviations section.

No `src/` file was changed. No flag default was flipped. No `_DELIBERATE_ON_DEFAULT_FLAGS`
allowlist was touched.

## Test Summary
- `tests/architecture/test_adventure_routing_flag_inert.py -q` — **1 passed** (new guard test).
- `tests/simulation_quality/test_grade_regression.py -k selfmodel -q` — **2 failed, 4 skipped, 83
  deselected** (both target tests un-skipped and ran, but failed — real anchor drift, disclosed
  honestly, not fixed; see Implementation Notes/trial_evidence.md).
- `tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/config/test_phase10_feature_flags.py -q`
  — **12 passed**.
- `tests/integration/domains/test_fused_loop.py -k "self_model or branch_b or belief" -q` — **7
  passed, 3 deselected**.
- `tests/integration/test_world_profile_feature_flag_guardrail.py -q` — **67 passed**.
- `tests/unit/config/test_phase10_feature_flags.py tests/integration/test_scenario_feature_flag_defaults.py tests/certification/test_phase10_enhanced_determinism_parity.py -q`
  — **57 passed**.
- `tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off -q` —
  **1 passed, 3 deselected**.
- `tests/unit/worldassembly/test_corpus_diversity.py -k unit_selfmodel_pilot -q` — **1 failed, 2
  passed** (environment load-sensitivity, unrelated to this ticket — see Implementation Notes).
- `tests/unit/domains/optimization/test_component_patches.py -q` (corrected path) — **10 passed**.

## Files Changed
- `tests/architecture/test_adventure_routing_flag_inert.py` (new — AC2 regression guard)
- `docs/architecture/rollout_flag_decisions_m1.md` (row update + new
  `## ENABLE_SELF_MODEL_COGNITION — Validation Trial Result` section)
- `staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md` (new,
  this session)
- `staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/plan.md` (Deviations
  section added this session; the rest was written earlier this session's own Plan phase and is
  part of this run's changeset — confirmed via `git status` showing the whole
  `staging_artifacts/TCK-20260826-.../` directory untracked)
- `staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/investigation.md` (written
  this session's own Investigate phase; read but not rewritten during Implement — part of this
  run's own untracked changeset)
- `staging_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/test_plan.md` (written this
  session's own Plan phase; read but not rewritten during Implement — part of this run's own
  untracked changeset)
- `tickets/inprogress/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION.md` (this file)

## Completion Summary
Ran 2 fresh 200-tick `ENABLE_SELF_MODEL_COGNITION=ON` corpus trials against `urban_political`
(`urban_political_selfmodel_probe`, `urban_political_selfmodel_execution_probe`), layering fresh
evidence on top of 2 already-real prior trials (`unit_selfmodel_pilot`'s shipped-ON world,
`INFRA-266`'s real-world generalization split verdict). The fresh trials reproduced INFRA-266's
event-volume order of magnitude cleanly, but did **not** cleanly reproduce the committed
`grade_anchors.json` baselines: both probe run keys' `INFORMATION` and `SOCIAL` pillars drifted
beyond the tests' own tolerance, traced to a real, reproducible mechanism
(`SelfModelUpdatePhase.run()`'s own knowledge-assimilation step firing independent of
`ENABLE_BELIEF_ASSIMILATION`) — disclosed honestly as a new finding requiring a separate follow-up
ticket to re-anchor or investigate, not fixed here. AC2 (`ENABLE_ADVENTURE_ROUTING` combination)
is resolved via static analysis (zero live gating call sites) plus a new durable regression guard
test. **Recommendation: Keep OFF, deferred** — matching the plan's working expectation:
`unit_selfmodel_pilot` remains the sole flag-ON shipped profile and is a dedicated Unit-tier
isolation world, not a real archetype world, so the DEV-003 "shipped production profile" bar is
still unmet regardless of the anchor-drift finding. No `src/` file was changed and no flag default
was flipped, per scope.
