---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-DETERMINISTIC-CODE-INDEX
artifact_type: plan
tags: [ai, investigation]
---

# Implementation Plan — TCK-20260729-DETERMINISTIC-CODE-INDEX

## Summary

Build `tools/code_test_index.py`, a new standalone module that indexes `graphify-out/graph.json`
into deterministic symbol records. The crux of this ticket — verified by investigation against
the live 86,909-edge graph — is that a relation-type-name-only filter would wrongly admit 45.1%
of "Part A" edges as deterministic (100% of `uses`, 39% of `calls`). The module therefore admits
an edge only if **both** (a) its `relation` is in the working Part A allowlist and (b) its own
`confidence_score` field equals the float `1.0` — never the string `confidence` field, which is
proven to disagree with `confidence_score` on 5 real `inherits` edges. Records expose
module/symbol/docstring/owned-component/associated-tests, each populated from a real mapping
(source-file `ast` parsing for docstrings, a minimal `src/<module>/` → `tests/unit/<module>/`
glob for associated tests) or an explicit non-empty gap sentinel — never silently empty. A
bounded-hop (default 2-hop) neighbor query is the default lookup mode by changed `src/` path;
full-community traversal is opt-in only via an explicit flag. The module is standalone, has no
workflow wiring, and does not touch `tools/knowledge_search.py`'s corpus or scope guard.

## Resolved Decisions

These four items were flagged as open questions by investigation.md. Per CLAUDE.md's
Clarification Rule ("ask only if it changes outcomes... otherwise follow existing patterns") and
the instruction accompanying this planning task, each is resolved here with a stated rationale
rather than left as a blocking "Unresolved Questions" item.

1. **AC48 field conflation (`confidence_score` float vs. `confidence` string).** The ticket's AC
   text literally says "the edge's own `confidence_score` field == `'EXTRACTED'`", which is a
   type mismatch (`confidence_score` is a float; `'EXTRACTED'` is a value of the separate
   `confidence` string field). **Resolved: admit iff `edge["confidence_score"] == 1.0`** (exact
   float equality against the literal value the decision doc's own §1.2 construction rule assigns
   to `EXTRACTED`). The `confidence` string field is read nowhere in the admission path. This is
   stricter and provably correct — it is the only field that catches the 5 real `inherits` edges
   where `confidence="EXTRACTED"` but `confidence_score=0.5`.

2. **`graphifyy` version pin.** Ticket Scope says pin `==0.6.7`; investigation confirms the
   installed and actually-graph-producing version is `0.8.39`, and neither `requirements.txt` nor
   `requirements-knowledge.txt` pins `graphifyy` at all today. **Resolved: pin
   `graphifyy==0.8.39`** (the actually-installed, actually-graph-producing version) in
   `requirements-knowledge.txt`, not `0.6.7`. The ticket's `0.6.7` figure is stale — inherited
   from the Phase 2 decision doc's evidence date, not re-verified before this ticket was written
   — and pinning it would assert a version that was never installed and is not known to reproduce
   the current `graph.json`. This choice is recorded here and in the module docstring (Step 8),
   not silently substituted.

