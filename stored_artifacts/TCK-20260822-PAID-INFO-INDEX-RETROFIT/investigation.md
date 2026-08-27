---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260822-PAID-INFO-INDEX-RETROFIT
artifact_type: investigation
tags: [information, performance, determinism]
---

# Investigation — TCK-20260822-PAID-INFO-INDEX-RETROFIT

## Current Behavior

**`PaidInformationTransactionSystem.enforce(state, update)`**
(`src/engine/pipeline_phases/paid_information.py:74-183`)

- Line 85: `providers = getattr(state, "information_providers", {})`; returns `update` unchanged if
  empty (line 86-87).
- Line 92: `for entity in sorted(state.entities.values(), key=lambda e: e.id):` — the outer O(N)
  seeker scan (explicitly Out of Scope for this ticket per the ticket body).
- Lines 96-107: for each live entity, linear-scans `entity.strategic.projects.values()` for an
  `ACTIVE` `INFORMATION_SEEKING` project; skips entity if none found.
- **Lines 111-116 — the hotspot this ticket targets:**
  ```python
  provider_record = None
  for pid in sorted(providers.keys()):
      if pid == entity.id:
          continue
      provider_record = providers[pid]
      break
  ```
  `sorted(providers.keys())` is recomputed from scratch **inside the per-seeker loop**, i.e. once
  per seeking entity, not once per `enforce()` call. This is an O(seekers × M log M) cost where M =
  `len(providers)`, versus an O(M log M) cost if hoisted outside the loop. The ticket's Request
  Summary already corrects the originally-filed premise: it is resort-repetition
  (O(N × M log M)), not a full O(N × M) comparison scan.
- **Selection semantics (confirmed by reading, not assumed):** the loop takes the **smallest
  `entity_id` among all registered providers whose id != the seeker's own id** — `knowledge_domains`,
  `archetype`, and `reliability_score` play **no role in selection**; `reliability_score` is read
  only *after* a provider is chosen (line 122), to compute cost/certainty. This matches the
  ticket's Request Summary ("smallest non-self entity_id," not the archetype/reliability-filtered
  selection originally designed) and is provable from the code: no domain/archetype comparison
  exists anywhere in the `for pid in sorted(providers.keys())` loop.
