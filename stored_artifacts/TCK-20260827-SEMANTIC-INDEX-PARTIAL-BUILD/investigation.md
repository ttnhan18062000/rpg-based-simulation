---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD
artifact_type: investigation
tags: [engine, performance, determinism]
---

# Investigation — TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD

## Context-Search Note

Both mandatory Step-0c tools returned no usable result for this topic: `mcp__knowledge-search__search_docs`
returned `{"error": "index not found", "action": "run make knowledge-index"}` (the knowledge index has
not been built in this worktree), and `graphify query "semantic entity index partial build"` failed
with `error: graph file not found: .../graphify-out/graph.json` (this worktree has no `graphify-out/`
of its own — it only exists in the parent checkout, and `GRAPH_REPORT.md` there has zero
`SemanticEntityIndex`/`semantic_entity_index` nodes, confirming the graph predates
TCK-20260822-SEMANTIC-ENTITY-INDEX and is not useful for this ticket). The fallback,
`python3 tools/knowledge_search.py query ... --top-k 5`, also failed with `knowledge index not found`.
All three tools were tried, in the required order, before any grep/file read. Proceeded to source-level
investigation per the "skip silently if fallback also fails" instruction.

## Current Behavior

**`src/engine/semantic_entity_index.py`** — `SemanticEntityIndexService.get_indexes()` (lines 46-73):
```python
existing = getattr(state, "semantic_entity_indexes", None)
if existing is not None and existing.tick == state.tick:
    return existing
role_class_index = existing.by_role_class if existing and not should_invalidate("identity", dirty) else _build_role_class_index(state)
region_index = existing.by_region if existing and not should_invalidate("region", dirty) else _build_region_index(state)
faction_index = existing.by_faction if existing and not should_invalidate("identity", dirty) else _build_faction_index(state)
needs_index = existing.by_need if existing and not should_invalidate("needs", dirty) else _build_needs_index(state)
knowledge_index = existing.by_knowledge_domain if existing and not should_invalidate("knowledge", dirty) else _build_knowledge_domain_index(state)
```
All 5 dimensions are computed unconditionally on every call (lines 53-57) — there is no parameter to
request only a subset. `SemanticEntityQuery`'s 5 methods (lines 128-151) each call
`get_indexes(state, dirty)` in full and then pick one dict key out of the result.

**`src/engine/apply.py`** — `ApplyPath.apply_generation`'s new-state constructor call (lines ~340-418)
carries `world_indexes=getattr(prior_state, "world_indexes", None)` at line 406, but has **no**
`semantic_entity_indexes=...` line anywhere in that constructor call. Confirmed by direct `grep` of the
file: the only two `semantic_entity_indexes` hits in the whole codebase's `apply.py` are absent — the
field is not referenced in `apply.py` at all. `src/core/state.py:1112` defines
`semantic_entity_indexes: Any = field(default=None, repr=False, compare=False)`, so a freshly
constructed `new_state` always gets the dataclass default (`None`) for this field every tick. This
reconfirms Deviation #3 in `tickets/done/TCK-20260822-SEMANTIC-ENTITY-INDEX.md` is still accurate —
the gap has not silently regressed or been fixed since. (Contrast: `to_readonly()` at
`src/core/state.py:1250-1251` DOES pass `semantic_entity_indexes=self.semantic_entity_indexes` through
its `replace(...)` call — that is a same-tick read-only view, not the cross-tick carry-forward `apply.py`
needs; it does not substitute for the missing line in `apply_generation`.)

