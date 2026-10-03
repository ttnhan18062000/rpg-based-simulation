---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-SETTLEMENT-CULTURE-READ
artifact_type: test_plan
tags: [content, documentation]
---

# Test Plan — TCK-20260904-SETTLEMENT-CULTURE-READ

## Regression Surface

Existing tests that must keep passing — nothing in this ticket's recommended design (a new pure
module + a new `CampaignOrchestrator` read method + a new REST endpoint, all additive) should
change behavior of existing culture/motivation/orchestrator/API code, but all of the following are
directly adjacent and must be re-run:

**Unit — Culture Drift substrate:**
- `tests/unit/domains/culture/test_culture_model.py`
- `tests/unit/domains/culture/test_culture_deriver.py`
- `tests/unit/domains/culture/test_culture_applicator.py`
- `tests/unit/domains/culture/test_culture_exporter.py`

**Unit — Motivation bias:**
- `tests/unit/domains/motivation/test_phase14_bias_service.py`
- `tests/unit/motivation/test_motivation_bias_culture.py`

**Integration — Culture Drift acceptance:**
- `tests/integration/culture/test_culture_drift_acceptance.py` (WORLD-CULT-003's own test_path —
  must keep passing unmodified; this ticket does not touch derivation/application formulas)
- `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`
- `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`

**Unit/Integration — CampaignOrchestrator (if the new method touches orchestrator.py):**
- `tests/unit/domains/campaigns/` (full directory — orchestrator/state/exporter tests; confirm
  exact path before running, e.g. `test_campaign_orchestrator*.py`, `test_campaign_state*.py`)
- `tests/integration/scenarios/test_campaign_runtime.py`

**API — if the new REST endpoint lands in `src/api/routes/campaigns.py`:**
- `tests/api/` or `tests/unit/api/routes/` tests covering `campaigns.py` (locate exact file via
  `test-scoper` once the implementation's actual file paths are known — likely named around
  `test_campaign_history` or `test_campaigns_routes`)

**Architecture guard — only if `AdventureRouteScorer.score()` is touched (not recommended, but
must be re-run if Plan chooses that path anyway):**
- `tests/architecture/test_adventure_route_score_max_unchanged.py`
- `tests/unit/domains/adventure/test_phase3_route_scoring.py`
- `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py`
- `tests/unit/ai/goals/test_adventure_goal_scorer.py`

## New Tests Required

Per acceptance criteria, mapped to the investigation's recommended design (module names are
suggestions; adjust to whatever Plan finalizes, but the *behavioral* coverage below must exist
regardless of exact naming):

1. **Test name:** `test_describe_with_none_culture_returns_neutral_descriptor`
   **Category:** unit
   **Verifies:** the new pure read-side function (e.g. `SettlementPersonalityService.describe`)
   returns a well-defined neutral/empty result when given `culture=None` — the realistic default
   case for all 21 corpus worlds (see investigation.md Risks). Must not raise.
   **Location:** `tests/unit/domains/culture/test_settlement_personality.py` (new file, mirroring
   the existing `test_culture_applicator.py` structure)

2. **Test name:** `test_describe_with_zero_axes_culture_returns_neutral_descriptor`
   **Category:** unit
   **Verifies:** a `CultureState()` with all-default (0.0) axes produces the same neutral result
   as `None` — parity with `CulturalBiasApplicator`'s own
   `test_zero_culture_produces_zero_delta` precedent (WORLD-CULT-003's evidence pattern).
   **Location:** same new file as above

3. **Test name:** `test_describe_with_high_fatalism_axis_produces_fatalistic_signal`
   **Category:** unit
   **Verifies:** a `CultureState(fatalism=0.8)` (above `CULTURE_ACTIVATION_THRESHOLD`) produces a
   personality signal reflecting fatalism (whatever concrete shape Plan picks — e.g. a named trait,
   or a non-zero delta for the `caution`/`recovery`/`flee` tag group) — mirrors
   `CulturalBiasApplicator`'s own axis-threshold test pattern
   (`test_high_fatalism_increases_caution_delta`).
   **Location:** same new file as above

4. **Test name:** one test per remaining axis (`hero_veneration`, `resource_scarcity_memory`,
   `faction_conflict_exposure`) analogous to #3, confirming each axis independently produces a
   distinguishable signal — following the existing per-axis test structure in
   `tests/unit/domains/culture/test_culture_applicator.py`.
   **Category:** unit
   **Location:** same new file as above

5. **Test name:** `test_describe_delta_bounded` (mirrors `test_delta_bounded_upper`/
   `test_delta_bounded_lower` in `test_culture_applicator.py`)
   **Category:** unit
   **Verifies:** the new service's output stays within whatever bound it defines (if it exposes a
   raw delta) even for saturated multi-axis `CultureState` inputs — same bounding discipline as
   `CulturalBiasApplicator.compute_culture_delta`'s own `[-0.5, 1.0]` clamp.
   **Location:** same new file as above

6. **Test name:** `test_campaign_orchestrator_describe_settlement_personality_with_populated_region_cultures`
   **Category:** integration
   **Verifies:** given a `CampaignOrchestrator` whose `state.region_cultures` has been populated
   (e.g. by directly seeding a `CultureCarryForward` the way
   `test_culture_exporter.py`/`test_culture_drift_acceptance.py` do, or by running a short
   synthetic multi-episode campaign as the acceptance test already does), the new orchestrator
   method returns a non-neutral descriptor for a region with real culture data, and does **not**
   touch `_build_initial_state()`/`_advance_state()` (assert episode_index/entities are
   unaffected by the call — a pure read).
   **Location:** `tests/unit/domains/campaigns/test_settlement_personality_read.py` (new file) or
   folded into an existing orchestrator test file if Plan prefers

