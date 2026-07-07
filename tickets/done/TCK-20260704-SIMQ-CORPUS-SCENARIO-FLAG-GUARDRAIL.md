---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, feature-flags]
---

# TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL

## Title
Add per-scenario feature-flag guardrail test covering the expanded corpus's flag surface

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Folds in `docs/plans/audit_fix_plan.md` P2-E ("Feature-gated phases have no per-scenario default
test"). Per that finding, 8 pipeline phases are gated behind `FeatureMode` flags
(`src/domains/optimization/feature_flags.py`) and no test verifies the correct default flag values
per scenario/world type — a misconfigured scenario silently loses features. This risk is
substantially amplified by this epic's own preceding 9 tickets: before this batch, only
`urban_political` had a non-empty `feature_flags:` profile block (`ENABLE_BELIEF_ASSIMILATION`,
`ENABLE_SOCIAL_COOPERATION`) and only `simq_routing_test` had `ENABLE_ADVENTURE_ROUTING` (via a
hardcoded harness special case, generalized by ticket 3 in this batch). After tickets 3-9 land, the
corpus will have many more worlds with many more per-world flag combinations
(`ENABLE_ADVENTURE_ROUTING`, `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_SELF_MODEL_COGNITION` across
unit/end-to-end/stress-tier worlds) — exactly the kind of expanded, easy-to-misconfigure surface
P2-E's finding warns about. This ticket lands last in the batch specifically so its test matrix
covers that expanded surface, not just the pre-epic baseline.

## Scope
1. Add a test (in `tests/integration/` or `tests/certification/`, per P2-E's own fix guidance) that:
   - Loads every world's `config/simulation_quality/profiles/<world>.yaml` (or
     `default.yaml` fallback where a world has no dedicated profile)
   - Asserts the expected `feature_flags:` state for that world, per this epic's own record of what
     should be ON/OFF for each world:
     - The 9 pre-existing non-routing worlds (`urban_political`, `dungeon_crawl`, `sandbox_world`,
       `wilderness_survival`, `highland_traverse`, `swamp_border_world`, `frontier_living_world`,
       `frontier_extended`, `generated_frontier_3_42`) — `ENABLE_ADVENTURE_ROUTING` must be
       OFF/absent (per `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s anti-drift note: "if any calibration
       world enables `ENABLE_ADVENTURE_ROUTING`, AGENCY will activate and grade anchors must be
       updated" — this test is exactly that anti-drift guard, made concrete)
     - `simq_routing_test` and the new AGENCY unit-tier world (ticket 6) —
       `ENABLE_ADVENTURE_ROUTING` must be ON
     - `urban_political` and any world from ticket 7 (E2E content expansion) that seeded
       `information_source_profiles` — `ENABLE_BELIEF_ASSIMILATION` must be ON
     - The new self-model pilot world (ticket 5) — `ENABLE_SELF_MODEL_COGNITION` must be ON, and
       `ENABLE_BELIEF_ASSIMILATION` must be OFF (per that ticket's explicit isolation requirement)
     - New unit-tier FACTION/INFORMATION worlds (ticket 4) — flag state matching each world's single
       isolated mechanic
     - New stress-tier worlds (ticket 8) — flag state matching whatever content ticket 8 actually
       seeded (e.g. its large-scale FACTION/INFORMATION world should have
       `ENABLE_BELIEF_ASSIMILATION` ON if it seeded `information_source_profiles`)
2. Assert the inverse direction too: a world with a Pattern-6 content field seeded
   (`faction_tension_overrides`, `information_source_profiles`, etc.) but the corresponding flag OFF
   (or vice versa) is flagged as a real misconfiguration — this is the "seeding profiles without
   turning the flag on produces zero signal" trap investigation.md §3 documents; catch it at test
   time, not by discovering silent zero-signal grades after the fact.
3. Confirm the test matrix explicitly covers every world that exists after tickets 1-9 land — do
   not write it against only the pre-epic 10-world baseline.
4. Run the new test and confirm it passes against the actual post-epic corpus state.

## Out of Scope
- Fixing any misconfiguration this test discovers in an already-completed prior ticket in this
  batch — if this test finds a real drift/misconfiguration, that is a legitimate finding; either fix
  it directly if trivial (e.g. a missing flag line) or file a targeted follow-up ticket, but do not
  silently loosen the test to make it pass
- Changing `FeatureMode`, `feature_flags.py`, or any flag-gated phase's runtime behavior — this
  ticket only adds a static/config-level assertion test, not new engine logic
- Re-scoping or re-authoring any of tickets 1-9's world content — this ticket is a guardrail on top
  of what they produce, not a redo of their content decisions

## Acceptance Criteria
- [x] New test exists (`tests/integration/` or `tests/certification/`) loading every world's
      profile YAML (or `default.yaml` fallback) and asserting expected `feature_flags:` state
- [x] Test explicitly enumerates and covers all worlds added by tickets 4, 5, 6, 8 in this batch,
      not just the pre-epic 10-world baseline
- [x] Test asserts both directions of the flag/content-field pairing (flag ON with no matching
      content, and content seeded with flag OFF, are both caught as misconfigurations)
- [x] Test asserts the 9 pre-existing non-routing worlds keep `ENABLE_ADVENTURE_ROUTING` OFF (the
      AGENCY-DA anti-drift guard, made concrete and automatically enforced)
- [x] Test passes against the actual corpus state after tickets 1-9 have landed
- [x] `docs/plans/audit_fix_plan.md` P2-E section updated from "OPEN" to resolved, with the new
      test's path cited, and the Summary Table's P2-E row updated to match

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE — this ticket's test matrix must cover the
  generalized mechanism ticket 3 introduces
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO — worlds this test matrix must cover
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT — worlds this test matrix must cover
  (including the ENABLE_BELIEF_ASSIMILATION-must-be-OFF isolation requirement)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — worlds this test matrix must cover
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — worlds this test matrix must cover
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — worlds this test matrix must cover
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — source of the anti-drift note this test operationalizes

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory) and §4 open question 5 (P2-E fold-in rationale)
- `docs/plans/audit_fix_plan.md` — P2-E section (source finding, fix guidance) and Summary Table
- `docs/simulation_quality/eval_matrix_results.md` — AGENCY Cross-World Design Note (anti-drift
  language this test enforces)

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation

## Related Code Areas
- `src/domains/optimization/feature_flags.py` — 8 gated phases/flags
- `config/simulation_quality/profiles/` — every world's profile YAML, including all new ones tickets
  4-8 add
- `data/content/simulation_scenarios/` (per P2-E's original file reference)
- `tests/integration/` or `tests/certification/` — new test location (implementer's choice, justify
  in Implementation Notes)

## Assumptions / Open Questions
- UQ-1: Should this test be a single parametrized test iterating all worlds, or one test function
  per world? Default to a single parametrized test (per-world flag-expectation table as test data)
  for maintainability — adding a future world means adding one table row, not one new function.
- UQ-2: Where should the "expected flag state per world" table live — hardcoded in the test file, or
  in a small fixture/config file? Default to hardcoding in the test file unless the number of worlds
  makes that unwieldy (>15 worlds), in which case a fixture file is preferable; implementer's
  judgment.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL/plan.md`'s
7 steps, no deviations.

1. **Fixture** (`tests/simulation_quality/fixtures/expected_world_flag_state.json`) authored with the
   exact content from plan.md Step 1 — 17 world entries, `_meta` block (AGENCY-DA groupings, world
   count), `known_exceptions.self_model_content_without_flag` citing `INFRA-259`/`INFRA-260` for
   `urban_political`. Before writing, independently re-derived every row from the live repo (not
   just trusting the plan's transcription): wrote a throwaway Python check that called the same
   `_resolve_profile()`/`_load_profile_feature_flags()` logic against every profile YAML, and a
   second check that read every `data/worlds/<world>/world.yaml`'s `faction_tension_overrides`/
   `information_source_profiles`/`pending_information_responses`/
   `pending_self_model_information_events` presence. Both checks matched the plan's fixture content
   for all 17 worlds exactly — fixture confirmed accurate before use, not just copy-pasted.
2. **Pytest marker** registered in `pyproject.toml` (`corpus_flag_guardrail`), appended after the
   existing `feature_flag_default` line per plan.md Step 2.
3. **Test file** (`tests/integration/test_world_profile_feature_flag_guardrail.py`) — 7 test
   functions per plan.md's spec (`test_all_worlds_have_a_resolvable_profile_or_default_fallback`,
   `test_flag_state_matches_expected_per_world` [parametrized, 17 worlds],
   `test_agency_da_anti_drift_guard`, `test_information_flag_content_pairing_both_directions`
   [parametrized, symmetric, no exceptions], `test_self_model_flag_content_pairing_both_directions_with_documented_exception`
   [parametrized, urban_political allow-listed and its exception shape re-validated, not just
   skipped], `test_faction_content_has_no_flag_requirement`, `test_fixture_covers_every_live_world_exactly`).
   Imports `_resolve_profile`/`_load_profile_feature_flags` directly from `tools.calibrate_simq`
   (`from tools.calibrate_simq import ...`) — confirmed this import style resolves cleanly without
   `sys.path` manipulation because `pyproject.toml`'s `[tool.pytest.ini_options] pythonpath = ["."]`
   already puts the repo root on the path; `tests/unit/tools/test_simq_audit_gaps.py` is the existing
   precedent for this exact style (`import tools.simq_audit_gaps as sag`), so plan.md's more
   conservative `sys.path.insert(...)` fallback text was not needed. Did not implement the optional
   `_read_world_pattern6_flags()` live cross-check helper plan.md described as "optional... not a
   reimplementation of world.yaml parsing for flags" — per plan.md's own framing this was a nice-to-have,
   not required by any of the 7 test specs, and the content-field values it would have cross-checked
   were already independently re-derived and verified in step 1 above; adding it would have been an
   unused abstraction (three similar lines > premature helper).
4. **Test run**: new file — 55 cases (7 functions, 3 parametrized × 17 worlds) all pass. Regression
   surface (`test_scenario_feature_flag_defaults.py`, `test_phase10_feature_flags.py`,
   `test_corpus_diversity.py`) all pass, no changes needed. **No misconfiguration beyond the cited
   `urban_political` exception was found** — the guardrail passed cleanly against the real corpus on
   first run.
5. **Parity ledger**: appended `INFRA-262` to `docs/parity_ledger/infrastructure.yaml` (end of file,
   after `INFRA-255` — the file's entries are not in strict ID-numeric order, e.g. `INFRA-261` is
   followed by `INFRA-246`, so appended at EOF rather than searching for a numeric insertion point).
   Cites `INFRA-259`/`INFRA-260` for the one exception and explicitly marks `INFRA-221` as a
   companion, not a duplicate, in `support_boundary`. `python3 tools/parity_ledger_scan.py` exits 0;
   YAML re-parses as a 267-entry list.
6. **`docs/plans/audit_fix_plan.md`**: three edits per plan.md Step 6 exactly — P2-E section heading
   + Resolution paragraph, Summary Table row (found at line 634, not line 623 as plan.md's text
   assumed — an earlier ticket's edits in this same file shifted line numbers; content match was
   exact, only the line number differed), and the "Still open" list (found at line 688, same line
   shift). All three verified via `grep -n "P2-E"` post-edit.
7. **`make evaluate`**: found 26 pre-existing `FACTION` pillar regressions (`S`/`A` anchor vs actual
   `C`) across `dungeon_crawl`/`sandbox_world`/`frontier_extended`/`frontier_living_world`/
   `wilderness_survival`/`highland_traverse`/`swamp_border_world` calibration runs. **Verified via
   `git stash --include-untracked` + re-run that these 26 regressions are 100% pre-existing on the
   branch tip (`135cce8c`, `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`) and present with zero
   of this ticket's changes applied** — this ticket touches no calibration data, no
   `grade_anchors.json`, no world/profile/faction content, so it cannot be the cause. Stashed changes
   were fully restored afterward (`git stash pop` + re-verified all new/modified files and re-ran the
   new test suite green). This is flagged as a candidate follow-up (see
   `REAL_MISCONFIGURATIONS_FOUND`/final report) — likely stale `data/calibration/` output relative to
   `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`'s faction-relationship content changes, not
   related to this ticket's flag-guardrail scope. Not fixed here (out of scope: this ticket adds a
   static config-assertion test only). `make knowledge-index-update` and `graphify update .` both ran
   clean (13 files re-embedded for the doc/index update; graph rebuilt with the new test file
   included).

## Test Summary
- `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v` — 55 passed (7 functions;
  3 parametrized across 17 worlds each = 51, + 4 standalone = 55).
- `pytest tests/integration/test_scenario_feature_flag_defaults.py -m "not slow"` — 45 passed
  (regression, untouched).
- `pytest tests/unit/config/test_phase10_feature_flags.py tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"` —
  35 passed, 12 deselected (regression, untouched).
- `pytest --markers | grep corpus_flag_guardrail` — marker registered and visible.
- `make evaluate` — 490 pillars checked, 26 pre-existing regressions (confirmed unrelated to this
  ticket via stash-and-rerun on the unmodified branch tip; see Implementation Notes step 7), 0
  missing.
- `python3 tools/parity_ledger_scan.py` — exits 0 against the updated `infrastructure.yaml`.

## Files Changed
- `tests/simulation_quality/fixtures/expected_world_flag_state.json` (new) — 17-world expected
  flag/content-field fixture + `known_exceptions` block.
- `tests/integration/test_world_profile_feature_flag_guardrail.py` (new) — 7 guardrail test
  functions.
- `pyproject.toml` — registered `corpus_flag_guardrail` pytest marker.
- `docs/parity_ledger/infrastructure.yaml` — appended `INFRA-262` (companion to `INFRA-221`, cites
  `INFRA-259`/`INFRA-260`).
- `docs/plans/audit_fix_plan.md` — P2-E section heading + Resolution paragraph, Summary Table row,
  "Still open" list updated to RESOLVED.

## Completion Summary
Added a static guardrail test asserting per-world `feature_flags:` state against actual Pattern-6
content seeding for all 17 worlds in the post-epic corpus — closing the calibration-profile half of
`docs/plans/audit_fix_plan.md`'s P2-E finding (the half `TCK-20260627-P2E-FEATURE-FLAG-TEST`/
`INFRA-221` never covered, since that ticket tests `data/content/simulation_scenarios/*.yaml`
scenario templates, a genuinely different subsystem — independently re-confirmed zero overlap by
reading both test files directly). New fixture (`expected_world_flag_state.json`) and test file
(`test_world_profile_feature_flag_guardrail.py`, 7 functions, 55 passing parametrized/standalone
cases) cover: per-world flag-state assertions, a standalone-named AGENCY-DA anti-drift guard (the
9 pre-existing non-routing worlds must stay OFF; only `simq_routing_test`/`hero_guild_routing` are
ON), both-direction pairing checks for the 2 flags that are actually content-gated (INFORMATION↔
`ENABLE_BELIEF_ASSIMILATION`, self-model↔`ENABLE_SELF_MODEL_COGNITION`, the latter with one cited,
re-validated `urban_political` exception per `INFRA-259`/`INFRA-260`/`STRAT-245` — confirmed
genuinely intentional and parity-verified, not silently tolerated), a structural guard confirming
`faction_tension_overrides` requires no flag at all (only 2 of 4 Pattern-6 fields are actually
flag-gated — a real, non-obvious corpus structure the investigation surfaced), and a
fixture-covers-every-live-world coverage check. New parity ledger entry `INFRA-262`.
`docs/plans/audit_fix_plan.md`'s P2-E section, Summary Table row, and "still open" list all updated
to RESOLVED, all three independently re-verified against the real file text.

Along the way, the implementer's `make evaluate` run surfaced 26 apparent FACTION-pillar
regressions (S/A→C) across 7 worlds. Investigated directly by the orchestrator before finalizing
this ticket: confirmed via fresh recalibration (`sandbox_world_seed42_200t` re-run live, producing
`FACTION=S` matching the committed anchor exactly) that this was **entirely a stale local
`data/calibration/` cache artifact** — those on-disk reports predated
`TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`'s content changes by roughly 20 hours, not a real
regression. Refreshed the full corpus via `make evaluate-full` (61 scenarios, ~7 minutes), then
re-confirmed `make evaluate` shows **0 regressions across 610 pillars**. No follow-up ticket filed,
since there was nothing actually broken — the finding was fully resolved as a false alarm, not
deferred.
