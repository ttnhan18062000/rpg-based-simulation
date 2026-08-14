---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-DETERMINISTIC-CODE-INDEX
artifact_type: test_plan
tags: [ai, investigation]
---

# Test Plan — TCK-20260729-DETERMINISTIC-CODE-INDEX

## Regression Surface

This ticket adds a new module (`tools/code_test_index.py`) and does not modify any
existing file, so the regression surface is about **proving no accidental coupling** into
adjacent tools, not about re-passing pre-existing behavior of touched code.

**Unit — must keep passing unmodified:**
- `tests/tools/test_knowledge_search.py` (all 24 test classes, 1864 lines) — in particular
  `TestCorpusScopeGuard::test_collect_corpus_only_reads_defined_roots` (line 508) and
  `TestCorpusScopeGuard::test_collect_corpus_includes_all_three_sources` (line 536) must
  still pass with `src/`/`tests/` absent from `knowledge_search.py`'s corpus — proves this
  ticket did not fold code-index data into the docs/ticket text corpus.
- `tests/tools/test_build_index.py` (389 lines) — agent-monitoring SQLite index builder;
  unrelated module, but the ticket's Related Docs cite it as a precedent shape, so a
  regression here would indicate an accidental shared-code change.
- `tests/tools/test_eval_search.py` (321 lines) — Recall@5/MRR@10 harness over
  `knowledge_search.py`'s existing index; must be unaffected since this ticket adds no new
  corpus source to that index.

**Integration:** none apply — this ticket ships no workflow wiring (explicitly out of
scope) and no `.claude/workflows/*.js` file is touched.

**Arena-combat:** not applicable — this is agent-orchestration tooling, no simulation code
under `src/` is touched.

## New Tests Required

Target file: `tests/tools/test_code_test_index.py` (does not exist yet — new file).

1. **`test_admits_part_a_relation_with_confidence_score_1_0`**
   Category: unit.
   Verifies: an edge whose `relation` is in the Part A allowlist AND
   `confidence_score == 1.0` is admitted into the index output.
   Location: `tests/tools/test_code_test_index.py`.

2. **`test_rejects_inferred_edge_despite_allowlisted_relation_name`**
   Category: unit (this is AC48's explicit required assertion).
   Verifies: zero `INFERRED` (i.e. `confidence_score != 1.0`) edges appear in the index
   output, even when `relation` is in the Part A allowlist. Use a synthetic fixture with a
   `uses` edge (`confidence_score=0.5`) and a `calls` edge with `confidence_score=0.8` —
   both must be excluded. This directly encodes the ticket's core, verified finding (39.0%
   of `calls` and 100% of `uses` are INFERRED in the live graph) as a permanent regression
   guard, not just a one-time check against today's `graph.json` snapshot.
   Location: `tests/tools/test_code_test_index.py`.

3. **`test_rejects_edge_where_confidence_label_and_confidence_score_disagree`**
   Category: unit (regression-prone edge case found during investigation).
   Verifies: an edge with `confidence="EXTRACTED"` but `confidence_score=0.5` (the exact
   pattern found on 5 real `inherits` edges, e.g.
   `domain_quest_questdomainanalyzer inherits domain_base_domainanalyzer` at
   `src/observability/understanding/domain/quest.py:21`) is excluded — proves filtering
   keys off `confidence_score`, not the `confidence` string label. This is the single
   highest-value new test since it's the one case where relation-name-and-label-only
   filtering would still (incorrectly) pass.
   Location: `tests/tools/test_code_test_index.py`.

4. **`test_rebuild_is_byte_identical`**
   Category: unit / architecture guard (AC2).
   Verifies: running the index builder twice against the same fixed `graph.json` input
   (a frozen fixture copy, not a live `graphify update .` rebuild — see investigation's
   Anti-Drift Hazards) produces byte-identical output (hash comparison of the output
   file(s), or deep-equality of a stable-sorted in-memory structure if output is
   non-file). Guards against non-deterministic iteration order (e.g. unsorted dict/set
   iteration) leaking into the index.
   Location: `tests/tools/test_code_test_index.py`.

5. **`test_record_exposes_required_fields_or_explicit_gap_flag`**
   Category: unit (AC3).
   Verifies: every emitted record has non-empty `module`, `symbol`, and either a populated
   `associated_tests` value OR an explicit sentinel/flag value (never `None`/`[]`/`""`
   silently) — matching the "never silently empty" convention already used for
   `context_packet_contract.md`'s `unrated` sentinel. Assert the specific sentinel value
   chosen by planning is present and distinguishable from a real empty result.
   Location: `tests/tools/test_code_test_index.py`.

6. **`test_docstring_and_owned_component_populated_from_real_mapping`**
   Category: unit (AC3).
   Verifies: for a symbol with a known docstring in a fixture graph, the record's
   `docstring` field is populated from real graph/source data, not a placeholder.
   Location: `tests/tools/test_code_test_index.py`.

