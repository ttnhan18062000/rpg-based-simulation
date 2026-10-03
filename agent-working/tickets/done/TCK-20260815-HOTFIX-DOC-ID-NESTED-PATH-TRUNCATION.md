---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION
phase: done
date: 2026-08-15
tags: [ai, bug]
---

# TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION

## Title
Fix doc_id truncation of nested docs/ paths beyond the first subdirectory; rebuild the search
index

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tools/knowledge_search.py`'s corpus builder derives each indexed document's `doc_id` as
`f"{section}/{stem}"`, where `section = rel_parts[0]` — only the immediate subdirectory of
`docs/`, discarding any deeper nesting. A doc at `docs/engine/contracts/knowledge_gateway_mcp/
measurement_baseline_contract.md` gets `doc_id = "engine/measurement_baseline_contract"`, silently
dropping `contracts/knowledge_gateway_mcp/`. This creates two real problems:

1. **Collision risk**: two distinct docs sharing a top-level directory and stem but differing only
   in deeper nesting (e.g. `docs/engine/a/foo.md` and `docs/engine/b/foo.md`) both resolve to
   `doc_id = "engine/foo"` — the index cannot distinguish them.
2. **Confirmed real-world impact**: `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` (knowledge-
   gateway-mcp-phase1 epic) traced part of its honest §4.3 no-regression-recall threshold FAIL to
   this exact truncation — Phase 0's baseline recorded `doc_id`-based `sources_recalled` values
   that cannot be matched against Phase 1's full-path-based `evidence_id` values for any doc
   nested more than one level under `docs/`, independent of the recall miss's other (architectural,
   expected) cause.

`doc_id` is core search-index infrastructure, not specific to the Knowledge Gateway epic — it is
consumed by `tools/context_packet_assembler.py` (`source_id=result.doc_id`), `tools/
search_server.py` (index lookup via `doc_ids.index(doc_id)`), and `tools/search_mcp.py` (response
`doc_id`/title derivation), in addition to the BM25/vector index itself
(`knowledge-index/knowledge.db`).

## Scope
- **Investigate (mandatory before Plan):** scan the real corpus for actual `doc_id` collisions
  under the current truncated scheme (not just the theoretical risk) — quantify how many, if any,
  currently exist.
- Fix `tools/knowledge_search.py`'s `doc_id` derivation to preserve the full nested path under
  `docs/` (e.g. derive from the already-computed `path_str` rather than `section`/`stem` alone),
  eliminating the collision risk and the truncation.
- Rebuild `knowledge-index/knowledge.db` via `make knowledge-index-update` (or the appropriate
  full-rebuild target if an ID-format change requires a non-incremental rebuild — Investigate must
  check whether the incremental build path handles an ID-scheme change correctly, given its
  content-hash-based cache-reuse logic, or whether a full rebuild is required).
- Verify the 3 known downstream consumers (`context_packet_assembler.py`, `search_server.py`,
  `search_mcp.py`) continue to function correctly against the new `doc_id` shape — run their
  existing test suites.
- Verify `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`'s normalization function still
  produces correct results against the corrected `doc_id` format (it may need updating once
  `doc_id` itself is fixed — check whether the fix changes what normalization is still needed).

## Out of Scope
- Re-running `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s full baseline comparison or updating
  its committed fixture/results doc — that ticket is DONE and its historical result stands as
  recorded; this hotfix does not retroactively rewrite it. A future ticket may choose to re-run the
  comparison with the corrected index, but that is not this ticket's job.
- The other, architectural cause of the same §4.3 recall FAIL (single-provider routing per §8) —
  unrelated to this bug, not addressed here.
- Any change to the Knowledge Gateway MCP epic's own code (`tools/knowledge_gateway_*.py`) —
  those files remain untouched; this ticket fixes the underlying shared search-index infrastructure
  those modules read from.

## Acceptance Criteria
- [x] `investigation.md` reports the real, quantified collision count found in the actual corpus
      under the current truncated scheme (not an estimate).
