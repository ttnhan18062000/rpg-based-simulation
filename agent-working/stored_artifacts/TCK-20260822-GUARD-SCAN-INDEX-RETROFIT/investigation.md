---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260822-GUARD-SCAN-INDEX-RETROFIT
artifact_type: investigation
tags: [faction, grand-strategy, performance]
---

# Investigation — TCK-20260822-GUARD-SCAN-INDEX-RETROFIT

## Current Behavior

**`MilitaryConflictPhase._find_guard_entities_in_region`** (`src/engine/military_conflict.py:121-137`):
```python
@staticmethod
def _find_guard_entities_in_region(state, region_id) -> List[int]:
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
Full `O(N)` scan over `state.entities` (every entity in the world), filtered to `nav.region_id ==
region_id` and `identity.role == EntityRole.GUARD`. Returns a sorted `List[int]`.

**Call site** (`src/engine/military_conflict.py:304-307`), inside `execute()`'s siege loop, which
iterates `war_pairs` (one entry per WAR faction dyad, `get_war_pairs()` at lines 48-63):
```python
guard_ids = MilitaryConflictPhase._find_guard_entities_in_region(state, contested_region_id)
if len(guard_ids) >= _DEF_ENTITY_THRESHOLD:   # >= 3
    wu = wu.merge(WorldUpdate(service_availability_delta=+0.02, siege_progress_delta=-0.02))
squad_ids = guard_ids[:_MAX_SQUAD_SIZE]        # cap 5
if squad_ids:
    groups_add.append(GroupRecord(..., member_ids=set(squad_ids), roles={eid: "FACTION_SQUAD" ...}))
