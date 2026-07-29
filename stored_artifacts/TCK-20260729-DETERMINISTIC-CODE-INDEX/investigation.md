---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-DETERMINISTIC-CODE-INDEX
artifact_type: investigation
tags: [ai, investigation]
---

# Investigation — TCK-20260729-DETERMINISTIC-CODE-INDEX

## Current Behavior

**No code/test symbol index exists today.** `tools/code_test_index.py` and
`tests/tools/test_code_test_index.py` (the ticket's "expected:" paths) do not exist —
confirmed by directory listing of `tools/` and `tests/tools/`. This is greenfield work,
not a modification.

**`tools/knowledge_search.py`** (1142 lines) is the only existing retrieval tool and it
deliberately does **not** touch `src/`, `tests/`, or `graphify-out/`. Its `_collect_corpus()`
(`tools/knowledge_search.py:128-208`) reads exactly four roots: `tickets/done/TCK-*.md`
(Request Summary only), `stored_artifacts/*/investigation.md` (first 500 chars),
`tickets/working_log.csv`, and `docs/` (heading-aware chunks, excluding `archive/`/`lab/`).
`tests/tools/test_knowledge_search.py::TestCorpusScopeGuard::test_collect_corpus_only_reads_defined_roots`
(line 508) is a standing anti-drift guard asserting `src/engine.py` never leaks into this
corpus. **This ticket's new module must not be folded into `knowledge_search.py`'s corpus
or its scope guard will need updating — it is a structurally separate index over
`graphify-out/graph.json`, not a docs/ticket text corpus.**

**`graphify-out/graph.json`** (41.9MB, `built_at_commit: 96bb229...`, last built Jul 28
16:33) is a NetworkX node-link JSON with top-level keys `nodes` (27,830 entries) and
`links`/edges (86,909 entries). Each node carries `source_file` (e.g.
`src/core/state.py`), `source_location` (e.g. `L1080`), `id`, `label`, `community`. Each
edge carries `relation` (string), `confidence` (string: `EXTRACTED`/`INFERRED`/
`AMBIGUOUS`), `confidence_score` (float), `source`/`target` (node ids), `source_file`,
`source_location`. There is **no existing consumer of `graph.json` in `tools/` other than
`tools/graphify_to_html.py`** (renders it to an HTML viewer; does not filter or index it).

**`graphify-out/manifest.json`** (425KB) maps `{file_path: {mtime, ast_hash,
semantic_hash}}` — used for change detection, not node lookup. Mapping a changed `src/`
file path to its graph nodes must instead be done by scanning `nodes[].source_file` (no
manifest shortcut exists for this).

## Verification of the Ticket's Core Claim (crux of this ticket)

Counted directly against `graphify-out/graph.json` (86,909 edges total) with
`python3`/`json`, grouping by `relation` and `confidence_score`:

**Part A allowlist relations (per `docs/ai/code_test_index_boundaries_decision.md` §2),
per-relation-type breakdown:**

| relation | total edges | `confidence_score==1.0` (EXTRACTED) | INFERRED | INFERRED % |
|---|---:|---:|---:|---:|
| `imports` | 10,254 | 10,254 | 0 | 0.0% |
| `imports_from` | 223 | 223 | 0 | 0.0% |
| `calls` | 19,548 | 11,916 | 7,632 (score=0.8) | **39.0%** |
| `contains` | 12,975 | 12,975 | 0 | 0.0% |
| `defines` | 0 | — | — | n/a (zero occurrences in this repo) |
| `uses` | 26,984 | 0 | 26,984 (score=0.5) | **100.0%** |
| `uses_static_prop` | 0 | — | — | n/a |
| `references_constant` | 0 | — | — | n/a |
| `bound_to` | 0 | — | — | n/a |
| `listened_by` | 0 | — | — | n/a |
| `includes` | 0 | — | — | n/a |
| `uses_component` | 0 | — | — | n/a |
| `binds_method` | 0 | — | — | n/a |
| `rationale_for` | 6,845 | 6,845 | 0 | 0.0% |

**Ticket claim vs. verified reality:** the ticket's Request Summary states `uses`=100%
INFERRED (**confirmed exactly**) and `calls`=42% INFERRED (**verified as 39.0%**, i.e.
7,632/19,548 — directionally correct, materially the same conclusion, off by ~3
percentage points from the ticket's stated figure, likely a rounding/earlier-snapshot
discrepancy, not a different conclusion). **The ticket's core claim — that the decision
doc's per-relation-type "confidence_score=1.0 for all Part A types" assertion is false at
the per-edge level — is CONFIRMED, and confirmed more starkly than the ticket even
states** (see "Aggregate impact" below).

**`method` and `inherits` (ticket's open question — not in the decision doc's table at
all):**

| relation | total | `confidence_score==1.0` | other |
|---|---:|---:|---:|
| `method` | 4,566 | 4,566 (100%) | — |
| `inherits` | 715 | 710 (99.3%) | 5 edges at `confidence_score=0.5` despite `confidence="EXTRACTED"` |

`method` is 100% deterministic and a strong Part A candidate. `inherits` is **not
uniformly deterministic** — see below.

**Critical additional finding beyond what the ticket asked to verify:** the `confidence`
(string) and `confidence_score` (float) fields are **not always consistent with each
other**, which is a sharper version of the ticket's own thesis. Five `inherits` edges
carry `confidence: "EXTRACTED"` (the label) but `confidence_score: 0.5` (the float the
decision doc's own §1.2 says `INFERRED` maps to). Concrete example:
```json
{"relation": "inherits", "confidence": "EXTRACTED", "confidence_score": 0.5,
 "source_file": "src/observability/understanding/domain/quest.py", "source_location": "L21",
 "source": "domain_quest_questdomainanalyzer", "target": "domain_base_domainanalyzer"}
```
(4 more identical-pattern edges in `tests/unit/observability/test_domain_analyzer_registry.py`.)
**This proves the AC's filter must key off `confidence_score` (the numeric field), not
the `confidence` label string — the two fields diverge on real edges, and only
`confidence_score` matches the decision doc's own stated `EXTRACTED→1.0` construction
rule.** The ticket's AC48 text ("...the edge's own `confidence_score` == 'EXTRACTED'")
conflates the two field names/types — `confidence_score` is a float, `'EXTRACTED'` is a
value of the separate `confidence` field. **Flagged as an open question below — the
implementer must filter on `confidence_score == 1.0`, not a string comparison, and the
ticket text should be read with that correction, not literally.**

**Aggregate impact (not asked for by the ticket, but directly informs Scope's filtering
requirement):** Summing across the full Part A allowlist —
- Filtering by **relation-type membership only** (the naive reading of the decision doc's
  Resolution §3) admits **76,829 edges**.
- Filtering by **relation-type membership AND `confidence_score == 1.0`** (what this
  ticket's AC48 requires) admits **42,213 edges**.
- **34,616 edges (45.1% of the naive set) would be wrongly admitted as "deterministic" by
  a relation-type-only filter.** This is overwhelmingly driven by `uses` (26,984, 100%
  wrong) and `calls`'s INFERRED slice (7,632). This is the single strongest piece of
  evidence that per-edge filtering, not per-relation-type filtering, is required — a
  relation-name allowlist alone would silently admit almost half its candidate edges as
  "deterministic" when they are not.

**Relations present in the graph but absent from the decision doc's table entirely**
(found by enumerating all relation types in `graph.json`, not just the ones the ticket
asked about):

| relation | total | `confidence_score==1.0` |
|---|---:|---:|
| `references` | 4,658 | 4,658 (100%) |
| `re_exports` | 137 | 137 (100%) |

Both are fully deterministic in the live graph. `references` is a naming collision with a
concern: the decision doc's Part B table lists `implements / references / cites` as
LLM-derived (`llm.py:76`'s prompt vocabulary). Direct inspection of the installed
`graphify` package source (`.../graphify/extract.py:108,137,2372,2471,2519,...` — dozens
of call sites) shows a **separately-named, Part-A-only `"references"` relation** emitted
by the deterministic AST walker with `add_edge`'s default `confidence="EXTRACTED"`
(`extract.py:2233-2247`), structurally unrelated to the LLM's self-reported `references`
output. The decision doc's Part B table entry for `references` is about the **LLM's**
output vocabulary, which happens to share a string with a **different, Part A** edge type
that decision doc's Part A table never mentions. Both `references` and `re_exports` are
real, checked-in, deterministic data currently outside the decision doc's documented
scope — same category of gap the ticket already flags for `method`/`inherits`.

**`graphifyy` package version drift — confirmed, not hypothetical:** the decision doc
(§1.1) evidenced its entire relation-type table against `graphifyy==0.6.7`
("`$ pip show graphifyy` → `Version: 0.6.7`") and explicitly warned that an unpinned
future upgrade "can silently change or remove relation types this decision treats as
stable, with no repo-level signal." **That has already happened.** The installed package
in this environment's `uv` cache is
`graphifyy-0.8.39` (`/home/u24desktop/.cache/uv/archive-v0/dAJSHndn1ta-7zBt/graphifyy-0.8.39.dist-info/METADATA`
— `Version: 0.8.39`), and neither `requirements.txt` nor `requirements-knowledge.txt`
pins `graphifyy` at all (grep for `graphify` in both files returns nothing).
`graphify-out/graph.json`'s `calls` relation shows INFERRED edges at a materially
different `confidence_score` (0.8) than `uses`'s INFERRED edges (0.5) — i.e. even the
`INFERRED → 0.5` default the decision doc cited from `export.py`'s
`_CONFIDENCE_SCORE_DEFAULTS` is not uniformly true across relation types in the
currently-installed 0.8.39 build. **This is exactly the drift risk the decision doc
predicted, already realized, and directly explains why the decision doc's per-type table
(evidenced against 0.6.7) no longer matches live 0.8.39 data (evidenced in this
investigation).**

## Mechanics / Engine Constraints

This is agent-orchestration/retrieval tooling, not simulation logic — no `docs/mechanics/`
chapter or `docs/engine/` contract governs code/test-index semantics directly. The
relevant constraints are process/architecture contracts, not simulation laws:

- `docs/engine/contracts/context_packet_contract.md` §2 — any future `ContextPacket`
  `included[]` entry of `kind: code_symbol` / `kind: test` / `kind: graphify_node` must
  carry `authority`/`freshness` = the literal sentinel `unrated` (§3 "Extension —
  non-registry-backed source fallback") since none of these `kind`s are indexed by
  `docs/REGISTRY.yaml`. This ticket does not build `ContextPacket` assembly itself (that
  is the separate, dependent sibling ticket `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`), but
  the index's per-record shape (module/symbol/docstring/owned-component/associated-tests)
  should be assemblable into that `included[]` shape without rework.
- `docs/ai/code_test_index_boundaries_decision.md` §3 Resolution — binds this ticket to
  Part A relations only; Part B (LLM-derived: `conceptually_related_to`,
  `semantically_similar_to`, `shares_data_with`, LLM-self-reported
  `calls`/`implements`/`references`/`cites`) is explicitly out of scope (also restated in
  the ticket's own Out of Scope).
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
  §"Retrieval layers" (lines 131-135) — "index symbols and relationships—not entire files
  as large embedding chunks... Graphify remains the relationship layer; it should not
  inject an entire community unless the task asks for architectural traversal." This is
  the direct source of AC4 (bounded-hop neighbors, not full-community injection).
  §"Maturity: PROPOSED FUTURE EPIC" banner (line 13) and
  `ticket_plan_structure_phase3.md`'s restatement (lines 25-30): this ticket may not wire
  into any `.claude/workflows/*.js` file or any mandatory pipeline gate — must remain a
  standalone, directly-testable, manually-invocable module.

## Parity Ledger Overlap

No existing `docs/parity_ledger/` entry mentions `graphify`, `knowledge_search`, or
`code_test`/`retrieval` (grepped all six subsystem YAML files). This is expected —
agent-orchestration tooling is out of Mechanics Bible scope, same posture the
`context_packet_contract.md` §4 already states.

**However, `docs/parity_ledger/infrastructure.yaml` has an established, actively-used
precedent for ledgering exactly this class of change**: `INFRA-281` through `INFRA-292`
(all `status: verified`, `priority: P2`) each cover a code-producing agent-monitoring/
agent-infrastructure tooling ticket (not simulation logic), each carrying a
`support_boundary` field explicitly stating "Agent-orchestration/monitoring-pipeline
tooling only — no simulation behavior... governs this reporting tool's semantics." The
closest sibling is `INFRA-292` (`docs/parity_ledger/infrastructure.yaml:5927-5956`),
covering `TCK-20260728-RETRIEVAL-BASELINE-METRICS` — a Phase-2-era retrieval-adjacent
tool with `test_path: tests/tools/test_retrieval_baseline_metrics.py`. **This ticket
should very likely get its own new `INFRA-293` entry (or next available ID) following the
same pattern once `tools/code_test_index.py` lands**, not be treated as exempt. Flag: the
Phase 2 decision docs (`context_packet_contract.md` §4) claim "a future reader should not
read the absence of a parity ledger entry here as a gap" for `ContextPacket`-schema-only
work, but that framing was written for a documentation-only ticket
(`CONTEXT-PACKET-SCHEMA`), not a code-producing one like this one — `INFRA-281`–`292`'s
own pattern is code-producing tickets DO get an entry. This is a **discrepancy between
what one Phase 2 doc implies and what the actual established ledger practice does** —
resolve in favor of the ledger's own precedent (add an entry) when this ticket implements,
not the doc's aside.

## Prior Work

- `docs/ai/code_test_index_boundaries_decision.md` (`TCK-20260728-CODE-TEST-INDEX-BOUNDARIES`,
  hotfix tier, no staging artifacts — DONE) is this ticket's direct predecessor and the
  document whose per-relation-type claim this ticket's Request Summary corrects.
- `tickets/todos/context-retrieval-phase3/SEQUENCE.md` establishes this ticket (#1 of 4,
  "no deps in this batch") alongside three siblings still in `tickets/todos/`:
  `TCK-20260729-HYBRID-RETRIEVAL-FUSION`, `TCK-20260729-RETRIEVAL-CACHE-LEVELS`, and
  `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` (the last has a hard dependency on the other
  two, not on this ticket). This ticket's output shape should be stable/self-contained
  since nothing in this batch currently depends on it, but `CONTEXT-PACKET-ASSEMBLY` may
  consume it later informally.
- `tools/knowledge_search.py` / `tools/agent-monitoring/build_index.py` are the two
  explicit precedent SQLite-index shapes `ticket_plan_structure_phase3.md` (line 50-51)
  names as the pattern to follow for a new SQLite-backed store — relevant for how
  `tools/code_test_index.py` should structure its own persistence, if any (the ticket
  doesn't mandate SQLite explicitly, only "byte-identical output on rebuild," so a plain
  JSON/JSONL output may also satisfy AC2 without a DB).
- `tests/tools/test_knowledge_search.py::TestCorpusScopeGuard` (line 506) is the existing
  anti-drift-guard pattern this ticket's own test file should mirror for `src/`/`tests/`
  vs. docs/tickets scope separation.

## Risks and Open Questions

1. **BLOCKING for implementation — field-name/type mismatch in AC48.** The AC text says
   "the edge's own `confidence_score` field == 'EXTRACTED'" but `confidence_score` is a
   float (`1.0`/`0.8`/`0.5`/etc.) and `'EXTRACTED'` is a value of the separate string field
   `confidence`. Verified against real data that these two fields are **not always
   consistent** (5 `inherits` edges have `confidence="EXTRACTED"` but
   `confidence_score=0.5`). The planner/implementer must decide explicitly: filter on
   `confidence_score == 1.0` (recommended — matches the decision doc's own stated
   `EXTRACTED→1.0` construction rule and is stricter/more correct given the observed
   mismatch) vs. `confidence == "EXTRACTED"` (looser, would incorrectly admit the 5
   mismatched `inherits` edges). **Do not resolve this silently — the planner should state
   the choice explicitly since it changes the guarantee's literal definition.**
2. **`graphifyy` version pin target is unclear and possibly wrong as stated.** The
   ticket's Scope says "Pin graphifyy==0.6.7 in requirements given it's currently unpinned"
   — but the actually-installed version in this environment is **0.8.39**, and
   `graph.json` was built with whatever version produced its current edge data (which
   already shows behavior — `calls` INFERRED edges, `inherits` confidence/score mismatch —
   inconsistent with the 0.6.7-evidenced decision doc). Pinning `==0.6.7` while `0.8.39` is
   what's actually installed and what actually produced the graph this ticket indexes
   would create a **pin that lies about reality** — a downgrade to 0.6.7 was never
   performed, isn't verified to reproduce the current graph, and isn't what any
   `pip install` in this environment would currently produce. **Recommend pinning to the
   actually-installed `graphifyy==0.8.39` instead, and flag in the ticket/plan that the
   0.6.7 figure in Scope is stale** (inherited from the Phase 2 decision doc's evidence
   date, not re-verified before this ticket was written). This does not block starting
   the index-builder work, but does block writing an accurate `requirements.txt` pin line
   — needs a decision before that specific line of Scope is implemented.
3. **Whether to formalize test-scoper's mapping (AC3) is a real decision, not a gap to
   silently skip.** `docs/ai/code_test_index_boundaries_decision.md` §1.3/§3 already
   concluded test-naming linkage is "deterministic-in-principle but not checked-in code
   today" and explicitly deferred formalizing it to "a future ticket if Phase 2+ retrieval
   work needs it as data." This ticket's Scope explicitly asks to decide this now. Given
   `.claude/agents/test-scoper.md`'s mapping (`src/<module>/` → `tests/unit/<module>/`, a
   pure naming convention over `tests/unit/`'s fixed directory list, lines 10-22) is
   simple and already checked-in as prose, a minimal deterministic implementation (glob
   `tests/unit/<module>/**` for a given `src/<module>/` symbol) is low-risk and directly
   closes the "never silently empty" requirement in AC3. Recommend implementing this
   minimal version rather than flagging-only, but this is a planning-level choice, not
   dictated by this investigation alone.
4. **`references` / `re_exports` inclusion decision.** Ticket's Assumptions section only
   asks about `method`/`inherits`; this investigation additionally found `references`
   (4,658 edges, 100% deterministic, but name-colliding with a Part B LLM output type) and
   `re_exports` (137 edges, 100% deterministic) as real, checked-in, fully deterministic
   data outside the decision doc's table. Same "include only if planning confirms it fits
   Part A's intent" posture the ticket already applies to `method`/`inherits` should
   extend to these two — flagging here since the ticket text doesn't mention them at all.
5. **Zero-occurrence allowlist entries** (`defines`, `uses_static_prop`,
   `references_constant`, `bound_to`, `listened_by`, `includes`, `uses_component`,
   `binds_method`) confirmed to have 0 edges in this repo's current graph — matches the
   ticket's Assumptions note; tests must not assume these will ever populate (they may be
   legitimate for other languages/frameworks not present in this repo).

## Anti-Drift Hazards

- **Do not merge this index into `tools/knowledge_search.py`'s corpus or its `cmd_build`/
  `cmd_query` pipeline.** They are structurally different data sources (docs/tickets text
  vs. graph edges) with a standing scope-guard test
  (`TestCorpusScopeGuard::test_collect_corpus_only_reads_defined_roots`) that explicitly
  asserts `src/` never leaks into the docs corpus. A well-intentioned "just add code
  results to the same search" implementation would violate that guard's intent even if it
  doesn't touch that exact file.
- **Do not build a relation-type-name-only filter and call it "deterministic."** The
  verified 34,616-edge gap (45.1% of the naive relation-type-only set) between "in the
  Part A allowlist" and "in the Part A allowlist AND `confidence_score==1.0`" is the
  entire reason this ticket exists — a filter keyed only on relation-type name silently
  reintroduces the bug this ticket is meant to fix.
- **Do not touch `graphify/extract.py` or any file inside the installed `graphifyy`
  package.** It is an external pip dependency (confirmed at
  `/home/u24desktop/.cache/uv/archive-v0/.../graphify/`), not repo-owned code — this
  ticket only reads `graphify-out/graph.json`, the already-extracted output.
- **Do not wire this module into any `.claude/workflows/*.js` file or make it run
  automatically as part of any existing pipeline/gate.** Both the idea doc's Maturity
  banner and `ticket_plan_structure_phase3.md` are explicit that Phase 3 ships
  "standalone, directly-testable... callable manually" code only.
- **Do not build hybrid retrieval fusion, cache layers, or `ContextPacket` assembly in
  this ticket** — those are the three sibling tickets in
  `tickets/todos/context-retrieval-phase3/` (`HYBRID-RETRIEVAL-FUSION`,
  `RETRIEVAL-CACHE-LEVELS`, `CONTEXT-PACKET-ASSEMBLY`), explicitly out of this ticket's
  scope per its own Out of Scope section.
- **Do not silently drop the "associated tests" field to empty** if the test-naming
  mapping isn't implemented — AC3 explicitly requires an explicit flagged-gap value, not
  a silently empty field, mirroring the project-wide "never silently empty" convention
  already used for the `unrated` sentinel in `context_packet_contract.md` §3.
- **Do not assume `graphify-out/graph.json` is static.** It is regenerated by an external
  tool (`graphify update .` per this repo's CLAUDE.md) and its `built_at_commit` field
  (currently `96bb229...`) changes across rebuilds — AC2's "byte-identical output on
  rebuild from the same `graph.json`" must be tested by holding `graph.json` fixed
  (fixture or copy), not by re-running `graphify` twice, since a `graphify` rebuild is not
  itself guaranteed byte-identical (external tool, versioned, not repo-controlled).