- [x] `doc_id` is derived from the full nested relative path under `docs/`, verified against a real
      multi-level-nested doc (e.g. one under `docs/engine/contracts/knowledge_gateway_mcp/`).
- [x] `knowledge-index/knowledge.db` is rebuilt and confirmed to contain the corrected `doc_id`
      values for a real sample of nested docs.
- [x] `context_packet_assembler.py`, `search_server.py`, and `search_mcp.py`'s own existing test
      suites all still pass against the corrected `doc_id` format.
- [ ] No regression to `tools/eval_search.py`'s recall/MRR metrics (the same metric family
      `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX` — a prior doc_id-anchor-related fix — protected;
      re-run `make eval-search` and compare against its pre-fix baseline). **Left unchecked
      deliberately**: real post-fix numbers are Recall@5 0.50 (baseline 0.53, -0.03), Recall@10
      0.74 (baseline 0.65, +0.09), MRR@10 0.28 (baseline 0.33, -0.05). Two of three metrics moved
      down. Per plan.md Step 5, a hit/miss status change on the 9 queries.json entries corrected in
      Step 3 is expected/acceptable (not a regression by itself) — most of those 9 queries are now
      misses at top-5 under the corrected scheme, which plausibly explains the Recall@5/MRR@10 dip.
      However the documented baseline (0.53/0.65/0.33) is from a much earlier ticket
      (`TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`) measured against a materially smaller corpus
      (this run indexed 7382 documents; the corpus has grown substantially since), so the
      before/after comparison is confounded by corpus growth and is not a clean isolation of this
      fix's effect alone. Both before and after remain below the pre-existing 0.80 pass threshold
      (a known, out-of-scope condition per investigation.md). Reporting honestly rather than
      checking this box: a small, partially-explained, partially-confounded numeric regression on
      2 of 3 metrics did occur.

## Related Tickets
- TCK-20260815-KGMCP-P1-BASELINE-COMPARISON (DONE; discovered and diagnosed this bug as one of
  two real causes behind its honest §4.3 recall threshold FAIL)
- TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX (DONE; a prior, related doc_id/anchor correctness fix
  in the same search-index subsystem — read for precedent before touching this code again)
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (DONE; original corpus-builder/doc_id design this ticket
  corrects)
- TCK-20260612-LOCAL-CTX-MCP (DONE; built `tools/search_mcp.py`, one of the 3 downstream
  consumers to verify)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (the results doc
  that surfaced this bug)

## Related Stored Artifacts
None yet (hotfix — no staging artifacts).

## Related Code Areas
- `tools/knowledge_search.py` (the `doc_id` derivation to fix, around line 293)
- `tools/context_packet_assembler.py`, `tools/search_server.py`, `tools/search_mcp.py` (downstream
  consumers to verify)
- `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` (normalization logic that may need
  updating once the underlying format is fixed)
- `knowledge-index/knowledge.db` (index to rebuild)

## Assumptions / Open Questions
- Whether the incremental index-build path (`make knowledge-index-update`) correctly regenerates
  every doc's `doc_id` on an ID-scheme change, or whether its content-hash-based cache-reuse logic
  would incorrectly skip re-deriving `doc_id` for unchanged file content — Investigate must check
  this before Plan decides whether a full rebuild is required.

## Implementation Notes
Followed `staging_artifacts/TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION/plan.md`'s 6 steps
in order (Step 6 deferred per this ticket's explicit instruction).

- **Step 1**: `tools/knowledge_search.py::_collect_docs_chunks()` (~L279–293) — removed the
  `section`/`stem`-truncated `doc_id = f"{section}/{stem}" if section else stem` and replaced with
  `doc_id = rel.with_suffix("").as_posix()` (the full relative path under `docs_root`, minus
  `.md`). `section` is still computed the same way immediately after, for the unrelated
  `"section"` chunk-metadata field (unchanged semantics). Removed the now-dead `stem = md_file.stem`
  local (confirmed unused elsewhere in the function). Updated the function's docstring (`id`/
  `doc_id` key descriptions) to state the new full-path semantics instead of the stale
  `"{section}/{stem}"` claim. No other writer to `doc_id`/`id` exists in the file (confirmed by
  reading the full function body) — no other change needed.