7. **`test_query_by_changed_path_returns_bounded_hop_neighbors_only`**
   Category: unit / architecture guard (AC4 — this is the ticket's other core testable
   claim besides the confidence filter).
   Verifies: querying the index by a `src/` file path returns only nodes within N hops
   (per whatever bound the plan fixes, e.g. depth-1 or depth-2) of that file's nodes, and
   that the result set is strictly smaller than that file's full `community` membership
   in `graph.json` (use a `community` with many members in the fixture to prove the guard
   is real, not vacuously true because the community happens to be small).
   Location: `tests/tools/test_code_test_index.py`.

8. **`test_architectural_traversal_explicitly_requested_returns_full_community`**
   Category: unit / architecture guard (AC4, the opt-in path).
   Verifies: the same query with an explicit "architectural traversal" flag/parameter
   set returns the full community, proving the bounded-hop default isn't the only mode
   and the opt-in path exists and is distinguishable from the default.
   Location: `tests/tools/test_code_test_index.py`.

9. **`test_zero_occurrence_allowlist_relations_do_not_crash_builder`**
   Category: unit (regression-prone edge case, per investigation Risk 5).
   Verifies: a fixture `graph.json` with none of `defines`, `uses_static_prop`,
   `references_constant`, `bound_to`, `listened_by`, `includes`, `uses_component`,
   `binds_method` present builds successfully with an empty result for those relation
   types — not an exception or a hard assumption they populate.
   Location: `tests/tools/test_code_test_index.py`.

10. **`test_pyproject_pins_graphifyy_version`** (contingent — only if planning resolves
    Open Question 2 in favor of adding a pin in this ticket)
    Category: unit / architecture guard, mirrors
    `tests/tools/test_knowledge_search.py::TestPyprojectDeps` pattern (line 553).
    Verifies: `requirements.txt` (or wherever the pin lands) contains a `graphifyy==`
    line with a specific version — value should match whatever the plan decides
    (**not** blindly `0.6.7`; see investigation's flagged discrepancy with the
    actually-installed `0.8.39`).
    Location: `tests/tools/test_code_test_index.py` or a small addition to
    `tests/tools/test_knowledge_search.py::TestPyprojectDeps` if the pin lands in the
    same `[knowledge]` optional-deps group.

## Scoped Pytest Commands

```
# New module's own test suite
.venv/bin/python3 -m pytest tests/tools/test_code_test_index.py -v

# Regression surface — existing retrieval tooling tests, scoped to tools/
.venv/bin/python3 -m pytest tests/tools/test_knowledge_search.py tests/tools/test_build_index.py tests/tools/test_eval_search.py -v
```

Never `pytest tests/`. If a shared fixture directory is introduced for `graph.json`
sample data, also run the full `tests/tools/` directory once at the end to catch fixture
name collisions:

```
.venv/bin/python3 -m pytest tests/tools/ -k "code_test_index or knowledge_search or build_index or eval_search"
```

## Anti-Drift Test Guards

- **`TestCorpusScopeGuard` (existing, `tests/tools/test_knowledge_search.py:508`) must
  keep passing unmodified** — this is the guard that would catch this ticket's index
  logic accidentally being merged into `knowledge_search.py`'s docs/ticket corpus.
- **Test #2 and #3 above are permanent regression guards, not one-time verification
  checks** — they encode the investigation's live-data finding (relation-name-only
  filtering silently admits 45.1% non-deterministic edges; label/score can disagree) as
  code that fails loudly if a future edit reverts to relation-name-only filtering.
- **Test #4 (byte-identical rebuild) must use a frozen fixture, never a live `graphify
  update .` invocation** — a flaky test here would either mask real non-determinism in
  the index builder or produce false failures from upstream `graphify` version drift
  (already confirmed to have happened once between the decision doc's 0.6.7 evidence and
  this investigation's live 0.8.39 finding).
- **Test #7/#8 pair guards against the "never inject a full community unless explicitly
  requested" law from the idea doc's Retrieval-layers section** — a regression here would
  silently blow up context budgets for any future consumer (e.g. the
  `CONTEXT-PACKET-ASSEMBLY` sibling ticket) querying this index for an ordinary
  changed-path lookup.
- **No test in this suite should assert on live `graphify-out/graph.json`'s exact edge
  counts** (e.g. "26,984 `uses` edges") — those numbers are a point-in-time snapshot of
  this repo's current code and will drift as the codebase grows. Tests must use small,
  hand-built fixture graphs with a handful of edges chosen to exercise each boundary
  condition (allowlisted+EXTRACTED, allowlisted+INFERRED, non-allowlisted, label/score
  mismatch), not the live 41.9MB `graph.json`.
