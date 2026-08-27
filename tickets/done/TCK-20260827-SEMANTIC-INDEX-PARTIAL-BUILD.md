---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD
phase: done
date: 2026-08-27
tags: [engine, performance, determinism]
---

# TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD

## Title
Close SemanticEntityIndexService's partial-single-dimension build gap (cross-tick carry-forward + selective dimension build)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`SemanticEntityIndexService.get_indexes()` (`src/engine/semantic_entity_index.py`, shipped by
TCK-20260822-SEMANTIC-ENTITY-INDEX) has no genuine partial-single-dimension build path. Confirmed
root cause (two compounding gaps, not one):

1. **Cross-tick carry-forward is missing.** Unlike `WorldIndexService`
   (`src/engine/world_index.py`), whose `world_indexes` field IS carried forward via
   `world_indexes=getattr(prior_state, "world_indexes", None)` in
   `ApplyPath.apply_generation` (`src/engine/apply.py:406`), `semantic_entity_indexes` is not
   carried forward there. This is already documented as a "Known limitation" in
   `docs/engine/performance_contract.md` §8.2 and recorded as Deviation #3 in
   TCK-20260822-SEMANTIC-ENTITY-INDEX's Implementation Notes: "Production ticks therefore always
   full-rebuild on the first post-tick query rather than reusing the prior tick's per-dimension
   cache." Because of this, `existing` is `None` on the *first* query of every single tick in
   production (not just tick 0), which defeats `get_indexes()`'s per-dimension
   reuse-or-rebuild ternaries entirely -- they all evaluate to "rebuild" every tick regardless of
   `CacheInvalidationPolicy.should_invalidate(...)`'s actual per-domain answer.
2. **Even with carry-forward fixed, there is still no way to ask for only one dimension.**
   `get_indexes()` always computes (reuse-or-rebuild) all 5 dimensions on every call. If a caller
   wants only `by_region` this call, but the `identity`/`needs`/`knowledge` domains happen to be
   invalidated this tick, `get_indexes()` still eagerly pays the full `_build_*` cost for those
   three unwanted dimensions. `WorldIndexService` has the architecturally identical shape (same
   eager-all-N-dimensions pattern) but does not visibly suffer from this today because (a) its
   carry-forward already works, and (b) its existing call sites collectively touch most of its 5
   dimensions across a tick anyway.

This was confirmed as the root cause blocking both TCK-20260822-PAID-INFO-INDEX-RETROFIT and
TCK-20260822-GUARD-SCAN-INDEX-RETROFIT from wiring their call sites into the index -- each would
have been the index's first-ever production caller, needing only one dimension, with zero
same-tick amortization (both call sites query once per tick). Both tickets shipped working local
hoists instead, leaving `SemanticEntityQuery` with zero production callers. An architecture-reviewer
flagged this explicitly as a non-blocking process observation on
TCK-20260822-GUARD-SCAN-INDEX-RETROFIT's review, recommending a follow-up ticket "before drafting
further per-call-site retrofit tickets against this index."

## Scope
- Wire `AuthoritativeState.semantic_entity_indexes` cross-tick carry-forward into
  `ApplyPath.apply_generation`'s new-state construction (`src/engine/apply.py`), mirroring the
  existing `world_indexes=getattr(prior_state, "world_indexes", None)` line -- closing the
  documented "Known limitation" in `docs/engine/performance_contract.md` §8.2 / Deviation #3.
- Investigate and design a genuine per-dimension selective build path for
  `SemanticEntityIndexService.get_indexes()` (and/or the `SemanticEntityQuery` call surface) so
  that a caller requesting a single dimension does not force an eager rebuild of another
  invalidated-but-unrequested dimension in the same call. Decide during planning whether this
  requires an `Optional`-per-dimension-field variant of the frozen `SemanticEntityIndexes`
  dataclass (allowing a "partial" object to exist with some dimensions unbuilt), independently
  tick-stamped per-dimension attributes on `AuthoritativeState`, or a different mechanism that
  keeps the public dataclass shape unchanged -- document the decision and rationale explicitly
  before implementation, the way TCK-20260822-SEMANTIC-ENTITY-INDEX documented its lifecycle
  choice.
