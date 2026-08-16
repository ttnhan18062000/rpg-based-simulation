---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, mcp, testing]
---

# Knowledge Gateway MCP — Phase 4 Direct-Tool Comparison Results

Source ticket: `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON` — Phase 4's own acceptance-measurement
ticket, mirroring `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`/`TCK-20260815-KGMCP-P2-BASELINE-
RECOMPARISON`/`TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`'s own "no result may be assumed,
only measured" Gate Integrity discipline. This ticket answers a genuinely new question those
tickets didn't: not "does the cache produce hits," but "does calling the gateway at all (vs. calling
Context Search/Graphify/the new Parity Ledger adapter directly) produce a real, measurable
advantage." Full per-entry data is committed at
`tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json`, produced by
`tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`.

## Why every entry was re-run fresh, not compared against Phase 1-3 fixtures

`TCK-20260816-KGMCP-P4-PARITY-ADAPTER` changed `ROUTING_TABLE["requirement_completeness_verification"]`
from a dead-end to a live `("context_search", "parity_ledger")` row — every Phase 1-3 fixture's
`Q3_requirement_completeness` gateway-side number predates this and is stale beyond dispute. More
broadly, general repo-state drift since Phase 1-3 (many other tickets, cache rows, and doc changes
landed in the meantime) means treating any of the other 6 entries' historical fixture numbers as
"still current" would be an unverified assumption, not a measured fact. This ticket therefore ran
all 7 entries fresh, both the gateway side and the direct-tool side, rather than mixing 6 stale + 1
fresh numbers in one table.

## Headline result: the gateway shows no genuine latency or token advantage over direct tool use for any of the 7 query types in this fresh, cold-cache run

| Entry | Routing shape | Gateway ms | Direct combined ms | Latency ratio | Gateway tokens | Direct combined tokens | Token ratio | Reviewer verdict |
|---|---|---|---|---|---|---|---|---|
| Q1_authoritative_state | definition_terminology_architecture | 5361 | 1427 | 3.76x slower | 2668 | 2562 | 1.04x heavier | direct_equal_or_better |
| Q2_symbol_lookup | symbol_lookup_callers_references | 2742 | 1316 | 2.08x slower | 4980 | 2622 | 1.90x heavier | direct_equal_or_better |
| Q3_requirement_completeness | requirement_completeness_verification | 3251 | 1138 | 2.86x slower | 2869 | 2680 | 1.07x heavier | mixed |
| Q4_historical_rationale | ticket_historical_rationale | 1654 | 1107 | 1.49x slower | 2753 | 2566 | 1.07x heavier | direct_equal_or_better |
| Q5_test_impact | test_impact_of_change | 2610 | 1174 | 2.22x slower | 4932 | 2495 | 1.98x heavier | direct_equal_or_better |
| Q6_ticket_status | ticket_work_status | 1537 | 1175 | 1.31x slower | 2836 | 2487 | 1.14x heavier | direct_equal_or_better |
| Q7_negative_knowledge | broad_task_context | 2623 | 1118 | 2.35x slower | 7655 | 2609 | 2.93x heavier | direct_equal_or_better |

**Every single one of the 7 entries is slower and heavier on tokens through the gateway than
calling the direct tool(s) directly, in this fresh, cold-cache run.** No entry is excluded from
this table, no threshold is redefined to flip a real result — this is the real, disclosed output.
This is a materially clearer negative finding than Phase 1's own comparison (universal 1.05x-3.0x
token overhead, but latency slower for only 4/7 entries): here, with all 7 gateway calls genuinely
cold (no warm cache reuse across entries, matching Phase 1's own cold-call precedent), latency lost
for all 7 as well. This does not contradict Phase 3's own finding that a warm (`HIT_L2`) gateway
call beats a cold baseline on latency — that is a different, cache-warm comparison this ticket does
not repeat; this ticket measures the gateway exactly as Phase 1 did, one real call per entry, no
warm-cache advantage assumed.

## Quality axis, part (a): objective source-completeness proxy

**Context-Search half** reuses Phase 1's `_compute_threshold_4_3()` unmodified for its comparison
logic, comparing each entry's own freshly-run direct Context Search call against the real gateway
response's `context[*].source_id` list. `pass: False` for all 7 entries (see per-entry detail
below) — closer inspection during Step 6 (below) shows roughly half of the recorded "misses" are
methodology-shape false positives, not real content loss.

