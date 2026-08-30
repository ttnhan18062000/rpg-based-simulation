---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260822-PAID-INFO-INDEX-RETROFIT
artifact_type: test_plan
tags: [information, performance, determinism]
---

# Test Plan — TCK-20260822-PAID-INFO-INDEX-RETROFIT

## Regression Surface

**Unit — `tests/unit/cognition/test_information_seeking.py`**
- `TestPaidInformationTransaction` (9 tests, lines 346-491) — the ticket's AC #1 explicitly names
  this class; all 9 must pass **unmodified**:
  - `test_paid_transaction_transfers_gold_and_lead`
  - `test_vague_lead_for_low_reliability`
  - `test_approximate_lead_for_mid_reliability`
  - `test_transaction_cost_formula_high_reliability`
  - `test_transaction_cost_formula_low_reliability`
  - `test_lead_subject_matches_project_objective`
  - `test_no_provider_no_intent`
  - `test_no_seeking_project_no_intent`
  - `test_seeker_is_own_provider_skipped`
- Adjacent classes in the same file (`TestLeadContradiction` and others, lines 578+) exercise
  `information_providers`/lead machinery downstream of `PaidInformationTransactionSystem` — not in
  this ticket's direct scope but share fixtures/helpers (`V2EntityBuilder`, `_make_provider`), so a
  full-file run is cheap insurance against an accidental import-time or helper-signature break.

**Unit — `tests/unit/domains/optimization/test_semantic_entity_index.py`** (regression surface for
`SemanticEntityQuery`/`SemanticEntityIndexService`, only relevant if the retrofit routes through it
— see investigation.md's open question):
- `test_by_knowledge_domain_matches_naive_scan`
- `test_index_reflects_dirty_set_change_without_full_rebuild`
- `test_incremental_index_bit_identical_to_full_rebuild`
- `test_delete_and_rebuild_index_matches_incremental_across_all_dimensions`
- `test_semantic_index_excluded_from_canonical_state_hash`
- Full file otherwise, to catch any accidental cross-dimension break.

**Integration / parity — `TOWN-182`'s cited `test_path`** (subset of the unit list above; re-run as
part of parity ledger discipline for a P1 entry):
- `TestPaidInformationTransaction::test_paid_transaction_transfers_gold_and_lead`
- `TestPaidInformationTransaction::test_vague_lead_for_low_reliability`
- `TestPaidInformationTransaction::test_transaction_cost_formula_high_reliability`

**Determinism / arena-combat**: none directly — `paid_information.py` does not touch combat state.
No arena-combat regression surface identified.

## New Tests Required

Per AC #2 (sort computed at most once per `enforce()` call, not once per seeker):
- **Test name:** `test_sorted_providers_computed_once_per_enforce_call`
- **Category:** unit (call-count instrumentation)
- **What it verifies:** builds a state with N ≥ 2 seekers and M ≥ 2 providers, monkeypatches/spies
  on whichever function performs the sort (either `sorted` itself scoped via a wrapper, or — if the
  retrofit routes through `SemanticEntityQuery` — a spy on
  `SemanticEntityIndexService._build_knowledge_domain_index` / `get_indexes`) and asserts the
  sort/build path executes at most once, not once per seeker. If the retrofit hoists a local
  variable instead, assert equivalently via a `sorted()`-call counter (e.g. wrap `providers.keys()`
  access, or count via a `unittest.mock.patch("builtins.sorted", wraps=sorted)` spy scoped to the
  `enforce()` call) that the call count is 1 regardless of seeker count.
