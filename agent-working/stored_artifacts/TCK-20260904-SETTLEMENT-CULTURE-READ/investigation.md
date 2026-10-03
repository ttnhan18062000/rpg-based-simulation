---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-SETTLEMENT-CULTURE-READ
artifact_type: investigation
tags: [content, documentation]
---

# Investigation — TCK-20260904-SETTLEMENT-CULTURE-READ

## Search-Before-Grep Trail

Per CLAUDE.md's hard rule, run fresh for this ticket's own topic (not reused from create-tickets'
prior research, though the findings agree):

1. `mcp__knowledge-search__search_docs` — `"settlement personality culture drift region_cultures
   CulturalBiasApplicator"` and `"CampaignOrchestrator build initial state region place
   authoritative state"`. Surfaced `docs/world/culture_drift_contract.md`,
   `docs/simulation/domains/campaign_orchestrator_contract.md`,
   `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`,
   `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`, and the E62A/B/C done tickets.
2. `graphify query "region_cultures CulturalBiasApplicator settlement Place"` and `graphify query
   "PlaceState Place-level behavior world compiler per-tick system"` — traversed the
   `CulturalBiasApplicator`/`MotivationBiasService`/`CultureDeriver` community (all test/exporter
   nodes, no non-test production caller node) and the `PlaceState` community (`WorldCompiler`,
   `AuthoritativeState`, `RegionState`, `BuildingState`, etc.).
3. `docs/REGISTRY.yaml` exists; read for prior idea-61/culture-drift ticket coverage (E62A/B/C,
   TCK-20260619-E62*, all `done`).
4. Followed with source reads and targeted grep only after the above, per the required order.

## Current Behavior

### Culture Drift substrate — confirmed live, not dormant

- `CultureDeriver.derive()` (`src/domains/culture/deriver.py:48-111`) — pure, stateless.
  `ChronicleHierarchy.events` → `Dict[region_id, CultureState]`, keyed by
  `entry.payload.get("region_id", "__global__")`. Four axes (`fatalism`, `hero_veneration`,
  `resource_scarcity_memory`, `faction_conflict_exposure`), each `min(1.0, raw_sum / 3.0)`.
- `CulturalBiasApplicator.compute_culture_delta(culture, tags)` (`src/domains/culture/applicator.py:45-92`)
  — pure. Axis > `CULTURE_ACTIVATION_THRESHOLD` (0.3) → additive tag-keyed deltas, bounded
  `[-0.5, 1.0]`.
- `CultureDriftExporter.export()` (`src/domains/culture/exporter.py:30-61`) — the **real, live**
  write-side call site: `CampaignOrchestrator._advance_state()`
  (`src/domains/campaigns/orchestrator.py:226-230`), called after
  `narrative_ledger.extend()`/`ChronicleGrouper().group(...)`, once per completed episode. Writes
  `CampaignState.region_cultures[region_id] = CultureCarryForward(region_id, culture,
  derived_episode)`.
- `CultureDriftImporter.get_culture(campaign_state, region_id)` (`exporter.py:64-79`) — thin
  read-side lookup helper, returns `Optional[CultureState]`. Already exists; not yet called from
  any production code.
- `MotivationBiasService.compute_bias_multiplier(entity, tags, culture_values=None)`
  (`src/domains/motivation/service.py:17-72`) — accepts an optional `CultureState` and, when
  given, adds `CulturalBiasApplicator.compute_culture_delta(...)` before the final
  `max(0.1, multiplier)` clamp.

This confirms the ticket's premise: the write side (`CultureDriftExporter.export()`) is real and
live. The 2026-09-02 hardening-plan correction (`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`)
was accurate; the atlas's "zero callers anywhere" framing (see Docs Requiring Update) is stale for
the *write* side but happens to still be literally true for the *read* side, which is the actual
gap.

### Read side — genuinely zero production call sites (broader than the ticket text states)

Verified directly (grep across `src/`, excluding `tests/`):

- `CulturalBiasApplicator` — imported/used only inside `src/domains/culture/applicator.py` itself
  and `src/domains/motivation/service.py` (the optional-branch that calls it). No other `src/`
  module imports it.
