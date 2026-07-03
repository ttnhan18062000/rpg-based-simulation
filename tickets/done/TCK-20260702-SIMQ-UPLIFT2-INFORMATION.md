---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-INFORMATION
phase: closed
date: 2026-07-02
tags: [simulation_quality, information, belief, worldbuilder, feature_flag]
---

# TCK-20260702-SIMQ-UPLIFT2-INFORMATION

## Title
Seed InformationSourceProfile compile-time plumbing + enable belief-assimilation gate in urban_political (pillar activation blocked by dead trigger paths — see deferred follow-up)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
INFORMATION pillar grades C across all 30 calibration runs. Original diagnosis (SOCIAL-ZERO) named a
dual gate: (1) `ENABLE_BELIEF_ASSIMILATION=OFF` short-circuits `InformationBeliefPhase`
(`src/engine/pipeline.py:152`), (2) `AuthoritativeState.information_source_profiles = []` in every
compiled world (same "compiler never constructs the field" bug class already found and fixed for
`FactionState` in the sibling `TCK-20260702-SIMQ-UPLIFT2-FACTION` ticket).

**Investigation on 2026-07-03 found a third, deeper gap not visible from the dual-gate framing:**
even with both named gates lifted, `InformationBeliefPhase.apply()`'s two trigger branches are
themselves unreachable in the current engine, independent of this ticket's flag/profile fix:
- Branch A requires `state.pending_information_responses`, which nothing in `src/` ever writes.
- Branch B requires `self_model.knowledge.unknowns`, but `SelfModelUpdatePhase.apply()` hardcodes
  `events=[]`, so `KnowledgeModelService.assimilate()` is never invoked.

This means the ticket's originally-stated fix (seed profiles + flip flag) will compile cleanly and
**still produce zero `belief_assimilated`/`lead_certainty_updated` events** — AC-3 as originally
written cannot be met by this ticket's scope alone. Per user direction (2026-07-03), this ticket
now ships only the legitimate, self-contained portion of the fix and defers the trigger-wiring gap
to a separate, properly-scoped follow-up: **TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER**
(see `docs/plans/idea_information_belief_trigger_wiring.md` for the full investigation writeup,
options considered, and recommendation).