3. **AC3 code-to-test mapping (`associated_tests`).** The decision doc deferred formalizing
   test-naming linkage to "a future ticket if Phase 2+ retrieval work needs it as data"; this
   ticket's own Scope explicitly asks to decide now. **Resolved: implement the minimal
   glob-based mapping** (`src/<module>/` → `tests/unit/<module>/**/test_*.py`, mirroring
   `.claude/agents/test-scoper.md`'s documented convention) rather than flag-only. Where the glob
   finds no matches (non-standard test layout, symbol outside `src/`, etc.) the field is set to an
   explicit sentinel string, never `[]`/`None`/`""`. Remaining non-standard layouts are a
   documented gap in the sentinel's own text and in the module docstring, not silently absorbed.

4. **`references` / `re_exports` inclusion.** Investigation found these two relation types are
   100% deterministic in the live graph but are not mentioned anywhere in the ticket text, only
   discovered during investigation, and are not in the decision doc's documented Part A table.
   **Resolved: do NOT add them to the allowlist.** The ticket's own Scope says "admit only if
   relation type is in the Part A allowlist" (i.e., the documented table), and Out of Scope
   forbids force-resolving Open Decisions 5/6 — expanding the allowlist with a type the ticket
   never asked about is the same class of unilateral scope-widening. This omission is recorded
   explicitly here and in the module docstring (Step 8) as a noted, deliberate gap, not a silent
   oversight — a future ticket can decide to add them.

5. **`method` / `inherits` inclusion (additional decision, raised by the ticket's own Assumptions
   section, not by the 4 items above).** Unlike `references`/`re_exports`, the ticket's own
   Assumptions section explicitly invites this decision: "to be included only if planning confirms
   they fit Part A's intent." **Resolved: INCLUDE `method` and `inherits`** in the working
   allowlist. Rationale: both are structurally AST-derived, non-LLM relations — the same category
   Part A's intent targets — merely absent from the decision doc's table because that table was
   evidenced against the older `graphifyy==0.6.7`. Critically, including them does not weaken the
   determinism guarantee: the per-edge `confidence_score==1.0` filter (Decision 1) still excludes
   the 5 non-conforming `inherits` edges even though the relation type itself is allowlisted — the
   whole point of per-edge filtering is that allowlist membership alone is never sufficient. This
   is the one case in this plan where the working allowlist diverges from the decision doc's
   literal table; it is recorded here and in the module docstring, and is distinct from Decision 4
   precisely because the ticket itself asked for this call to be made, while it never asked about
   `references`/`re_exports`.

6. **`docstring` field source (not one of investigation's flagged open questions, discovered
   during planning verification).** Direct inspection of `graphify-out/graph.json` confirms graph
   nodes carry **no** docstring field at all (`node.metadata` only ever contains
   `language`/`kind`/`mcp_kind` keys in this repo's data). **Resolved: extract docstrings by
   parsing the live `.py` source file** named in `source_file` with Python's `ast` module,
   matching the `FunctionDef`/`AsyncFunctionDef`/`ClassDef` node whose name equals the graph
   node's `label` (disambiguated by proximity to `source_location`'s line number if multiple
   matches), and calling `ast.get_docstring()`. If the source file is not `.py`, the symbol isn't
   found in the parse, or the file can't be read/parsed, the field is set to the same class of
   explicit gap sentinel used for `associated_tests` (Decision 3) — never silently empty. This is
   a "real mapping" per AC3's language: it reads actual source, not graph metadata that doesn't
   exist.

7. **`owned_component` field source (not one of investigation's flagged open questions, discovered
   during planning verification).** No per-symbol "component" concept exists in `graph.json`
   except the graphify community-detection integer already present on every code node as
   `node["community"]`. **Resolved: `owned_component` = `node["community"]`** (the integer
   community id graphify's own AST-based clustering assigned). This is real, already-computed,
   deterministic data — not fabricated — and is exactly the grouping AC4's bounded-hop-vs-full-
   community distinction already keys off, keeping the two AC3/AC4 concepts consistent with each
   other.

No item here is genuinely undecidable without a human — see "Unresolved Questions" (absent) below.

## Steps

### Step 1 — Module skeleton, allowlist constant, and per-edge admission filter
**Files:** `tools/code_test_index.py` (new), `tests/tools/test_code_test_index.py` (new)
**Change:**
- Create `tools/code_test_index.py` with a module docstring stating this module's scope (indexes
  `graphify-out/graph.json` into deterministic symbol records; Part A relations only; no LLM/Part
  B data; standalone, no workflow wiring — see Step 8 for the full docstring content).
- `PART_A_ALLOWLIST: frozenset[str]` = the decision doc's 14 documented Part A relation names
  (`imports`, `imports_from`, `calls`, `contains`, `defines`, `uses`, `uses_static_prop`,
  `references_constant`, `bound_to`, `listened_by`, `includes`, `uses_component`, `binds_method`,
  `rationale_for`) **plus** `method` and `inherits` (Resolved Decision 5). Explicitly does NOT
  include `references` or `re_exports` (Resolved Decision 4) — add a one-line comment above the
  constant naming both exclusions and pointing at this plan.
- `load_graph(graph_path: Path) -> dict`: reads and `json.load`s the graph file. No caching, no
  mutation of the input.
- `iter_admitted_edges(graph_data: dict) -> Iterator[dict]`: yields each edge in
  `graph_data["links"]` (or whatever the top-level edge key is — confirm exact key name against
  `graphify-out/graph.json` before writing; investigation calls it `links`/edges interchangeably)
  where `edge["relation"] in PART_A_ALLOWLIST` **and** `edge.get("confidence_score") == 1.0`
  (exact equality, Resolved Decision 1). Never reads `edge["confidence"]` in the admission
  decision.
**Do NOT touch:** `tools/knowledge_search.py` (any function or its corpus), `tools/graphify_to_html.py`,
`graphify-out/graph.json` itself (read-only), any file inside the installed `graphifyy` package.
**Verify:** `test_admits_part_a_relation_with_confidence_score_1_0`,
`test_rejects_inferred_edge_despite_allowlisted_relation_name`,
`test_rejects_edge_where_confidence_label_and_confidence_score_disagree`,
`test_zero_occurrence_allowlist_relations_do_not_crash_builder`.

### Step 2 — Symbol record construction (module/symbol/docstring/owned_component)
**Files:** `tools/code_test_index.py`, `tests/tools/test_code_test_index.py`
**Change:**
- `_module_from_source_file(source_file: str) -> str`: convert a `source_file` path (e.g.
  `src/core/state.py`) into a dotted module path (`src.core.state`) via simple path-segment
  join, no filesystem access.
- `_extract_docstring(source_file: str, source_location: str, symbol_label: str, repo_root: Path)
  -> str`: implements Resolved Decision 6 — parse the `.py` file with `ast.parse`, walk
  `ast.walk()` for `FunctionDef`/`AsyncFunctionDef`/`ClassDef` nodes matching `node.name ==
  symbol_label`, pick the match closest to the `source_location` line number if more than one,
  return `ast.get_docstring(match) or DOCSTRING_GAP` where `DOCSTRING_GAP` is an explicit sentinel
  constant (e.g. `"UNRESOLVED_GAP:no_docstring_found"`). Any `OSError`/`SyntaxError`/non-`.py`
  file also returns `DOCSTRING_GAP`. Never returns `None`/`""` on failure.
- `build_records(graph_data: dict, admitted_edges: list[dict], repo_root: Path) -> list[dict]`:
  collect every node id referenced as `source` or `target` by an admitted edge, look up each
  node in `graph_data["nodes"]`, and emit one record per unique node id:
  `{"id": ..., "module": _module_from_source_file(...), "symbol": node["label"], "docstring":
  _extract_docstring(...), "owned_component": node["community"], "associated_tests": <Step 3>}`.
  Sort the returned list by `id` (stable, deterministic ordering — feeds Step 4's byte-identical
  requirement).
**Do NOT touch:** any node/edge shape in `graph.json`; do not add new keys to the source graph
file; do not attempt community-*label* resolution (only the raw integer id, per Resolved Decision
7 — resolving a human-readable community name is out of scope, not asked for by any AC).
**Verify:** `test_docstring_and_owned_component_populated_from_real_mapping`.

### Step 3 — Associated-tests mapping with explicit gap sentinel
**Files:** `tools/code_test_index.py`, `tests/tools/test_code_test_index.py`
**Change:**
- `ASSOCIATED_TESTS_GAP: str = "UNRESOLVED_GAP:no_test_mapping_found"` — module-level sentinel
  constant, distinguishable from a real empty match (a real "no tests found after searching" case
  still uses this same sentinel, since AC3 requires a non-silent gap flag either way).
- `_associated_tests_for_module(source_file: str, repo_root: Path) -> list[str] | str`: derive the
  `src/<module>/` directory segment from `source_file` (e.g. `src/observability/understanding` from
  `src/observability/understanding/domain/quest.py` — use the immediate parent directory of the
  file, mirroring `.claude/agents/test-scoper.md`'s `src/<module>/` → `tests/unit/<module>/`
  convention), then glob `tests/unit/<module>/**/test_*.py` under `repo_root`. If the glob returns
  one or more matches, return the sorted list of paths (relative to `repo_root`, POSIX separators
  for determinism across platforms). If zero matches, return `ASSOCIATED_TESTS_GAP`.
- Wire this into `build_records` from Step 2 for the `associated_tests` field.
**Do NOT touch:** `.claude/agents/test-scoper.md` (read-only reference for the naming convention;
this ticket does not modify the agent definition itself). Do not attempt to handle non-standard
test layouts beyond the single `src/<module>/` → `tests/unit/<module>/` convention — anything else
falls through to `ASSOCIATED_TESTS_GAP` by design (Resolved Decision 3's stated gap).
**Verify:** `test_record_exposes_required_fields_or_explicit_gap_flag`.

### Step 4 — Deterministic serialization and byte-identical rebuild
**Files:** `tools/code_test_index.py`, `tests/tools/test_code_test_index.py`
**Change:**
- `write_index(records: list[dict], output_path: Path) -> None`: `json.dump(records, f,
  sort_keys=True, ensure_ascii=True, indent=2)` — no wall-clock timestamps, random UUIDs, or
  hash-of-current-time fields anywhere in the output. If any provenance/build metadata is
  included (e.g. `graph_data.get("built_at_commit")`), it must come from the input `graph.json`
  itself (already-fixed per input), never `datetime.now()`.
- `build_index(graph_path: Path, output_path: Path | None, repo_root: Path) -> list[dict]`:
  orchestrates `load_graph` → `iter_admitted_edges` → `build_records`, optionally calls
  `write_index` if `output_path` is given, and always returns the in-memory records list.
- CLI entrypoint: `if __name__ == "__main__":` with `argparse` subcommand `build --graph PATH
  --output PATH [--repo-root PATH]`.
**Do NOT touch:** any existing CLI tool's argument parser (`tools/knowledge_search.py`,
`tools/agent-monitoring/build_index.py`, `tools/eval_search.py`) — this is a wholly separate
entrypoint, not an extension of an existing one.
**Verify:** `test_rebuild_is_byte_identical` (build twice from a frozen fixture `graph.json` copy,
hash- or byte-compare the two output files).

### Step 5 — Bounded-hop neighbor query with opt-in full-community traversal
**Files:** `tools/code_test_index.py`, `tests/tools/test_code_test_index.py`
**Change:**
- `_build_adjacency(admitted_edges: list[dict]) -> dict[str, set[str]]`: undirected adjacency map
  built only from the already-admitted (deterministic) edge set from Step 1 — `source`↔`target`
  both directions, since "neighbor" for a code-navigation query is not inherently directional.
- `query_by_path(records: list[dict], admitted_edges: list[dict], graph_data: dict, src_path: str,
  *, hops: int = 2, architectural_traversal: bool = False) -> list[dict]`:
  - Find seed node ids whose `source_file == src_path`.
  - Default (`architectural_traversal=False`): BFS over `_build_adjacency(...)` from the seed
    node ids up to `hops` hops (default 2); return the subset of `records` whose `id` was reached.
  - Opt-in (`architectural_traversal=True`): return every record whose `owned_component` equals
    any seed node's `community` value — i.e. the full community, only when explicitly requested.
- CLI subcommand: `query --graph PATH --path SRC_FILE [--hops N] [--architectural-traversal]`.
**Do NOT touch:** `tools/knowledge_search.py`'s query path, `tools/graphify_to_html.py`'s
rendering logic — this is a new, separate query surface over the new index only.
**Verify:** `test_query_by_changed_path_returns_bounded_hop_neighbors_only`,
`test_architectural_traversal_explicitly_requested_returns_full_community`.

### Step 6 — Pin `graphifyy==0.8.39`
**Files:** `requirements-knowledge.txt`
**Change:** add a `graphifyy==0.8.39` line, with a comment (matching the file's existing comment
style) stating this is the actually-installed version that produced the current `graph.json`, and
that this supersedes an earlier `0.6.7` reference in the Phase 2 decision doc's evidence (Resolved
Decision 2). Do not add `graphifyy` to `pyproject.toml`'s `[project.optional-dependencies]` groups
— it is a standalone CLI tool invoked via `graphify update .`, not a Python import dependency of
this project's installable package, matching `requirements-knowledge.txt`'s own stated scope
("Local agent working-environment tooling only... Not required by the engine, API, or CI test
suite").
**Do NOT touch:** `requirements.txt`, `pyproject.toml`'s `dependencies`/`optional-dependencies`
tables.
**Verify:** `test_pyproject_pins_graphifyy_version`, adapted per test_plan.md's own contingency
note to assert against `requirements-knowledge.txt` instead of `pyproject.toml` (the pin's actual
landing location per this step, not the file test_plan.md speculatively named).

### Step 7 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** append a new entry `id: INFRA-293` (next available id after `INFRA-292`) following
the exact shape of `INFRA-281`–`INFRA-292`: `text` (one paragraph describing the new deterministic
code/test index and its confidence_score-based admission fix), `status: verified`, `priority: P2`,
`legacy_evidence: null`, `v2_evidence: >` citing `tools/code_test_index.py`'s actual function/line
ranges once Steps 1-5 are implemented, `proof_type: regression`, `test_path:
tests/tools/test_code_test_index.py`, `divergence_note: null`, `support_boundary: >` stating
"Agent-orchestration/monitoring-pipeline tooling only — no simulation behavior, Mechanics Bible
chapter, or engine contract governs this index's semantics" (same category as `INFRA-281`–`292`).
**Do NOT touch:** any other entry in `infrastructure.yaml` or any other parity ledger file (no
`docs/mechanics/` chapter governs this — confirmed by investigation's Parity Ledger Overlap
section).
**Verify:** YAML loads validly (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`);
covered structurally by `done-checker`'s frontmatter/ledger checks at Finalize, no dedicated new
pytest test (matches existing `INFRA-281`–`292` precedent, none of which have a ledger-entry-
specific unit test).

### Step 8 — Module-level documentation of scope decisions
**Files:** `tools/code_test_index.py` (module docstring only)
**Change:** finalize the module docstring (started in Step 1) to explicitly state, in prose,
inside the code itself:
- The working allowlist = decision doc's Part A table + `method` + `inherits` (Resolved Decision
  5), explicitly excluding `references`/`re_exports` despite their 100% per-edge determinism
  (Resolved Decision 4), with a one-line pointer to `staging_artifacts/TCK-20260729-DETERMINISTIC-CODE-INDEX/plan.md`
  (or its `stored_artifacts/` location after ticket close) for the full rationale.
- `confidence_score == 1.0` is the sole per-edge admission gate; the `confidence` string field is
  read nowhere in this module (Resolved Decision 1).
- `associated_tests`/`docstring` gap-sentinel semantics and what triggers each (Resolved Decisions
  3 and 6).
- `owned_component` = raw graphify community integer, not a resolved human-readable label
  (Resolved Decision 7).
**Do NOT touch:** `docs/ai/code_test_index_boundaries_decision.md` itself — this ticket documents
its own deviations inline in code, it does not edit the Phase 2 decision doc (editing that doc is
not in this ticket's Scope or ACs).
**Verify:** no dedicated pytest assertion required by test_plan.md; covered by code review /
done-checker doc-consistency posture only.

### Step 9 — Regression pass
**Files:** none changed — verification only.
**Change:** run, in order:
```
.venv/bin/python3 -m pytest tests/tools/test_code_test_index.py -v
.venv/bin/python3 -m pytest tests/tools/test_knowledge_search.py tests/tools/test_build_index.py tests/tools/test_eval_search.py -v
.venv/bin/python3 -m pytest tests/tools/ -k "code_test_index or knowledge_search or build_index or eval_search"
```
Confirm `TestCorpusScopeGuard::test_collect_corpus_only_reads_defined_roots` and
`TestCorpusScopeGuard::test_collect_corpus_includes_all_three_sources` (both in
`tests/tools/test_knowledge_search.py`) are still green — proving `src/`/`tests/` were not folded
into `knowledge_search.py`'s docs/ticket corpus.
**Do NOT touch:** any file under `tests/tools/` other than the new `test_code_test_index.py`.
**Verify:** all listed suites pass with zero failures/errors.

## Scope Guards

Verbatim from the ticket's Out of Scope section:
- Any Part B (LLM-derived) graphify relation type.
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.

Additional guards derived from investigation.md's Anti-Drift Hazards:
- Do not merge this index into `tools/knowledge_search.py`'s corpus, `cmd_build`, or `cmd_query`
  pipeline — they are structurally different data sources with a standing scope-guard test.
- Do not build a relation-type-name-only filter anywhere in the admission path — the entire
  reason this ticket exists is the verified 34,616-edge (45.1%) gap between name-only and
  per-edge `confidence_score==1.0` filtering.
- Do not touch `graphify/extract.py` or any file inside the installed `graphifyy` package — it is
  an external pip dependency, not repo-owned code.
- Do not wire `tools/code_test_index.py` into any `.claude/workflows/*.js` file or any existing
  pipeline/gate — it must remain standalone and manually invocable.
- Do not build hybrid retrieval fusion, cache layers, or `ContextPacket` assembly in this ticket —
  those belong to the three sibling tickets in `tickets/todos/context-retrieval-phase3/`.
- Do not silently leave `associated_tests` or `docstring` empty when a mapping isn't found — both
  must use their explicit gap sentinels (Steps 2, 3).
- Tests must use small, hand-built fixture graphs, never assert on live `graph.json`'s exact edge
  counts, and must use a frozen fixture copy (not a live `graphify update .` invocation) for the
  byte-identical rebuild test (Step 4).

## Dependency Map

- Step 1 (edge filter) — no dependencies. Foundational; all other steps depend on it.
- Step 2 (record construction) — depends on Step 1 (`iter_admitted_edges`).
- Step 3 (associated_tests) — depends on Step 2 (`build_records`'s field slot); independent of
  Steps 4-5.
- Step 4 (serialization / byte-identical rebuild) — depends on Steps 1-3 (needs complete records).
- Step 5 (bounded-hop query) — depends on Step 1 (admitted edges for adjacency) and Step 2
  (records to filter/return); independent of Steps 3-4.
- Step 6 (requirements pin) — fully independent; can be done in parallel with any other step.
- Step 7 (parity ledger entry) — depends on Steps 1-5 being implemented (cites their line ranges
  as evidence); do last among the code-producing steps.
- Step 8 (module docstring finalization) — depends on Steps 1-5's decisions being final in code;
  do after Step 5, before Step 9.
- Step 9 (regression pass) — depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — admits an edge only if relation in Part A allowlist AND confidence_score==1.0; zero INFERRED edges in output | Steps 1, 2 | `test_admits_part_a_relation_with_confidence_score_1_0`, `test_rejects_inferred_edge_despite_allowlisted_relation_name`, `test_rejects_edge_where_confidence_label_and_confidence_score_disagree`, `test_zero_occurrence_allowlist_relations_do_not_crash_builder` |
| AC2 — rebuilding the index twice from the same graph.json produces byte-identical output | Step 4 | `test_rebuild_is_byte_identical` |
| AC3 — each record exposes module/symbol/docstring/owned component/associated-tests, from a real mapping or explicit flagged gap, never silently empty | Steps 2, 3 | `test_record_exposes_required_fields_or_explicit_gap_flag`, `test_docstring_and_owned_component_populated_from_real_mapping` |
| AC4 — querying by a changed src/ path returns only bounded-hop neighbors, never a full community, unless architectural traversal is explicitly requested | Step 5 | `test_query_by_changed_path_returns_bounded_hop_neighbors_only`, `test_architectural_traversal_explicitly_requested_returns_full_community` |
| Scope — pin graphifyy in requirements | Step 6 | `test_pyproject_pins_graphifyy_version` (adapted to `requirements-knowledge.txt`) |

## Anti-Drift Notes

- The single highest-risk regression is reintroducing a relation-type-name-only filter (e.g. "just
  check `relation in PART_A_ALLOWLIST`" without the `confidence_score == 1.0` clause) — this would
  silently readmit the 34,616 wrongly-"deterministic" edges the investigation measured. Steps 1-2
  and their three dedicated tests exist specifically to prevent this.
- `confidence` (string) and `confidence_score` (float) diverge on real data (5 `inherits` edges).
  Any future edit that reads `edge["confidence"] == "EXTRACTED"` instead of
  `edge["confidence_score"] == 1.0` reintroduces a proven bug, not a hypothetical one.
- `graph.json`'s edge collection key must be confirmed exactly (investigation refers to it as
  "`links`/edges interchangeably") before Step 1 is written — a one-line `json.load` + `.keys()`
  check against the real file resolves this without needing a decision.
- The byte-identical rebuild test (Step 4 / AC2) must use a frozen fixture copy of a small
  `graph.json`, never a live `graphify update .` invocation — `graphify` itself is an external,
  versioned, unpinned-until-Step-6 tool and is not guaranteed byte-identical across runs.
- `docstring` and `owned_component` field sourcing (Resolved Decisions 6, 7) were not asked about
  explicitly by the ticket or investigation.md but were required to make AC3 concretely
  implementable; both resolutions reuse already-established repo conventions (parse real source
  via `ast`; reuse graphify's own computed `community` field) rather than inventing new logic, and
  both are documented in Step 8's module docstring so a future reader does not mistake either for
  an oversight.
- `method`/`inherits` inclusion (Resolved Decision 5) intentionally diverges from the decision
  doc's literal Part A table; `references`/`re_exports` exclusion (Resolved Decision 4) does not.
  Do not treat these two as the same kind of decision or "fix" the asymmetry without a new ticket —
  the asymmetry is deliberate (ticket invited one decision, not the other).

## Deviations

Recorded during implementation (see `tickets/inprogress/TCK-20260729-DETERMINISTIC-CODE-INDEX.md`
Implementation Notes for the same writeup):

1. **Step 3's worked example for the `associated_tests` directory segment is internally
   inconsistent, and implementation followed the rule that actually produces a real mapping,
   not the literal example text.** Step 3 says to derive the `src/<module>/` segment by "the
   immediate parent directory of the file," then gives the example
   `src/observability/understanding/domain/quest.py` -> `src/observability/understanding`. The
   immediate parent directory of `quest.py` is actually `src/observability/understanding/domain`
   (one level up), not `src/observability/understanding` (two levels up) — the rule and its own
   example disagree with each other. Implemented instead using the single top-level path segment
   after `src/` (i.e. `observability`), because that is what
   `.claude/agents/test-scoper.md`'s own documented `src/<module>/` -> `tests/unit/<module>/`
   convention and Test Directory Map actually specify (a flat list of top-level directory names,
   no nested `understanding` entry), and it is the only one of the three candidate
   interpretations (immediate parent / stated example / test-scoper's top-level convention) that
   correctly resolves to the real, already-cited `tests/unit/observability/test_domain_analyzer_registry.py`
   file for a symbol under `src/observability/understanding/domain/quest.py`. Verified directly:
   `tests/unit/observability/test_domain_analyzer_registry.py` exists on disk;
   `tests/unit/observability/understanding/` does not. This is a narrow implementation-level
   fix to an internal inconsistency in the plan's own text, not a scope or architecture change —
   `_associated_tests_for_module`'s gap-sentinel behavior, signature, and AC3 semantics are
   otherwise implemented exactly as planned.
