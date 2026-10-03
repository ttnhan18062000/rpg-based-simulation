---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260822-PAID-INFO-INDEX-RETROFIT
artifact_type: plan
tags: [information, performance, determinism]
---

# Implementation Plan — TCK-20260822-PAID-INFO-INDEX-RETROFIT

## Summary

The hotspot is `sorted(providers.keys())` being recomputed inside the per-seeker loop at
`src/engine/pipeline_phases/paid_information.py:112` (confirmed by reading the file directly —
current code shown below). This plan eliminates the per-seeker resort by hoisting
`sorted(providers.keys())` into a single local variable computed once at the top of
`PaidInformationTransactionSystem.enforce()`, immediately after the existing early-return guard
(`paid_information.py:85-87`) and before the seeker loop (`paid_information.py:92`), leaving every
other line of selection/cost/certainty/intent logic untouched. This plan deliberately does **not**
route the lookup through `SemanticEntityQuery` (`src/engine/semantic_entity_index.py`) — see
"Design Decision" below for the evidence-based reasoning — so `semantic_entity_index.py` is not
touched at all by this plan. Three new tests are added to the existing
`TestPaidInformationTransaction` class to make AC #2 and AC #3 machine-verified, and
`docs/engine/performance_contract.md` §8.2 is updated to replace its "separately scoped and not yet
done" sentence with an accurate description of the shipped mechanism.

### Design Decision — local hoist, not `SemanticEntityQuery`

