---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON
phase: done
date: 2026-08-16
tags: [ai, mcp, testing]
---

# TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON

## Title
Honestly compare real gateway packets against real direct-tool calls

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Proposal §20 Phase 4's fourth bullet is "Compare gateway packets against existing direct-tool
behavior." This is Phase 4's own acceptance-measurement ticket, mirroring
`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` and `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-
MEASUREMENT`'s own "no result may be assumed, only measured" Gate Integrity discipline — extended
here to a genuinely new question those tickets didn't answer: not "does the cache produce hits," but
"does calling the gateway at all (vs. calling Context Search/Graphify/the new Parity adapter
directly, without the gateway) produce a real, measurable advantage for a representative query set."

## Scope
- Reuse the frozen 7-entry corpus and the Phase 1-3 measurement-runner precedent
  (`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` through `kgmcp_phase3_gateway_runner.py`)
  — import pure helpers, never reimplement.
- For each corpus entry, run both: (a) the real gateway call (`knowledge_context`, exercising
  whatever real routing/cache/Parity-adapter behavior exists by the time this ticket runs — it
  depends on `TCK-20260816-KGMCP-P4-PARITY-ADAPTER` and `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`
  both being DONE first, per `SEQUENCE.md`), and (b) the equivalent real direct-tool call(s) an agent
  would make without the gateway (e.g. calling `search_docs`/`graphify query` directly for the same
  question, or `tools/parity_index.py::entry()` directly for a parity-shaped question).
- Compare, honestly: latency (gateway overhead vs. direct call), token cost (gateway's packet
  assembly/redaction overhead vs. raw direct-tool output), and result quality/completeness (does the
  gateway's routing/dedup/budget-enforcement genuinely produce an equal-or-better answer, or does
  going direct sometimes win because the gateway's own budget truncation or routing choice drops
  something a direct call would have kept).
- Report per-query-type results, not just an aggregate — the honest answer may be "the gateway wins
  for symbol lookups but loses for broad architecture questions," and that granularity matters more
  than a single pass/fail number.
- If the real result shows the gateway does NOT provide a genuine advantage for some or all query
  types, report this plainly — mirroring Phase 3's own real, disclosed FAIL on budget tolerance. Do
  not redefine "advantage" or exclude an unfavorable query type to force a favorable aggregate.

## Out of Scope
- Any code change to the gateway, router, cache, or Parity adapter — this ticket measures and
  reports, following the exact same "measurement-only" discipline as its Phase 1-3 predecessors.
- Fixing any disadvantage this ticket's own measurement finds — that is a separate, later,
  human-scoped follow-up ticket's job, mirroring Phase 2/Phase 3's own precedent.
- Declaring Phase 4 complete or the gateway broadly superior/inferior to direct tool use — this
  ticket reports the real, per-query-type measurement; broader characterization is a human reviewer's
  call.

## Acceptance Criteria
- [x] Each of the 7 corpus entries is run through both the real gateway and the real equivalent
      direct-tool call(s), with real latency/token/quality numbers captured for both.
- [x] Results are reported per-query-type, not only as a single aggregate.
- [x] Any query type where the gateway shows no genuine advantage (or a real disadvantage) is
      reported plainly as such — no redefinition, no exclusion to force a favorable result.
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added, certifying this
      ticket's real, measured gateway-vs-direct-tool comparison result — the honest, negative
      result IS what is certified here (unlike `INFRA-344`'s "methodology, not conclusion"
      precedent), since this ticket's own job was to report the real comparison, whatever it
      turned out to be. Added in the Parity phase as `INFRA-354`.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC (parent; this ticket closes its acceptance loop)
- TCK-20260816-KGMCP-P4-PARITY-ADAPTER (dependency)
- TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT (dependency)
- TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT (DONE; supplies the corpus/methodology
  precedent this ticket reuses)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` (methodology
  precedent)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` through
  `kgmcp_phase3_gateway_runner.py` (precedent this ticket's own new runner reuses, never
  reimplements)

