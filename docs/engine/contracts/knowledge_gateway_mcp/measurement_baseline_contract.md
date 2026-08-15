---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, schema, mcp]
---

# Knowledge Gateway MCP — Measurement Baseline Contract

Source ticket: `TCK-20260814-KGMCP-MEASUREMENT-BASELINE`. This document delivers Phase 0's final
three §20 checklist bullets: "Record current latency, tool-call counts, repeated-demand signals,
and returned-token estimates for representative queries," "Define separate measurement for
lookup, evidence validation, provider fallback, packet assembly, and end-to-end latency," and
"Predeclare measurable promotion thresholds from that baseline." It is placed under
`docs/engine/contracts/knowledge_gateway_mcp/` alongside the sibling wire-contract,
evidence/cache-identity, and redaction/retention-policy documents. No `src/` or `tools/` gateway
code exists yet, and none is added by this ticket — the two real Python artifacts this ticket does
add (`tools/agent-monitoring/kgmcp_baseline_corpus.py`,
`tools/agent-monitoring/kgmcp_baseline_runner.py`) are agent-orchestration/measurement tooling, not
gateway code.

## 1. Representative-Query Corpus

The fixed, versioned representative-query corpus is defined in
`tools/agent-monitoring/kgmcp_baseline_corpus.py` (`CORPUS_VERSION = 1`, `CORPUS`, a list of 7
entries) — this document references that module by name and path and does not duplicate its query
text as a second source of truth. `CORPUS` has exactly one entry per §8's Query Routing table row
(7 rows: definition/terminology/architecture, symbol lookup, requirement-completeness, ticket/
historical rationale, test-impact-of-change, ticket-work-status, broad-task-context), and 5 of the
7 entries also carry one of §22's 5 Representative Use Case IDs
(`authoritative_state_ownership`, `feature_completeness_check`, `historical_removal_rationale`,
`test_impact_of_change`, `negative_knowledge_kafka`).

The real, recorded-from-a-real-run direct-tool baseline for each corpus entry is committed at
`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`, produced once by
`tools/agent-monitoring/kgmcp_baseline_runner.py` — a one-time script, not part of the recurring
pytest loop and not wired into `generate_retro.py`'s recurring weekly cadence. It calls
`tools/search_mcp.py::_run_search()` directly and shells out to `graphify query`, timing each with
`time.perf_counter()`. The fixture is pinned (git-committed), not regenerated on every CI run.

## 2. Latency Measurement Points

§18 requires 5 distinct latency measurement points rather than one blended number. For each, this
section states: meaning, unit (milliseconds), attachment point, and live-precedent status in this
repository today.

### 2.1 Lookup latency

**Meaning:** time to determine which cached candidate, if any, the gateway should examine next for
a request — the routing-key selection step (`evidence_cache_identity_contract.md` §1's lookup
identity), not a validity claim.

**Unit:** milliseconds.

**Attachment point:** where a future gateway's cache-lookup step would sit, before any evidence-
validity check runs.

**Live-precedent status:** `wrap_retrieval_cache_check()` (`tools/retrieval_events.py:223-288`,
timing at `:259-261`) is implemented but not invoked by any live call site — it already times
`check_index_cache()`/`check_query_cache()`/`check_packet_cache()`
(`tools/retrieval_cache.py:204`, `:266`, `:335`) and is the closest real precedent for this
measurement point's instrumentation shape.

**Caveat (cited from `evidence_cache_identity_contract.md` §3, the Non-collapse rule):** that
existing wrapper's single `latency_ms` blends lookup time with any incidental validity bookkeeping
the `check_*_cache()` functions perform internally. Once a real, disjoint evidence-validation step
exists (§2.2 below), lookup latency must be re-measured as lookup-only — this wrapper's current
number must never be reused verbatim as a lookup-only figure.

### 2.2 Evidence-validation latency

**Meaning:** time to determine, for a candidate the lookup step already selected, whether it is
still safe to return right now (`evidence_cache_identity_contract.md` §2's evidence-validity
identity) — a disjoint question from lookup, per that document's Non-collapse rule (§3).

**Unit:** milliseconds.