- Lines 118-166: cost via `_transaction_cost` (line 58-60: `int(10 / max(0.1, reliability))`),
  certainty via `_lead_certainty_for_reliability` (lines 44-55), subject derived from the project's
  `ASK_INFORMATION` objective, then a `ResourceTransferIntent` (`source_kind="INFORMATION_PURCHASE"`)
  with a contingent `StrategicUpdate` is appended to `entity_updates` via `dataclasses.replace`.
  This flow is unrelated to the hotspot and is explicitly preserved unchanged by Scope ("Preserve
  gold-deduction flow through the authoritative `ResourceTransactionResolver`").
- Called from `src/engine/pipeline.py:309-310`, Phase 6 (Economy & Evolution), inside
  `run_phase("paid_information", update, lambda u: PaidInformationTransactionSystem.enforce(state, u))`
  — **only `state` and `update` are passed**, no `dirty` argument. At that call site
  `update.dirty_set` has just been rebuilt (`pipeline.py:296-297`: `dirty_builder.mark_from_update(...)`
  then `update.replace(dirty_set=dirty_builder.build())`), so a live `DirtySet` **is** reachable as
  `update.dirty_set` from inside `enforce()` without changing its 2-argument signature — relevant
  if a retrofit needs `SemanticEntityQuery`'s `dirty: Optional[DirtySet]` parameter.

**`SemanticEntityQuery` / `SemanticEntityIndexService`** (`src/engine/semantic_entity_index.py`,
shipped by `TCK-20260822-SEMANTIC-ENTITY-INDEX`, confirmed DONE)

- `SemanticEntityIndexes` (lines 22-34) has exactly five dimensions:
  `by_role_class: Dict[(role, class_id), Tuple[int,...]]`, `by_region`, `by_faction`, `by_need`,
  `by_knowledge_domain: Dict[str, Tuple[int,...]]`.
- `_build_knowledge_domain_index` (lines 113-119) is the **only** dimension over
  `state.information_providers` — it buckets provider `entity_id`s **by each string in
  `InformationProviderState.knowledge_domains`**, not by "all registered providers." A provider
  with an empty `knowledge_domains` tuple is invisible to every `by_knowledge_domain` bucket.
- `SemanticEntityQuery.by_knowledge_domain(state, dirty, domain) -> Tuple[int, ...]` (lines
  148-151) returns only the provider ids tagged with that one `domain` string — sorted (line 119:
  `tuple(sorted(v))`).
- **Gap confirmed against this ticket's actual retrofit target:** none of the five dimensions
  return "all registered `information_providers` keys, sorted" as a single call. The current
  shipped `paid_information.py` selection logic does not filter by domain at all (see above), so
  `by_knowledge_domain(state, dirty, domain)` cannot be substituted 1:1 without either (a)
  iterating every domain and unioning results (re-deriving the M-key sort by another route, no real
  win, and changing dedup/ordering subtly), or (b) changing selection semantics to
  domain-filtered, which Scope explicitly forbids ("Preserve the exact current selection
  semantics: smallest non-self entity_id"). See Risks and Open Questions below — this is the
  central design question this ticket's plan phase must resolve.
- `docs/engine/performance_contract.md:100-103` itself already anticipates this exact retrofit
  and states it is "separately scoped and not yet done" — i.e., the dependency ticket's own
  plan/investigation (see Prior Work) deliberately left `paid_information.py` untouched and did not
  design a dimension for it.

**`InformationProviderState`** (`src/domains/information/providers.py:36-58`) — frozen dataclass,
fields `entity_id`, `archetype`, `reliability_score`, `knowledge_domains: Tuple[str,...]`,
`knowledge_age`. Confirms `knowledge_domains` is a per-provider declared-priority tuple (no sort
applied per its own docstring, line 65-66) — orthogonal to the `entity_id`-ordering the current
selection logic actually uses.

## Mechanics / Engine Constraints

- **`docs/mechanics/03_economic_laws.md`** — governs atomic conservation for the gold deduction
  this ticket does not touch (Scope explicitly preserves "gold-deduction flow through the
  authoritative `ResourceTransactionResolver` — no change to that path"). Grepped the chapter: it
  contains no text about paid information / provider selection specifically (that mechanic's
  authoritative record lives in the parity ledger, `TOWN-182`, not a Bible chapter section) — a
  pure performance retrofit that preserves selection/cost semantics exactly does not touch any law
  in this chapter.
- **`docs/engine/performance_contract.md` §8.2 "Semantic Entity Indexes"** — this is the contract
  this ticket must comply with when choosing *how* to eliminate the per-seeker resort. Constraints
  that bind the implementation: (a) any index/cache attached to `AuthoritativeState` must go through
  `object.__setattr__`, never `StateUpdate`/`replace()` (§8.2, "Attached to
  `AuthoritativeState.semantic_entity_indexes` via `object.__setattr__`"); (b) it must stay excluded
  from `CanonicalStateHasher` (§8.2 "Determinism" — `to_canonical_data()` is a hand-written
  allow-list, never touch it); (c) **Known limitation** — `semantic_entity_indexes` is not carried
  forward across ticks in `ApplyPath.apply_generation`, so even if this ticket routes through
  `SemanticEntityQuery`, the first post-tick query in production still does a full rebuild; the win
  is confined to eliminating same-tick per-seeker repetition, not a warm cross-tick cache (per the
  Scope-phase note already supplied with this ticket).
- **§4.1 Parity Invariant** (`performance_contract.md`) — "Optimization MUST NOT change the semantic
  outcome... a hash mismatch in `AuthoritativeState` vs. baseline is a failure." Directly backs
  AC #3 (byte-identical `StateUpdate.entity_updates` across two calls on byte-identical state).
- **`docs/core/state.md`** — grepped: contains no text mentioning `information_providers` or
  `semantic_entity_indexes` specifically; the general immutability/authoritative-vs-derived state
  partitioning law it documents is respected as long as any new cache this ticket introduces is
  non-authoritative and derived (same category as `world_indexes`/`semantic_entity_indexes`), not a
  new durable field requiring a typed model.
- **`docs/guidelines/intentional_divergences.md`** — grepped: no existing entry for E42C / paid
  information provider selection. AC #4 only requires a new entry **if** selection semantics change
  from min-non-self-id — not expected under current scope.

## Docs Requiring Update

- `docs/engine/performance_contract.md`: §8.2's own text (lines 101-103) currently states "the live
  `paid_information.py` seeker/provider scan -- retrofitting that call site is separately scoped and
  not yet done." Once this ticket lands, that sentence becomes stale and must be updated to reflect
  completion and to accurately describe whichever mechanism the plan settles on (routing through
  `SemanticEntityQuery`, or a locally-hoisted per-`enforce()`-call cache — see Risks below; either
  way the "not yet done" framing needs replacing with the real, shipped shape, including a note if
  the chosen mechanism is NOT `SemanticEntityQuery` so future readers don't assume it went through
  the semantic index).

The following docs from the ticket's own "Related Docs" list were considered and are NOT required
to change, based on what was actually read:

`docs/mechanics/03_economic_laws.md` is not required to change: grepped for "information"/"provider"
and found zero matches — the chapter does not document this mechanic at all today (the authoritative
record for paid-information transactions is `docs/parity_ledger/town_resource.yaml`'s `TOWN-182`
entry, not a Mechanics Bible chapter), and this ticket's scope preserves the existing cost formula
and conservation-law gold flow exactly, so there is no formula/law text in this chapter to update.

`docs/core/state.md` is not required to change: grepped for "information"/"provider"/"semantic" and
found zero matches — it documents general immutability/state-partitioning law, and this ticket does
not add a new durable state field (any retrofit cache, if one is introduced at all, follows the
already-documented non-authoritative derived-cache pattern `semantic_entity_indexes`/`world_indexes`
already established, which is `performance_contract.md`'s territory, not `state.md`'s).

`docs/guidelines/intentional_divergences.md` is not required to change under the current, expected
scope (preserving exact min-non-self-entity_id selection): AC #4 only requires a new entry
**conditionally**, if selection semantics end up changing — which Scope explicitly says is not
expected. If the plan phase or a stakeholder decides to change selection semantics, this doc
becomes a required-update item at that time, not now.

## Parity Ledger Overlap

- **`TOWN-182`** (`docs/parity_ledger/town_resource.yaml:1981-2000`), status `verified`, priority
  `P1`. Text: paid information transactions deduct gold via `ResourceTransferIntent`
  (`source_kind="INFORMATION_PURCHASE"`) through the authoritative `ResourceTransactionResolver`;
  cost formula `int(10 / max(0.1, reliability_score))`; conservation law applies; certainty tiers
  PRECISE/APPROXIMATE/VAGUE. `v2_evidence` cites `src/engine/pipeline_phases/paid_information.py`
  directly. **This is a P1 entry with a passing `test_path`** (the same 3 of the 9
  `TestPaidInformationTransaction` tests cited in this ticket's AC #1). Since this ticket's Scope
  explicitly preserves the cost formula, conservation flow, and certainty derivation unchanged,
  `TOWN-182`'s `status`/`v2_evidence` text should remain accurate as-is — **no ledger edit is
  required unless the retrofit's implementation incidentally changes any of the cited evidence
  file/line shape enough to warrant refreshing `v2_evidence`'s file:line references** (a judgment
  call for the planner/implementer once the actual diff is known, not a required edit today).
  Re-run all three `test_path` tests as part of this ticket's regression surface regardless (P0/P1
  ledger discipline).
- Grepped `social_narrative.yaml` and `infrastructure.yaml` for `paid_information`/
  `information_provider`/`INFORMATION_PURCHASE`/`information_seeking` — matches found are either
  event-name mentions inside unrelated entries' prose (event taxonomy lists, SimQ scoring notes) or
  the `semantic_entity_index`'s own `"knowledge"` cache-invalidation note (`infrastructure.yaml:11535`,
  from the dependency ticket) — none of these are separate parity IDs whose `status`/`v2_evidence`
  this ticket's scope requires editing.
- **No `P0` entries overlap this ticket's scope** — `TOWN-182` is `P1`.

## Prior Work

- **`tickets/done/TCK-20260822-SEMANTIC-ENTITY-INDEX.md`** (DONE) — shipped the index this ticket
  retrofits into. Its own plan.md (`stored_artifacts/TCK-20260822-SEMANTIC-ENTITY-INDEX/plan.md`)
  Scope Guards explicitly state: "Do NOT retrofit `src/engine/pipeline_phases/paid_information.py`
  or any faction/military conflict call site to use the new index. Those are
  `TCK-20260822-PAID-INFO-INDEX-RETROFIT` and `TCK-20260822-GUARD-SCAN-INDEX-RETROFIT`" — confirms
  this ticket is the designated follow-up, sequencing is correct, and `paid_information.py` is
  untouched by the dependency ticket (verified: no `SemanticEntityQuery`/`SemanticEntityIndexService`
  import anywhere in `paid_information.py` today).
  Deviation #3 in that plan.md records, with source citations, that `semantic_entity_indexes` is
  **not** carried across ticks in `ApplyPath.apply_generation` — matches the Scope-phase note
  already given with this ticket; independently reconfirmed here by reading
  `docs/engine/performance_contract.md:133-140`'s "Known limitation" paragraph, which cites the same
  gap.
- **`TCK-20260619-E42C-PAID-TRANSACTION`** and **`TCK-20260619-E42B-INFO-PROVIDER`** (Related
  Tickets) — original tickets that shipped `PaidInformationTransactionSystem` and
  `InformationProviderState` respectively; not re-read in full (not in Related Code Areas), but
  `TOWN-182`'s `v2_evidence` and the module docstrings in both files under investigation cite them
  directly and are consistent with current code.

## Risks and Open Questions

- **Central open question (blocks a clean plan without a decision): there is no existing
  `SemanticEntityQuery` dimension that maps onto "all registered `information_providers`, sorted by
  `entity_id`, excluding self."** `by_knowledge_domain` is the only dimension touching
  `information_providers`, and it buckets by domain string — using it would either require
  iterating every domain (not obviously cheaper, and changes what "matching providers" means) or
  silently narrowing selection to domain-tagged providers only, which Scope forbids. The ticket's
  own Scope text anticipates this ambiguity ("...or an equivalently-scoped index if sequencing
  requires it, computed at most once per enforce() call") — read literally, this permits the
  retrofit to NOT go through `SemanticEntityQuery` at all, and instead hoist
  `sorted(providers.keys())` to a single local variable computed once at the top of `enforce()`,
  before the per-seeker loop, which trivially satisfies AC #2 ("computed at most once per
  `enforce()` call, not once per seeker") without touching `semantic_entity_index.py` or its Out-of-
  Scope boundary ("Building the index data structure itself... is not part of this retrofit"). This
  reading is consistent with the ticket's Out-of-Scope line and does not require any new dimension.
  **Flagging this for the planner rather than assuming an answer**: the plan phase must explicitly
  choose between (a) a local per-`enforce()`-call hoist (no `semantic_entity_index.py` involvement),
  or (b) wiring through `SemanticEntityQuery.by_knowledge_domain` with a union-of-all-domains
  fallback path that is provably equivalent to today's un-filtered selection (higher complexity,
  weaker fit), or (c) some other equivalently-scoped mechanism. Given the ticket's own Out-of-Scope
  wording and the confirmed dimension mismatch, (a) is the most literal, lowest-risk reading of
  Scope — but this investigation does not decide it, since the ticket names `SemanticEntityQuery`'s
  parent ticket by ID in Scope and a planner/stakeholder may have intended something more specific.
- `entity_updates == dict(update.entity_updates)` no-op check (line 180) does a full dict equality
  comparison every call; unrelated to the sort hotspot but worth the implementer noticing it is not
  itself the target of this ticket (not called out in Scope) — do not touch it as drive-by cleanup.
- Confirmed no `P0` parity entries in scope, so no `test_path` failure risk there; the only P1 in
  scope (`TOWN-182`) already has a passing `test_path` overlapping this ticket's own AC #1 test
  list (`test_paid_transaction_transfers_gold_and_lead`, `test_vague_lead_for_low_reliability`,
  `test_transaction_cost_formula_high_reliability` are common to both lists).
- The `dirty` parameter needed by every `SemanticEntityQuery.by_*` method is `Optional[DirtySet]`
  and reachable in production as `update.dirty_set` at the `pipeline.py:309-310` call site, but the
  9 existing unit tests construct `state`/`update` directly via `_make_state`/`StateUpdate()` with
  no `dirty_set` populated (defaults to `None` on a bare `StateUpdate()`). If the plan chooses to
  route through `SemanticEntityQuery` (option (b) above), passing `dirty=None` is safe per
  `CacheInvalidationPolicy.should_invalidate`'s existing `if dirty is None: return True` unconditional-
  rebuild guard (confirmed in the dependency ticket's plan.md, Step 7) — so this would not break the
  9 existing tests on its own, but does mean every test-driven call forces the "knowledge" domain to
  always rebuild, which does not exercise the intended caching win outside production ticks.

## Anti-Drift Hazards

- Do not touch the outer O(N) `sorted(state.entities.values(), key=lambda e: e.id)` seeker scan —
  explicitly Out of Scope (needs a distinct "seekers by active project kind" index dimension the
  index's dimension table does not have today).
- Do not change provider selection from "smallest non-self entity_id" to any
  archetype/reliability/domain-filtered logic — explicitly Out of Scope unless flagged as a new,
  separate divergence (AC #4).
- Do not touch the gold-deduction / `ResourceTransactionResolver` flow, the cost formula
  (`_transaction_cost`), or the certainty-tier derivation (`_lead_certainty_for_reliability`) — all
  three are `TOWN-182`-covered and outside this ticket's Scope.
- Do not build a new `SemanticEntityIndexes` dimension (e.g. an "all provider ids" dimension) as
  part of this ticket — that is "building the index data structure itself," explicitly named
  Out of Scope and would encroach on `TCK-20260822-SEMANTIC-ENTITY-INDEX`'s already-closed territory.
  If the plan phase concludes a new dimension is genuinely required, that is a scope decision to
  surface explicitly, not something to silently add here.
- Do not widen `PaidInformationTransactionSystem.enforce`'s signature in a way that breaks the 9
  existing tests' 2-positional-argument call shape (`enforce(state, update)`) — any `dirty` access
  needed should come from `update.dirty_set` (already reachable at the real call site), not a new
  required parameter.
- Do not silently "fix" the `entity_updates == dict(update.entity_updates)` no-op-detection line
  (paid_information.py:180) as drive-by cleanup — unrelated to this ticket's scope.
