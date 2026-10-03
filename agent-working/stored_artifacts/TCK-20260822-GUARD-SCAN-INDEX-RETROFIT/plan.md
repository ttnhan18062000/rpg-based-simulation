---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260822-GUARD-SCAN-INDEX-RETROFIT
artifact_type: plan
tags: [faction, grand-strategy, performance]
---

# Implementation Plan — TCK-20260822-GUARD-SCAN-INDEX-RETROFIT

## Summary

The hotspot is `MilitaryConflictPhase._find_guard_entities_in_region` (`src/engine/military_conflict.py:121-137`),
a full `O(N)` scan over `state.entities` called once per WAR pair inside `execute()`'s siege loop
(`military_conflict.py:304-307`), giving `O(N × war_pair_count)` per tick. This plan eliminates the
per-pair rescan by hoisting a single `region_id -> sorted [GUARD entity id]` dict, built with one pass
over `state.entities` at the top of `execute()`, then doing dict lookups per WAR pair inside the
existing siege loop — bounding the scan to `O(N)` once per tick regardless of `war_pair_count`.

This plan deliberately does **not** route through `SemanticEntityQuery.by_region`
(`src/engine/semantic_entity_index.py:122-152`) — see "Design Decision" below for the evidence. Three
new tests cover the previously-uncovered `>=3`-GUARD reinforcement branch and the squad-commitment
(cap 5) branch (AC #2, AC #3), one new test proves output-identity with the pre-change scan (AC #1),
and `docs/parity_ledger/faction.yaml` FAC-008's `test_path`/`v2_evidence` and
`docs/engine/performance_contract.md` §8.2 are updated to reflect the shipped mechanism and corrected
test coverage (AC #4).

### Design Decision — local per-`execute()` hoist, not `SemanticEntityQuery.by_region`

Read `src/engine/semantic_entity_index.py:122-152` (via investigation.md) and
`src/engine/semantic_entity_index.py:47-73`/`world_index.py:46-48` (via investigation.md): confirmed
`SemanticEntityIndexService.get_indexes()` has no partial/single-dimension build path — any query call
rebuilds all 5 dimensions whenever `CacheInvalidationPolicy.should_invalidate(domain, dirty)` is true,
and that function returns `True` unconditionally when `dirty is None`. `military_conflict.py`'s call
site must pass `dirty=None`, because `pipeline.py` builds `DirtySet` only *after* `military_conflict`
runs (`dirty_builder.build()` at `pipeline.py:262`, confirmed by investigation.md's citation of that
line ordering) — so every tick's first `by_region(...)` call inside `execute()` would pay for
rebuilding all 5 index dimensions (`by_role_class`, `by_faction`, `by_need`, `by_knowledge_domain` in
addition to `by_region`), roughly 5x the cost of today's plain `O(N)` scan. That cost is amortized only
across multiple WAR pairs sharing the same tick-scoped cache within one `execute()` call — and
investigation.md confirms (grep across `test_faction_campaign.py::_make_initial_state`,
`test_siege_model.py`, `test_war_exhaustion.py`, `test_territory_transfer.py`, `test_siege_ledger.py`)
every existing shipped scenario has exactly **one** WAR pair active per tick, never more. `grep -rn
"SemanticEntityQuery" src/` (confirmed by investigation.md) also shows zero production callers today —
this retrofit would be the index's first production consumer, paying the full 5x rebuild tax for a
single dimension used by a single query, once per tick, in every real shipped scenario. **For the
actual common case this is a net performance regression, not a win** — the opposite of what a
"performance retrofit" ticket should ship.

`by_region`'s alternative, `by_role_class`, was also ruled out (investigation.md, Current Behavior):
its key is `(role, class_id)` with no region dimension at all, so it would still need a second
in-memory `region_id` filter on top, buying nothing over `by_region` while adding a fragile dependency
on `class_id_by_role`'s single-value-for-GUARD content-data fact
(`data/content/spawn_tables.yaml:17`) that the schema does not enforce (`IdentityComponent.class_id`
is a free-form `str`, `src/core/state.py:482`).

This mirrors `TCK-20260822-PAID-INFO-INDEX-RETROFIT`'s own resolution (`stored_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/plan.md`,
Design Decision): that ticket hit a *dimension* mismatch and hoisted a local sort instead of routing
through the index; this ticket hits a *cost* mismatch (the dimension fits, but the index's all-or-
nothing rebuild cost does not, for the real single-WAR-pair workload) and resolves it the same way —
hoist locally, don't force the wire-in. A local `Dict[str, List[int]]` built with one pass over
`state.entities` at the top of `execute()` achieves the ticket's real goal (bound the scan to `O(N)`
once per tick, not `O(N × war_pair_count)`) without the 5x tax and without taking on a dependency on
`SemanticEntityIndexService`'s tick-cache lifecycle (whose cross-tick non-carry-forward limitation is
a separate, pre-existing, out-of-scope issue per investigation.md's Anti-Drift Hazards). This is the
plan's design call, made on the investigation's own performance evidence — no further stakeholder
check-in is required for it, matching how PAID-INFO's equivalent deviation was accepted and documented
rather than escalated.