**Attachment point:** after a lookup hit, before the candidate is returned or falls back to
provider generation.

**Live-precedent status:** no existing wrapper in this repository performs a validity check
disjoint from lookup. Confirmed: none of `check_index_cache()`/`check_query_cache()`/
`check_packet_cache()` returns a `freshness`/`verification` field
(`evidence_cache_identity_contract.md` §2/§3, `:112-118`). This measurement point is a pure
definition today — no live number exists, and none is fabricated.

### 2.3 Provider-fallback latency

**Meaning:** time spent falling back to live `PROVIDER_GENERATION` evidence
(`evidence_cache_identity_contract.md` §4) when no finer-grained cached evidence fingerprint is
available or valid.

**Unit:** milliseconds.

**Attachment point:** after an evidence-validation miss or stale-rejection, before a fresh provider
call is dispatched.

**Live-precedent status:** no existing wrapper; this concept has no timed call site anywhere in
this repository today. Pure definition — no live number exists, and none is fabricated.

### 2.4 Packet-assembly latency

**Meaning:** time to assemble the final bounded, deduplicated multi-provider context packet
returned to the caller.

**Unit:** milliseconds.

**Attachment point:** after all providers/cache levels for a request have resolved, immediately
before the packet is returned.

**Live-precedent status:** `wrap_context_packet_assembly()` (`tools/retrieval_events.py:299-352`,
timing at `:324-326`) is implemented but not invoked by any live call site — it already times
`assemble_context_packet()` end to end and is direct precedent for this measurement point's
instrumentation shape.

### 2.5 End-to-end latency

**Meaning:** total wall time for one `knowledge_context` request, from the caller's call to the
returned packet.

**Unit:** milliseconds.

**Attachment point:** the outermost boundary of a future gateway's request handler.

**Live-precedent status:** no existing wrapper computes this directly. **Reconciliation rule
(stated explicitly here since §18 lists 7 total metrics without stating the composition rule
itself):** end-to-end latency is defined as the sum of whichever of §2.1–§2.4 actually execute for
a given request — never a 6th, independently-measured number. A cache-hit path skips
provider-fallback latency (§2.3) entirely; a cache-miss path includes it. No implementation may
measure end-to-end latency as anything other than this sum.

### 2.6 Fixture baseline vs. future gateway end-to-end latency — not the same number

The Step-2 fixture's `combined.wall_time_ms` field (§1 above,
`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`) is today's real,
direct-tool, **no-gateway-exists** baseline: the wall time of calling Context Search and Graphify
directly and summing their latencies. It is **not** the same number as §2.5's future gateway
"end-to-end latency" measurement point, which will exist only once a gateway is built and will
compose §2.1–§2.4 per the reconciliation rule above, not a sum of two direct provider calls. The
two numbers are compared against each other in §4's thresholds below precisely because they answer
different questions — the fixture's number is the pre-gateway baseline a future gateway's
end-to-end latency must beat; it must never be presented as if it already were that gateway's
end-to-end latency.

## 3. Distinct-Version-Axis Note

None of §2's 5 measurement points introduces a new "version" concept. Where a future
implementation stamps a version alongside a latency measurement, it reuses one of the four
already-distinct version axes named in `redaction_retention_policy.md` §6
(`retrieval_cache_schema_version`, `RETRIEVAL_VERSION`, `retrieval_event_schema_version`,
`redaction_policy_version`) — never a fifth, latency-specific version constant.

## 4. Predeclared Promotion Thresholds

Per §20's explicit instruction ("This proposal deliberately does not invent numeric thresholds
before that baseline exists"), every threshold below is a formula over a named field of the
committed fixture, `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` — never a
literal number invented independently of that fixture. The fixture's 7 entries, recorded
`2026-08-15T05:09:04.120766Z` (`recorded_at_utc`), give a corpus-wide average
`combined.wall_time_ms` of **1870.648 ms** and a corpus-wide average
`combined.serialized_tokens_estimate` of **2527.143 tokens**, each computed directly from the
fixture's 7 entries (arithmetic mean, no entry excluded). These figures are illustrative of the
formula below, pinned to the specific real run that produced the currently-committed fixture — a
future re-recording of the corpus (a new `corpus_version`) legitimately produces different
`latency_ms` figures (network/CPU timing is not reproducible), at which point this section's
computed figures must be refreshed from the new fixture, never left stale.

