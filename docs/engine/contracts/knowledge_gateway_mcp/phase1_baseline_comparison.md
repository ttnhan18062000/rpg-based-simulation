---
status: historical
layer: ai
authority: P1
audience: agent
tags: [ai, mcp, testing]
---

# Knowledge Gateway MCP — Phase 1 Baseline Comparison Results

Source ticket: `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` (5th and final child of the
Knowledge Gateway MCP Phase 1 epic). This document reports, honestly, the outcome of running the
real Phase 1 gateway (`tools/knowledge_gateway_mcp.py::_run_knowledge_context()`) against the
Phase 0 measurement-baseline corpus and computing
`measurement_baseline_contract.md` §4's three predeclared promotion thresholds against the real
numbers. Full per-entry data is committed at
`tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json`, produced by
`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`.

## Headline result: all three §4 thresholds FAIL, in aggregate and for every one of the 7 entries

| Threshold | Aggregate result | Pass count |
|---|---|---|
| §4.1 Minimum latency | **FAIL** | 0 / 7 |
| §4.2 Minimum token reduction | **FAIL** | 0 / 7 |
| §4.3 No-regression recall | **FAIL** | 0 / 7 |

This is a real, comprehensive miss — not only the Q2/Q5 recall miss the Plan phase's Design
Decision D4 predicted from the routing table alone. Every threshold's own formula, computed live
against the real fixture and the real gateway response, evaluates to `False` for every one of the
7 corpus entries. No threshold was redefined, narrowed, or loosened to attempt a pass, and no
entry was excluded from the comparison. This section states that plainly, not as a qualification
to explain away.

## Scope-text correction (Design Decision D1)

The ticket's own Scope text said gateway latency would be recorded "via the now-wired
`retrieval_events.py` Wrapper functions." This was factually wrong as of the real Phase 1 code:
`wrap_hybrid_retrieval()`, `wrap_retrieval_cache_check()`, and `wrap_context_packet_assembly()`
are implemented but invoked by no live call site in `tools/knowledge_gateway_mcp.py`
(`tests/tools/test_knowledge_gateway_mcp.py::test_wrapper_functions_genuinely_not_applicable_zero_invoked`
proves this by spying on all 3 and asserting zero calls during a real invocation). Latency was
instead recorded with external `time.perf_counter()` wrapped directly around each
`_run_knowledge_context(query_text)` call — exactly mirroring
`tools/agent-monitoring/kgmcp_baseline_runner.py`'s own external-timing precedent for the Phase 0
direct-tool baseline. No wrapper call site was invented to match the ticket's inaccurate wording.

## §4.1 — Minimum latency threshold

**Formula:** gateway warm-hit end-to-end latency ≤ 50% × (Phase 0 fixture's average
`combined.wall_time_ms`), re-derived live from the fixture on every run —
**935.32 ms** for the currently-committed Phase 0 fixture.

**Result: FAIL, 0/7.**

| Entry | providers_selected | gateway_wall_time_ms | threshold_ms | Result |
|---|---|---|---|---|
| Q1_authoritative_state | context_search | 5325.8 | 935.32 | FAIL |
| Q2_symbol_lookup | graphify | 2650.2 | 935.32 | FAIL |
| Q3_requirement_completeness | context_search | 1686.9 | 935.32 | FAIL |
| Q4_historical_rationale | context_search | 1497.5 | 935.32 | FAIL |
| Q5_test_impact | graphify | 2627.6 | 935.32 | FAIL |
| Q6_ticket_status | context_search | 1469.7 | 935.32 | FAIL |
| Q7_negative_knowledge | context_search, graphify | 2521.8 | 935.32 | FAIL |

