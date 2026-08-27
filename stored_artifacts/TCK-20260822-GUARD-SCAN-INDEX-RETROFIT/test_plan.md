---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260822-GUARD-SCAN-INDEX-RETROFIT
artifact_type: test_plan
tags: [faction, grand-strategy, performance]
---

# Test Plan — TCK-20260822-GUARD-SCAN-INDEX-RETROFIT

## Regression Surface

All existing tests importing `MilitaryConflictPhase` must keep passing unmodified (confirmed by grep
— these are the only production/test consumers of `military_conflict.py`):

**Unit:**
- `tests/unit/domains/faction/test_military_conflict_phase.py` (6 tests — noop/empty-factions,
  noop-on-peace, war-pair detection, `get_war_pairs` dedup, non-WAR-pair filtering, return-type guard)
- `tests/unit/domains/faction/test_siege_model.py` (17 tests — `SiegeState`/`RegionState`
  round-trip/immutability, `WorldUpdate` merge/clamp semantics, plus the 4
  `MilitaryConflictPhase` siege-loop integration tests at the bottom of the file)
- `tests/unit/domains/faction/test_war_exhaustion.py` (9 tests — exhaustion drain, orphan siege
  cleanup, `WAR_ENDED_EXHAUSTION` threshold crossing)
- `tests/unit/domains/faction/test_territory_transfer.py` (5 tests — territory-transfer block)
- `tests/unit/domains/faction/test_siege_ledger.py` (3 tests — siege ledger integration)
- `tests/unit/domains/optimization/test_semantic_entity_index.py` (12 tests — must stay green
  regardless of which option Plan chooses; only relevant if Option A wires into
  `SemanticEntityQuery.by_region`, but running it either way catches accidental changes to the shared
  index service)

**Integration:**
- `tests/integration/scenarios/test_faction_campaign.py` (3 tests, `@pytest.mark.slow` —
  `test_war_declared_and_territory_transferred` and 2 others; real `AuthoritativeState`, single
  ALPHA/BETA WAR pair, no GUARD entities populated — exercises the "0 guards, scan returns empty list"
  path end-to-end over 25 ticks)