**`src/engine/world_index.py`** — `WorldIndexService.get_indexes()` (lines 105-138) has the
byte-for-byte identical eager-all-5-dimensions shape as `SemanticEntityIndexService.get_indexes()`:
`res_index`/`bldg_index`/`ent_index`/`item_index`/`corpse_index` are all computed on every call with no
selective-dimension parameter. This confirms the ticket's claim that `WorldIndexService` shares the
identical structural limitation. It does not visibly suffer from it because (a) its carry-forward
already works (`apply.py:406`), and (b) `SpatialQueryService` (`src/engine/spatial_query.py`) has 3
call sites that route through it — `nearest_resource_node` (dim: `active_resource_nodes`),
`nearest_building` (dim: `buildings_by_kind`), `nearby_entities` (dim: `entities_by_tile`) — each
invoked per-entity, many times per tick, across movement/pathfinding/routing logic. Collectively these
calls exercise 3 of 5 dimensions every tick regardless of which single dimension any one call wanted,
giving natural cross-call amortization that `SemanticEntityQuery` (zero production callers) has no
equivalent of.

**`CacheInvalidationPolicy.should_invalidate()`** (`src/engine/world_index.py` lines 46-74) — the
`"knowledge"` domain unconditionally returns `True` (line 73, comment at line 70-72: "information_providers
mutations carry no dedicated DirtySet tag today... Conservatively always invalidate"). This is
independent of `dirty` being `None` or populated, and independent of carry-forward. This is directly
asserted by an existing, must-stay-passing test:
`tests/unit/domains/optimization/test_cache_invalidation_policy.py::test_empty_dirty_invalidates_nothing`
(line 83): `assert CacheInvalidationPolicy.should_invalidate("knowledge", dirty) is True` even for a
completely empty `DirtySet()`.

**Tick-pipeline timing** (`src/engine/kernel.py`): `Kernel.tick_once()` calls `_phase_resolution()`
(line 398) before `_phase_advancement()` (line 408). `_phase_resolution()` calls
`AuthoritativeApplyPipeline.refine(...)` (line 649) against `self._state` — the AuthoritativeState
object produced by the PRIOR tick's `_phase_advancement()` call to `ApplyPath.apply_generation(...)`
(line 726). `military_conflict.py`'s `MilitaryConflictPhase` and
`pipeline_phases/paid_information.py`'s `PaidInformationTransactionSystem` are engine-phase classes of
the same shape as the ones wired into `pipeline.py`'s `refine()` sequence (neither currently calls
`SemanticEntityQuery`/`SemanticEntityIndexService` — confirmed by `grep`, zero hits in either file).
This means: if either had wired into the index, their query would run during tick N's
`_phase_resolution`, against the state object built by tick (N-1)'s `apply_generation`. So carrying
`semantic_entity_indexes` forward in `apply_generation`'s constructor (mirroring `world_indexes`) is
mechanically well-timed — by the time either hypothetical call site would query in tick N, the carried
object from tick N-1 would already be attached and non-`None`.

## Central Open Question — Resolved

**Is cross-tick carry-forward alone sufficient, or is true per-dimension selective building also
independently required?** Evidence strongly supports **both fixes are independently necessary** — the
ticket's own scoping of two ACs (carry-forward AND selective-build) is correctly justified, not
over-scoped. Concrete evidence:

1. **`docs/engine/performance_contract.md` §8.2 (lines 113-124) — GUARD-SCAN's own documented
   rejection reason is explicitly the missing selective-build path, not the missing carry-forward**:
   > "`SemanticEntityIndexService.get_indexes()` has no partial-dimension build path -- any query call
   > rebuilds all five dimensions together, and this call site would be the index's first production
   > caller, paying that full rebuild cost with no same-tick amortization in any shipped scenario (every
   > existing scenario has exactly one WAR pair active per tick)."

   This is a direct quote from the actually-shipped ticket's own investigation/plan reasoning, written
   with full knowledge that carry-forward was already a known, separately-documented gap (the very next
   paragraph in the same doc, "Known limitation," lines 154-161, calls out carry-forward as a distinct
   issue). The two gaps are treated as separate and both real in the doc that was written closest in
   time to the actual blocking decision.

