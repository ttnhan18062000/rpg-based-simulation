---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
phase: done
date: 2026-07-28
tags: [ai, investigation]
---

# TCK-20260728-CODE-TEST-INDEX-BOUNDARIES

## Title
Resolve Code/Test Index Boundaries Without a New Semantic Code Model

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The author wants a decision document resolving Open Decision 2: which code/test relationships (AST, import, test-naming, Graphify-derived) can be built deterministically today, without introducing any new semantic code model. This must be grounded by investigating graphify-out/ and tools/graphify-adjacent code for what already exists, not hypothetical capability — the risk being that the doc could otherwise overstate what's actually deterministic and checked-in versus what only exists as agent-followed procedure.

## Scope
- Author a decision document (expected: docs/ai/code_test_index_boundaries_decision.md) enumerating each code/test relationship type (imports, imports_from, calls, contains, defines, uses, bound_to, listened_by, test-naming convention) and stating whether it is deterministically available today.
- Cite graphify's extract.py relation strings and confidence_score=1.0 EXTRACTED semantics as the evidentiary basis.
- Explicitly separate graphify's Part A (AST/tree-sitter, LLM-free, deterministic) from Part B (semantic/LLM extraction producing conceptually_related_to/semantically_similar_to/rationale_for edges), stating that only Part A satisfies 'no new semantic code model.'
- State that test-naming mapping is deterministic as a procedure today but exists only as agent prose in .claude/agents/test-scoper.md, not a checked-in script/index, and record this as a gap.
- Record that graphify's extractor is an externally installed pip package, not repo-owned code, and state the reproducibility/versioning implication.
- Resolve Open Decision 2 in the epic ticket, updating its Open Questions section (and SEQUENCE.md) once the doc lands.

## Out of Scope
- Building any new relationship-extractor code or formalizing test-scoper's mapping into a checked-in script/index.
- Any src/ or tools/ implementation.
- Phase 3 retrieval/cache implementation.
- Phase 4 observability events/dashboard work.
- Phase 5-6 shadow packets or workflow adoption.
- Force-resolving any Open Decision other than Decision 2.

## Acceptance Criteria
- [ ] Decision doc enumerates each relationship type (imports, imports_from, calls, contains, defines, uses, bound_to, listened_by, test-naming convention) and states deterministic-availability today, citing graphify's extract.py relation strings and confidence_score=1.0 EXTRACTED semantics.
- [ ] Doc separates graphify Part A (AST, LLM-free, deterministic) from Part B (semantic/LLM extraction), stating only Part A satisfies 'no new semantic code model.'
- [ ] Doc states test-naming mapping is deterministic in procedure today but exists only as agent prose (.claude/agents/test-scoper.md), not a checked-in script/index, recording this as a gap.
- [ ] Doc records that graphify's extractor is an externally installed pip package, not repo-owned tools/ code, and states the reproducibility/versioning implication.

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-EVAL-FIXTURE-REPAIR

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/ai/monitoring_writer_decision.md
- docs/testing/how_to_add_requirement_tests.md
- docs/testing/test_taxonomy.md
- graphify-out/GRAPH_REPORT.md

## Related Stored Artifacts
None.

## Related Code Areas
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md
- tickets/todos/context-efficient-retrieval/SEQUENCE.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/ai/monitoring_writer_decision.md
- .claude/agents/test-scoper.md
- docs/testing/how_to_add_requirement_tests.md
- docs/testing/test_taxonomy.md
- graphify-out/GRAPH_REPORT.md
- tools/graphify_to_html.py
- tools/knowledge_search.py
- expected: docs/ai/code_test_index_boundaries_decision.md