**Honest caveat, stated plainly, not as an excuse for the FAIL:** §4.1's own formula in
`measurement_baseline_contract.md` §4.1 is framed against a future gateway's **warm-hit**
end-to-end latency. Phase 1 has **no cache at all** — `knowledge_status`'s own response
explicitly omits every cache-specific field because "no cache exists yet" (Phase 2, not yet
built; see `tools/knowledge_gateway_mcp.py::_run_knowledge_status()`'s docstring). Every one of
the 7 measured calls above is therefore necessarily a cold call — Phase 1 today cannot produce a
"warm-hit" state for this threshold to be measured against. This is a genuine, structural gap
between what §4.1 was written to measure and what Phase 1, as it exists today, is capable of
producing — not a redefinition of the threshold. The threshold is still computed and reported
exactly as written, against the only real number Phase 1 can produce today, and it FAILS.

## §4.2 — Minimum token-reduction threshold

**Formula:** gateway packet token count (`kgmcp_char_heuristic_v1` applied to the full real
`json.dumps(response)` payload) ≤ 50% × (Phase 0 fixture's average
`combined.serialized_tokens_estimate`), re-derived live from the fixture —
**1263.57 tokens** for the currently-committed Phase 0 fixture.

**Result: FAIL, 0/7.**

| Entry | gateway_tokens | threshold_tokens | Result |
|---|---|---|---|
| Q1_authoritative_state | 2649 | 1263.57 | FAIL |
| Q2_symbol_lookup | 4999 | 1263.57 | FAIL |
| Q3_requirement_completeness | 2846 | 1263.57 | FAIL |
| Q4_historical_rationale | 2734 | 1263.57 | FAIL |
| Q5_test_impact | 4934 | 1263.57 | FAIL |
| Q6_ticket_status | 2817 | 1263.57 | FAIL |
| Q7_negative_knowledge | 7633 | 1263.57 | FAIL |

**Honest note:** the Phase 1 response is a richer, structured payload than Phase 0's raw
concatenation of context-search results and graphify stdout — it separately carries
`statements[]`, `context[]`, `evidence[]`, `conflicts[]`, and provenance/verification metadata,
each with its own JSON field names and often overlapping representations of the same underlying
evidence (e.g. the same source appears in both `context[]` and `evidence[]`). That structural
overhead, plus the fact that single-primary-provider routing was expected to reduce token volume
by *not* double-calling both providers, evidently does not net out to a token count below the
threshold for any of the 7 entries — the gateway's real token count is measured and reported as
is, never estimated.

## §4.3 — No-regression-recall threshold

**Formula:** for a given corpus query, the gateway's `sources_recalled` set must be a superset of
the union of that fixture entry's `context_search.sources_recalled` list and whatever
authoritative sources the fixture's `graphify` result for that entry would resolve to, evaluated
**per query**.

**Result: FAIL, 0/7** — including, but not limited to, the two entries predicted at Plan time.

| Entry | providers_selected | missing_sources count | Result |
|---|---|---|---|
| Q1_authoritative_state | context_search | 4 / 8 | FAIL |
| Q2_symbol_lookup | graphify | 8 / 8 | FAIL (expected — see below) |
| Q3_requirement_completeness | context_search | 2 / 8 | FAIL |
| Q4_historical_rationale | context_search | 1 / 8 | FAIL |
| Q5_test_impact | graphify | 8 / 8 | FAIL (expected — see below) |
| Q6_ticket_status | context_search | 3 / 8 | FAIL |
| Q7_negative_knowledge | context_search, graphify | 3 / 8 | FAIL |

### Design Decision D2 — evidence-ID normalization rule (applied to every entry above)

Phase 1's evidence identity (`tools/knowledge_gateway_packet_assembly.py::_evidence_id_for_context_search_result`,
L100-125) is one of `doc:{source_path}#{anchor}`, `ticket:{TCK-id}`, or `file:{source_path}`.
Phase 0's `sources_recalled` (`tools/search_mcp.py`'s raw `doc_id`) carries none of these
prefixes. Before comparison, every Phase 1 source ID is normalized: strip the `doc:`/`ticket:`/
`file:`/`symbol:` prefix; for `doc:`-prefixed IDs, additionally strip a leading `docs/` and a
`.md` immediately before the anchor (or at end of string). Comparison then matches on normalized
**path only** (the part before `#`) — anchor-level exact match is reported as an informational,
non-blocking sub-field (`anchor_exact_matches`), never a source of a false miss driven purely by
cosmetic anchor re-slugging drift (Phase 1's anchor is independently re-derived via `_slugify()`
and may not byte-for-byte match Phase 0's).

### Design Decision D3 — graphify half of the union: N/A, not faked

**No Phase 0 graphify source baseline exists to compare against.** The Phase 0 fixture's
`graphify` sub-object records only `raw_stdout_bytes` (a byte count) — never a source list — so
there is no ground truth to diff the gateway's graphify-derived evidence against. This comparison
therefore evaluates §4.3 using the `context_search` half of the union only, for every entry. Every
`threshold_4_3_recall` sub-object in the committed fixture carries
`"graphify_half_status": "N/A"` stating this explicitly — it is never silently treated as
empty-and-passing.

### Design Decision D4 — Q2/Q5: expected FAIL, routing-design behavior, not a defect

The real router (`tools/knowledge_gateway_router.py::ROUTING_TABLE`) selects `graphify` as the
**sole** primary provider for `symbol_lookup_callers_references` (Q2) and `test_impact_of_change`
(Q5) — confirmed against a real `route()` call inside this ticket's own runner and test suite, not
assumed. `context_search` is therefore never consulted for these two entries, so
`response["context"]` structurally contains zero `context_search`-derived items, and 100% of each
entry's 8 baseline sources are reported missing. This is the single-primary-provider routing
design from `TCK-20260815-KGMCP-P1-QUERY-ROUTER` (INFRA-335, Done, frozen) working exactly as
designed — not an implementation defect, and not something this ticket alters to force a pass.

### An additional, genuine root cause discovered during Implementation — beyond DD2/DD4's prediction

The Plan phase's Design Decision D2 assumed Phase 0's `doc_id` and Phase 1's `source_path` refer
to the *same underlying path*, differing only by prefix/decoration. Running the real comparison
surfaces a second, independent, structural reason recall misses on entries that route to
`context_search` (Q1, Q3, Q4, Q6, Q7 — not only Q2/Q5): Phase 0's `doc_id`
(`tools/knowledge_search.py:293`, `doc_id = f"{section}/{stem}"`) is built from only the **first**
path segment under `docs/` plus the file stem, collapsing any deeper subdirectory nesting. Phase
1's `source_id` is built from the **full** `source_path`
(`tools/knowledge_gateway_packet_assembly.py:109`). For a document nested more than one level
deep — e.g. `docs/engine/contracts/infrastructure_compat_contract.md` — Phase 0 recorded
`doc_id = "engine/infrastructure_compat_contract"` (dropping `contracts/`) while Phase 1 builds
`source_id = "doc:docs/engine/contracts/infrastructure_compat_contract.md#..."`, which normalizes
to `"engine/contracts/infrastructure_compat_contract#..."` — a different path string even after
DD2's documented normalization is applied correctly. This is a real, pre-existing divergence
between `tools/search_mcp.py`'s two own ID fields on the *same result object* (`doc_id` vs
`path`), not a bug in this ticket's normalization function, and not something this ticket "fixes"
by inventing a smarter truncation-aware normalization rule — DD2's normalization rule is applied
exactly as documented, and this residual mismatch is reported honestly as an additional cause of
the broader-than-predicted §4.3 miss, not papered over.