- As part of the same investigation, determine whether `WorldIndexService`
  (`src/engine/world_index.py`) has the identical eager-all-N-dimensions limitation and, if so,
  whether to fix it too for architectural consistency in this ticket, or explicitly document why
  its usage pattern makes that unnecessary for now.
- Update `docs/engine/performance_contract.md` §8.2's "Known limitation" callout to reflect the
  new behavior (or replace it with a narrower, accurate limitation statement if full
  dimension-selectivity is intentionally deferred further).
- Update parity ledger entry `INFRA-395` (`docs/parity_ledger/infrastructure.yaml`) `v2_evidence`
  to describe the new carry-forward/selective-build mechanism and cite the new test coverage.

## Out of Scope
- Retrofitting any concrete call site (`paid_information.py`'s provider lookup,
  `military_conflict.py`'s guard scan) into `SemanticEntityQuery` -- those already shipped working
  local-hoist alternatives (TCK-20260822-PAID-INFO-INDEX-RETROFIT,
  TCK-20260822-GUARD-SCAN-INDEX-RETROFIT). Whether to migrate them onto this index once fixed is a
  separate future decision, not part of this ticket.
- Inventing a dedicated `DirtySet` tag for `information_providers` mutations to stop the
  `knowledge` domain's always-invalidate behavior -- orthogonal to the partial-build gap, already
  a separately documented, deliberate limitation.
- Restructuring Kernel phase boundaries or moving to an eager Persistence-phase write lifecycle --
  the lazy, pull-based `CacheInvalidationPolicy`-driven lifecycle (Recommendation 1 from
  TCK-20260822-SEMANTIC-ENTITY-INDEX) is not reopened here; this ticket only fixes carry-forward
  and selective-dimension building within that existing lifecycle.
- Rewriting `WorldIndexService`'s implementation unless investigation concludes it shares the
  identical limitation and needs the identical fix -- do not speculatively change it otherwise.

## Acceptance Criteria
- [x] `semantic_entity_indexes` is carried forward from `prior_state` into the new state object in
  `ApplyPath.apply_generation`, mirroring `world_indexes`'s carry-forward -- verified by a new test
  asserting a second-tick `get_indexes()` call with no invalidated dimensions reuses the prior
  tick's cached per-dimension values (identity/equality, not a rebuild) instead of rebuilding.
- [x] A test demonstrates that when only one invalidation domain is dirty on a given tick (e.g.
  only `identity`), the other 4 dimensions are NOT rebuilt across that tick's queries -- via
  rebuild-call spies on the unaffected `_build_*` methods -- confirming the cross-tick "Known
  limitation" is closed.
- [x] A caller requesting a single dimension through `SemanticEntityQuery` (e.g. `by_region`) does
  not trigger a rebuild of a dimension that is both invalidated AND not requested in that call --
  verified by a new test with rebuild-call spies proving the unrequested-but-invalidated
  dimension's `_build_*` method is not invoked. Implementation shape (dataclass change vs.
  internal control-flow change) follows whatever investigation/planning documents as the decision.
- [x] `docs/engine/performance_contract.md` §8.2's "Known limitation" callout is updated to reflect
  the new carried-forward, dimension-selective behavior (or replaced with a new, accurate,
  narrower limitation statement if full selectivity is intentionally deferred further).
- [x] `INFRA-395` in `docs/parity_ledger/infrastructure.yaml` has `v2_evidence` updated to cite the
  new mechanism and its test coverage.
- [x] All existing tests in `tests/unit/domains/optimization/test_semantic_entity_index.py` and
  `tests/unit/domains/optimization/test_cache_invalidation_policy.py` continue to pass unmodified
  (behavior preservation for already-tested paths: AC #1-4 of TCK-20260822-SEMANTIC-ENTITY-INDEX
  are not regressed).

