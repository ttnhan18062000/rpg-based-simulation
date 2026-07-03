---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-INFORMATION
artifact_type: test_plan
tags: [simulation_quality, information, belief, worldbuilder, feature_flag]
---

# Test Plan — TCK-20260702-SIMQ-UPLIFT2-INFORMATION

## Regression Surface (existing tests that must pass unmodified)

Domain (`src/domains/information/*`, `src/cognition/knowledge_model.py`,
`src/engine/domain/cognition_extras.py`):

- `tests/unit/domains/information/test_phase5_information_source_profile.py`
  (`test_blacksmith_scope_definition`, `test_guide_scope_definition`)
- `tests/unit/domains/information/test_phase5_information_query_router.py`
  (`test_router_selects_and_sorts_correctly`)
- `tests/unit/domains/information/test_phase5_information_boundary.py`
- `tests/unit/domains/information/test_phase5_belief_route_impact.py`
- `tests/unit/domains/information/test_phase5_information_intent_resolver.py`
- `tests/unit/domains/information/test_phase5_information_events.py`
- `tests/unit/domains/information/test_phase5_observation_belief_bridge.py`
- `tests/unit/domains/information/test_phase5_belief_contradiction.py`
- `tests/unit/domains/information/test_phase5_source_trust_update.py`
- `tests/unit/domains/information/test_phase5_information_assimilation.py`
- `tests/unit/domains/information/test_phase5_information_response_normalizer.py`
- `tests/integration/domains/information/test_phase5_information_belief_phase.py`
  (`test_phase_routes_query_for_active_unknowns` — exercises Branch B directly with a
  hand-built entity that already has non-empty `unknowns`; must keep passing exactly as-is,
  since this ticket does not change `InformationBeliefPhase.apply()` itself)
- `tests/perf/test_phase5_information_belief_budget.py`
- `tests/unit/cognition/test_information_seeking.py` — all classes
  (`TestInformationNeedDetectorNormalFlow`, `TestInformationNeedDetectorEdgeCases`,
  `TestUnknownFactExtendedFields`, `TestInformationProviderState`,
  `TestPaidInformationTransaction`, `TestLeadContradiction`,
  `TestKnowledgeStalenessDecay`, `TestLeadKindEnum`, `TestLeadRoutingSystem`) — these
  exercise `InformationNeedDetector`/`PaidInformationTransactionSystem` as pure functions;
  none of them assert engine-wiring reachability, so they must stay green whether or not
  this ticket's scope is expanded to address Risk 1.
- `tests/unit/strategic/test_belief_cycle.py`, `tests/unit/strategic/test_belief_integration.py`,
  `tests/unit/strategic/test_information.py`
- `tests/unit/observability/test_event_extractor_information2.py`
  (`TestLeadCertaintyUpdated`, `TestBeliefStale`, `TestDecisionDivergedByBelief`,
  `TestDecisionDivergenceDetected`) — these test the emitter with hand-built prior/current
  entity state diffs; unaffected by whether the upstream data pathway is wired.
- `tests/simulation_quality/test_information_scorer.py`

Worldbuilding/worldassembly (schema/compiler/resolver — will be touched by this ticket's
plumbing work):

- `tests/unit/worldbuilding/test_world_compiler.py` — all existing cases, in particular
  `test_compiler_minimal_world`, `test_compiler_seeds_faction_tension_from_spec`,
  `test_compiler_seeds_full_faction_roster_at_zero_tension_by_default`,
  `test_compiler_no_factions_declared_yields_empty_factions_dict`,
  `test_urban_political_resolved_world_seeds_bandit_town_council_tension` (FACTION's
  compiled-tension regression guard — must remain unaffected by an unrelated
  `information_source_profiles` schema addition)
