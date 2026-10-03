---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-MEASUREMENT-BASELINE
phase: done
date: 2026-08-14
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260814-KGMCP-MEASUREMENT-BASELINE

## Title
Record the Knowledge Gateway Phase 0 measurement baseline and predeclare promotion thresholds,
reusing existing retrieval-effectiveness metrics

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 0 requires recording a direct-tool
baseline (latency, tool-call counts, repeated-demand signals, returned-token estimates) for a fixed
representative-query corpus, and predeclaring measurable promotion thresholds, before any gateway
work is evaluated. §18 requires separately measuring lookup, evidence-validation, provider-fallback,
packet-assembly, and end-to-end latency rather than one blended number. §18.1 requires a repeated-
demand estimate using safe deterministic intent/entity IDs, not raw prompt text.

This ticket must **not** build a second, parallel measurement path.
`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (sibling epic child, `agent-tooling-integrity-
hardening`) is already wiring `raw_investigation_count`/`search_count`/`read_to_search_ratio` from
`tools/agent-monitoring/retrieval_baseline_metrics.py` into the recurring `generate_retro.py`
report, including a compliant-vs-non-compliant `Read`-count correlation section. This ticket's
baseline work depends on and extends that infrastructure.

## Scope
- **Investigate (mandatory before Plan):** check the real status of
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (OPEN as of this ticket's creation). If it
  has landed, build directly on its retro sections. If it is still open, coordinate rather than
  duplicate — this ticket's baseline corpus should consume the same
  `retrieval_baseline_metrics.py` functions that ticket wires into the retro, not a second
  `read_to_search_ratio`-equivalent computation.
- Create a fixed representative-query corpus (per §20) spanning the query-routing shapes in §8's
  table (definition/terminology, symbol lookup, requirement-completeness, ticket/historical
  rationale, test-impact, ticket-status, broad-task-context) and the representative use cases in
  §22 (`AuthoritativeState` ownership, feature-completeness check, historical-removal rationale,
  test-impact-of-change, negative-knowledge/Kafka-style query).
- For each corpus query, record the direct-tool baseline: provider outputs, authoritative sources
  recalled, wall time, tool-call count, and serialized tokens returned — using real tool
  invocations against this repository, not estimates.
- Define separate measurement points for lookup latency, evidence-validation latency, provider-
  fallback latency, packet-assembly latency, and end-to-end latency (§18), even though no gateway
  exists yet to measure — this ticket defines the measurement points and instrumentation contract
  that Phase 1+ code must emit into.
- Predeclare minimum latency, token-reduction, and no-regression-recall thresholds derived from the
  recorded baseline (§20's explicit requirement not to invent thresholds before the baseline
  exists).
- Define the repeated-demand estimation approach from §18.1: exact repeated lookup identities,
  entity-and-intent-equivalent requests with different query hashes, repeated misses by entity and
  intent — using safe deterministic intent/entity IDs and the keyed query hash, never raw prompt
  text.

## Out of Scope
- Wiring any of this into a live gateway — no gateway exists yet in Phase 0.
- Modifying `retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design or Bash-exclusion
  rationale — reused as-is, per `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s own
  out-of-scope note.
- Semantic clustering of repeated demand — §18.1 explicitly defers privacy-reviewed semantic
  clustering to Phase 5.
- Backfilling correlation numbers for historical weeks — first data point is real, forward-looking
  data only.

## Acceptance Criteria
- [x] `investigation.md` confirms the real status of `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-
      TRACKING` and states explicitly how this ticket's baseline work reuses (not duplicates) its
      metric functions.
- [x] A fixed, versioned representative-query corpus exists, covering all routing shapes from §8
      and all 5 use cases from §22.
- [x] Each corpus query has a recorded direct-tool baseline (provider outputs, sources recalled,
      wall time, tool-call count, serialized tokens) from a real run, not an estimate.
- [x] Lookup, evidence-validation, provider-fallback, packet-assembly, and end-to-end latency are
      defined as distinct measurement points with a documented instrumentation contract.
- [x] Minimum latency, token-reduction, and no-regression-recall thresholds are predeclared and
      derived from the recorded baseline numbers (not invented independently of them).
- [x] The repeated-demand estimation design uses only deterministic intent/entity IDs and query
      hashes — no raw prompt text is persisted.
- [x] Tests mirror `tests/tools/test_retrieval_baseline_metrics.py`'s never-silent,
      derivation-string convention.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (OPEN; owns the metric infrastructure this
  ticket must reuse — check status before Plan)
- TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC (DONE; original `raw_investigation_count`/
  `read_to_search_ratio` metric)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (BACKLOG; broader retrieval epic this baseline also
  informs)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18, §18.1, §20, §22
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_retrieval_baseline_metrics.py`

