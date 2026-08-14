---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260728-EVAL-FIXTURE-REPAIR
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20260728-EVAL-FIXTURE-REPAIR

## Current Behavior

### `tools/eval/queries.json` (40 entries today)
Flat JSON array. Each entry currently has 4 keys: `query`, `expected_doc_ids` (list),
`category`, `notes`. Category distribution: `semantic` 15, `exact-term` 15,
`cross-section` 5, `edge-case` 5 (`tools/eval/queries.json:1-242`). 4 of the 5
`edge-case` entries have `expected_doc_ids: []` (queries.json:213-216, 225-229,
230-235, 236-241); one edge-case entry (misspelled damage-formula query,
queries.json:218-223) has a real expected id and is not truly "no-result".

### `tools/eval_search.py`
- `_run_query()` (L18-34) shells out to `knowledge_search.py query` and parses
  tab-separated stdout into an ordered `doc_id` list.
- `_strip_anchor()` (L37-39) reduces a chunk id (`section/stem#heading-seq`) to
  document identity by splitting on the first `#`.
- `_reciprocal_rank()` (L42-46) / `_hit()` (L49-50) compare `_strip_anchor(d)`
  against the `expected` set.
- `evaluate()` (L53-109): `total = len(queries)` (L54) — **this is unconditional,
  it includes every entry regardless of whether `expected_doc_ids` is empty.**
  `hits5`/`hits10` only increment when `expected` is non-empty and hit (L71-78).
  `recall5 = hits5 / total` and `recall10 = hits10 / total` (L95-96) — **both use
  the full `total`, not a total restricted to queries that have an expected
  answer.** By contrast `mrr10` correctly divides by `queries_with_expected`
  (L98-99), which excludes empty-expected entries. This is an internal
  inconsistency: MRR already excludes no-answer queries from its denominator,
  Recall@5/10 does not. Today, with 4 truly-unanswerable edge-case entries out
  of 40, the maximum achievable Recall@5 is capped at 36/40 = 0.90 regardless of
  retrieval quality.
- No metric beyond Recall@5, Recall@10, MRR@10, and a raw `zero_results` counter
  exists today (L53-109, L125-148).
- `main()` (L151-179) wires `--queries`/`--top-k`/`--threshold` (default 0.80)
  and exits 1 on missing index or missing queries file.

### `tests/tools/test_eval_search.py`
- `TestQueriesJson.test_required_keys` (L35-43) asserts only `query`,
  `expected_doc_ids`, `notes` are present, and that `expected_doc_ids` is a list
  and `query` is a str. No `category`, `allowable_alternatives`,
  `source_lifecycle_assumption`, or `context_budget` checks exist.
- `TestQueriesJson.test_category_balance` (L45-56) hardcodes exactly 4 category
  names (`semantic`, `exact-term`, `cross-section`, `edge-case`) with minimums
  15/15/5/5. Any new category value is invisible to this test as written — it
  would not fail if new categories were added incorrectly, and it would not
  enforce a minimum for them either.
- `TestQueriesJson.test_has_40_entries` (L30-33) uses `>= 40`, so growing the
  fixture is safe against this specific assertion.
- 27 total tests today (7 predecessor-ticket regression tests plus the
  original 21; confirmed via `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`
  completion notes).

### The live index (`tools/knowledge_search.py`)
`cmd_query` (L944-1069) reads `knowledge-index/knowledge.db`, a sqlite-vec +
BM25 hybrid index built by `cmd_build`/`cmd_build_incremental`. Verified present
and current at `/home/vboxuser/Work/rpg-based-simulation/knowledge-index/`
(`knowledge.db`, `bm25.pkl`, `manifest.json`, `embeddings_cache.pkl`, all dated
2026-07-28).

**Root cause of most staleness — a doc_id derivation bug in
`_collect_docs_chunks()` (`tools/knowledge_search.py:232-443`), not a set of
independently-drifted renames.** `section = rel_parts[0]` (L275-278) takes only
the *immediate* subdirectory of `docs/`, so any file two or more levels deep
collapses its intermediate path segments into the doc_id. Confirmed empirically
against the live DB (`knowledge_docs.doc_id` column, itself populated from the
chunk-level `id` field per `cmd_build` L701-707 — the DB column named `doc_id`
is actually chunk-level, `_strip_anchor` is required to reduce it to document
identity):

