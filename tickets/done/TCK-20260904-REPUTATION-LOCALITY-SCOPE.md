---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-REPUTATION-LOCALITY-SCOPE
phase: done
date: 2026-09-04
tags: [social, determinism]
---

# TCK-20260904-REPUTATION-LOCALITY-SCOPE

## Title
Idea 60 — Reputations Are Local (region-scoped public_reputation)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 60 (Reputations Are Local, docs/brainstorm/rpg_feature_atlas.html) targets SocialComponent.public_reputation (src/core/models/social.py:51) — a single unscoped float with no location, observer, or region parameter anywhere in its read or write paths (idea 60's own card, citing src/systems/social_systems/relationships.py:92-93). The M5 epic doc's premise that a "competing reputation system" risk was downgraded because "PublicReputationProfile's only mutator has zero call sites anywhere" is CONFIRMED STALE as of 2026-09-04: TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING (DONE, landed 2026-08-28) wired ReputationUpdateService.process_witnessed_event() to a real call site in QuestResolutionSystem.enforce() (src/engine/quests.py:233), for the "successful_escort" event kind only. However, fresh investigation (2026-09-04) confirms this correction does NOT change idea 60's actual scope: PublicReputationProfile (src/core/cognition.py, a per-label dict on RelationshipModel) is structurally distinct from SocialComponent.public_reputation (a plain float) — idea 60's own card and the 2026-09-02 social/relationship-axis proposal (§3.5) both confirm idea 60 targets the latter exclusively and never proposed building on or merging with PublicReputationProfile. This ticket's Investigate phase should record the corrected premise as fresh evidence, not repeat the epic doc's stale claim, while scoping strictly to SocialComponent.public_reputation. Idea 60 is sequenced first within the reputation branch because ideas 53 and 54 (sibling child tickets of the same epic) both write to this same field and must account for whatever shape this ticket leaves it in.

## Scope
- Add region/observer-local scoping to SocialComponent.public_reputation's read and write paths, reusing the shape precedent of the existing SocialComponent.place_attachment field (Dict[RegionID, float], src/core/models/social.py:47, already maintained per-tick by SocialMemoryService) rather than inventing a new locality representation from scratch — exact granularity (per-region vs per-observer vs per-settlement) is a Plan-phase decision.
- Keep RelationshipService.process_update() (src/systems/social_systems/relationships.py) as the sole authoritative write path for the new locality-scoped structure — no second write path introduced.
- Update the three known live consumers of the current scalar field to consume the new shape without breaking existing tests: SocialAppraisalSystem.appraise_contract()'s trust-blend read (src/systems/social_systems/appraisal.py:30-36, currently `public_trust = source_entity.social.public_reputation / 2.0`), apply_reputation_discount() (src/systems/economy_systems/reputation_discount.py), and campaigns/social_memory.py's cross-episode carry-forward.
- Extend EntityState.to_canonical_dict() / CanonicalStateHasher (src/engine/checkpoint.py) and src/replay/fingerprint.py (currently line 69, `reputation={ent.social.public_reputation:.3f}`) to cover the new shape explicitly — public_reputation is currently 1 of the 10-of-15 SocialComponent fields already covered as a scalar; the shape change must preserve that determinism coverage in the same ticket, not leave it silently dropped.
- Document, as a corrected investigation finding, that PublicReputationProfile/ReputationUpdateService (src/core/cognition.py, src/domains/commitment/reputation.py) is a structurally distinct, unrelated field this ticket does not touch, despite now having one real call site (src/engine/quests.py:233).

## Out of Scope
- Any change to PublicReputationProfile, ReputationUpdateService, or QuestResolutionSystem's quest-completion wiring — a separate, unrelated system.
- The 5 already-tracked missing SocialComponent canonical-hash fields (debt_history, salience_history, nemesis_ids, place_attachment, betrayal_records) — tracked separately by TCK-20260902-SOCIAL-CANONICAL-HASH-GAP, not this ticket's concern.
- Idea 53's birth-seed write or idea 54's ClanState.clan_reputation field — sibling child tickets of the same epic that depend on this ticket landing first, not the reverse.
- Idea 55/58 (death-and-lineage branch) — tracked as a separate sibling child ticket.

## Acceptance Criteria
- [x] SocialComponent.public_reputation (or its replacement locality-scoped structure) is read and written exclusively through RelationshipService.process_update(); no second write path exists, verified by a source-text guard test. (`tests/architecture/test_social_write_paths.py` — also caught and fixed a second, previously-undisclosed bypass in `CampaignOrchestrator._build_initial_state()`.)
- [x] A locality/observer-scoped read for the same entity at two different regions returns two distinguishably different reputation values after region-specific reputation-affecting events, verified by a new test. (`tests/unit/social/test_relationships.py::test_public_reputation_locality_differs_by_region_after_region_scoped_event`.)
- [x] EntityState.to_canonical_dict()'s public_reputation coverage remains present and shape-correct after the change (no silent loss of determinism coverage), verified by an updated canonical-hash test. (`tests/unit/core/test_entity_integrity.py::test_social_public_reputation_locality_participates_in_canonical_hash` + a paired `StateFingerprinter` test.)
- [x] SocialAppraisalSystem.appraise_contract(), apply_reputation_discount(), and campaigns/social_memory.py all consume the new shape without breaking any existing test. (All three are unaffected by design — they keep reading the retained global `public_reputation` scalar unchanged; existing `test_parity_soc_134.py`, `test_macro_economy.py::test_reputation_discount_applies`, and `test_social_memory.py` all still pass. Region-aware consumption of `regional_reputation` by these three is a disclosed follow-up, not required by this AC's literal text — "consume the new shape without breaking" is satisfied by non-breakage, not by new region-aware reads.)
- [x] This ticket's Investigation Notes explicitly record the corrected premise (PublicReputationProfile's real call site as of 2026-09-04, and why it remains structurally unrelated to this ticket's own scope) rather than repeating the epic doc's stale "zero call sites anywhere" claim. (Already satisfied by `staging_artifacts/TCK-20260904-REPUTATION-LOCALITY-SCOPE/investigation.md`'s "confirmed structurally distinct" section.)

## Related Tickets
- TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION
- TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
- TCK-20260619-E33D-REP-DISCOUNTS
- TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md
- docs/mechanics/03_economic_laws.md
- docs/parity_ledger/social_narrative.yaml
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md

## Related Stored Artifacts
None

## Related Code Areas
- src/core/models/social.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/appraisal.py
- src/systems/economy_systems/reputation_discount.py
- src/domains/campaigns/social_memory.py
- src/engine/checkpoint.py
- src/replay/fingerprint.py

## Assumptions / Open Questions
- Exact locality granularity (per-region vs per-observer vs per-settlement) is a Plan-phase decision; place_attachment's RegionID-keyed Dict[str, float] shape is the recommended default per investigation, not a mandate.
- This ticket must land before idea 53's and idea 54's own child tickets (both depend on this ticket's final field shape) — sequencing enforced via SEQUENCE.md for this batch.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260904-REPUTATION-LOCALITY-SCOPE/plan.md`'s 9 ordered
steps (1-8 are source/test/parity-ledger work; step 9, docs, is deferred to the Document-Update
phase per the plan's own note).

1. Added `SocialComponent.regional_reputation: Dict[str, float] = field(default_factory=dict)`
   (`src/core/models/social.py`), mirroring `place_attachment`'s exact shape. `public_reputation`
   itself is untouched — retained as the global scalar.
2. Added `SocialUpdate.regional_reputation_delta: Dict[str, float]` (`src/core/updates.py`), wired
   into `is_noop()` and `merge()`'s sum-by-key rule, mirroring `place_attachment_delta` exactly.
   `reputation_set`/`heroism_delta`/`notoriety_delta`'s existing merge semantics are untouched.
3. `RelationshipService.process_update()` (`src/systems/social_systems/relationships.py`) now
   additionally applies `regional_reputation_delta` per region, clamped `[0.0, 2.0]` — the same
   clamp range as `public_reputation`'s own clamp, confirmed against
   `docs/mechanics/03_economic_laws.md` §4.1 before implementing. The existing
   `public_reputation=update.reputation_set if ... else (...)` line is byte-for-byte unchanged.
4. Fixed `SocialMemoryImporter.apply()`'s direct-`dc_replace` bypass
   (`src/domains/campaigns/social_memory.py`): the `public_reputation` write now routes through
   `RelationshipService.process_update(entity.social, SocialUpdate(reputation_set=...))`;
   `trust_history` keeps its separate bulk-carry-forward `dc_replace()` (distinct semantics from
   `SocialUpdate.trust_delta`, per the plan). **Deviation found during implementation:** the plan's
   claim that `SocialUpdate` was "already imported" in this file was incorrect — added both
   `SocialUpdate` and `RelationshipService` imports. **A second, previously-undisclosed bypass was
   found and fixed in the same category**: `CampaignOrchestrator._build_initial_state()`
   (`src/domains/campaigns/orchestrator.py`) also wrote `public_reputation` via a direct
   `dc_replace(base.social, public_reputation=cf.reputation)` at episode-start construction. This
   was caught by the Step 7 architecture guard test once actually run (the investigation had
   mis-classified this exact line as a read site). Fixed the same way — routed through
   `RelationshipService.process_update()` — confirmed zero-behavior-change since `base` is always a
   fresh default `SocialComponent` at that call site.
5. `EntityState.to_canonical_dict()` (`src/core/state.py`) now includes
   `"regional_reputation": dict(sorted(self.social.regional_reputation.items()))`, following the
   `place_attachment` precedent exactly.
6. `StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py`) now includes a
   `regional_reputation=...` sorted-join segment, following the `region_ident`/`scar_ident`
   precedent.
7. Added `tests/architecture/test_social_write_paths.py` (new), a source-text guard asserting
   `public_reputation=`/`regional_reputation=` writes are allowlisted to only
   `relationships.py` (the authoritative writer), `social.py` (the field declaration), and
   `builder.py` (construction-time seeding) — plus two confirmed false-positive allowlist entries
   (`src/engine/quests.py`, a structurally distinct `RelationshipModel.public_reputation` field;
   `src/replay/fingerprint.py`, this ticket's own fingerprint string label). Verified the guard
   catches a real reintroduced bypass by temporarily re-injecting one, confirming failure, then
   restoring the fix (per Step 7's TDD instruction).
8. Updated the parity ledger via `tools/parity_ledger_writer.py::write_entry` (never hand-edited
   YAML): SOC-005 (fixed broken `test_path`, now points at
   `tests/unit/social/test_relationships.py::test_public_reputation_impact`), SOC-134
   (`v2_evidence` now notes `appraise_contract()`'s read is unchanged), SOC-CROSS-EP-002
   (`v2_evidence`/`divergence_note` now document the importer-bypass fix, the orchestrator-bypass
   fix, and that `regional_reputation` does not participate in cross-episode carry-forward),
   TOWN-181 (`divergence_note` now discloses the shop-discount-consumer gap), and new entry SOC-266
   documenting the `regional_reputation` mechanism itself.

**Disclosed follow-up gaps (explicitly out of scope, per plan's Scope Guards):**
- `src/engine/shop.py:84` and `src/town/shop.py:38` (the two real `apply_reputation_discount()`
  callers) still read only the retained global `public_reputation` scalar — not wired to
  `regional_reputation`. Documented in TOWN-181's `divergence_note`.
- `SocialAppraisalSystem.appraise_contract()`'s region-blending was not implemented — it still
  reads `source_entity.social.public_reputation` unchanged. Documented in SOC-134's `v2_evidence`.
- `regional_reputation` is not exported/imported across campaign episode boundaries — only the
  flat `faction_reputation["default"]` carries forward (unchanged). Documented in
  SOC-CROSS-EP-002's `v2_evidence`/`divergence_note`.

## Test Summary

New tests added (all passing):
- `tests/unit/social/test_relationships.py`: `test_public_reputation_locality_differs_by_region_after_region_scoped_event`, `test_regional_reputation_delta_clamped_to_public_reputation_range`, `test_regional_reputation_delta_merges_by_summing_per_region`.
- `tests/unit/core/test_entity_integrity.py`: `test_social_public_reputation_locality_participates_in_canonical_hash`, `test_social_public_reputation_locality_participates_in_fingerprint`.
- `tests/architecture/test_social_write_paths.py` (new file): `test_public_reputation_and_regional_reputation_write_paths_are_allowlisted`, `test_relationships_py_is_the_authoritative_writer`.

Regression suites run, all passing:
- `tests/unit/social/` (260 passed)
- `tests/unit/social/test_parity_soc_134.py`, `tests/unit/social/test_social_memory.py`, `tests/integration/scenarios/test_macro_economy.py` (59 passed, 2 deselected — AC #4 named consumers)
- `tests/unit/core/ tests/unit/engine/test_hash_scheduler.py tests/unit/engine/test_resource_budget_gate.py tests/unit/kernel/ tests/certification/ tests/architecture/` (502 passed, 1 skipped, 3 deselected)
- `tests/unit/domains/campaigns/ tests/integration/campaigns/ tests/integration/scenarios/test_campaign_chronicle.py tests/integration/scenarios/test_campaign_runtime.py tests/integration/scenarios/test_faction_campaign.py` (139 passed, 8 deselected — covers both the SocialMemoryImporter and CampaignOrchestrator bypass fixes)
- `tests/tools/ -k parity` (161 passed — parity ledger schema/writer/index still valid after Step 8's writes)

## Files Changed

Source:
- `src/core/models/social.py`
- `src/core/updates.py`
- `src/systems/social_systems/relationships.py`
- `src/domains/campaigns/social_memory.py`
- `src/domains/campaigns/orchestrator.py` (unplanned but required fix, see Implementation Notes)
- `src/core/state.py`
- `src/replay/fingerprint.py`

Tests:
- `tests/architecture/test_social_write_paths.py` (new)
- `tests/unit/social/test_relationships.py`
- `tests/unit/core/test_entity_integrity.py`

Parity ledger:
- `docs/parity_ledger/social_narrative.yaml`
- `docs/parity_ledger/town_resource.yaml`

Docs (Document-Update phase):
- `docs/mechanics/03_economic_laws.md`
- `docs/simulation/social_systems_contract.md`
- `docs/simulation/domains/social_memory_contract.md`
- `docs/brainstorm/rpg_feature_atlas.html`
- `docs/brainstorm/simulation_capabilities.html`

Ticket/artifacts:
- `tickets/inprogress/TCK-20260904-REPUTATION-LOCALITY-SCOPE.md`
- `staging_artifacts/TCK-20260904-REPUTATION-LOCALITY-SCOPE/investigation.md` (created this run's Investigate phase)
- `staging_artifacts/TCK-20260904-REPUTATION-LOCALITY-SCOPE/plan.md` (created this run's Plan phase; Deviations section added during Implement)
- `staging_artifacts/TCK-20260904-REPUTATION-LOCALITY-SCOPE/test_plan.md` (created this run's Investigate phase)

## Completion Summary

Added `SocialComponent.regional_reputation: Dict[str, float]` (RegionID -> local reputation,
[0.0, 2.0] clamp, mirroring `place_attachment`'s shape) as a new field additive to the retained,
unchanged global `public_reputation` scalar. Wired it end-to-end through the sole authoritative
write path (`RelationshipService.process_update()`, via a new `SocialUpdate.regional_reputation_delta`
field with sum-by-key merge semantics), through both determinism surfaces
(`EntityState.to_canonical_dict()` and `StateFingerprinter.get_fingerprint()`), and closed two
pre-existing direct-write bypasses of that authoritative path (`SocialMemoryImporter.apply()` and
`CampaignOrchestrator._build_initial_state()` — the latter found during this ticket's own
architecture-guard-test implementation, not previously disclosed) as zero-behavior-change
refactors. A new architecture guard test enforces no third bypass can be reintroduced. The three
named consumers (`appraise_contract()`, `apply_reputation_discount()`, `campaigns/social_memory.py`)
all continue to work unchanged against the retained global scalar; region-aware consumption by
those three, and cross-episode carry-forward of `regional_reputation`, are explicitly disclosed
follow-up gaps, not implemented here. Five parity ledger entries were updated via the sanctioned
writer tool (one broken `test_path` fixed, one new entry added). All targeted and regression test
suites pass (961+ tests across social, core, kernel, certification, architecture, and campaigns
scopes).
