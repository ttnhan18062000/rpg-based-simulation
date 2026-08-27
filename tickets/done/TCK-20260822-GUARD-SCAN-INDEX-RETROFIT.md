---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260822-GUARD-SCAN-INDEX-RETROFIT
phase: done
date: 2026-08-22
tags: [faction, grand-strategy, performance]
---

# TCK-20260822-GUARD-SCAN-INDEX-RETROFIT

## Title
Retrofit GUARD-entity index into MilitaryConflictPhase's per-war-pair region scan (corrected target)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Preserves the original intent that E53 shipped without a TerritorialObserver-style seam and needs an index retrofit for faction/region-scoped GUARD-entity queries running an O(N) scan per governance tick. Corrected by investigation: the concern's own title/description misattributed the target to FactionDecisionPhase / src/domains/faction/, which was confirmed to have zero entity/GUARD/border scanning. The real O(N) GUARD-entity scan is MilitaryConflictPhase._find_guard_entities_in_region (src/engine/military_conflict.py, lines 121-137), called once per WAR pair per tick for one already-selected contested_region_id -- not per-faction-per-border as originally framed. This ticket retrofits the corrected, actual call site.

## Scope
- Replace MilitaryConflictPhase._find_guard_entities_in_region(state, region_id)'s full O(N) entity scan with a lookup against the semantic entity index's (TCK-20260822-SEMANTIC-ENTITY-INDEX) role+region dimensions.
- Add net-new test coverage (currently zero) for the >=3-GUARD reinforcement branch (+0.02 service_availability / -0.02 siege_progress) and the squad-commitment branch (GroupRecord capped at 5, FACTION_SQUAD role) before/alongside the retrofit, since neither is exercised by any existing test.
- Correct docs/parity_ledger/faction.yaml FAC-008's v2_evidence/test_path to cite a test that actually covers these branches -- the existing citation (test_siege_model.py) does not.

## Out of Scope
- src/domains/faction/diplomatic_state_machine.py -- investigation found its territorial check is O(faction-pairs), not an O(N) entity scan, and it is not a retrofit target despite being named in the original proposal.
- src/engine/faction_decision.py -- confirmed to have zero entity/GUARD/border scanning (only 3 tension/territory/military-strength rules); not part of this retrofit.
- Any per-faction-per-border query pattern -- the real call site is scoped per-WAR-pair to one already-selected contested_region_id, not the broader per-faction-per-border shape the original concern assumed.

## Acceptance Criteria
- [x] Index-backed replacement for _find_guard_entities_in_region(state, region_id) returns an identical sorted List[int] of GUARD-role entity IDs to the current full-scan implementation, verified by a new test populating mixed GUARD/non-GUARD entities across regions.
- [x] New test asserts the reinforcement branch fires +0.02/-0.02 deltas when >=3 GUARD entities are present in the contested region.
- [x] New test asserts squad commitment produces a GroupRecord capped at 5 when >5 GUARD entities are present.
- [x] FAC-008's v2_evidence/test_path in docs/parity_ledger/faction.yaml is updated to cite the new/corrected test coverage.

## Related Tickets
- TCK-20260619-E53Cb-SIEGE-MODEL
- TCK-20260619-E53Ca-CONFLICT-PHASE
- TCK-20260619-E53Ab-DECISION-PHASE
- TCK-20260619-E53-FACTION-DIPLOMACY
- TCK-20260702-PLANS-IDEA-REFRESH
- TCK-20260822-SEMANTIC-ENTITY-INDEX

## Related Docs
- docs/parity_ledger/faction.yaml
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/military_conflict.py
- src/engine/faction_decision.py
- src/domains/faction/diplomatic_state_machine.py
- tests/unit/domains/faction/test_military_conflict_phase.py
- tests/unit/domains/faction/test_siege_model.py
- tests/integration/scenarios/test_faction_campaign.py
- tests/unit/domains/faction/test_faction_decision_phase.py

## Assumptions / Open Questions
- Depends on TCK-20260822-SEMANTIC-ENTITY-INDEX's index existing (or a scoped equivalent) before/alongside this retrofit.
- The corrected target (military_conflict.py) diverges from the original idea doc's wording (which named src/domains/faction/) -- flagged explicitly so future readers aren't confused by the mismatch.
- `layer: engine` chosen over a faction-specific layer since none is registered in registries/layer_registry.jsonl and the actual retrofit target (src/engine/military_conflict.py) is an engine-phase file; `faction` remains a registered tag instead.

## Implementation Notes