- **Where:** `tests/unit/cognition/test_information_seeking.py`, new method on
  `TestPaidInformationTransaction` (keeps it colocated with the class AC #1 already names).

Per AC #2's benchmark alternative wording ("verified via call-count instrumentation or a
benchmark"):
- **Test name:** `test_paid_information_enforce_scales_with_providers_not_seekers_times_providers`
- **Category:** unit (micro-benchmark / complexity assertion, not a strict perf gate)
- **What it verifies:** with fixed M providers, `enforce()` wall time (or sort-call count) does not
  grow proportionally with seeker count N — a light guard against the O(N × M log M) regression
  this ticket exists to fix, complementary to the call-count test above rather than a replacement
  for it (call-count is deterministic and CI-stable; wall-clock timing is not — prefer call-count as
  the primary assertion and keep this test call-count-based too rather than wall-clock-based, to
  avoid CI flakiness).
- **Where:** same file, same class.

Per AC #3 (byte-identical `StateUpdate.entity_updates` across two calls on byte-identical state):
- **Test name:** `test_enforce_is_deterministic_across_repeated_calls`
- **Category:** unit
- **What it verifies:** build one `AuthoritativeState` with ≥2 seekers and ≥2 providers, call
  `PaidInformationTransactionSystem.enforce(state, StateUpdate())` twice independently (fresh
  `StateUpdate()` each time, same `state` object), and assert the two returned
  `update.entity_updates` dicts are equal (structural equality on the frozen dataclasses is
  sufficient — `EntityUpdate`/`ResourceTransferIntent`/`StrategicUpdate`/`LeadState` are frozen
  dataclasses with value equality). This directly targets `performance_contract.md` §4.1's Parity
  Invariant as applied to this specific optimization.
- **Where:** same file, same class.

Per AC #4 (conditional — only if selection semantics change, not expected under current scope):
- No new test required now. If the plan phase or Implement discovers the retrofit cannot preserve
  exact min-non-self-entity_id semantics without a real behavior change, this AC requires: a new
  `docs/parity_ledger/town_resource.yaml` entry or `TOWN-182` update, a new
  `docs/guidelines/intentional_divergences.md` entry, and a corresponding regression test proving
  the new selection rule — none of that is scaffolded here since it is explicitly not the expected
  path.

If the plan phase resolves the open dimension-mismatch question (investigation.md, Risks and Open
Questions) in favor of routing through `SemanticEntityQuery`:
- **Test name:** `test_provider_lookup_uses_semantic_index_not_raw_state_dict` (architecture guard)
- **Category:** architecture guard / static
- **What it verifies:** `paid_information.py` imports and calls into
  `src.engine.semantic_entity_index` rather than iterating `state.information_providers` directly
  inside the per-seeker loop — a source-scan test mirroring
  `tests/static/test_no_direct_dirtyset_candidate_selection.py`'s pattern.
- **Where:** `tests/static/` (new or extended file), only add if this path is actually chosen —
  do not add if the plan instead hoists a local sort (Risk (a) in investigation.md), since in that
  case there would be nothing meaningful to assert about `semantic_entity_index.py` usage.

## Scoped Pytest Commands

```
pytest tests/unit/cognition/test_information_seeking.py -v
pytest tests/unit/domains/optimization/test_semantic_entity_index.py -v
```

If the retrofit adds a static/architecture guard test file under `tests/static/`, include it:
```
pytest tests/static/ -k "semantic_index or paid_information" -v
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- `TestPaidInformationTransaction`'s 9 existing tests, run **unmodified** — the primary guard
  against a silent selection-semantics change (AC #1's own wording). Any edit to these test bodies
  to make them pass is itself a signal the retrofit changed behavior and must be treated as a Scope
  violation to report, not routed around.
- `test_enforce_is_deterministic_across_repeated_calls` (new, above) is also the guard against a
  non-deterministic index build order (e.g. dict iteration order leaking into provider selection if
  the retrofit changes from `sorted(providers.keys())` to some other structure).
- `test_semantic_index_excluded_from_canonical_state_hash` (existing, from the dependency ticket) —
  re-run as part of this ticket's regression surface if the retrofit touches
  `semantic_entity_index.py` at all, to guard against accidentally pulling any new cache into
  `CanonicalStateHasher`.
- `test_seeker_is_own_provider_skipped` (existing) — the specific guard for the self-provision skip
  rule; a naive "just use `SemanticEntityQuery`" retrofit that iterates a domain-bucketed result
  without re-checking `pid == entity.id` would regress this silently.
- `test_no_provider_no_intent` (existing) — guards the early-return-on-empty-`providers` path
  (line 86-87), which any retrofit must keep intact regardless of which lookup mechanism replaces
  the sort.
- If the retrofit is later found to route through `SemanticEntityQuery.by_knowledge_domain`, add an
  explicit guard that providers with an **empty** `knowledge_domains` tuple are still selectable
  (today's shipped code makes no domain distinction at all) — this is the concrete regression this
  investigation flags as the most likely silent scope-creep vector for that implementation path.
