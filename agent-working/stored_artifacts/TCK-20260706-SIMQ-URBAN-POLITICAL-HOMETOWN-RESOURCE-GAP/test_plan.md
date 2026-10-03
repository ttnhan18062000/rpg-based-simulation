---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP
artifact_type: test_plan
tags: [simulation-quality, world, adventure, bug]
---

# Test Plan — TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP

This ticket's investigation concludes the "dormant, accepted" path (no code, no profile, no
world-content changes; documentation only), matching the precedent established by
`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` (also a hotfix-tier, doc-only ticket). The test plan below
is scoped accordingly: primarily regression guards confirming nothing was silently changed, plus
the guard tests that would catch scope-creep if a future edit attempted to flip
`ENABLE_ADVENTURE_ROUTING` on for `urban_political` outside of a proper reversal of the two cited
precedents.

## Regression Surface

**Unit:**
- `tests/simulation_quality/test_weights.py::test_urban_political_profile_overrides` — confirms
  `urban_political` profile's `pillar_weights` load correctly; must be unaffected since this
  ticket does not touch the profile YAML.
- `tests/unit/strategic/test_opportunities.py` — `wood_node`/`herb_patch` `source_region_tags`
  behavior (already fixed by the parent ticket); confirms no regression from re-reading the same
  catalog file.

**Integration:**
- `tests/integration/test_world_profile_feature_flag_guardrail.py` — full file, especially:
  - `test_flag_state_matches_expected_per_world` (T2) — `urban_political` must still resolve
    `ENABLE_ADVENTURE_ROUTING` to `OFF` per `expected_world_flag_state.json`.
  - `test_agency_da_anti_drift_guard` (T3) — the **direct** anti-drift guard for this ticket's
    decision: asserts every world in `_meta.agency_da_non_routing_worlds` (includes
    `urban_political`) resolves the flag to `OFF`, and every world in
    `_meta.agency_da_routing_worlds` (`simq_routing_test`, `hero_guild_routing`) resolves to `ON`.
  - `test_information_flag_content_pairing_both_directions` (T4) and the self-model pairing test
    (T5) — unaffected by this ticket but share the same fixture file; run to confirm no accidental
    edit to `expected_world_flag_state.json`.
- `tests/integration/test_scenario_feature_flag_defaults.py` — confirms
  `ENABLE_ADVENTURE_ROUTING` is `FeatureMode.OFF` by default for every scenario except explicit
  overrides; `urban_political_scenarios.yaml` is one of the parametrized scenario files.
- `tests/integration/worldassembly/test_e2e_smoke.py::test_smoke_urban_political_compiles_to_authoritative_state`
  — confirms `urban_political` still compiles with `resource_node_count >= 3`; unaffected since no
  content/module change is made.

**arena-combat:** none relevant — this ticket does not touch combat mechanics.

**simulation_quality:**
- `tests/simulation_quality/test_grade_regression.py` — `urban_political_seed{42,123,456}_
  {200t,500t,1000t}` anchors must remain unchanged (AGENCY stays `"C"` for all 7 entries) since no
  flag/content change occurs.
- `tests/simulation_quality/test_evaluate_harness.py::test_parse_run_key` (or equivalent) — smoke
  check that `urban_political` run-key parsing is unaffected.

## New Tests Required

Per the ticket's Acceptance Criteria, since the "not enabled" branch is the one this
investigation confirms applies, **no new pytest test is strictly required** — the AC calls for a
documentation update, not new runtime behavior. However, one guard is recommended to make this
ticket's "permanently dormant, not just currently inert" claim machine-checked rather than only
doc-asserted:

- **Test name:** `test_urban_political_stays_non_routing_per_agency_da_precedent` (or extend the
  existing `test_agency_da_anti_drift_guard` docstring/parametrization if a maintainer prefers not
  to add a new test function)
  - **Category:** integration / anti-drift guard
  - **What it verifies:** `urban_political` remains present in
    `expected_world_flag_state.json`'s `_meta.agency_da_non_routing_worlds` list specifically (not
    just "some non-routing world resolves OFF" — a name-specific assertion), so that if a future
    edit removes `urban_political` from that list (the first step of ever flipping it to routing)
    without an explicit ticket reversing the two precedents, the guard fails loudly rather than
    silently passing because the list shrank.
  - **Where it should live:** `tests/integration/test_world_profile_feature_flag_guardrail.py`
    (extend T3's existing body or add an adjacent T3b) — this file already owns the
    `agency_da_non_routing_worlds`/`agency_da_routing_worlds` fixture contract.

  This is optional per the AC's literal text (the AC only requires the doc note when the
  "not enabled" branch is taken) — recommend Plan decide whether to include it. It is low-cost
  (one assertion against an already-loaded fixture) and directly closes the "what could silently
  break this decision" question raised by Scope's own framing.

## Scoped Pytest Commands

```
# Direct regression surface for this ticket's decision (flag-state guardrails)
pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q

# Scenario-level flag-default regression
pytest tests/integration/test_scenario_feature_flag_defaults.py -q

# urban_political-specific unit/profile tests
pytest tests/simulation_quality/test_weights.py -k urban_political -q

# Grade-anchor regression (confirm urban_political AGENCY anchors unchanged)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q

# e2e compile smoke check for urban_political
pytest tests/integration/worldassembly/test_e2e_smoke.py -k urban_political -q
```

Never run `pytest tests/` — scope is limited to the simulation_quality / world-profile-flag /
urban_political domains above.

## Anti-Drift Test Guards

- `test_agency_da_anti_drift_guard` (T3, `test_world_profile_feature_flag_guardrail.py`) is the
  primary existing guard: it would fail immediately if any future change silently flips
  `ENABLE_ADVENTURE_ROUTING` to `ON` for `urban_political` (or any of the other 8 originally-named
  non-routing worlds) without updating `expected_world_flag_state.json`'s `_meta` lists and this
  ticket's/AGENCY-DA's/`UNIT-WORLD-AGENCY`'s doc trail in lockstep.
- `test_grade_regression.py`'s `urban_political_*` anchor entries (7 total, all `AGENCY: "C"`)
  guard against a silent grade drift if the flag or resource-tag catalog changes without the
  anchors being recalibrated — matching this ticket family's established "recompute is required,
  not assumed" discipline (see `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s §6 for the
  same reasoning applied to `simq_routing_test`).
- `tests/unit/strategic/test_opportunities.py`'s existing `wood_node`/`herb_patch` coverage
  (already extended by the parent ticket) prevents a regression of the catalog-level
  `source_region_tags` fix that this ticket depends on as a precondition for its "already closed"
  claim.
- No new test should assert the *absence* of `hometown` coverage — that would contradict the
  now-fixed catalog state and this ticket's own confirmation that the content fix already applies
  to `urban_political`.
