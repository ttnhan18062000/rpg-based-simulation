---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-HYBRID-RETRIEVAL-FUSION
artifact_type: investigation
tags: [ai, debugging, testing]
---

# Investigation — TCK-20260729-HYBRID-RETRIEVAL-FUSION

## Current Behavior

### `tools/knowledge_search.py::cmd_query()` (lines 944-1069)

- Lines 972-995: `query_tokens = _tokenize(query_text)`; if `mode in ("hybrid",
  "keyword")`, `bm25_obj, _bm25_doc_ids = _load_bm25(bm25_path)` (line 980), then
  (line 992-995) `bm25_raw = bm25_obj.get_scores(query_tokens)` — `rank_bm25`'s
  `get_scores()` returns one score **per document in the entire BM25-indexed
  corpus** (parallel array indexed by the corpus row order captured at build
  time, `_build_bm25_index()` lines 468-483). So the raw BM25 score array itself
  *is* computed over the full corpus, not merely dense-surviving candidates —
  this one clause, read alone, does not match the ticket's literal wording.
- Lines 998-1038 (the `hybrid`/`vector` branch, which `hybrid` mode always takes
  once BM25 loads successfully): line 1010 sets `candidate_k = top_k * 3`; lines
  1011-1021 run the ANN query `SELECT ... FROM knowledge_vec v ... WHERE
  v.embedding MATCH ? AND k = ?` with `candidate_k` — this is the **only** source
  of the `rows` that ever become `results`. Lines 1024-1034 iterate `rows` (dense
  ANN hits only) and, for each, look up `bm25_raw[rowid]` (line 1028-1029) to
  attach a keyword score, then combine via `_hybrid_score()` (line 1033).
- **Net effect (CONFIRMED, with a precision correction):** BM25 scores are
  computed for the whole corpus, but the **candidate set eligible to appear in
  `results` at all** is restricted to the dense-channel ANN's top `candidate_k =
  top_k * 3` rows (line 1010, 1020 `k = ?`). A document with a high BM25 score
  but outside that ANN cut is structurally unreachable — its BM25 score, however
  high, is computed but never consulted because the document never enters
  `rows`. This is the substance of the ticket's claim ("BM25 is computed only
  over candidates that already survived the dense-channel ANN cut") even though
  the literal mechanism is "BM25 raw scores are computed corpus-wide, but only
  looked up for/applied to ANN-surviving rows" rather than "BM25 itself never
  runs over the full corpus." The observable symptom — a lexical-only exact
  match outside the dense top-N is silently dropped from `hybrid` mode results —
  is real and verified against the code, not just the ticket's assertion.
- The separate `mode == "keyword"` branch (lines 1040-1060) is unaffected: it
  full-scans `knowledge_docs` (line 1044) and ranks purely by BM25 — this is the
  code path the ticket's Scope requires to be preserved unmodified.

### `tools/search_mcp.py::_run_search()` (lines 73-146)

- Line 105: `rows = con.execute(sql, (q_bytes, min(top_k * 4, 50))).fetchall()`
  — the ANN query is the **sole** source of `rows`; `min(top_k*4, 50)` is this
  file's dense-channel candidate cut (its own constant, different from
  `knowledge_search.py`'s `top_k*3`, both magic numbers with no shared
  definition — an anti-drift note for planning, see below).
- Lines 118-131: for `row in rows[:top_k]` (i.e., only ANN-surviving rows),
  line 123-129 calls `_STATE.bm25.get_scores(query_tokens)` **inside the loop**
  (recomputed once per row — wasteful but not part of this ticket's bug scope)
  and looks up `scores[idx]` by `doc_id`. Same structural bug as
  `knowledge_search.py`: BM25 scores exist for the full corpus but only rows
  that survived the ANN cut are ever scored/returned.
- **CONFIRMED**, same mechanism and same nuance as `knowledge_search.py` above.
  `search_mcp.py`'s `_run_search()` is what every agent's `search_docs` MCP
  call invokes in this session and every other — so the bug is live today for
  the exact tool this project's own CLAUDE.md mandates agents call first for
  every investigation, not merely a latent/future-facing bug.

### Third call site not in ticket scope: `tools/search_server.py`

`tools/search_server.py` (`search()` function, confirmed via `graphify query`
and direct read of `import`/call lines) reuses `_ks._compute_boosts()` and
`_ks._hybrid_score()` and runs its own independent ANN-then-BM25-lookup
sequence with the same dense-candidate-gating shape. It is **not** listed in
this ticket's Related Code Areas or Scope, and the ticket's "fix both call
sites" instruction names only `knowledge_search.py` and `search_mcp.py`. This
third site carries the identical bug pattern and is out of this ticket's scope
— see Anti-Drift Hazards.

### `_reciprocal_rank()` naming-collision resolution (`tools/eval_search.py:42-46`)

```python
def _reciprocal_rank(results: list[str], expected: set[str]) -> float:
    for rank, doc_id in enumerate(results):
        if _strip_anchor(doc_id) in expected:
            return 1.0 / (rank + 1)
    return 0.0
