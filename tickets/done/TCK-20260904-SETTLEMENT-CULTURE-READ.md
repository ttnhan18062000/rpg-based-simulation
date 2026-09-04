---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-SETTLEMENT-CULTURE-READ
phase: open
date: 2026-09-04
tags: [content, documentation]
---

# TCK-20260904-SETTLEMENT-CULTURE-READ

## Title
Settlements read region_cultures as a Culture Drift consumer (idea 61)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 61 (Settlements Develop Personalities). Corrected scope per the 2026-09-02 culture-drift-hardening finding: `CultureDeriver`/`CulturalBiasApplicator` is NOT dormant — it's live, tested, and has a real write-side call site (`CampaignOrchestrator._advance_state` -> `CultureDriftExporter.export`, `src/domains/campaigns/orchestrator.py`) populating `CampaignState.region_cultures`. The real blocker is reachability: `CampaignOrchestrator._build_initial_state()` never carries Region/Place data into its per-episode `AuthoritativeState` at all (no `regions=` argument, no `WorldCompiler` call), so Campaign mode cannot deliver `region_cultures` back into in-episode settlement behavior today, independent of idea 66. This ticket scopes idea 61 as a read-side consumer and resolves the Campaign-mode-reachability question explicitly rather than assuming it's trivially unblocked.

