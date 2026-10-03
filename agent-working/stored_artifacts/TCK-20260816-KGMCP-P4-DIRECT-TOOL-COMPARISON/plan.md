---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON
artifact_type: plan
tags: [ai, mcp, testing]
---

# Implementation Plan — TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON

## Summary

Build a new, one-time, measurement-only runner (`tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`)
that, for each of the 7 frozen corpus entries, makes a real gateway call and the real
equivalent direct-tool call(s) (Context Search, Graphify, and — for `Q3_requirement_completeness`
only — the Parity Ledger `entry()` adapter), and records latency, token, and quality/completeness
numbers for both sides into a new committed fixture. All 7 entries are run fresh (no reuse of
Phase 1-3 fixture data for the comparison itself — see Step 1's staleness reasoning), because two
routing-affecting behavior changes (`INFRA-351`, `INFRA-352`) postdate every existing fixture and
this ticket's own Investigation found no reliable way to know in advance which of the 6
"unaffected" entries were untouched by `INFRA-352`'s changed-path-context work. The quality axis
has two explicitly separate parts, one objective and one disclosed-subjective: (a) a
source/evidence-completeness proxy, computed by extracting normalized source identifiers from both
sides' raw output for the Context-Search half (reusing Phase 1's `_compute_threshold_4_3`
exactly, imported not reimplemented) and, newly, the Graphify half — closing Design Decision D3's
long-standing N/A by regex-extracting `src=<path>` occurrences from Graphify's own structured CLI
stdout (`NODE ... [src=<path> loc=L<n> community=<n>]` lines, confirmed by a real `graphify query`
run during Plan) on both the direct call's own stdout and the gateway's own internal `match_symbol_name()`
call's stdout; and (b) an explicitly labeled reviewer-judgment field, populated by a human/agent
reading both sides' retained raw content per entry, that is structurally distinct from (a) and
carries its own `basis: "reviewer_judgment"` disclosure so it can never be mistaken for a computed
score. Results are grouped by `routing_shape` (the corpus's own query-type taxonomy) in both the
fixture and the results doc. A new `INFRA-354` parity-ledger entry certifies the measurement tool
and honest reporting only, mirroring `INFRA-353`'s "methodology, not conclusion" framing, and the
proposal's Phase 4 fourth bullet is annotated Done only after the real doc exists and genuinely
satisfies it.

## Steps

### Step 1 — Decide and document: full fresh 7-entry run, no fixture reuse for comparison
**Files:** `staging_artifacts/TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON/plan.md` (this file,
already recording the decision below); the new runner module's own docstring (Step 2) must restate
it.

**Decision (confirmed, not merely proposed):** the new runner re-runs **all 7** corpus entries
fresh — both the gateway side and the direct-tool side — rather than reusing any Phase 0-3 fixture
data as one side of the comparison. Reasoning, grounded in Investigation's own findings:
- `INFRA-351` (Parity Adapter) concretely changed `ROUTING_TABLE["requirement_completeness_verification"]`
  from a dead-end to a live `("context_search", "parity_ledger")` row
  (`tools/knowledge_gateway_router.py:163-166`, confirmed by direct read during Plan) — this makes
  every existing fixture's `Q3_requirement_completeness` gateway-side number stale beyond dispute.
- **Correction (Architecture Review 1st pass, verified by direct trace):** `INFRA-352`'s
  `changed_paths` mechanism is NOT the source of any blast-radius risk for this ticket's own
  runner — this ticket's own Step 4 gateway calls pass only `query`, no `changed_paths` override,
  so `working_tree_overlap_forces_revalidation()` (`tools/knowledge_gateway_cache.py:206-211`)
  evaluates against an empty set and is provably always `False`; the mechanism is a deterministic
  no-op for every one of this ticket's own 7 calls. The real justification for the full fresh
  rerun is general repo-state drift since Phase 1-3 (many other tickets, cache rows, and doc
  changes have landed in the meantime, independent of `INFRA-352` specifically) — treating any of
  the other 6 entries' historical fixture numbers as "still current" would be an unverified
  assumption about the current repo state, not a measured fact, regardless of which specific
  ticket might be responsible for any drift.
- Mixing 6 stale + 1 fresh numbers in one comparison table (even if labeled) invites exactly the
  "assumed, not measured" failure mode Phase 2/3's own Gate Integrity discipline exists to prevent.
  A full fresh run costs 7 gateway calls + 7-11 direct-tool calls (Context Search + Graphify per
  entry, plus one extra Parity Ledger call for Q3) — cheap relative to the honesty cost of a mixed
  table.

**Do NOT touch:** any existing fixture (`kgmcp_measurement_baseline_corpus_results.json`,
`kgmcp_phase1_baseline_comparison_results.json`, `kgmcp_phase2_baseline_recomparison_results.json`,
`kgmcp_phase3_pilot_acceptance_measurement_results.json`) — these remain frozen, read-only
historical inputs. This ticket's own new fixture is a new file, never a merge into an existing one.

**Verify:** `test_q3_and_changed_path_context_entries_reflect_current_not_stale_routing` (confirms
Q3 is live, not stale) plus `test_all_7_corpus_entries_present_with_both_gateway_and_direct_results`
(confirms all 7, not a partial 1-entry patch, were freshly run).

---

### Step 2 — New runner module skeleton: imports, module docstring, sys.path setup
**Files:** `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py` (new)

**Change:** Create the new runner file mirroring `kgmcp_phase1_gateway_runner.py`'s and
`kgmcp_phase3_gateway_runner.py`'s own header/sys.path/import structure exactly
(`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py:68-97`,
`tools/agent-monitoring/kgmcp_phase3_gateway_runner.py:65-99`, both read during Investigation and
Plan). Concretely:
- `from kgmcp_baseline_corpus import CORPUS, CORPUS_VERSION, kgmcp_char_heuristic_v1_token_count`
  (imported, never redefined — mirrors `kgmcp_baseline_corpus.py:1-102`, read in full during Plan;
  confirms these 3 names exist and are the only pure exports).
- `from kgmcp_phase1_gateway_runner import _compute_threshold_4_3, _normalize_phase1_source_id, _path_only`
  (imported, never redefined — exact same reuse Phase 3 already established at
  `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py:147-163`, confirmed read during
  Plan).
- `from search_mcp import _run_search` (signature confirmed at `tools/search_mcp.py:82-83`:
  `_run_search(query: str, top_k: int = 8, section: str | None = None, mode: str = "hybrid") -> list[dict] | dict`).
- `importlib.util`-based loader for `tools/knowledge_gateway_mcp.py`, mirroring
  `kgmcp_phase1_gateway_runner.py:106-113`'s `_load_gateway_module()` exactly (module-key string
  changed to `"kgmcp_phase4_comparison_gateway"` to avoid `sys.modules` collision with Phase 1/3's
  own loader keys).