- **Step 2**: Ran `make knowledge-index` (full rebuild, not `--incremental`) — `cmd_build()`
  unconditionally `unlink()`s and rewrites `knowledge.db`/`bm25.pkl` from a fresh corpus pass.
  Result: 7382 documents embedded (1419 ticket summaries, 973 investigation files, 1393 working
  log rows, 3597 docs chunks). Verified via direct SQLite query that
  `docs/engine/contracts/knowledge_gateway_mcp/*.md` files now produce full-path `doc_id`s (e.g.
  `engine/contracts/knowledge_gateway_mcp/cache_migration_plan`) and that the old truncated form
  `engine/measurement_baseline_contract` no longer exists in `knowledge_docs`. 5121 distinct
  `doc_id` values across all rows post-rebuild.
- **Step 3**: Updated all 9 affected `expected_doc_ids` array entries across 8 query objects in
  `tools/eval/queries.json`, applying the exact 6-string mapping from plan.md (`engine/X` →
  `engine/contracts/X` for `replay_contract`, `scheduler_contract`, `infrastructure_overview`
  (2 occurrences), `observability_contract` (2 occurrences), `supported_gameplay_surface`,
  `worker_contract`). Verified via grep that no old-scheme string remains and the file is still
  valid JSON with 61 queries total (unchanged count).
- **Step 4**: Ran the full regression suite from test_plan.md. No source code changes to
  `context_packet_assembler.py`, `search_server.py`, `search_mcp.py`,
  `kgmcp_phase1_gateway_runner.py`, or `hybrid_retrieval.py` — all confirmed opaque/insulated
  consumers per investigation.md. Added the new `_derive_title()` nesting-agnosticism guard test
  to both `tests/tools/test_search_server.py::TestDeriveTitle` and
  `tests/tools/test_search_mcp.py` (new `TestDeriveTitle` class).
- Added all 7 new tests from test_plan.md to `tests/tools/test_knowledge_search.py` (tests 1–4, in
  `TestDocsChunkExtraction`; test 6, `test_build_incremental_noop_leaves_stale_doc_id_documented`,
  in `TestManifestHelpers`), `tests/tools/test_search_server.py` (test 5a),
  `tests/tools/test_search_mcp.py` (test 5b), and `tests/tools/test_eval_search.py` (test 7, new
  `TestQueriesFixtureIntegrity` class).