- `tests/unit/worldbuilding/test_compiler_context.py`
- `tests/unit/worldbuilding/test_worldspec_schema.py`
  (`test_valid_minimal_world_spec_loads` explicitly named as a must-not-break case in the
  FACTION plan's precedent — same applies to any new `WorldSpec` field added here)
- `tests/unit/worldassembly/test_resolver.py`
  (`test_compile_profile_resolver_overrides`, `test_compiler_backward_compatibility`,
  `test_v2_service_refs_assembly_is_documented_gap`,
  `test_contribution_snapshot_after_normalization`,
  `test_resolve_module_contribution_rejects_raw_spec`)
- `tests/unit/worldassembly/test_assembly.py`
- `tests/integration/worldassembly/test_real_content_world_compositions.py` — re-resolves
  every real `data/worlds/*/world.yaml`; must confirm zero other world picks up
  `information_source_profiles` content unless it declares the new field itself.
- `tests/certification/test_world_compile_determinism.py` — any new compiler seeding step
  must remain deterministic (no RNG, or RNG seeded/scoped per existing `DeterministicRNG`
  convention if content selection ever becomes non-trivial).

## New Tests Required (per AC)

**AC: `ENABLE_BELIEF_ASSIMILATION=ON` injected for all `urban_political_*` calibration runs**
- Reuse the existing `_load_profile_feature_flags()` mechanism (no new test needed for the
  loader itself — already covered by SOCIAL-ZERO's `ENABLE_SOCIAL_COOPERATION` precedent).
  Add one assertion-level check (or extend an existing profile-loading test if one exists) that
  `_load_profile_feature_flags("urban_political")` returns
  `{"ENABLE_SOCIAL_COOPERATION": "ON", "ENABLE_BELIEF_ASSIMILATION": "ON"}` after the YAML
  edit (both flags present, not just the new one — regression guard against clobbering
  SOCIAL-ZERO's prior edit).

**AC: `AuthoritativeState.information_source_profiles` contains ≥2 profiles after compilation
of `urban_political`**
- `test_compiler_seeds_information_source_profiles_from_spec` (new,
  `tests/unit/worldbuilding/test_world_compiler.py`): hand-built `WorldSpec` with 2
  `InformationSourceProfileSpec`-equivalent entries → compiled
  `state.information_source_profiles` has length 2, correct `source_id`/`source_kind`/
  `knowledge_scopes`/`accuracy`/etc. round-tripped from spec to domain object.
- `test_compiler_no_information_sources_declared_yields_empty_list` (new, same file):
  `spec.information_source_profiles == []` → `state.information_source_profiles == []`
  (schema-level regression guard, mirrors FACTION's
  `test_compiler_no_factions_declared_yields_empty_factions_dict`).
- `test_urban_political_resolved_world_seeds_two_information_sources` (new, same file):
  load `data/worlds/urban_political/resolved/world.resolved.yaml` via the existing
  `load_world_spec_from_yaml` helper, compile with a fixed seed, assert
  `len(state.information_source_profiles) == 2` and the two profiles match the corrected
  content (post UQ-2/UQ-4 fixes — see investigation.md Risks 3-4) for `source_id`,
  `source_kind`, `knowledge_scopes`, `accuracy`, `cost_gold`.
- If a composition-level `information_source_profiles`-equivalent field is added to
  `WorldCompositionSpec`/`NormalizedWorldComposition` (per investigation.md UQ-1, pending
  plan-phase resolution of the module-vs-composition fork): mirror FACTION's
  `test_compile_profile_resolver_overrides`-style resolver test —
  `test_resolver_applies_information_source_profiles_from_composition` (new,
  `tests/unit/worldassembly/test_resolver.py`): composition declaring the profiles →
  resolved `WorldSpec.information_source_profiles` contains them; composition declaring none
  → resolved spec unaffected (regression guard, byte-identical to pre-ticket resolved output
  for every world other than `urban_political`).

**AC: At least one of `belief_assimilated` or `lead_certainty_updated` has
`calibration_hits > 0` in at least one `urban_political_*` run**
- **Blocked pending Risk 1's resolution** (investigation.md "Risks and Open Questions" #1) —
  this AC cannot be satisfied by world-content + flag changes alone under current engine
  wiring. Whichever option the human/DA decision selects, add:
  - If option (a) (seed one entity's `self_model.knowledge.unknowns` at compile time to
    reach Branch B): `test_phase_produces_belief_or_route_update_with_seeded_unknown_and_profiles`
    (new, `tests/integration/domains/information/test_phase5_information_belief_phase.py` or
    a new file alongside it) — minimal scenario: one entity with a compiled non-empty
    `unknowns` entry + 2 seeded `InformationSourceProfile`s + flag ON →
    `InformationBeliefPhase.apply()` produces at least one `EntityUpdate` with
    `property_updates["last_routed_query_subject"]` set (Branch B's actual effect — confirm
    with the plan phase whether Branch B alone is enough for AC's literal wording, since
    Branch B does **not** set `last_assimilated_tick`/fire `belief_assimilated` by itself —
    only `last_routed_query_tick`; if AC truly requires `belief_assimilated` specifically,
    Branch A also needs a reachable trigger, which is a larger scope expansion than Branch B
    alone — flag this distinction explicitly back to the ticket owner before writing this
    test, do not silently narrow AC to whatever is easiest to reach).
  - If option (b) (target `paid_information_transaction` instead, with an AC wording
    amendment): `test_paid_information_transaction_fires_with_seeded_provider_and_seeking_project`
    (new) — requires also wiring `InformationNeedDetector.detect_and_generate()` into the
    pipeline and seeding `state.information_providers`, both currently out of this ticket's
    named Scope items; do not implement this option without an explicit scope-amendment
    from the ticket owner.
- **Regression guard (existing-world non-regression)**: `test_information_belief_phase_noop_when_flag_off`
  (new or confirm existing coverage) — a world with `information_source_profiles=[]` and/or
  `ENABLE_BELIEF_ASSIMILATION=OFF` still produces zero `belief_assimilated`/
  `lead_certainty_updated` events (mirrors the ticket's own Test Summary regression bullet).
  Confirm this against `dungeon_crawl` or another untouched world's calibration output,
  analogous to the FACTION plan's `dungeon_crawl`/`frontier_extended` spot-checks.

**AC: `make evaluate --dry-run` exits 0 after anchors updated (0 regressions)**
- No new unit test — this is a calibration/tooling verification step. Run
  `python3 tools/evaluate_simq.py --dry-run` after `grade_anchors.json` updates and confirm
  exit code 0 with 0 regressions outside `urban_political`'s `INFORMATION` pillar (and
  `SOCIAL`, if `ENABLE_SOCIAL_COOPERATION` interacts — it should not, per SOCIAL-ZERO's prior
  clean landing).

**AC: `docs/simulation_quality/event_type_coverage.md` updated with confirmed hits / AC:
Parity ledger updated**
- No new unit test — documentation/ledger updates verified by manual diff review + the
  project's `make knowledge-index-update` step if `docs/` files change (per project
  Workflow Rule).

## Scoped Pytest Commands

```bash
# Information domain (must all still pass unmodified unless this ticket's scope is
# expanded per Risk 1)
pytest tests/unit/domains/information/ tests/integration/domains/information/ \
       tests/perf/test_phase5_information_belief_budget.py \
       tests/unit/cognition/test_information_seeking.py \
       tests/unit/strategic/test_belief_cycle.py tests/unit/strategic/test_belief_integration.py \
       tests/unit/strategic/test_information.py \
       tests/unit/observability/test_event_extractor_information2.py \
       tests/simulation_quality/test_information_scorer.py -v

# Worldbuilding / worldassembly plumbing (schema + compiler + resolver changes)
pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ \
       tests/integration/worldassembly/test_real_content_world_compositions.py \
       tests/certification/test_world_compile_determinism.py -v
```

Do not run the full `pytest tests/` suite (Testing Rule) — scope is bounded to the
information domain and the worldbuilding/worldassembly compile pipeline this ticket touches.

## Anti-Drift Test Guards

- Every new compiler/resolver test must assert **byte-identical** behavior for every world
  other than `urban_political` (or whichever world declares the new field) — mirrors the
  FACTION plan's `test_compiler_no_factions_declared_yields_empty_factions_dict` and its
  `frontier_extended` spot-check precedent. A test that only asserts the happy path for
  `urban_political` without an empty/absent-field regression case is insufficient.
- Do not write a test that asserts `belief_assimilated` fires merely because
  `InformationBeliefPhase.apply()` was called with non-empty `profiles` — per this
  investigation, that alone produces a no-op unless the actor also has a reachable
  `unknowns` entry or pending response. A passing test here must construct that upstream
  condition explicitly (hand-built entity with non-empty `self_model.knowledge.unknowns`, or
  hand-built `pending_responses` list), not merely assert on `profiles` presence.
- Do not let a new test silently redefine AC's literal event names — if the implementation
  path only reaches `paid_information_transaction` (option (b) above) but the AC still reads
  "belief_assimilated or lead_certainty_updated" unamended, the test suite must not be written
  to quietly satisfy a different, easier event; this must go back through the ticket
  process as a scope/AC amendment first.
- `test_urban_political_resolved_world_seeds_two_information_sources`-style tests must load
  the actual regenerated `resolved/world.resolved.yaml` (never hand-edited, always produced
  via `python -m src.worldbuilding.cli resolve urban_political`) — a test that hand-constructs
  a `WorldSpec` bypassing the resolver would not catch a resolver-wiring gap, which is exactly
  the class of bug this ticket is fixing.
- Any test exercising `InformationQueryRouter.route()` with the corrected `knowledge_scopes`
  values (UQ-2 fix) must assert the GUIDE profile is actually selected as a candidate for at
  least one query kind — a test that only checks compilation/seeding without exercising
  `route()` would miss the silent-non-match bug identified in investigation.md.
- Keep `config/simulation_quality/profiles/urban_political.yaml`'s
  `pillar_weights` block and `ENABLE_SOCIAL_COOPERATION: "ON"` (from the prior SOCIAL-ZERO
  ticket) untouched — only add `ENABLE_BELIEF_ASSIMILATION: "ON"` alongside it; a test or
  manual check should confirm both flags are present post-edit, not just the new one.