- `MotivationBiasService.compute_bias_multiplier(...)` — **has zero call sites anywhere in
  `src/`, with or without `culture_values`.** Every call site found (12 of them) is in
  `tests/unit/domains/motivation/test_phase14_bias_service.py`,
  `tests/unit/motivation/test_motivation_bias_culture.py`,
  `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`, and
  `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`. This is a stronger
  finding than the ticket text's framing ("`CulturalBiasApplicator` has zero production call
  sites") — the entire `MotivationBiasService` class it was built to extend is also unused in
  production, independent of the culture parameter. Route/goal scoring in this codebase does not
  currently go through `MotivationBiasService` at all; it goes through
  `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`), which has its own
  independent, inline personality/urgency/risk formula and never calls
  `MotivationBiasService`.

### CampaignOrchestrator — confirmed reachability blocker, and it is worse than just Region/Place

- `CampaignOrchestrator._build_initial_state()` (`src/domains/campaigns/orchestrator.py:575-655`)
  — confirmed: constructs `AuthoritativeState(tick=0, seed=episode_seed)` (episode 0 / no
  survivors) or reconstructs only `entities: Dict[int, EntityState]` from
  `EntityCarryForward` snapshots (identity/equipment/social fields only). **No `regions=`
  argument, no `WorldCompiler` call, anywhere in this method.** `state.regions` is therefore an
  empty dict for every Campaign-mode episode today.
- This is a **general** reachability gap, not culture-specific. `TownResolutionSystem.resolve()`
  (`src/engine/town_resolution.py:38-43`) early-exits when `len(state.regions) == 0` — meaning
  regional tax/suppression/vacancy-signal logic is *also* silently inert for every Campaign-mode
  episode today, for the same root cause. Worth citing as corroborating evidence of the blocker's
  severity, not something this ticket fixes.
- By contrast, every non-Campaign entrypoint that constructs an initial `AuthoritativeState` does
  call `WorldCompiler.compile(spec, seed=...)` and does get `regions`/`places` populated:
  `src/cli/entry.py:223-228`, `src/api/engine_manager.py:136`, `src/lab/orchestrator.py:198`,
  `src/worldbuilding/cli.py:282`. `WorldCompiler.compile()` (`src/worldbuilding/compiler.py:322`)
  is confirmed to construct real `PlaceState` objects today (idea 66's schema-migration and the
  three sibling tickets on this branch have wired this — `PlaceState` is not schema-only anymore).

### Where region_cultures physically lives vs. where entity decisions run

- `CampaignState.region_cultures: Dict[str, CultureCarryForward]`
  (`src/domains/campaigns/state.py:301`) lives on `CampaignState`, an object owned exclusively by
  `CampaignOrchestrator`. It has **no relationship to `AuthoritativeState`/`EntityState` at all** —
  `_build_initial_state()` never threads any campaign-level context (culture, region_cultures, or
  otherwise) into the per-episode `AuthoritativeState`. This means: even if the Region/Place-carry
  gap above were fixed (out of scope, tracked separately), `region_cultures` specifically would
  *still* not reach in-episode entity decision-making without a **second**, distinct piece of new
  plumbing (e.g. seeding a culture snapshot into `RegionState` or a new `AuthoritativeState` field
  at episode start) — this is not automatically solved by fixing Region/Place reachability alone.
  Flagging this explicitly so it is not silently assumed away later.
- Because of this, wiring `CulturalBiasApplicator`/`MotivationBiasService` into any per-tick,
  per-entity system that only ever sees `AuthoritativeState` (`AdventureRouteScorer.score()`,
  `WorldDynamicsSystem`, `TownResolutionSystem`, `CampService`) would produce **dead-in-practice**
  wiring today: those systems have no code path that could ever receive a non-`None` `CultureState`
  from `CampaignState.region_cultures`, Campaign-mode or not. This is the real reason a genuinely
  reachable "production consumer" cannot live in the per-tick entity-decision layer without first
  building the cross-layer plumbing this ticket's own Out of Scope explicitly defers.

### Recommended non-Campaign-mode-episode-machinery consumption point

Given the above, the only place a **real, reachable, non-`None`-in-practice** production consumer
can live today is the layer that already legitimately holds `CampaignState`: the orchestrator/API
layer, *not* `_build_initial_state()`/`_advance_state()` themselves. A directly analogous, already-
shipped precedent exists for exactly this shape of read:

- `GET /api/v1/campaigns/{campaign_id}/history` (`src/api/routes/campaigns.py:66-133`, E32E) reads
  `CampaignState.narrative_ledger` from a module-level `_CAMPAIGN_REGISTRY: Dict[str,
  CampaignState]`, wraps it in a domain `NarrativeLedger`, and shapes the result through a
  Pydantic presenter (`src/api/presenters/campaigns.py`) — "no raw domain models from API" is
  already enforced here for the sibling narrative-ledger read.

**Recommended shape for this ticket's read-side consumer** (concrete, evidence-backed; final
naming/placement is a Plan-phase call, not locked here):

1. A new pure function/service, e.g. `SettlementPersonalityService.describe(culture:
   Optional[CultureState]) -> <descriptor>` (new module under `src/domains/culture/`) that wraps
   `CulturalBiasApplicator.compute_culture_delta` over a small canonical tag set to produce a
   named settlement-personality signal, and returns a defined neutral/empty result when
   `culture is None`. Pure and CampaignState-independent — trivially testable with hand-built
   `CultureState` fixtures for both the populated and absent cases (satisfies the AC directly).
2. A new read method on `CampaignOrchestrator` (e.g. `describe_settlement_personality(region_id)`)
   composing `CultureDriftImporter.get_culture(self._state, region_id)` + step 1. This does **not**
   touch `_build_initial_state()` or `_advance_state()` — it is a pure query over already-populated
   `CampaignState`, satisfying "without depending on CampaignOrchestrator's episode-boundary
   machinery."
3. A new REST endpoint alongside `get_campaign_history` in `src/api/routes/campaigns.py` (e.g.
   `GET /api/v1/campaigns/{campaign_id}/regions/{region_id}/personality`), with a new Pydantic
   presenter in `src/api/presenters/campaigns.py`, following the exact existing pattern. This is
   the "real production consumer" the ticket's Assumptions require — it is genuine `src/` route
   code, not test scaffolding.

**Caveat to carry into Plan**: `register_campaign()` (`src/api/routes/campaigns.py:40-50`) —
which populates `_CAMPAIGN_REGISTRY` — has **zero call sites anywhere in `src/`** today either;
its own docstring claims "In production, CampaignOrchestrator calls register_campaign() after
creation," but `CampaignOrchestrator.__init__`/`run_episode()` never does. This means the existing
`/history` endpoint is already in the same "wired but never actually reachable via a real running
campaign" state this ticket would put a new endpoint into. This is a pre-existing gap, not
introduced by this ticket, and the existing `/history` endpoint shipped without fixing it — so
precedent supports not fixing it here either, but Plan should decide explicitly rather than
silently inherit it.