- **Deviation** (recorded in plan.md's new Deviations section): `tests/tools/
  test_eval_search.py::_KNOWN_STALE_DOC_IDS` (added by the earlier `TCK-20260728-EVAL-FIXTURE-
  REPAIR` ticket) contained exactly the 4 full-path strings this ticket's Step 3 reintroduces into
  `queries.json`, asserted via `test_no_stale_expected_doc_ids` to never reappear — because that
  prior ticket had repaired the fixture in the opposite direction to match the (then-live, now-
  fixed) truncated scheme. Removed those 4 entries from `_KNOWN_STALE_DOC_IDS` with an explanatory
  comment; left the 3 unrelated entries (archived/excluded docs) untouched. This was necessary for
  Step 3's own fixture update to not break an existing test, not a scope change.
- **Step 5**: Ran `make eval-search` post-fix. Real numbers: Recall@5 0.50, Recall@10 0.74, MRR@10
  0.28 (61 queries, 54 with expected, 0 zero-result, avg duplicate rate 0.09). Compared honestly
  against investigation.md's documented pre-fix baseline (Recall@5 0.53, Recall@10 0.65, MRR@10
  0.33) — see Acceptance Criteria and Completion Summary for the full honest comparison and the
  corpus-growth confound noted there. Pass threshold (0.80) remains unmet both before and after —
  a known, out-of-scope, pre-existing condition per investigation.md and this ticket's own AC #5
  framing.
- **Step 6 (parity ledger `INFRA-340`)**: explicitly NOT done in this Implement pass, per the
  ticket's own instruction deferring it to this ticket's later Parity phase.

## Test Summary
Scoped suite run twice: once full (including `@pytest.mark.slow` live tests), once with
`-m "not slow"` per the project Testing Rule.

- Full run (`pytest tests/tools/test_knowledge_search.py tests/tools/test_eval_search.py
  tests/tools/test_context_packet_assembler.py tests/tools/test_search_server.py
  tests/tools/test_search_mcp.py tests/tools/test_hybrid_retrieval.py
  tests/tools/test_kgmcp_phase1_baseline_comparison.py
  tests/tools/test_kgmcp_measurement_baseline.py -v`): **242 passed, 6 failed** in 355.89s.
  - 4 of the 6 failures are `@pytest.mark.slow` tests in `test_knowledge_search.py`
    (`TestQueryHappyPath::test_query_completes_within_2_seconds`,
    `TestLiveQueryDocsMechanics::test_build_docs_chunk_count_exceeds_500`,
    `TestLiveQueryDocsMechanics::test_build_completes_under_five_minutes`,
    `TestLiveQueryDocsMechanics::test_existing_ticket_query_still_works`) that hit
    `tests/conftest.py`'s default `--resource-budget medium` 60s per-test wall-clock limit (one
    test's own SLA assertion literally requires up to 5 minutes) — an environment/resource-budget
    mismatch unrelated to this fix, reproducible on unmodified `main` under the same default
    budget.
  - 2 of the 6 failures (`test_search_mcp.py::TestMcpJson::test_command_is_python3`,
    `test_args_point_to_search_mcp`) assert `.mcp.json`'s `knowledge-search` server entry uses
    `command: "python3"` / `args[0]` ending in `search_mcp.py`; the actual entry now points at a
    bash wrapper (`tools/start_search_mcp.sh`), a pre-existing drift from an unrelated, already-
    merged ticket (`TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`, confirmed via `git log -- .mcp.json`).
    `.mcp.json` and `search_mcp.py`'s command wiring were never touched by this ticket (confirmed
    zero diff on `.mcp.json`).
- Re-run with `-m "not slow"`: **218 passed, 2 failed** (the same 2 pre-existing `.mcp.json`
  failures above), 28 deselected, 52.64s. All tests relevant to this ticket's actual change pass.
- New tests added and passing: 4 in `TestDocsChunkExtraction`
  (`test_collect_docs_chunks_preserves_full_nested_path`,
  `test_collect_docs_chunks_no_collision_same_stem_different_subdir`,
  `test_collect_docs_chunks_single_level_path_unchanged`,
  `test_chunk_id_anchor_suffix_unaffected_by_nesting_fix`), 1 in `TestManifestHelpers`
  (`test_build_incremental_noop_leaves_stale_doc_id_documented`), 1 in
  `test_search_server.py::TestDeriveTitle` (`test_agnostic_to_nesting_depth`), 1 new
  `TestDeriveTitle` class in `test_search_mcp.py` (`test_agnostic_to_nesting_depth`), 1 new
  `TestQueriesFixtureIntegrity` class in `test_eval_search.py`
  (`test_expected_doc_ids_match_current_scheme`) — 8 new tests total, matching test_plan.md's 7
  planned tests (test 5 implemented as one case per file, per test_plan.md's own "one case each"
  option).
- `make eval-search` real post-fix numbers: Recall@5 0.50 | Recall@10 0.74 | MRR@10 0.28 |
  Zero-result 0 (61 queries, 54 with expected). See Acceptance Criteria for full honest comparison
  against the documented baseline.

## Files Changed
- `tools/knowledge_search.py` — Step 1 fix (`_collect_docs_chunks()` `doc_id` derivation + docstring)
- `tools/eval/queries.json` — Step 3 fixture update (9 `expected_doc_ids` entries across 8 query objects)
- `tests/tools/test_knowledge_search.py` — 5 new tests (4 in `TestDocsChunkExtraction`, 1 in `TestManifestHelpers`)
- `tests/tools/test_search_server.py` — 1 new test (`TestDeriveTitle::test_agnostic_to_nesting_depth`)
- `tests/tools/test_search_mcp.py` — 1 new test (new `TestDeriveTitle` class)
- `tests/tools/test_eval_search.py` — `_KNOWN_STALE_DOC_IDS` updated (4 entries removed, deviation) + 1 new test class (`TestQueriesFixtureIntegrity`)
- `tickets/inprogress/TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION.md` — this ticket, updated
- `staging_artifacts/TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION/plan.md` — Deviations section appended
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-340` entry, via `write_entry()`, Parity
  phase

Not git-tracked (gitignored, regenerated as an operational side effect, not a source change):
`knowledge-index/knowledge.db`, `knowledge-index/bm25.pkl`, `knowledge-index/manifest.json`
(rebuilt by `make knowledge-index`), `reports/eval_search_20260815.json` (written by
`make eval-search`).

## Completion Summary
Fixed `tools/knowledge_search.py::_collect_docs_chunks()`'s `doc_id` derivation to preserve the
full nested relative path under `docs/` instead of truncating to `{immediate-subdirectory}/{stem}`,
eliminating a real (if not-yet-collided) collision risk and the confirmed cross-index identity
mismatch that caused part of `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s §4.3 recall FAIL. Ran a
full (non-incremental) index rebuild — `make knowledge-index` — since the incremental path's
mtime-only change detection would have silently no-op'd on this pure code-derivation change,
verified directly against the rebuilt `knowledge.db` that nested docs now carry full-path `doc_id`s.
Updated the 9 stale `tools/eval/queries.json` fixture entries this fix invalidated, and (as a
necessary follow-through, not a scope change) removed 4 now-obsolete entries from
`test_eval_search.py`'s `_KNOWN_STALE_DOC_IDS` guard set that a prior, opposite-direction fixture
repair had added. All 3 named downstream consumers plus the 2 additional real consumers found in
investigation required zero source changes — confirmed via their full test suites
(218 passed / 2 pre-existing, unrelated `.mcp.json`-wiring failures, with `-m "not slow"`; the 4
additional failures seen in the unfiltered run are `@pytest.mark.slow` tests hitting the default
60s resource budget, reproducible on unmodified `main`). Added all 7 test_plan.md-specified new
tests plus one deviation-driven fixture-guard update. Ran `make eval-search` post-fix: real numbers
are Recall@5 0.50, Recall@10 0.74, MRR@10 0.28 (baseline: 0.53 / 0.65 / 0.33) — Recall@10 improved,
Recall@5 and MRR@10 dipped slightly. Document-Update confirmed no doc needed a change. Architecture-
Verify independently confirmed, via direct inspection of the real per-query eval report and the
rebuilt SQLite index (not just plan-narrative trust), that this dip is a benign, correctly-diagnosed
consequence: (a) `doc_id`'s only live ranking input, `title_boost`, is a lexical superset match that
can only stay the same or increase under the fix, never decrease, ruling it out as the dip's cause;
(b) 4 of the 9 corrected queries miss even at top-10 in the real per-query data, with the actual
retrieved top-10 dominated by tickets dated well after the original 2026-07-11 baseline — direct,
concrete evidence that corpus growth (not the fix) crowds out the targets; (c) one query
(`replay contract determinism`) hits at rank 7, confirming the identity-matching mechanism itself
works correctly, with the top-5 miss being a ranking-position effect from corpus growth. The
pre-existing 0.80 pass threshold remains unmet both before and after (unrelated, out-of-scope
condition). AC #5 is left unchecked and reported honestly rather than marked satisfied, since a
strict "no regression" reading is not fully met on 2 of 3 metrics — no fixture or threshold was
further adjusted to force a clean pass. Parity added `INFRA-340`, re-verified 6/6 test_path pass,
explicitly worded to certify the fix's correctness without overstating the eval-search result as a
win. Both Document-Update and Parity phases are now complete.