### 4.1 Minimum latency threshold

**Formula:** a future gateway's warm-hit end-to-end latency (§2.5) must not exceed 50% of the
corpus-wide average of `combined.wall_time_ms` across the fixture's 7 entries.

**Policy choice:** the 50% fraction is a policy choice — a warm-hit gateway response should be at
least twice as fast as calling both direct tools separately, or the gateway is not earning its
added lookup/validation overhead.

**Computed figure:** 50% × 1870.648 ms = **935.32 ms**. A future gateway's warm-hit end-to-end
latency must be ≤ 935.32 ms to satisfy this threshold, re-derived from the fixture, not hand-typed
independently of it, whenever the fixture is ever re-recorded under a new `corpus_version`.

### 4.2 Minimum token-reduction threshold

**Formula:** a future gateway's packet token count (via `kgmcp_char_heuristic_v1`,
`tools/agent-monitoring/kgmcp_baseline_corpus.py::kgmcp_char_heuristic_v1_token_count`) must be
some fraction lower than the corpus-wide average of `combined.serialized_tokens_estimate` across
the fixture's 7 entries.

**Policy choice:** 50%, matching §4.1's fraction — a gateway packet should return at most half the
raw serialized token volume of calling both direct tools and returning their combined output
unfiltered, since deduplication and bounded packet assembly (§18) are the gateway's core token-
savings mechanism.

**Computed figure:** 50% × 2527.143 tokens = **1263.57 tokens**. A future gateway's assembled
packet must be ≤ 1263.57 `kgmcp_char_heuristic_v1` tokens, per query, to satisfy this threshold.

### 4.3 No-regression-recall threshold

**Formula:** for a given corpus query, a future gateway's `sources_recalled` set must be a superset
of (or equal to) the union of that same fixture entry's `context_search.sources_recalled` list and
whatever authoritative sources the fixture's `graphify` result for that entry would resolve to.

**Rule:** recall must never regress below the direct-tool baseline's own recall, evaluated **per
query**, not only in aggregate — a gateway that recalls fewer sources for `Q4_historical_rationale`
specifically has regressed on that query even if its aggregate recall across all 7 entries improved.

### 4.4 Scope boundary

These three thresholds are this document's own Phase 0 measurement-baseline promotion bar. They
are not, and must never be presented as, §21's Phase 3 pilot acceptance criteria — §21 is a
separate, later-phase acceptance bar this document only cross-references, never restates as its
own threshold.

## 5. Repeated-Demand Estimation Design (§18.1)

Per §18.1, repeated-demand grouping must use only safe deterministic intent, provider-native
entity IDs, normalized filters, and the keyed query hash — never raw prompt text, and never
semantic clustering (explicitly deferred to Phase 5, out of scope here).

### 5.1 Identity schema

Repeated-demand grouping uses exactly these four fields, none of them redefined here — each is
reused by citation from an already-frozen source:

| Field | Source | Reused from |
|---|---|---|
| `intent` | One of `ROUTING_SHAPES` (`tools/agent-monitoring/kgmcp_baseline_corpus.py`) — a closed, deterministic vocabulary of 7 values, never free text. | Step 1's corpus module |
| `entity_id` | One of the 5 closed deterministic identity forms already frozen at `evidence_cache_identity_contract.md:47-54` — `symbol:<name>`, `ticket:<id>`, `parity:<entry-id>`, `doc:<registry-id>`, `subsystem:<name>`. | `evidence_cache_identity_contract.md` §1, cited only |
| `normalized_filters` | Reuses `_hash_filters()`'s existing normalize-then-hash shape (`tools/retrieval_cache.py:179-180`) — by citation, no import, since no live gateway code exists to import it into. | `tools/retrieval_cache.py`, cited only |
| `query_hash` | Reuses `_normalize_query()` + `_hash_text()` (`tools/retrieval_cache.py:171-176`) — by citation, no import. | `tools/retrieval_cache.py`, cited only |