```
`execute()` itself runs **once per tick** from `pipeline.py:227-233` (`MilitaryConflictPhase.execute(state)`,
no `dirty`/index argument passed). The `O(N)` scan therefore runs once **per WAR pair**, inside that
single `execute()` call — i.e. `O(N × war_pair_count)` per tick, confirming the ticket's own
correction of the original per-tick framing. In every existing test and integration scenario
(`test_faction_campaign.py::_make_initial_state`, `test_siege_model.py`, `test_war_exhaustion.py`,
`test_territory_transfer.py`, `test_siege_ledger.py`) there is exactly **one** WAR pair active at a
time — no shipped scenario exercises multiple simultaneous WAR pairs in the same tick.

**`SemanticEntityQuery`** (`src/engine/semantic_entity_index.py:122-152`) — confirmed API surface:
`by_role_class(state, dirty, role, class_id)`, `by_region(state, dirty, region_id)`,
`by_faction`, `by_need`, `by_knowledge_domain`. All return `Tuple[int, ...]`.

- `by_region(state, dirty, region_id)` (lines 133-136) returns `indexes.by_region.get(region_id, ())`
  — a pre-sorted tuple of **every** entity ID whose `NavigationComponent.region_id == region_id`,
  regardless of role. This is a real dimension match for the region half of the current scan: it
  narrows from `O(N)` (all entities in the world) to `O(k)` (entities in one region), and the caller
  still needs to filter the returned IDs to `identity.role == EntityRole.GUARD` in-memory (one
  `state.entities[eid]` lookup per candidate, bounded by region population, not world population).
  This is the real, legitimate win the ticket's open question was asking about — not a literal
  `O(1)`/`O(k)` role+region lookup (no such compound dimension exists), but a genuine narrowing from
  world-scan to region-scan.

- `by_role_class(state, dirty, role, class_id)` requires an exact `class_id` value, and `class_id` is
  a per-entity progression field (`IdentityComponent.class_id`, default `"NOVICE"`,
  `src/core/state.py:482`), not fixed per role in the schema. Checked the actual GUARD population:
  `data/content/spawn_tables.yaml:17` — `class_id_by_role: {guard: ["WARRIOR"], ...}` — in **every**
  shipped world-compile path (`WorldCompiler`, `src/worldbuilding/compiler.py:158/419`), GUARD-role
  entities are assigned `class_id="WARRIOR"` and only `"WARRIOR"` (single-element eligible-class
  list). So `by_role_class(state, dirty, EntityRole.GUARD, "WARRIOR")` would, for shipped content,
  return the same *set* of entity IDs as filtering `identity.role == GUARD` directly — but:
  1. This is a **content-data invariant**, not a schema/type invariant. `IdentityComponent.class_id`
     is a free-form `str` field; nothing in `src/core/state.py`, `src/content/schema.py`, or the apply
     path enforces "GUARD implies class_id=WARRIOR". `tests/unit/domains/optimization/
     test_semantic_entity_index.py` itself constructs entities with arbitrary
     `role`/`class_id` combinations via a `make_entity(...)` helper with no such constraint.
  2. `by_role_class` has **no region dimension at all** — its key is `(role, class_id)` only
     (`_build_role_class_index`, `semantic_entity_index.py:76-81`). Using it would still require a
     second, separate filter against `region_id` (either intersecting with `by_region`'s result, or
     reading `nav.region_id` per candidate) — so it buys nothing over `by_region` and adds a fragile
     dependency on a data assumption the type system does not enforce.
  **Conclusion: `by_region` + in-memory role filter is the correct dimension, not `by_role_class`.**

**Cost caveat found during investigation (new finding, not covered by the ticket's own framing):**
grepped all of `src/` for production callers of `SemanticEntityQuery` — **zero** exist outside
`src/engine/semantic_entity_index.py` itself and test files. `PAID-INFO-INDEX-RETROFIT`
(`TCK-20260822-PAID-INFO-INDEX-RETROFIT`) deliberately did **not** wire into it (dimension mismatch —
see Prior Work). This ticket's retrofit would therefore be the **first production consumer**.
`SemanticEntityIndexService.get_indexes()` (lines 47-73) has no partial/single-dimension build path:
any query call rebuilds **all 5** dimensions together whenever `CacheInvalidationPolicy.should_invalidate(domain, dirty)`
is true for that domain, and `should_invalidate` returns `True` unconditionally when `dirty is None`
(`world_index.py:46-48`) — which is what this call site must pass, since `pipeline.py` does not build
`DirtySet` until *after* `military_conflict` runs (`dirty_builder.build()` at `pipeline.py:262`, well
after line 233). So the **first** `by_region(...)` call inside a tick's `execute()` pays for rebuilding
all 5 dimensions (~4 additional `O(N)`-over-`entities` passes for `by_role_class`/`by_faction`/`by_need`,
plus one smaller `O(P)`-over-`information_providers` pass for `by_knowledge_domain`), not just the one
`by_region` pass actually needed. Only *subsequent* calls within the **same** `execute()` invocation
(i.e. additional WAR pairs in the same tick) hit the tick-scoped cache and pay only `O(k)`. Given every
existing test/scenario has exactly one WAR pair per tick, and `AuthoritativeState.semantic_entity_indexes`
is documented as **not carried forward across ticks** (`performance_contract.md` §8.2 "Known
limitation"), a literal `by_region`-only retrofit is a **net regression** versus today's single `O(N)`
scan for the common (single-WAR-pair) case, and only pays off once `war_pair_count` is large enough to
amortize the ~5x one-time rebuild cost. See Risks and Open Questions for the recommended alternative.

## Mechanics / Engine Constraints

- `docs/engine/performance_contract.md` §4.1 (Parity Invariant): "Optimization MUST NOT change the
  semantic outcome... Any optimization that causes a hash mismatch in `AuthoritativeState` vs. the
  baseline is a failure." Directly constrains this ticket: the retrofit must return byte-identical
  `List[int]` output to the current full scan (AC #1 already states this explicitly).
- `docs/engine/performance_contract.md` §8.2 (Semantic Entity Indexes): documents
  `SemanticEntityIndexes`/`SemanticEntityQuery`, its lazy pull-based `CacheInvalidationPolicy`-driven
  lifecycle (no per-dimension selective build), the "first production caller pays full rebuild" shape
  implicitly (not stated outright — this investigation adds that specific finding), and the existing
  PAID-INFO precedent of declining to wire in when the dimension shape doesn't fit cleanly.
- Determinism: `SemanticEntityIndexes` is excluded from `CanonicalStateHasher` by omission — using it
  is safe with respect to determinism/hash-parity as long as the *returned entity ID list* stays
  identical, since the index itself never enters `StateUpdate`/`to_canonical_data()`.
- No `docs/mechanics/` chapter documents the GUARD reinforcement/squad-commitment mechanic itself
  (checked `01_entity_anatomy.md`, `04_strategic_cognition.md`, `05_world_evolution.md`,
  `docs/combat/combat_movement_overhaul_spec.md` — all GUARD/siege/reinforcement hits found are either
  unrelated ("VANGUARD", generic "reinforcement spawns" ownership prose, or the `HUNT_WEAK_ENEMY`
  GUARD patrol-proxy rule) — none describe *this* siege-reinforcement/squad-cap mechanic). This
  mechanic's authoritative documentation lives entirely in `docs/parity_ledger/faction.yaml` (FAC-008)
  and `docs/engine/performance_contract.md` §8.2 (for the index piece), not the Mechanics Bible.

## Docs Requiring Update

- `docs/parity_ledger/faction.yaml`: FAC-008's `test_path` currently cites only
  `tests/unit/domains/faction/test_siege_model.py`, which (confirmed by grep) contains **zero**
  references to GUARD/reinforcement/squad/GroupRecord/FACTION_SQUAD — it does not cover the ≥3-GUARD
  reinforcement branch or the squad-commitment cap. Must be corrected to cite the new tests this
  ticket adds for those two branches (and can additionally cite the new index/full-scan parity test).
  `v2_evidence` should also gain a short addition describing the index-backed (or hoisted, depending
  on Plan's decision — see Risks) implementation, mirroring how `TOWN-182` was updated in
  `TCK-20260822-PAID-INFO-INDEX-RETROFIT`.
- `docs/engine/performance_contract.md`: §8.2 must gain a short addition (same pattern as the existing
  PAID-INFO paragraph already in this section) stating what was actually retrofitted at the GUARD-scan
  call site — either "routed through `SemanticEntityQuery.by_region`" or "hoisted to a local per-`execute()`
  scan, declining to route through the index for cost reasons" — whichever Plan selects, plus the
  reasoning, so this section stays accurate for future readers the way it already is for PAID-INFO.

The Mechanics Bible chapters checked above (`docs/mechanics/01_entity_anatomy.md`,
`04_strategic_cognition.md`, `05_world_evolution.md`) are not required to change for this ticket: none
of them documents the siege GUARD-reinforcement/squad-commitment mechanic itself (only unrelated
GUARD/reinforcement mentions), and this ticket is a pure implementation/performance retrofit that must
preserve identical output (AC #1) — no semantic/gameplay change to document.
`docs/guidelines/intentional_divergences.md` (path: `docs/guidelines/intentional_divergences.md`) is
also not required: AC #1 requires bit-identical behavior preservation, so no intentional divergence is
introduced by this ticket, matching the same "N/A" conclusion `PAID-INFO-INDEX-RETROFIT`'s own AC #3
reached for the identical reason.

## Parity Ledger Overlap

- **FAC-008** (P1, `status: verified`) — text describes exactly the retrofit target (`get_war_pairs`,
  `execute`, `_find_contested_region`, `_find_guard_entities_in_region`, the ≥3-GUARD reinforcement
  offset). Its `test_path` citation is wrong for the reinforcement/squad-commitment branches (see Docs
  Requiring Update) — must be corrected in the same session per the Authoritative Mechanics Rule.
  `priority: P1` (not P0), so a passing `test_path` is required for hygiene/accuracy but this entry
  does not carry the P0 "hard gate" weight.
- **FAC-009** (P1, verified) — siege state/`RegionState` fields; cites the same source file but a
  disjoint set of behaviors (siege state shape, clamping). Not directly touched by this retrofit but
  shares the file — flagged as an adjacency risk (see Anti-Drift Hazards).
- **FAC-010** (P1, verified) — territory transfer; same file, disjoint behavior (transfer block, not
  the GUARD scan). Adjacency risk only.
- **FAC-011** (P1, verified) — exhaustion drain / orphan cleanup; same file, disjoint behavior.
  Adjacency risk only.
- No `P0` parity entries are touched by this ticket's actual scope.

## Prior Work

- `stored_artifacts/TCK-20260822-SEMANTIC-ENTITY-INDEX/` (done, `tickets/done/TCK-20260822-SEMANTIC-ENTITY-INDEX.md`):
  built the index this ticket retrofits into. Confirms: lazy pull-based `CacheInvalidationPolicy`-driven
  lifecycle (Recommendation 1 in that ticket), `semantic_entity_indexes` **not** carried forward
  across ticks (explicit known limitation, directly relevant to the cost finding above), query methods
  return ID tuples only.
- `tickets/done/TCK-20260822-PAID-INFO-INDEX-RETROFIT.md` +
  `stored_artifacts/TCK-20260822-PAID-INFO-INDEX-RETROFIT/plan.md` (Design Decision section): the
  sibling retrofit ticket for the same index, which hit a **dimension mismatch** (no index dimension
  maps onto "all providers sorted by entity_id" without changing selection semantics) and resolved it
  by hoisting `sorted(providers.keys())` to a single local variable computed once per `enforce()` call
  — explicitly declining to route through `SemanticEntityQuery`/`by_knowledge_domain`. This ticket's
  situation is different in kind (the dimension *does* fit — `by_region` is a clean match) but similar
  in structure: evidence here shows a **cost mismatch** (paying for 5 dimensions to use 1, as the
  index's first production caller) rather than a dimension mismatch. The same "don't force a wire-in
  when the evidence doesn't support it" precedent applies — see Risks and Open Questions for the
  concrete recommendation.
- `docs/engine/performance_contract.md` §8.2 already narrates the PAID-INFO precedent in prose, useful
  as the template for whatever addition this ticket makes to the same section.

## Risks and Open Questions

**Central open question (from Scope), now resolved with evidence:** `by_region` is the correct
dimension (not `by_role_class` — see Current Behavior for why the class_id-uniqueness argument doesn't
hold structurally even though it happens to hold in today's content data). However, whether to
actually route through `SemanticEntityQuery.by_region` or to hoist a local per-`execute()` scan (like
PAID-INFO did) is a **real, evidence-backed open question for Plan to decide, not something this
investigation can settle unilaterally**, because it depends on a product/performance tradeoff:

- **Option A — wire into `SemanticEntityQuery.by_region`** (literal reading of the ticket's Scope
  text): architecturally consistent with the intended future where multiple engine call sites share
  one warmed-per-tick index (this ticket would be the index's first production consumer, warming it
  for any future consumer added later in the same tick). Costs ~5x a single `O(N)` scan on the first
  call of a tick (see Current Behavior's cost caveat), amortized only when `war_pair_count` in a single
  tick is high enough — not the case in any existing shipped scenario (all have exactly 1 WAR pair).
  For those scenarios this is a **net regression**, not an improvement, until/unless a later ticket
  adds more same-tick consumers of the index or cross-tick carry-forward (documented existing
  limitation) is fixed.
- **Option B — local hoist**, mirroring `PAID-INFO-INDEX-RETROFIT`'s resolution: build a single
  `region_id -> sorted [GUARD entity ids]` dict once at the top of `execute()` (one `O(N)` pass over
  `state.entities`, regardless of `war_pair_count`), then do dict lookups per WAR pair inside the
  existing loop. This achieves the ticket's real underlying goal — bounding the scan to `O(N)` once
  per tick instead of `O(N × war_pair_count)` — without paying for 4 unused index dimensions and
  without introducing a dependency on `SemanticEntityIndexService`'s tick-cache lifecycle (whose
  cross-tick non-carry-forward limitation is orthogonal to this ticket and shouldn't become load-bearing
  for it). Strictly better on the evidence gathered here, but is a deviation from the ticket's literal
  Scope wording ("a lookup against the semantic entity index's ... role+region dimensions") the same
  way PAID-INFO deviated from its own Scope wording — that deviation was accepted and documented there,
  not silently made.

This investigation recommends Option B on the performance evidence above, but flags it explicitly as a
decision for Plan (with the ticket's own author or a stakeholder check-in if Plan disagrees), since it
changes what "index retrofit" concretely means for this call site — the same class of decision PAID-INFO
made and documented rather than assumed.

**Other risks:**
- `EntityRole` is an `IntEnum` (`GUARD = 5`) and `by_role_class`'s key is `(role: int, class_id: str)`
  — confirmed consistent typing with `identity.role` used directly (no coercion bugs to watch for if
  Option A is chosen).
- `state.entities[eid].identity`/`.navigation` are non-Optional (`default_factory`-backed) on real
  `EntityState` (`src/core/state.py:674/686`) — the current code's defensive `getattr(..., None)`
  checks are dead code for real state, but multiple test files use hand-rolled `_FakeState`
  doubles (`test_siege_model.py`, `test_military_conflict_phase.py`, `test_war_exhaustion.py`,
  `test_territory_transfer.py`, `test_siege_ledger.py`) with `entities={}` by default — any retrofit
  must keep working against an empty `entities` dict without raising, under both Option A and B.
- Under Option A, the call site must explicitly pass `dirty=None` (pipeline.py does not build a
  `DirtySet` until after `military_conflict` runs) — confirmed `should_invalidate` treats `None` as
  "always invalidate," so this is safe but must not be assumed without the citation above.

## Anti-Drift Hazards

- Do not let this retrofit touch `_find_contested_region`, `get_war_pairs`, the territory-transfer
  block, or the exhaustion-drain loop — all confirmed out of scope, sharing the same source file as
  FAC-009/010/011 but not the same function.
- Do not "fix" the reinforcement/squad-commitment mechanic's semantics while adding coverage for it —
  AC #1 requires identical output to the current scan; any behavior change here is out of scope and
  would require a new `docs/guidelines/intentional_divergences.md` entry, which this ticket is not
  scoped to add.
- Do not silently choose Option A or B without recording the choice and rationale in `plan.md`'s
  Design Decision section (or ticket Implementation Notes) the way `PAID-INFO-INDEX-RETROFIT` did —
  this is exactly the kind of decision CLAUDE.md's "no important decision undocumented" rule targets.
- Do not conflate this ticket with `TCK-20260822-SEMANTIC-ENTITY-INDEX`'s own known limitation
  (cross-tick carry-forward) — that limitation is pre-existing and out of scope for this ticket; do not
  attempt to fix it here even if Option A makes it more visible.
- `class_id_by_role`'s single-value-for-guard content fact (`data/content/spawn_tables.yaml:17`) must
  not be hardcoded into the implementation as a load-bearing assumption (e.g. "just filter
  `class_id == 'WARRIOR'` instead of `role == GUARD`") — it is a content-data fact, not a schema
  guarantee, and doing so would silently break for any future world/content that spawns a GUARD with a
  different class.
