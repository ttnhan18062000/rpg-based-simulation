---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD
artifact_type: plan
tags: [engine, performance, determinism]
---

# Implementation Plan — TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD

## Summary

This plan closes both confirmed gaps in `SemanticEntityIndexService` independently: (1) cross-tick
carry-forward of `AuthoritativeState.semantic_entity_indexes`, added to `ApplyPath.apply_generation`'s
new-state constructor exactly mirroring the existing `world_indexes` line; and (2) a genuine
per-dimension selective-build path on `get_indexes()`, implemented as a `dimensions:
Optional[Set[str]] = None` parameter (the investigation's recommended lower-risk option) rather than
making `SemanticEntityIndexes`' fields `Optional`. `SemanticEntityQuery`'s 5 query methods are updated
to pass their own single dimension name so a caller like a hypothetical `by_region` retrofit no longer
pays for rebuilding `identity`/`needs`/`knowledge` in the same call. The `knowledge` domain's
unconditional `should_invalidate` `True` is left completely untouched — selective building achieves
its goal purely through the new "was this dimension requested at all" gate, which sits logically prior
to the existing invalidation check, so a caller who does not request `knowledge` never pays for it
regardless of `CacheInvalidationPolicy`'s answer, while a caller who does request it still always gets
a fresh rebuild exactly as today. This design was chosen instead of touching
`CacheInvalidationPolicy.should_invalidate("knowledge", ...)` because it requires zero change to a
policy function referenced by both the semantic and (indirectly, by symmetry) spatial-index tests, and
it keeps the "knowledge always invalidates when it is actually wanted" deliberate limitation fully
intact per the ticket's anti-drift hazard.

A same-tick correctness hazard was identified during planning (not called out in investigation.md or
test_plan.md) and is addressed in Step 2: the existing `existing.tick == state.tick` fast path
(`semantic_entity_index.py:50-51`) blindly returns the cached object without re-running any
per-dimension logic. Once partial requests are possible, a second same-tick call requesting a
dimension that an earlier same-tick call did not request (and which was invalidated but skipped
because it was unrequested) must not silently return the stale value through this fast path. The
originally-planned fix (narrowing the fast path to fire only when `dimensions is None`) was itself found
insufficient by a second Review round — see below; the mechanism actually shipped in Step 2 removes the
fast path outright.

**Revision (post-Review round 1, architecture-reviewer NEEDS_CHANGES finding):** the first version of
this plan stopped at the narrowed-fast-path fix above and was wrong. `CacheInvalidationPolicy.should_invalidate()`
is a pure function of `dirty`, which does not change within a tick, but that cuts the other way from how
the first version used it: for a dimension that IS invalidated this tick, re-running the per-dimension
ternary on *every* same-tick call that requests it re-triggers `_build_*_index(state)` on every one of
those calls, not just the first — because the ternary's rebuild branch has no memory of "I already
rebuilt this dimension once this tick." This is a real regression versus pre-fix (eager, all-5,
once-per-call) behavior for exactly the scenario this ticket exists to fix: an invalidated dimension
queried repeatedly within one tick via `SemanticEntityQuery`. Step 2 was revised to add genuine per-tick
"already resolved this dimension" bookkeeping, carried as a new 6th field, `resolved_dimensions:
FrozenSet[str]`, on `SemanticEntityIndexes` (default `frozenset()`, so every existing 5-keyword
construction call site and every test that pattern-matches or reads the existing 5 fields is
unaffected — grep confirms `SemanticEntityIndexes(` is only ever constructed at
`semantic_entity_index.py:59`, nowhere in `tests/`). A dimension enters `resolved_dimensions` the moment
any call this tick has settled its value (built fresh, or confirmed not-invalidated) — a later same-tick
call for that same dimension then skips `should_invalidate` entirely and reuses the settled value,
regardless of what `should_invalidate` would independently say. This bookkeeping is layered on top of,
not a replacement for, the original "was this dimension requested at all" gate.