Implemented exactly per the APPROVED plan (Option B — local per-`execute()` hoist, not
`SemanticEntityQuery.by_region`; see plan.md's Design Decision):

- `src/engine/military_conflict.py`: added `MilitaryConflictPhase._build_guard_index_by_region(state) -> Dict[str, List[int]]`,
  a single pass over `state.entities.items()` bucketing GUARD-role entity IDs by `nav.region_id`
  (same `getattr(..., None)` defensive checks and `identity.role == EntityRole.GUARD` filter as the
  original scan), then sorting each region's list. `_find_guard_entities_in_region(state, region_id)`
  is kept in place with its original 2-argument signature and `List[int]` return type, reimplemented
  as a thin wrapper: `return MilitaryConflictPhase._build_guard_index_by_region(state).get(region_id, [])`.
  `execute()` now computes `guard_ids_by_region` once (right after the local imports, before
  `world_updates: Dict[str, WorldUpdate] = {}`), and the per-WAR-pair siege loop does a dict
  `.get(contested_region_id, [])` lookup instead of re-scanning `state.entities` per pair — bounding
  the scan to `O(N)` once per tick regardless of `war_pair_count`, matching the ticket's real goal.
  Filtering stays strictly on `identity.role == EntityRole.GUARD`; `class_id`/`spawn_tables.yaml`'s
  `WARRIOR` content fact was not made load-bearing anywhere in the new code.
- `tests/unit/domains/faction/test_siege_model.py`: added `_make_entity` and
  `_naive_find_guard_entities_in_region` (a local reference copy of the pre-retrofit scan, test-only)
  helpers, plus `_make_war_state_with_guards`, and 6 new tests: `test_guard_index_matches_naive_full_scan`
  (AC #1 — asserts exact list equality, including a zero-GUARD region and an entity constructed via
  `EntityState(id=..., kind="npc")` relying on real `default_factory` component defaults to exercise the
  defensive `getattr` branch as dead-but-safe code), `test_military_conflict_reinforcement_fires_at_three_guards`
  / `test_military_conflict_reinforcement_does_not_fire_below_threshold` (AC #2), and
  `test_military_conflict_squad_commitment_capped_at_five` / `..._no_truncation_at_five` /
  `..._empty_when_no_guards` (AC #3, using non-sequential entity IDs to catch a sort-order regression).
- `docs/parity_ledger/faction.yaml`: FAC-008's `v2_evidence` extended (surgical text edit, not a full
  YAML round-trip — confirmed via `git diff --stat` showing only 17 insertions/1 deletion, no
  reformatting) to describe the `_build_guard_index_by_region` hoist and cite why
  `SemanticEntityQuery.by_region` was not used; `test_path` corrected from the single (non-covering)
  `test_siege_model.py` file reference to the 6 new test node IDs by name. `status`, `priority`, and
  `text` left unchanged — no semantic divergence (AC #1 requires identical output).
- `docs/engine/performance_contract.md` §8.2: added a paragraph (same pattern as the existing
  PAID-INFO paragraph) after the PAID-INFO paragraph and before "**Lifecycle**", stating what was
  retrofitted and why `by_region` was not wired in despite being the correct dimension for this call
  site (index has no partial-dimension build path; would be the first production caller paying a ~5x
  rebuild cost with no same-tick amortization, since every shipped scenario has exactly one WAR pair
  per tick).

**Deviation from plan.md (documented in plan.md's Deviations section)**: the orchestrator-run Parity
cross-reference gate found `src/engine/military_conflict.py` mapped (via an unrelated pre-existing
citation, `SOC-FAC-007`) to `docs/parity_ledger/social_narrative.yaml`, one of the 8 canonical ledger
files — but `faction.yaml` (where `FAC-008`, this ticket's real and complete parity record, lives)
is not part of that canonical set. Added a new, minimal, genuinely true cross-reference entry
(`SOC-245`) to `social_narrative.yaml` pointing to `FAC-008` as the authoritative record, rather
than duplicating FAC-008's description there. This is a real structural gap in the parity-ledger
tooling (`faction.yaml` predates the canonical-8 convention), not a documentation gap in this
ticket's own work — flagged for a separate follow-up hotfix ticket rather than restructured here.
All 6 of the plan's own Steps were otherwise implemented exactly as specified.

## Test Summary

Ran (all pass):
- `tests/unit/domains/faction/test_siege_model.py` — 22 tests (16 pre-existing + 6 new), all pass.
- `tests/unit/domains/faction/test_military_conflict_phase.py` — 6 pre-existing tests, unmodified, all pass.
- `tests/unit/domains/faction/test_war_exhaustion.py`, `test_territory_transfer.py`, `test_siege_ledger.py` —
  all pre-existing, unmodified, all pass (confirms the hoist did not disturb adjacent
  FAC-009/010/011 behaviors sharing the same source file).
- Full `tests/unit/domains/faction/` + `tests/integration/scenarios/test_faction_campaign.py` — 126 passed.
- `tests/tools/test_parity_ledger_schema.py` — 1 passed (confirms the surgical `faction.yaml` edit
  still validates against `docs/parity_ledger/schema.json`).

## Files Changed
- src/engine/military_conflict.py
- tests/unit/domains/faction/test_siege_model.py
- docs/parity_ledger/faction.yaml
- docs/parity_ledger/social_narrative.yaml — new SOC-245 cross-reference entry to FAC-008 (see Deviations)
- docs/engine/performance_contract.md
- staging_artifacts/TCK-20260822-GUARD-SCAN-INDEX-RETROFIT/plan.md — added Deviations section
- tickets/inprogress/TCK-20260822-GUARD-SCAN-INDEX-RETROFIT.md

## Completion Summary

Replaced `MilitaryConflictPhase._find_guard_entities_in_region`'s per-WAR-pair O(N) full-entity scan
with a single-pass, per-`execute()` hoisted index (`_build_guard_index_by_region`), bounding the
GUARD-entity scan to O(N) once per tick instead of O(N × war_pair_count), while keeping the original
method's signature/return type intact as a thin wrapper. Added 6 tests closing the previously-zero
coverage on the ≥3-GUARD reinforcement offset and the squad-commitment cap-at-5 branches, plus a
naive-scan parity test proving byte-identical output (AC #1-#3). Corrected FAC-008's parity-ledger
`v2_evidence`/`test_path` to cite the new tests and the actual shipped mechanism, and updated
`docs/engine/performance_contract.md` §8.2 to document why the hoist (not `SemanticEntityQuery.by_region`)
was chosen (AC #4). No production-observable behavior changed — output is identical to the pre-change
scan for every input. Also added a new `SOC-245` cross-reference entry in `social_narrative.yaml`
pointing to `FAC-008` as the authoritative record, to satisfy the parity cross-reference gate's
canonical-8-file scan honestly (see Implementation Notes / Deviations) — flagged a real, separate
structural gap (`faction.yaml` not being part of the canonical ledger set) for a follow-up hotfix
ticket.
