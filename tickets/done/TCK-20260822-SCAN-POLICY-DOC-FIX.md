---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260822-SCAN-POLICY-DOC-FIX
phase: done
date: 2026-08-22
tags: [documentation]
---

# TCK-20260822-SCAN-POLICY-DOC-FIX

## Title
Correct two stale performance claims in the semantic-index reconciliation doc

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Preserves the original intent that performance_contract.md §7's scan_policy+DirtySet mitigation must be reconciled with any semantic-index proposal rather than treating the index as the only mitigation in play. Corrected by investigation: that reconciliation is already committed in docs/plans/idea_semantic_entity_index.md (same-session commit 4fc13ac4, the staleness-fix pass). The real remaining scope is two narrower factual corrections still needed in that doc: (1) scan_policy/DirtySet do not actually gate paid_information.py's live hotspot -- that call site ignores both mechanisms entirely; and (2) MOVEMENT_STRESS_100_ACTORS is cited as a benchmark-scale scenario but has zero hits in src/perf/scenarios.py or tests/ -- it is not a real wired scenario.

## Scope
- Correct docs/plans/idea_semantic_entity_index.md to state explicitly that scan_policy/DirtySet do not currently gate paid_information.py's hotspot.
- Correct or remove the MOVEMENT_STRESS_100_ACTORS reference in that doc, since it is not a wired scenario anywhere in src/perf/scenarios.py or tests/.
- Note (documentation-only) the unrelated pre-existing bug found during investigation: CacheInvalidationPolicy.invalidated_indexes() references 'region_index' with a passing test, but WorldIndexes has no region_index field/method -- flag as a known follow-up, do not fix it here.

## Out of Scope
- Building the index itself (TCK-20260822-SEMANTIC-ENTITY-INDEX) or retrofitting any call site (TCK-20260822-PAID-INFO-INDEX-RETROFIT, TCK-20260822-GUARD-SCAN-INDEX-RETROFIT).
- Fixing the CacheInvalidationPolicy 'region_index' dead-code/phantom-field bug -- flagged for awareness only, tracked as a separate future concern, not fixed in this ticket.
- Any code changes -- this ticket is doc-only.

## Acceptance Criteria
- [x] docs/plans/idea_semantic_entity_index.md's Status review note is verified accurate: 0 repo-wide hits for ProviderLocator/TerritorialObserver, and WorldIndexes has no role/faction/region dimension, confirming scan_policy/DirtySet reduce but don't eliminate the semantic-index gap.
- [x] Doc explicitly states scan_policy/DirtySet do NOT currently gate paid_information.py's hotspot -- today's mitigation is engine-wide precedent, not an applied fix at that call site.
- [x] MOVEMENT_STRESS_100_ACTORS benchmark-scale claim is corrected in the doc to note it is not a real wired scenario (zero hits in src/perf/scenarios.py or tests/).
- [x] The region_index CacheInvalidationPolicy/WorldIndexes mismatch is recorded as a known follow-up note (doc or ticket), not silently dropped and not fixed in this pass.

## Related Tickets
- TCK-20260517-WORLD-INDEX-SERVICE
- TCK-20260518-CACHE-INVALIDATION-POLICY
- TCK-20260517-STATIC-DIRTYSET-GUARD
- TCK-20260702-PLANS-IDEA-REFRESH

## Related Docs
- docs/plans/idea_semantic_entity_index.md
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/idea_semantic_entity_index.md
- docs/engine/performance_contract.md
- src/core/dirty.py
- src/engine/phase_governor.py
- src/engine/policy.py
- src/engine/candidate_selector.py
- src/engine/world_index.py
- src/engine/spatial_query.py
- src/engine/pipeline_phases/paid_information.py
- src/perf/scenarios.py

## Assumptions / Open Questions
- Assumes the doc-level reconciliation committed in 4fc13ac4 remains the current state at implementation time (not re-reverted by concurrent work).
- The region_index dead-code bug is explicitly deferred, not silently dropped -- should be captured as a follow-up note per investigation's risk flag.

## Implementation Notes

Independent verification (all three ticket claims confirmed TRUE, no discrepancy with ticket text):

1. `src/engine/pipeline_phases/paid_information.py` — read in full and grepped for
   `scan_policy|DirtySet|dirty_set` (case-insensitive): zero hits. The nested
   `for entity in sorted(state.entities.values()...)` / `for pid in sorted(providers.keys())` scan (lines
   92/112) runs unconditionally every tick with no `scan_policy`/`DirtySet` gating whatsoever. Ticket claim
   confirmed accurate.