## Assumptions / Open Questions
- Whether the real result favors the gateway, direct tools, or a mixed per-query-type picture is not
  assumed — the real measurement decides, per this ticket's own Gate Integrity discipline.

## Implementation Notes

Implemented exactly per the Architecture-Review-APPROVED (2 passes) `plan.md`, Steps 1-9 and 12
(Steps 10-11 explicitly skipped this session, per the stated per-phase ownership convention).

- **Step 1 (decision):** all 7 corpus entries run fresh — no Phase 0-3 fixture reuse. Restated in
  the new runner's own module docstring.
- **Step 2-4 (runner skeleton, direct-tool calls, gateway call):** new
  `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`. Imports
  `CORPUS`/`CORPUS_VERSION`/`kgmcp_char_heuristic_v1_token_count` from `kgmcp_baseline_corpus` and
  `_compute_threshold_4_3`/`_normalize_phase1_source_id`/`_path_only` from
  `kgmcp_phase1_gateway_runner` (imported, never redefined — AST-verified by
  `test_new_runner_imports_not_reimplements_phase0_pure_helpers`). `_run_direct_context_search`,
  `_run_direct_graphify`, `_run_direct_parity_ledger` (Q3 only, `entry(query_text)` with the raw
  query text as `entry_id`, plus `check_staleness()` when `found` is `False`), and `_run_gateway`
  (`_run_knowledge_context(query=query_text)`, real `route()` call for `providers_selected`) all
  retain full raw content (`raw_results`/`raw_stdout`/`response`) — this ticket's own new
  instrumentation, absent from every predecessor fixture.