Read `src/engine/semantic_entity_index.py:22-34` (via the investigation) and confirmed against
`docs/engine/performance_contract.md:93-103` (read directly for this plan): `SemanticEntityIndexes`
has exactly five dimensions, and the only one touching `information_providers` is
`by_knowledge_domain`, which buckets provider ids **by knowledge-domain string**
(`semantic_entity_index.py:113-119`), not by "all registered provider ids, sorted, excluding self."
The current shipped selection logic (`paid_information.py:111-116`, confirmed by direct read) applies
no domain/archetype/reliability filter at all — it takes the smallest non-self `entity_id` among
*every* registered provider. Routing through `by_knowledge_domain` would require either (a) unioning
every domain bucket (re-deriving an M-key sort by a more expensive route, and changing dedup/ordering
semantics for providers with overlapping or empty `knowledge_domains` — a provider with an empty
`knowledge_domains` tuple is invisible to every bucket per `semantic_entity_index.py:113-119`, which
would silently drop it from selection — a forbidden semantics change per Scope), or (b) narrowing
selection to only domain-tagged providers (explicitly forbidden by Scope: "Preserve the exact current
selection semantics"). The ticket's own Scope text — "...or an equivalently-scoped index if
sequencing requires it, computed at most once per `enforce()` call" — permits a mechanism other than
`SemanticEntityQuery`, and Out of Scope explicitly forbids "building the index data structure itself."
A local hoisted variable is the smallest change that satisfies AC #2 exactly ("computed at most once
per `enforce()` call, not once per seeker") without touching `semantic_entity_index.py`'s already-shipped,
already-closed dimension table, and without any semantics risk. This is the plan's design call — no
further stakeholder decision is required for it.

## Steps

### Step 1 — Hoist `sorted(providers.keys())` out of the per-seeker loop

**Files:** `src/engine/pipeline_phases/paid_information.py`

**Change:** In `PaidInformationTransactionSystem.enforce()`, the current code (confirmed by direct
read, `paid_information.py:85-116`) is:

```python
providers = getattr(state, "information_providers", {})
if not providers:
    return update

entity_updates = dict(update.entity_updates)

for entity in sorted(state.entities.values(), key=lambda e: e.id):     # line 92
    ...
    provider_record = None
    for pid in sorted(providers.keys()):                                # line 112 — recomputed every seeker
        if pid == entity.id:
            continue
        provider_record = providers[pid]
        break
```

Change it to compute the sort once, immediately after the early-return guard (after line 87, before
line 89's `entity_updates = dict(...)`):

```python
providers = getattr(state, "information_providers", {})
if not providers:
    return update

sorted_provider_ids = sorted(providers.keys())   # hoisted: computed once per enforce() call, not per seeker

entity_updates = dict(update.entity_updates)

for entity in sorted(state.entities.values(), key=lambda e: e.id):
    ...
    provider_record = None
    for pid in sorted_provider_ids:
        if pid == entity.id:
            continue
        provider_record = providers[pid]
        break
```

The inner loop body (`if pid == entity.id: continue` / `provider_record = providers[pid]` / `break`)
is otherwise byte-identical — same list contents, same order, same first-match rule, so selection
output for every seeker is unchanged. No other line in `enforce()` (cost formula, certainty
derivation, `ResourceTransferIntent` construction, the `entity_updates == dict(update.entity_updates)`
no-op check at line 180) is touched.

**Other writers to the shared resource this step reads (`state.information_providers` /
`providers`):** Enumerated by grep (`grep -rn "information_providers" src/`, run for this plan):
- `src/core/state.py:1155` — declares `information_providers: Dict[int, InformationProviderState]`
  as a field on the frozen `AuthoritativeState` dataclass. `AuthoritativeState` instances are
  immutable for the lifetime of a single `enforce()` call — nothing can mutate `state.information_providers`
  out from under the hoisted local variable mid-call.
- `src/engine/pipeline_phases/lead_contradiction.py:124,203,268` — the *only* other pipeline phase
  that touches provider data. It reads `state.information_providers.get(provider_id)` (reliability
  decay logic) and writes to `update.information_providers_update` (a separate `StateUpdate` field,
  `src/core/updates.py:929`), never to `state.information_providers` directly. That update dict is
  applied to the *next* tick's `AuthoritativeState.information_providers` by `ApplyPath`, not visible
  within the current tick's `enforce()` call. There is no ordering conflict: this step's hoist reads
  a value that is fixed for the duration of `enforce()` regardless of what `lead_contradiction.py`
  queues for the next tick.
- `src/engine/semantic_entity_index.py:116` — reads `state.information_providers.items()` to build
  `by_knowledge_domain`; read-only, and not invoked by this step's code path at all (this plan does
  not touch `semantic_entity_index.py` — see Design Decision above).
- No writer mutates `providers` (the local variable) or `state.information_providers` inside
  `enforce()` itself — the hoist is safe.

**Do NOT touch:** the outer seeker scan (`sorted(state.entities.values(), key=lambda e: e.id)`,
line 92); the `pid == entity.id` self-skip check; `_transaction_cost`, `_lead_certainty_for_reliability`,
`ResourceTransferIntent`/`StrategicUpdate` construction (lines 118-166); the
`entity_updates == dict(update.entity_updates)` no-op check (line 180); the `enforce(state, update)`
2-positional-argument signature.

**Verify:** All 9 existing tests in `tests/unit/cognition/test_information_seeking.py::TestPaidInformationTransaction`
pass unmodified (AC #1) — `pytest tests/unit/cognition/test_information_seeking.py -v`.

---

### Step 2 — Add call-count test proving the sort runs once per `enforce()` call

**Files:** `tests/unit/cognition/test_information_seeking.py`

**Change:** Add a new test method `test_sorted_providers_computed_once_per_enforce_call` to
`TestPaidInformationTransaction` (colocated per test_plan.md, after `test_seeker_is_own_provider_skipped`,
line 488, using the class's existing `_make_seeker`/`_make_provider`/`_make_state` helpers at
`test_information_seeking.py:294-342`, confirmed by direct read). Build a state with N=3 seekers
(distinct entity ids, each with an active `INFORMATION_SEEKING` project via `_make_seeker`) and M=2
providers (via `_make_provider`). Patch `builtins.sorted` with `unittest.mock.patch("builtins.sorted",
side_effect=<spy>)` where `<spy>` wraps the real `sorted` and records the argument list of every call.
After calling `PaidInformationTransactionSystem.enforce(state, StateUpdate())`, filter the recorded
calls to those whose argument set equals `set(providers.keys())` (this isolates the provider-id sort
from the unrelated, unconditional entity-scan sort at `paid_information.py:92`, which also uses
`builtins.sorted` and would otherwise pollute a raw global call count). Assert exactly 1 such call
occurred, despite N=3 seekers each needing a provider lookup — this directly proves Step 1's hoist
(if the hoist were absent, this filtered count would be 3, one per seeker, matching the
`sorted(providers.keys())` call inside the loop at the pre-Step-1 line 112).

**Do NOT touch:** any other test in the file; do not spy on or assert about
`SemanticEntityIndexService`/`SemanticEntityQuery` (out of scope per Design Decision — this retrofit
does not route through the semantic index).

**Verify:** New test passes; depends on Step 1 already being applied (without the hoist, the
filtered call count would be N=3, not 1, so this test is a genuine regression guard, not a tautology).

---

### Step 3 — Add scale test proving cost does not grow with seeker count

**Files:** `tests/unit/cognition/test_information_seeking.py`

**Change:** Add `test_paid_information_enforce_scales_with_providers_not_seekers_times_providers` to
`TestPaidInformationTransaction`, using the same `builtins.sorted`-spy/filter technique as Step 2
(reuse a small local helper if convenient, e.g. a module-level `_count_provider_sorts(state)` in the
test file that returns the filtered call count for one `enforce()` call — implementer's choice on
whether to factor this out or duplicate the ~6-line spy). Build two states with the same M=2 providers
but different seeker counts (N=1 and N=5), call `enforce()` once per state, and assert the filtered
provider-sort call count is 1 in both cases (not proportional to N — i.e., not 1 vs 5). This is the
AC #2 "benchmark" alternative from the ticket, implemented as a deterministic call-count assertion
rather than wall-clock timing, per test_plan.md's explicit guidance to avoid CI flakiness.

**Do NOT touch:** wall-clock timing assertions (test_plan.md explicitly prefers call-count for CI
stability) — do not add a `time.perf_counter()`-based assertion as a substitute.

**Verify:** New test passes; depends on Step 1.

---

### Step 4 — Add determinism test for AC #3

**Files:** `tests/unit/cognition/test_information_seeking.py`

**Change:** Add `test_enforce_is_deterministic_across_repeated_calls` to
`TestPaidInformationTransaction`. Build one `AuthoritativeState` via `_make_state` with >=2 seekers
and >=2 providers (reuse `_make_seeker`/`_make_provider`). Call
`PaidInformationTransactionSystem.enforce(state, StateUpdate())` twice, independently, each with a
fresh `StateUpdate()` (matching the existing 9 tests' call pattern, confirmed at
`test_information_seeking.py:362` etc. — `state` itself is never mutated between calls, since
`AuthoritativeState` is frozen). Assert the two returned `update.entity_updates` dicts are equal
(structural/value equality — `EntityUpdate`, `ResourceTransferIntent`, `StrategicUpdate`, `LeadState`
are frozen dataclasses with value equality, confirmed by their use as plain `==`-compared objects
throughout the existing 9 tests, e.g. `test_information_seeking.py:369-379`). This directly verifies
`performance_contract.md` §4.1's Parity Invariant as applied to Step 1's hoist: hoisting to a local
variable computed from `sorted(providers.keys())` cannot introduce dict-iteration-order
nondeterminism because Python `sorted()` output is deterministic for a fixed input list regardless of
how many times or when it is called.

**Do NOT touch:** the existing 9 tests' assertions or call patterns.

**Verify:** New test passes; depends on Step 1 (tests the shipped hoisted code path, though it would
also pass against the pre-Step-1 code since that code was already deterministic — this test's primary
value is as a permanent regression guard per AC #3, not as a hoist-specific proof).

---

### Step 5 — Update `docs/engine/performance_contract.md` §8.2

**Files:** `docs/engine/performance_contract.md`

**Change:** §8.2 currently reads (confirmed by direct read, `performance_contract.md:99-103`):

> `by_knowledge_domain` (`AuthoritativeState.information_providers` keyed by
> `InformationProviderState.knowledge_domains`). Introduced by `TCK-20260822-SEMANTIC-ENTITY-INDEX`
> to give strategic/governance layers O(1)/O(k) entity lookups instead of O(N) scans (e.g. the live
> `paid_information.py` seeker/provider scan -- retrofitting that call site is separately scoped and
> not yet done).

Replace the parenthetical with an accurate statement that the retrofit is done and did **not** go
through `SemanticEntityQuery`: state that `TCK-20260822-PAID-INFO-INDEX-RETROFIT` eliminated the
per-seeker `sorted(providers.keys())` resort in `paid_information.py` by hoisting the sort to a single
local variable computed once per `enforce()` call, and explicitly note this did not route through
`by_knowledge_domain` or any other `SemanticEntityIndexes` dimension, because none of the five
dimensions match "all registered providers sorted by entity_id" without changing selection semantics
(citing the same domain-bucketing gap documented in this plan's Design Decision) — so a future reader
does not assume `paid_information.py` now depends on `semantic_entity_index.py`.

**Do NOT touch:** any other section of `performance_contract.md` (§8.1, the rest of §8.2's dimension
list, the "Known limitation" or "Determinism" paragraphs) — those describe `SemanticEntityIndexService`
itself, which this plan does not modify.

**Verify:** No automated test covers doc prose; verify by re-reading the edited paragraph for
accuracy against Step 1's actual shipped code once Step 1 is complete.

## Scope Guards

- Do not touch the outer O(N) seeker scan (`sorted(state.entities.values(), key=lambda e: e.id)`,
  `paid_information.py:92`) — needs a distinct "seekers by active project kind" index dimension not
  covered by `SemanticEntityIndexes` today; explicitly Out of Scope per the ticket.
- Do not change provider selection from "smallest non-self `entity_id`" to any
  archetype/reliability/domain-filtered logic — explicitly Out of Scope unless flagged as a new,
  separate divergence (AC #4, not triggered by this plan).
- Do not touch the gold-deduction / `ResourceTransactionResolver` flow, `_transaction_cost`,
  `_lead_certainty_for_reliability`, or `ResourceTransferIntent`/`StrategicUpdate` construction
  (`paid_information.py:118-166`) — all covered by `TOWN-182` (P1, verified) and outside this
  ticket's Scope.
- Do not build a new `SemanticEntityIndexes` dimension in `src/engine/semantic_entity_index.py`
  (e.g. an "all provider ids" dimension) — explicitly Out of Scope; this plan's Design Decision
  chose the local-hoist path specifically to avoid needing one.
- Do not widen `PaidInformationTransactionSystem.enforce`'s signature beyond `enforce(state, update)`
  — the 9 existing tests call it with exactly 2 positional arguments.
- Do not touch the `entity_updates == dict(update.entity_updates)` no-op-detection line
  (`paid_information.py:180`) — unrelated to this ticket's scope, called out explicitly in the
  investigation as a non-target.
- Do not edit `docs/parity_ledger/town_resource.yaml`'s `TOWN-182` entry — its `v2_evidence` cites
  `src/engine/pipeline_phases/paid_information.py — PaidInformationTransactionSystem` at the
  module/class level (no line numbers), which remains accurate after Step 1's hoist; no ledger edit
  is triggered.
- Do not add a `docs/guidelines/intentional_divergences.md` entry — AC #4 only requires one if
  selection semantics change, and this plan preserves them exactly.
- Do not touch `docs/mechanics/03_economic_laws.md` or `docs/core/state.md` — investigation confirmed
  (by grep) zero mentions of `information`/`provider`/`semantic` in either file; nothing in this plan
  changes conservation law text or state-partitioning law.
- Do not touch `src/engine/pipeline_phases/lead_contradiction.py` or `update.information_providers_update`
  — it is a distinct writer to provider-related data via a separate `StateUpdate` field, unaffected by
  and unrelated to this plan's hoist (see Step 1's writer enumeration).
- Do not touch `src/engine/semantic_entity_index.py` at all — this plan's chosen mechanism does not
  route through it.

## Dependency Map

- Step 1 has no dependencies — pure code change, independently verifiable against the 9 existing
  tests (AC #1).
- Steps 2, 3, and 4 each depend on Step 1 being applied first (their assertions are only meaningful,
  and in Step 2/3's case only true, once the hoist exists). Steps 2, 3, and 4 are independent of each
  other and can be done in any order once Step 1 lands.
- Step 5 depends on Step 1 being complete (the doc text must describe the actual shipped mechanism,
  not a planned one) but is otherwise independent of Steps 2-4.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — all 9 existing `TestPaidInformationTransaction` tests pass unmodified | Step 1 | `pytest tests/unit/cognition/test_information_seeking.py::TestPaidInformationTransaction -v` (all 9 existing methods) |
| AC #2 — sort computed at most once per `enforce()` call, not once per seeker | Step 1 (hoist), Step 2 (call-count proof), Step 3 (scale proof) | `test_sorted_providers_computed_once_per_enforce_call`, `test_paid_information_enforce_scales_with_providers_not_seekers_times_providers` |
| AC #3 — two `enforce()` calls on byte-identical state produce byte-identical `StateUpdate.entity_updates` | Step 1 (deterministic hoist), Step 4 | `test_enforce_is_deterministic_across_repeated_calls` |
| AC #4 — divergence doc + parity ledger update if selection semantics change | Not triggered — this plan preserves selection semantics exactly (Design Decision, Step 1) | N/A — no new test scaffolded, per test_plan.md |

## Anti-Drift Notes

- The central risk flagged by the investigation — forcing `SemanticEntityQuery.by_knowledge_domain`
  into this call site — is resolved by this plan's Design Decision, not deferred: the local hoist is
  chosen precisely because no shipped dimension matches "all providers sorted by entity_id" without
  either weakening the fit (union-of-domains) or changing selection semantics (domain-narrowing,
  forbidden by Scope). Do not revisit this mid-implementation by attempting a `SemanticEntityQuery`
  wire-in "for consistency" — that was evaluated and rejected here with cited evidence.
  `test_provider_lookup_uses_semantic_index_not_raw_state_dict` (the conditional architecture guard
  test_plan.md scaffolds only for the `SemanticEntityQuery` path) must NOT be added under this plan,
  since it asserts the opposite of what this plan implements.
  test_plan.md is explicit on this: "do not add if the plan instead hoists a local sort."
- `providers` (the dict) is never mutated inside `enforce()` — only `providers.keys()` is sorted once
  and cached locally. If a future change needs to invalidate the hoisted list mid-`enforce()`, that
  would be a sign `state.information_providers` is not actually immutable during a single `enforce()`
  call, which would contradict `AuthoritativeState`'s frozen-dataclass contract (`state.py:1155`) —
  treat any such symptom as a bug to investigate separately, not something to patch around here.
- A provider with an empty `knowledge_domains` tuple must remain selectable after this change (it was
  selectable before, since the shipped selection logic never reads `knowledge_domains` at all) — this
  is implicitly covered by the 9 existing tests (none of which set `knowledge_domains`, so
  `InformationProviderState`'s default applies) and must not regress.
- `dirty_set` / `SemanticEntityQuery`'s `dirty: Optional[DirtySet]` parameter is irrelevant to this
  plan — it is only needed by callers of `SemanticEntityQuery`, which this plan does not become one
  of. Do not add a `dirty` parameter to `enforce()`.

## Deviations

- **Step 2/3 spy implementation**: the plan describes filtering `builtins.sorted` calls by "argument
  set equals `set(providers.keys())`." The outer seeker scan at `paid_information.py`'s per-tick loop
  (`sorted(state.entities.values(), key=lambda e: e.id)`) also runs through the same patched
  `builtins.sorted`, and its arguments are `EntityState` objects, which are unhashable (contain a
  `set`-typed field on `IdentityComponent`). A literal `set(items) == provider_key_set` filter raises
  `TypeError: unhashable type: 'set'` on that call before it can be excluded by inequality. Fixed by
  wrapping the comparison in `try/except TypeError: matches_providers = False` inside the test-only
  spy helper (`_count_provider_sorts`, `tests/unit/cognition/test_information_seeking.py`). This is a
  test-harness-only fix — it does not change production code, the filtering intent, or which calls
  get counted; it only makes the intended filter robust to the entity-scan sort's unhashable
  argument type, which the plan's prose did not anticipate.

- **TOWN-182 v2_evidence edit, despite this plan's Scope Guard saying not to touch it**: this plan
  explicitly instructed "do not edit `docs/parity_ledger/town_resource.yaml`'s `TOWN-182` entry"
  (per investigation.md's conclusion that no ledger edit was needed, since selection semantics were
  preserved exactly). During the Parity phase, the orchestrator-run cross-reference gate — which
  checks that every `src/` file mapped to a parity-ledger subsystem has a corresponding touch in the
  diff, independent of whether Investigate/Plan judged a semantic edit necessary — failed, since
  `src/engine/pipeline_phases/paid_information.py` maps to `town_resource.yaml` and the file had zero
  diff. `TOWN-182`'s `v2_evidence` was updated with a small, surgical addition describing the code's
  current shape (the `sorted_provider_ids` hoist); `status`/`text`/`priority`/`test_path` were left
  unchanged, since the underlying selection semantics genuinely did not change. This plan's original
  "do not edit" instruction was correct about *semantics* (no divergence, no status change) but did
  not anticipate the orchestrator-level gate requiring the file to be touched at all when a mapped
  `src/` file changes.
