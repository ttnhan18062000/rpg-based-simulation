---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-HYBRID-RETRIEVAL-FUSION
artifact_type: plan
tags: [ai, debugging, testing]
---

# Implementation Plan — TCK-20260729-HYBRID-RETRIEVAL-FUSION

## Summary

Build `tools/hybrid_retrieval.py`, a new standalone module implementing true reciprocal-rank
fusion (RRF) over two independently-bounded channels — dense ANN and full-corpus BM25 — plus a
pre-fusion metadata filter, and route both confirmed buggy call sites
(`tools/knowledge_search.py::cmd_query()`'s `hybrid` branch and
`tools/search_mcp.py::_run_search()`) through it. The confirmed bug is structural: today, BM25
scores are computed corpus-wide but a document can only ever appear in `results` if it survived
the dense-channel ANN's `top_k*3` (or `min(top_k*4,50)`) cut — a high-BM25-score, low-semantic-
similarity exact match is silently unreachable. The fix independently retrieves a bounded top-N
from each channel, unions by `doc_id`, and fuses with the literal RRF formula
(`score = Σ 1/(k+rank)`), replacing the current `_hybrid_score()` linear-weighted formula for the
`hybrid` path only — `_hybrid_score()` itself is untouched and keeps serving `--mode vector`/
`--mode keyword`. Metadata filtering (`authority`/`freshness`, per
`context_packet_contract.md` §3, resolved below) excludes non-matching candidates from each
channel's ranked list *before* RRF scores are computed, not after. `tools/search_server.py`
shares the identical bug but is out of this ticket's scope and is not touched.

## Resolved Decisions

Three items were flagged by investigation.md as open questions. Per CLAUDE.md's Clarification
Rule and the explicit instruction accompanying this planning task, each is resolved here with a
stated rationale, not left as a blocking "Unresolved Questions" item.