```

This computes the **reciprocal rank of the first relevant hit in a single
ranked list against one query's expected-set** — the per-query building block
of **MRR@10** (`evaluate()` at line 111: `mrr10 = rr_sum /
queries_with_expected`, averaged across queries; module docstring line 1
literally says "Recall@5, Recall@10, MRR@10"). It does **not** implement
**RRF (reciprocal-rank fusion)** — RRF combines *multiple ranked lists for the
same query* into one score per document via `score(d) = Σ_lists 1/(k + rank_in_list(d))`,
summed across channels, not averaged across queries against a single list.
**CONFIRMED**: `_reciprocal_rank()` is an MRR@10 primitive, not RRF. The
ticket's own Out-of-Scope line ("must not be named/implemented the same as
`eval_search.py`'s `_reciprocal_rank()`") is correct and must be honored —
the new fusion module needs its own distinctly-named function (e.g. something
like `_rrf_score()` or `_fuse_rankings()`), never reusing `_reciprocal_rank`.

## Mechanics / Engine Constraints

This ticket is agent-orchestration/retrieval tooling, not simulation logic —
no `docs/mechanics/` chapter governs it. The binding constraints are process/
architecture contracts:

- `docs/engine/contracts/context_packet_contract.md` §2 — the `included[]`
  field shape (`source_id, kind, path, heading_or_symbol, hash, authority,
  freshness, score, inclusion_reason, excerpt_budget`) that a fused/filtered
  candidate must be assemblable into, per `ticket_plan_structure_phase3.md`
  item 1. **Discrepancy found**: the ticket's own Assumptions section
  paraphrases the metadata-filter field list as "authority/status/provider/
  lifecycle/freshness," but the actual contract's per-source `included[]`
  fields are only `authority` and `freshness` — `status` feeds into deriving
  `freshness` (§3: "`freshness` is derived from that source's frontmatter
  `status`... plus `last_verified`"), it is not an independent filterable
  field on a packet entry. `provider` and `lifecycle` are not `included[]`
  fields at all — `provider` is a top-level `ContextRequest` field (who is
  asking), and no field named `lifecycle` exists anywhere in
  `context_packet_contract.md`. The idea doc's "Retrieval layers" section
  (`idea_context_efficient_agent_retrieval_observability.md` line 127) does
  list "source kind, component, status, authority, provider, lifecycle, and
  freshness" as filter dimensions in prose, but that is the *idea doc's*
  aspirational list, not the *resolved* Decision-3 contract's field shape —
  `ticket_plan_structure_phase3.md` (line 64) itself narrows this to "source
  kind, authority, freshness" for this phase. **Flagged as an open question
  below**: the planner must pick a concrete, small filter-field set grounded
  in the resolved contract (`kind`, `authority`, `freshness`), not the wider
  aspirational idea-doc list, unless a reason is given to widen it.
- `docs/ai/code_test_index_boundaries_decision.md` — governs the sibling
  code/test index ticket, not this one, but its Part A/Part B distinction is
  precedent for "only build what's deterministically groundable now."
- `ticket_plan_structure_phase3.md` — binds this ticket's Item 1 (hybrid
  retrieval fusion) to "no mandatory invocation," "no `.claude/workflows/*.js`
  wiring," "no lightweight re-ranker," all mirrored in the ticket's own Out of
  Scope section.
- `docs/ai/default_packet_scenarios_decision.md` — informs which scenarios a
  future consumer of this fusion module might serve, but does not constrain
  this ticket's implementation directly (no scenario routing required here).

## Parity Ledger Overlap

- **No existing entry** in any `docs/parity_ledger/*.yaml` covers
  `tools/knowledge_search.py`'s or `tools/search_mcp.py`'s BM25/dense fusion
  logic specifically. Grepped all subsystem files for
  `hybrid|BM25|lexical|retrieval|fusion|rrf`; the only real hits are
  `INFRA-188` (`docs/parity_ledger/infrastructure.yaml:1990-1999`, `status:
  verified`, `priority: P2`, covers `tools/search_server.py` generically as
  "hybrid-scored results," `test_path: tests/tools/test_search_server.py`) and
  `INFRA-292` (`infrastructure.yaml:5927-5956`, covers the unrelated
  `TCK-20260728-RETRIEVAL-BASELINE-METRICS` tool). Neither entry names
  `knowledge_search.py::cmd_query()` or `search_mcp.py::_run_search()`
  directly, and neither is `P0`, so no existing `test_path` is required to
  keep passing as a parity gate for this specific fix (though INFRA-188's own
  `test_path` should still pass since `search_server.py` is untouched by this
  ticket — see Anti-Drift Hazards for why that could still regress).
- **Established precedent for adding a new entry**: `docs/parity_ledger/
  infrastructure.yaml`'s `INFRA-281` through `INFRA-292` block is an active,
  repeated pattern of giving each code-producing agent-infrastructure/
  monitoring tooling ticket its own `P2`, `status: verified` entry with a
  `support_boundary` field stating "Agent-orchestration/monitoring-pipeline
  tooling only — no simulation behavior." The sibling ticket
  `TCK-20260729-DETERMINISTIC-CODE-INDEX` (done, same Phase-3 batch)
  independently concluded it should get its own next-available `INFRA-29X`
  entry on the same grounds, explicitly rejecting `context_packet_contract.md`
  §4's "absence of a parity entry is not a gap" framing as applicable only to
  documentation-only tickets, not code-producing ones. **This ticket should
  follow the same precedent**: once `tools/hybrid_retrieval.py` lands, add a
  new `INFRA-29X` entry (next available ID after whatever
  `DETERMINISTIC-CODE-INDEX` claimed) with `priority: P2`,
  `support_boundary: "Agent-orchestration/retrieval tooling only — no
  simulation behavior"`, and `test_path` pointing at
  `tests/tools/test_hybrid_retrieval.py`. This is not a hard requirement
  since no `P0` entry exists to gate on, but it is the established, actively
  maintained pattern this batch's own sibling ticket already validated —
  deviating from it without reason would be inconsistent, not neutral.

## Prior Work

- `TCK-20260612-LOCAL-CTX-HYBRID-SEARCH` (done) — added BM25 + the current
  linear-weighted `_hybrid_score()` formula (`semantic*0.55 + keyword*0.25 +
  title*0.10 + heading*0.05 + code*0.05`, `knowledge_search.py:513-537`) this
  ticket's Scope explicitly says to replace with RRF, not tune further.
- `TCK-20260612-LOCAL-CTX-DOCS-CORPUS` (done) — established the docs/ corpus
  and the standing scope-guard test pattern
  (`TestCorpusScopeGuard::test_collect_corpus_only_reads_defined_roots`) that
  the sibling `DETERMINISTIC-CODE-INDEX` ticket cites as the anti-drift
  pattern to mirror for its own module boundary; the same discipline applies
  here — `tools/hybrid_retrieval.py` should not be folded into
  `knowledge_search.py`'s corpus definition.
- `TCK-20260612-LOCAL-CTX-EVAL` (done) — built `tools/eval_search.py` and
  `tools/eval/queries.json`; `_reciprocal_rank()`/MRR@10 both originate here
  (see naming-collision analysis above).
- `TCK-20260728-CONTEXT-PACKET-SCHEMA` (done, stored_artifacts present) —
  resolved the `ContextPacket`/`ContextRequest` field contract this ticket
  must assemble filtered/fused candidates into; no code was added by that
  ticket (documentation only), confirmed by its own investigation.
- `TCK-20260728-DEFAULT-PACKET-CRITERIA` (done, hotfix tier, no staging
  artifacts — content read directly from
  `docs/ai/default_packet_scenarios_decision.md`) — informs future scenario
  routing, not required by this ticket's fusion+filter scope.
- `TCK-20260728-CODE-TEST-INDEX-BOUNDARIES` (done, hotfix tier, no staging
  artifacts) — governs the sibling code/test index ticket's Part A/B
  boundary; not directly load-bearing for this ticket, but its
  Part-A-deterministic-only discipline is the same "don't overclaim
  correctness" posture this ticket's fix embodies.
- `TCK-20260729-DETERMINISTIC-CODE-INDEX` (done, same Phase-3 batch,
  stored_artifacts present) — sibling ticket #1 in
  `tickets/todos/context-retrieval-phase3/SEQUENCE.md`. Its investigation
  independently confirms: (a) the parity-ledger-entry precedent cited above,
  (b) `tools/knowledge_search.py` and `tools/agent-monitoring/build_index.py`
  as the two established local-SQLite-index shapes to follow if this ticket's
  module needs its own persistence (it likely does not — fusion is a
  per-query computation over the two existing indexes, not a new corpus), and
  (c) that `tools/hybrid_retrieval.py` and `tools/code_test_index.py` are
  explicitly separate, non-overlapping modules per both tickets' Out of
  Scope sections.
- `tickets/todos/context-retrieval-phase3/SEQUENCE.md` — confirms this ticket
  (#2 of 4) has no in-batch dependency and can be implemented independently
  of `TCK-20260729-RETRIEVAL-CACHE-LEVELS`, but ticket #4
  (`TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) has a **hard, load-bearing
  dependency on this ticket's actual return-value shape** — meaning the new
  fusion module's public function signature/return type should be treated as
  a stable interface once landed, not an implementation detail to be
  reshuffled casually later.

## Risks and Open Questions

1. **DB schema conclusion (required investigation item).** Direct read of
   `knowledge-index/knowledge.db`'s live schema
   (`SELECT type, name, sql FROM sqlite_master`) shows exactly one metadata-
   bearing table, `knowledge_docs`, with columns `rowid, doc_id, path, text,
   source_type, heading, section` — **no `authority`, `status`, `provider`,
   `lifecycle`, or `freshness` column exists today**, confirmed directly, not
   assumed. `docs/REGISTRY.yaml` (read directly) carries `status`, `layer`,
   `authority`, `audience`, `tags`, `last_verified` per doc entry — the
   closest available source for `authority`/`freshness` (per
   `context_packet_contract.md` §3's exact derivation rule: `freshness` =
   `status` + `last_verified`). **Conclusion: implementing metadata filtering
   requires (a) a build-time join against `docs/REGISTRY.yaml` frontmatter**
   — either at query time (loading `docs/REGISTRY.yaml`, keyed by `path`, on
   each `hybrid_retrieval` call) or by adding new columns to
   `knowledge_docs` populated at `cmd_build()`/`cmd_build_incremental()` time
   from the same registry data. Both are legitimate implementations of the
   same underlying join; **this ticket's investigation cannot pick between
   them from evidence alone** — (b), new schema columns, is very plausibly
   the better-performing and more consistent-with-existing-precedent choice
   given `cmd_build()` already writes per-doc metadata columns at index-build
   time (`heading`, `section` are exactly this shape already), but a
   query-time join is simpler to implement without touching `cmd_build()`'s
   schema and matches this ticket's "read-only... no mandatory invocation"
   posture more literally. **This is a planning-level decision, not
   resolved here — flag explicitly in plan.md rather than silently picking
   one.** Note also: `docs/REGISTRY.yaml` only indexes `docs/` (minus
   `_SKIP_DOC_SUBDIRS`) and `tickets/done/` — `knowledge_docs` additionally
   contains `investigation` and `working_log` source_types that have **no**
   REGISTRY.yaml entry to join against at all. Per
   `context_packet_contract.md` §3's own "Extension — non-registry-backed
   source fallback," those rows have no registry-backed authority/freshness
   signal and must not be defaulted to a real-looking value (e.g. `P2`/
   `historical`) — they need the same `unrated`-style sentinel treatment or
   an explicit design decision for how `_collect_corpus()`'s `ticket` and
   `investigation`/`working_log` source_types map into a metadata filter that
   is fundamentally REGISTRY-shaped.
2. **Metadata filter field-set discrepancy** (see Mechanics/Engine Constraints
   above) — the ticket's Assumptions list `authority/status/provider/
   lifecycle/freshness`, but the resolved contract only supports
   `kind`/`authority`/`freshness` as populated `included[]` fields, and
   `ticket_plan_structure_phase3.md` narrows the filter scope to "source
   kind, authority, freshness" for this phase specifically. Recommend
   grounding the plan in the narrower, resolved set (`kind`, `authority`,
   `freshness`) unless there's a concrete reason to widen it — inventing
   `provider`/`lifecycle` filter semantics here would exceed what Decision 3
   actually resolved.
3. **`search_server.py`'s un-fixed third call site** (see Anti-Drift Hazards)
   is a real, live instance of the same bug, structurally out of scope. Not
   blocking, but should be explicitly named as a known-remaining-gap in the
   ticket's Completion Summary when this ticket closes, not silently ignored.
4. **Candidate-k inconsistency between the two call sites being fixed**:
   `knowledge_search.py` uses `top_k * 3` (line 1010) and `search_mcp.py` uses
   `min(top_k * 4, 50)` (line 105) as their dense-channel candidate bound.
   The new shared fusion helper needs an explicit, single bounded-candidate-
   count policy (a parameter, not two different hardcoded multipliers
   silently preserved) — the plan should decide this rather than copy either
   number forward by default.
5. **Return-value shape stability** (see Prior Work) — since
   `CONTEXT-PACKET-ASSEMBLY` (ticket #4) has a hard dependency on this
   ticket's actual output shape, the plan should treat the new module's
   public function signature as a designed interface, not an incidental
   detail.

## Anti-Drift Hazards

- **Do not silently "fix" `search_server.py`'s copy of the same bug as a
  drive-by.** It shares `_hybrid_score()`/`_compute_boosts()` with the two
  in-scope files but is not in this ticket's Related Code Areas or Scope, and
  a fix there is not requested. If both in-scope call sites move to RRF and
  metadata filtering while `search_server.py` keeps the old linear-weighted
  formula and dense-only-gated bug, that is an intentional, ticket-scoped
  divergence to note at completion — not silently patch or silently ignore.
- **Do not conflate the new RRF fusion function with `eval_search.py`'s
  `_reciprocal_rank()`.** Confirmed distinct concepts (MRR@10 building block
  vs. RRF). Name and implement separately, per the ticket's own Out of Scope
  line.
- **Do not widen the metadata-filter field set beyond what
  `context_packet_contract.md` §3 actually resolved** (`kind`, `authority`,
  `freshness`) without an explicit planning decision — the ticket's own
  Assumptions section paraphrase (`authority/status/provider/lifecycle/
  freshness`) is broader than the resolved contract and should not be
  implemented literally without checking back against the source contract
  (done above).
- **Do not silently default non-REGISTRY-indexed corpus rows** (`ticket`,
  `investigation`, `working_log` source_types) **to a real-looking
  authority/freshness value.** Per `context_packet_contract.md` §3's
  fallback rule, they carry no registry-backed signal and must be
  represented as such (an explicit sentinel), not silently coerced to `P2`/
  `historical` as if a real registry read occurred.
- **Preserve `--mode vector` / `--mode keyword` code paths byte-for-byte** —
  ticket Scope and existing tests
  (`tests/tools/test_knowledge_search.py::TestQueryModeRouting`,
  `TestMissingBm25Fallback`) both depend on today's behavior for those two
  modes; only `hybrid` mode's internals should change.
- **Do not fold this ticket's module into `knowledge_search.py`'s own
  `_collect_corpus()`/`cmd_build()` corpus definition** — it is a fusion/
  filter layer that reads the *existing* two indexes (`knowledge_vec`/
  `knowledge_docs` and `bm25.pkl`), not a new corpus source. The standing
  `TestCorpusScopeGuard` test class is the existing anti-drift guard this
  new work must not need to touch.
- **Do not build a lightweight re-ranker** — explicitly out of scope per the
  ticket, the idea doc ("later option only if evaluation proves... fusion and
  metadata are insufficient"), and `ticket_plan_structure_phase3.md`.
- **Do not wire the new module into any `.claude/workflows/*.js` file** or
  make it auto-invoked by any existing pipeline — must remain a standalone,
  manually-invocable module per the Phase-3 maturity banner.