## Steps

### Step 1 — Hoist the GUARD-entity scan out of the per-WAR-pair loop

**Files:** `src/engine/military_conflict.py`

**Change:** Confirmed current code by direct read (`military_conflict.py:121-137` for the scan,
`military_conflict.py:304-307` for the call site inside the siege loop at lines 232-334):

```python
@staticmethod
def _find_guard_entities_in_region(
    state: AuthoritativeState,
    region_id: str,
) -> List[int]:
    """Return sorted list of entity IDs with EntityRole.GUARD in the given region."""
    result: List[int] = []
    for eid, entity in state.entities.items():
        nav = getattr(entity, "navigation", None)
        if nav is None or nav.region_id != region_id:
            continue
        identity = getattr(entity, "identity", None)
        if identity is None:
            continue
        if identity.role == EntityRole.GUARD:
            result.append(eid)
    return sorted(result)
```
called once per WAR pair at line 304-307:
```python
guard_ids = MilitaryConflictPhase._find_guard_entities_in_region(
    state, contested_region_id
)
```

Replace with: (a) a new private helper `_build_guard_index_by_region(state) -> Dict[str, List[int]]`
that does a single pass over `state.entities.items()` (same `getattr(..., None)` defensive checks,
same `identity.role == EntityRole.GUARD` filter), appending each matching `eid` into
`result.setdefault(nav.region_id, []).append(eid)`, then sorting each region's list before returning
— i.e. identical per-region filtering logic to today's function, just bucketed by region in one pass
instead of re-filtered by region on every call; (b) call this helper exactly once, at the top of
`execute()` immediately after the `if not state.factions: return StateUpdate()` guard (line 166-167)
and before `world_updates: Dict[str, WorldUpdate] = {}` (line 172), storing the result in a local
`guard_ids_by_region: Dict[str, List[int]] = MilitaryConflictPhase._build_guard_index_by_region(state)`;
(c) replace the per-pair call site (lines 304-307) with a dict lookup:
`guard_ids = guard_ids_by_region.get(contested_region_id, [])`. Keep
`_find_guard_entities_in_region(state, region_id)` itself in place, unchanged, as a thin wrapper
delegating to the new helper (`return MilitaryConflictPhase._build_guard_index_by_region(state).get(region_id, [])`)
so any external caller or test that still calls it directly by name continues to get identical
per-region output — this preserves the existing public method signature or removes the method (see
Verify below).

Output for every `(region_id, guard_ids)` pair is identical to today's per-call scan: same filter
predicate (`nav.region_id == region_id and identity.role == EntityRole.GUARD`), same `sorted()` call
per region, same handling of entities missing `navigation`/`identity` (skipped, matching the existing
`getattr(..., None)` guards). The siege loop's downstream use of `guard_ids`
(`len(guard_ids) >= _DEF_ENTITY_THRESHOLD` at line 308, `guard_ids[:_MAX_SQUAD_SIZE]` at line 316) is
untouched — both operate on a `List[int]`, which `guard_ids_by_region.get(contested_region_id, [])`
still returns.