- **Step 5 (objective source-completeness):** `_compute_context_search_half()` calls the imported,
  unmodified `_compute_threshold_4_3()` and then overwrites only its returned `"derivation"` key
  with a locally-authored string (the Architecture Review 1st-pass fix) before persistence — the
  function's own hardcoded string falsely claims Phase 0 fixture provenance once fed this ticket's
  own freshly-run data. `_extract_graphify_source_paths()` uses
  `re.findall(r"src=([^\s\]]+)", raw_stdout)`, re-verified for real against all 7 entries' own
  queries (not merely re-trusted from Plan's single sample) — 4 of 7 entries route through
  Graphify (`Q2`, `Q5`, and `Q7`'s dual-provider route), all showing an exact 0-missing/0-extra
  match; the other 3 entries correctly record `graphify_half_status: "not_routed_this_entry"`.
- **Step 6 (reviewer_judgment):** hand-authored per entry after running the script and reading
  both sides' retained raw content directly (gateway `response["context"]`, direct
  `raw_results`/`raw_stdout`/`entry_result`). Followed the falsifiable procedure exactly: every
  entry with a recorded `source_completeness` gap cites at least one real, verbatim recorded
  source_id/path and states whether it mattered; all 7 `rationale` strings are pairwise distinct
  (verified programmatically before commit). A genuine finding surfaced only by this hand-reading
  pass: 2 of the 7 entries' (`Q4`, `Q6`) recorded "missing" sources turned out to be normalization-
  shape false positives (the document was genuinely present in the gateway's context, just under a
  `file:stored_artifacts/<ticket>/investigation.md` id rather than the bare ticket-id `doc_id`
  shape the direct call's raw result carries) — disclosed in the rationale and the results doc,
  never "corrected" in the frozen `_compute_threshold_4_3()` output itself.
- **Step 7 (assembly/fixture):** `run_corpus()` writes
  `tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json` (new file, never merged
  into an existing fixture), including `by_routing_shape` (Step 7's per-query-type grouping
  requirement).
- **Step 8/9 (honest reporting, results doc):** new
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md`. The real,
  disclosed result: the gateway is slower (1.31x-3.76x) and heavier on tokens (1.04x-2.93x) than
  the direct-tool combination for **all 7 of 7 entries** in this fresh, cold-cache run — a real,
  honest finding, not massaged. 6/7 entries judged `direct_equal_or_better`; 1/7
  (`Q3_requirement_completeness`, the newly-live Parity Ledger route) judged `mixed`. No entry
  judged `gateway_equal_or_better`.
- **Steps 10-11 skipped** per instruction: no `proposal.md` "Done" annotation, no `INFRA-354`
  parity ledger entry added this session.
- **Step 12 (tests):** `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` (17 tests,
  including both Architecture-Review-fix tests:
  `test_reviewer_judgment_rationales_are_not_byte_identical_across_entries` and
  `test_reviewer_judgment_cites_a_real_recorded_source_when_source_completeness_shows_a_gap`) and
  `tests/docs/test_phase4_direct_tool_comparison_doc.py` (5 tests). The `INFRA-354` schema-validity
  test named in test_plan.md is not written this session, since Step 11 (creating the entry) is
  explicitly deferred to the Parity phase.

No deviations from the plan's logic — see `staging_artifacts/.../plan.md`'s new "Deviations"
section for the one structural clarification recorded (frozen-file SHA-256 hash list needed 3
additional entries beyond Phase 3's own list, since this ticket also calls
`knowledge_gateway_router.py`/`knowledge_gateway_packet_assembly.py`/`parity_index.py`/
`search_mcp.py` directly and those needed their own frozen-hash guards).

## Test Summary

All new and regression-surface tests run against the real, live implementation (no mocks):

- `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` — 19 tests total (18 fast + 1
  `extra_slow`), all passing. The `extra_slow` test was run separately with
  `--resource-budget large` (38.6s), confirmed zero mutation of `agent-monitoring/`. **Test phase
  correction:** the Implementation-phase count of 17 above was stale — the Test phase closed 2
  further real gaps found during its own review (mechanical verification of the Q4/Q6
  normalization-"false positive" claim, `test_reviewer_judgment_normalization_false_positive_claims_are_mechanically_verified`;
  a corpus-version staleness check, `test_fixture_corpus_version_matches_currently_imported_baseline_corpus`),
  raising this file's real count from 17 to 19. Re-confirmed via
  `pytest tests/tools/test_kgmcp_phase4_direct_tool_comparison.py tests/docs/test_phase4_direct_tool_comparison_doc.py --collect-only -q`
  and a full run during the Parity phase: 24 collected, 24 passed.
- `tests/docs/test_phase4_direct_tool_comparison_doc.py` — 5 tests, all passing.
- Combined new-test total: 24 tests, 24 passed.
- Regression surface (frozen predecessors): `test_kgmcp_measurement_baseline.py`,
  `test_kgmcp_phase1_baseline_comparison.py`, `test_kgmcp_phase2_baseline_recomparison.py`,
  `test_kgmcp_phase3_pilot_acceptance_measurement.py` — 84 passed (1 `extra_slow` deselected).
- Gateway component regression: `test_knowledge_gateway_mcp.py`, `test_knowledge_gateway_router.py`,
  `test_knowledge_gateway_packet_assembly.py`, `test_knowledge_gateway_cache.py`,
  `test_knowledge_gateway_contract_schemas.py`, `test_knowledge_gateway_failure_semantics.py`,
  `test_knowledge_gateway_redaction.py`, `test_parity_index.py`, `test_parity_index_baseline.py`,
  `test_search_mcp.py`, `test_parity_ledger_schema.py` — 323 passed, 5 failed. All 5 failures
  (`test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`,
  `::test_v1_decision_artifact_covers_all_scope_boundaries`,
  `::test_v1_decision_artifact_does_not_authorize_mutation_cli`,
  `test_search_mcp.py::TestMcpJson::test_command_is_python3`,
  `::test_args_point_to_search_mcp`) were confirmed pre-existing and unrelated to this ticket's own
  diff via `git stash` (they fail identically against the pre-Implementation working tree — repo
  environment/config drift, not caused by this ticket's changes).

Total: 24 (new, this ticket, corrected count per above) + 84 + 323 = 431 tests run, 426 passed, 5
pre-existing unrelated failures, 0 new failures introduced by this ticket's own changes.

## Files Changed

- `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py` (new)
- `tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json` (new, committed)
- `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` (new)
- `tests/docs/test_phase4_direct_tool_comparison_doc.py` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` (new)
- `tickets/inprogress/TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON.md` (this file — Status,
  Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed updated)
- `staging_artifacts/TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON/plan.md` (Deviations section
  appended)

No frozen predecessor file, fixture, or gateway/router/cache/parity-adapter source file was
modified (SHA-256-verified by `test_new_runner_never_edits_any_frozen_predecessor_file_or_fixture`).

### Document-Update phase

- `docs/plans/knowledge-gateway-mcp-proposal.md` (§20 Phase 4, fourth bullet — "Compare gateway
  packets against existing direct-tool behavior") — marked **Done**
  (`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`), mirroring the inline annotation style of the
  other 3 Phase 4 bullets. States the real, negative headline result plainly, not softened: gateway
  slower (1.31x-3.76x) and heavier in tokens (1.04x-2.93x) than direct tool use for all 7 of 7
  entries; Graphify-half source-completeness an exact match on all 4 routed entries;
  Context-Search-half showed real narrow drops on 3 of 7 entries after ruling out 2 false
  positives; reviewer judgment 6/7 `direct_equal_or_better`, 1/7 (`Q3`) `mixed`, 0/7
  `gateway_equal_or_better`. Points to
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` for full detail.
  With this bullet marked Done, all 4 of §20 Phase 4's bullets now individually carry a `**Done**`
  annotation — no broader "Phase 4 complete" characterization was added anywhere; that remains an
  explicit human-reviewer/epic-closure call, out of scope for this ticket.
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` — created by
  Implement, not modified by this phase; verified content against the annotation above.
- Investigation's "Docs Requiring Update" list was reviewed and found already correctly scoped: it
  named `docs/plans/knowledge-gateway-mcp-proposal.md` (this phase's edit, above),
  `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` (already created
  by Implement, cite-only here), and `docs/parity_ledger/infrastructure.yaml` (correctly assigned
  to the Parity phase, not touched here — `docs/parity_ledger/*.yaml` is doc-updater's exclusive
  out-of-scope territory per role definition). No restructuring was needed.

## Completion Summary

Delivered a real, live, paired comparison of the Knowledge Gateway MCP against calling Context
Search / Graphify / the Parity Ledger adapter directly, across all 7 frozen corpus entries, fresh
(no Phase 0-3 fixture reuse — `INFRA-351`/`INFRA-352` made every historical Q3 and general-drift
number stale, per Step 1's decision). The honest, real result is a **negative** outcome for the
gateway: for **all 7 of 7 entries** it was slower (1.31x-3.76x) and heavier in tokens
(1.04x-2.93x) than the direct-tool combination in this fresh, cold-cache run, and the hand-written,
mechanically-verified `reviewer_judgment` field found direct tools equal-or-better on 6 of 7
entries, mixed on the 7th (`Q3_requirement_completeness`), and the gateway equal-or-better on
**none**. This is the delivered value of the ticket — a trustworthy, honest, unspun number, not a
result engineered to favor the gateway. No entry was excluded or redefined to force a more
favorable aggregate (Step 8's guard, `test_no_query_type_disadvantage_is_silently_excluded_or_redefined`).

Architecture Review (2 passes) required and confirmed 2 real pre-implementation fixes before
approval: (1) a false provenance string in the reused `_compute_threshold_4_3()` output — its
hardcoded `"derivation"` field claimed Phase 0 fixture provenance even when fed this ticket's own
freshly-run direct-call data; corrected by overwriting only that string post-call
(`_compute_context_search_half()`, `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py:265`,
override at lines 282-287), never touching the imported comparison logic itself; and (2) an
unfalsifiable subjective `reviewer_judgment` field, made falsifiable by Step 6's concrete
procedure — every entry with a recorded `source_completeness` gap must cite a real, verbatim
source_id/path and state whether it mattered, and no two entries' `rationale` strings may be
byte-identical, enforced by `test_reviewer_judgment_cites_a_real_recorded_source_when_source_completeness_shows_a_gap`
and `test_reviewer_judgment_rationales_are_not_byte_identical_across_entries`. Architecture-Verify
independently confirmed both fixes applied against the real diff, and confirmed via SHA-256
content-hash snapshot that no frozen predecessor runner, fixture, or gateway/router/cache/parity-
adapter source file was modified by this ticket's own diff.

The Test phase closed 2 further real gaps beyond Architecture-Verify's sign-off: mechanical
verification of the Q4/Q6 normalization-"false positive" claim recorded in Implementation Notes/
Deviations (`test_reviewer_judgment_normalization_false_positive_claims_are_mechanically_verified`)
and a corpus-version staleness check (`test_fixture_corpus_version_matches_currently_imported_baseline_corpus`).
This raised the new-test count from 17 to 19 in
`tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`; combined with the 5 tests in
`tests/docs/test_phase4_direct_tool_comparison_doc.py`, the real, re-confirmed total is **24
tests, 24 passing** (re-verified during this Parity phase via
`pytest tests/tools/test_kgmcp_phase4_direct_tool_comparison.py tests/docs/test_phase4_direct_tool_comparison_doc.py -v`).
The Test Summary section above has been corrected in this phase to state 24 (was stale at 22 from
the Implementation hand-off).

**Parity phase complete:** added `INFRA-354` to `docs/parity_ledger/infrastructure.yaml`
(`status: verified`, `priority: P2`, `proof_type: differential`) via the schema-validating
`write_entry()`, followed by a separate, visible `python3 tools/parity_index.py build`.
`INFRA-353` was confirmed the last existing id before writing. Unlike `INFRA-344`/`350`/`353`'s
"methodology, not conclusion" framing, `INFRA-354` certifies the real measured comparison result
itself — because this ticket's actual job was to report the real gateway-vs-direct comparison,
whatever it turned out to be, and the honest, negative, unspun result IS what is certified as
correct and real. `v2_evidence` cites the runner's key functions by line number
(`_compute_context_search_half:265`, derivation-override:282-287,
`_extract_graphify_source_paths:256`, `run_corpus:373`), the new fixture, and the results doc.
`support_boundary` states the headline result plainly and cites both Architecture-Review-required
fixes as evidence the measurement itself is trustworthy, not fabricated or dressed-up. A quick
citation-drift check confirmed no existing `tools/` file this ticket cites in prior entries was
touched by this ticket's own diff (confirmed empty per Architecture-Verify's frozen-file
SHA-256 check) — no drift risk on prior code-citing entries. (Note, out of scope for this ticket:
`git status` shows unrelated uncommitted changes to `tools/knowledge_gateway_router.py` and
`tools/knowledge_gateway_packet_assembly.py` in the working tree — these belong to the dependency
ticket `TCK-20260816-KGMCP-P4-PARITY-ADAPTER`'s own already-DONE work sitting uncommitted, not to
this ticket's diff; this ticket's runner calls but never edits either file.)

No `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`, or `.claude/agents/*.md` file was
touched by this ticket at any phase, and no gateway/router/cache/Parity-adapter source file was
edited — measurement-only, exactly as scoped.

This is the fourth and final child ticket of
`tickets/todos/knowledge-gateway-mcp-phase4/TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC.md` to
reach DONE, alongside `TCK-20260816-KGMCP-P4-PARITY-ADAPTER`,
`TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`, and
`TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION` — noted here as a fact only; no
"Phase 4 complete" characterization is made by this ticket or its parity entry, per Out of Scope
and the epic's own human-reviewer-call precedent.