**Revision 2 (post-Review round 2, architecture-reviewer NEEDS_CHANGES finding on the narrowed fast
path itself):** round 1's revision kept the narrowed fast path — `if existing is not None and
existing.tick == state.tick and dimensions is None: return existing` — believing "full request" and
"dimensions is None" were interchangeable safety conditions. They are not: a full request
(`dimensions=None`) issued *after* an earlier same-tick partial request can hit this fast path and
return `existing` even though `existing.resolved_dimensions` covers only the dimensions that earlier
partial call actually resolved — any OTHER dimension invalidated this tick (e.g. `region`, if the
partial call only requested `role_class`) is silently never checked and a stale value is returned for
it, a genuine Parity Invariant violation (`docs/engine/performance_contract.md` §4.1). Step 2 is revised
again below to remove the fast path entirely rather than add a second, narrower guard condition to it
(`dimensions is None and existing.resolved_dimensions == _ALL_DIMENSIONS` was the alternative
considered — see the Design Decision in Step 2 for why removal was chosen instead). Removal is safe and
cheap: with `resolved_dimensions`/`already_resolved` bookkeeping already in place from round 1, every
per-field ternary already correctly and cheaply decides "reuse or rebuild" for its own field on every
call — the outer fast path was only ever a convenience to skip running those 5 cheap checks, and skipping
them incorrectly is worse than just running them. Running the per-field ternaries on every call, partial
or full, is not a reintroduction of the *original* problem this ticket exists to fix (an unconditional
full-object return that bypassed per-field invalidation logic entirely, on every call, including a
state's very first call): the per-field ternaries always correctly consult `already_resolved`,
`dimensions`, and `should_invalidate` before deciding to reuse `existing`'s pre-tick/carried-forward field
value or rebuild — that per-field logic is exactly what was missing before this ticket, and removing the
outer fast path does not touch it.

`WorldIndexService` is confirmed (via direct read of `src/engine/world_index.py:105-138`) to share the
identical eager-all-5-dimensions shape, but per the ticket's Out-of-Scope guard and the investigation's
finding that its 3 `SpatialQueryService` call sites collectively amortize across most dimensions every
tick, this plan does not modify `world_index.py` code — only documents the finding in
`performance_contract.md` §8.1.

## Steps

### Step 1 — Carry `semantic_entity_indexes` forward across ticks in `apply.py`

**Files:** `src/engine/apply.py`

**Change:** In `ApplyPath.apply_generation`'s `AuthoritativeState(...)` constructor call, add one line
immediately after the existing `world_indexes=getattr(prior_state, "world_indexes", None),` line
(confirmed present at `src/engine/apply.py:406`, read directly during planning):

```python
world_indexes=getattr(prior_state, "world_indexes", None),
semantic_entity_indexes=getattr(prior_state, "semantic_entity_indexes", None),
_index_hits=getattr(prior_state, "_index_hits", 0),
```

This mirrors `world_indexes`'s carry-forward exactly (same `getattr(..., None)` default pattern already
used for `_index_hits`/`_index_misses`/`_opt_profile`/`_force_full_scan` at
`src/engine/apply.py:407-410`). `AuthoritativeState.semantic_entity_indexes` is confirmed defined as
`field(default=None, repr=False, compare=False)` at `src/core/state.py:1112` — same shape as
`world_indexes` at `src/core/state.py:1111` — so this is a type-compatible, non-breaking addition.

**Other writers to this field (enumerated):** grep of `src/` for `semantic_entity_indexes` (excluding
tests) confirms exactly three touch points, none of which conflict with this change:
1. `src/engine/semantic_entity_index.py:69` — `SemanticEntityIndexService.get_indexes()`'s
   `object.__setattr__(state, "semantic_entity_indexes", new_indexes)`, which lazily attaches a freshly
   resolved object to whatever `AuthoritativeState` instance it is given. This is the only place that
   ever writes a *non-None* value; it runs strictly after `apply_generation` has already constructed
   `new_state` (both because `_phase_resolution` runs after `_phase_advancement` produced the state
   object per tick per `src/engine/kernel.py:398`/`:408`/`:726`, and because within a single call it is
   the last statement in `get_indexes`), so there is no ordering conflict — this step only changes what
   `existing` is at the *start* of the next tick's first `get_indexes()` call, from always-`None` to the
   prior tick's resolved object.
2. `src/core/state.py:1251` — `to_readonly()`'s `replace(...)` call copies `self.semantic_entity_indexes`
   through unchanged; it is a same-tick read-only view, not a write of new content, and is unaffected by
   this step.
3. `src/core/state.py:1112` — the dataclass field definition itself (default value only, not a runtime
   writer).

No concurrent-write race exists: the engine is single-threaded per tick, and `apply_generation` runs
exactly once per tick, strictly before any `get_indexes()` call that tick.

**Do NOT touch:** any other field in the `AuthoritativeState(...)` constructor call in `apply.py`, or
any other logic in the surrounding ~90-line constructor block. `apply.py` was an explicit Scope-Guard
read-only file for `TCK-20260822-SEMANTIC-ENTITY-INDEX`; this step reopens it for exactly this one
additive line, mirroring `world_indexes`.

**Verify:**
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_semantic_entity_indexes_carried_forward_across_ticks` (new, test_plan.md #1)
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_get_indexes_only_rebuilds_dirty_domains_across_ticks` (new, test_plan.md #2)
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_apply_generation_semantic_index_carry_forward_bit_identical_to_full_rebuild` (new, test_plan.md #5)
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_semantic_entity_indexes_carry_forward_survives_dirty_set_audit` (new, test_plan.md #6)
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_identity_only_update_does_not_raise_dirty_set_leak_error` (existing, must still pass unmodified)

---

### Step 2 — Add a `dimensions` selective-build parameter to `SemanticEntityIndexService.get_indexes()`, with per-tick "already resolved" tracking

**Files:** `src/engine/semantic_entity_index.py`

**Change:** Confirmed current shape by direct read (`src/engine/semantic_entity_index.py:46-73`):
`get_indexes(state, dirty=None)` always resolves all 5 fields via one ternary per field
(lines 53-57), and short-circuits on an exact same-tick fast path (lines 50-51). `SemanticEntityIndexes`
is a frozen dataclass with exactly 5 fields, confirmed at `src/engine/semantic_entity_index.py:22-34`
(`tick`, `by_role_class`, `by_region`, `by_faction`, `by_need`, `by_knowledge_domain` — 6 names total
including `tick`). Confirmed by grep that `SemanticEntityIndexes(` is constructed nowhere except
`semantic_entity_index.py:59` — no test or other call site builds one directly, so a new field with a
default is safe to add. Modify as follows:

**Design decision, round 1 (resolves the first Review finding):** `CacheInvalidationPolicy.should_invalidate()`
is a pure function of `dirty`, and `dirty` does not change within a tick — so once a dimension's
invalidation question has been answered once this tick (whether that answer led to a fresh build or to
reusing the prior value), asking it again this same tick is always redundant and, for a dimension that
answers `True`, would trigger a second unnecessary `_build_*_index(state)` call. The existing lazy
`SemanticEntityIndexes`/`get_indexes()` object is the only per-tick-lifetime state this mechanism has to
work with (no new field on `AuthoritativeState`, no new `DirtySet` tag), so the tracking is added as a
**6th field on `SemanticEntityIndexes` itself**: `resolved_dimensions: FrozenSet[str]`, defaulted via
`field(default_factory=frozenset)`. This is additive only — it does not change any of the 5 existing
field names or types, so every existing direct read of `.by_region`/`.by_role_class`/etc. across the
test suite is unaffected, and the field's leading-underscore-free name is deliberately still distinct
from "the 5 public dimension fields" referenced everywhere else in this plan (Scope Guards updated
below to name it explicitly as the one field this ticket is permitted to add).

**Design decision, round 2 (resolves the second Review finding):** the round-1 version of this step kept
a same-tick fast path (`if existing is not None and existing.tick == state.tick and dimensions is None:
return existing`) that only checked `dimensions is None`, not whether `existing.resolved_dimensions`
actually covers all 5 dimensions — so a full request following an earlier same-tick *partial* request
could return a stale value for whatever dimensions that partial request never touched. Two fixes were
weighed:
  - **(a) Tighten the guard's condition** to `dimensions is None and existing.resolved_dimensions ==
    _ALL_DIMENSIONS` — keeps the early-return shape, adds a completeness check.
  - **(b) Remove the fast path entirely** and let every call, partial or full, fall through to the
    per-field ternaries.

  **(b) is chosen.** The per-field ternaries (point 6 below) already, on every call, correctly and
  cheaply decide per dimension whether to reuse `existing`'s value (via `already_resolved`, the
  "not requested" gate, or `should_invalidate`) or rebuild it — this is plain dict/set-membership and
  boolean-branch logic, not a rebuild, for any dimension that is already in `resolved_dimensions` or is
  simply not invalidated. A full request that follows a same-tick partial request costs at most one
  membership check per already-resolved dimension plus (for any dimension that partial request skipped)
  exactly the same `should_invalidate` check the fast path would have skipped incorrectly — i.e. option
  (b) is not just simpler than (a), it is what (a) reduces to anyway once `existing.resolved_dimensions
  == _ALL_DIMENSIONS` is true, while additionally being *correct* (not stale) in every case where it
  isn't. Option (a) was rejected only because it adds a second place (the guard condition) that has to
  independently stay in sync with `resolved_dimensions`' semantics, for a saving that the per-field
  ternaries already provide for free.

  This does **not** reintroduce the *original* problem this ticket exists to fix. The original problem
  (pre-ticket, and the shape the very first, pre-Review version of this plan risked recreating) was an
  **unconditional** full-object return that bypassed per-field invalidation logic *entirely*, on *every*
  call, including a state's first-ever call — i.e. no per-field reasoning ran at all. Removing this one
  same-tick, full-request early return does not touch the per-field ternaries in any way; they still run
  their existing `already_resolved` / "requested" / `should_invalidate` logic on every call exactly as
  round 1 specified, still starting from the pre-tick/carried-forward `existing` object as their reuse
  baseline exactly as before. The only thing that changes is that this reasoning now runs on *every*
  call instead of being skipped by an early return that could not be trusted to have already reasoned
  about every dimension.

1. Add a module-level mapping from per-field "dimension name" to the `CacheInvalidationPolicy` domain
   name it depends on (these are deliberately different vocabularies — e.g. both `"role_class"` and
   `"faction"` dimensions map to the `"identity"` invalidation domain, exactly matching today's existing
   ternaries at lines 53 and 55, which both already call `should_invalidate("identity", dirty)`), and a
   frozenset of all 5 dimension names for the bootstrap/full-request case:
   ```python
   _DIMENSION_TO_DOMAIN = {
       "role_class": "identity",
       "region": "region",
       "faction": "identity",
       "need": "needs",
       "knowledge_domain": "knowledge",
   }
   _ALL_DIMENSIONS: FrozenSet[str] = frozenset(_DIMENSION_TO_DOMAIN.keys())
   ```
2. Add the 6th field to `SemanticEntityIndexes`:
   ```python
   resolved_dimensions: FrozenSet[str] = field(default_factory=frozenset)
   ```
   placed after the existing 5 fields (order does not matter for keyword-constructed instances; the sole
   construction call site at line 59 uses keywords).
3. Change `get_indexes`'s signature to `get_indexes(state, dirty=None, dimensions: Optional[Set[str]] =
   None) -> SemanticEntityIndexes`. `dimensions=None` means "all 5" — this is the default, so every
   existing call site and every existing test calling `get_indexes(state)` / `get_indexes(state, dirty)`
   positionally is unaffected (satisfies AC #6 and the investigation's flagged signature-compatibility
   risk).
4. **Remove the same-tick fast path entirely.** Delete the existing
   `if existing is not None and existing.tick == state.tick: return existing` check
   (`semantic_entity_index.py:50-51`) outright — do not replace it with a narrower still-early-return
   variant keyed on `dimensions is None` (the round-1 shape) or on `resolved_dimensions == _ALL_DIMENSIONS`
   (the alternative considered and rejected above). Every call, partial or full, now falls through
   unconditionally to compute `already_resolved` (point 5) and run the per-field ternaries (point 6),
   which already correctly and cheaply decide reuse-vs-rebuild per dimension — this is what makes removal
   safe rather than a performance regression: no call, of any shape, ever pays for a real rebuild of a
   dimension that is already in `resolved_dimensions` or that `should_invalidate` says is clean.
5. Before the per-field ternaries, compute which dimensions were already resolved earlier this same
   tick:
   ```python
   already_resolved: FrozenSet[str] = (
       existing.resolved_dimensions
       if existing is not None and existing.tick == state.tick
       else frozenset()
   )
   ```
   `existing.tick == state.tick` is `True` only when at least one earlier call *this tick* already wrote
   a `new_indexes` back onto `state.semantic_entity_indexes` (see point 7) — this is now the only place
   in `get_indexes()` that condition is checked, since point 4 removed the fast path that used to check
   it too. On the first call of a tick (including immediately after cross-tick carry-forward, where
   `existing.tick` is the *prior* tick's number), this is always `frozenset()`, matching pre-fix
   bootstrap behavior for "nothing resolved yet this tick."
6. For each of the 5 per-field ternaries, add the "already resolved this tick" check as a new clause
   OR'd in *before* the existing "was this dimension requested" and "not invalidated" clauses from the
   pre-Review version of this step — this is the actual fix. Concretely, for `role_class`:
   ```python
   role_class_index = (
       existing.by_role_class
       if existing is not None and (
           "role_class" in already_resolved
           or (dimensions is not None and "role_class" not in dimensions)
           or not CacheInvalidationPolicy.should_invalidate("identity", dirty)
       )
       else SemanticEntityIndexService._build_role_class_index(state)
   )
   ```
   Apply the same pattern to `region`/`"region"`, `faction`/`"identity"`, `need`/`"needs"`,
   `knowledge_domain`/`"knowledge"` — the existing domain string passed to `should_invalidate` for each
   field is unchanged; only the new `"<name>" in already_resolved or` clause is added, ahead of the two
   clauses Step 2 already had. When `existing is None` (first-ever call for this state lineage, i.e.
   tick 0 before any carry-forward exists), the whole `existing is not None and (...)` guard is `False`
   regardless of `dimensions` or `already_resolved`, so every field is always built — unchanged bootstrap
   behavior, and still why no `Optional`-field variant of the 5 original fields is needed.
7. Compute the new `resolved_dimensions` to write back, so the *next* same-tick call (if any) sees this
   call's settled dimensions as already-resolved:
   ```python
   newly_settled: FrozenSet[str] = (
       _ALL_DIMENSIONS if (existing is None or dimensions is None) else frozenset(dimensions)
   )
   resolved_dimensions = already_resolved | newly_settled
   ```
   `newly_settled` is "every dimension this call just settled the invalidation question for" — for the
   bootstrap case (`existing is None`) or a full request (`dimensions is None`), that is all 5 (matching
   the fact that all 5 ternaries in point 6 unconditionally resolve when `existing is None`, and all 5
   are "requested" when `dimensions is None`); for a partial request it is exactly the requested set.
   Include `resolved_dimensions=resolved_dimensions` in the `SemanticEntityIndexes(...)` constructor call
   at line 59, alongside the existing 5 fields.
8. Do **not** change `CacheInvalidationPolicy.should_invalidate()` in `src/engine/world_index.py` at
   all — the `"knowledge"` domain's unconditional `return True` (confirmed at
   `src/engine/world_index.py:69-73`) is untouched. A caller that does not request `knowledge_domain`
   skips its rebuild via the "not requested" gate; a caller that requests it for the first time this
   tick still always rebuilds, because `should_invalidate("knowledge", dirty)` is still unconditionally
   `True`; a caller that requests it *again* this same tick reuses the value from the first call via the
   new `already_resolved` gate (point 6) — this is the mechanism this Review round adds, and it does not
   touch `should_invalidate` to achieve it. This directly answers the ticket's deferred design question:
   the `knowledge` domain's always-invalidate-on-first-request-per-tick behavior stays exactly as
   documented and tested today
   (`tests/unit/domains/optimization/test_cache_invalidation_policy.py::test_empty_dirty_invalidates_nothing`
   is unaffected because it asserts against `CacheInvalidationPolicy.should_invalidate` directly, which
   this step does not modify).

**Do NOT touch:** `SemanticEntityIndexes`' original 5 field names/types (dataclass at
`src/engine/semantic_entity_index.py:22-34` — only the new 6th `resolved_dimensions` field is added,
with a default, per point 2); `_build_*` static methods' bodies (lines 76-119, unchanged);
`CacheInvalidationPolicy` in `world_index.py` (see point 8 above); `WorldIndexService.get_indexes()`
(`src/engine/world_index.py:105-138`) — confirmed to share the identical eager-all-5 shape but is
documentation-only in this ticket per Out of Scope.

**Verify:**
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_knowledge_domain_still_always_rebuilds_when_requested` (new, test_plan.md #4)
- A new test not listed in test_plan.md, added here because it guards a correctness hazard found during
  planning that the Parity Invariant (`docs/engine/performance_contract.md` §4.1) requires but that
  test_plan.md's enumerated tests do not exercise: `test_partial_dimension_request_does_not_reuse_stale_same_tick_object`
  — construct a state where `identity` and `knowledge` are both invalidated this tick; call
  `get_indexes(state, dirty, dimensions={"region"})` first (which must not rebuild `role_class`/
  `faction`/`knowledge_domain`), then call `get_indexes(state, dirty, dimensions={"role_class"})`
  immediately after within the same tick, and assert `_build_role_class_index` WAS called on the second
  call (proving the per-field ternaries, which is all that now runs on every call since point 4 removed
  the fast path, correctly rebuild a dimension the first call never touched — this covers the case where
  the *newly requested* dimension differs from what was resolved before).
- **Revised/extended per the Review round-1 finding**: the same test (or a new sibling test in the same
  file, `test_repeated_same_tick_request_for_same_invalidated_dimension_builds_once`) must also cover the
  fixed regression case: with `identity` invalidated this tick, call
  `get_indexes(state, dirty, dimensions={"role_class"})` twice in a row within the same tick (same
  `state`/`dirty` object across both calls, no intervening tick advance), and assert
  `_build_role_class_index` was called **exactly once** across both calls combined (via a call-count spy,
  reusing the existing monkeypatch pattern from `test_index_reflects_dirty_set_change_without_full_rebuild`),
  and that the second call's returned `.by_role_class` `is` (identity-equal to) the first call's. This is
  the test that would have failed against the pre-Review-round-1 version of this step and must pass
  against the mechanism in points 5-7 above.
- **New test required by the Review round-2 finding**:
  `test_full_request_after_partial_same_tick_rebuilds_invalidated_unresolved_dimension` — reproduces the
  exact trace the reviewer gave. Construct a state/dirty combo where only `region` is invalidated this
  tick (`identity`/`needs`/`knowledge` are not). Call 1: `get_indexes(state, dirty,
  dimensions={"role_class"})` — settles only `role_class` (reusing/not rebuilding `by_region`, since
  `region` was never requested this call); assert `resolved_dimensions == {"role_class"}` on the
  returned object. Call 2 (same `state`/`dirty` object, no tick advance): a full request, `get_indexes(state,
  dirty)` with `dimensions` omitted. Assert `_build_region_index` WAS called during call 2 (proving the
  removed fast path is not silently reintroduced in any form) and that the returned `.by_region` reflects
  a fresh rebuild against current entity state, not call 1's carried-forward/stale value — construct the
  test data so a stale vs. fresh `by_region` are distinguishably different (e.g. an entity's `region_id`
  changed between the state `existing` was carried from and the state under test), so a bug that returns
  the stale value fails the assertion rather than passing by coincidence. This is the test that would have
  failed against the Review-round-1 version of Step 2 (narrowed-but-not-removed fast path) and must pass
  against the round-2 mechanism (fast path removed).
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_index_reflects_dirty_set_change_without_full_rebuild` (existing, must still pass unmodified — exercises `get_indexes(state, dirty)` with no `dimensions` arg)
- `tests/unit/domains/optimization/test_cache_invalidation_policy.py::test_empty_dirty_invalidates_nothing` (existing, must still pass unmodified)

---

### Step 3 — Wire `SemanticEntityQuery`'s 5 methods to request only their own dimension

**Files:** `src/engine/semantic_entity_index.py`

**Change:** Confirmed current shape by direct read (`src/engine/semantic_entity_index.py:128-151`):
each of the 5 `SemanticEntityQuery` static methods (`by_role_class`, `by_region`, `by_faction`,
`by_need`, `by_knowledge_domain`) currently calls `SemanticEntityIndexService.get_indexes(state, dirty)`
with no dimension filter, then reads exactly one field off the result. Update each call to pass the
single matching dimension name introduced in Step 2, e.g.:
```python
@staticmethod
def by_region(state: AuthoritativeState, dirty: Optional[DirtySet], region_id: str) -> Tuple[int, ...]:
    indexes = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"region"})
    return indexes.by_region.get(region_id, ())
```
and correspondingly `dimensions={"role_class"}` / `{"faction"}` / `{"need"}` / `{"knowledge_domain"}`
for the other four. **Public method signatures of `SemanticEntityQuery`'s 5 methods do not change** —
only their internal call to `get_indexes()` gains the new keyword argument. This directly satisfies the
investigation's flagged risk ("does not mandate changing all 5 by_* signatures") while still closing
the actual perf gap for every dimension, not just the one AC #3's test exercises.

**Do NOT touch:** the return-shape contract (`Tuple[int, ...]`, IDs only — guarded by
`tests/static/test_semantic_entity_index_returns_ids_only.py`); do not add a `dimensions` parameter to
any of these 5 public methods' own signatures.

**Verify:**
- `tests/unit/domains/optimization/test_semantic_entity_index.py::test_single_dimension_query_does_not_rebuild_unrequested_invalidated_dimension` (new, test_plan.md #3 — this is the AC #3 test, and requires both Step 2 and Step 3 to be complete)
- `tests/static/test_semantic_entity_index_returns_ids_only.py` (existing, must still pass unmodified)

---

### Step 4 — Update `docs/engine/performance_contract.md` §8.2 (and add a §8.1 note)

**Files:** `docs/engine/performance_contract.md`

**Change:** Replace the "Known limitation" paragraph at §8.2 (confirmed present, describing the
carry-forward gap: "unlike `world_indexes`, `semantic_entity_indexes` is not carried forward across
ticks...") with a paragraph describing the shipped mechanism: cross-tick carry-forward now mirrors
`world_indexes` exactly (cite the new `apply.py` line from Step 1), and `get_indexes()` now accepts an
optional `dimensions` parameter that lets a caller skip rebuilding invalidated-but-unrequested
dimensions (cite Step 2/3). Explicitly document the new `resolved_dimensions` per-tick bookkeeping field
added to `SemanticEntityIndexes` in Step 2: within a single tick, a dimension is rebuilt at most once
regardless of how many separate `SemanticEntityQuery` calls request it that tick — the first call that
settles a dimension's invalidation question (build or reuse) marks it resolved, and every subsequent
same-tick call for that dimension reuses the settled value without re-consulting
`CacheInvalidationPolicy.should_invalidate()`. Also note there is deliberately no same-tick "return the
cached object immediately" shortcut in `get_indexes()` at all (an earlier version of this mechanism had
one and it was found, in review, to be able to return a stale value for a dimension a prior same-tick
call had not yet resolved) — every call, partial or full, always runs the per-field resolution logic,
which is what makes `resolved_dimensions` correctness-bearing rather than merely a performance nicety.
Note explicitly that the `knowledge` domain's unconditional
always-invalidate-on-first-request-per-tick behavior is unchanged — this is a deliberate, still-documented
limitation, not something this ticket removed; only *repeated* same-tick requests for `knowledge_domain`
now avoid redundant rebuilds. Also correct the PAID-INFO and GUARD-SCAN paragraphs
(existing text says GUARD-SCAN's rejection reason was "no partial-dimension build path" — cite that
this is no longer true of the index as of this ticket, while noting GUARD-SCAN itself was not
retrofitted, per Out of Scope, so its shipped local-hoist behavior is unaffected). Add a short note to
§8.1 stating `WorldIndexService.get_indexes()` (`src/engine/world_index.py:105-138`) has the
structurally identical eager-all-5-dimensions shape but is not being given the same `dimensions`
parameter in this ticket, because its 3 `SpatialQueryService` call sites collectively exercise most of
its 5 dimensions every tick already (natural amortization `SemanticEntityQuery`, with zero production
callers, does not have).

**Do NOT touch:** any other section of `performance_contract.md` outside §8.1's new note and §8.2's
rewritten limitation/PAID-INFO/GUARD-SCAN paragraphs.

**Verify:** No automated test covers doc prose directly; verified by re-reading the edited section
against Steps 1-3's actual shipped behavior for accuracy (manual review, consistent with how
`docs/plans/idea_semantic_entity_index.md`'s superseded-by marker was verified in the prior ticket).

---

### Step 5 — Update parity ledger `INFRA-395`'s `v2_evidence`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed current entry at `docs/parity_ledger/infrastructure.yaml:11510-11530+` (`id:
INFRA-395`, `status: verified`, `priority: P1`). Append to `v2_evidence` (do not replace the existing
description of the original 5-dimension index) a description of: (a) the `apply.py` carry-forward line
from Step 1, (b) the `dimensions` parameter on `get_indexes()` from Step 2, (c) the `resolved_dimensions`
per-tick "already settled this dimension" bookkeeping field added to `SemanticEntityIndexes` in Step 2,
which ensures a dimension is rebuilt at most once per tick even across multiple same-tick
`SemanticEntityQuery` calls requesting it — and which, per Step 2's round-2 revision, is consulted on
*every* call (no same-tick early-return shortcut exists in `get_indexes()`), so a full request following
a same-tick partial request always correctly re-checks any dimension the partial request left unresolved
— (d) `SemanticEntityQuery`'s per-method single-dimension wiring from Step 3, and cite the new test node
IDs from Steps 1-3's Verify sections once they exist in the repo
(do this edit last, after Steps 1-3 land, so the cited test names are exact matches, not guesses).
`status` stays `verified`; `priority` stays `P1`; no `text` or `divergence_note` change (no
semantic/behavioral divergence — Parity Invariant requires identical query outputs, confirmed by the
bit-identical test from Step 1).

**Other writers to this shared resource (enumerated):** `docs/parity_ledger/infrastructure.yaml` is a
single YAML file with many independent entries maintained by many different tickets over time; the only
entry this step touches is `INFRA-395`. No other in-flight ticket in this session touches
`infrastructure.yaml` (confirmed by this session's own git status showing no other staged changes to
that file). Editing only the `v2_evidence` field of one existing entry, appending rather than
replacing, avoids any collision with unrelated entries in the same file.

**Do NOT touch:** any other entry in `infrastructure.yaml`; `status` or `priority` of `INFRA-395`
itself.

**Verify:**
- `tests/tools/test_parity_ledger_schema.py` (existing schema validator, must still pass — confirms the
  edited YAML stays schema-valid)

## Scope Guards

- Do not retrofit `paid_information.py`'s provider lookup or `military_conflict.py`'s guard scan into
  `SemanticEntityQuery` — both already ship working local-hoist alternatives
  (TCK-20260822-PAID-INFO-INDEX-RETROFIT, TCK-20260822-GUARD-SCAN-INDEX-RETROFIT); per the
  investigation's Central Open Question finding, PAID-INFO's blocker (a missing query-shape dimension)
  is not fixed by either of this ticket's changes anyway, so attempting it would be scope creep chasing
  an unrelated, unresolvable-by-this-ticket problem. Whether to migrate either call site onto the index
  after this ticket ships is a separate future ticket, not decided here.
- Do not invent a dedicated `DirtySet` tag for `information_providers` mutations to make `knowledge`
  invalidation conditional — Step 2 explicitly achieves selective building without touching
  `CacheInvalidationPolicy.should_invalidate("knowledge", ...)` at all; it stays unconditionally `True`
  whenever `knowledge_domain` is actually requested.
- Do not modify `src/engine/world_index.py`'s code (`WorldIndexService`, `CacheInvalidationPolicy`,
  `SpatialIndex`, `WorldIndexes`) — confirmed to share the identical eager-all-N shape, but its 3
  `SpatialQueryService` call sites already amortize the cost naturally; only a documentation note is
  added (Step 4), no code change.
- Do not restructure Kernel phase boundaries or move to an eager Persistence-phase write lifecycle — the
  lazy, pull-based `CacheInvalidationPolicy`-driven lifecycle stays exactly as
  TCK-20260822-SEMANTIC-ENTITY-INDEX designed it.
- Do not touch `CanonicalStateHasher`/`src/engine/checkpoint.py` — both fixes operate entirely within
  the non-authoritative derived-cache pattern; `semantic_entity_indexes` stays excluded from
  `to_canonical_data()` by omission, exactly as today.
- Do not change `SemanticEntityIndexes`' 5 original public field names (`tick`, `by_role_class`,
  `by_region`, `by_faction`, `by_need`, `by_knowledge_domain`), their types, or make any of them
  `Optional` — the `dimensions`-parameter approach (Step 2) was chosen specifically to avoid this; the
  dataclass stays fully populated on every return, at every call site, permanently. The one narrow
  exception, explicitly authorized by this plan's revision, is the new 6th field,
  `resolved_dimensions: FrozenSet[str]` (default `frozenset()`), added in Step 2 solely to track which
  dimensions have already been settled for the current tick — this is additive bookkeeping, not a change
  to any of the 5 original fields, and must not be conflated with them or used as a substitute for a
  `dimensions`/`Optional` change to the 5.
- Do not add a `dimensions` (or any new) parameter to `SemanticEntityQuery`'s 5 public method
  signatures — only their internal call to `get_indexes()` changes (Step 3).
- Do not touch any other field in `apply.py`'s `AuthoritativeState(...)` constructor call beyond the one
  new `semantic_entity_indexes=...` line (Step 1) — `apply.py` was an explicit Scope-Guard read-only
  file for the prior ticket and stays narrowly reopened here.
- Do not modify any other entry in `docs/parity_ledger/infrastructure.yaml` beyond `INFRA-395`'s
  `v2_evidence` field (Step 5).

## Dependency Map

- Step 1 (apply.py carry-forward) — independent, no dependency on Steps 2-5.
- Step 2 (get_indexes `dimensions` parameter) — independent of Step 1 (different file, different
  mechanism), but its "existing is None → always build" fallback behavior is most meaningfully exercised
  once Step 1 ships (otherwise `existing` is always `None` in production and every call still full-builds
  regardless of `dimensions`). Can be implemented and unit-tested in isolation before or after Step 1.
- Step 3 (SemanticEntityQuery wiring) — depends on Step 2 (needs the `dimensions` parameter to exist on
  `get_indexes()` before it can be passed).
- Step 4 (performance_contract.md) — depends on Steps 1-3 being functionally complete, so the doc
  accurately describes shipped behavior; content-wise it should be written last among the code/doc work,
  though the file itself does not block any other step.
- Step 5 (INFRA-395 v2_evidence) — depends on Steps 1-3's test node IDs existing in the repo (so the
  citation is exact), and should be done last.

Suggested execution order: Step 1 → Step 2 → Step 3 → Step 4 → Step 5. No step other than 3→2 and 5→(1,2,3)
is a hard blocker; the suggested order minimizes rework.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `semantic_entity_indexes` carried forward from `prior_state`; second-tick `get_indexes()` with no invalidated dimensions reuses prior tick's cached values by identity | Step 1 | `test_semantic_entity_indexes_carried_forward_across_ticks` |
| Only one invalidation domain dirty on a tick → other 4 dimensions NOT rebuilt across that tick's queries (rebuild-call spies) | Step 1 | `test_get_indexes_only_rebuilds_dirty_domains_across_ticks` |
| Caller requesting a single dimension via `SemanticEntityQuery` does not trigger rebuild of an invalidated-but-unrequested dimension | Steps 2, 3 | `test_single_dimension_query_does_not_rebuild_unrequested_invalidated_dimension` |
| (Same AC #3, regression case surfaced by Review round 1) A caller repeatedly requesting the SAME invalidated dimension within one tick triggers at most one rebuild, not one per call | Step 2 (points 5-7: `resolved_dimensions` tracking) | `test_repeated_same_tick_request_for_same_invalidated_dimension_builds_once` |
| (Same AC #3, correctness gap surfaced by Review round 2) A same-tick FULL request following an earlier same-tick PARTIAL request must still correctly re-check any dimension the partial request left unresolved, not return it stale | Step 2 (point 4: fast path removed entirely; points 5-7 run unconditionally on every call) | `test_full_request_after_partial_same_tick_rebuilds_invalidated_unresolved_dimension` |
| `docs/engine/performance_contract.md` §8.2 "Known limitation" updated to reflect new carried-forward, dimension-selective behavior | Step 4 | Manual review (no automated doc test) |
| `INFRA-395` `v2_evidence` updated to cite new mechanism and new test coverage | Step 5 | `tests/tools/test_parity_ledger_schema.py` |
| All existing tests in `test_semantic_entity_index.py` and `test_cache_invalidation_policy.py` continue to pass unmodified | Steps 1, 2, 3 (behavior-preservation constraint on every step) | Full scoped pytest runs per test_plan.md's "Scoped Pytest Commands" |

## Anti-Drift Notes

- **This is the hazard Review round 1 caught and remains a highly drift-prone edit in this plan:**
  it is easy to implement the "was this dimension requested" gate (Step 2 point 6's second and third
  OR'd clauses) and stop there, without also adding the `already_resolved` tracking (point 6's first
  clause, fed by points 5 and 7). That narrower version passes every test in test_plan.md's original
  7-test list, because none of them happen to exercise two separate same-tick calls requesting the *same*
  dimension while it is invalidated — but it silently reintroduces a per-call rebuild for that exact
  scenario, which is this ticket's whole reason for existing. Do not implement Step 2 without the
  `resolved_dimensions` field and the `already_resolved` computation; do not skip the
  `test_repeated_same_tick_request_for_same_invalidated_dimension_builds_once` test even though it is not
  in test_plan.md's original list — it exists specifically to guard this hazard, and was added after an
  architecture-reviewer NEEDS_CHANGES finding on an earlier version of this plan.
- **This is the hazard Review round 2 caught and is now the single most drift-prone edit in this plan,
  because it is a regression that is trivial to reintroduce by "helpfully simplifying" Step 2 later:**
  do NOT add back any same-tick early-return shortcut in `get_indexes()` — not the round-1 shape
  (`existing.tick == state.tick and dimensions is None → return existing`, which is exactly what Review
  round 2 rejected because it can return a stale value for a dimension an earlier same-tick partial
  request never touched), and not the completeness-check alternative considered and explicitly rejected
  in Step 2's Design Decision round 2 (`dimensions is None and existing.resolved_dimensions ==
  _ALL_DIMENSIONS`) — the latter is not wrong so much as redundant and an extra place to keep in sync
  with `resolved_dimensions`' semantics, for no real savings over just letting the per-field ternaries
  run. **Every call to `get_indexes()`, partial or full, must always fall through to compute
  `already_resolved` and run the 5 per-field ternaries** — that is the only place in this mechanism that
  is allowed to decide "return the existing value for this dimension." Do not skip
  `test_full_request_after_partial_same_tick_rebuilds_invalidated_unresolved_dimension` — it exists
  specifically to catch a reintroduced shortcut of either shape, and was added after this second
  architecture-reviewer NEEDS_CHANGES finding.
- Do not conflate the two vocabularies introduced in Step 2: `dimensions` values (`"role_class"`,
  `"region"`, `"faction"`, `"need"`, `"knowledge_domain"` — one per dataclass field) are distinct strings
  from `CacheInvalidationPolicy` domain names (`"identity"`, `"region"`, `"needs"`, `"knowledge"` — note
  `"needs"` vs `"need"` and the many-to-one `role_class`/`faction` → `"identity"` mapping already present
  in the pre-existing code). `_DIMENSION_TO_DOMAIN` exists specifically to keep this mapping explicit and
  in one place rather than duplicated inline per field. `resolved_dimensions` (point 2) uses the same
  "dimension name" vocabulary as `dimensions`, not the `CacheInvalidationPolicy` domain vocabulary — do
  not store domain names (`"identity"`/`"needs"`/etc.) into `resolved_dimensions` by mistake.
- `existing.tick == state.tick` will almost never be true across ticks even after carry-forward, because
  `new_state.tick` is incremented relative to the carried `existing.tick` — this is expected (confirmed
  by symmetry with `world_indexes`' identical behavior in the investigation) and is why the per-dimension
  ternaries are what carry the actual carry-forward benefit cross-tick (there is no separate fast path
  as of Step 2's round-2 revision — see above). Within a single tick, however, `existing.tick ==
  state.tick` becomes `True` starting from the second call onward (since the first call's `new_indexes`
  is written back with `tick=state.tick`) — this is exactly the condition `already_resolved` (point 5)
  depends on to have any effect at all.
- `SemanticEntityIndexes` remains fully populated on its 5 original fields (no `None`/missing values) on
  every return from `get_indexes()`, at every call site, forever — this was a deliberate Step 2 design
  choice to avoid blast-radius on every existing test that reads `.by_region`/`.by_role_class`/etc.
  directly assuming a populated dict. The new 6th field, `resolved_dimensions`, does not change this —
  it is bookkeeping metadata, not a 6th "dimension" in the query sense, and no `SemanticEntityQuery`
  method should ever read or expose it. Do not let a later drift toward `Optional` fields on the original
  5 creep in without re-opening this ticket's design decision explicitly.
- `WorldIndexService`/`world_index.py` code is genuinely out of scope here — resist "fixing it too while
  we're at it," even though the shape is identical, per the ticket's own Out-of-Scope guard and the
  investigation's amortization finding. Note this also means `WorldIndexService` does NOT get the
  `resolved_dimensions`-style fix from this Review round either — it never had a `dimensions` parameter
  to begin with, so it cannot exhibit this exact hazard, and remains untouched per the existing Scope
  Guard.

## Deviations (post-Implement)

- **Step 1's Verify pass surfaced a static-guard false positive the plan did not anticipate.**
  `tests/static/test_semantic_entity_index_no_stateupdate_write.py` greps `src/` for any
  `semantic_entity_indexes=` line and fails unless the line matches one of a small whitelist
  (`self.semantic_entity_indexes`, the dataclass field declaration, or `object.__setattr__`). The
  new `apply.py` carry-forward line from Step 1 matched none of those and failed the test. This is
  not a real architecture violation — the guard's own docstring states its purpose is to forbid a
  `StateUpdate`/`.replace()`-driven write that would promote the field to authoritative state, and
  the `apply.py` line is neither: it is `ApplyPath.apply_generation`'s own `AuthoritativeState(...)`
  constructor passing a non-authoritative derived-cache value through unchanged by `getattr`,
  structurally identical to the pre-existing, unguarded `world_indexes=getattr(prior_state,
  "world_indexes", None)` line at the exact same call site (confirmed: no equivalent static guard
  exists for `world_indexes` at all — the field-specific guard for `semantic_entity_indexes` simply
  predates this ticket's legitimate carry-forward addition). Fixed by adding one narrowly-scoped
  whitelist condition to the guard (matching the literal `getattr(prior_state,
  "semantic_entity_indexes", None)` pattern) and updating its docstring to document the extension,
  rather than loosening the pattern-matching in a way that could admit a real future violation. This
  is a correction to a stale guard whitelist that the plan's Step 1 could not have anticipated (the
  guard postdates the plan's own investigation of `apply.py`'s carry-forward mechanics), not a
  substantive work-around of a real architectural finding. No other step deviated from this plan.