**Faction domain (adjacent, same source file's other functions — FAC-006/007 coverage, must not
regress from an unrelated edit to `_find_guard_entities_in_region`):**
- `tests/unit/domains/faction/test_diplomacy.py`
- `tests/unit/domains/faction/test_faction_decision_phase.py` (confirmed zero GUARD/entity scanning —
  out of scope per the ticket, but scoped-run anyway since it's in Related Code Areas)

## New Tests Required

Per Acceptance Criteria:

1. **Name:** `test_find_guard_entities_matches_naive_full_scan` (or equivalent, e.g.
   `test_guard_lookup_identical_to_reference_scan`)
   **Category:** unit (parity/regression guard)
   **What it verifies:** AC #1 — populates a mix of GUARD and non-GUARD entities (varying
   `identity.role`, including `HERO`/`MONSTER`/`WORKER`) across at least 2 distinct `region_id`
   values, calls the retrofitted lookup, and asserts it returns the exact same sorted `List[int]` as
   a naive reference re-implementation of the original full scan (mirroring
   `test_semantic_entity_index.py`'s own `_naive_by_role_class` pattern) — not just "same set," to
   catch any accidental sort-order regression.
   **Where:** `tests/unit/domains/faction/test_siege_model.py` (co-located with the other
   `MilitaryConflictPhase` siege-loop tests) or a new small file
   `tests/unit/domains/faction/test_guard_scan_index_retrofit.py` if Plan prefers a dedicated file —
   either is acceptable; prefer `test_siege_model.py` for locality with the existing siege-loop suite
   unless Plan's design decision (Option A vs B, see investigation.md) suggests otherwise.

2. **Name:** `test_military_conflict_reinforcement_fires_at_three_guards` (currently **zero**
   coverage — confirmed by grep across `test_siege_model.py`, `test_military_conflict_phase.py`,
   `test_faction_campaign.py`, `test_faction_decision_phase.py`)
   **Category:** unit (behavior/AC)
   **What it verifies:** AC #2 — a WAR-pair state with exactly 3 GUARD entities (role=`GUARD`) placed
   in the contested region (via `nav.region_id`) produces a `WorldUpdate` with the combined delta
   `service_availability_delta == -0.05 + 0.02 == -0.03` and `siege_progress_delta == 0.05 - 0.02 ==
   0.03` (i.e. both the base degradation delta and the +0.02/-0.02 reinforcement offset merged in the
   same tick) — and a companion test with only 2 GUARD entities asserting the reinforcement offset
   does **not** fire (base degradation delta only: `-0.05`/`+0.05`).
   **Where:** `tests/unit/domains/faction/test_siege_model.py`, appended to the "MilitaryConflictPhase
   siege loop (E53Cb integration)" section (matches the module's own E53Cb docstring: "squad
   commitment, defender reinforcement").

3. **Name:** `test_military_conflict_squad_commitment_capped_at_five`
   **Category:** unit (behavior/AC)
   **What it verifies:** AC #3 — a WAR-pair state with >5 (e.g. 7) GUARD entities in the contested
   region produces exactly one `GroupRecord` in `StateUpdate.groups_add_or_update` with
   `len(member_ids) == 5`, `roles` mapping all 5 members to `"FACTION_SQUAD"`, and `member_ids` being
   the 5 lowest entity IDs (since `squad_ids = guard_ids[:_MAX_SQUAD_SIZE]` slices the sorted list) —
   plus a companion boundary test with exactly 5 GUARD entities (all 5 committed, no truncation) and a
   companion test with 0 GUARD entities (`groups_add_or_update` stays empty, no `GroupRecord` created).
   **Where:** `tests/unit/domains/faction/test_siege_model.py`, same section as test #2.

4. **Name:** `test_guard_scan_returns_list_not_tuple` (only needed if Option A is chosen and
   `SemanticEntityQuery.by_region` — which returns `Tuple[int, ...]` — is used directly; skip if
   Option B's local hoist naturally returns a `list`)
   **Category:** unit (API-contract guard)
   **What it verifies:** `_find_guard_entities_in_region`'s public return type stays `List[int]`
   (matching its docstring and existing callers' expectations, e.g. `guard_ids[:_MAX_SQUAD_SIZE]`
   slicing and `len(guard_ids)`), even if the underlying index returns tuples — i.e. the retrofit must
   convert, not leak the index's native tuple type.
   **Where:** same file as test #1.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/domains/faction/ tests/unit/domains/optimization/test_semantic_entity_index.py -q
.venv/bin/python3 -m pytest tests/integration/scenarios/test_faction_campaign.py -q -m "not slow"
.venv/bin/python3 -m pytest tests/integration/scenarios/test_faction_campaign.py -q -m "slow"
```
(Split the integration command in two since `test_war_declared_and_territory_transferred` is marked
`@pytest.mark.slow` and the project rule excludes `slow` by default — run it explicitly at least once
to confirm the retrofit doesn't regress the 25-tick territory-transfer scenario.)

Use the project's real virtualenv interpreter (`.venv/bin/python3`), not ambient `python3` — confirmed
project convention from `TCK-20260822-SEMANTIC-ENTITY-INDEX`'s and
`TCK-20260822-PAID-INFO-INDEX-RETROFIT`'s own Test Summary sections.

Never: `pytest tests/`.

## Anti-Drift Test Guards

- The naive-full-scan parity test (New Test #1) doubles as an anti-drift guard: if a future change to
  the retrofit's implementation (e.g. someone "optimizes" it further) silently changes selection
  semantics or sort order, this test catches it immediately, the same role
  `test_semantic_entity_index.py::_naive_by_role_class`-style parity tests play for the index itself.
- `test_military_conflict_phase.py::test_military_conflict_phase_returns_state_update_not_list` (existing) already
  guards against `execute()`'s return type regressing to a bare list — keep passing unmodified;
  extending this file is unnecessary since it already covers the outer contract.
- If Option A (wire into `SemanticEntityQuery.by_region`) is chosen: add or reuse a call-count/spy
  assertion (mirroring `PAID-INFO-INDEX-RETROFIT`'s `_count_provider_sorts` spy pattern) proving the
  index is built **at most once** per `execute()` call regardless of `war_pair_count` — i.e. a 3-WAR-pair
  scenario should trigger exactly one full-index rebuild, not three, to guard against a caller
  accidentally passing a fresh `dirty`/breaking the tick-scoped cache reuse.
- If Option B (local hoist) is chosen: add a call-count assertion proving `state.entities.items()` (or
  equivalent) is iterated exactly once per `execute()` call regardless of `war_pair_count`, to guard
  against a future edit accidentally moving the hoisted scan back inside the per-WAR-pair loop —
  exactly the regression this ticket exists to prevent.
- A test asserting `_find_guard_entities_in_region` behaves correctly with `state.entities == {}` (the
  default in every existing `_FakeState`/`_make_state` test double) guards against the retrofit
  introducing an `AttributeError`/`KeyError` on the empty-entities path all 5 regression-surface test
  files currently rely on implicitly.
- A test confirming `FAC-009`/`FAC-010`/`FAC-011`'s covered behaviors (siege state shape, territory
  transfer, exhaustion drain) are unaffected — already covered by the Regression Surface list above;
  no new test needed, just confirm those suites stay green as an explicit anti-drift signal that the
  retrofit didn't leak into adjacent functions in the same file.