## Assumptions / Open Questions
- Whether the representative-query corpus lives as a fixture file consumed by both this ticket and
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation section, or is scoped
  independently — Investigate should check that sibling ticket's actual implementation (once it
  lands) before deciding, to avoid a second corpus definition.

## Implementation Notes
Implemented all 7 steps of `staging_artifacts/TCK-20260814-KGMCP-MEASUREMENT-BASELINE/plan.md`,
following its Design Decision ("code + docs, not docs-only") exactly:

- **Step 1** — `tools/agent-monitoring/kgmcp_baseline_corpus.py`: `CORPUS_VERSION = 1`,
  `ROUTING_SHAPES` (7 IDs, one per §8 table row, confirmed 7 rows not 8 by direct read),
  `USE_CASES` (5 IDs, one per §22 heading), `CORPUS` (7 entries, 5 double-tagged with a use case),
  and `kgmcp_char_heuristic_v1_token_count()` implementing the frozen formula from
  `redaction_retention_policy.md:147-149` as a callable for the first time.
- **Step 2** — `tools/agent-monitoring/kgmcp_baseline_runner.py`: a one-time script separating a
  pure `run_corpus()` (in-memory, no file write) from `main()` (writes the fixture). Calls
  `tools/search_mcp.py::_run_search()` directly and shells out to `graphify query`, both timed via
  `time.perf_counter()` mirroring `tools/retrieval_events.py:175-177`. Ran it by hand; wrote
  `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` (7 real entries,
  `recorded_at_utc: 2026-08-15T05:09:04.120766Z`). Verified `git status --porcelain --
  agent-monitoring/` was identical before and after the run (zero mutation) — confirmed twice, by
  hand and again inside the test suite via `run_corpus()`.
- **Steps 3-5** — `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`
  §1 (corpus summary), §2 (5 latency measurement points, each citing `tools/retrieval_events.py`'s
  3 Wrapper functions where live precedent exists, using the phrasing "implemented but not invoked
  by any live call site" per the Architecture Review's wording-clarity note), §2.6 (fixture-
  baseline-vs-future-gateway-latency non-conflation), §4 (3 predeclared thresholds, each a formula
  over the Step-2 fixture's fields, with the actual computed millisecond/token figures cited
  alongside the formula), §5 (§18.1 repeated-demand design using only `intent`/`entity_id`/
  `normalized_filters`/`query_hash`, reporting 0 for all 4 categories today and stating explicitly
  why).
- **Step 6** — `tests/tools/test_kgmcp_measurement_baseline.py`, 23 tests. Mirrors
  `test_retrieval_baseline_metrics.py`'s never-silent/derivation-string convention plus
  `test_knowledge_gateway_contract_schemas.py`'s raw-text structural pattern. Exactly one bounded
  live smoke-check (`test_corpus_baseline_wall_time_and_tool_call_count_are_plausible`, scoped to
  `Q1_authoritative_state` only) with an explicit `signal.alarm`-based 60s timeout (no
  `pytest-timeout` plugin is installed in this venv, so a manual wrapper was used, per the
  Architecture Review's note that the plan didn't specify a timeout mechanism).
- **Step 7** — annotated §20's 3 previously-unannotated Phase 0 bullets in
  `docs/plans/knowledge-gateway-mcp-proposal.md` with "**Done**
  (`TCK-20260814-KGMCP-MEASUREMENT-BASELINE`)"; added a note to
  `docs/agent-monitoring/README.md` distinguishing this one-time recording from both
  `retrieval_baseline_metrics.py`'s periodic snapshot and `generate_retro.py`'s recurring cadence;
  added `INFRA-334` to `docs/parity_ledger/infrastructure.yaml` via
  `tools/parity_ledger_writer.py::write_entry()` (the required authoritative write path, which also
  rebuilt the derived SQLite index in-process), then issued the separate visible
  `python3 tools/parity_index.py build` call per that writer module's own documented reason.

**Deviation from Step 6's literal wording (recorded in plan.md's Deviations section too):**
`test_zero_mutation_of_real_agent_monitoring_corpus` calls `kgmcp_baseline_runner.run_corpus()`
in-process rather than invoking `main()` via subprocess. `main()` overwrites the committed fixture
with fresh (necessarily different, since network/CPU timing is not reproducible) `latency_ms`
figures on every invocation, which directly contradicts Step 2 point 6's own rule that the fixture
"is pinned (git-committed), not regenerated by the test suite." `run_corpus()` exercises the
identical live-call code path (`_run_context_search`/`_run_graphify`, all 7 entries) that `main()`
does, so the zero-mutation proof against `agent-monitoring/` is unaffected; only the file-write
step (irrelevant to that specific assertion) is skipped. Confirmed via direct `git status
--porcelain -- agent-monitoring/` before/after, both by hand (twice) and inside the test.