7. **Test name:** `test_campaign_orchestrator_describe_settlement_personality_with_unknown_region_returns_none`
   **Category:** unit
   **Verifies:** given a `region_id` with no entry in `region_cultures` (the default/empty-corpus
   case), the method returns `None`/neutral without raising — mirrors
   `CultureDriftImporter.get_culture`'s own documented "does not raise — unknown regions return
   None" contract.
   **Location:** same new file as #6

8. **Test name:** `test_settlement_personality_endpoint_returns_shaped_presenter_not_raw_domain_object`
   **Category:** integration (API)
   **Verifies:** if Plan adds the REST endpoint, confirm the response body is the new Pydantic
   presenter's shape (no `CultureState`/`CultureCarryForward` fields leaking through directly) —
   architecture-boundary compliance, mirroring how `NarrativeLedgerEntryPresenter` is verified
   for the sibling `/history` endpoint.
   **Location:** wherever `src/api/routes/campaigns.py`'s existing tests live (locate exact path
   before writing — see Regression Surface above)

9. **Test name:** `test_settlement_personality_endpoint_404_for_unregistered_campaign` and
   `test_settlement_personality_endpoint_empty_for_unknown_region`
   **Category:** integration (API)
   **Verifies:** matches `get_campaign_history`'s existing 404-on-unknown-campaign contract, plus
   the new endpoint's own empty/neutral-not-error behavior for a known campaign whose queried
   region has no culture data yet (the realistic default case).
   **Location:** same as #8

10. **Architecture guard — only required if `AdventureRouteScorer.score()` ends up touched despite
    the investigation's recommendation against it:**
    **Test name:** `test_adventure_route_score_max_still_covers_culture_bias_term` (or an update to
    the existing `test_adventure_route_score_max_unchanged.py` assertion/comment)
    **Category:** architecture guard
    **Verifies:** `_ADVENTURE_ROUTE_SCORE_MAX` in
    `src/systems/strategic_systems/intelligence.py` still correctly bounds the Generalized Bypass
    gate after any new additive term is introduced — must fail loudly if the new term silently
    invalidates the shared normalization used by `RegionStabilizationGoalScorer`/
    `SocialContractGoalScorer`.
    **Location:** `tests/architecture/test_adventure_route_score_max_unchanged.py`

## Scoped Pytest Commands

```
# Culture Drift substrate + new settlement-personality unit tests
pytest tests/unit/domains/culture/ -v

# Motivation bias overlay
pytest tests/unit/domains/motivation/ tests/unit/motivation/ -v

# Culture Drift acceptance + related integration scenarios
pytest tests/integration/culture/ -v
pytest tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py -v

# CampaignOrchestrator (new read method) — full domain directory, not cherry-picked files
pytest tests/unit/domains/campaigns/ -v
pytest tests/integration/scenarios/test_campaign_runtime.py -v

# API route (only if the REST endpoint is built)
pytest tests/api/ -k campaign -v

# Architecture guard (only if AdventureRouteScorer is touched — not recommended)
pytest tests/architecture/test_adventure_route_score_max_unchanged.py tests/unit/domains/adventure/ tests/unit/ai/goals/test_adventure_goal_scorer.py -v
```

Never `pytest tests/` — scope strictly to the domains above per project testing rule.

## Anti-Drift Test Guards

- **`test_zero_culture_produces_zero_delta`-style parity**: every new axis-threshold test in the
  new settlement-personality module must assert the *same* `CULTURE_ACTIVATION_THRESHOLD = 0.3`
  boundary `CulturalBiasApplicator` already uses — a divergent threshold in the new consumer would
  silently create two different "personality activates" definitions in the same subsystem.
- **Empty-region_cultures-is-the-default guard**: at least one new test must explicitly assert
  behavior when `region_cultures` is entirely empty (a freshly-constructed `CampaignState`, no
  episodes run) — not just "unknown single region_id" — since this is the actual state of all 21
  corpus worlds today (per investigation.md's answered AC). A test suite that only covers the
  populated-culture path would pass in CI while shipping a consumer nobody's real corpus world
  ever exercises non-trivially.
- **No entity-decision-path regression guard**: if the implementation does *not* touch
  `AdventureRouteScorer`/`MotivationBiasService`'s live call sites (the recommended path), add or
  confirm a test/assertion that entity route scoring is byte-identical before/after this ticket for
  a fixed seed — proving the ticket is genuinely additive and did not accidentally thread culture
  into the tier-5 competition scorer's shared normalization.
- **`_build_initial_state()`/`_advance_state()` untouched guard**: the new `CampaignOrchestrator`
  read method's test (#6 above) must assert `episode_index`, `persistent_entities`, and
  `narrative_ledger` are unchanged by calling it — proving the read genuinely does not depend on or
  mutate episode-boundary machinery, which is the ticket's own explicit scope boundary.
- **API boundary guard**: the new endpoint's test must fail if a raw `CultureState`/
  `CultureCarryForward` attribute name leaks unshaped into the JSON response — matching this
  repo's "no raw domain models from API" rule already enforced for `NarrativeLedgerEntryPresenter`.
