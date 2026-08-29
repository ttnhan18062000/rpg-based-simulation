---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION
artifact_type: test_plan
tags: [feature-flags]
---

# Test Plan — TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION

## Regression Surface

This is an evidence-gathering/chore ticket (no source code changes proposed). The regression
surface is the existing test coverage for `InformationIntentExecutionPhase`,
`InformationBeliefPhase` Branch B, and the flag registration itself — all must continue passing
unchanged.

**Unit:**
- `tests/unit/engine/test_information_intent_execution_phase.py` (all 3 tests — read in full):
  - `test_action_intent_execution_phase_filters_non_action_intent_entries` — confirms the
    `isinstance(candidate, ActionIntent)` guard rejects unrelated `IntentResult` entries.
  - `test_action_intent_execution_phase_only_executes_the_action_intent_entry_in_a_mixed_list` —
    confirms only the `ActionIntent` entry in a mixed `intent_results` list fires.
  - `test_action_intent_execution_phase_preserves_deterministic_entity_order` — confirms
    sorted-entity-ID iteration (kernel determinism law).
- `tests/unit/config/test_phase10_feature_flags.py::test_new_flag_registered_in_feature_flag_manager`
  — confirms `ENABLE_INFORMATION_INTENT_EXECUTION` is registered with the correct default.

**Integration:**
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` (full file, 6
  tests — read in full):
  - `test_phase_routes_query_for_active_unknowns`, `test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure`,
    `test_ask_information_intent_execution_closes_the_loop` — Branch B routing/fallback/adapter
    correctness, independent of this flag.
  - `test_action_intent_execution_phase_fires_in_real_tick_pipeline` — with all three flags
    (`ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_INFORMATION_INTENT_EXECUTION`)
    ON, a real `AuthoritativeApplyPipeline.refine()` call closes the loop into
    `self_model_bundle_set.knowledge.facts` within one tick.
  - `test_action_intent_execution_phase_off_by_default_is_a_noop` — same setup but this flag left
    unset (default OFF): Branch B still routes into `intent_results`, but
    `ActionIntentAdapter.execute()` must not fire (`"iron_ore"` stays in `unknowns`, never reaches
    `facts`). This is the direct proof the gate actually blocks production reachability.
- `tests/integration/test_world_profile_feature_flag_guardrail.py` — `_GATED_FLAGS` (line 37)
  already includes `ENABLE_INFORMATION_INTENT_EXECUTION`; its content/flag-pairing assertions must
  keep passing for all shipped worlds.

**Simulation-quality (grade-anchor regression):**
- `tests/simulation_quality/test_grade_regression.py::test_information_intent_execution_fires_through_kernel_tick_once`
  (line 507) — deterministic hand-built-scenario proof of AC "execution fires through a real
  `Kernel.tick_once()` loop."
- `tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor`
  (line 466) — corpus-based grade-anchor guard: the phase must not regress calibration
  grades/costs when wired in and gated ON, using `urban_political_selfmodel_execution_probe.yaml`.

## New Tests Required

None. This is a validation-evidence ticket (chore tier), not a code-behavior-change ticket — no new
production code paths are introduced, so no new unit/integration test code is required per the
Acceptance Criteria. What is required instead:
- A real corpus-profile trial run with `ENABLE_INFORMATION_INTENT_EXECUTION=ON` (via profile-YAML
  `feature_flags:` override — never a bare env-var override, per the `_KNOWN_FLAGS` gap documented
  in investigation.md) against at least one world, with `ENABLE_BELIEF_ASSIMILATION` left at its
  now-ON default.
- Re-running the existing regression suite listed above un-skipped (where a local
  `data/calibration/*/quality_report.json` gates a test via `pytest.skip(...)`) so the grade-anchor
  tests actually assert rather than silently skip, mirroring the SELF-MODEL-COGNITION sibling's own
  "Step 4" method (`stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`).
- If Plan decides the existing `urban_political_selfmodel_execution_probe_seed42_200t` run (already
  on file from the sibling ticket) is insufficient as this ticket's own primary evidence (see
  investigation.md's Risks/Open Questions), a fresh run of the same or a new probe profile is the
  concrete deliverable — not new test *code*.
- One caveat, not a new test requirement: if Plan's trial surfaces a genuine, previously-undocumented
  regression (mirroring the SELF-MODEL-COGNITION sibling's own `INFORMATION`/`SOCIAL` anchor-drift
  finding, or the PROGRESSION-EVOLUTION sibling's pipeline-crash finding), that finding must be
  disclosed in trial_evidence.md as a new risk requiring its own follow-up ticket — not silently
  fixed or a new regression test authored inline, per the Anti-Drift Hazards in investigation.md and
  the batch's own established Scope Guards pattern ("do not fix any new bug the trial might surface
  inline").

## Scoped Pytest Commands

Regression re-verification (before and after the trial):
```
python3 -m pytest tests/unit/engine/test_information_intent_execution_phase.py -q
python3 -m pytest tests/integration/domains/information/test_phase5_information_belief_phase.py -q
python3 -m pytest tests/unit/config/test_phase10_feature_flags.py -q
python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q
python3 -m pytest tests/simulation_quality/test_grade_regression.py -k "information_intent_execution or selfmodel_execution" -q
```
Note (environment): the sibling SELF-MODEL-COGNITION ticket found the worktree's bare `python3`
lacks `pydantic`; it substituted `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`
with `cwd` still the worktree. Verify the same substitution is needed here before running — do not
assume the venv path is stale across sessions.

Never: `pytest tests/` — always scoped to the domain above per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- `test_action_intent_execution_phase_off_by_default_is_a_noop` is the load-bearing guard proving
  the flag gate is real (not a dead switch) — must keep passing unmodified through this ticket. If
  this test's assertions ever needed to change, that would itself be a red flag this ticket's Scope
  explicitly forbids acting on (no flipping the default).
- `test_action_intent_execution_phase_filters_non_action_intent_entries` guards against the
  `isinstance(candidate, ActionIntent)` filter regressing and misinterpreting `economy.py`/
  `patches.py`'s unrelated `IntentResult` entries as executable intents — a scope-creep-adjacent
  hazard specifically called out in the phase's own class docstring.
- `tests/integration/test_world_profile_feature_flag_guardrail.py`'s `_GATED_FLAGS`-driven
  assertions guard against any shipped world silently gaining `ENABLE_INFORMATION_INTENT_EXECUTION:
  "ON"` in its default profile — since this ticket's own Anti-Drift Hazards forbid creating or
  editing a *shipped* profile to fabricate production evidence, this test failing would be the
  first signal such drift occurred.
- `test_urban_political_selfmodel_execution_isolated_grade_anchor`'s band-check (not hard-equality)
  on `INFORMATION`/`COGNITION` guards against a silent regression in the phase's calibration-safety
  properties; a genuine anchor drift here (as the SELF-MODEL-COGNITION sibling found on this exact
  profile) must be disclosed as a new finding, not silently re-anchored to make the gate pass —
  per CLAUDE.md's Gate Integrity rule.
