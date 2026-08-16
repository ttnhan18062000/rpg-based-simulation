---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, mcp, testing]
---

# Knowledge Gateway MCP — Phase 2 Baseline Recomparison Results

Source ticket: `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` (the "other half" of Phase 2's own
bargain: once `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` landed a real cache, this ticket runs
the same frozen 7-entry corpus through the gateway TWICE per entry — cold, then warm — and reports
`measurement_baseline_contract.md` §4's three predeclared promotion thresholds against the real
warm-path numbers, honestly). Full per-entry data is committed at
`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`, produced by
`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`.

## Headline result: 0/7 genuine cache hits; all four threshold checks FAIL, in aggregate and for every entry

| Threshold | Aggregate result | Pass count |
|---|---|---|
| §4.1 Minimum latency (warm-path) | **FAIL** | 0 / 7 |
| §4.2 Minimum token reduction (cold) | **FAIL** | 0 / 7 |
| §4.2 Minimum token reduction (warm) | **FAIL** | 0 / 7 |
| §4.3 No-regression recall | **FAIL** | 0 / 7 |

**Genuine cache-hit count: 0 / 7.** Every one of the 7 corpus entries' warm ("second") call was,
structurally, a second cold call — not a genuine cache hit. This is the real, current capacity of
the deployed cache relative to this gateway's real response sizes, confirmed by a live run, not
assumed from Investigation's code-level prediction. No threshold was redefined, narrowed, or
loosened to attempt a pass, and no entry was excluded from the comparison. This section states
that plainly, not as a qualification to explain away.

## Design Decision DD1's resolution: option (b), exact Phase 1 request-shape parity

