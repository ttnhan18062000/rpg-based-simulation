---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-DETERMINISTIC-CODE-INDEX
phase: done
date: 2026-07-29
tags: [ai, investigation]
---

# TCK-20260729-DETERMINISTIC-CODE-INDEX

## Title
Deterministic-only code/test symbol index

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extend retrieval to cover code/test symbols using ONLY relationship types the Phase 2 decision doc (docs/ai/code_test_index_boundaries_decision.md) confirmed are deterministic (graphify's AST edges) -- no new semantic/LLM code model. Investigation found the decision doc's per-relation-type claim (that all Part A relation types carry confidence_score=1.0) is factually wrong at the per-edge level: live graphify-out/graph.json shows 'uses' edges 100% INFERRED and 'calls' 42% INFERRED. This ticket must therefore filter admission on each edge's own confidence_score field, not on relation-type name alone, to actually deliver the deterministic-only guarantee the decision doc intended.

## Scope
- Build a new deterministic code/test symbol index module that admits an edge only if its relation type is in the Part A allowlist AND the edge's own confidence_score field == 'EXTRACTED'.
- Explicitly correct for the Phase 2 decision doc's per-relation-type claim, which investigation found factually wrong at the per-edge level (uses=100% INFERRED, calls=42% INFERRED).
- Explicitly decide and state whether to formalize test-scoper's code-to-test mapping into this index, or leave 'associated tests' as a stated/flagged gap -- do not silently leave it empty.
- Index symbols/relationships, not whole-file chunks; bounded-hop neighbor queries only, never inject a full community unless architectural traversal is explicitly requested.
- Pin graphifyy==0.6.7 in requirements given it's currently unpinned and externally pip-installed.

## Out of Scope
- Any Part B (LLM-derived) graphify relation type.
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.

## Acceptance Criteria
- [ ] Index builder admits an edge ONLY if relation is in the Part A allowlist AND the edge's own confidence_score == 'EXTRACTED' (not just relation-name membership); unit test asserts zero INFERRED edges appear in output.
- [ ] Rebuilding the index twice from the same graph.json produces byte-identical output.
- [ ] Each record exposes module/symbol/docstring/owned component/associated-tests, populated from a real mapping OR explicitly flagged as an unresolved gap, never silently empty.
- [ ] Querying by a changed src/ file path returns only bounded-hop neighbors, never a full community, unless the caller explicitly requests architectural traversal.

## Related Tickets
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Related Docs
- docs/ai/code_test_index_boundaries_decision.md
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- graphify-out/graph.json
- graphify-out/GRAPH_REPORT.md
- graphify-out/manifest.json
- tools/knowledge_search.py
- tools/eval_search.py
- tools/eval/queries.json
- tests/tools/test_knowledge_search.py
- tests/tools/test_build_index.py
- tests/tools/test_eval_search.py
- expected: tools/code_test_index.py
- expected: tests/tools/test_code_test_index.py

## Assumptions / Open Questions
- The Phase 2 decision doc's claim that all Part A relation types carry confidence_score=1.0 is contradicted by live graphify-out/graph.json data (uses=100% INFERRED, calls=42% INFERRED); this ticket's filtering must use per-edge confidence, not the doc's per-type claim.
- graph.json also contains 'method' (100% EXTRACTED) and 'inherits' (100% EXTRACTED) relation types not listed in the decision doc's table at all -- real deterministic data outside documented scope, to be included only if planning confirms they fit Part A's intent.
- graphifyy pip package is not currently pinned in requirements; a future upstream upgrade could silently change vocabulary/confidence semantics.
- Several allowlisted relation types have zero occurrences in this repo's graph currently -- not a bug, tests should not assume they'll ever populate.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260729-DETERMINISTIC-CODE-INDEX/plan.md`'s 9 ordered
steps, all Resolved Decisions 1-7 applied as written.

- `tools/code_test_index.py` (new, standalone, no workflow wiring): `PART_A_ALLOWLIST`
  (decision doc's 14 relations + `method`/`inherits`, excluding `references`/`re_exports`);
  `load_graph` / `iter_admitted_edges` (per-edge `relation in PART_A_ALLOWLIST and
  confidence_score == 1.0` filter -- never reads `edge["confidence"]`); `build_records`
  (module/symbol/docstring/owned_component/associated_tests per record, sorted by `id`);
  `_extract_docstring` (real `ast.parse()` of the source file, falls back to `DOCSTRING_GAP`);
  `_associated_tests_for_module` (glob `tests/unit/<module>/**/test_*.py`, falls back to
  `ASSOCIATED_TESTS_GAP`); `write_index`/`build_index` (deterministic
  `json.dump(sort_keys=True, ensure_ascii=True, indent=2)`, no timestamps/UUIDs);
  `_build_adjacency`/`query_by_path` (bounded-hop default-2 BFS, `architectural_traversal=True`
  opt-in full-community mode); `build`/`query` argparse CLI subcommands.
- Confirmed `graphify-out/graph.json`'s top-level edge key is `links` (not ambiguous once
  checked directly) and that graph nodes carry no docstring field (`node["community"]` is the
  only pre-computed per-node grouping value used, per Resolved Decision 7).
- `requirements-knowledge.txt`: added `graphifyy==0.8.39` pin with a comment explaining it
  supersedes the decision doc's stale `0.6.7` evidence (Resolved Decision 2); not added to
  `pyproject.toml` (standalone CLI tool, not a Python import dependency).
- `docs/parity_ledger/infrastructure.yaml`: appended `INFRA-293` following the exact
  `INFRA-281`-`INFRA-292` agent-tooling precedent shape, citing `tools/code_test_index.py`'s
  actual line ranges as `v2_evidence`.
- `tests/tools/test_code_test_index.py` (new, 11 tests, all passing): admission-filter tests
  (including the AC1-required "zero INFERRED edges in output" assertion and the
  confidence-label-vs-confidence_score-disagreement regression guard), record-construction
  tests (real docstring/owned_component mapping, explicit gap sentinels, never silently empty),
  a byte-identical-rebuild test (AC2, frozen fixture copy, not a live `graphify update .`),
  bounded-hop vs. architectural-traversal query tests (AC4), a zero-occurrence-relation
  no-crash test, and a `requirements-knowledge.txt` pin-content test. All fixtures are small,
  hand-built graphs -- no assertion on live `graph.json`'s exact edge counts, per test_plan.md.

**Implementation-level clarification not explicitly covered by the plan's Resolved
Decisions** (documented here and in plan.md's Deviations section): the plan's Step 3 text
gives an internally inconsistent example for the `associated_tests` `src/<module>/` directory
segment -- it says to use "the immediate parent directory of the file" but its own worked
example (`src/observability/understanding` from
`src/observability/understanding/domain/quest.py`) is the file's *grandparent* directory, not
its immediate parent (`domain`). Implemented using the single top-level segment after `src/`
(e.g. `observability`), which is what `.claude/agents/test-scoper.md`'s own documented
`src/<module>/` -> `tests/unit/<module>/` convention and Test Directory Map actually specify
(single top-level names only, no nested `understanding` entry), and which is the only
interpretation that correctly locates the real, already-cited
`tests/unit/observability/test_domain_analyzer_registry.py` file for a symbol under
`src/observability/understanding/domain/quest.py`. Verified directly:
`tests/unit/observability/test_domain_analyzer_registry.py` exists; a
`tests/unit/observability/understanding/` directory does not.

## Test Summary

`.venv/bin/python3 -m pytest tests/tools/test_code_test_index.py -v` -- **11 passed, 0 failed.**

`.venv/bin/python3 -m pytest tests/tools/test_knowledge_search.py tests/tools/test_build_index.py tests/tools/test_eval_search.py -q`
-- **151 passed, 5 failed** (630.63s). `TestCorpusScopeGuard::test_collect_corpus_only_reads_defined_roots`
and `TestCorpusScopeGuard::test_collect_corpus_includes_all_three_sources` (re-run in isolation
to confirm) both PASS -- `src/`/`tests/` were not folded into `knowledge_search.py`'s corpus.
The 5 failures are all in `TestQueryHappyPath`/`TestLiveQueryDocsMechanics` and are **pre-existing
staleness of the checked-in `knowledge-index/knowledge.db` artifact** (`knowledge-index/*` last
built 2026-07-28 17:24, before several same-day ticket-closing commits landed content these
live-query tests expect to find, e.g. "No ticket/investigation result in: [...]" and a docs
chunk-count assertion). This live SQLite DB is a frozen, pre-built artifact that cannot be
affected by any file this ticket touches (`tools/code_test_index.py`,
`tests/tools/test_code_test_index.py`, `requirements-knowledge.txt`,
`docs/parity_ledger/infrastructure.yaml` -- none are inputs to
`tools/knowledge_search.py`'s corpus build, and the DB predates this ticket's work entirely).
Rebuilding `knowledge-index/knowledge.db` (`make knowledge-index-update`, several minutes) is
out of this ticket's scope -- not required by any of its 4 acceptance criteria and not touched
by its plan. `tests/tools/test_build_index.py` and `tests/tools/test_eval_search.py` had zero
failures.

`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` --
loads validly, 298 entries, last id `INFRA-293`.

`graphify update .` run after adding `tools/code_test_index.py` and
`tests/tools/test_code_test_index.py` -- graph rebuilt (27913 nodes, 87051 edges, 1022
communities), AST-only, no API cost.

## Files Changed

- `tools/code_test_index.py` (new)
- `tests/tools/test_code_test_index.py` (new)
- `requirements-knowledge.txt` (added `graphifyy==0.8.39` pin)
- `docs/parity_ledger/infrastructure.yaml` (added `INFRA-293`)

## Completion Summary

Built `tools/code_test_index.py`, a standalone module that indexes `graphify-out/graph.json`
into deterministic code/test symbol records, admitting an edge only if its relation is in the
Part A allowlist AND its own `confidence_score` field equals `1.0` -- correcting the Phase 2
decision doc's per-relation-type claim, which live-graph investigation proved false at the
per-edge level (`uses`=100% INFERRED, `calls`=39.0% INFERRED). Records expose
module/symbol/docstring/owned_component/associated_tests from real mappings (AST-parsed source
docstrings, a `src/<module>/` -> `tests/unit/<module>/` glob) or explicit gap sentinels, never
silently empty. Rebuild is byte-identical from a frozen `graph.json` (deterministic
`json.dump`). Querying by a changed `src/` path defaults to bounded-hop (2-hop) neighbors;
full-community traversal is opt-in only via `architectural_traversal=True`. Pinned
`graphifyy==0.8.39` in `requirements-knowledge.txt` (the actually-installed version, not the
ticket's stale `0.6.7` figure) and added `INFRA-293` to the parity ledger. All 4 acceptance
criteria met; 11 new tests pass; the module is standalone with no workflow wiring.