| queries.json expects (doc-level) | Live index actually has | File |
|---|---|---|
| `engine/contracts/replay_contract` | `engine/replay_contract` | `docs/engine/contracts/replay_contract.md` |
| `engine/contracts/scheduler_contract` | `engine/scheduler_contract` | `docs/engine/contracts/scheduler_contract.md` |
| `engine/contracts/observability_contract` | `engine/observability_contract` | `docs/engine/contracts/observability_contract.md` |
| `engine/contracts/infrastructure_overview` | `engine/infrastructure_overview` | `docs/engine/contracts/infrastructure_overview.md` |
| `architecture/adr-004-simulation-watchdog` | `architecture/simulation_watchdog` | `docs/architecture/simulation_watchdog.md` (no `adr-004-` prefix ever existed in the filename) |
| `architecture/adr-005-performance-optimization` | `architecture/performance_optimization` | `docs/architecture/performance_optimization.md` (no `adr-005-` prefix ever existed) |
| `engine/contracts/progression_package` | **not indexed at all** | `docs/archive/engine_contracts/progression_package.md` — moved under `docs/archive/`, which `_collect_docs_chunks` unconditionally excludes (L251-253, L261-262) |

This means 6 of the 7 stale entries are fixable by correcting the string to
match the indexer's actual (not the intended) doc_id scheme; 1
(`engine/contracts/progression_package`) is genuinely gone from the live
corpus by design (archived docs are excluded on purpose) and has no like-for-
like replacement doc_id — see Risks below.

Traced this assumption back to its origin:
`stored_artifacts/TCK-20260612-LOCAL-CTX-EVAL/investigation.md:21-22` lists
`architecture/adr-004-simulation-watchdog`, `architecture/adr-005-performance-
optimization`, and the `engine/contracts/*` scheme as "representative doc_ids"
at design time — **the assumption was wrong from the moment queries.json was
authored**, not a later rename. It was masked entirely by the separate
anchor-stripping bug that `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX` fixed
(that ticket made Recall@5 go from a hard-coded-false 0.00 to a real but still
partly-wrong 0.53 — the 7 stale ids above are baked into that 0.53, not
introduced after it).

Exhaustive scan: I extracted every distinct `expected_doc_ids` value across
all 40 entries (24 distinct values) and diffed them against the live,
anchor-stripped `knowledge_docs.doc_id` set (1,572 distinct document ids). The
7 listed above are the complete set of misses — no others exist.

## Mechanics / Engine Constraints

None. This ticket touches only `tools/eval/`, `tools/eval_search.py`, and
`tests/tools/test_eval_search.py` — agent tooling/testing infrastructure, not
simulation mechanics or engine contracts. No chapter of `docs/mechanics/` or
contract in `docs/engine/` constrains this work.

## Parity Ledger Overlap

None found. Grepped all of `docs/parity_ledger/*.yaml` for `eval_search`,
`queries.json`, `knowledge_search`, `retrieval` — the only hits are an
unrelated strategic-cognition test-name string match and the
`TCK-20260728-RETRIEVAL-BASELINE-METRICS` entry (`infrastructure.yaml:5939-5956`,
`INFRA-292`), which covers a different tool
(`tools/agent-monitoring/retrieval_baseline_metrics.py`) and is not about
`eval_search.py`/`queries.json`. No P0 entries are affected. No new parity
ledger entry is required by this ticket's own scope (agent-tooling test
fixtures are not mechanics/engine parity subject matter), consistent with the
ticket's own "Related Docs: None."

## Prior Work

- **`TCK-20260612-LOCAL-CTX-EVAL`** (done) — original 40-query fixture and
  `eval_search.py`. Its investigation
  (`stored_artifacts/TCK-20260612-LOCAL-CTX-EVAL/investigation.md`) is the
  source of the incorrect doc_id assumptions listed above — useful as a record
  of *intent* but not as ground truth for current doc_ids.
- **`TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`** (done, hotfix) — fixed the
  bare-vs-anchored comparison bug (`_strip_anchor`), explicitly scoped out
  "auditing/expanding queries.json beyond what's needed to verify the fix" and
  flagged the sub-0.80 result as "a legitimate follow-up ticket" — this ticket
  is that follow-up.