Architecture Review ruled in favor of Plan's recommended option (b): this recomparison uses the
**exact same request shape** as Phase 1's own comparison — every `_run_knowledge_context(query_text)`
call uses the gateway's own default `budget_tokens` (`DEFAULT_BUDGET_TOKENS = 4000`), with no
per-entry override to try to shrink the response under the cache-write size cap. This was a
deliberate choice, not an oversight: shrinking `budget_tokens` specifically because the real
default triggers the size-cap REJECT would answer a different, narrower question ("does the cache
mechanism work at all for an artificially small payload") than the one this ticket exists to
answer ("does caching make the real, default-shaped gateway response measurably faster/smaller").
See `staging_artifacts/TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON/plan.md` DD1 for the full
reasoning. No `budget_tokens_used` field in the committed fixture ever differs from `4000`.

## Why 0/7: the real size-cap finding, confirmed by direct measurement

`tools/knowledge_gateway_redaction.py::check_size_cap()` rejects any cache write whose redacted
payload exceeds `MAX_PAYLOAD_BYTES = 8192` bytes. Every one of the 7 corpus entries' real response
payload is well over that cap under the default request shape:

| Entry | cold gateway_tokens | implied bytes (≈ tokens×4) | vs. 8192-byte cap | cache_write_rejection_reason |
|---|---|---|---|---|
| Q1_authoritative_state | 2653 | ~10,612 | +30% over | `oversized_payload` |
| Q2_symbol_lookup | 4993 | ~19,972 | +144% over | `oversized_payload` |
| Q3_requirement_completeness | 2851 | ~11,404 | +39% over | `oversized_payload` |
| Q4_historical_rationale | 2739 | ~10,956 | +34% over | `oversized_payload` |
| Q5_test_impact | 4939 | ~19,756 | +141% over | `oversized_payload` |
| Q6_ticket_status | 2822 | ~11,288 | +38% over | `oversized_payload` |
| Q7_negative_knowledge | 7637 | ~30,548 | +273% over | `oversized_payload` |

Every single entry's cache write was rejected with `rejection_category == "oversized_payload"` —
captured by a real, pass-through spy on `tools.knowledge_gateway_redaction.evaluate_write_candidate`
(DD3; `perform_cache_write()` itself always returns `None` and discards this information, so a spy
is the only way to observe it). No entry's "MISS" is a bare, mechanism-less label — every one names
the real reason. This confirms, by live measurement rather than code-level prediction alone,
Investigation's central finding: **the deployed cache's size cap (8 KB) is smaller than every one
of this gateway's real, default-budget response payloads (10.6–30.5 KB).**

Both cache-hit-verification signals agree on every entry, with zero disagreement (`signal_anomaly`
is `null` for all 7 entries): the `assemble_packet` provider-round-trip spy recorded exactly 2 calls
(cold + warm) for every entry, and the direct SQL `hit_count` delta was exactly `0` for every entry.
Neither signal was ever inferred from `response["cache"]` alone (DD2).

## §4.1 — Minimum latency threshold (warm-path only)

**Formula:** gateway warm-hit end-to-end latency ≤ 50% × (Phase 0 fixture's average
`combined.wall_time_ms`), re-derived live from the fixture — **935.32 ms** for the currently-
committed Phase 0 fixture. Per AC2, `cold_call_wall_time_ms` is never used for this threshold's
`pass` determination — only `warm_call_wall_time_ms`, whatever the real number is.

**Result: FAIL, 0/7.**

| Entry | providers_selected | cold_call_wall_time_ms | warm_call_wall_time_ms | threshold_ms | Result |
|---|---|---|---|---|---|
| Q1_authoritative_state | context_search | 5404.1 | 1631.7 | 935.32 | FAIL |
| Q2_symbol_lookup | graphify | 2686.1 | 2802.8 | 935.32 | FAIL |
| Q3_requirement_completeness | context_search | 1513.8 | 1506.8 | 935.32 | FAIL |
| Q4_historical_rationale | context_search | 1608.5 | 1495.5 | 935.32 | FAIL |
| Q5_test_impact | graphify | 2562.3 | 2560.1 | 935.32 | FAIL |
| Q6_ticket_status | context_search | 1521.9 | 1493.5 | 935.32 | FAIL |
| Q7_negative_knowledge | context_search, graphify | 2662.1 | 2557.6 | 935.32 | FAIL |

**Honest note:** for `Q1_authoritative_state`, the warm call (1631.7 ms) is noticeably faster than
the cold call (5404.1 ms) despite being a structurally genuine MISS (no cache row was ever written
— `cache_write_rejection_reason: "oversized_payload"`). This speedup is real but has nothing to do
with caching: it reflects ordinary warm-process effects (e.g. OS filesystem cache, in-process model/
index state already loaded from the first call) that would apply to *any* two successive calls of
the same query, cached or not. It is reported honestly as the real warm-path number this threshold
is computed against, but it must not be read as evidence of a working cache for this entry — the
`cache_status_warm: "MISS"` and `cache_write_rejection_reason: "oversized_payload"` fields on this
same entry are the authoritative record of what actually happened. Every other entry's warm call is
roughly the same latency as its cold call, consistent with 0 genuine hits.

## §4.2 — Minimum token-reduction threshold (cold and warm, computed separately)

**Formula:** gateway packet token count (`kgmcp_char_heuristic_v1` applied to the full real
`json.dumps(response)` payload) ≤ 50% × (Phase 0 fixture's average
`combined.serialized_tokens_estimate`), re-derived live — **1263.57 tokens** for the currently-
committed Phase 0 fixture. Computed independently for the cold and the warm response of every
entry — never assumed, never copied from one to the other.

**Result: FAIL, 0/7 (cold). FAIL, 0/7 (warm).**

| Entry | cold gateway_tokens | warm gateway_tokens | threshold_tokens | Cold Result | Warm Result |
|---|---|---|---|---|---|
| Q1_authoritative_state | 2653 | 2653 | 1263.57 | FAIL | FAIL |
| Q2_symbol_lookup | 4993 | 4944 | 1263.57 | FAIL | FAIL |
| Q3_requirement_completeness | 2851 | 2851 | 1263.57 | FAIL | FAIL |
| Q4_historical_rationale | 2739 | 2739 | 1263.57 | FAIL | FAIL |
| Q5_test_impact | 4939 | 4939 | 1263.57 | FAIL | FAIL |
| Q6_ticket_status | 2822 | 2822 | 1263.57 | FAIL | FAIL |
| Q7_negative_knowledge | 7637 | 7637 | 1263.57 | FAIL | FAIL |

**Honest note on DD5's prediction:** Investigation predicted that for any entry reaching a genuine
`cache_status_warm == "HIT"`, warm tokens would never be smaller than cold tokens (a genuine hit
response replays the stored cold payload plus an extra `cache_key_version` field). **No entry in
this real run reached a genuine HIT, so this prediction was never put to the test.** Separately,
`Q2_symbol_lookup`'s warm token count (4944) came in *smaller* than its cold count (4993) — this is
not a violation of DD5 (DD5's invariant applies only to genuine hits), it is ordinary run-to-run
variation in `graphify`'s own output between two independent, uncached invocations of the same
query. No assumption that caching alone would satisfy §4.2 was made or needed — the epic's own
Out-of-Scope explicitly forbids that assumption, and this run does not make it: caching produced
zero genuine hits, so it had zero opportunity to affect token count either way for this run.

## §4.3 — No-regression-recall threshold

**Formula:** for a given corpus query, the gateway's `sources_recalled` set must be a superset of
the union of that fixture entry's `context_search.sources_recalled` list and whatever authoritative
sources the fixture's `graphify` result for that entry would resolve to, evaluated **per query**.
Computed from the **cold** response for every entry (Plan Step 3 decision — see fixture's
`threshold_4_3_recall_cold.derivation` for the full reasoning: a genuine hit's content is identical
to the cold response that produced it, and no entry in this run reached a genuine hit anyway, so a
separately-labeled "warm recall" number would just be a second cold measurement relabeled).

**Result: FAIL, 0/7.**

| Entry | providers_selected | missing_sources count (this run) | missing_sources count (Phase 1, recorded) | Result |
|---|---|---|---|---|
| Q1_authoritative_state | context_search | 4 / 8 | 4 / 8 | FAIL |
| Q2_symbol_lookup | graphify | 8 / 8 | 8 / 8 | FAIL (expected — see below) |
| Q3_requirement_completeness | context_search | 2 / 8 | 2 / 8 | FAIL |
| Q4_historical_rationale | context_search | 1 / 8 | 1 / 8 | FAIL |
| Q5_test_impact | graphify | 8 / 8 | 8 / 8 | FAIL (expected — see below) |
| Q6_ticket_status | context_search | 3 / 8 | 3 / 8 | FAIL |
| Q7_negative_knowledge | context_search, graphify | 3 / 8 | 3 / 8 | FAIL |

**Honest note — reported, not assumed improved:** this ticket's own Scope named
`TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION`'s evidence-ID normalization fix as something
this recomparison would re-exercise. That fix was already in effect (and confirmed unaffected by
the cache-wiring work) *before* Phase 1's own comparison ran — Phase 1's own recorded per-entry
missing-source counts (4/8, 8/8, 2/8, 1/8, 8/8, 3/8, 3/8) already reflect it. This recomparison's
real, live counts are **identical** to Phase 1's own recorded counts, entry for entry. No further
improvement occurred, and none was fabricated or assumed — the fix was already fully reflected by
the time Phase 1 measured it, and both `Q1/Q3/Q4/Q6/Q7`'s residual misses (the `doc_id`-vs-
`source_path` structural mismatch Phase 1's own results doc documented) and `Q2/Q5`'s architectural
single-provider-routing miss persist unchanged.

### Q2/Q5: expected FAIL, routing-design behavior, not a defect (reused from Phase 1's own narrative)

The real router (`tools/knowledge_gateway_router.py::ROUTING_TABLE`) selects `graphify` as the
**sole** primary provider for `symbol_lookup_callers_references` (Q2) and `test_impact_of_change`
(Q5) — confirmed against a real `route()` call inside this ticket's own runner, not assumed.
`context_search` is therefore never consulted for these two entries, so `response["context"]`
structurally contains zero `context_search`-derived items, and 100% of each entry's 8 baseline
sources are reported missing. This is the single-primary-provider routing design working exactly as
designed — not an implementation defect, and not something this ticket alters (by widening routing)
to force a pass. This ticket's own Scope predicted this exact, unchanged outcome, and that is what
the live run shows.

## Overall honest verdict

**§4.1: FAIL (0/7).** **§4.2 cold: FAIL (0/7). §4.2 warm: FAIL (0/7).** **§4.3: FAIL (0/7) — FAIL
for Q2/Q5 exactly as predicted (expected, by design, per the real single-primary-provider routing
table), and FAIL for the remaining 5 entries too, for the same structural `doc_id`-vs-`source_path`
reason Phase 1's own results doc documented, unchanged by this run.**

**Genuine cache-hit count: 0/7.** Phase 2's real cache-write path, under the exact same request
shape Phase 1 used, cannot demonstrate a working warm-hit path against this gateway's real,
default-budget response sizes — every one of the 7 corpus entries' response payload exceeds the
deployed cache's 8 KB size cap. This is not characterized as a partial success or as "Phase 2
succeeded" in any blanket sense; every threshold misses, for every entry, and the central §4.1/§4.2
warm-hit measurability question this ticket exists to resolve resolves honestly to "not
measurable as a genuine warm-hit under the current size cap and default request shape." This
finding is informative evidence for a future, separate, human-reviewer decision about whether to
widen the size cap, change the default response shape, or otherwise revisit the cache's design —
this ticket does not itself make or recommend that decision, per its own Out of Scope section.

## Cross-references

- `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` — the runner that produced this
  recomparison, including the cold+warm double-call loop, both cache-hit-verification spies, and
  the threshold-computation functions (importing, never reimplementing, Phase 1's own
  `_normalize_phase1_source_id`/`_path_only`/`_compute_threshold_4_3`).
- `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` — full per-entry, per-
  threshold committed data from the real run this document reports.
- `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` — the frozen Phase 1
  comparison this recomparison measures against (read-only, never modified by this ticket).
- `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` — the frozen Phase 0
  baseline both comparisons measure against (read-only).
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4 — the three
  predeclared threshold formulas this document reports against, unedited.
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` — the Phase 1 result
  this recomparison extends, never edited by this ticket.
- `tools/knowledge_gateway_redaction.py::check_size_cap()`,
  `tools/knowledge_gateway_redaction.py::MAX_PAYLOAD_BYTES` — the real 8 KB cache-write size cap
  responsible for this run's 0/7 genuine-cache-hit result.
- `staging_artifacts/TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON/plan.md` DD1 — the Architecture
  Review ruling (option (b), exact Phase 1 request-shape parity) governing this ticket's own request
  shape.