**Other writers to the shared resource this step reads (`state.entities`):** Enumerated by reading
`src/core/state.py:665-692` (`EntityState`/`AuthoritativeState` are frozen dataclasses) plus
investigation.md's citation that `_find_guard_entities_in_region` and its call site are the only
GUARD/entity-scanning code in `military_conflict.py`. `state.entities` is a field on the frozen
`AuthoritativeState` passed into `execute(state)` — nothing can mutate it mid-call (same immutability
argument PAID-INFO's plan made for `state.information_providers`, `state.py`). No other function in
`military_conflict.py` (`get_war_pairs`, `_find_contested_region`, the orphan-cleanup loop at lines
178-195, the exhaustion-drain loop at lines 201-229, the territory-transfer block at lines 253-277)
reads or writes `state.entities` at all — confirmed by direct read of the full file above. No other
module writes to `state.entities` within a single tick's `execute()` call — entity mutations flow
through `StateUpdate.entity_updates`, applied by `ApplyPath` only between ticks, never visible inside
one `execute()` invocation. The hoist is safe: `guard_ids_by_region` is computed once from a value
that cannot change for the duration of `execute()`.

**Do NOT touch:** `get_war_pairs` (lines 48-63), `_find_contested_region` (lines 65-119), the orphan
siege-cleanup loop (lines 178-195), the exhaustion-drain loop (lines 201-229), the territory-transfer
block (lines 253-277), the siege-initiation/degradation block (lines 279-302), the
`EntityRole`/`identity.role` comparison semantics, `_DEF_ENTITY_THRESHOLD`/`_MAX_SQUAD_SIZE` constants,
`class_id`/`spawn_tables.yaml` (must not become a load-bearing assumption per investigation.md's
Anti-Drift Hazards).

**Verify:** All existing `MilitaryConflictPhase` siege-loop tests in `test_siege_model.py` (4 tests:
`test_military_conflict_initiates_siege_on_first_tick`, `test_military_conflict_emits_degradation_delta`,
`test_military_conflict_resumes_existing_siege`, `test_military_conflict_noop_when_no_war`) and all 6
tests in `test_military_conflict_phase.py` pass unmodified — they use `_FakeState` with
`entities={}` default, which the new helper must handle without raising (empty dict → empty
`guard_ids_by_region`, `.get(region_id, [])` returns `[]`, matching today's behavior of an empty
`state.entities` producing an empty scan result).

---

### Step 2 — Add naive-scan parity test (AC #1)

**Files:** `tests/unit/domains/faction/test_siege_model.py`

**Change:** Add `test_guard_index_matches_naive_full_scan` to the "MilitaryConflictPhase siege loop
(E53Cb integration)" section (after `test_military_conflict_noop_when_no_war`, line 269-onward).
Build a `_FakeState` (reusing the file's existing `_FakeState`/`_make_faction`/`_make_region` helpers,
confirmed at `test_siege_model.py:12-56`) with an `entities` dict containing a mix of GUARD
(`EntityRole.GUARD = 5`, `src/core/enums.py:6-12`) and non-GUARD (`HERO`, `MONSTER`, `WORKER`)
`EntityState` instances (constructed via `EntityState(id=..., kind="npc", identity=IdentityComponent(role=...),
navigation=NavigationComponent(region_id=...))`, confirmed field shapes at `src/core/state.py:665-692`,
`358-377`, `471-482`) spread across at least 2 distinct `region_id` values. Call
`MilitaryConflictPhase._find_guard_entities_in_region(state, region_id)` for each region and assert
the result equals a locally-written naive reference implementation (a copy of the pre-Step-1 loop body,
kept only inside this test function, not in production code) — asserting exact list equality (order
included), not just set equality, to catch a sort-order regression. Include one region with zero GUARD
entities (asserts `[]`) and confirm entities with no `navigation`/`identity` component are excluded
(construct one via `EntityState(id=..., kind="npc")` relying on the `default_factory` component
defaults, which real entities always have per `src/core/state.py:673-686` — non-`None` — this exercises
the defensive `getattr(..., None)` branch as dead-but-safe code, matching the existing production
files' hand-rolled `_FakeState` doubles' expectations).

**Do NOT touch:** any other test in the file; do not remove or rename the existing `_FakeState` class
or its helpers.

**Verify:** New test passes; depends on Step 1 (exercises the retrofitted lookup path). Run:
`.venv/bin/python3 -m pytest tests/unit/domains/faction/test_siege_model.py -v`.

---

### Step 3 — Add reinforcement-branch tests (AC #2)

**Files:** `tests/unit/domains/faction/test_siege_model.py`

**Change:** Add two tests to the same section: `test_military_conflict_reinforcement_fires_at_three_guards`
and `test_military_conflict_reinforcement_does_not_fire_below_threshold`. Both build a `_FakeState`
with one WAR pair (`fa` vs `fb`, `fb` owning territory `["r2"]`, matching the existing
`test_military_conflict_emits_degradation_delta` fixture shape at `test_siege_model.py:228-244`) and
an `entities` dict placing GUARD entities in region `"r2"` via `NavigationComponent(region_id="r2")` +
`IdentityComponent(role=EntityRole.GUARD)`.
- `test_military_conflict_reinforcement_fires_at_three_guards`: exactly 3 GUARD entities in `"r2"`.
  Call `MilitaryConflictPhase.execute(state)` and assert
  `result.world_updates["r2"].service_availability_delta == _SIEGE_SVC_DELTA + _DEF_SVC_DELTA ==
  -0.05 + 0.02 == -0.03` and `siege_progress_delta == _SIEGE_PROGRESS_DELTA + _DEF_PROGRESS_DELTA ==
  0.05 - 0.02 == 0.03` (both deltas from `military_conflict.py:26-31`'s module constants — import them
  from the module under test rather than hardcoding literals twice, matching the file's existing style).
- `test_military_conflict_reinforcement_does_not_fire_below_threshold`: exactly 2 GUARD entities in
  `"r2"`. Assert only the base degradation delta applies: `service_availability_delta == _SIEGE_SVC_DELTA
  == -0.05`, `siege_progress_delta == _SIEGE_PROGRESS_DELTA == 0.05` (no `+0.02`/`-0.02` offset).

**Do NOT touch:** the reinforcement threshold constant `_DEF_ENTITY_THRESHOLD` or its comparison
operator (`>=`, `military_conflict.py:308`) — this is a coverage-only step, not a behavior change; AC
#1 requires identical output to the pre-existing implementation.

**Verify:** Both new tests pass; depend on Step 1 (they exercise `execute()`'s call site after the
hoist, but would pass equally against the pre-Step-1 code since Step 1 preserves output — their
primary value is closing the AC #2 zero-coverage gap identified in investigation.md, not proving the
hoist itself).

---

### Step 4 — Add squad-commitment tests (AC #3)

**Files:** `tests/unit/domains/faction/test_siege_model.py`

**Change:** Add three tests to the same section, reusing the same WAR-pair/region fixture shape as
Step 3: `test_military_conflict_squad_commitment_capped_at_five`,
`test_military_conflict_squad_commitment_no_truncation_at_five`,
`test_military_conflict_squad_commitment_empty_when_no_guards`.
- `..._capped_at_five`: 7 GUARD entities (ids chosen non-sequentially, e.g. `101..107`, so a sort-order
  bug would be caught) placed in `"r2"`. Call `execute()`, assert `result.groups_add_or_update` has
  exactly one `GroupRecord`, `len(group.member_ids) == 5`, `group.roles == {eid: "FACTION_SQUAD" for
  eid in <5 lowest ids>}`, and `group.member_ids == set(<5 lowest ids>)` — confirming
  `squad_ids = guard_ids[:_MAX_SQUAD_SIZE]` (`military_conflict.py:316`) slices the *sorted* list, so
  the 5 lowest entity IDs are committed, not an arbitrary 5.
- `..._no_truncation_at_five`: exactly 5 GUARD entities. Assert one `GroupRecord` with all 5 members,
  no truncation (boundary case for the `<=` vs `<` cap behavior).
- `..._empty_when_no_guards`: 0 GUARD entities in the contested region (only non-GUARD entities, or an
  empty `entities` dict). Assert `result.groups_add_or_update == []` — no `GroupRecord` created.

**Do NOT touch:** `_MAX_SQUAD_SIZE`, `GroupRecord`'s field shape (`src/core/state.py`, imported locally
inside `execute()` at line 169 — confirmed by direct read, not re-verified here since this step only
asserts against it, doesn't construct or modify it), or the `roles`/`anchor`/`group_id` construction
logic (`military_conflict.py:317-332`).

**Verify:** All three new tests pass; depend on Step 1 for the same reason as Step 3 (exercises the
post-hoist call site; behavior is unchanged from pre-Step-1, so this closes the AC #3 zero-coverage gap
identified in investigation.md).

---

### Step 5 — Correct FAC-008's `test_path` and `v2_evidence`

**Files:** `docs/parity_ledger/faction.yaml`

**Change:** Confirmed current FAC-008 entry (`faction.yaml:145-164`, read directly for this plan):
`test_path: tests/unit/domains/faction/test_siege_model.py` and `v2_evidence` citing
`_find_guard_entities_in_region`. Since `test_siege_model.py` is still where all of Steps 2-4's new
tests live (no new file introduced), `test_path` itself does not need to change file — but it currently
under-specifies coverage: the entry's `text` field describes exactly the ≥3-GUARD reinforcement offset,
which (per investigation.md, confirmed by grep) had **zero** test coverage before this ticket. Update
`v2_evidence` to append a short clause naming the new tests added in Steps 2-4 by name
(`test_guard_index_matches_naive_full_scan`, `test_military_conflict_reinforcement_fires_at_three_guards`,
`test_military_conflict_reinforcement_does_not_fire_below_threshold`,
`test_military_conflict_squad_commitment_capped_at_five`,
`test_military_conflict_squad_commitment_no_truncation_at_five`,
`test_military_conflict_squad_commitment_empty_when_no_guards`) and stating that
`_find_guard_entities_in_region` is now backed by `_build_guard_index_by_region`, a single-pass
per-`execute()` hoist (not `SemanticEntityQuery`), mirroring how `TOWN-182` was updated in
`TCK-20260822-PAID-INFO-INDEX-RETROFIT` (`stored_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/plan.md`,
Deviations section). Leave `status: verified`, `priority: P1`, and `text` unchanged — no semantic
divergence was introduced (AC #1 requires identical output).

**Other writers to this shared resource (`docs/parity_ledger/faction.yaml`):** grep confirms FAC-009
(siege state shape, `faction.yaml:166+`), FAC-010 (territory transfer), and FAC-011 (exhaustion drain)
are adjacent entries in the same file citing the same source file (`military_conflict.py`) but disjoint
functions/behaviors (per investigation.md's Parity Ledger Overlap section) — this step edits only the
FAC-008 entry's `v2_evidence` field and must not alter FAC-009/010/011's text, status, or evidence.

**Do NOT touch:** FAC-009, FAC-010, FAC-011 entries; FAC-008's `status`, `priority`, `text`, or
`legacy_evidence` fields.

**Verify:** No automated test covers YAML prose directly; verify by re-reading the edited entry for
accuracy against Steps 1-4's actual shipped code and test names once those steps are complete. If a
frontmatter/parity-ledger schema check exists in the pipeline (`validate_frontmatter.py` or similar),
it must still pass against `faction.yaml`'s schema (`docs/parity_ledger/schema.json`).

---

### Step 6 — Update `docs/engine/performance_contract.md` §8.2

**Files:** `docs/engine/performance_contract.md`

**Change:** Confirmed current §8.2 text (`performance_contract.md:93-111`, read directly for this
plan) already narrates the PAID-INFO precedent in a matching paragraph shape ("The live
`paid_information.py` seeker/provider hotspot was retrofitted by
`TCK-20260822-PAID-INFO-INDEX-RETROFIT`, but **not** by routing through `SemanticEntityQuery`: ...").
Add a new sentence/short paragraph immediately after that existing PAID-INFO paragraph (before
"**Lifecycle**", line 113), following the same pattern: state that
`TCK-20260822-GUARD-SCAN-INDEX-RETROFIT` retrofitted `MilitaryConflictPhase._find_guard_entities_in_region`
(`src/engine/military_conflict.py`)'s per-WAR-pair `O(N)` scan by hoisting a single per-`execute()`
`region_id -> sorted [GUARD entity id]` dict (`_build_guard_index_by_region`), **not** by routing
through `SemanticEntityQuery.by_region`, and cite the reason: `by_region` is the correct index
dimension for this call site (unlike PAID-INFO's dimension mismatch), but
`SemanticEntityIndexService.get_indexes()` has no partial-dimension build path — any query call
rebuilds all 5 dimensions, and this call site would be the index's first production caller with no
same-tick amortization in any shipped scenario (every existing scenario has exactly one WAR pair per
tick), making a literal `by_region` wire-in a net regression versus the local hoist for the real
workload.

**Do NOT touch:** §8.1, the rest of §8.2's dimension list/description (lines 93-100), the PAID-INFO
paragraph itself, the "Lifecycle", "`identity_entities` DirtySet tag", "Determinism", or "Known
limitation" paragraphs (lines 113-144+) — none of those describe this ticket's call site and none are
touched by this plan.

**Verify:** No automated test covers doc prose; verify by re-reading the edited paragraph for accuracy
against Step 1's actual shipped code once Step 1 is complete.

## Scope Guards

- Do not touch `_find_contested_region` (`military_conflict.py:65-119`), `get_war_pairs`
  (`military_conflict.py:48-63`), the orphan siege-cleanup loop (lines 178-195), the exhaustion-drain
  loop (lines 201-229), or the territory-transfer block (lines 253-277) — all confirmed out of scope by
  investigation.md's Anti-Drift Hazards, despite sharing the same source file as FAC-009/010/011.
- Do not touch `src/domains/faction/diplomatic_state_machine.py` or `src/engine/faction_decision.py` —
  explicitly Out of Scope per the ticket (confirmed by investigation to have zero entity/GUARD scanning
  or an O(faction-pairs), not O(N)-entity-scan, shape).
- Do not build a new `SemanticEntityIndexes` dimension in `src/engine/semantic_entity_index.py`, and do
  not route `_find_guard_entities_in_region`/`_build_guard_index_by_region` through
  `SemanticEntityQuery.by_region` or `by_role_class` — this plan's Design Decision explicitly rejected
  both, citing the 5x-rebuild-with-no-amortization finding.
- Do not hardcode `class_id == "WARRIOR"` as a substitute for `identity.role == EntityRole.GUARD` — a
  content-data fact (`data/content/spawn_tables.yaml:17`), not a schema guarantee (investigation.md
  Anti-Drift Hazards).
- Do not change the ≥3-GUARD reinforcement threshold, the squad-commitment cap of 5, or any of
  `_SIEGE_SVC_DELTA`/`_SIEGE_PROGRESS_DELTA`/`_DEF_SVC_DELTA`/`_DEF_PROGRESS_DELTA`'s numeric values —
  AC #1 requires byte-identical output to the pre-change scan; any value change would be an
  undocumented mechanics divergence.
- Do not touch `docs/mechanics/01_entity_anatomy.md`, `04_strategic_cognition.md`, or
  `05_world_evolution.md` — investigation.md confirmed none document this mechanic; no Mechanics Bible
  update is required.
- Do not add a `docs/guidelines/intentional_divergences.md` entry — no behavior change is introduced
  (AC #1).
- Do not touch FAC-009, FAC-010, or FAC-011 in `docs/parity_ledger/faction.yaml` — adjacent entries in
  the same file, disjoint behaviors.
- Do not touch `TCK-20260822-SEMANTIC-ENTITY-INDEX`'s cross-tick carry-forward known limitation
  (`AuthoritativeState.semantic_entity_indexes` not carried across ticks) — pre-existing, out of scope,
  and irrelevant to this plan since it does not use the index at all.
- Do not modify `_FakeState`, `_make_faction`, or `_make_region` helpers in `test_siege_model.py` — new
  tests add an `entities=` argument to `_FakeState(...)` (already supported per the constructor at
  `test_siege_model.py:52`) without changing the helper definitions themselves.

## Dependency Map

- Step 1 has no dependencies — pure code change, independently verifiable against the existing 4
  `test_siege_model.py` siege-loop tests and 6 `test_military_conflict_phase.py` tests (AC #1's
  regression-preservation half).
- Steps 2, 3, and 4 each depend on Step 1 being applied (they exercise the post-hoist call site,
  though Steps 3-4's assertions would also pass against the pre-Step-1 code since output is
  unchanged — their real dependency is only that Step 1 doesn't break the fixtures they build on). Steps
  2, 3, and 4 are independent of each other and can be done in any order once Step 1 lands.
- Step 5 depends on Steps 2-4 being complete (it cites their test names by name).
- Step 6 depends on Step 1 being complete (the doc text must describe the actual shipped mechanism).
  Independent of Steps 2-5 otherwise.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — index-backed replacement returns identical sorted `List[int]` to current full-scan, verified by mixed-entity/multi-region test | Step 1 (hoist), Step 2 (parity test) | `test_guard_index_matches_naive_full_scan`; existing 4 `test_siege_model.py` siege-loop tests + 6 `test_military_conflict_phase.py` tests pass unmodified |
| AC #2 — reinforcement branch fires +0.02/-0.02 when >=3 GUARD entities present | Step 3 | `test_military_conflict_reinforcement_fires_at_three_guards`, `test_military_conflict_reinforcement_does_not_fire_below_threshold` |
| AC #3 — squad commitment produces `GroupRecord` capped at 5 when >5 GUARD entities present | Step 4 | `test_military_conflict_squad_commitment_capped_at_five`, `test_military_conflict_squad_commitment_no_truncation_at_five`, `test_military_conflict_squad_commitment_empty_when_no_guards` |
| AC #4 — FAC-008's `v2_evidence`/`test_path` updated to cite new/corrected test coverage | Step 5 | N/A — doc/ledger edit, verified by re-read, not a test |

## Anti-Drift Notes

- The central risk the investigation flagged — being pushed into `SemanticEntityQuery.by_region` "for
  architectural consistency" because the ticket's Scope text literally says "a lookup against the
  semantic entity index" — is resolved by this plan's Design Decision, not deferred: the local hoist is
  chosen precisely because `SemanticEntityIndexService.get_indexes()` has no partial-dimension build
  path, and this call site would be the index's first-ever production caller, paying a ~5x rebuild cost
  for one dimension with zero same-tick amortization in any shipped scenario (every scenario has
  exactly one WAR pair per tick). Do not revisit this mid-implementation by wiring into
  `SemanticEntityQuery` "since Scope says so" — that literal reading was evaluated and rejected here
  with cited evidence, the same way `PAID-INFO-INDEX-RETROFIT` deviated from its own Scope wording and
  documented it rather than following it blindly.
- `class_id_by_role`'s single-value-for-GUARD content fact (`data/content/spawn_tables.yaml:17`) must
  never become a load-bearing assumption in `_build_guard_index_by_region` — filtering must stay on
  `identity.role == EntityRole.GUARD`, never on `class_id == "WARRIOR"`, even though today's shipped
  content makes the two sets equal.
- `state.entities` is read once per `execute()` call by the new hoist; if a future change needs the
  hoisted dict to reflect a mid-`execute()` mutation, that would mean `AuthoritativeState` is no longer
  actually frozen for the duration of one `execute()` call — treat that as a bug to investigate
  separately, not something to patch around inside this call site (mirrors PAID-INFO's identical note
  about `state.information_providers`).
- Multiple existing test files construct `_FakeState`/hand-rolled state doubles with `entities={}` by
  default (`test_siege_model.py`, `test_military_conflict_phase.py`, `test_war_exhaustion.py`,
  `test_territory_transfer.py`, `test_siege_ledger.py`) — `_build_guard_index_by_region` must handle an
  empty `entities` dict without raising, returning `{}`, so `.get(region_id, [])` degrades to `[]`
  exactly as today's per-call scan does on an empty world.
- Keep `_find_guard_entities_in_region(state, region_id)` present as a name (even if reimplemented as a
  thin wrapper around `_build_guard_index_by_region`) — Step 2's parity test and any other future direct
  caller expects this method name to keep working with the same 2-argument signature and return type
  (`List[int]`, not the index's native tuple type, matching how PAID-INFO's Test #4-equivalent guard
  checked `SemanticEntityQuery`'s tuple leakage — the same care applies here even though this plan
  doesn't use `SemanticEntityQuery` at all).

## Deviations

- **Added a new `SOC-245` cross-reference entry to `docs/parity_ledger/social_narrative.yaml`, not
  planned in the original Steps.** `src/engine/military_conflict.py`'s canonical parity record for
  this ticket's mechanic is `FAC-008` in `docs/parity_ledger/faction.yaml` — but `faction.yaml` is
  not one of the 8 files in `tools/parity_ledger_scan.py::CANONICAL_LEDGER_FILES`, which is the only
  set `tools/gate_checks/parity_updater_static.py`'s cross-reference check scans. Since
  `military_conflict.py` is *also* cited (for unrelated code — `SIEGE_BEGINS` WorldEvent emission,
  `SOC-FAC-007`) in the canonical `social_narrative.yaml`, the orchestrator-run cross-reference gate
  required a genuine touch to that file when this ticket's diff landed, even though the actual
  correct documentation already existed, complete and accurate, in `FAC-008`. Rather than fabricate a
  second description of the GUARD-scan mechanic in `social_narrative.yaml` (duplicating/risking
  drift from `FAC-008`), added `SOC-245`: a minimal, genuinely true cross-reference entry pointing to
  `FAC-008` as the authoritative record, satisfying the gate with honest content. This is a real,
  structural gap in the parity-ledger tooling (`faction.yaml` predates the 8-canonical-file
  convention and was never folded in) — flagged for a separate follow-up hotfix ticket, not fixed
  here (out of scope for this ticket to restructure shared ledger tooling).