## Related Tickets
- TCK-20260822-SEMANTIC-ENTITY-INDEX
- TCK-20260822-PAID-INFO-INDEX-RETROFIT
- TCK-20260822-GUARD-SCAN-INDEX-RETROFIT
- TCK-20260517-WORLD-INDEX-SERVICE

## Related Docs
- docs/engine/performance_contract.md (§8.1 WorldIndexService, §8.2 Semantic Entity Indexes)
- docs/parity_ledger/infrastructure.yaml (INFRA-395)
- docs/plans/idea_semantic_entity_index.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260822-SEMANTIC-ENTITY-INDEX/
- stored_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/
- stored_artifacts/TCK-20260822-GUARD-SCAN-INDEX-RETROFIT/

## Related Code Areas
- src/engine/semantic_entity_index.py
- src/engine/apply.py
- src/engine/world_index.py
- src/core/state.py
- tests/unit/domains/optimization/test_semantic_entity_index.py
- tests/unit/domains/optimization/test_cache_invalidation_policy.py

## Assumptions / Open Questions
- Assumes the lazy, pull-based `CacheInvalidationPolicy`-driven lifecycle (not eager
  Persistence-phase write) stays the chosen pattern -- already decided/documented by
  TCK-20260822-SEMANTIC-ENTITY-INDEX and not reopened here.
- Open question (must be resolved in investigation/planning, not assumed): does true per-dimension
  selective building require making `SemanticEntityIndexes`' fields `Optional` (so a "partial"
  object can exist with some dimensions unbuilt), or can it be achieved by restructuring
  `get_indexes()`'s internal control flow (e.g. a `dimensions: Optional[Set[str]]` parameter that
  skips unrequested-and-unneeded rebuild work) without changing the public dataclass shape?
- Open question: does `WorldIndexService` share the identical eager-all-N-dimensions limitation
  (distinct from the cross-tick issue, which it does not have)? Default assumption is fixing
  `SemanticEntityIndexService` only and documenting `WorldIndexService`'s status as part of this
  ticket's investigation, unless a materially cheap consistent fix is found.
- Priority is P2 because zero production callers currently depend on this fix -- both existing
  retrofit tickets (PAID-INFO, GUARD-SCAN) shipped working local-hoist alternatives that do not
  route through `SemanticEntityQuery`. If investigation surfaces a near-term planned caller,
  priority should be revisited before implementation proceeds.