2. **The "knowledge" domain's unconditional always-invalidate design makes carry-forward insufficient
   by itself, mechanically, regardless of what any other domain's dirty state looks like.** Even after
   carry-forward is fixed so `existing` is never `None` on a tick's first query, `should_invalidate("knowledge", dirty)`
   still returns `True` on literally every single call (proven by the existing
   `test_empty_dirty_invalidates_nothing` assertion against an empty `DirtySet`). That means
   `_build_knowledge_domain_index(state)` — a full scan of `state.information_providers` — runs on
   every single `get_indexes()` call forever, carry-forward or not. A caller wanting only `by_region`
   (GUARD-SCAN's case) or only `by_role_class` would still pay for this rebuild every time under
   carry-forward-only fix. This is proof, independent of any inference about real-world dirty patterns,
   that carry-forward alone cannot close the "~5x rebuild" cost the ticket describes — it can only ever
   reduce it to "however many of the OTHER 4 domains happen to be dirty this tick, plus 1 mandatory
   knowledge rebuild," never below that floor, unless a caller can say "I don't need knowledge this
   call."

3. **PAID-INFO's rejection reason was different and orthogonal to both of this ticket's fixes** —
   worth flagging explicitly so this ticket's scope is not misread as "the fix that would unblock
   PAID-INFO too." Per `tickets/done/TCK-20260822-PAID-INFO-INDEX-RETROFIT.md`'s Implementation Notes
   and `docs/engine/performance_contract.md` §8.2 (lines 103-111): the live `PaidInformationTransactionSystem.enforce()`
   needs "all providers sorted by entity_id, unfiltered by domain," but `by_knowledge_domain` is bucketed
   by knowledge-domain string and drops any provider with an empty `knowledge_domains` tuple — "no
   dimension in this section maps onto 'all providers sorted by entity_id' without changing that
   selection semantics." This is a missing-query-shape/dimension gap, not a cost/rebuild gap. Neither
   carry-forward nor true per-dimension selective building would change this outcome — PAID-INFO would
   remain correctly unable to route through `SemanticEntityQuery` even after both of this ticket's
   fixes ship, because the index simply has no dimension shaped like what it needs. This is correctly
   out of this ticket's scope (retrofitting call sites is explicitly Out of Scope) and should not be
   treated as unfinished business of this ticket.

**Recommendation**: implement both fixes, exactly as the ticket already scopes them — carry-forward in
`apply.py` (mirrors `world_indexes` exactly, mechanically simple, and is a real, independently-provable
gap per Deviation #3) AND a genuine per-dimension selective-build mechanism in
`SemanticEntityIndexService.get_indexes()` / the `SemanticEntityQuery` call surface (closes the
always-eager-all-5 cost that the "knowledge" domain's unconditional invalidation makes unavoidable
without it). Carry-forward alone would NOT have been sufficient to safely land either retrofit ticket's
hypothetical index-backed version — GUARD-SCAN's own words confirm the selective-build gap was the
actual decision-driving concern, and the knowledge-domain-always-invalidates mechanism proves this
mathematically regardless of what GUARD-SCAN's own dirty-domain overlap would have looked like in
practice. Do NOT narrow this ticket to carry-forward-only.

## Mechanics / Engine Constraints

- `docs/engine/performance_contract.md` §4.1 "Parity Invariant": "Optimization MUST NOT change the
  semantic outcome of an official RPG slice. Any optimization that causes a hash mismatch in the
  `AuthoritativeState` vs. the baseline is a failure." This ticket is pure performance/caching-shape
  work — both fixes must produce byte-identical query results to a from-scratch rebuild in all cases;
  this is exactly what the existing `test_incremental_index_bit_identical_to_full_rebuild` and
  `test_delete_and_rebuild_index_matches_incremental_across_all_dimensions` tests already assert for
  the current (non-carried-forward) behavior, and new tests must assert the same property holds with
  carry-forward and selective-build added.
- `docs/engine/performance_contract.md` §8.1/§8.2: the two "Derived Entity Indexes" subsections this
  ticket must update. `SemanticEntityIndexes` is explicitly "non-authoritative, derived, always
  rebuildable" (semantic_entity_index.py:26) and excluded from `CanonicalStateHasher` by omission
  (confirmed still true — no `semantic_entity_indexes` reference found in `src/engine/checkpoint.py`'s
  `to_canonical_data()` via the existing `test_semantic_index_excluded_from_canonical_state_hash` test).
  Both fixes must preserve this exclusion; neither the carry-forward nor a selective-build change should
  touch `CanonicalStateHasher`.
- `docs/core/state.md`'s immutability law: `AuthoritativeState.semantic_entity_indexes` is attached via
  `object.__setattr__`, never `StateUpdate`/`replace()` (guarded today by the static test
  `tests/static/test_semantic_entity_index_no_stateupdate_write.py`). Any dataclass-shape change for
  selective building (e.g. making per-dimension fields independently `Optional`/tick-stamped) must
  preserve this — no new field may become writable through the authoritative mutation path.

## Docs Requiring Update

- `docs/engine/performance_contract.md`: §8.2's "Known limitation" callout (lines 154-161) must be
  rewritten to describe the new carried-forward, per-dimension-selective behavior (or a narrower,
  accurate remaining-limitation statement if selectivity is scoped down during planning). The existing
  PAID-INFO and GUARD-SCAN paragraphs (lines 93-124) that cite "no partial-dimension build path" as the
  reason those retrofits didn't route through `SemanticEntityQuery` will become stale once selective
  building ships and should be corrected or annotated (they remain historically accurate as an
  explanation of why those two tickets made their choice at the time, but should not read as still
  describing today's capability once this ticket lands). §8.1 should also gain a short note
  documenting that `WorldIndexService` has the identical eager-all-N-dimensions shape but is not being
  fixed in this ticket, per the investigation finding above (its 3 `SpatialQueryService` call sites
  collectively amortize across most dimensions every tick, unlike `SemanticEntityQuery`'s zero
  production callers) — this satisfies the ticket's Scope requirement to "explicitly document why its
  usage pattern makes that unnecessary for now" if planning confirms no fix is warranted.
- `docs/parity_ledger/infrastructure.yaml`: `INFRA-395`'s `v2_evidence` field must be updated to
  describe the new carry-forward mechanism (mirroring `world_indexes=getattr(prior_state, "world_indexes", None)`)
  and the new selective-build mechanism, and cite the new test node IDs once written. `status` stays
  `verified`; `priority` stays `P1` (entry priority, distinct from this ticket's own `P2`); no
  `text`/`divergence_note` change is expected since this is evidence-only (no semantic/behavioral
  divergence — Parity Invariant requires identical query outputs).

The `docs/plans/idea_semantic_entity_index.md` doc (path: `docs/plans/idea_semantic_entity_index.md`)
is not required to change for this ticket: it already carries a "superseded-by" marker from
TCK-20260822-SEMANTIC-ENTITY-INDEX pointing to the shipped implementation, and this ticket does not
change the index's original design intent or dimension set — only its cross-tick lifecycle and
call-granularity mechanics, which are performance_contract.md's and infrastructure.yaml's territory, not
this historical idea doc's.

`docs/guidelines/intentional_divergences.md` is not required to change: both fixes are constrained by
the Parity Invariant to produce byte-identical query results to a from-scratch rebuild in all cases (see
Mechanics/Engine Constraints above) — there is no intentional behavior divergence from legacy or from
the Mechanics Bible to record, only a caching-lifecycle change to an already non-authoritative derived
projection.

## Parity Ledger Overlap

- `INFRA-395` (`docs/parity_ledger/infrastructure.yaml`, lines 11510-11560) — status `verified`,
  priority `P1`. Directly covers `SemanticEntityIndexService.get_indexes`, `CacheInvalidationPolicy`,
  and the `SemanticEntityQuery` methods this ticket modifies. `test_path` currently lists the 16 tests
  from `TCK-20260822-SEMANTIC-ENTITY-INDEX`; this ticket's new tests should be appended, not replace
  existing entries (AC requires all current tests keep passing unmodified). This is a `P1` entry —
  per the project's Authoritative Mechanics Rule, `P0` entries require a passing `test_path`; `P1` does
  not carry that hard gate but `v2_evidence` must still stay accurate to actual shipped code, which is
  the specific thing this ticket's Scope requires updating.
- No other parity ledger entries were found with `text` overlapping `semantic_entity_index.py`,
  `CacheInvalidationPolicy`, or `apply.py`'s carry-forward mechanics. `TOWN-182` (`town_resource.yaml`)
  and `FAC-008`/`SOC-245` (`faction.yaml`/`social_narrative.yaml`) were touched by the two retrofit
  tickets but describe the *local-hoist* mechanisms those tickets shipped instead of routing through
  the index — they are not affected by this ticket, since this ticket explicitly does not touch either
  retrofit call site (Out of Scope).

## Prior Work

- `tickets/done/TCK-20260822-SEMANTIC-ENTITY-INDEX.md` — shipped the index itself; Deviation #3 is the
  exact carry-forward gap this ticket closes (re-confirmed still accurate above, not regressed).
- `tickets/done/TCK-20260822-PAID-INFO-INDEX-RETROFIT.md` and
  `tickets/done/TCK-20260822-GUARD-SCAN-INDEX-RETROFIT.md` — both real production call sites that
  evaluated wiring into the index and rejected it; GUARD-SCAN's rejection reason is the direct evidence
  resolving this ticket's central open question (see above). Both shipped local hoists with their own
  passing test coverage and parity-ledger updates (`TOWN-182`, `FAC-008`/`SOC-245`) that remain
  unaffected by this ticket.
- `stored_artifacts/TCK-20260822-SEMANTIC-ENTITY-INDEX/plan.md` — documents the original decision to
  follow `WorldIndexService`'s lazy pull-based lifecycle exactly (Recommendation 1) and lists
  `src/engine/apply.py` as an explicit Scope-Guard read-only file for that ticket — this ticket is the
  designated follow-up that reopens exactly that one file for exactly this one addition.
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_index_reflects_dirty_set_change_without_full_rebuild`
  (lines 133-172) already demonstrates the rebuild-call-spy pattern (monkeypatching `_build_*` static
  methods to record calls) that AC #2 and AC #3's new tests should reuse directly — no new test
  infrastructure needs inventing.

## Risks and Open Questions

- **Open (must be resolved during planning, not assumed here)**: the ticket's own Assumptions section
  leaves the selective-build mechanism's shape undecided — `Optional`-per-dimension fields on
  `SemanticEntityIndexes` vs. a `dimensions: Optional[Set[str]]` parameter on `get_indexes()` that
  skips unrequested-and-unneeded rebuild work without changing the public dataclass shape. This
  investigation does not resolve this — it is explicitly a planning-phase design decision per the
  ticket text ("document the decision and rationale explicitly before implementation"). Recommend the
  `dimensions` parameter approach as lower-risk: it keeps `SemanticEntityIndexes` a fully-built,
  non-partial dataclass at all times (preserving every existing test's assumptions about the return
  type), and only changes internal control flow inside `get_indexes()` — but this is a planning call,
  not asserted as decided here.
- Risk: adding a `dimensions` parameter to `SemanticEntityQuery`'s public methods (or `get_indexes`)
  changes a call signature that 0 production call sites currently use but that IS covered by existing
  unit tests (`test_semantic_entity_index.py`) calling `get_indexes(state)` / `get_indexes(state, dirty)`
  positionally with 1-2 args. Any new parameter must be added with a default that preserves those exact
  call signatures unmodified, per AC's "all existing tests... continue to pass unmodified."
  `SemanticEntityQuery.by_region` etc. currently always request all 5 dimensions internally (line
  134-136); if a `dimensions` parameter is added at the `SemanticEntityQuery` level too (not just
  `get_indexes`), each `by_*` method would need updating to pass its own single dimension — this is
  itself a semantic/call-count-reducing change to `SemanticEntityQuery`'s callers, so should be scoped
  carefully during planning to whichever surface actually needs it (AC #3 only requires proof that
  "a caller requesting a single dimension... does not trigger a rebuild of an unrequested dimension" —
  it does not mandate changing all 5 `by_*` signatures if only one needs to demonstrate the property).
- Risk: `existing.tick == state.tick` fast-path check (line 50) will almost never fire cross-tick even
  after carry-forward, since `new_state.tick` is incremented relative to the carried `existing.tick`
  (matches `WorldIndexes`' identical behavior — confirmed by symmetry with `world_indexes`, not
  independently tested here). This is expected and fine — the per-dimension ternaries handle the
  mismatch correctly regardless, as proven by the existing `test_index_reflects_dirty_set_change_without_full_rebuild`
  test already passing `next_state` objects with a bumped `tick` and a pre-set `semantic_entity_indexes`
  from the prior tick.
- Open question already flagged by the ticket and not contradicted by this investigation: whether
  `WorldIndexService` needs the identical selective-build fix for "architectural consistency." This
  investigation found no shipped call site currently forces `WorldIndexService` to pay an unwanted
  ~5x cost (its 3 `SpatialQueryService` callers collectively touch 3-5 of its dimensions every tick via
  independent per-entity calls), so the default assumption in the ticket ("fix `SemanticEntityIndexService`
  only... unless a materially cheap consistent fix is found") is supported by the evidence gathered
  here — but this is a judgment call for planning, not asserted as final.

## Anti-Drift Hazards

- Do not let this ticket drift into retrofitting `paid_information.py` or `military_conflict.py` into
  `SemanticEntityQuery` — both are explicitly Out of Scope, and (per the Central Open Question findings
  above) PAID-INFO's blocker is an unrelated missing-dimension gap that neither of this ticket's two
  fixes would resolve anyway; attempting it would be scope creep chasing a problem this ticket cannot
  actually fix.
- Do not let the "knowledge always-invalidates" behavior get silently changed as a side effect of
  adding selective building — `test_empty_dirty_invalidates_nothing`'s
  `should_invalidate("knowledge", dirty) is True` assertion and the `test_index_reflects_dirty_set_change_without_full_rebuild`
  test's `assert knowledge_calls == [1]` assertion both currently encode "knowledge always rebuilds" as
  correct, expected behavior (documented deliberate limitation, out of scope to fix per the original
  ticket's AC #3 boundary) — a selective-build mechanism must still allow a caller who DOES want
  `by_knowledge_domain` to always get a fresh rebuild; it should only stop UNREQUESTED domains from
  being eagerly rebuilt.
- Do not touch `CanonicalStateHasher`/`checkpoint.py` — both fixes operate entirely within the
  non-authoritative derived-cache pattern; touching hashing would violate the exclusion-by-omission
  invariant this whole feature relies on.
- Do not change `SemanticEntityIndexes`' existing 5 public field names/types if a
  selective-build/`Optional`-fields approach is chosen during planning — any caller pattern reading
  `.by_region`/`.by_role_class`/etc. directly (tests do this extensively) must keep working; if fields
  become `Optional[...]`, every existing direct-access test that assumes a populated dict will need
  re-validation, which is a large blast radius to weigh during planning.
- The `apply.py` carry-forward line addition is a single, narrow, additive line (mirroring
  `world_indexes` exactly) — resist the temptation to "clean up" or refactor the surrounding
  large constructor call while touching this file; `apply.py` was an explicit Scope-Guard read-only
  file for the original ticket, and this ticket only reopens it for this one addition.