A second, smaller honest note: the live corpus/document index reflects the *current* state of
`docs/`/`tickets/`, which continues to evolve after the Phase 0 fixture was recorded
(`recorded_at_utc: 2026-08-15T05:09:04Z`) — this comparison ran at `2026-08-15T12:08:34Z`, roughly
7 hours later, and several `gateway_sources` entries (e.g. Q6's
`TCK-20260814-KGMCP-MEASUREMENT-BASELINE`) reflect tickets/docs that did not exist, or were not
indexed, at Phase 0 recording time. This natural corpus drift is a real, honest confound on top of
the two structural causes above, not a defect in either system.

## Overall honest verdict

**§4.1: FAIL (0/7).** **§4.2: FAIL (0/7).** **§4.3: FAIL (0/7) — FAIL for Q2/Q5 exactly as
predicted (expected, by design, per the real single-primary-provider routing table), and FAIL for
the remaining 5 entries too, for the additional structural `doc_id`-vs-`source_path` reason above.**

Phase 1 does **not** meet any of Phase 0's three predeclared promotion thresholds against this
7-entry corpus, as measured on 2026-08-15. This is not characterized as a partial success or as
"Phase 1 succeeded" in any blanket sense — every threshold misses, for every entry. This finding
is informative evidence for a future, separate, human-reviewer decision about whether and how to
proceed toward Phase 2 (real provider-result cache, which would address §4.1's warm-hit gap) and
beyond; this ticket does not itself make or recommend that decision, per its own Out of Scope
section.

## Cross-references

- `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` — the runner that produced this
  comparison, including the evidence-normalization and threshold-computation functions.
- `tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json` — full per-entry, per-
  threshold committed data.
- `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` — the frozen Phase 0
  baseline this comparison measures against (read-only, never modified by this ticket).
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4 — the three
  predeclared threshold formulas this document reports against, unedited.
- `tools/knowledge_gateway_router.py::ROUTING_TABLE` — the real, frozen 7-row routing table
  responsible for Q2/Q5's expected recall miss.
- `tools/search_mcp.py`, `tools/knowledge_search.py:293` — the `doc_id` truncation behavior
  underlying the additional root cause discussed above.