**Alternative considered and not recommended as primary: `AdventureRouteScorer.score()`.** This is
the one genuinely live, per-entity, non-Campaign-mode-specific route-scoring pipeline in
production (`src/domains/adventure/scoring.py`, invoked from `AdventureGoalScorer.score()` via
`StrategicIntelligenceSystem`, confirmed the sole live adventure-decision path per
`src/engine/faction_decision.py`'s own module docstring). It already has an established pattern of
optional additive bias terms (`memory_adjustment`, `dependent_bias`, `plan_advance_bonus`) that a
`culture_bias` term could follow. **Rejected as the primary recommendation** for two concrete
reasons found during this investigation: (a) as shown above, this scorer only ever sees
`AuthoritativeState`/`EntityState`, which has no channel to `CampaignState.region_cultures` at
all — wiring it here would be dead code in practice, identical to the current
`MotivationBiasService` situation, just moved; (b) `tests/architecture/test_adventure_route_score_max_unchanged.py`
pins `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` in
`src/systems/strategic_systems/intelligence.py` as the shared Generalized Bypass gate denominator
(STRAT-186) reused by `RegionStabilizationGoalScorer`/`SocialContractGoalScorer` — an unconditional
new additive term of up to `+1.0` (the applicator's own upper bound) risks silently invalidating
that shared normalization across three unrelated scorers. If Plan chooses this path anyway despite
the reachability problem above, this constant and its guard test must be explicitly re-examined,
not left as collateral damage.

### PlaceState / RegionState identity — the named gap, and a workaround that avoids it

- `RegionState` (`src/core/state.py:259-320`) already has a `name: str` field (line 263) and an
  `id: str` — `region_cultures` keys align exactly with `RegionState.id` (both are `region_id`
  strings from the same event-payload attribution). **No new field is needed to attach a
  personality signal at Region granularity.**
- `PlaceState` (`src/core/state.py:334-...`) has **no name/descriptive-identity field** — only
  `place_id` (a slug) — confirmed by direct read. If a future ticket wants personality attached to
  an individual CITY-kind `Place` rather than its parent `Region`, that schema gap is real and
  unresolved.
- **Recommended resolution for this ticket** (per Scope bullet 4's requirement to name this
  explicitly rather than assume it away): scope the read-side consumer to **Region granularity**,
  using `RegionState.id`/`RegionState.name` as the settlement-personality signal's identity —
  matching `region_cultures`'s own natural keying — and explicitly do **not** attempt to attach
  the signal to an individual `PlaceState` in this ticket. Name the `PlaceState` display-identity
  gap in Out of Scope as a real, separate, unresolved gap (schema addition, not built here), so it
  is not silently assumed solved.

## Mechanics / Engine Constraints

- `docs/mechanics/05_world_evolution.md` §7 "Cultural Drift (E62)" — the Bible-level statement of
  the same formulas verified above (axis rules, normalisation, delta rules, activation threshold).
  Any new consumer must stay consistent with these already-certified formulas — this ticket adds a
  *caller*, not new derivation logic, so no formula change is anticipated.
- `docs/world/culture_drift_contract.md` (AUTHORITATIVE, E62A–E62C complete) — the authoritative
  contract. Its "Purpose" section already claims culture state "produces measurable differences in
  entity motivation scoring (per-region, transient)" in present tense — this is aspirational/not
  yet true in production (see Docs Requiring Update).
- Authoritative-state immutability (`docs/core/state.md`) — the recommended consumer design is
  fully compliant: it is a pure read over `CampaignState` (already mutable-but-owned-by-orchestrator,
  not `AuthoritativeState`) and never touches `AuthoritativeState`/`EntityState` durable fields.
- API boundary rule (project CLAUDE.md, "Do not expose raw domain models from APIs") — the
  recommended REST-endpoint consumer must go through a new Pydantic presenter, following
  `src/api/presenters/campaigns.py`'s existing pattern; do not return `CultureState`/
  `CultureCarryForward` directly from a route.

## Docs Requiring Update

- `docs/brainstorm/rpg_feature_atlas.html`: idea 61's card badge (line ~2683-2686,
  `"badges": [{"cls": "gated", "text": "Blocked — the mechanism it needs (Culture Drift) is real
  and live, but has zero callers anywhere; not buildable until that's wired"}]`) is stale and
  directly contradicted by the confirmed live write-side call site
  (`CultureDriftExporter.export()` from `_advance_state()`). Must be corrected to distinguish:
  `CultureDeriver`/write-side is live; `CulturalBiasApplicator`/`MotivationBiasService` read-side
  has zero production call sites (until this ticket adds one); the real remaining gap is
  Campaign-mode Region/Place-AuthoritativeState reachability (tracked by the new ticket this
  ticket must file), not "wiring." This is explicitly named as in-scope by the ticket itself.
- `docs/world/culture_drift_contract.md`: the "Purpose" section's present-tense claim that culture
  state "produces measurable differences in entity motivation scoring" is true only in tests
  today; and its "Integration Points" table should gain a row for the new read-side consumer this
  ticket adds (whatever Plan finalizes: `SettlementPersonalityService` and/or the new
  `CampaignOrchestrator`/API method), since the contract currently stops at
  `CultureDriftImporter` with no listed caller.
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`: item 3 (idea 61) should record that
  the read-side consumer has shipped (mirroring how item 1's 2026-09-04 status update was recorded
  for the Camp/Nest classification ticket) and reference this ticket's ID plus the new
  Region/Place-carry-gap ticket ID.

The following docs were considered and are explicitly **not** required to change by this ticket
(Format 2 — do not read as Format 1 bullets):

`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md` (path:
`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`) does not need to change: it is
itself a plan/finding document describing the investigation that produced this ticket, and its own
Scope item 2 (the 21-corpus-worlds question) is answered by this ticket's investigation.md per the
ticket's own AC, not by editing the hardening-plan doc itself — the hardening plan's Acceptance
Signal is satisfied by the epic docs being corrected (which is in scope above), not by editing the
hardening-plan document.

`docs/mechanics/05_world_evolution.md` (path: `docs/mechanics/05_world_evolution.md`) does not need
to change: §7's formulas are unaffected by adding a new caller of already-certified derivation/
application logic — no formula, axis, or threshold changes.

`docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` and
`docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` (paths as named) do not need to
change: the ticket's own Out of Scope explicitly excludes these broader doc-language corrections,
reserving them for the hardening plan's own separate scope.

## Parity Ledger Overlap

- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-CULT-001` (status: verified, P1, CultureState
  round-trip), `WORLD-CULT-002` (status: verified, P1, `CultureDeriver` axis rules), `WORLD-CULT-003`
  (status: verified, P1, `CulturalBiasApplicator` delta rules + acceptance test). All three
  `test_path` values confirmed to exist and pass their described behavior:
  `tests/unit/domains/culture/test_culture_applicator.py::test_zero_culture_produces_zero_delta`,
  `tests/integration/culture/test_culture_drift_acceptance.py::test_two_regions_diverge_after_5_episodes`.
  None are P0, so none strictly *require* a passing `test_path` by the P0 rule, but all three are
  P1 and already verified — this ticket's new read-side consumer does not change any of these
  three entries' underlying formulas, so no `status`/`v2_evidence` edit is required to them. If
  Plan's final design introduces a genuinely new, distinct behavior claim (e.g. "settlement
  personality descriptor produces a named trait when an axis exceeds threshold"), a **new** parity
  entry should be added under `world_dynamics.yaml` rather than editing the three existing ones —
  flag this as a Plan-phase decision, not resolved here.

## Prior Work

- `TCK-20260619-E62A-CULTURE-MODEL`, `TCK-20260619-E62B-CULTURE-DERIVER` (implied by contract doc),
  `TCK-20260619-E62C-MOTIVATION-OVERLAY` (all `tickets/done/`) — built the full write-side +
  transient-overlay substrate this ticket consumes. No conflict; this ticket is purely additive on
  top.
- `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md` (2026-09-02) — the direct
  parent finding that produced this ticket; its Scope item 2 (21-corpus-worlds question) is
  answered below (Risks and Open Questions).
- Sibling tickets landed on this branch (`TCK-20260904-CAMP-NEST-CLASSIFICATION`,
  `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`, `TCK-20260904-LAIR-ENTITY-ANCHOR`) — confirmed genuinely
  unrelated: all three touch `CampService`/`Place` classification/world-gen wiring, none touch
  `src/domains/culture/`, `src/domains/motivation/`, or `src/domains/campaigns/orchestrator.py`'s
  `_advance_state()`/`_build_initial_state()`. One relevant fact inherited from them: `PlaceState`
  is confirmed no longer schema-only (`WorldCompiler.compile()` at `src/worldbuilding/compiler.py:322`
  really constructs `PlaceState` objects now), which is why this investigation could confirm the
  Region-vs-Place identity gap concretely rather than as a hypothetical.
- `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD` — the parent epic tracking the broader
  Region/Place rebuild; the new Campaign-mode Region/Place-carry-gap ticket this ticket must file
  should reference this epic too, since it is the same underlying schema family.

## Risks and Open Questions

- **Answered (per AC requirement): do any of the 21 real corpus worlds run multi-episode Campaign
  mode today? No.** Evidence: `config/simulation_quality/corpus_registry.yaml`'s `_worlds` key
  (the canonical 21-world registry) has no campaign-related key per world. The only place
  `campaign_episodes` appears anywhere in `config/` is
  `config/simulation_quality/profiles/campaign_life_arc.yaml` (`campaign_episodes: 3`,
  `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`) — a **standalone calibration profile**, not one of the
  21 registered corpus worlds (confirmed: `campaign_life_arc` does not appear in
  `corpus_registry.yaml`). `tools/calibrate_simq.py`'s `_run_campaign_engine()` is described in its
  own docstring as "previously reachable only from test scaffolding" until that ticket added it as
  a calibration-profile entry point — again, not the standard 21-world corpus-scoring pipeline.
  Campaign mode is also reachable via the live `/api/v1/campaigns` route (registered in
  `src/api/server.py:136-137`), which is client-triggered, not part of any automated corpus run.
  **Conclusion: Culture Drift's write side is real and tested but is not exercised by the standard
  corpus pipeline against any of the 21 registered worlds today** — this is consistent with, and
  reinforces, `rpg_m9_corpus_test_coverage_epic.md`'s independent finding that ideas needing a real
  Campaign run "can only be tested by a real multi-episode Campaign run" and
  `CampaignScorecardEvaluator` has no fields to catch a failure in them.
- **Direct consequence for this ticket's tests**: the "empty/absent `region_cultures`" test case is
  not a synthetic edge case — it is the realistic default for every one of the 21 corpus worlds
  today. Test coverage must treat it as at least as important as the "populated" case, not as an
  afterthought.
- **Open, for Plan to decide, not assumed here**: the exact placement/naming of the new consumer
  (module name, method name, endpoint path) — this investigation recommends a concrete shape
  (Section "Recommended non-Campaign-mode consumption point") with evidence but does not lock file
  names, since that is Plan's job.
  Also open: whether Plan bundles the small, apparently-pre-existing `register_campaign()`
  wiring gap into this ticket (so the new endpoint is reachable from a real running campaign, not
  just router-registered) or explicitly defers it as a separate, named gap the same way the
  existing `/history` endpoint currently leaves it. Recommend the latter (defer, name explicitly)
  to keep this ticket's scope matched to its stated Out of Scope, but flag for Plan's explicit
  decision.
- **New ticket to file** (per Scope/AC requirement): the Campaign-mode Region/Place-carry gap in
  `CampaignOrchestrator._build_initial_state()` — confirmed real and independent of idea 66 landing
  (idea 66's schema/WorldCompiler work is done; the orchestrator simply never calls
  `WorldCompiler.compile()` or passes `regions=`). Should also note, per the finding above, that
  fixing Region/Place carry alone does **not** automatically make `region_cultures` reachable
  in-episode — a second, distinct piece of plumbing would still be needed to thread culture into
  `AuthoritativeState`. The new ticket should scope Region/Place carry only, and explicitly flag
  the second gap as a further, even-later dependency for any idea (56/57/61/62) that eventually
  wants *in-episode* (not just post-episode-query) culture-biased entity behavior.

## Anti-Drift Hazards

- **Do not wire `CulturalBiasApplicator`/`MotivationBiasService` into
  `AdventureRouteScorer.score()`'s unconditional scoring path** without first re-deriving/re-pinning
  `_ADVENTURE_ROUTE_SCORE_MAX` (`src/systems/strategic_systems/intelligence.py`,
  guarded by `tests/architecture/test_adventure_route_score_max_unchanged.py`) — a naive additive
  `culture_bias` term risks silently invalidating the Generalized Bypass gate's normalization
  shared by `RegionStabilizationGoalScorer`/`SocialContractGoalScorer` (STRAT-186). This
  investigation recommends not choosing this call site as primary at all (see above); if Plan
  overrides that recommendation, this guard test is the first thing to re-examine.
- **Do not conflate "wired into a route/method" with "exercised by real gameplay."** Per the
  `register_campaign()` finding above, a technically-correct new consumer can still be
  practically unreachable without a live campaign actually registering itself. Do not let a
  green `done-checker` pass stand in for confirming the consumer is genuinely exercised outside
  tests — call this out explicitly in the ticket's Completion Summary rather than implying full
  end-to-end reachability if it isn't actually there.
- **Do not silently expand scope into fixing `_build_initial_state()`'s Region/Place gap** while
  building the read-side consumer — it is tempting once inside `orchestrator.py`, but is
  explicitly Out of Scope and tracked by a separate new ticket.
- **Do not add a `name`/display-identity field to `PlaceState`** as an incidental side-effect of
  wanting a settlement label for the personality signal — the Region-granularity workaround
  (`RegionState.id`/`.name`) avoids needing this. If Plan decides Place-granularity is actually
  required, that is a deliberate schema-addition decision to make explicitly, not a silent
  addition.
- **Do not treat the atlas card correction as free-form** — the exact stale text to replace is
  cited above with its approximate line location; verify against current file content before
  editing, since other atlas edits may have landed on this fast-moving doc between investigation
  and implementation.