- **`TCK-20260728-RETRIEVAL-BASELINE-METRICS`** (done, same epic, sibling
  ticket) — read-only baseline metrics over `agent-monitoring/*.jsonl`, not
  directly reusable code for this ticket, but establishes the
  epic's precedent for "derived proxy, explicitly labeled, never fabricated"
  metric framing (`INFRA-292`), which the Plan phase should follow when
  designing the new authority/freshness or cost metric here.
- **Epic source doc**
  (`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md:229-243`,
  "Offline retrieval evaluation" section) is the authoritative origin of this
  ticket's exact requirements: the 6 conceptual query-type groups (of which
  group 4, "symbol-to-test and changed-path queries," was split into the
  ticket's 2 separate category values, yielding 7 total), the 4 new per-entry
  fields (worded there as "expected authoritative source IDs, allowable
  alternatives, source lifecycle assumptions, and a context budget" — ticket
  keeps `expected_doc_ids` as-is and adds the other 3), and the 4 candidate new
  metrics ("recall at the packet boundary, authority/freshness correctness,
  duplicate rate, estimated injected-token cost" — the ticket already narrowed
  this to authority/freshness correctness, duplicate rate, or estimated
  injected-token cost, dropping "recall at the packet boundary" since no packet
  boundary exists yet).

## Risks and Open Questions