- `import tools.parity_index as` (or an `importlib.util` loader mirroring
  `tools/knowledge_gateway_router.py:280-286`'s `_load_parity_index_module()`) for the direct
  Parity Ledger call.
- Module docstring states: one-time, hand-run script, never wired into pytest's fast loop or
  `generate_retro.py`'s cadence (mirrors every predecessor's own convention); states the Step 1
  full-fresh-7-entry decision explicitly; states the "never touches" list (Step 2's own "Do NOT
  touch" below).

**Do NOT touch:** `kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`,
`kgmcp_phase1_gateway_runner.py`, `kgmcp_phase2_gateway_runner.py`,
`kgmcp_phase3_gateway_runner.py`, `tools/knowledge_gateway_mcp.py`,
`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
`tools/knowledge_gateway_cache.py`, `tools/parity_index.py`, `tools/search_mcp.py` — all read-only
call targets, never edited.

**Verify:** `test_new_runner_imports_not_reimplements_phase0_pure_helpers` (AST-checks the import,
not redefinition, of `CORPUS`/`CORPUS_VERSION`/`kgmcp_char_heuristic_v1_token_count`).

---

### Step 3 — Direct-tool call functions: Context Search, Graphify, Parity Ledger
**Files:** `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`

**Change:** Implement three direct-call helpers, each an exact, real, runnable Python call (per
the ticket's Design Decision 1 requirement) — no hand-waving:

1. `_run_direct_context_search(query_text: str) -> dict`: calls `_run_search(query_text, top_k=8)`
   directly (never through `wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`), timed with
   `time.perf_counter()`. Mirrors `kgmcp_baseline_runner.py::_run_context_search`
   (`tools/agent-monitoring/kgmcp_baseline_runner.py:68-89`, read during Investigation) exactly,
   **except** it also retains `raw_results` in the persisted output (Step 6's new-instrumentation
   requirement — Phase 0's own `run_corpus()` dropped this field before serialization, confirmed by
   reading `kgmcp_baseline_runner.py:144-150` during Investigation; this ticket's own fixture must
   not repeat that drop).

2. `_run_direct_graphify(query_text: str) -> dict`: `subprocess.run(["graphify", "query", query_text], cwd=repo_root, capture_output=True, text=True, timeout=120)`,
   timed the same way. Mirrors `kgmcp_baseline_runner.py::_run_graphify`
   (`tools/agent-monitoring/kgmcp_baseline_runner.py:92-114`) exactly, again retaining full
   `raw_stdout` in the persisted output (not just `raw_stdout_bytes`).

3. `_run_direct_parity_ledger(query_text: str) -> dict`, called **only for `Q3_requirement_completeness`**:
   `tools.parity_index.entry(query_text)` — passing `query_text` itself as `entry_id`, **not** a
   resolved/looked-up parity ID. This exactly mirrors the gateway's own real usage,
   `tools/knowledge_gateway_router.py::_run_parity_provider()`
   (`tools/knowledge_gateway_router.py:290-312`, read in full during Plan): its own docstring states
   "`query_text` is used directly as the entry_id ... for a natural-language query shape-classified
   into the same `requirement_completeness_verification` row, `entry()` legitimately returns
   `found: False` for the whole sentence treated as an id — real provider behavior, not an error."
   The direct call must use this same convention (not a different, "fairer" resolved-id lookup) —
   using a different calling convention on the direct side than the gateway actually uses would
   make the comparison dishonest (the two sides would no longer be exercising the same real
   question). `tools/parity_index.py::entry(entry_id: str, db_path=None) -> dict` signature
   confirmed at `tools/parity_index.py:550`. If `found` is `False`, additionally call
   `tools.parity_index.check_staleness()` — mirroring `_run_parity_provider`'s own `found: False`
   branch (`tools/knowledge_gateway_router.py:310-311`) so the direct side's disclosure shape
   matches the gateway side's.

**Do NOT touch:** any of the 3 called functions' own source files. Do not add a `top_k` value
other than 8 for Context Search (matches every predecessor's own convention — introducing a
different `top_k` would make the two sides' result-set sizes incomparable).

**Verify:** `test_q3_direct_result_includes_a_real_parity_index_entry_call`;
`test_raw_content_retained_on_both_sides_for_quality_comparison`.

---

### Step 4 — Gateway-side call function
**Files:** `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`

**Change:** `_run_gateway(query_text: str) -> dict`: loads `tools/knowledge_gateway_mcp.py`
in-process via the Step 2 loader and calls the real
`_run_knowledge_context(query=query_text)` (signature confirmed at
`tools/knowledge_gateway_mcp.py:149-156`: `query: str, mode=None, budget_tokens=None,
changed_paths=None, include_history=None, evidence_detail=None` — this ticket passes only
`query`, no other overrides, matching Phase 1's own call shape at
`kgmcp_phase1_gateway_runner.py:230`), timed externally with `time.perf_counter()` wrapped directly
around the call (Design Decision D1 precedent: `retrieval_events.py`'s wrapper functions have zero
call sites on this path, confirmed by Phase 1's own investigation and re-confirmed unchanged here
since no ticket in this epic has added a wrapper call site). Also calls
`knowledge_gateway_router.route(query_text)` directly (read-only, side-effect-free) to record the
real `providers_selected` for that entry — never assumed from `ROUTING_TABLE` alone, mirroring
`kgmcp_phase1_gateway_runner.py:233-234`. Measures `gateway_tokens` via
`knowledge_gateway_packet_assembly.kgmcp_char_heuristic_v1(json.dumps(response))`
(confirmed real function at `tools/knowledge_gateway_packet_assembly.py:85`), mirroring Phase 1
exactly. Retains the full `response` dict (not just derived counts) in the persisted output — the
same new-instrumentation requirement as Step 3.

**Do NOT touch:** `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`. Never call `emit_retrieval_event`,
`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, or `wrap_context_packet_assembly`.

**Verify:** `test_never_calls_emit_retrieval_event_or_wrap_functions`;
`test_q3_and_changed_path_context_entries_reflect_current_not_stale_routing` (asserts
`"parity_ledger" in providers_selected` for Q3's real, fresh `route()` result).

---

### Step 5 — Quality axis, part (a): objective source-completeness proxy, both halves
**Files:** `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`

**Change:** Two sub-computations, kept structurally separate and each individually labeled with
its own `derivation` string (matching every predecessor's own disclosure convention):

1. **Context-Search half (reused, not reimplemented):** call the imported
   `_compute_threshold_4_3(direct_sources, gateway_sources_raw)` from
   `kgmcp_phase1_gateway_runner.py` (Step 2's import), where `direct_sources` is **this ticket's
   own freshly-run** `_run_direct_context_search()`'s `sources_recalled` list (per Step 1's
   full-fresh-run decision — never the historical Phase 0 fixture's list, since Step 1 already
   established that reusing any historical side would violate the no-stale-mixing decision), and
   `gateway_sources_raw` is `response["context"][*]["source_id"]` from Step 4's fresh gateway call,
   normalized the same way Phase 1 already does (`_normalize_phase1_source_id`, `_path_only` —
   imported, not reimplemented). **Provenance-honesty fix (Architecture Review 1st pass):**
   `_compute_threshold_4_3`'s own returned dict hardcodes a `"derivation"` string reading
   `"baseline_sources = Phase 0 fixture's context_search.sources_recalled for this entry
   (read-only)"` — this is a real, false provenance claim once fed this ticket's own freshly-run
   `direct_sources` instead of a Phase 0 fixture. The runner must NOT persist this string verbatim.
   After calling `_compute_threshold_4_3()`, overwrite the returned dict's `"derivation"` key with
   a locally-authored string before writing to the fixture, e.g.: `"baseline_sources =
   THIS TICKET's own freshly-run _run_direct_context_search() call for this entry (not a Phase 0/1
   fixture — see TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON Step 1's full-fresh-run decision),
   compared via the unmodified, reused _compute_threshold_4_3() matching logic."` The comparison
   *logic* inside `_compute_threshold_4_3()` stays completely untouched (frozen, Do-Not-Touch below)
   — only the misleading provenance string in its return value gets corrected before persistence.

2. **Graphify half (new — closes Design Decision D3's 3-phase-old N/A):** define
   `_extract_graphify_source_paths(raw_stdout: str) -> list[str]` using
   `re.findall(r"src=([^\s\]]+)", raw_stdout)`. This regex and its capture behavior were verified
   during Plan by running `graphify query "Where is compute_search_investigation_trend defined, and
   what functions call it?"` directly: its real stdout consists of lines shaped
   `NODE <name>() [src=<path> loc=L<n> community=<n>]`, and `src=([^\s\]]+)` captures the path
   component (e.g. `tools/agent-monitoring/generate_retro.py`) correctly for every sampled line.
   Apply this extractor to **both** (i) `_run_direct_graphify()`'s own freshly-captured
   `raw_stdout` for the entry, and (ii) the gateway's own internal Graphify call's `raw_stdout` —
   captured by calling `knowledge_gateway_router.match_symbol_name(query_text)` directly, a second,
   independent, real CLI-shelled call for the identical `query_text`
   (`tools/knowledge_gateway_router.py:99-119`, confirmed read during Plan: pure, side-effect-free,
   deterministic given a stable repo state, no different from how Step 4's gateway call and Step
   3's direct call are already two independently-run calls compared by content, not one spied
   call — matching the existing Phase 0/1 precedent of independent, not instrumented-inline,
   measurement). Compare the two extracted path sets with simple set difference (no anchor
   normalization needed — Graphify's `src=` paths carry no `#anchor` component). Record
   `graphify_half_status: "measured"` (replacing every predecessor's literal `"N/A"`) plus
   `graphify_missing_sources` (paths present in the gateway-side call's own graphify invocation but
   absent from the direct call's — or, since both calls are for the identical query against the
   same repo state, the expected/typical real result is an **empty** `graphify_missing_sources`
   list; a non-empty result would itself be a genuine, real, disclosed finding, not treated as a
   bug in the extractor). This only runs for entries whose `providers_selected` (Step 4) actually
   includes `"graphify"` — for entries where Graphify was never consulted by the gateway (per
   real, per-entry `providers_selected`, not the static `ROUTING_TABLE` optional/primary
   distinction alone), record `graphify_half_status: "not_routed_this_entry"` instead of a
   fabricated comparison.

Both sub-results are written under a single `source_completeness` object per entry (with
`context_search_half` and `graphify_half` sub-keys), never merged into one number — the two are
methodologically different (one reuses Phase 1's proven anchor-aware path matching, the other is
this ticket's own new plain-path regex extraction) and must stay individually inspectable.

**Do NOT touch:** `_compute_threshold_4_3`, `_normalize_phase1_source_id`, `_path_only` — call
only, never modify (they live in the frozen `kgmcp_phase1_gateway_runner.py`).

**Verify:** `test_graphify_half_of_recall_is_no_longer_na`.

---

### Step 6 — Quality axis, part (b): disclosed reviewer-judgment field
**Files:** `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`

**Change:** For each of the 7 entries, add a `reviewer_judgment` object with exactly these keys:
`basis` (a fixed literal string, always exactly `"reviewer_judgment_not_a_computed_metric"` —
this literal is what the anti-drift test asserts on, per test_plan.md's
`test_quality_signal_is_labeled_judgment_not_scored_metric`), `verdict` (one of
`"gateway_equal_or_better"`, `"direct_equal_or_better"`, `"mixed"` — a plain-English judgment call,
not a numeric score), and `rationale` (free text, written by whoever runs Implementation, reading
both sides' now-retained raw content per entry (Step 3/4's retained `raw_results`/`raw_stdout`/
`response`) and stating plainly whether the gateway's budget/dedup/routing dropped something a
direct call would have kept, or vice versa — Scope's own judgment-phrased language, not a new
rubric).

**Concrete, falsifiable procedure (Architecture Review 1st pass — required, not optional prose):**
`rationale` must not be genericized boilerplate. Specifically:
- For any entry where Step 5's `source_completeness` recorded a non-empty
  `context_search_missing_sources`/`context_search_extra_sources`/`graphify_missing_sources` on
  either half, `rationale` MUST name at least one specific, real source_id/path from that recorded
  set (copy it verbatim from the `source_completeness` object already computed for that entry) and
  state in one clause whether that specific item mattered to the answer's usefulness — not a vague
  "some sources differed."
- For any entry where `source_completeness` shows no missing/extra sources on either half,
  `rationale` MUST say so explicitly (e.g. "no source-set difference recorded for either half —
  judgment is based on X instead") rather than offering generic praise unconnected to the actual
  computed data.
- No two entries' `rationale` strings may be byte-identical — each entry's own retained content is
  different, so a genuinely-read judgment cannot legitimately produce copy-pasted text across
  entries.
This field is populated by hand during Implementation (the runner script itself cannot
compute it — it requires reading content), one entry at a time, and is written into the fixture's
JSON directly (not auto-generated) before the fixture is committed. The `source_completeness`
object from Step 5 and the `reviewer_judgment` object from this step are never merged into a single
top-level `quality` field — they stay two separately-keyed sub-objects under a shared parent
(e.g. `entry["quality"] = {"source_completeness": {...}, "reviewer_judgment": {...}}`), so no
downstream reader can mistake the subjective half for the objective half.

**Do NOT touch:** do not compute `reviewer_judgment.verdict` programmatically from
`source_completeness`'s numbers — that would silently convert a disclosed-subjective field into a
dressed-up derivative of the objective proxy, which is exactly what the Investigation's Risk
section and Gate Integrity forbid. The two must be independently arrived at.

**Verify:** `test_quality_signal_is_labeled_judgment_not_scored_metric`,
`test_reviewer_judgment_rationales_are_not_byte_identical_across_entries` (asserts all 7
`rationale` strings are pairwise distinct), `test_reviewer_judgment_cites_a_real_recorded_source_
when_source_completeness_shows_a_gap` (for every entry where `source_completeness` records at
least one missing/extra source on either half, asserts that entry's `rationale` string contains at
least one of those recorded source_id/path strings verbatim).

---

### Step 7 — Assemble `run_corpus()`, write the fixture
**Files:** `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`;
`tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json` (new, committed)

**Change:** `run_corpus()` iterates `CORPUS` (imported, Step 2), calling Step 3's direct-tool
functions, Step 4's gateway function, Step 5's source-completeness computation, per entry. Each
entry dict carries: `id`, `query_text`, `routing_shape`, `use_case`, `gateway` (full response +
timing + `providers_selected` + `gateway_tokens`), `direct` (`context_search` + `graphify`, plus
`parity_ledger` only for `Q3_requirement_completeness`), `quality.source_completeness`
(Step 5 — machine-computed, left `null`/pending for `reviewer_judgment` at script-write time),
`latency_comparison` (`gateway_wall_time_ms` vs `direct_combined_wall_time_ms`, `gateway_faster: bool`),
`token_comparison` (`gateway_tokens` vs `direct_combined_tokens_estimate` via
`kgmcp_char_heuristic_v1_token_count`, `gateway_lighter: bool`). Top-level fixture carries
`corpus_version`, `recorded_at_utc`, `entries`, and `by_routing_shape` — a dict keyed by each of
the 7 `ROUTING_SHAPES` values, each holding that shape's one entry's id and a one-line
latency/token/quality-verdict summary (Design Decision 4's per-query-type grouping requirement).
After the script runs and writes the fixture, Implementation manually fills in each entry's
`quality.reviewer_judgment` (Step 6) by reading the retained raw content, then re-serializes the
same file (`json.dumps(..., indent=2, sort_keys=True)`, matching every predecessor's own
serialization convention) before committing.

**Do NOT touch:** any existing fixture file (Step 1's guard, restated). `run_corpus()`'s own output
path must be the new file above, never an existing one.

**Verify:** `test_all_7_corpus_entries_present_with_both_gateway_and_direct_results`;
`test_results_grouped_by_query_type_not_only_aggregate`;
`test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture`;
`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`.

---

### Step 8 — Honest-reporting guard: no exclusion or redefinition of unfavorable entries
**Files:** `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py` (no special code
needed — this step is a written-into-the-results-doc discipline, verified structurally); Step 9's
results doc is where this becomes visible.

**Change:** When writing the results doc (Step 9), every one of the 7 entries must appear with its
real `latency_comparison`/`token_comparison`/`quality` verdict intact, regardless of whether it
favors the gateway or the direct call. No entry is filtered out of the doc's per-query-type table;
no threshold or verdict definition is adjusted after seeing an unfavorable result. This mirrors
Phase 1's own Design Decision D4 precedent (`kgmcp_phase1_gateway_runner.py:47-53`: "The resulting
`pass: False` for those two entries is real, expected, honest output, not a bug in this script").

**Do NOT touch:** do not add a filtering/exclusion parameter to `run_corpus()` or the doc-writing
step that could later be used to drop an entry from the report.

**Verify:** `test_no_query_type_disadvantage_is_silently_excluded_or_redefined`.

---

### Step 9 — New results doc
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` (new)

**Change:** New doc, mirroring `phase3_pilot_acceptance_measurement.md`'s own structure/audience
(sibling doc, read during Investigation's Prior Work). Required content, each independently
testable (Step 10):
- States the corpus has no gold/expected-answer field and that quality judgments are
  reviewer-judgment-based for the `reviewer_judgment` sub-field, objectively computed (with method
  disclosed) for the `source_completeness` sub-field — the two are never conflated (mirrors
  Investigation's own Risk section language almost verbatim, since that section already states the
  correct disclosure).
- Cites the fixture path: `tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json`.
- Per-query-type (per `routing_shape`) results table/section — not only an aggregate — using the
  fixture's own `by_routing_shape` grouping from Step 7.
- States each entry's real verdict in plain, disclosed terms (which side won on latency, tokens,
  and quality, or "mixed"/"no genuine advantage" where that is the real result) — no entry omitted,
  matching Step 8's guard.
- States the Q3/`INFRA-351`/`INFRA-352` staleness reasoning from Step 1, so a future reader
  understands why this doc's numbers are a full fresh run rather than a partial patch onto Phase
  1-3 numbers.
- Cites the Graphify-half closure of Design Decision D3 explicitly (states plainly that this is the
  first phase to measure it, and the extraction method used).

**Do NOT touch:** `phase1_baseline_comparison.md`, `phase2_baseline_recomparison.md`,
`phase3_pilot_acceptance_measurement.md` — read for structure only, never edited.

**Verify:** `test_results_doc_states_no_gold_answer_limitation`;
`test_results_doc_cites_real_fixture_and_states_pass_fail_per_query_type`.

---

### Step 10 — proposal.md Phase 4 fourth-bullet annotation
**Files:** `docs/plans/knowledge-gateway-mcp-proposal.md`

**Change:** After Step 9's doc is real and complete, add a `**Done** (`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`)`
inline annotation to Phase 4's fourth bullet ("Compare gateway packets against existing direct-tool
behavior"), mirroring the first bullet's own existing annotation style at
`docs/plans/knowledge-gateway-mcp-proposal.md:1368` (read during Investigation/Plan). The
annotation text must state the real, per-query-type result honestly (which shapes favored gateway,
direct, or mixed) — never a bare "Done" with no result summary, and never an overclaim beyond what
Step 9's doc actually states. **This bullet is marked Done only if Step 9's doc genuinely reports a
real measured result for all 7 entries** — if Implementation cannot complete a genuine live run
(e.g. an unrecoverable environment failure), this step must not be marked Done and the ticket must
disclose the gap rather than force an annotation, per the epic's own "no result may be assumed,
only measured" precedent (ticket Request Summary) and CLAUDE.md's gate-integrity hard rule.

**Do NOT touch:** any other Phase 4 bullet, any other phase's annotation.

**Verify:** doc-review at Verify phase confirms the annotation text matches Step 9's doc's actual
stated result (no automated test specified for this step — it is a documentation cross-check, same
as the first bullet's own precedent, which also has no dedicated automated test).

---

### Step 11 — New `INFRA-354` parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after `INFRA-353` (`docs/parity_ledger/infrastructure.yaml:10201`,
confirmed the current highest ID in this file during Investigation), following the exact schema
shape required by `docs/parity_ledger/schema.json` (read during Plan:
required `["id", "text", "status", "priority"]`; `status: "verified"` requires both `v2_evidence`
and `test_path` non-null per the `allOf` conditional at `schema.json`'s items block). Concretely:
`id: INFRA-354`, `status: verified`, `priority: P2` (mirrors `INFRA-353`'s own priority, per
Investigation's Parity Ledger Overlap finding — no P0 entries are touched since this is a
measurement/reporting ticket with no runtime behavior change), `v2_evidence` citing the new runner
file and the new fixture, `test_path` citing
`tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` (the primary new-test file). The `text`
field must state explicitly, mirroring `INFRA-353`'s own framing verbatim in structure
(`docs/parity_ledger/infrastructure.yaml:10201-10220`, read in full during Plan): this entry
certifies the measurement tool and honest reporting are correct/tested — it does **not** certify
that the gateway is superior or inferior to direct-tool use for any query type; that determination
is the real, disclosed measurement result reported in Step 9's doc, which is a human-reviewable
finding, not a certified "pass."

**Do NOT touch:** any other entry in `infrastructure.yaml` (`INFRA-350`, `INFRA-351`, `INFRA-352`,
`INFRA-353`, or earlier) — read-only precedent only.

**Verify:** `test_infra354_entry_is_schema_valid_and_certifies_methodology_not_conclusion` (new
test, location: `tests/docs/test_infrastructure_ledger_infra354.py`, since no existing general
schema-validation-against-live-entries test was found in `tests/` during Plan — the only existing
`infrastructure.yaml`-adjacent tests are `test_parity_ledger_writer.py` (tests the writer tool, not
live entries) and `test_parity_ledger_schema.py` (tests `schema.json`'s own raw structure, not
entries) — confirmed via `grep -rl "infrastructure.yaml" tests/`, neither validates committed
entries against the schema directly).

---

### Step 12 — New tests: write `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` and `tests/docs/test_phase4_direct_tool_comparison_doc.py`
**Files:** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` (new);
`tests/docs/test_phase4_direct_tool_comparison_doc.py` (new)

**Change:** Implement every test named in `test_plan.md`'s "New Tests Required" section (13 tests
total, listed there by name with target file). Structural/architecture-guard tests
(`test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture`,
`test_new_runner_imports_not_reimplements_phase0_pure_helpers`,
`test_never_calls_emit_retrieval_event_or_wrap_functions`,
`test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`) mirror the identically
named/shaped tests already proven out in `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`
(read during Investigation and Plan) — reuse their SHA-256 content-hash-snapshot and AST-inspection
patterns exactly, retargeted at this ticket's own new runner filename and frozen-file list.

**Note for Implementation (not a scope change):** `test_plan.md` specifies
`tests/docs/test_phase4_direct_tool_comparison_doc.py` as a separate file from
`tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`. The actual Phase 3 precedent (confirmed
during Plan via `grep -rl test_results_doc_cites_real_fixture_and_states_pass_fail_per_criterion tests/`)
placed its equivalent doc-citation test inside the single
`tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` file, not a separate `tests/docs/`
file. Follow `test_plan.md`'s stated file split as written (it is the authoritative test plan for
this ticket) — this note is only to flag the minor structural divergence from the nearest
precedent, not to authorize silently changing the test plan.

**Do NOT touch:** `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` or any other
existing test file in `tests/tools/`/`tests/docs/` — new tests go in the two new files only.

**Verify:** `pytest tests/tools/test_kgmcp_phase4_direct_tool_comparison.py tests/docs/test_phase4_direct_tool_comparison_doc.py -v`
plus the full regression-surface commands listed in `test_plan.md`'s "Scoped Pytest Commands"
section.

## Scope Guards

- No diff to `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
  `tools/knowledge_gateway_redaction.py`, or `tools/parity_index.py` — Out of Scope explicitly
  forbids any gateway/router/cache/Parity-adapter code change; this ticket calls these modules,
  never edits them.
- No diff to `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_baseline_runner.py`,
  `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
  `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`,
  `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`, or any of their 4 existing committed
  fixtures — frozen historical inputs, imported/read from only.
- No fixing of any disadvantage this ticket's own measurement finds (e.g. do not tune
  `budget_tokens`, routing weights, or dedup logic to make the gateway look better after seeing an
  unfavorable result) — that is explicitly a separate, later, human-scoped follow-up ticket.
- No declaration that Phase 4 is complete or that the gateway is broadly superior/inferior to
  direct tool use — Step 10's annotation states only this ticket's own real per-query-type result,
  not a broader characterization.
- The new `INFRA-354` entry certifies the measurement tool and reporting only, never the
  comparison's conclusion (gateway wins/loses) — Step 11's guard, directly enforced by
  `test_infra354_entry_is_schema_valid_and_certifies_methodology_not_conclusion`.
- No entry is excluded from the results doc or fixture to force a favorable aggregate — Step 8's
  guard, directly enforced by `test_no_query_type_disadvantage_is_silently_excluded_or_redefined`.
- The `reviewer_judgment` field (Step 6) must never be computed programmatically from
  `source_completeness` (Step 5) — the two stay independently arrived at and separately labeled.
- Do not implement any workflow integration change (`.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`,
  `.claude/agents/*.md`) — this ticket is measurement/reporting only, mirroring `INFRA-353`'s own
  Out of Scope.

## Dependency Map

- Step 1 (staleness decision) has no code dependency but must be settled before Step 7 (fixture
  assembly) — it determines whether any historical fixture data is read as one side of a
  comparison (answer: no).
- Steps 2, 3, 4 are independent of each other (module skeleton, direct-call functions, gateway-call
  function) but all must exist before Step 5 (which consumes Step 3's and Step 4's outputs).
- Step 5 depends on Steps 3 and 4 (needs both sides' raw content).
- Step 6 depends on Step 3/4's raw-content retention (needs something to read) but is otherwise
  independent of Step 5's computation.
- Step 7 depends on Steps 2-6 (assembles and writes the fixture from all prior steps' outputs).
- Step 8 is a discipline applied during Step 9's writing, not a separate code artifact — depends on
  Step 7's fixture existing with all 7 entries' real numbers.
- Step 9 depends on Step 7 (fixture must exist to cite/summarize) and observes Step 8's guard.
- Step 10 depends on Step 9 (doc must be real and complete before the proposal bullet can honestly
  say Done).
- Step 11 (`INFRA-354`) depends on Step 12's test file existing (schema validity test path must be
  real) and Step 9's doc existing (its `text` field should be consistent with the real doc, though
  it does not cite the doc's conclusion).
- Step 12 (tests) can be written in parallel with Steps 2-9 (test-first is acceptable per
  `test-driven-development` convention) but must all pass before the ticket is considered complete;
  the doc-structure tests (Step 12's second file) necessarily run after Step 9's doc exists.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Each of the 7 corpus entries is run through both the real gateway and the real equivalent direct-tool call(s), with real latency/token/quality numbers captured for both. | Steps 1, 2, 3, 4, 5, 6, 7 | `test_all_7_corpus_entries_present_with_both_gateway_and_direct_results`, `test_q3_direct_result_includes_a_real_parity_index_entry_call`, `test_raw_content_retained_on_both_sides_for_quality_comparison`, `test_q3_and_changed_path_context_entries_reflect_current_not_stale_routing` |
| Results are reported per-query-type, not only as a single aggregate. | Step 7 (`by_routing_shape`), Step 9 | `test_results_grouped_by_query_type_not_only_aggregate`, `test_results_doc_cites_real_fixture_and_states_pass_fail_per_query_type` |
| Any query type where the gateway shows no genuine advantage (or a real disadvantage) is reported plainly as such — no redefinition, no exclusion to force a favorable result. | Step 8, Step 9 | `test_no_query_type_disadvantage_is_silently_excluded_or_redefined` |
| A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added, certifying this ticket's measurement tool and honest reporting as correct/tested — not the measured gateway-vs-direct-tool comparison result itself, mirroring `INFRA-344`'s precedent. | Step 11 | `test_infra354_entry_is_schema_valid_and_certifies_methodology_not_conclusion` |

## Anti-Drift Notes

- **Do not silently mix stale Phase 1-3 fixture numbers with fresh Phase 4 numbers.** Step 1's
  decision (full fresh 7-entry run) resolves this — no step reads Phase 0-3 fixture data as a
  comparison side. If any step is tempted to shortcut by reusing a historical number for an
  "unaffected" entry, stop: Investigation could not establish which of the 6 non-Q3 entries were
  genuinely unaffected by `INFRA-352`.
- **Do not invent an objective "quality score" the corpus cannot support.** Step 5 (objective
  source-completeness proxy) and Step 6 (disclosed reviewer judgment) must remain two separately
  labeled sub-objects, never merged into one number, never with Step 6 derived from Step 5's
  output.
- **The Graphify recall-extension regex (`src=([^\s\]]+)`) was verified against one real sample
  during Plan, not exhaustively against all 7 entries' actual Graphify output.** Implementation
  must re-verify the regex correctly extracts paths from each entry's own real Graphify stdout
  (some entries may hit zero-match Graphify results, e.g. if a query returns no NODE lines) and
  handle a zero-match case as `graphify_missing_sources: []` with a `derivation` note, not a crash.
- **Do not let the new `INFRA-354` entry's `text` field drift into stating a conclusion** (e.g.
  "the gateway is faster for symbol lookups") — that belongs only in Step 9's results doc, per
  `INFRA-353`'s own established precedent and this ticket's own Acceptance Criterion 4.
- **The Parity Ledger direct call for Q3 must use `entry(query_text)` with the raw query text as
  `entry_id`, not a resolved/looked-up ID** — using a "fairer" resolved ID on the direct side while
  the gateway uses the raw query text would make the two sides test different things, invalidating
  the comparison's honesty.
- **`match_symbol_name()` and Graphify's CLI output are read live, not mocked, for both the direct
  and (indirectly, via the real gateway call) gateway sides** — if the repo's Graphify index is
  stale or the `graphify` CLI is unavailable in the Implementation environment, this is a real
  environment blocker to disclose (per Step 10's guard), not a condition to work around with a
  mock or a skipped entry.
- **No Unresolved Questions remain from Investigation that block this plan.** Investigation's two
  "Open, not blocking" questions (whether Q2/Q5 show a real graphify recall gap; whether all 7
  entries needed a fresh run) are resolved here: the second by Step 1's explicit decision, the
  first is left to the real measurement in Step 5 to answer, not assumed by this plan.

## Deviations (recorded during Implementation)

- **Frozen-file SHA-256 hash list needed 3 more entries than Phase 3's own precedent list.**
  Phase 3's `test_kgmcp_phase3_pilot_acceptance_measurement.py::_FROZEN_FILE_HASHES` snapshots 7
  files. This ticket's own runner directly calls `knowledge_gateway_router.py` (for `route()` and
  `match_symbol_name()`), `knowledge_gateway_packet_assembly.py` (for `kgmcp_char_heuristic_v1`),
  `parity_index.py` (for the direct `entry()`/`check_staleness()` calls), and `search_mcp.py` (for
  `_run_search`) as first-class, directly-imported/directly-loaded dependencies this ticket's own
  quality-axis computation depends on byte-for-byte — not merely indirectly reached through the
  gateway as Phase 3's runner does. `test_kgmcp_phase4_direct_tool_comparison.py`'s own
  `_FROZEN_FILE_HASHES` therefore snapshots these 4 additional files (14 total files + 1 fixture =
  15 entries) so a future accidental edit to any of them is caught with the same fidelity Phase 3
  established for its own narrower dependency set. This is a scope clarification, not a deviation
  from Step 2's own "Do NOT touch" list, which already named all of these files as read-only call
  targets.
- **The runner module's own docstring escape sequences required raw-string (`r"""`) literals.**
  Both the module-level docstring and `_extract_graphify_source_paths()`'s own docstring quote the
  literal regex `re.findall(r"src=([^\s\]]+)", raw_stdout)`; a plain (non-raw) triple-quoted
  docstring containing `\s` triggers a `SyntaxWarning: invalid escape sequence`. Both docstrings
  were written as raw strings (`r"""..."""`) to eliminate the warning — no behavior change, no
  scope change.
- **Step 6's reviewer_judgment procedure surfaced a genuine, previously-unknown measurement-
  methodology limitation, disclosed rather than silently worked around:** for 2 of the 7 entries
  (`Q4_historical_rationale`, `Q6_ticket_status`), the objective `source_completeness.
  context_search_half`'s recorded "missing" sources turned out, on direct inspection of the
  gateway's own `response["context"]`, to already be present under a `file:stored_artifacts/
  <ticket>/investigation.md`-shaped normalized id — the imported, frozen `_normalize_phase1_
  source_id()`/`_path_only()` never reconciles this shape against the direct call's own bare
  ticket-id `doc_id` for `stored_artifacts/` files. Per Step 5's own Do-Not-Touch guard, the
  objective proxy's own computed `missing_sources` list was left exactly as computed (not
  "corrected") — this finding is disclosed only in the hand-authored `reviewer_judgment.rationale`
  for those 2 entries and in the results doc's own dedicated section, exactly as the plan's Step 6
  falsifiable procedure requires ("state whether it mattered").