1. **Metadata filter field set.** The ticket's own Assumptions section paraphrases the field list
   as `authority/status/provider/lifecycle/freshness`, but `context_packet_contract.md` §2/§3 (the
   authoritative, resolved contract per CLAUDE.md's Authoritative Mechanics Rule) only populates
   `authority` and `freshness` on an `included[]` entry. `status` is not an independent filterable
   field — it is one of the two inputs `freshness` is *derived from* (§3: `freshness` = frontmatter
   `status` + `last_verified`). `provider` is a top-level `ContextRequest` field (who is asking),
   never a per-source/doc-level field. No field named `lifecycle` exists anywhere in the contract.
   **Resolved: the new module filters on `authority` (`P0`/`P1`/`P2`) and `freshness`
   (`authoritative`/`active`/`historical`/`archive`, i.e. REGISTRY's `status` value passed through
   as `freshness` per the contract's derivation rule — `last_verified`-based recency refinement is
   not implemented, since no AC or contract clause requires numeric recency scoring, only the
   status-derived category) only.** `status` is not exposed as a separate filter key (it *is*
   `freshness`'s source, per the contract). `provider`/`lifecycle` are not implemented as doc-level
   filters at all — inventing them would exceed what Decision 3 (`context_packet_contract.md`)
   actually resolved. The module also exposes a `kind` field (`doc`, `ticket`, `investigation`,
   `working_log`, derived 1:1 from `knowledge_docs.source_type` — the contract's `kind` list is
   explicitly "e.g."-prefixed, i.e. illustrative not exhaustive, so extending it with the two
   source_types the contract's registry-backed/non-registry-backed split doesn't itself enumerate
   is a direct, non-inventive pass-through) for future consumers, but this ticket's filter
   predicate (Step 3) only accepts `authority_in`/`freshness_in` — `kind` filtering is not wired
   into `filter_candidates()`'s signature since neither the ticket's Scope nor ACs ask for it; adding
   it would be scope creep beyond "authority/freshness" fields this decision narrows to.

2. **Join mechanism for metadata (query-time vs. new `knowledge_docs` columns).** `knowledge.db`'s
   live schema has no `authority`/`status`/`freshness` column (confirmed by investigation's direct
   `sqlite_master` read); `docs/REGISTRY.yaml` already carries `authority`/`status`/`last_verified`
   per doc, keyed by repo-relative `path`. **Resolved: a query-time join against
   `docs/REGISTRY.yaml`, not a `knowledge_docs` schema migration.** This ticket's Scope names only
   "a new fusion module + bug fix" — no DB migration is requested, and a schema change to
   `knowledge_docs` would require touching `cmd_build()`/`cmd_build_incremental()`, which is
   explicitly not in this ticket's Related Code Areas. `docs/REGISTRY.yaml` is already the
   authoritative flat index CLAUDE.md's Graphify Integration section instructs callers to query for
   exactly this class of per-doc metadata. Mechanically: `tools/hybrid_retrieval.py` loads
   `docs/REGISTRY.yaml` once (`load_registry_index()`, `functools.lru_cache(maxsize=1)`-cached by
   resolved path — "once per query call, or cache it" per investigation's own framing; caching is
   preferable here because `search_mcp.py` is a long-lived server process making many
   `search_docs` calls, so re-parsing the YAML on every call would be wasteful), keyed by `path`,
   and looks up each candidate's `knowledge_docs.path` value against it. A `knowledge_docs` row
   whose `path` has no `docs/REGISTRY.yaml` entry (covers every `ticket`/`investigation`/
   `working_log` row not under `tickets/done/`, since REGISTRY only indexes `docs/` and
   `tickets/done/`) resolves to the `unrated` sentinel for both `authority` and `freshness` per
   `context_packet_contract.md` §3's non-registry-backed fallback rule — never a fabricated
   `P2`/`historical`-looking default.

3. **`tools/search_server.py`'s identical bug.** Confirmed by investigation to share the same
   dense-candidate-gating structure via `_ks._compute_boosts()`/`_ks._hybrid_score()`, but it is
   not named in this ticket's Related Code Areas or Scope ("fix both call sites" names only
   `knowledge_search.py` and `search_mcp.py`). **Resolved: out of scope, not touched by this
   diff.** No import of, or edit to, `tools/search_server.py` occurs in any step below. This is
   named explicitly in the ticket's Completion Summary at close as a known, deliberate remaining
   gap (not silently dropped) — a follow-up ticket may be filed later, but filing it is outside
   this planning task's authority and is not done here.

No item above is genuinely undecidable without a human — no "Unresolved Questions" heading
follows this section.

## Steps

### Step 1 — Module skeleton and true RRF core (`reciprocal_rank_fusion`)
**Files:** `tools/hybrid_retrieval.py` (new), `tests/tools/test_hybrid_retrieval.py` (new)
**Change:**
- Create `tools/hybrid_retrieval.py` with a module docstring stating: standalone fusion/filter
  layer over the *existing* `knowledge_vec`/`knowledge_docs` tables and `bm25.pkl` — not a new
  corpus source, not wired into any `.claude/workflows/*.js` file, no lightweight re-ranker.
- `DEFAULT_RRF_K: int = 60` — module constant (the standard RRF literature default).
- `reciprocal_rank_fusion(ranked_lists: dict[str, list[str]], k: int = DEFAULT_RRF_K) -> dict[str, float]`:
  for each named channel's ranked `doc_id` list (index 0 = rank 1, best), accumulate
  `1.0 / (k + rank)` per `doc_id` into a running total across all channels; a `doc_id` absent from
  a channel contributes `0.0` from that channel. Returns `{doc_id: total_score}` covering the
  **union** of all `doc_id`s across all input lists (a `doc_id` present in only one channel still
  appears in the output with that channel's sole contribution).
- Name it `reciprocal_rank_fusion` (or `rrf_score` as an internal per-item helper) — never
  `_reciprocal_rank`, and never a re-export/alias of `eval_search.py::_reciprocal_rank`
  (Resolved by ticket's own Out of Scope line; distinct signatures: RRF takes `dict[str,
  list[str]]` of multiple ranked lists, MRR's `_reciprocal_rank` takes one `list[str]` + one
  `set[str]`).
**Do NOT touch:** `tools/eval_search.py` (any function, including `_reciprocal_rank()` itself —
read-only reference for the naming-collision guard, not modified).
**Verify:** `test_rrf_score_matches_formula_for_known_ranks`,
`test_union_by_doc_id_includes_single_channel_hits`,
`test_fusion_function_name_distinct_from_eval_search_reciprocal_rank`.

### Step 2 — Metadata resolution against `docs/REGISTRY.yaml` (query-time join)
**Files:** `tools/hybrid_retrieval.py`, `tests/tools/test_hybrid_retrieval.py`
**Change:**
- `UNRATED: str = "unrated"` — module constant, the sentinel value for both `authority` and
  `freshness` on any candidate with no `docs/REGISTRY.yaml` entry (Resolved Decision 1/2). Must be
  distinct from `AUTHORITY_VALUES = {"P0","P1","P2"}` and
  `STATUS_VALUES = {"authoritative","active","historical","archive"}`
  (`tools/validate_frontmatter.py:44,54`) — read those two constants from
  `tools.validate_frontmatter` (import, do not re-literal them) so the module never drifts from
  the one enum source of truth.
- `load_registry_index(registry_path: Path) -> dict[str, dict]`: parse `docs/REGISTRY.yaml` (PyYAML
  `safe_load`), key the returned dict by each entry's `path` field, value = the full entry dict
  (`status`, `authority`, `last_verified`, etc.). Cached via
  `functools.lru_cache(maxsize=1)` on a private wrapper keyed by the resolved path string (single
  process, e.g. `search_mcp.py`'s long-lived server, re-parses at most once).
- `resolve_metadata(path: str, source_type: str, registry_index: dict[str, dict]) -> dict`:
  look up `registry_index.get(path)`. If found, return
  `{"kind": <mapped from source_type below>, "authority": entry["authority"], "freshness":
  entry["status"]}`. If not found, return `{"kind": ..., "authority": UNRATED, "freshness":
  UNRATED}`. `kind` mapping is a direct 1:1 pass-through of `knowledge_docs.source_type`
  (`doc_chunk` → `"doc"`, `ticket` → `"ticket"`, `investigation` → `"investigation"`,
  `working_log` → `"working_log"`) — confirm before writing that `knowledge_docs.path` values use
  the same repo-relative-path format as `docs/REGISTRY.yaml`'s `path` field (both should be
  `docs/...`/`tickets/done/...`-style paths from repo root; verify against a live row before
  wiring the join key literally).
**Do NOT touch:** `tools/generate_registry.py`, `tools/validate_frontmatter.py` (read `
AUTHORITY_VALUES`/`STATUS_VALUES` only — no edits), `docs/REGISTRY.yaml` itself (read-only).
**Verify:** `test_non_registry_backed_rows_get_sentinel_not_fabricated_value`.

### Step 3 — Pre-fusion metadata filter (`filter_candidates`)
**Files:** `tools/hybrid_retrieval.py`, `tests/tools/test_hybrid_retrieval.py`
**Change:**
- `filter_candidates(ranked_lists: dict[str, list[str]], metadata_by_id: dict[str, dict], *,
  authority_in: set[str] | None = None, freshness_in: set[str] | None = None) -> dict[str,
  list[str]]`: for each channel's ranked list, keep only `doc_id`s whose
  `metadata_by_id[doc_id]["authority"] in authority_in` (if `authority_in` given) **and**
  `metadata_by_id[doc_id]["freshness"] in freshness_in` (if `freshness_in` given), preserving
  original relative order within each list (so filtered rank position = index+1 in the filtered
  list — no renumbering trick, no post-hoc down-weighting). If both filter args are `None`, return
  `ranked_lists` unchanged (no-op — filtering is opt-in, not forced on every call).
- The returned filtered `ranked_lists` is what gets passed into `reciprocal_rank_fusion()` (Step
  1) — a filtered-out `doc_id` never appears in any list `reciprocal_rank_fusion` sees, satisfying
  AC3's literal "excluded from fusion entirely," not merely down-ranked post-hoc.
**Do NOT touch:** `reciprocal_rank_fusion()` itself (Step 1) — filtering is a separate,
composable step that runs strictly before fusion, not folded into the fusion function's own
logic.
**Verify:** `test_metadata_filter_excludes_before_fusion`.

### Step 4 — Orchestration: bounded dense + lexical retrieval, union, filter, fuse
**Files:** `tools/hybrid_retrieval.py`, `tests/tools/test_hybrid_retrieval.py`
**Change:**
- `@dataclass(frozen=True) class HybridResult`: `doc_id: str`, `path: str`, `heading: str`,
  `section: str`, `text: str`, `rrf_score: float`, `dense_rank: int | None`,
  `lexical_rank: int | None`, `semantic_score: float | None`, `keyword_score: float | None`,
  `authority: str`, `freshness: str`, `kind: str`. This is a designed, stable return shape —
  `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` (ticket #4 of this batch) has a hard, load-bearing
  dependency on it per investigation's Prior Work section; do not reshuffle field names once
  Steps 5-6 land without checking that ticket first.
- `DEFAULT_CANDIDATE_MULTIPLIER: int = 4`, `DEFAULT_CANDIDATE_CAP: int = 50` — module constants
  unifying the two pre-existing, inconsistent magic numbers (`knowledge_search.py`'s bare
  `top_k*3` and `search_mcp.py`'s `min(top_k*4, 50)`) into one explicit, single policy:
  `candidate_k(top_k) = min(top_k * DEFAULT_CANDIDATE_MULTIPLIER, DEFAULT_CANDIDATE_CAP)`. Chosen
  over `top_k*3`: it is already-capped (bounded compute even for large `top_k`), and is the
  bound the ticket's own most-critical live call site (`search_mcp.py`'s `search_docs`, invoked by
  every agent this session and others) already uses — both channels (dense and lexical) use this
  same formula, each exposed as an overridable keyword parameter, not a hardcoded literal.
- `hybrid_fuse_and_filter(*, conn: sqlite3.Connection, query_vec_bytes: bytes, query_tokens:
  list[str], bm25_obj, bm25_doc_ids: list[str], top_k: int, dense_candidate_k: int | None = None,
  lexical_candidate_k: int | None = None, registry_index: dict[str, dict] | None = None,
  authority_in: set[str] | None = None, freshness_in: set[str] | None = None, rrf_k: int =
  DEFAULT_RRF_K) -> list[HybridResult]`:
  1. Default `dense_candidate_k`/`lexical_candidate_k` to `candidate_k(top_k)` if not given.
  2. **Dense channel**: run the ANN `SELECT ... FROM knowledge_vec v JOIN knowledge_docs d ...
     WHERE v.embedding MATCH ? AND k = ? ORDER BY v.distance` query (same SQL shape as today's
     `cmd_query`/`_run_search`) with `dense_candidate_k`. Build `dense_ranked: list[doc_id]` in
     distance-ascending order and a `row_by_id: dict[doc_id, row]` cache of full row data
     (`path, heading, section, text, source_type`).
  3. **Lexical channel** (independent of the dense query, this is the bug fix): compute
     `bm25_obj.get_scores(query_tokens)` once (full corpus, as today), sort **all** corpus rows by
     score descending, take the top `lexical_candidate_k` `doc_id`s (via `bm25_doc_ids`, the
     parallel array from `_load_bm25()`) as `lexical_ranked: list[doc_id]`. For any `doc_id` in
     `lexical_ranked` not already in `row_by_id` (a genuine lexical-only hit outside the dense
     cut — the exact scenario the bug drops today), fetch its row from `knowledge_docs` by
     `doc_id` and add it to `row_by_id`.
  4. Build `metadata_by_id` via `resolve_metadata()` (Step 2) for every `doc_id` in
     `row_by_id`, using `registry_index` (or an empty dict if `None`, in which case every
     candidate resolves to `UNRATED` and any `authority_in`/`freshness_in` filter excludes
     everything not literally passing `"unrated" in authority_in`/`freshness_in` — documented as
     the expected, non-silent behavior when no registry is supplied).
  5. `filter_candidates({"dense": dense_ranked, "lexical": lexical_ranked}, metadata_by_id,
     authority_in=authority_in, freshness_in=freshness_in)` (Step 3) → filtered ranked lists.
  6. `reciprocal_rank_fusion(filtered_lists, k=rrf_k)` (Step 1) → `{doc_id: rrf_score}`.
  7. Sort surviving `doc_id`s by `rrf_score` descending, tie-break by `doc_id` ascending
     (determinism — Hard Rule "Do not break determinism"), take top `top_k`.
  8. For each, compute `dense_rank`/`lexical_rank` (1-based position in the *filtered* list, or
     `None` if absent from that channel) and `semantic_score`/`keyword_score` (derived from the
     original distance/BM25 raw value the same way `cmd_query`/`_run_search` do today, purely for
     output/debugging — not fed back into `rrf_score`), and build the `HybridResult`.
**Do NOT touch:** the SQL shape of the existing ANN query beyond parameterizing `dense_candidate_k`
— do not change `knowledge_vec`'s schema or the `MATCH`/`k = ?` sqlite-vec query syntax itself.
**Verify:** `test_lexical_only_match_outside_dense_cut_is_surfaced` (the direct regression test
for the confirmed bug, using a small fixture DB + BM25 index where one document's exact rare
token places it outside `dense_candidate_k` on the dense channel alone).

### Step 5 — Wire `tools/knowledge_search.py::cmd_query()`'s `hybrid` branch to the new helper
**Files:** `tools/knowledge_search.py`, `tests/tools/test_knowledge_search.py`
**Change:**
- In `cmd_query()`, the `mode in ("hybrid", "vector")` branch (lines ~998-1038): when `mode ==
  "hybrid"` **and** `bm25_obj is not None` (i.e. true hybrid, not the graceful `hybrid`→`vector`
  fallback already handled above at lines 981-983), replace the current
  "ANN query → iterate `rows` → look up `bm25_raw[rowid]`" sequence with a call to
  `hybrid_retrieval.hybrid_fuse_and_filter(conn=conn, query_vec_bytes=_serialize_f32(query_emb.tolist()),
  query_tokens=query_tokens, bm25_obj=bm25_obj, bm25_doc_ids=_bm25_doc_ids, top_k=top_k)` (no
  `authority_in`/`freshness_in`/`registry_index` — this ticket does not add new `--authority`/
  `--freshness` CLI flags to the `query` subcommand; those parameters exist on the module for the
  future `CONTEXT-PACKET-ASSEMBLY` ticket to wire, not this one). Map the returned
  `list[HybridResult]` to the same tab-separated print format the function already emits
  (`doc_id, path, heading, section, final, semantic, keyword, snippet`), using `rrf_score` in the
  `final` column position and `semantic_score`/`keyword_score` for the other two score columns
  (`0.0` if `None`).
- When `mode == "vector"` (bm25 not loaded, or `mode` never was `"hybrid"`), the existing
  ANN-only path (no BM25 lookup at all) is **unchanged** — it must not call into
  `hybrid_retrieval` at all, since it has no lexical channel to fuse.
- Add `import hybrid_retrieval` (or the sibling-file `importlib` load pattern
  `search_mcp.py` already uses for `knowledge_search`, whichever matches the existing import
  convention in `knowledge_search.py` more closely — `knowledge_search.py` currently has no
  intra-`tools/` import, so a plain `from hybrid_retrieval import hybrid_fuse_and_filter` at
  module top, mirroring how `tools/` scripts are invoked, is preferred unless it breaks the
  existing `python3 tools/knowledge_search.py` direct-invocation pattern — verify with a quick
  `python3 tools/knowledge_search.py query "test"` smoke run before finalizing the import style).
**Do NOT touch:** the `mode == "keyword"` branch (lines ~1040-1060) — full-corpus BM25-only scan,
untouched byte-for-byte, per ticket Scope's explicit "Preserve existing --mode vector/--mode
keyword code paths unmodified." Do not change `_hybrid_score()`'s formula, signature, or callers
in the vector/keyword paths.
**Verify:** `test_knowledge_search_cmd_query_uses_fusion_helper` (integration, subprocess CLI),
plus the pre-existing `TestQueryModeRouting::test_query_mode_vector_skips_bm25` and
`test_query_mode_keyword_skips_embedding` must still pass unmodified, plus the new
`test_vector_and_keyword_modes_do_not_import_fusion_module` (patch/spy on
`hybrid_retrieval.hybrid_fuse_and_filter`, assert zero calls when `mode` is `"vector"` or
`"keyword"`).

### Step 6 — Wire `tools/search_mcp.py::_run_search()` to the new helper
**Files:** `tools/search_mcp.py`, `tests/tools/test_search_mcp.py`
**Change:**
- Replace `_run_search()`'s body (lines ~89-145: the ANN-only `rows` fetch, the per-row BM25
  lookup loop recomputing `get_scores()` inside the loop) with a call to
  `hybrid_retrieval.hybrid_fuse_and_filter(conn=con, query_vec_bytes=q_bytes,
  query_tokens=query_tokens, bm25_obj=_STATE.bm25, bm25_doc_ids=_STATE.doc_ids, top_k=top_k)`
  (same no-filter-args posture as Step 5 — `section` post-filtering, line 115-116, stays a
  post-fusion filter on the final `HybridResult` list by `.section == section`, since `section` is
  not one of this ticket's resolved metadata-filter fields and the existing behavior — filtering
  the CLI-facing result set by an exact `section` string match — is orthogonal to
  authority/freshness filtering).
- Map each `HybridResult` to the exact existing external return-shape dict (`doc_id, title,
  heading, source_path, section, score, semantic_score, keyword_score, excerpt`) — `score` =
  `rrf_score` (was `combined` from `_hybrid_score()`), `excerpt` = `text[:200]` as today. This
  preserves `_run_search()`'s documented external contract (test_plan.md's Regression Surface
  note) even though its internals change.
- This also fixes the incidental inefficiency investigation noted (BM25 `get_scores()` recomputed
  once per row inside the old loop) as a natural side effect of routing through
  `hybrid_fuse_and_filter`, which computes it once — not a separately-scoped optimization task,
  just what correctly calling the shared helper produces.
**Do NOT touch:** `_ensure_loaded()`, `_run_health()`, the MCP tool registration/`--test` stdin
mode, or `_derive_title()` — none of these are part of the bug or its fix.
**Verify:** `test_search_mcp_run_search_uses_fusion_helper` (the same lexical-outside-dense-cut
fixture run through `_run_search()` directly), plus pre-existing `TestRunSearch` (external
return-shape contract) must still pass unmodified.

### Step 7 — Regression pass and parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml` (append only); no other files changed.
**Change:**
- Run, in order:
  ```
  pytest tests/tools/test_hybrid_retrieval.py -v
  pytest tests/tools/test_knowledge_search.py tests/tools/test_search_mcp.py tests/tools/test_eval_search.py -v -m "not slow"
  pytest tests/tools/test_knowledge_search.py tests/tools/test_search_mcp.py tests/tools/test_eval_search.py tests/tools/test_hybrid_retrieval.py -v
  ```
  (last line only if `sentence-transformers`/`sqlite-vec`/`rank-bm25` + a live/fixture index are
  available, per test_plan.md's Scoped Pytest Commands).
- Append a new entry `id: INFRA-294` (next available after `INFRA-293`, claimed by the sibling
  `TCK-20260729-DETERMINISTIC-CODE-INDEX`) to `docs/parity_ledger/infrastructure.yaml`, following
  the exact shape of `INFRA-281`–`INFRA-293`: `text` (one paragraph: new RRF-fusion module fixing
  the confirmed dense-candidate-gating bug at both `knowledge_search.py::cmd_query()` and
  `search_mcp.py::_run_search()`, replacing the linear-weighted `_hybrid_score()` for the hybrid
  path only, with pre-fusion authority/freshness metadata filtering), `status: verified`,
  `priority: P2`, `legacy_evidence: null`, `v2_evidence: >` citing `tools/hybrid_retrieval.py`'s
  actual function/line ranges once Steps 1-6 land, `proof_type: regression`, `test_path:
  tests/tools/test_hybrid_retrieval.py`, `divergence_note: null`, `support_boundary: >` stating
  "Agent-orchestration/retrieval tooling only — no simulation behavior, Mechanics Bible chapter, or
  engine contract governs this module's semantics" (same category as `INFRA-281`–`293`). This is
  not a hard gate (no `P0` entry exists), but follows the batch's own established, actively-
  maintained precedent per investigation's Parity Ledger Overlap section.
**Do NOT touch:** any other entry in `infrastructure.yaml` or any other parity ledger file — no
`docs/mechanics/` chapter governs this (confirmed by investigation).
**Verify:** all suites above pass with zero failures/errors; YAML loads validly
(`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`).

## Scope Guards

Verbatim from the ticket's Out of Scope section:
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.
- Conflating with eval_search.py's existing _reciprocal_rank() (an MRR@10 metric) -- new RRF
  fusion logic must be named/implemented distinctly.

Additional guards, derived from investigation.md's Anti-Drift Hazards:
- **Do not touch `tools/search_server.py`** — it shares the identical bug pattern but is not in
  this ticket's Related Code Areas or Scope. No import of it, no edit to it, in any step above.
  Note as a known-remaining-gap in the ticket's Completion Summary at close, not silently ignored;
  filing a follow-up ticket for it is optional and not part of this plan.
- Do not widen the metadata-filter field set beyond `authority`/`freshness` (Resolved Decision 1)
  — no `provider`/`lifecycle` filter semantics, and `status` is not exposed as an independent
  filter key separate from `freshness`.
- Do not add new `knowledge_docs` schema columns or touch `cmd_build()`/`cmd_build_incremental()`
  — metadata filtering is a query-time join against `docs/REGISTRY.yaml` (Resolved Decision 2).
- Do not silently default non-REGISTRY-indexed rows (`ticket` under `tickets/inprogress/`,
  `investigation`, `working_log` source_types) to a real-looking `authority`/`freshness` value —
  they must resolve to the `unrated` sentinel (Step 2).
- Preserve `--mode vector`/`--mode keyword` code paths and their tests byte-for-byte — only
  `hybrid` mode's internals change (Steps 5-6's "Do NOT touch" clauses).
- Do not fold `tools/hybrid_retrieval.py` into `knowledge_search.py`'s own
  `_collect_corpus()`/`cmd_build()` corpus definition — it reads the *existing* two indexes, it is
  not a new corpus source. `TestCorpusScopeGuard`/`TestDocsCorpusScopeGuard` must stay green,
  untouched.
- Do not build a lightweight re-ranker — fusion + metadata filtering is the full scope.
- Do not wire `tools/hybrid_retrieval.py` into any `.claude/workflows/*.js` file or any existing
  pipeline/gate — standalone, manually-invocable-via-import only.
- Do not add new `--authority`/`--freshness` CLI flags to `knowledge_search.py`'s `query`
  subcommand or to `search_mcp.py`'s `search_docs` tool schema — the filter parameters exist on
  the module function signature for a future ticket (`CONTEXT-PACKET-ASSEMBLY`) to wire up; this
  ticket's two call sites pass no filter args (Steps 5-6).
- Do not rename or alias `reciprocal_rank_fusion` to `_reciprocal_rank`, and do not modify
  `tools/eval_search.py::_reciprocal_rank()` or its MRR@10 semantics in any way.

## Dependency Map

- Step 1 (RRF core) — no dependencies. Foundational.
- Step 2 (metadata resolution) — no dependency on Step 1; independent, can be done in parallel.
- Step 3 (filter) — depends on Step 2 (`resolve_metadata`'s output shape) for its test fixtures;
  logically independent of Step 1's implementation (consumes/produces the same `dict[str,
  list[str]]` shape Step 1 consumes, but does not call Step 1's function itself).
- Step 4 (orchestration) — depends on Steps 1, 2, 3 (calls all three).
- Step 5 (`knowledge_search.py` wiring) — depends on Step 4 (`hybrid_fuse_and_filter` must exist
  and be tested first).
- Step 6 (`search_mcp.py` wiring) — depends on Step 4; independent of Step 5 (can be done in
  parallel with Step 5 once Step 4 lands — both call sites route through the same helper but
  neither imports the other).
- Step 7 (regression + parity entry) — depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — exact-term query outside dense candidate_k now surfaces via the lexical channel | Steps 4, 5, 6 | `test_lexical_only_match_outside_dense_cut_is_surfaced`, `test_knowledge_search_cmd_query_uses_fusion_helper`, `test_search_mcp_run_search_uses_fusion_helper` |
| AC2 — dense/lexical channels independently retrieve bounded top-N, unioned by doc/chunk id, ranked via literal RRF (not the linear-weighted formula) | Steps 1, 4 | `test_rrf_score_matches_formula_for_known_ranks`, `test_union_by_doc_id_includes_single_channel_hits`, `test_fusion_function_name_distinct_from_eval_search_reciprocal_rank` |
| AC3 — metadata filter excludes non-matching candidates before RRF ranking | Steps 2, 3 | `test_metadata_filter_excludes_before_fusion`, `test_non_registry_backed_rows_get_sentinel_not_fabricated_value` |
| AC4 — existing --mode vector/--mode keyword paths and their tests continue passing unmodified | Step 5 ("Do NOT touch" clause) | pre-existing `TestQueryModeRouting`, `TestMissingBm25Fallback`; new `test_vector_and_keyword_modes_do_not_import_fusion_module` |
| Scope — fix both named call sites, not just one | Steps 5, 6 | `test_knowledge_search_cmd_query_uses_fusion_helper`, `test_search_mcp_run_search_uses_fusion_helper` |

## Anti-Drift Notes

- The single highest-risk regression is reintroducing the dense-candidate-gating shape inside
  `hybrid_fuse_and_filter()` itself — e.g. building `lexical_ranked` only from `doc_id`s already
  present in `row_by_id` (dense-surviving rows) instead of independently sorting the *full* BM25
  score array and fetching any lexical-only hit's row on demand (Step 4, sub-step 3). That would
  silently reproduce the exact bug this ticket exists to fix, just inside the new module instead
  of the old call sites. `test_lexical_only_match_outside_dense_cut_is_surfaced` exists
  specifically to catch this.
- Filtering must happen on the *ranked lists* fed into `reciprocal_rank_fusion()`, never as a
  post-hoc pass over already-fused `{doc_id: rrf_score}` output — the AC3 test asserts exclusion
  "before fusion," and a post-hoc filter would let a since-excluded low-authority/stale document's
  score still influence which documents got displaced from the bounded `dense_candidate_k`/
  `lexical_candidate_k` cut before its own exclusion, which is the literal ordering bug AC3 is
  designed to prevent.
- `UNRATED` ("unrated") must never collapse into `AUTHORITY_VALUES`/`STATUS_VALUES`'s real enum
  members — it is a sentinel stating "no registry-backed signal exists," not a real rating.
  Constructing it as a distinct string literal outside both imported enums (Step 2) is the guard.
- `reciprocal_rank_fusion` and `eval_search.py::_reciprocal_rank` are confirmed distinct concepts
  (RRF fusion of multiple ranked lists for one query vs. the reciprocal rank of one list's first
  hit, an MRR@10 building block) — do not rename, alias, or merge them under a future refactor
  without re-reading investigation.md's naming-collision analysis first.
- `HybridResult`'s field names are a designed interface `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`
  depends on (investigation's Prior Work section) — treat as stable once Steps 5-6 land; a
  post-hoc rename is not "just a refactor," it is a breaking change to a downstream ticket's
  assumed contract.
- `_hybrid_score()` (the old linear-weighted formula, `knowledge_search.py:513-537`) is not
  deleted and not modified — it remains the scoring function for `--mode vector`/`--mode keyword`
  and for `tools/search_server.py` (out of scope, untouched). Only the `hybrid`-mode branches of
  the two named call sites stop calling it.
- `search_mcp.py`'s `section` post-filter (line 115-116 today) is preserved as a post-fusion
  filter on the final result list — it is not one of this ticket's resolved metadata-filter
  fields (`authority`/`freshness`) and must not be folded into `filter_candidates()`'s pre-fusion
  logic, which would change its semantics from an exact CLI-facing narrowing to a pre-ranking
  exclusion the existing `TestRunSearch` contract does not expect.

## Deviations

Recorded during implementation. None change the plan's Steps/Scope Guards/Acceptance-Criteria
Map — both are implementation-detail resolutions the plan's prose left implicit or ambiguous.

1. **`bm25_obj=None` handling in `hybrid_fuse_and_filter()` (Step 4).** The plan's signature
   marks `bm25_obj` as a required parameter with no stated null-handling. Investigation showed
   `search_mcp.py::_run_search()` calls into the hybrid path unconditionally regardless of whether
   BM25 loaded (unlike `knowledge_search.py::cmd_query()`, which only reaches the true-hybrid
   branch once `bm25_obj is not None` is already confirmed) — `_run_search()`'s pre-existing
   contract already tolerates a missing BM25 index by degrading to vector-only scoring rather than
   crashing (`if _STATE.bm25 is not None and query_tokens: ...`). To preserve that contract through
   the new shared helper, `hybrid_fuse_and_filter()` treats `bm25_obj=None` (or empty
   `bm25_doc_ids`) as "lexical channel contributes nothing" — `lexical_ranked = []`, RRF degrades
   to dense-only ranking — rather than raising. This does not change any of the plan's four ACs or
   its Steps; it closes an edge case the plan's prose didn't explicitly resolve for this specific
   caller. Covered by `test_bm25_none_degrades_to_dense_only_without_crashing` in
   `tests/tools/test_hybrid_retrieval.py`.

2. **`semantic_score`/`keyword_score` formula for the shared `HybridResult` (Step 4, sub-step 8).**
   The plan states these are derived "the original distance/BM25 raw value the same way
   `cmd_query`/`_run_search` do today" — but investigation.md's own Current Behavior section
   documents that the two old call sites used *different* ad hoc formulas
   (`knowledge_search.py`: `semantic = 1 - dist/2.0`, `keyword = raw/bm25_max`; `search_mcp.py`:
   `sem_score = 1 - distance` (no `/2.0`), `kw_score = raw/10.0`). Since `HybridResult` is one
   shared, designed type consumed by both callers (per the plan's own stability note citing
   `CONTEXT-PACKET-ASSEMBLY`'s dependency), both formulas could not be literally preserved
   simultaneously. Resolved by adopting `knowledge_search.py`'s formula
   (`1 - dist/2.0`, `raw/bm25_max`) as the single canonical normalization inside
   `hybrid_fuse_and_filter()`, since it is properly bounded to `[0,1]` for sqlite-vec's cosine
   distance range, whereas `search_mcp.py`'s old `1 - distance`/`/10.0` were unbounded/arbitrary.
   Both `semantic_score`/`keyword_score` are explicitly debug/output-only fields (not fed back
   into `rrf_score`), so this changes the *numeric value* of `search_mcp.py`'s
   `semantic_score`/`keyword_score` output fields but not their presence, type, key names, or the
   ranking itself — `_run_search()`'s external return-shape contract (key set) is unchanged and
   `TestRunSearch` passes unmodified.