2. `MOVEMENT_STRESS_100_ACTORS` — grepped `src/perf/scenarios.py` and all of `tests/`: zero hits in both.
   `SCENARIO_BUILDERS` in `src/perf/scenarios.py` registers only `idle`, `movement`, `resource`, `combat`,
   `strategic`, `mixed`, `metropolis`, each parameterized by `entity_count` (no fixed 100-actor preset). The
   name exists only in doc prose (`docs/engine/performance_contract.md`,
   `docs/performance/perf_baseline_policy.md`, and this doc's own prior revision) — never as code. Ticket
   claim confirmed accurate.
3. `CacheInvalidationPolicy.invalidated_indexes()` (`src/engine/world_index.py`) adds `"region_index"` to
   its return set when `dirty.region_ids` is populated, and `should_invalidate("regions", ...)` checks for
   that same key. `WorldIndexes` (same file) has fields for resource/building/entity/ground-item/corpse
   indexes only — no `region_index` field — and `WorldIndexService.get_indexes()` never calls
   `should_invalidate("regions", ...)`. The passing unit test
   (`tests/unit/domains/optimization/test_cache_invalidation_policy.py::test_region_dirty_invalidates_region_index`)
   only asserts `"region_index" in invalidated`, so it passes despite the field never existing. Ticket claim
   confirmed accurate — recorded as a known follow-up note in the doc, not fixed here (out of scope).

Also independently re-verified the pre-existing Status-review claims already in the doc (not part of this
ticket's corrections, but part of AC #1): zero repo-wide hits for `ProviderLocator`/`TerritorialObserver`
in `src/` or `tests/` — matches the doc's existing text, no change needed there.

Edited only the "Status review (2026-08-22)" callout block in `docs/plans/idea_semantic_entity_index.md`
to (a) state explicitly that `scan_policy`/`DirtySet` do not gate `paid_information.py`'s hotspot, (b)
correct the `MOVEMENT_STRESS_100_ACTORS` claim to say it is not a real wired scenario and list the actual
`SCENARIO_BUILDERS` names instead, and (c) add a new "Known follow-up, not fixed here" paragraph
documenting the `CacheInvalidationPolicy`/`WorldIndexes` `region_index` mismatch. No other sections of the
doc were touched. No `src/` files were touched.

Ran `python3 tools/validate_frontmatter.py docs/plans/idea_semantic_entity_index.md` as the applicable
lint for this doc. It reports one pre-existing violation (`status: invalid value 'idea'`) that predates
this session's edit (confirmed via `git show HEAD:...` — the `status: idea` frontmatter value was already
present before any change in this ticket) and is unrelated to the body-text corrections made here; left
unfixed as out of scope for this doc-only correction ticket.

## Test Summary
Doc-only change; no code tests apply. Ran `python3 tools/validate_frontmatter.py
docs/plans/idea_semantic_entity_index.md` as the structural check for docs/plans/ files — it surfaces one
pre-existing frontmatter violation (`status: idea` is not in the allowed enum) that predates this ticket's
edit and is out of scope to fix here.

## Files Changed
- docs/plans/idea_semantic_entity_index.md (body text corrections to the "Status review" callout only)
- docs/engine/performance_contract.md (§3.1 `Scenario` example corrected: `MOVEMENT_STRESS_100_ACTORS` replaced with the real `movement` scenario builder from `src/perf/scenarios.py`, with a dated correction note)
- docs/performance/perf_baseline_policy.md (§3.1 correction note added documenting that `MOVEMENT_STRESS_100_ACTORS`/`COMBAT_ARENA_STRESS` are not real wired scenario identifiers, cross-referencing the real registered names in `src/perf/scenarios.py` and `src/certification/scenarios.py`)
- tickets/inprogress/TCK-20260822-SCAN-POLICY-DOC-FIX.md (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary
Independently verified all three factual claims in the ticket and found them all accurate: (1)
`paid_information.py`'s hotspot has zero `scan_policy`/`DirtySet` references and is ungated, (2)
`MOVEMENT_STRESS_100_ACTORS` is not a real wired scenario (zero hits in `src/perf/scenarios.py` or
`tests/`), and (3) `CacheInvalidationPolicy.invalidated_indexes()` references a `region_index` that
`WorldIndexes` doesn't have, with a passing test that only checks set membership. Corrected
`docs/plans/idea_semantic_entity_index.md`'s Status-review callout to state (1) and (2) explicitly with
supporting evidence, and added a new "Known follow-up, not fixed here" paragraph documenting (3) as a
future ticket candidate. No code was changed; no behavior changed.