- `layer: engine` chosen (matching TCK-20260822-SEMANTIC-ENTITY-INDEX's own layer choice) since the
  affected code (`src/engine/semantic_entity_index.py`, `src/engine/apply.py`,
  `src/engine/world_index.py`) is squarely in the engine/tick-pipeline layer; no narrower
  registered layer fits better.

## Implementation Notes

Implemented all 5 steps of the approved (round-3) plan exactly as specified, with one necessary
deviation discovered during implementation (see below).

**Step 1 (`src/engine/apply.py`)**: added
`semantic_entity_indexes=getattr(prior_state, "semantic_entity_indexes", None),` immediately after
the existing `world_indexes=...` line in `ApplyPath.apply_generation`'s `AuthoritativeState(...)`
constructor call, mirroring `world_indexes` exactly.

**Step 2 (`src/engine/semantic_entity_index.py`)**: added `_DIMENSION_TO_DOMAIN` mapping and
`_ALL_DIMENSIONS` frozenset at module level; added the 6th field `resolved_dimensions:
FrozenSet[str] = field(default_factory=frozenset)` to `SemanticEntityIndexes`; added `Set`/`FrozenSet`
imports; added the `dimensions: Optional[Set[str]] = None` parameter to `get_indexes()`; removed the
same-tick fast path (`if existing is not None and existing.tick == state.tick: return existing`)
entirely; computed `already_resolved` before the 5 per-field ternaries; updated each ternary to
consult `already_resolved` first, then the "not requested" gate, then the existing
`should_invalidate` check; computed and returned `resolved_dimensions` on every construction.

**Step 3 (`src/engine/semantic_entity_index.py`)**: wired all 5 `SemanticEntityQuery` methods
(`by_role_class`, `by_region`, `by_faction`, `by_need`, `by_knowledge_domain`) to pass their own
single-dimension `dimensions={...}` set to `get_indexes()`. Public method signatures unchanged.

**Step 4 (`docs/engine/performance_contract.md`)**: rewrote §8.2's "Known limitation" paragraph into
a "Cross-tick carry-forward and per-dimension selective building" section describing the shipped
mechanism (carry-forward, `dimensions` parameter, `resolved_dimensions` bookkeeping, no same-tick
shortcut, `knowledge` domain's unchanged always-invalidate behavior); corrected the stale
"no partial-dimension build path" claim in the GUARD-SCAN paragraph; added the §8.1 note about
`WorldIndexService` sharing the identical eager-all-N shape but remaining unfixed (documentation-only,
per Out of Scope).

**Step 5 (`docs/parity_ledger/infrastructure.yaml`)**: checked `tools/parity_ledger_writer.py` --
`write_entry()` supports upsert-by-id (replaces an existing entry sharing the same `id`), which is
sufficient for an evidence-append (pass the full entry with only `v2_evidence`/`test_path` changed).
Used this sanctioned path rather than a raw `Edit` call. Appended a description of the shipped
mechanism to `INFRA-395`'s `v2_evidence` and appended the 9 new test node IDs to `test_path`.
`status`/`priority`/`text`/`divergence_note` left untouched. Verified via `tests/tools/test_parity_ledger_schema.py`
(passes) and a scripted per-entry diff against `git show HEAD:...` confirming only `INFRA-395`'s
content changed -- the large surrounding diff in the file is `write_entry()`'s whole-file YAML
re-dump reformatting already-uncommitted, unrelated entries from earlier tickets in this session
(this worktree's `HEAD` predates substantial uncommitted parity-ledger work); no other entry's
field values changed.

**Deviation from the plan (found during Step 1's Verify pass, not anticipated by the plan)**:
`tests/static/test_semantic_entity_index_no_stateupdate_write.py` failed after the Step 1 edit --
its forbidden-pattern scan flags any `semantic_entity_indexes=` line in `src/` that isn't already
on its whitelist (`self.semantic_entity_indexes`, the field declaration, or `object.__setattr__`),
and the new `apply.py` carry-forward line matched none of those. This is a false positive, not a
real architecture violation: the guard's own docstring states its purpose is to forbid a
`StateUpdate`/`.replace()`-driven write that would promote the field to authoritative state: the
`apply.py` line is neither -- it is `ApplyPath.apply_generation`'s own `AuthoritativeState(...)`
constructor passing a non-authoritative cache value through unchanged, structurally identical to
the pre-existing, unguarded `world_indexes=getattr(prior_state, "world_indexes", None)` line at the
same call site (confirmed no equivalent static guard exists for `world_indexes` at all). Fixed by
adding one narrowly-scoped whitelist condition to the guard
(`'getattr(prior_state, "semantic_entity_indexes", None)' in line`) and updating its docstring to
document the extension, rather than loosening the pattern-matching in a way that could admit a real
future violation. This is documented here and in `staging_artifacts/.../plan.md`'s new Deviations
section per project convention; it is a correction to a stale guard whitelist, not a substantive
work-around of a real finding.

## Test Summary

9 new tests added to `tests/unit/domains/optimization/test_semantic_entity_index.py` (see Files
Changed for exact names). All existing tests in the file (12) continue to pass unmodified --
21/21 pass. Full scoped pytest commands from `test_plan.md` were run:
- `tests/unit/domains/optimization/` (122 passed)
- `tests/static/test_semantic_entity_index_returns_ids_only.py`,
  `tests/static/test_semantic_entity_index_no_stateupdate_write.py`,
  `tests/static/test_no_direct_dirtyset_candidate_selection.py` (3 passed)
- `tests/unit/perf/test_phase10_cache_invalidation.py`, `tests/unit/perf/test_phase10_dirty_work_scheduler.py` (14 passed)
- `tests/perf/test_dirty_set_integrity.py`, `tests/perf/test_dirty_parity.py` (5 passed)
- `tests/integration/kernel/test_checkpoint_reproducibility.py`, `tests/unit/test_dirty_refresh.py` (7 passed)
- `tests/unit/engine/`, `tests/unit/core/` (394 passed, 1 skipped, 3 deselected -- pre-existing, unrelated to this change)
- `tests/unit/cognition/test_information_seeking.py`, `tests/unit/domains/faction/`, `tests/integration/scenarios/test_faction_campaign.py` (174 passed, 3 deselected)
- `tests/tools/test_parity_ledger_schema.py` (1 passed)

No pre-existing test was modified except the one narrow static-guard whitelist addition described
above in Implementation Notes/Deviations. Full `pytest tests/` was not run (per project convention --
Test-scoper's job next).

## Files Changed
- `src/engine/apply.py` -- Step 1: cross-tick carry-forward line.
- `src/engine/semantic_entity_index.py` -- Steps 2-3: `dimensions` parameter, `resolved_dimensions`
  field, `_DIMENSION_TO_DOMAIN`/`_ALL_DIMENSIONS`, fast-path removal, `SemanticEntityQuery` wiring.
- `tests/unit/domains/optimization/test_semantic_entity_index.py` -- 9 new tests:
  `test_semantic_entity_indexes_carried_forward_across_ticks`,
  `test_get_indexes_only_rebuilds_dirty_domains_across_ticks`,
  `test_single_dimension_query_does_not_rebuild_unrequested_invalidated_dimension`,
  `test_knowledge_domain_still_always_rebuilds_when_requested`,
  `test_apply_generation_semantic_index_carry_forward_bit_identical_to_full_rebuild`,
  `test_semantic_entity_indexes_carry_forward_survives_dirty_set_audit`,
  `test_partial_dimension_request_does_not_reuse_stale_same_tick_object`,
  `test_repeated_same_tick_request_for_same_invalidated_dimension_builds_once`,
  `test_full_request_after_partial_same_tick_rebuilds_invalidated_unresolved_dimension`.
- `tests/static/test_semantic_entity_index_no_stateupdate_write.py` -- deviation fix: added one
  whitelist condition for the new sanctioned `apply.py` carry-forward line; updated docstring.
- `docs/engine/performance_contract.md` -- Step 4: §8.1 new note on `WorldIndexService`'s identical
  shape; §8.2 rewritten "Known limitation" -> shipped-mechanism section, corrected GUARD-SCAN
  paragraph.
- `docs/parity_ledger/infrastructure.yaml` -- Step 5: `INFRA-395`'s `v2_evidence`/`test_path`
  updated via `tools/parity_ledger_writer.py::write_entry()`.
- `staging_artifacts/TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD/plan.md` -- Deviations section added.
- `tickets/inprogress/TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD.md` -- this file (Status, Acceptance
  Criteria, Implementation Notes/Test Summary/Files Changed/Completion Summary).

## Completion Summary
Closed both confirmed gaps in `SemanticEntityIndexService`: cross-tick carry-forward of
`semantic_entity_indexes` in `ApplyPath.apply_generation` (mirroring `world_indexes` exactly), and a
genuine per-dimension selective-build path on `get_indexes()` via a new `dimensions` parameter,
backed by a `resolved_dimensions` per-tick bookkeeping field that makes repeated same-tick partial
and full requests both correct (no stale reuse) and cheap (no redundant rebuilds). All 5
`SemanticEntityQuery` methods now request only their own dimension. `docs/engine/performance_contract.md`
and `INFRA-395`'s `v2_evidence` were updated to describe the shipped mechanism. One deviation was
required and is fully documented: a pre-existing static anti-drift guard's whitelist needed a
narrow, one-line extension to admit the new sanctioned carry-forward pattern, which it had not
anticipated.