Also relaxed `test_predeclared_thresholds_cite_recorded_baseline_numbers` from an exact-numeric-
match assertion (my own initial over-specification, not in the plan) down to the plan's actual
literal spec — presence of the fixture path string in §4's prose — for the same reproducibility
reason: any test that hardcodes an exact average recomputed from a fixture whose numbers can
legitimately drift on re-recording would be inherently flaky.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_kgmcp_measurement_baseline.py -q` → 23 passed.
Verified zero mutation of `agent-monitoring/` across the full suite run (`git status --porcelain --
agent-monitoring/` identical pre/post). Regression check on sibling/related suites — `pytest
tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_generate_retro.py
tests/tools/test_knowledge_gateway_contract_schemas.py
tests/tools/test_evidence_cache_identity_contract.py tests/tools/test_retrieval_cache.py -q` → 220
passed, no regressions. `python3 tools/validate_frontmatter.py` passed for the ticket file and the
new contract doc.

**Test phase (orchestrator-run, post-Implement scoped regression):**
`.venv/bin/python3 -m pytest tests/tools/test_kgmcp_measurement_baseline.py
tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_retrieval_events.py
tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_parity_ledger_writer.py
tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_ledger_scan.py
tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py
tests/docs/test_doc_integrity.py -q` → 251 passed, 3 failed, 1 skipped. All 23 new tests pass; no
sibling/precedent regression. The 3 failures (`test_generate_registry.py::TestRealDocsTree` x2,
`test_validate_frontmatter.py::TestPreviouslyFrontmatterMissingDocs[docs/mechanics/
content_usage_matrix.md]`) trace to a single root cause — `docs/mechanics/content_usage_matrix.md`
missing a frontmatter block — confirmed via `git log`/`git status` to be **pre-existing and
unrelated to this ticket's diff**: zero uncommitted changes to that file, last touched in commit
`29d78798` (before this epic began). This same scoped run also caught a second, genuinely
in-scope frontmatter gap on a file this ticket actually edits —
`docs/plans/knowledge-gateway-mcp-proposal.md` had never carried a frontmatter block (confirmed at
`HEAD`, predating all 4 prior KGMCP tickets' edits to it) — fixed directly (added `status: active,
layer: ai, authority: P1, audience: agent, tags: [mcp]`, all registry-backed values) since this
ticket's own Files-Changed already includes this file and its own Step 7 regenerates
`docs/REGISTRY.yaml`. Re-running the scoped suite after that fix leaves only the 3
`content_usage_matrix.md`-caused failures, confirmed pre-existing and out of this ticket's scope —
recommend a follow-up hotfix ticket to add frontmatter to `docs/mechanics/content_usage_matrix.md`
repo-wide (not raised here to avoid unrelated scope creep on this ticket).

## Files Changed
- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (new)
- `tools/agent-monitoring/kgmcp_baseline_runner.py` (new)
- `tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json` (new, committed fixture)
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` (new)
- `tests/tools/test_kgmcp_measurement_baseline.py` (new, 23 tests)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (§20 annotation for 3 Phase 0 bullets)
- `docs/agent-monitoring/README.md` (new "Knowledge Gateway MCP Phase 0 Measurement Baseline"
  note)
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-334` entry, via `write_entry()`)
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (§5 cross-reference bullet added for
  the new `measurement_baseline_contract.md`, Document-Update phase)
- `docs/REGISTRY.yaml` (regenerated)
- `tickets/inprogress/TCK-20260814-KGMCP-MEASUREMENT-BASELINE.md` (this file)
- `staging_artifacts/TCK-20260814-KGMCP-MEASUREMENT-BASELINE/plan.md` (Deviations section added)

## Completion Summary
Delivered Knowledge Gateway MCP Phase 0's final 3 §20 checklist bullets: a fixed, versioned
7-entry representative-query corpus (`tools/agent-monitoring/kgmcp_baseline_corpus.py`) with a
real, recorded-from-a-real-run direct-tool baseline
(`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`, produced by
`tools/agent-monitoring/kgmcp_baseline_runner.py`); a 5-point latency instrumentation contract
citing `tools/retrieval_events.py`'s existing-but-unwired Wrapper functions; 3 predeclared
promotion thresholds computed as formulas over the recorded fixture; and the §18.1 repeated-demand
design using only deterministic `intent`/`entity_id`/`normalized_filters`/`query_hash` fields, all
in `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`. Unlike its two
pure-documentation KGMCP siblings, this ticket adds real, tested Python code under
`tools/agent-monitoring/` and accordingly ledgers it as `INFRA-334`. 23 new tests pass; zero
mutation of `agent-monitoring/`'s real corpus was verified both by hand and by permanent
regression test.