## Assumptions / Open Questions
- Graphify's AST extraction lives in an externally installed pip package (~/.local/lib/python3.13/site-packages/graphify), not repo tools/ — the doc must correct this misconception rather than imply it's repo-owned code.
- test-scoper's relationship mapping is agent-instruction prose, not checked-in deterministic code; 'deterministic' claims in the doc must distinguish 'procedure an agent follows' from 'deterministic checked-in code.'
- Whether this is a new child ticket under the epic or a standalone preparatory ticket should be confirmed by updating the epic's Open Questions and SEQUENCE.md when this ticket closes.
- Tier is hotfix because the deliverable is a single decision document citing already-produced evidence (graphify's existing extraction behavior, GRAPH_REPORT.md), with no new schema/contract invented and no code/test changes.

## Implementation Notes

Authored `docs/ai/code_test_index_boundaries_decision.md`, resolving Open Decision 2. All claims
were independently verified against the installed package before writing (not copied from the
prior investigation pass):

- Confirmed via `python3 -c "import graphify; print(graphify.__file__)"` and `pip show graphifyy`
  that the import name (`graphify`) and pip distribution name (`graphifyy`, version 0.6.7) differ,
  and that it is installed to `~/.local/lib/python3.13/site-packages/graphify/`, not repo-owned
  `tools/` code.
- Read `graphify/extract.py` directly and confirmed the deterministic tree-sitter engine
  (`LanguageConfig` + `_extract_generic`, lines 66-1541) emits `imports`, `imports_from`, `calls`,
  `contains`, `defines`, `uses`, `uses_static_prop`, `references_constant`, `bound_to`,
  `listened_by` (plus `includes`/`uses_component`/`binds_method` from the Blade-specific
  extractor), all tagged `confidence: EXTRACTED`, which `graphify/export.py`'s
  `_CONFIDENCE_SCORE_DEFAULTS` (line 329) maps to `confidence_score = 1.0` on serialization.
- Read `graphify/llm.py` and confirmed Part B's LLM prompt schema (line 76) fixes its own output
  vocabulary to `calls|implements|references|cites|conceptually_related_to|shares_data_with|
  semantically_similar_to`, requiring a live `_call_claude`/OpenAI-compatible API call
  (`ANTHROPIC_API_KEY`).
- **Correction to the ticket's stated premise:** the ticket (and the prior investigation) placed
  `rationale_for` in Part B. Direct inspection shows `rationale_for` is emitted only by
  `_extract_python_rationale()` (`extract.py:1542-1599`), a deterministic tree-sitter docstring
  pass with `confidence: EXTRACTED` — it does not appear anywhere in `llm.py`'s LLM output
  vocabulary. The decision doc documents and corrects this rather than silently reproducing the
  ticket's framing.
- Confirmed test-naming mapping (`.claude/agents/test-scoper.md`,
  `docs/testing/how_to_add_requirement_tests.md` §3, `docs/testing/test_taxonomy.md`) is agent
  prose only — `grep -rl "tests/unit" tools/` and a filename search for `*test_map*`/
  `*test_index*`/`*code_test*` under `tools/` found no checked-in mapping code.
- Updated `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Assumptions/Open
  Questions to mark OPEN DECISION 2 resolved, citing the new doc.
- Did not touch `tickets/todos/context-efficient-retrieval/SEQUENCE.md` — confirmed it only tracks
  Phase 0-1 batch ticket ordering for an already-closed batch and has no Open Decision references.

No deviation from the ticket's scope. No code, script, or index was created — documentation only.

## Test Summary

`python3 tools/validate_frontmatter.py docs/ai/code_test_index_boundaries_decision.md` → OK, no
violations (status/layer/authority/audience all valid, tags `[ai, investigation]` both registered
per `tools/tag_registry.py list`). No behavior changed, so no pytest scope applies; this is a
documentation-only hotfix.

## Files Changed

- `docs/ai/code_test_index_boundaries_decision.md` (new)
- `tickets/inprogress/TCK-20260728-CODE-TEST-INDEX-BOUNDARIES.md` (this ticket)
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (Open Questions updated)

## Completion Summary

Open Decision 2 is resolved: the deterministic-today code/test relationship set is exactly
Graphify's Part A (tree-sitter/AST) relations — `imports`, `imports_from`, `calls`, `contains`,
`defines`, `uses`, `uses_static_prop`, `references_constant`, `bound_to`, `listened_by`,
`includes`, `uses_component`, `binds_method`, `rationale_for` — all `confidence_score = 1.0`,
already produced by the externally pip-installed `graphifyy==0.6.7` package and stored in
`graphify-out/graph.json`. Part B (LLM-derived `conceptually_related_to`,
`semantically_similar_to`, `shares_data_with`) requires a live model call and is excluded as it
would itself constitute a new semantic code model. Test-naming linkage is a deterministic
*procedure* today (test-scoper prose + naming convention docs) but is **not backed by any
checked-in script/index** — recorded as an explicit gap, not treated as equivalent to graphify's
stored-artifact determinism. See `docs/ai/code_test_index_boundaries_decision.md` for full
evidence and the relationship-type table.