1. **`engine/contracts/progression_package` has no live replacement doc_id.**
   The archived file still exists at
   `docs/archive/engine_contracts/progression_package.md`, but `docs/archive/`
   is permanently excluded from the index by design (this is intentional
   behavior, not a bug — matches the documented corpus definition in
   `knowledge_search.py`'s module docstring and `docs/` corpus exclusion list).
   The query this feeds ("entity attribute changes after XP reward and level
   up," a `cross-section` entry, queries.json:194-199) currently expects
   `["mechanics/01_entity_anatomy", "engine/contracts/progression_package"]`.
   `docs/mechanics/attribute_progression_contract.md` exists live and appears
   to be the current authoritative doc for this exact topic — but I did not
   verify semantic equivalence to the archived `progression_package.md`'s
   content, and this ticket's own scope note (queries.json line 33) frames
   `progression_package` as "permanently unmatchable," implying the intended
   fix is to drop it from `expected_doc_ids` rather than substitute a
   replacement. **This is exactly the scenario the new `policy-vs-superseded`
   category exists to model** — the Plan phase should decide whether to (a)
   simply drop the dead id from this cross-section entry, or (b) convert this
   entry (or a new one) into a `policy-vs-superseded` example that names
   `attribute_progression_contract` as current and `progression_package` as
   the superseded/archived source via `source_lifecycle_assumption` +
   `allowable_alternatives`. I did not verify (b)'s content match — flagging,
   not assuming.
2. **Recall@5/Recall@10 denominator bug.** `evaluate()`'s `total = len(queries)`
   (L54) is not restricted to queries with a non-empty `expected_doc_ids`, so
   unanswerable entries silently cap the maximum achievable Recall@5/10 below
   1.0 (today: 36/40 = 0.90 max, because 4 of 40 are true no-result). The
   ticket's AC5 wording ("excluded from recall/MRR denominators, matching
   existing edge-case query handling") reads as though this already happens —
   it does not, only MRR's `queries_with_expected` denominator does this
   correctly. Adding new `no-result` category entries without fixing this will
   further shrink the achievable ceiling and change the measured Recall@5
   number (though the 0.80 **threshold** itself is untouched, satisfying the
   ticket's Out-of-Scope constraint — only the achievable maximum and the
   as-measured value change, which appears to be exactly what AC5 is asking
   for). **Recommend the Plan phase treat this as an explicit fix**: restrict
   `total` for recall5/recall10 to `queries_with_expected` (mirroring MRR's
   existing pattern), and document the resulting new baseline number
   distinctly from the old 0.53 baseline so the "0.80 gate's pass/fail meaning
   is unchanged" claim is auditable.
3. **`symbol-to-test` / `changed-path` categories have no matching corpus.**
   The live index's corpus is *only* `tickets/done/`, `stored_artifacts/*/investigation.md`,
   `tickets/working_log.csv`, and `docs/` (excluding archive/lab) — confirmed
   from `knowledge_search.py`'s module docstring (L8-15) and
   `_collect_corpus()` (L128-208). It never indexes `src/` or `tests/`. A
   query whose intent is "given this changed source path, which test covers
   it" cannot be satisfied by doc-only retrieval today — the source doc itself
   places "symbol-to-test index" and "changed-path ownership index" under
   Sequenced-Future-Epic Phase 3 ("Read-only hybrid retrieval," not Phase 1
   which is this ticket). The Plan phase needs to decide what these 2 category
   values actually test given today's corpus: most plausible is that they
   target doc/ticket-corpus proxies for those concepts (e.g., a ticket in
   `working_log.csv` whose summary names a specific function/module, or a doc
   chunk whose `path` field matches a known source directory in prose), not
   literal source-code or test-file retrieval. This should be made explicit in
   each such entry's `notes` field so the category name doesn't imply
   capability that doesn't exist yet.
4. **Category semantics ambiguity — additive vs. replacing.** The ticket's
   Scope bullet says "Extend queries.json with the new category values"
   (additive phrasing), and the source doc's 6 conceptual groups do not obviously
   subsume the existing `semantic`/`exact-term`/`cross-section`/`edge-case`
   categories 1:1 (e.g., `doc/exact-id` looks like a probable rename/superset
   of `exact-term`, and `no-result` looks like a rename/superset of
   `edge-case`'s no-expected-id entries). I did not find an explicit ruling in
   any prior artifact on whether the final category set is 11 values (4 old +
   7 new, kept side by side) or a smaller consolidated set where `doc/exact-id`
   absorbs `exact-term` and `no-result` absorbs the empty-expected subset of
   `edge-case`. This changes `test_category_balance`'s exact shape and should
   be a named decision in `plan.md`, not inferred silently during
   implementation.
5. **`context_budget` and `source_lifecycle_assumption` have no prior schema.**
   Neither field exists anywhere in the repo today (grepped `docs/parity_ledger/`
   and all prior stored artifacts — no hits). The source doc only names them at
   the concept level ("source lifecycle assumptions," "a context budget"); it
   does not define units (tokens? chunks? a category enum like
   active/superseded/archived?) or an authoritative source. This is a Plan-
   phase judgment call, deliberately scoped "minimally" per the ticket's Out of
   Scope note ("Does not build new doc frontmatter status/authority
   infrastructure beyond what's minimally needed").

## Anti-Drift Hazards

- **Do not "fix" the doc_id staleness by changing `knowledge_search.py`'s
  section-derivation logic.** That would be an indexer behavior change
  (affecting `search_docs`/MCP/HTTP consumers) hiding inside a
  fixtures-and-tests ticket whose Related Code Areas explicitly list only
  `tools/eval/queries.json`, `tools/eval_search.py`,
  `tests/tools/test_eval_search.py`. The correct fix is to correct the fixture
  strings to match the indexer's actual (current) behavior, not the other way
  around — matching the precedent set by `TCK-20260711-EVAL-SEARCH-DOCID-
  ANCHOR-FIX`'s Out-of-Scope reasoning ("chunk-level doc_id is intentional and
  load-bearing elsewhere").
- **Do not silently change the 0.80 Recall@5 threshold value or wire eval-search
  into CI** — both are explicit Out-of-Scope items on the ticket itself.
- **Do not let the new metric(s) require semantic-search dependencies beyond
  what's already optional** (`sentence-transformers`, `sqlite-vec`,
  `rank_bm25`) — `eval_search.py` currently has no hard dependency on those
  (it shells out to `knowledge_search.py`, which degrades gracefully per its
  own `_check_deps()` pattern). A new authority/freshness metric that reads
  doc frontmatter should do so directly (e.g. `yaml`/regex over the docs
  corpus) rather than adding a new mandatory dependency.
- **Do not conflate this ticket's `no-result` category with a CI/production
  gate change.** The source doc frames "known difficult/no-result cases" as
  fixture content only; nothing in this ticket authorizes new mandatory
  workflow behavior (the epic ticket's own Out-of-Scope list bars exactly
  that).
- **Preserve the exact existing regression tests' pass/fail semantics** —
  particularly `TestEvaluateExitCode` (L141-188), which pins `evaluate()`'s
  exit-code contract against `_run_query` monkeypatches; changing `total`'s
  computation (Risk #2 above) must keep those tests' literal expected exit
  codes intact (they use fully-populated `expected_doc_ids` lists with no
  empty-expected entries, so they are insulated from a denominator fix — verify
  this holds after the change, don't assume).