Revised fix (this ticket): add the missing `information_source_profiles` compile-time plumbing
(schema + `WorldCompiler`/`WorldAssemblyResolver`, mirroring the FACTION ticket's pattern), seed
two corrected `InformationSourceProfile` entries in `urban_political` (the ticket's original
`knowledge_scopes` values were also found to be wrong — see UQ-2 resolution below), and flip
`ENABLE_BELIEF_ASSIMILATION=ON` in the calibration profile. This is real, needed groundwork
regardless of how the trigger-wiring follow-up is eventually resolved — it just does not, by
itself, move the INFORMATION grade this batch.

## Scope
1. Schema + compiler + resolver plumbing (mirrors `TCK-20260702-SIMQ-UPLIFT2-FACTION`'s pattern):
   add `information_source_profiles` as a properly typed, declarable field somewhere in the
   `WorldSpec`/`WorldCompositionSpec` schema chain, wire `WorldCompiler.compile()` to actually pass
   `information_source_profiles=` into the `AuthoritativeState(...)` constructor (confirmed currently
   omitted entirely — same bug class as the FACTION ticket's `factions=` gap), and confirm the resolver
   merges/validates any composition-level content correctly.
2. World content: add two `InformationSourceProfile` entries to `urban_political` world spec, with
   `knowledge_scopes` corrected to match the router's actual literal-string matching in
   `InformationQueryRouter.matches_scope()` (`common_resource_sources`, `recipe_requirements`,
   `regional_danger` — NOT the originally-proposed `danger_rating`/`material_source`/`recipe_definition`,
   which do not exist as router-recognized scopes and would have been dead content):
   ```
   Profile 1 — town notice board:
     source_id: "town_notice_board"
     source_kind: "guide"           # InformationSourceKind.GUIDE
     knowledge_scopes: ["regional_danger", "common_resource_sources"]
     accuracy: 0.4
     freshness: 0.6
     bias: 0.1
     cost_gold: 0
     max_answers_per_query: 2

   Profile 2 — merchant rumour network:
     source_id: "traveling_merchant_rumors"
     source_kind: "traveler"        # InformationSourceKind.TRAVELER
     knowledge_scopes: ["common_resource_sources", "recipe_requirements"]
     accuracy: 0.65
     freshness: 0.8
     bias: 0.2
     cost_gold: 5
     max_answers_per_query: 3
   ```
3. Feature flag: add `ENABLE_BELIEF_ASSIMILATION: "ON"` to
   `config/simulation_quality/profiles/urban_political.yaml` (same pattern as `ENABLE_SOCIAL_COOPERATION`
   added in TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO). Confirm `calibrate_simq.py` calls
   `_load_profile_feature_flags()` which already handles this injection.
4. Calibrate: re-run all `urban_political_*` scenarios to confirm the plumbing compiles and the
   profiles are present in `AuthoritativeState.information_source_profiles`. **`belief_assimilated`
   / `lead_certainty_updated` calibration_hits are expected to remain 0** — this is the deferred gap,
   not a regression. Verify 0 regressions on every other pillar/world (unrelated to this change).
5. Update `docs/simulation_quality/event_type_coverage.md` honestly: document that
   `information_source_profiles` now compiles non-empty and the flag is ON, but `belief_assimilated`
   / `lead_certainty_updated` remain at 0 calibration_hits due to the dead trigger-path gap, with a
   pointer to the follow-up ticket.
6. Update parity ledger (`docs/parity_ledger/infrastructure.yaml` and/or `social_narrative.yaml`) —
   add an entry for the compile-time plumbing (status reflects "scaffolding verified, pillar
   inactive pending trigger-wiring follow-up" — do not mark as fully `verified` INFORMATION-pillar
   activation, since it isn't).
7. Create the follow-up ticket `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` (tickets/todos/) and
   `docs/plans/idea_information_belief_trigger_wiring.md`, both already drafted as part of this
   ticket's scoping — implementer should confirm they still accurately reflect the shipped plumbing
   and update cross-references if anything changed during implementation.

## Out of Scope
- Activating INFORMATION in any world other than `urban_political` this ticket
- Adding new `InformationSourceKind` enum values (use existing: GUIDE, GUILD, BLACKSMITH, TRAVELER)
- Changing INFORMATION scoring weights
- Implementing a full information marketplace or NPC query-response loop (the phase already exists)
- **Wiring `InformationBeliefPhase`'s trigger paths to be reachable** (`pending_information_responses`
  population, or `SelfModelUpdatePhase`'s hardcoded `events=[]`, or the orphaned
  `InformationNeedDetector`/`information_providers` registry) — deferred to
  `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` per 2026-07-03 user direction; this is genuinely new,
  unreviewed, shared-engine-path scope that needs its own investigation/plan/architecture-review cycle

## Acceptance Criteria
- [x] `ENABLE_BELIEF_ASSIMILATION=ON` injected for all `urban_political_*` calibration runs
      (confirmed live in all 7 recalibration runs, 2026-07-03: console output shows
      `Profile feature flags: {'ENABLE_SOCIAL_COOPERATION': 'ON', 'ENABLE_BELIEF_ASSIMILATION': 'ON'}`)
- [x] `AuthoritativeState.information_source_profiles` contains ≥2 profiles after compilation
      of `urban_political`, with router-recognized `knowledge_scopes` (confirmed: 2 entries
      — `town_notice_board`, `traveling_merchant_rumors` — present in
      `data/worlds/urban_political/resolved/world.resolved.yaml`)
- [x] `make evaluate --dry-run` exits 0 after anchors updated (0 regressions on all pillars/worlds
      other than INFORMATION/urban_political, which is expected to remain unchanged at C) —
      confirmed 2026-07-03: exit 0, 250 pillars checked, 0 regressions, 0 missing; no anchor edit
      needed (INFORMATION stayed C everywhere, as expected)
- [x] `docs/simulation_quality/event_type_coverage.md` updated with the honest current state
      (profiles present, flag ON, calibration_hits still 0, pointer to follow-up ticket)
- [x] Parity ledger updated to reflect scaffolding-verified / pillar-still-inactive status
      (`docs/parity_ledger/infrastructure.yaml::INFRA-256`, extends `INFRA-245`)
- [x] Follow-up ticket `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` exists in `tickets/todos/`
- [x] `docs/plans/idea_information_belief_trigger_wiring.md` exists documenting the deferred gap
- [x] ~~At least one of `belief_assimilated` or `lead_certainty_updated` has `calibration_hits > 0`~~
      **DEFERRED** — not achievable within this ticket's scope; see Request Summary and follow-up ticket.
      Confirmed 2026-07-03: 0 hits for both event types across all 7 recalibrated
      `urban_political_*` runs (`grep -c` over each run's `quality_scores.jsonl`).

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO — confirmed INFORMATION root cause (c3): dual-gate; deferred follow-up defined here
- TCK-20260702-SIMQ-UPLIFT2-FACTION — sibling ticket; FACTION's compiler-plumbing pattern (add typed field → seed in `compile()` → composition-scoped content) is the template this ticket follows for `information_source_profiles`
- TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER — follow-up ticket (new, 2026-07-03) covering the deferred trigger-path wiring that this ticket's scope does not include

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — INFORMATION=C across all 30 runs
- `docs/audits/D20_simq_integration.md` §SimQ Uplift Batch — dual-gate follow-up noted
- `docs/simulation_quality/event_type_coverage.md` — `belief_assimilated`, `lead_certainty_updated` calibration_hits=0
- `docs/plans/idea_information_belief_trigger_wiring.md` (new, 2026-07-03) — full writeup of the dead
  trigger-path gap, options considered, and recommendation

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/investigation.md` — INFORMATION Deferral section

## Related Code Areas
- `src/domains/information/schema.py:24` — `InformationSourceProfile` dataclass (source_id, source_kind, knowledge_scopes, accuracy, freshness, bias, cost_gold, max_answers_per_query)
- `src/domains/information/schema.py:16` — `InformationSourceKind` enum: GUIDE, GUILD, BLACKSMITH, TRAVELER
- `src/domains/information/phase.py:15` — `InformationBeliefPhase.apply(state, source_profiles, …)`
- `src/domains/information/router.py:32` — router accepts `List[InformationSourceProfile]`
- `src/engine/pipeline.py:152` — `ENABLE_BELIEF_ASSIMILATION` gate for `InformationBeliefPhase`
- `src/domains/optimization/feature_flags.py:18` — `ENABLE_BELIEF_ASSIMILATION: FeatureMode.OFF`
- `src/core/state.py:1145` — `AuthoritativeState.information_source_profiles: List[Any]`
- `config/simulation_quality/profiles/urban_political.yaml` — calibration feature flag profile
- `tools/calibrate_simq.py` — `_load_profile_feature_flags()` injects flag into engine state
- `data/worlds/urban_political/` — world spec where profiles must be declared

## Assumptions / Open Questions
- UQ-1 (resolved, 2026-07-03): No schema field for `information_source_profiles` exists at any layer
  (`WorldSpec`, `WorldCompositionSpec`, `NormalizedWorldComposition`), and `WorldCompiler.compile()`'s
  single `AuthoritativeState(...)` call never passes `information_source_profiles=` — same bug class
  as FACTION's `factions=` gap, unfixed here until this ticket. No global catalog precedent exists
  (unlike FACTION's faction catalog), so schema placement is a plan-phase design choice, not a
  evidence-forced answer.
- UQ-2 (resolved, 2026-07-03): NOT free-form — `InformationQueryRouter.matches_scope()` hard-codes
  literal strings `common_resource_sources`, `recipe_requirements`, `regional_danger`. The ticket's
  originally-proposed values (`danger_rating`, `material_source`, `recipe_definition`) match none of
  these and would have been silently-dead content. Corrected in Scope item 2 above.
- UQ-3 (resolved, 2026-07-03): `belief_assimilated` fires only on Branch A (assimilating a
  `pending_information_responses` entry), not merely from the phase running. **Additional finding**:
  both of `InformationBeliefPhase.apply()`'s trigger branches are unreachable in the current engine
  regardless of this ticket's fix — see Request Summary and `docs/plans/idea_information_belief_trigger_wiring.md`.
  This is the reason AC "calibration_hits > 0" is marked DEFERRED rather than implemented this ticket.

## Implementation Notes
Root cause from SOCIAL-ZERO investigation:
- Dual gate prevents ANY INFORMATION events: flag OFF means the phase never runs; even with flag ON,
  `state.information_source_profiles = []` means no source can answer queries.
- Fix pattern mirrors SOCIAL-ZERO: inject flag via profile YAML + add world-spec content.
- `_load_profile_feature_flags()` already exists in `calibrate_simq.py` and handles flag injection —
  no new tooling code needed, just add `ENABLE_BELIEF_ASSIMILATION: "ON"` to the profile YAML.
- The `InformationBeliefPhase` at `src/engine/pipeline.py:152` reads `source_profiles` from state
  directly — seeding them at compile time is sufficient.

**Implemented 2026-07-03 (Steps 1-6 of `staging_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/plan.md`
only — Steps 7-9 (recalibration, docs/parity ledger update, follow-up-ticket cross-reference
confirmation) are deliberately deferred, per the narrowed 2026-07-03 scope):**
- Step 1: added `InformationSourceProfileSpec` (frozen Pydantic model) to
  `src/worldbuilding/schema.py`, co-located before `PopulationSpec`; added
  `WorldSpec.information_source_profiles: List[InformationSourceProfileSpec] = []`. Mirrored
  `information_source_profiles` onto `WorldCompositionSpec` and `NormalizedWorldComposition` in
  `src/worldassembly/schema.py` (import added; field placed alongside `faction_tension_overrides`).
- Step 2: `WorldAssemblyResolver.assemble()` (`src/worldassembly/resolver.py`) now passes
  `information_source_profiles=list(normalized_comp.information_source_profiles)` into the
  `WorldSpec(...)` constructor — direct passthrough, no merge/override logic (no catalog exists
  for this content, unlike factions).
- Step 3: `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`) imports
  `InformationSourceProfile` from `src.domains.information.schema`, builds a list of domain
  objects from `spec.information_source_profiles` (list→tuple conversion for `knowledge_scopes`),
  and passes `information_source_profiles=information_source_profiles` into the single
  `AuthoritativeState(...)` constructor call.
- Step 4: added the two corrected `InformationSourceProfile` entries (`town_notice_board`,
  `traveling_merchant_rumors`) to `data/worlds/urban_political/world.yaml`; regenerated
  `data/worlds/urban_political/resolved/{world.resolved.yaml,assembly_report.json,
  provenance_manifest.json,validation_report.json}` via
  `python3 -m src.worldbuilding.cli resolve urban_political`. Diff confirmed only the new
  `information_source_profiles:` block plus pre-existing regeneration noise (terrain-warning
  ordering, composition fingerprint, timestamp) changed — regions/entities/resources/
  buildings/quests/factions byte-identical.
- Step 5: added `test_urban_political_guide_profile_selected_for_danger_rating_query` and
  `test_urban_political_traveling_merchant_profile_always_candidate_with_zero_distance_cost` to
  `tests/unit/domains/information/test_phase5_information_query_router.py`, proving the corrected
  `knowledge_scopes` actually match `InformationQueryRouter.route()`'s hard-coded vocabulary, and
  documenting the traveler-bypass/zero-distance-cost behavior explicitly.
- Step 6: added `ENABLE_BELIEF_ASSIMILATION: "ON"` to
  `config/simulation_quality/profiles/urban_political.yaml`, alongside the existing
  `ENABLE_SOCIAL_COOPERATION: "ON"`. Verified via
  `_load_profile_feature_flags('urban_political')` → both flags present.
- Additional test coverage added beyond the plan's minimum: schema/resolver-level round-trip
  tests in `tests/unit/worldassembly/test_assembly.py`
  (`test_resolver_passes_information_source_profiles_from_composition`,
  `test_resolver_no_information_source_profiles_declared_yields_empty_list`, plus a mirrored-field
  assertion appended to `test_composition_normalization_shorthand_and_mixed`); compiler-level tests
  in `tests/unit/worldbuilding/test_world_compiler.py`
  (`test_compiler_seeds_information_source_profiles_from_spec`,
  `test_compiler_no_information_sources_declared_yields_empty_list`,
  `test_urban_political_resolved_world_seeds_two_information_sources`).
- Verified `python3 -m src.worldbuilding.cli validate urban_political --strict` still exits 1 with
  the same pre-existing `[WORLD-UNEXPECTED-SECTION]` warning class also present for untouched
  `dungeon_crawl` — not a new regression. Note: `information_source_profiles` itself is not among
  the flagged unexpected sections, because `WorldValidator.validate()`'s section check
  (`src/worldbuilding/validator.py:369`) compares raw composition YAML keys against
  `WorldSpec.model_fields`, and `information_source_profiles` is now (by Step 1's design) a
  `WorldSpec` field, unlike `faction_tension_overrides` which only exists on
  `WorldCompositionSpec`.
- All new/modified tests pass: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/
  tests/unit/domains/information/` (175 passed, 0 failed).
**Implemented 2026-07-03 (Steps 7-9, completing the ticket):**
- Step 7: recalibrated all 7 `urban_political_*` scenarios (200t/seed42, 500t/seeds
  42/123/456, 1000t/seeds 42/123/456) via `python3 tools/calibrate_simq.py --ticks <T> --seed <S>
  --name urban_political`. Confirmed in every run's console output:
  `Profile feature flags: {'ENABLE_SOCIAL_COOPERATION': 'ON', 'ENABLE_BELIEF_ASSIMILATION': 'ON'}`
  and `INFORMATION grade=C norm=+0.0000 events=0` in the pillar breakdown. Confirmed
  `data/worlds/urban_political/resolved/world.resolved.yaml` compiles
  `information_source_profiles:` with exactly the 2 expected entries (`town_notice_board`,
  `traveling_merchant_rumors`). Grepped each run's `quality_scores.jsonl` for
  `"event_type": "belief_assimilated"` and `"event_type": "lead_certainty_updated"` — 0 matches
  in all 7 runs, confirming the deferred gap stays exactly as documented (not a new regression, not
  an unexpected surprise). Spot-checked `dungeon_crawl` (seed123, 1000t, untouched world) — 0
  INFORMATION events, confirming no leakage from this ticket's schema/compiler/resolver changes
  into worlds without a composition-level `information_source_profiles` declaration. Ran
  `python3 tools/evaluate_simq.py --dry-run` — exit 0, "Summary: 250 pillars checked — 0
  regressions — 0 missing"; no `grade_anchors.json` edit needed (INFORMATION stays `C` in every
  `urban_political_*` entry, exactly as the plan predicted).
- Step 8: updated `docs/simulation_quality/event_type_coverage.md` — refreshed the top-level
  "Last updated" banner and appended honest per-row notes to `belief_assimilated`,
  `paid_information_transaction`, `lead_certainty_updated`, `lead_contradiction_resolved`,
  `paid_info_changed_goal`, `belief_stale`, `decision_diverged_by_belief`, and
  `lead_certainty_changed` — each now states that `information_source_profiles` compiles
  non-empty and `ENABLE_BELIEF_ASSIMILATION=ON` for `urban_political`, but calibration_hits remain
  0 (measured, not guessed) with a pointer to `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` and
  `docs/plans/idea_information_belief_trigger_wiring.md`. No row was marked as newly "hit" — all
  calibration_hits values in the doc still read 0 for these event types, matching the measured
  recalibration output. Added `docs/parity_ledger/infrastructure.yaml::INFRA-256` (next available
  ID after `INFRA-255`, confirmed via `grep '^- id: INFRA-' | tail`) documenting the compile-time
  scaffolding with `status: verified` (per this ledger's convention — "the described mechanism is
  confirmed present," not "the pillar is active," matching the `INFRA-237`/AGENCY-DA
  `support_boundary` precedent) plus an explicit `support_boundary` and `divergence_note` stating
  the pillar remains functionally inactive pending `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`.
  Extended `INFRA-245`'s `v2_evidence` with a pointer to `INFRA-256`. Ran
  `make knowledge-index-update` (docs changed).
- Step 9: re-read `tickets/todos/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER.md` and
  `docs/plans/idea_information_belief_trigger_wiring.md` against current `src/`. Verified
  `src/core/state.py:1144/1145/1150`, `src/engine/pipeline.py:152`, and
  `src/cognition/knowledge_model.py:93-101` citations are all still byte-accurate. Found one drift:
  `src/cognition/self_model_phase.py`'s hardcoded `events=[]` is actually at line 50, not the
  originally-cited line 47 — corrected in the idea doc with a note explaining the shift. Added
  concrete `INFRA-256` cross-references (replacing what would otherwise have been a placeholder)
  to both the follow-up ticket's Scope item 5 / Related Docs and the idea doc's Related section,
  including guidance that the follow-up ticket must *revise* (not just append to) `INFRA-256`'s
  `status`/`divergence_note`/`support_boundary` once a trigger is made reachable.
- Cleaned up `data/runs/` and `reports/release_proof/` per the Workflow Rule.

## Test Summary
(Superseded by the 2026-07-03 narrowed scope — see Implementation Notes above. The
`calibration_hits > 0` outcome originally anticipated here is explicitly DEFERRED, not shipped by
this ticket.)
- Unit/schema tests (317 passing pre-recalibration): `InformationSourceProfileSpec` validation
  bounds, `WorldSpec`/`WorldCompositionSpec`/`NormalizedWorldComposition` field round-trips,
  resolver passthrough, compiler seeding, and router scope-matching regression tests — see Files
  Changed below for the specific test modules.
- Regression: existing worlds with `information_source_profiles=[]` still produce 0 INFORMATION
  events (confirmed both at the unit-test level and live via the `dungeon_crawl` spot-check).
- Calibration (2026-07-03): all 7 `urban_political_*` scenarios recalibrated; confirmed
  `information_source_profiles` compiles with 2 entries and `ENABLE_BELIEF_ASSIMILATION=ON` in
  every run; confirmed `belief_assimilated`/`lead_certainty_updated` calibration_hits are 0 in
  every run (expected, matches the documented deferred gap — not a new finding).
- `python3 tools/evaluate_simq.py --dry-run` passes: exit 0, 250 pillars checked, 0 regressions, 0
  missing.

## Files Changed
- `src/worldbuilding/schema.py` — new `InformationSourceProfileSpec`; `WorldSpec.information_source_profiles` field
- `src/worldassembly/schema.py` — `WorldCompositionSpec`/`NormalizedWorldComposition.information_source_profiles` fields
- `src/worldassembly/resolver.py` — passthrough into `WorldSpec(...)` in `assemble()`
- `src/worldbuilding/compiler.py` — `InformationSourceProfile` construction + `AuthoritativeState(...)` seeding
- `data/worlds/urban_political/world.yaml` — 2 `information_source_profiles` entries
- `data/worlds/urban_political/resolved/world.resolved.yaml` (+ `assembly_report.json`, `provenance_manifest.json`, `validation_report.json`) — regenerated via CLI
- `config/simulation_quality/profiles/urban_political.yaml` — `ENABLE_BELIEF_ASSIMILATION: "ON"`
- `tests/unit/domains/information/test_phase5_information_query_router.py` — router regression tests
- `tests/unit/worldassembly/test_assembly.py` — resolver passthrough + normalizer mirror tests
- `tests/unit/worldbuilding/test_world_compiler.py` — compiler seeding tests
- `data/calibration/urban_political_seed{42,123,456}_{200,500,1000}t/` — recalibrated
  (7 scenarios; `dungeon_crawl_seed123_1000t` spot-checked, not modified as a fixture but re-run)
- `docs/simulation_quality/event_type_coverage.md` — honest current-state notes on 8 INFORMATION/
  COGNITION rows + refreshed "Last updated" banner
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-256`; `INFRA-245` `v2_evidence` extended
- `tickets/todos/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER.md` — cross-references to `INFRA-256`
  added
- `docs/plans/idea_information_belief_trigger_wiring.md` — `self_model_phase.py` line-number
  correction (47→50); `INFRA-256` cross-reference added

## Completion Summary
All 9 plan.md steps complete. Steps 1-6 (2026-07-03, earlier pass): schema/compiler/resolver
plumbing for `information_source_profiles`, corrected `urban_political` world content, router
regression test, `ENABLE_BELIEF_ASSIMILATION=ON` flag — 317 tests passing. Steps 7-9 (2026-07-03,
this pass): recalibrated all 7 `urban_political_*` scenarios, confirming
`information_source_profiles` compiles with 2 entries and the flag is live, while
`belief_assimilated`/`lead_certainty_updated` calibration_hits stay at the expected 0 (deferred,
not a regression); `dungeon_crawl` spot-check confirmed 0 leakage; `make evaluate --dry-run` exits
0 with 250 pillars checked, 0 regressions, 0 missing, no anchor edits needed (INFORMATION stays C
everywhere); `event_type_coverage.md` and parity ledger (`INFRA-256`, extending `INFRA-245`)
updated honestly to reflect scaffolding-verified/pillar-still-inactive status; follow-up ticket and
idea doc cross-references confirmed accurate (one line-number drift found and fixed). Ticket is
DONE. Pillar activation itself is explicitly out of this ticket's scope and deferred to
`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`.