**Graphify half** is new this ticket — closing Design Decision D3's 3-phase-old `"N/A"` gap. For
the 4 entries whose real `providers_selected` included `"graphify"` (Q2, Q5, and the graphify
component of Q7's dual-provider routing — Q7 routes `context_search` + `graphify`), the extracted
`src=<path>` sets from a second, independent, real `match_symbol_name()` call (standing in for the
gateway's own internal invocation) and the direct call's own Graphify stdout were compared via
`_extract_graphify_source_paths()` (`re.findall(r"src=([^\s\]]+)", raw_stdout)`). **Result: 0
missing, 0 extra for every entry where Graphify was routed** — the gateway's Graphify path recalls
exactly the same source set a direct `graphify query` call would. Entries where Graphify was not
part of `providers_selected` (Q1, Q3, Q4, Q6) correctly record `graphify_half_status:
"not_routed_this_entry"`, never a fabricated comparison.

## Quality axis, part (b): disclosed reviewer judgment (not a computed metric)

Per entry, `quality.reviewer_judgment` (`basis: "reviewer_judgment_not_a_computed_metric"`) was
populated by hand, reading both sides' retained raw content (the gateway's full `response` dict and
the direct call's `raw_results`/`raw_stdout`/`entry_result`) — never derived from the objective
`source_completeness` numbers above.

**A genuine, disclosed finding from this hand-reading pass:** for `Q4_historical_rationale` and
`Q6_ticket_status`, the context_search-half's recorded "missing" sources (`TCK-20260523-WORLD-
TEMPLATES` for Q4; `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` and `TCK-20260728-CONTEXT-
PACKET-SCHEMA` for Q6 — the second of which is the literal ticket the query asked the status of)
turned out, on direct inspection of the gateway's own `response["context"]`, to already be present
— just represented under a `file:stored_artifacts/<ticket>/investigation.md` identifier rather than
the bare ticket-id-shaped `doc_id` the direct Context Search call's raw result carries for
`stored_artifacts/` files. This is a real limitation of the imported, frozen
`_normalize_phase1_source_id()`/`_path_only()` (built to reconcile `doc:`/`ticket:`/`file:`/
`symbol:` prefixes, never a bare ticket-id `doc_id` against a `file:`-prefixed `stored_artifacts`
path) — not a real gateway content drop. It is disclosed here and in each entry's own
`reviewer_judgment.rationale`, never silently "corrected" in the objective proxy itself (Step 5's
own Do-Not-Touch guard on `_compute_threshold_4_3()`).

For Q1, Q3, and Q7, the recorded misses (`TCK-20260425-PH8-M3`, `TCK-20260804-RETRIEVAL-RAW-
INVESTIGATION-METRIC`, `TCK-20260405-LOGFIX` respectively) are real, if narrow, content drops: each
is a second `tickets/working_log.csv`-sourced chunk that the gateway's evidence-id builder collapses
into the single `file:tickets/working_log.csv` context item it already keeps (its anchor-dedup logic
only disambiguates `docs/`-prefixed paths, not `file:`-shaped ones) — the specific log line is
genuinely dropped, though the file itself remains cited.

For Q2 and Q5 (graphify-only routing), the context_search-half's misses are a structural routing-
shape effect, not a content bug — reading both sides' answers, the excluded Context Search hits are
triggered by loose keyword overlap rather than real relevance to a pure symbol/test-impact lookup.

**Real per-entry verdicts:** 6 of 7 entries (`Q1`, `Q2`, `Q4`, `Q5`, `Q6`, `Q7`) are judged
`direct_equal_or_better`; 1 of 7 (`Q3_requirement_completeness`) is judged `mixed` — its real,
narrow content loss and materially higher cost are offset by genuine new workflow convenience (one
gateway call now returns Context Search excerpts plus a live Parity Ledger check together, where the
direct route needs two separate tool calls). No entry is judged `gateway_equal_or_better` in this
real, honest measurement. Full per-entry rationale (citing the specific real source_id/path
involved in each case) is in the committed fixture's `quality.reviewer_judgment.rationale` field —
not restated here in full.

## No gold-answer limitation (disclosed, not resolved)

The frozen 7-entry corpus (`kgmcp_baseline_corpus.CORPUS`) carries only `id`, `query_text`,
`routing_shape`, `use_case` per entry — no expected-answer, expected-source-set, or rubric field
exists anywhere in this repository. "Quality" therefore cannot be scored as an objective pass/fail
the way latency/tokens can. The two proxies used here are explicitly, structurally separate:
`source_completeness` is objectively computed (method disclosed above) but is a completeness proxy,
not an answer-correctness score; `reviewer_judgment` is an explicitly disclosed, necessarily
subjective human/agent judgment call, never dressed up as a computed metric. This is a real
limitation of the corpus, not of this ticket's method, and is not resolved by inventing a rubric.

## The `Q3_requirement_completeness` Parity Ledger route, exercised for the first time

`tools/parity_index.py::entry(query_text)` was called directly with the raw query text
(`"Is the read_count_correlation feature fully implemented?"`) as `entry_id` — exactly mirroring
`tools/knowledge_gateway_router.py::_run_parity_provider()`'s own real convention. The real result:
`found: False` (the free-text sentence does not match a literal parity-ledger entry id — expected,
honest provider behavior, not an error), followed by a real `check_staleness()` call reporting
`status: "FRESH"`. The gateway's own real `_run_knowledge_context()` call for the same query shows
`providers_selected` includes both `"context_search"` and `"parity_ledger"` — confirming
`INFRA-351`'s routing change is live and reachable end-to-end, not stale Phase 1-3 dead-end
behavior.

## Overall honest verdict

No query type shows a genuine gateway advantage on latency or token cost in this fresh, cold-cache
run — all 7 entries are slower and heavier through the gateway than the equivalent direct-tool
call(s). On the quality/completeness axis, the picture is closer to parity than the cost numbers
suggest: the Graphify half is an exact match everywhere it was routed, and roughly half of the
Context-Search half's recorded "misses" turned out, on hand inspection, to be normalization-shape
false positives rather than real content loss. This is not characterized as the gateway being
broadly superior or inferior to direct tool use in any blanket sense — per this ticket's own Out of
Scope, that determination, and any decision to fix the real cost disadvantage found here, is a
separate, later, human-reviewer call.

## Cross-references

- `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py` — the runner that produced
  this measurement, including the direct-tool call functions, the gateway call function, the
  source-completeness computation (importing, never reimplementing, Phase 1's own
  `_compute_threshold_4_3`/`_normalize_phase1_source_id`/`_path_only`), and the new
  `_extract_graphify_source_paths()` regex extractor.
- `tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json` — full per-entry, real
  committed data, including the hand-authored `quality.reviewer_judgment` objects.
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` — the cold-path
  baseline comparison methodology this ticket's `_compute_threshold_4_3()` reuse builds on.
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` — the
  warm-cache latency/token measurement this ticket's own cold-call numbers do not contradict (a
  different, cache-warm comparison).
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4's fourth bullet ("Compare gateway
  packets against existing direct-tool behavior") — the requirement this document answers.
- `staging_artifacts/TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON/plan.md` — Architecture-Review-
  approved plan (2 passes) governing this ticket's own design, including the Step 1 full-fresh-run
  decision, the Step 5 derivation-string provenance fix, and the Step 6 falsifiable
  reviewer-judgment procedure.