No raw prompt text is ever a member of this schema. `intent`/`entity_id`/`normalized_filters`/
`query_hash` are the only four fields this design uses to identify repeated demand.

### 5.2 Honest current state

This design is validated only against the 7-entry corpus (§1) treated as a stand-in demand sample
— it reports **zero real repeated-demand numbers today**, because no gateway has ever run and no
production request stream exists to observe. This is the correct, honest state for a Phase 0
deliverable, not a gap to paper over — matching `_PARITY_INDEX_READPATH_RE`'s
"always-render 0 today, no code change needed once a call site exists" precedent
(`tools/agent-monitoring/generate_retro.py:286-321`).

### 5.3 Report shape

For each of §18.1's 4 required categories, this design states which field combination identifies
it and what the corpus-validated (not production) count is today. The 7-entry corpus is
deliberately non-repeating across its entries (§1: one entry per routing shape), so every category
below reports 0 by design — this is stated explicitly, not left for a reader to assume means "not
implemented":

| Category | Identifying field combination | Corpus-validated count today |
|---|---|---|
| Exact repeated lookup identities | Two or more requests sharing identical `(intent, entity_id, normalized_filters, query_hash)`. | 0 — the 7 corpus entries share no `query_hash`. |
| Entity-and-intent-equivalent requests with different query hashes | Two or more requests sharing `(intent, entity_id)` but differing `query_hash`. | 0 — the 7 corpus entries share no `(intent, entity_id)` pair (each entry has a distinct `routing_shape`, and no `entity_id` is assigned to more than one entry). |
| Repeated misses by entity and intent | Two or more cache-miss events sharing `(intent, entity_id)`. | 0 — no cache exists to record a miss event against; this category requires a live gateway to produce any non-zero count. |
| Queries repeatedly requiring the same evidence set | Two or more requests whose resolved evidence-fingerprint sets are identical, regardless of `query_hash`. | 0 — no evidence-fingerprint resolution exists yet at Phase 0 to compare. |

### 5.4 Distinct from `read_count_correlation`

This design is a structurally different metric from `generate_retro.py`'s
`read_count_correlation` (`generate_retro.py:1109-1141`, added by
`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`). `read_count_correlation` measures
per-Investigate-phase-pair `Read`-call counts split by that pair's own search-before-grep
compliance — a different metric over a different population (Investigate-phase tool-call pairs,
not corpus queries). This section's field names (`intent`, `entity_id`, `normalized_filters`,
`query_hash`) never alias `read_count_correlation`'s field names (`compliant_group`,
`non_compliant_group`), and the two sections are never merged.

## 6. Cross-References

- `tools/agent-monitoring/kgmcp_baseline_corpus.py` — the corpus definition and
  `kgmcp_char_heuristic_v1_token_count()`, referenced by §1 and §4.
- `tools/agent-monitoring/kgmcp_baseline_runner.py` — the one-time script that produced the §1
  fixture.
- `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` — the committed, real
  recorded baseline, referenced by §1 and §4.
- `tools/retrieval_events.py` — the 3 Wrapper functions cited in §2 as instrumentation precedent
  (`wrap_hybrid_retrieval()`, `wrap_retrieval_cache_check()`, `wrap_context_packet_assembly()`),
  each implemented but not invoked by any live call site.
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` — the lookup/
  validity identity fields and Non-collapse rule §2 cites, and the `entity_id` forms §5.1 reuses;
  referenced by citation only, never redefined here.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §6/§8 — the 4
  already-distinct version axes §3 cites, and the `kgmcp_char_heuristic_v1` formula §4.2 uses;
  drafted, not ratified.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §8, §18, §18.1, §20, §21, §22 — the proposal
  sections this document implements.

## 7. Parity Ledger

Unlike the sibling contract-only KGMCP documents, this ticket adds real, testable Python code
(`tools/agent-monitoring/kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`) under
`tools/agent-monitoring/`, following the `INFRA-281`-through-`INFRA-333`
agent-tooling-infrastructure precedent for ledgering this class of change
(`docs/parity_ledger/infrastructure.yaml`, `INFRA-292`). See `docs/parity_ledger/
infrastructure.yaml`'s `INFRA-334` entry.