## Scope
- Resolve, as an explicit AC (not left open), whether any of the 21 real corpus worlds runs multi-episode Campaign mode today (the same open question named in `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`'s Scope item 2) — record the answer in `investigation.md`.
- Scope idea 61 to non-Campaign-mode consumption of settlement-personality-relevant culture signal only: name the specific field(s)/method(s) this ticket reads (`region_cultures` / `CultureCarryForward` or the underlying `CultureState` it derives from) and implement a read-side consumer that biases settlement/Place behavior using `CulturalBiasApplicator.compute_culture_delta` or an equivalent narrow adapter, without depending on `CampaignOrchestrator`'s episode-boundary machinery.
- File a separate new ticket (not part of this one's implementation) for the Campaign-mode Region/Place-carry gap in `CampaignOrchestrator._build_initial_state()` — name it explicitly in this ticket's Out of Scope and Related Tickets rather than silently dropping it.
- Correct the stale badge text on `docs/brainstorm/rpg_feature_atlas.html`'s idea 61 card (currently implies `CulturalBiasApplicator` itself is unwired/dormant) to reflect: `CultureDeriver`/exporter write-side is live; `CulturalBiasApplicator` read-side has zero production call sites; the real gap is Campaign-mode Region/Place reachability, not activation.
- `PlaceState` currently has no name/descriptive-identity field (only `place_id` slug) — if this ticket's settlement-personality read-side needs a display identity to attach flavor/bias output to, that gap must be named explicitly (schema addition or explicit workaround), not silently assumed to already exist.

## Out of Scope
- Extending `CampaignOrchestrator._build_initial_state()` to carry compiled regions/places into per-episode `AuthoritativeState` — recommended as a separate, larger ticket given `CulturalBiasApplicator` has zero production call sites today and `CampaignOrchestrator`'s episode-state gap is independent of idea 66.
- Wiring `CultureDeriver`/`CulturalBiasApplicator` for the first time — confirmed already live/complete by the 2026-09-02 hardening-plan investigation; not this ticket's job.
- Broader doc-language corrections to `rpg_m5_memory_reputation_epic.md` / `rpg_m6_political_identity_epic.md` / the parent roadmap (also flagged by the culture-drift-hardening plan) — only the M4 epic doc and the atlas idea-61 card are in this ticket's scope.

## Acceptance Criteria
- [x] `investigation.md` records a definite answer to whether any real corpus world runs multi-episode Campaign mode today. (Answered: No.)
- [x] A read-side consumer exists that reads `region_cultures` (or the `CultureState` it derives from) and produces a settlement/Place-level personality signal, scoped explicitly to non-Campaign-mode consumption. (`SettlementPersonalityService.describe()`, `CampaignOrchestrator.describe_settlement_personality()`, `GET /api/v1/campaigns/{id}/regions/{id}/personality` — scoped to Region granularity, not Place, per the named `PlaceState` identity gap.)
- [x] A new ticket is filed for the `CampaignOrchestrator` Region/Place-carry gap and referenced by ID in this ticket's Related Tickets / Out of Scope — the gap is not silently dropped. (`TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`, `tickets/todos/`.)
- [x] `docs/brainstorm/rpg_feature_atlas.html`'s idea 61 card badge/text is corrected to distinguish `CultureDeriver` (live) from `CulturalBiasApplicator` (zero production call sites) and to name the real Campaign-mode-reachability gap.
- [x] New tests cover the read-side consumer's behavior given populated vs. empty/absent `region_cultures` data.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY (filed by this ticket for the Campaign-mode Region/Place-carry gap in CampaignOrchestrator._build_initial_state())

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md
- docs/world/culture_drift_contract.md
- docs/mechanics/05_world_evolution.md (Cultural Drift)
- docs/parity_ledger/world_dynamics.yaml (WORLD-CULT-001/002/003 untouched; new WORLD-CULT-004 added by this ticket)
- docs/brainstorm/rpg_feature_atlas.html (idea 61)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/domains/culture/deriver.py
- src/domains/culture/applicator.py
- src/domains/culture/exporter.py
- src/domains/campaigns/orchestrator.py (_build_initial_state, _advance_state)
- src/domains/campaigns/state.py (CampaignState.region_cultures)
- src/core/state.py (PlaceState — no name/identity field)

## Assumptions / Open Questions
- Whether any of the 21 real corpus worlds actually runs multi-episode Campaign mode is unresolved today and must be answered by this ticket, per the hardening plan's own Scope item 2.
- `CulturalBiasApplicator` (`src/domains/culture/applicator.py`) has zero production call sites today — only test coverage; this ticket is expected to wire it to at least one real production consumer as part of the read-side implementation, not add another unused/inert piece.
- `PlaceState` has no name/descriptive-identity field; if settlement personality needs one, that's a real schema gap this ticket must name rather than assume solved.
- This ticket deliberately narrows scope away from fixing `CampaignOrchestrator`'s episode-state Region/Place gap, per the epic doc's own recommended narrower framing — the Campaign-mode fix is real but out of scope here and must be tracked by a new ticket, not dropped.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260904-SETTLEMENT-CULTURE-READ/plan.md`'s 8 ordered
steps, no deviations:

1. **New `SettlementPersonalityService`** (`src/domains/culture/settlement_personality.py`) — pure,
   stateless. `describe(culture: Optional[CultureState]) -> SettlementPersonalityDescriptor`. Reuses
   `CULTURE_ACTIVATION_THRESHOLD` and `CulturalBiasApplicator.compute_culture_delta` from
   `src.domains.culture.applicator` unchanged — no new formulas, no redefined threshold.
   `SettlementPersonalityDescriptor` is a frozen dataclass with `traits: Tuple[str, ...]`,
   `tag_deltas: Dict[str, float]`, and an `is_neutral` property (`not traits`). `culture=None` never
   returns bare `None` — it returns the neutral descriptor object, matching the plan's resolved
   None→neutral-descriptor naming decision.
2. **`CampaignOrchestrator.describe_settlement_personality(region_id)`** (`src/domains/campaigns/orchestrator.py`)
   — added directly below the existing `state` property. Composes
   `CultureDriftImporter.get_culture(self._state, region_id)` + Step 1's service. Does not touch
   `_build_initial_state()`/`_advance_state()`/`run_episode()`; verified read-only by a dedicated test
   asserting `episode_index`/`persistent_entities`/`narrative_ledger` are unchanged before/after two
   calls (one populated region, one unknown region).
3. **REST endpoint + presenter** — `SettlementPersonalityResponse` (with `from_domain()`) added to
   `src/api/presenters/campaigns.py`, mirroring `NarrativeLedgerEntryPresenter`'s attribute-access
   pattern (no domain import). `GET /api/v1/campaigns/{campaign_id}/regions/{region_id}/personality`
   added to `src/api/routes/campaigns.py` directly below `get_campaign_history`, same
   `_CAMPAIGN_REGISTRY` lookup / 404-on-unknown-campaign / 500-on-unexpected-error shape. Reads
   `CampaignState` directly from the registry (not through an orchestrator instance), matching
   `/history`'s own pattern.
4. **`register_campaign()` reachability gap** — disclosed, not fixed. See Completion Summary below;
   this is the same pre-existing gap the `/history` endpoint already has.
5. **Atlas correction** (`docs/brainstorm/rpg_feature_atlas.html`, idea 61 card, ~line 2680-2691) —
   badge changed from `cls: gated` ("Blocked...zero callers anywhere") to `cls: partial` (matching the
   file's existing badge vocabulary — grepped, no new CSS class invented), citing this ticket's ID. A
   dated `<strong>Status update, 2026-09-04</strong>` correction sentence was appended to the existing
   `desc` field (not rewritten), naming the three new symbols, the `MotivationBiasService`
   dead-code-in-production finding (broader than just `CulturalBiasApplicator`), and the real
   remaining Campaign-mode-reachability gap. The unrelated `WOUND_THRESHOLD_RATIO` card at line 2137
   (which also contains the phrase "zero callers anywhere") was not touched — confirmed via grep after
   editing that only the idea-61 badge's literal stale text changed.
6. **New ticket filed**: `tickets/todos/TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY.md` — filing only, no
   implementation started. `layer: world`, `tags: [world]` (no "campaign"/"region"/"carry" tag is
   registered; `world` fits per the registry check). Frontmatter validated via
   `tools/validate_frontmatter.py` — passes. Cross-referenced back into this ticket's Related Tickets.
7. **Doc updates**: `docs/world/culture_drift_contract.md`'s Purpose section corrected to distinguish
   "true in tests" from "true via a real read-side consumer as of this ticket" from "not yet true via
   any per-tick entity-decision path"; its Integration Points table gained 3 new rows for the Step
   1-3 symbols. `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` item 3 (idea 61) got a
   `**Status update, 2026-09-04:**` paragraph appended, mirroring items 1/2's established pattern,
   citing both this ticket's ID and the new Step 6 ticket's ID.
8. **Parity ledger**: `WORLD-CULT-004` (P2, `status: verified`) added via
   `tools.parity_ledger_writer.write_entry()` (in-process Python call, not raw Edit) — confirmed the
   resulting diff to `docs/parity_ledger/world_dynamics.yaml` is a clean 14-line append (no full-file
   reformat), and `WORLD-CULT-001/002/003` are byte-identical in content afterward. **Fixed the
   architecture-reviewer-flagged shell-quoting artifact**: wrote the entry's `text` field with a
   normal Python string (real apostrophe in "axis's canonical tag group"), not the garbled
   `axis'"'"'s` substring that had leaked into plan.md's own draft text — confirmed in the written
   YAML the apostrophe rendered correctly.

No deviations from plan.md. No architectural issues encountered.

### Doc-Update phase addendum (independent verification, outside plan.md's stated doc scope)

Per this ticket's own IMPORTANT PROCESS NOTE requirement, disclosing an extra doc file touched
during the Doc-Update phase's independent verification pass:

- **`docs/brainstorm/rpg_simulation_wiring_map.html`** (Cultural Drift row, World layer table,
  ~line 398) — not in plan.md's Files Changed, not in investigation.md's "Docs Requiring Update"
  section, and not one of the 4 docs the implementer listed as already updated. Found stale during
  Doc-Update's own item-5 sweep for other "zero callers"/"dead code" claims about
  `CulturalBiasApplicator`/`MotivationBiasService`: this row's "Expected/next" and "Evidence" cells
  still said "Ideas 56/61/62 all depend on this substrate having a live caller" and
  "`CultureDeriver`/`CulturalBiasApplicator` have zero live callers — the substrate itself is real
  but unwired, a shared blocker for 3 separate ideas" — both now false for idea 61 specifically
  (this ticket gave `CulturalBiasApplicator` a real production caller) and the "zero live callers"
  framing was already stale even for the write side (`CultureDriftExporter.export()` has been
  calling from `CampaignOrchestrator._advance_state()` since E62C). Appended a dated
  "Correction, 2026-09-04" note to the Evidence cell and updated the Expected/next cell to say idea
  61 shipped its consumer while 56/62 remain pending — matching this file's own terse table-cell
  convention, no structural changes. Also tightened one sentence in the atlas idea-61 card's own
  status-update paragraph (in-scope, no disclosure needed) that read ambiguously — "CulturalBiasApplicator
  read-side and the broader MotivationBiasService class it extends remain dead code in production
  outside this new consumer" could be misread as implying MotivationBiasService also gained a call
  site via this ticket's consumer, which is false (the new consumer calls `CulturalBiasApplicator`
  directly, never `MotivationBiasService`) — reworded to state each class's status separately.

## Test Summary
New tests (all passing):
- `tests/unit/domains/culture/test_settlement_personality.py` (8 tests) — None/neutral, zero-axes,
  one test per axis (fatalism/hero_veneration/resource_scarcity_memory/faction_conflict_exposure),
  below-threshold-no-activation, bounded-delta-saturated-axes.
- `tests/unit/domains/campaigns/test_settlement_personality_read.py` (3 tests) — populated region,
  unknown region (neutral descriptor, not bare None), read-only guard (episode_index/
  persistent_entities/narrative_ledger unchanged across two calls).
- `tests/api/test_campaign_history_api.py` (3 new tests appended) — shaped-presenter-not-raw-domain-object,
  404-for-unregistered-campaign, neutral-descriptor-for-unknown-region-in-known-campaign.

Scoped regression run (per test_plan.md's Scoped Pytest Commands):
`pytest tests/unit/domains/culture/ tests/unit/domains/campaigns/ tests/api/ tests/unit/domains/motivation/ tests/unit/motivation/ tests/integration/culture/ -q`
→ 297 passed, 11 failed. All 11 failures are pre-existing live-server/websocket subprocess tests
(`test_live_entity_inspection`, `test_live_health_api_suite`, `test_live_observability_*`,
`test_observability_websocket_suite`, `test_rest_parity`, `test_api_compression`, `test_ws_*`)
requiring a running server on `127.0.0.1:8008` that is not started in this sandbox — matches the
project's documented environment-dependent/flaky category, unrelated to this ticket's changes
(confirmed: none touch culture/campaigns/settlement-personality code). Did not modify these tests or
their gating logic.

Also ran the new parity entry's own cited test directly:
`pytest tests/unit/domains/culture/test_settlement_personality.py::test_describe_with_high_fatalism_axis_produces_fatalistic_signal -q`
→ 1 passed.

Full suite not run (per project testing rule — scoped to domain under modification); Test phase
covers the broader run.

## Files Changed
- `src/domains/culture/settlement_personality.py` (new) — `SettlementPersonalityService`,
  `SettlementPersonalityDescriptor`, `CANONICAL_TAGS`.
- `src/domains/campaigns/orchestrator.py` — added `describe_settlement_personality()` method + 2 new
  imports.
- `src/api/presenters/campaigns.py` — added `SettlementPersonalityResponse` presenter.
- `src/api/routes/campaigns.py` — added `GET /{campaign_id}/regions/{region_id}/personality` route +
  2 new imports.
- `tests/unit/domains/culture/test_settlement_personality.py` (new)
- `tests/unit/domains/campaigns/test_settlement_personality_read.py` (new)
- `tests/api/test_campaign_history_api.py` — extended with 3 new tests + 2 new imports.
- `docs/brainstorm/rpg_feature_atlas.html` — idea 61 card badge + appended correction sentence.
- `docs/world/culture_drift_contract.md` — Purpose section correction + 3 new Integration Points rows.
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — item 3 (idea 61) status-update paragraph.
- `docs/parity_ledger/world_dynamics.yaml` — new `WORLD-CULT-004` entry (via `parity_ledger_writer.py`).
- `docs/brainstorm/rpg_simulation_wiring_map.html` (Doc-Update phase, disclosed above) — corrected
  the Cultural Drift row's stale "zero live callers"/"Ideas 56/61/62 all depend on... a live caller"
  cells, outside plan.md's stated doc scope.
- `tickets/todos/TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY.md` (new) — the filed Region/Place-carry gap
  ticket.
- `tickets/inprogress/TCK-20260904-SETTLEMENT-CULTURE-READ.md` (this file) — Related Tickets
  cross-reference, AC checkboxes, Status, Implementation Notes/Test Summary/Files Changed/Completion
  Summary.
- `staging_artifacts/TCK-20260904-SETTLEMENT-CULTURE-READ/investigation.md`, `plan.md`, `test_plan.md`
  — created during this run's own Investigate/Plan phases (read at the start of this Implement run;
  not authored by the implementer, but part of this run's real changeset).

## Completion Summary
Implemented idea 61 (Settlements Develop Personalities) as a read-side consumer of Culture Drift's
already-live write side, exactly per the approved plan. Added a pure `SettlementPersonalityService`
(`src/domains/culture/settlement_personality.py`) that reuses `CulturalBiasApplicator`'s existing
axis/threshold/delta rules unchanged, a read-only `CampaignOrchestrator.describe_settlement_personality()`
method, and a new `GET /api/v1/campaigns/{campaign_id}/regions/{region_id}/personality` REST endpoint
with a shaped Pydantic presenter — scoped to Region granularity since `PlaceState` has no
name/identity field (a gap named, not solved, per Scope). Filed a new ticket
(`TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY`) for the separate, real Campaign-mode Region/Place-carry
reachability gap rather than fixing it here. Corrected the stale atlas idea-61 badge and appended
dated status updates to `culture_drift_contract.md` and the M4 epic doc. Added one new parity entry,
`WORLD-CULT-004` (P2), via the sanctioned `parity_ledger_writer.py` tool, leaving
`WORLD-CULT-001/002/003` untouched.

**Explicit disclosure (per plan Step 4, not a fix)**: the new `/regions/{region_id}/personality`
endpoint is correct and tested but inherits the same "router-registered but not reachable from a real
running campaign" status the existing `/history` endpoint already has, because `register_campaign()`
(`src/api/routes/campaigns.py:40-50`) has zero production call sites anywhere in `src/` — a
pre-existing gap this ticket does not fix. Both endpoints are reachable in tests today (via direct
`register_campaign()` injection) and via the mounted FastAPI router, but not from a real running
`CampaignOrchestrator`, since nothing in production calls `register_campaign()` after constructing
one.
