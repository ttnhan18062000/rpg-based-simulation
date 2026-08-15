---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-BASELINE-COMPARISON
artifact_type: investigation
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260815-KGMCP-P1-BASELINE-COMPARISON

## Current Behavior

### The Phase 0 corpus and fixture (read verbatim, must be reused, never modified)
`tools/agent-monitoring/kgmcp_baseline_corpus.py` (`CORPUS_VERSION = 1`) defines exactly 7 entries
(`Q1_authoritative_state` … `Q7_negative_knowledge`), each with `id`, `query_text`,
`routing_shape`, `use_case`. It also defines `kgmcp_char_heuristic_v1_token_count(text)` =
`math.ceil(len(text.encode("utf-8")) / 4)` — pure data + one pure helper, no live calls.

`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` is the real, committed
Phase 0 fixture, produced by `tools/agent-monitoring/kgmcp_baseline_runner.py::main()`. Per entry
it records `context_search` (`latency_ms`, `tool_call_count=1`, `results_count`,
`sources_recalled` = `[r["doc_id"] for r in results]`, `derivation`), `graphify` (`latency_ms`,
`tool_call_count=1`, `raw_stdout_bytes`, `derivation` — **no `sources_recalled` field for
graphify, ever**), and `combined` (`wall_time_ms` = sum of the two latencies,
`tool_call_count=2`, `serialized_tokens_estimate` via the char heuristic over
`json.dumps(context_search results) + graphify raw stdout`). Every one of the 7 Phase 0 entries
called **both** `_run_search(query_text, top_k=8)` and `graphify query <text>` unconditionally —
Phase 0's runner never routed.

### `kgmcp_baseline_runner.py` (Phase 0 shape to mirror)
`_run_context_search()` / `_run_graphify()` each time with `time.perf_counter()`, `run_corpus()`
loops the 7 `CORPUS` entries and returns the report dict, `main()` writes it to the fixture path
with `json.dumps(..., indent=2, sort_keys=True)`. `run_corpus()` is deliberately kept separate
from `main()` so tests can exercise the full live-call path without re-writing the pinned fixture
(`test_zero_mutation_of_real_agent_monitoring_corpus`, `tests/tools/test_kgmcp_measurement_baseline.py:192-215`).
This ticket's new runner should mirror this `run_corpus()`/`main()` split exactly, targeting the
real gateway instead of direct tool calls.

### §4's predeclared thresholds (exact formulas, `measurement_baseline_contract.md` lines 186-222)
- **§4.1 Minimum latency threshold:** a future gateway's warm-hit end-to-end latency must be ≤ 50%
  × (corpus-wide average of `combined.wall_time_ms` across the fixture's 7 entries) =
  **935.32 ms** (computed from the currently-committed fixture's average of 1870.648 ms).
- **§4.2 Minimum token-reduction threshold:** the gateway's packet token count (via
  `kgmcp_char_heuristic_v1`) must be ≤ 50% × (corpus-wide average of
  `combined.serialized_tokens_estimate`) = **1263.57 tokens**, per query.
- **§4.3 No-regression-recall threshold:** for a given corpus query, the gateway's
  `sources_recalled` set must be a superset of (or equal to) the union of that fixture entry's
  `context_search.sources_recalled` list and "whatever authoritative sources the fixture's
  `graphify` result for that entry would resolve to" — evaluated **per query**, not only in
  aggregate. §4.4 explicitly scopes these three thresholds as Phase 0's own bar, never Phase 3's
  §21 pilot bar.

### The real Phase 1 gateway call path
`tools/knowledge_gateway_mcp.py::_run_knowledge_context(query, mode=None, budget_tokens=None,
changed_paths=None, include_history=None, evidence_detail=None) -> dict` (L139-287) is explicitly
documented as "Core logic shared by the registered MCP tool and any direct/test-mode caller" — a
plain importable module-level function, **not** gated behind any MCP server/session context. It:
validates the request against `REQUEST_SCHEMA`, calls `_kgr.route(query)`
(`knowledge_gateway_router.py::route()`), calls `_kgpa.assemble_packet(routing_decision, query,
effective_budget)` (`knowledge_gateway_packet_assembly.py::assemble_packet()`), and validates the
response against `RESPONSE_SCHEMA` before returning.

`route()` (`tools/knowledge_gateway_router.py:392-433`) is a 7-row **primary-provider** dispatch,
not "call both providers always" like Phase 0's runner did:

| Corpus entry | Routing shape matched | `providers_selected` |
|---|---|---|
| Q1_authoritative_state | `definition_terminology_architecture` (kw "what is") | `context_search` only |
| Q2_symbol_lookup | `symbol_lookup_callers_references` (kw "where is"/"defined") | `graphify` only |
| Q3_requirement_completeness | `requirement_completeness_verification` (kw "fully implemented") | `context_search` only |
| Q4_historical_rationale | `ticket_historical_rationale` (kw "why was"/"removed") | `context_search` only |
| Q5_test_impact | `test_impact_of_change` (kw "what tests"/"must run if") | `graphify` only |
| Q6_ticket_status | `ticket_work_status` (kw "current status") | `context_search` only |
| Q7_negative_knowledge | `broad_task_context` (kw "used in this repository") | `context_search` **and** `graphify` |

(Traced by hand against `_classify_routing_shape()`'s `_SHAPE_CLASSIFICATION_ORDER` and
`_SHAPE_KEYWORDS`, `tools/knowledge_gateway_router.py:326-358`; none of the 7 query strings is
identifier-shaped, so all 7 fall through `_match_identifier()` to keyword classification.) **Only
Q7 calls both providers like every one of Phase 0's 7 entries did.** See Risks below — this is
the single most consequential fact for §4.3.

`assemble_packet()` (`knowledge_gateway_packet_assembly.py:585-666`) calls only the providers in
`routing_decision.providers_selected` via `call_providers_for_routing_decision()` (L159-200), using
`_sm._run_search(query_text)` — no `top_k` argument passed, so the module's own default
(`top_k: int = 8` at `tools/search_mcp.py:82`) applies and matches Phase 0's explicit `top_k=8`.
Returned evidence lives at `response["context"][*]["source_id"]` /
`response["evidence"][*]["evidence_id"]`, built by `_evidence_id_for_context_search_result()`
(L100-125, form `doc:<source_path>#<anchor>` from `result["source_path"]`, or `ticket:<id>`, or
`file:<path>`) and `_evidence_id_for_graphify_result()` (L128-134, form `symbol:<query_text>`).
`response["provider_failures"]` is `packet.provider_failures` — the real, always-emitted list
added by the sibling `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS` (INFRA-338), populated only when a
*called* provider actually errors (context_search returns `{"error": ...}`, graphify raises
`TimeoutExpired`/`FileNotFoundError`, or graphify's subprocess returns nonzero) — never populated
for a provider the router simply chose not to call.

There is no `sources_recalled` field anywhere in `knowledge_context_response.schema.json`
(verified: its `properties` keys are `mode, status, freshness, verification, cache, answer,
statements, context, evidence, conflicts, provenance_providers, providers_consulted_this_call,
provider_failures, budget_requested, budget_returned, cache_key_version, error`) — this ticket's
new runner must derive a `sources_recalled`-shaped list itself (most naturally
`[c["source_id"] for c in response["context"]]` or from `response["evidence"]`), and that derived
list's string **format does not match** Phase 0's `sources_recalled` format. Phase 0's `doc_id`
looks like `"simulation/quest_contract#authoritative-status-001"` (no `docs/` prefix, no `doc:`
prefix — `search_mcp.py:132`'s `"doc_id": r.doc_id"`). Phase 1's `source_id` for the same
underlying document looks like `"doc:docs/simulation/quest_contract.md#authoritative-status-001"`
(`doc:` prefix, full `docs/…md` path, independently re-slugified anchor —
`_evidence_id_for_context_search_result`, L100-125). A ticket ID appears as `"TCK-…"` bare in
Phase 0's list vs. `"ticket:TCK-…"` in Phase 1's. **A literal string-set comparison will not match
even when the two runs recalled the exact same underlying document** — see Risks.

### `_run_knowledge_context` in-process calling convention (answers Assumptions/Open Question #1
and Investigate step 6)
`tests/tools/test_knowledge_gateway_mcp.py` already establishes and exercises the exact in-process
pattern this ticket's runner should reuse: `importlib.util.spec_from_file_location(...)` +
`spec.loader.exec_module(mod)` to load `tools/knowledge_gateway_mcp.py` as a standalone module,
then call `mod._run_knowledge_context(query)` directly — no MCP server startup
(`_build_server()`/`.run()`), no stdio transport, no monkeypatch or test-mode flag required. Every
call in that test file (`test_knowledge_context_tool_real_invocation_validates_against_response_schema`
etc.) is a bare, real, unmocked invocation. This settles the ticket's own open question: **the
runner should call `_run_knowledge_context()` in-process directly, exactly mirroring
`kgmcp_baseline_runner.py`'s precedent of calling real underlying functions rather than going
through any wire/transport protocol** — no second harness needs to be built.

### `kgmcp_char_heuristic_v1` — confirmed the correct, already-existing measurement function
(Investigate step 7)
`tools/knowledge_gateway_packet_assembly.py:81-87` defines `kgmcp_char_heuristic_v1(text) ->
int` — the first real callable of the frozen formula
(`ceil(len(text.encode("utf-8"))/4)`), ratified at `redaction_retention_policy.md` §8. It is
identical in formula (not merely "compatible") to
`kgmcp_baseline_corpus.py::kgmcp_char_heuristic_v1_token_count`, which Phase 0's own fixture used.
Both are pure, dependency-free, single-argument functions over `text`. This ticket should reuse
`knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1` (the "real" implementation, per that
module's own docstring framing) to measure the Phase 1 packet's returned-token count — not
reinvent a third copy, and not reuse the corpus module's copy purely because Phase 0's runner
happened to import it from there (both compute the identical formula, but the packet-assembly
module's copy is the one actually exercised on the real return path being measured).

## Mechanics / Engine Constraints
This is agent-infrastructure tooling, not simulation-domain logic — no `docs/mechanics/`,
`src/domains/`, or entity/combat/economy law applies. The controlling constraints are the
project's own engine-contract-equivalent documents for this subsystem:
`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §1-4 (corpus reuse
and threshold formulas, cited above) and `docs/plans/knowledge-gateway-mcp-proposal.md` §8
(routing table), §16 (failure/fallback semantics — `provider_failures` is a §16 concept), §18/§18.1
(measurement points and repeated-demand design), §20 (Phase 1 delivery checklist), §21 (Phase 3
pilot bar, explicitly out of scope for this ticket's own thresholds per §4.4).

## Docs Requiring Update
- `docs/plans/knowledge-gateway-mcp-proposal.md`: Scope requires updating §20's Phase 1 section
  with the comparison outcome once this ticket lands; per this investigation, all 6 existing Phase
  1 bullets are already annotated **Done** by the 4 prior child tickets (verified by direct read,
  lines 1142-1191) and none is naturally this ticket's own bullet to check off — this ticket's
  own contribution is better recorded as a new sentence/bullet appended to the Phase 1 section
  (or a short new paragraph) stating the real comparison outcome, not a retrofit onto an existing
  Done bullet that already describes different, already-shipped work. Flagged honestly per
  Investigate step 9, not silently resolved.
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (new file, per
  ticket Scope): the results doc presenting the comparison and its PASS/FAIL verdict per
  threshold, citing the real new fixture.
- `docs/parity_ledger/infrastructure.yaml`: add a new `INFRA-339` entry (next sequential ID after
  `INFRA-338`), following the exact one-entry-per-ticket precedent this epic has kept since
  INFRA-334 (Phase 0 baseline itself) through INFRA-338 (fail-open tests) — this ticket adds real,
  testable code (new runner script, new fixture, new test suite), which is the same class of
  change every prior sibling ticket ledgered this way.
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`: §4's "Computed
  figure" prose (lines 186-222) is explicitly pinned to the Phase 0 fixture and is not something
  this ticket edits (the Phase 0 baseline numbers do not change) — but if this ticket's own
  Plan phase decides §4.3's comparison method needs a stated normalization rule (see Risks below,
  format mismatch between `doc_id` and `source_id`), that rule belongs in this contract document
  (or its own new document) as a citable formula, not invented silently inside test/runner code
  with no doc trail.

## Parity Ledger Overlap
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-334` through `INFRA-338` entries (all `status:
verified`, `priority: P1`) cover the 5 prior KGMCP Phase 0/Phase 1 child tickets in this same
one-entry-per-ticket sequence. None is P0, so none carries a hard `test_path`-required gate for
this ticket's own change, but this ticket should add `INFRA-339` in the same sequence rather than
amending any existing entry, per that sequence's own established precedent (each entry text
explicitly states it records its own ticket's work rather than amending a sibling's entry — see
`INFRA-338`'s own text, lines 8816-8845, doing exactly this for the identical reason).

## Prior Work
- `stored_artifacts/TCK-20260814-KGMCP-MEASUREMENT-BASELINE/` — Phase 0's own investigation/plan;
  established the corpus, fixture, and threshold formulas this ticket measures against.
- `stored_artifacts/TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE/` — the dependency ticket; its
  Implementation Notes (per `measurement_baseline_contract.md`'s own "Reconfirmed 2026-08-15"
  citations at §2.1/§2.4) already did the full function-by-function re-verification that none of
  `retrieval_events.py`'s 3 Wrapper functions has a real call site in the Phase 1 pipeline — this
  ticket does not need to redo that re-verification, only cite it.
- `tests/tools/test_knowledge_gateway_mcp.py` — establishes the in-process direct-call test
  harness pattern (see above) this ticket's runner should mirror.
- `tests/tools/test_kgmcp_measurement_baseline.py` — the never-silent, derivation-string,
  structural-test convention (AST-based anti-drift guards, `git diff --stat` frozen-file checks,
  one bounded live smoke test rather than a full live re-run on every `pytest` invocation) this
  ticket's new test suite should mirror, per its own Scope line.

## Risks and Open Questions

1. **Ticket Scope text contains a factual error about `retrieval_events.py` wiring — blocks
   literal-as-written implementation.** The ticket's own Scope says to record "gateway latency
   (via the now-wired `retrieval_events.py` Wrapper functions)." This is false as of the real,
   current code: `measurement_baseline_contract.md` §2.1/§2.4 explicitly states (reconfirmed
   2026-08-15 against the real Phase 1 gateway) that `wrap_retrieval_cache_check()` and
   `wrap_context_packet_assembly()` are "implemented but not invoked by any live call site," and
   `tools/knowledge_gateway_mcp.py` "is not imported by `tools/knowledge_gateway_mcp.py` at all
   (verified zero-diff and zero-invocation)." `tests/tools/test_knowledge_gateway_mcp.py`'s
   `test_wrapper_functions_genuinely_not_applicable_zero_invoked` (L190-214) structurally proves
   this by spying on all 3 wrappers and asserting zero calls during a real
   `_run_knowledge_context()` invocation. **This ticket cannot record latency "via the Wrapper
   functions" because they are never on the real call path.** The only available approach is
   external timing — `time.perf_counter()` wrapped directly around the
   `_run_knowledge_context(query)` call — exactly mirroring `kgmcp_baseline_runner.py`'s own
   external-timing precedent for the direct-tool calls. Flagging this rather than assuming an
   answer: Plan should decide whether to (a) proceed with external timing and correct the ticket's
   Scope wording to state this honestly, or (b) treat the mismatch as blocking pending human
   clarification. Given the ticket's own Hard Rule about not silently redefining scope to make
   something appear to pass, (a) with an explicit, stated correction is the substantively honest
   path — inventing a wrapper call site that does not exist to satisfy the literal wording would be
   worse.

2. **§4.3's "no-regression-recall" threshold is very likely to fail on Q2 and Q5, and this appears
   to be by design, not by bug.** The real router (`route()`) selects only the *primary* provider
   for 6 of the 7 corpus entries (see the routing table above) — Phase 0's baseline, by contrast,
   unconditionally called both `context_search` and `graphify` for all 7 entries. For
   `Q2_symbol_lookup` and `Q5_test_impact` (both route to `graphify` only), the real Phase 1
   response will contain **zero** `context_search`-sourced evidence, so it structurally cannot be
   a superset of Phase 0's `context_search.sources_recalled` list for those two entries — not
   because retrieval quality regressed, but because the deliberate single-primary-provider routing
   design (a Done, ledgered decision from `TCK-20260815-KGMCP-P1-QUERY-ROUTER`) never calls that
   provider for those two query shapes. Per the ticket's own Out of Scope ("Redefining or adjusting
   the Phase 0 thresholds... is out of scope... a same-ticket edit that quietly resolves a miss" is
   explicitly forbidden) and its Gate Integrity framing, **this predicted per-query miss must be
   reported honestly as a FAIL for those two entries**, not routed around by force-calling both
   providers (which the real gateway never does) or by silently narrowing what "sources_recalled"
   means until it happens to pass.

3. **§4.3's comparison is format-ambiguous even where both providers ARE called (Q7) or where the
   provider recalled is the same as Phase 0's.** Phase 0's `sources_recalled` strings (raw
   `doc_id`, e.g. `"simulation/quest_contract#authoritative-status-001"`, or bare ticket IDs) do
   not lexically match Phase 1's `source_id`/`evidence_id` strings for the same underlying source
   (`"doc:docs/simulation/quest_contract.md#authoritative-status-001"`,
   `"ticket:TCK-…"`) — see Current Behavior above. A naive `set` superset check over the raw
   strings will report a false regression on every entry, including ones where the same real
   documents were actually recalled. **This needs an explicit, documented normalization rule**
   (e.g., strip the `doc:`/`ticket:`/`file:`/`symbol:` prefix and the `docs/`/`.md` decoration
   before comparing) decided and cited in Plan, not invented ad hoc inside the runner with no
   doc trail — otherwise the comparison's PASS/FAIL verdict is not trustworthy evidence either way.

4. **§4.3's graphify-half of the union formula is genuinely undefined for Phase 0.** The formula
   says the baseline the gateway must not regress below is the union of
   `context_search.sources_recalled` "and whatever authoritative sources the fixture's `graphify`
   result for that entry would resolve to" — but the Phase 0 fixture's `graphify` sub-object has
   no `sources_recalled`-shaped field, only `raw_stdout_bytes` (a byte count, not a source list).
   Resolving "whatever sources graphify's raw stdout would resolve to" requires parsing the raw
   `graphify query` stdout text (committed nowhere in the fixture — only its byte length was
   recorded) into a source-ID list, which is new interpretive logic with no existing precedent in
   this repository. Plan must decide and document how this half of the union is computed, or
   explicitly narrow §4.3 to the `context_search` half only with a stated, honest caveat — silently
   treating the graphify half as empty would understate the true recall bar without saying so.

5. **`Q3_requirement_completeness`'s Phase 0 baseline is itself a Context Search + Graphify-only
   substitution** (its own `notes` field states no Parity Ledger adapter exists yet at Phase 0).
   Phase 1's real routing sends Q3 to `context_search` only (not graphify) — so Q3's real recall
   comparison is really `context_search`-only vs. `context_search`-only, which is more directly
   comparable than Q2/Q5's cross-provider mismatch, but should still cite this history so a reader
   does not assume graphify recall is being silently dropped for a different reason.

6. **`provider_failures` and the ticket's own Investigate step 8.** No corpus query is expected to
   naturally trigger a real `provider_failures` entry (graphify is installed and on PATH per
   `graphify-out/` existing; `context_search`'s index exists per the working knowledge-search MCP
   tool used throughout this investigation) — but if a live run does produce one (e.g. a transient
   graphify subprocess hiccup), it must be reported honestly as part of the real numbers for that
   entry, consistent with `INFRA-338`'s own framing of `provider_failures` as "a real, always-
   present response field." It should not be silently excluded from the recall/latency/token
   computation for that entry, nor should the entry be re-run until it happens to succeed
   (survivorship bias) — a `provider_failures`-bearing entry is real signal, not noise to filter.

7. **§20 Phase 1 checklist has no unannotated bullet this ticket satisfies** (Investigate step 9,
   confirmed by direct read of lines 1142-1191): all 6 Phase 1 bullets already carry **Done**
   annotations from the 4 prior child tickets. This ticket is a measurement/acceptance-check
   activity, not itself a Phase 1 deliverable-checklist item — stating this honestly (see Docs
   Requiring Update) rather than force-fitting this ticket's own comparison work onto an existing
   Done bullet that already describes different, already-shipped code.

## Anti-Drift Hazards
- **Never widen routing to force both providers to be called** for Q2/Q5 "to make §4.3 pass" — the
  single-primary-provider routing table is Done, ledgered, frozen behavior from
  `TCK-20260815-KGMCP-P1-QUERY-ROUTER` (INFRA-335); modifying it is out of this ticket's scope and
  would be exactly the "quietly resolve a miss" pattern the ticket's own Out of Scope section
  forbids.
- **Never modify `kgmcp_baseline_corpus.py`'s `CORPUS`** (cherry-picking, reordering, or adding
  entries) — Scope requires reusing the corpus verbatim, and the Phase 0 fixture/threshold
  formulas are keyed to exactly these 7 entries in this order.
- **Never regenerate or hand-edit the Phase 0 fixture**
  (`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`) — it is the frozen
  comparison baseline; this ticket only reads it and writes a **new**, separate fixture
  (`kgmcp_phase1_baseline_comparison_results.json`).
- **Never touch `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  `tools/knowledge_gateway_mcp.py`, or `tools/retrieval_events.py`** — all are DONE/frozen
  dependencies from prior child tickets; `test_search_mcp_py_provably_untouched`-style
  `git diff --stat`-based frozen-file guards already exist as precedent this ticket's own test
  suite should extend to cover its new banned-edit list.
- **Never launder a §4.3 miss into a pass by loosening what counts as "recalled"** (e.g. comparing
  only `provenance_providers` set membership instead of actual per-query source identity, or
  comparing counts instead of the actual superset-of-sources relationship) — the formula is
  explicit and per-query; a passing aggregate number while individual entries silently regress is
  exactly the failure mode §4.3's own "per query, not only in aggregate" language exists to catch.
- **Never let the new fixture/test suite silently pass when a comparison field goes missing** (the
  ticket's own AC #4) — mirror `test_kgmcp_measurement_baseline.py`'s pattern of asserting field
  presence and truthy `derivation` strings explicitly, never a bare `.get(..., default)` that
  degrades silently.
