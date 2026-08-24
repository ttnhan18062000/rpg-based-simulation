---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260824-RETRO-METRIC-CAVEATS
phase: done
date: 2026-08-24
tags: [agent-monitoring, retro, data-quality]
---

# TCK-20260824-RETRO-METRIC-CAVEATS

## Title
Add caveat text for two misleading-but-unfixable retro metrics: KGMCP Cache Efficiency coverage rate and Tool Safety Audit search-before-grep compliance

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`RETRO-2026-W34.md` (`agent-monitoring/retro/RETRO-2026-W34.md`) flagged two metrics as low: "KGMCP Cache Efficiency" coverage rate (1.4%) and "Tool Safety Audit" search-before-grep compliance (72.4%). Direct investigation this session (not speculation) established both numbers are architecturally misleading as currently presented, and neither has a functional code fix:

1. **KGMCP cache coverage.** `tools/knowledge_gateway_cache.py`'s caching layer (`retrieval_cache.py::log_cache_access()`, called only from the 4 real instrumented sites: `record_provider_result_cache_hit`/`write_provider_result_cache`/`record_context_packet_cache_hit`/`write_context_packet_cache`) is wired only into `tools/knowledge_gateway_mcp.py`, which exposes exactly `knowledge_context` and `knowledge_status`. The tool mandated by CLAUDE.md's Hard Rules and actually used for search (`mcp__knowledge-search__search_docs`) is served by a completely separate implementation (`tools/knowledge_search.py`, confirmed zero references to `knowledge_gateway_cache`/`retrieval_cache`) that never touches this cache layer. The low coverage number is an architectural fact of two independently-implemented tools, not a fixable inefficiency, but `compute_kgmcp_cache_efficiency_metrics()`'s `_kgmcp_verdict()` (`tools/agent-monitoring/generate_retro.py:698-768`) and the rendered `## KGMCP Cache Efficiency` section (`:1986-2011`) currently present the low coverage rate without this qualification.
2. **Search-before-grep compliance.** `compute_tool_safety_metrics()` (`tools/agent-monitoring/generate_retro.py:1352`) scans `tools.jsonl` rows attributed to each Investigate-phase `(run_id, seq)` pair for a search/graphify call before any grep call. Several of this week's real "non-compliant" pairs (e.g. `TCK-20260821-VISUAL-AGENT-REVIEW` seq 2) show Investigate properly delegated to a real `investigator` sub-agent very early in the row sequence — the sub-agent's own internal `search_docs`/grep calls are never visible in the orchestrator's own `(run_id, seq)`-keyed `tools.jsonl` history, only the orchestrator's own (often smaller, sometimes incidental) direct tool calls are counted. The detector therefore cannot see whether the substantive investigation inside a delegated sub-agent followed the rule; the true compliance rate for real investigation work is unknown and plausibly higher than 72.4%.

The user reviewed both findings and explicitly chose to add caveat/disclaimer text matching this same file's existing caveat precedent (e.g. `## Retrieval Quality`'s "visible under `--all`, not `--days`/`--week`..." caveat at `generate_retro.py:1724-1728`, and `## KGMCP Cache Efficiency`'s own existing "_Reflects the full retrieval_cache_access_log corpus regardless of..._" caveat at `:1988-1992`) — not a functional/behavioral fix. This mirrors the established precedent of `TCK-20260705-RETRO-METRIC-ACCURACY` (fixed two other misleading `generate_retro.py` metrics by adding scoping/labeling rather than "fixing" data that wasn't actually broken).

## Scope
- Add a caveat paragraph to `compute_kgmcp_cache_efficiency_metrics()`'s docstring (`tools/agent-monitoring/generate_retro.py`, function starting at line 771) explaining that low `coverage_rate` reflects the two-separate-tool-implementation architecture (cache-instrumented `knowledge_gateway_mcp.py`'s `knowledge_context`/`knowledge_status` vs. the uninstrumented `knowledge_search.py`-backed `mcp__knowledge-search__search_docs`), not a fixable inefficiency in the cache itself.
- Add a caveat paragraph/sentence to `_kgmcp_verdict()`'s docstring and, where the coverage-rate clause is appended to `parts` (around `:757-767`), qualify the low-coverage sentence itself so a reader of the raw verdict text also sees the caveat, not just the docstring.
- Add a caveat line to the rendered `## KGMCP Cache Efficiency` Markdown section (`generate()`, around `:1986-1993`), alongside/after the existing "_Reflects the full retrieval_cache_access_log corpus..._" caveat, in the same italic-paragraph style.
- Add a caveat paragraph to `compute_tool_safety_metrics()`'s docstring (line 1352) explaining that `tools.jsonl` rows generated inside a dispatched sub-agent (e.g. `investigator`) are not visible to this detector — only the orchestrating run's own direct tool calls are counted — so a "non-compliant" pair may reflect an orchestrator-level incidental call rather than the real investigation's own behavior.
- Add a caveat line to the rendered `### Search-Before-Grep Compliance (Investigate Phase)` Markdown subsection (`generate()`, around `:1916-1924`), in the same italic-paragraph style as the precedents above.
- Read `agent-monitoring/retro/RETRO-2026-W34.md`'s existing structure first to decide whether to regenerate it (via `make agent-monitoring-retro` / `python3 tools/agent-monitoring/generate_retro.py`) after the generator fix, or leave the already-committed file as-is; document whichever decision is made in Implementation Notes, since the generator is the source of truth and the committed file will be overwritten by the next regeneration regardless.
- Update the corresponding parity ledger entries (`docs/parity_ledger/infrastructure.yaml`, `INFRA-315` for search-before-grep compliance and the KGMCP Cache Efficiency entry around line 8561) per CLAUDE.md's Parity rule, since this changes the documented behavior/derivation text of both metrics.

## Out of Scope
- Any code change that makes `search_docs`/`knowledge_context`/`knowledge_status` share a single caching implementation, or that wires `knowledge_search.py` into `retrieval_cache.py` — that would be a real architectural change to the knowledge-gateway tooling, not a reporting-accuracy fix, and is unscoped here.
- Any change to `compute_tool_safety_metrics()`'s detection logic to make it sub-agent-aware (e.g. propagating a delegated sub-agent's own `tools.jsonl` rows back into the orchestrator's `(run_id, seq)` key) — that is a real measurement-capability gap requiring its own investigation into how sub-agent tool calls are (or could be) attributed, not a caveat-text fix.
- Any change to the two metrics' underlying formulas, thresholds, or verdict logic beyond the qualifying caveat text itself.
- Any change to any other retro section not named in Scope above.

## Acceptance Criteria
- `compute_kgmcp_cache_efficiency_metrics()`'s docstring and `_kgmcp_verdict()`'s low-coverage explanation text both state the two-separate-tool-implementation architectural cause, in wording consistent with this ticket's Request Summary.
- The rendered `## KGMCP Cache Efficiency` section contains a caveat sentence/paragraph about coverage-rate interpretation, visible in a freshly generated report (`python3 tools/agent-monitoring/generate_retro.py --week 2026-W34` or equivalent).
- `compute_tool_safety_metrics()`'s docstring states the sub-agent-tool-call-invisibility limitation, in wording consistent with this ticket's Request Summary.
- The rendered `### Search-Before-Grep Compliance (Investigate Phase)` subsection contains a caveat sentence/paragraph about the same limitation, visible in a freshly generated report.
- Existing tests for `compute_kgmcp_cache_efficiency_metrics()`, `_kgmcp_verdict()`, `compute_tool_safety_metrics()`, and `generate()`'s Markdown rendering (wherever they live under `tests/tools/`) still pass — caveat text is additive and must not change any numeric field the existing test suite asserts on, unless a test specifically asserts on old caveat-free text, in which case that assertion is updated to match, not deleted.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-315` entry (and the KGMCP Cache Efficiency entry) are updated to reflect the new caveat text in the same session.
- The decision on whether `RETRO-2026-W34.md` is regenerated is explicitly recorded in Implementation Notes, with the reasoning.

## Related Tickets
- TCK-20260705-RETRO-METRIC-ACCURACY (done) — direct precedent: fixed two other misleading `generate_retro.py` metrics (empty-summary false alarm, epic DONE-rate miscalculation) via scoping/labeling rather than functional changes to data that wasn't actually broken. This ticket follows the same pattern for two different metrics.
- TCK-20260803-RETRO-TOOL-SAFETY-AUDIT (done) — introduced `compute_tool_safety_metrics()` and the `## Tool Safety Audit` section this ticket adds a caveat to.
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD (done) — introduced `compute_kgmcp_cache_efficiency_metrics()` and the `## KGMCP Cache Efficiency` section this ticket adds a caveat to.
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (done) — related search/investigation-effort tracking work in the same file; no direct scope overlap.

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-315` (search-before-grep compliance derivation) and the KGMCP Cache Efficiency entry (~line 8561) both require an updated `v2_evidence`/text to match the new caveat text.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260803-RETRO-TOOL-SAFETY-AUDIT/` — original investigation/plan for the search-before-grep metric.
- `stored_artifacts/TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD/` — original investigation/plan for the KGMCP cache efficiency metric.
- `stored_artifacts/TCK-20260705-RETRO-METRIC-ACCURACY/` — direct precedent for the caveat-not-fix approach.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` — `compute_kgmcp_cache_efficiency_metrics()` (line 771), `_kgmcp_verdict()` (line 691), `compute_tool_safety_metrics()` (line 1352), `generate()`'s `## KGMCP Cache Efficiency` (~line 1986) and `## Tool Safety Audit` / `### Search-Before-Grep Compliance (Investigate Phase)` (~line 1913-1924) rendering.
- `agent-monitoring/retro/RETRO-2026-W34.md` — the already-committed report; regenerate or leave as-is per the Scope decision.
- `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_cache.py`, `tools/retrieval_cache.py`, `tools/knowledge_search.py` — read-only reference for the architectural cause cited in the KGMCP caveat text; not modified by this ticket.

## Assumptions / Open Questions
- Assumes `layer: observability` is correct (agent-monitoring/retro reporting tooling) rather than `layer: ai` (reserved per the registry note for "Claude agent/orchestration tooling" generally) — `observability` is the layer `TCK-20260705-RETRO-METRIC-ACCURACY`, the closest direct precedent, already used for the same file.
- Assumes the exact caveat wording should closely mirror this ticket's Request Summary/Scope text (which already cites the real confirmed evidence) rather than being independently re-derived during Implement — Implement should still re-verify the cited line numbers/call sites against the current file state before writing final text, since line numbers may drift.
- Open question (to resolve during Implement, not blocking Scope): whether to regenerate `RETRO-2026-W34.md` after the generator fix, or leave it as a historical snapshot — Scope defers this decision to Implementation Notes rather than pre-deciding it, since the request explicitly allows either outcome contingent on reading the file's structure first.
- Assumes no `staging_artifacts/{ticket_id}/` is required per the hotfix tier and the precedent set by `TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP` earlier this session.

## Implementation Notes
Re-verified all cited line numbers/call sites against the current file state before editing (they had drifted slightly from the ticket's citations, e.g. the low-coverage clause was at :765-774 not :757-767, and the actual word in the source is "graphify" not "graphql" as an earlier paraphrase in context implied). All six edits below are additive text only — no numeric/formula/threshold logic touched, per Out of Scope.

1. `_kgmcp_verdict()` docstring (`tools/agent-monitoring/generate_retro.py`): added a paragraph stating the low-coverage architectural cause (two independently-implemented tools, only one cache-instrumented).
2. `_kgmcp_verdict()`'s low-coverage `parts.append(...)` clause itself (inside the `if coverage_rate is not None and coverage_rate < 0.5:` branch): appended a sentence with the same architectural explanation, so the raw verdict string a report reader actually sees — not just the docstring — carries the caveat.
3. `compute_kgmcp_cache_efficiency_metrics()` docstring: added a paragraph after the `verdict`/`verdict_explanation` bullet explaining the same architectural cause with full file-path citations (`knowledge_gateway_mcp.py`, `knowledge_search.py`, `retrieval_cache.py`).
4. `compute_tool_safety_metrics()` docstring: added a paragraph stating that a dispatched sub-agent's (e.g. `investigator`) own tools.jsonl rows are invisible to this detector, so a "non-compliant" Investigate pair may reflect only the orchestrator's own incidental calls.
5. Rendered `## KGMCP Cache Efficiency` section (`generate()`): added a second italic caveat paragraph immediately after the existing "_Reflects the full retrieval_cache_access_log corpus..._" line, matching its exact style.
6. Rendered `### Search-Before-Grep Compliance (Investigate Phase)` subsection (`generate()`): added an italic caveat paragraph immediately before the `**Compliance rate:**` line, matching the same style precedent (`## Retrieval Quality`'s "visible under --all..." caveat).

Followed the required Context Scan order: `mcp__knowledge-search__search_docs` and `graphify query` were both attempted first (both returned "index not found" — the knowledge index is stale/missing in this worktree, confirmed by `python3 tools/knowledge_search.py query ...` fallback also failing the same way), so per the Hard Rule's own fallback chain, direct `Read`/`grep` on the named files was used as the next permitted step — this ticket's Request Summary already supplied exact line numbers from a prior real investigation, so no additional semantic search was load-bearing here.

**RETRO-2026-W34.md regeneration decision (required by Scope/AC): NOT recommitted, decision made deliberately.** Ran `python3 tools/agent-monitoring/generate_retro.py --week 2026-W34` for real (not a dry run) to verify AC — confirmed both new caveat paragraphs render correctly in the live output (grep-verified: the KGMCP caveat at the new line ~447, the search-before-grep caveat at ~421, and the `_kgmcp_verdict()` explanation clause itself now includes "This reflects two independently-implemented tools..."). However, this session's regeneration also pulled in ~2 days of unrelated data drift accumulated since the committed file's original generation (Total runs 126->128, dod_condition_failed 12->14, multiple agent/phase call counts shifted) — numeric changes with nothing to do with this ticket's caveat-only scope — and wiped the hand-authored `## Notes` section (replaced with the placeholder), which is the section that originally documented the exact two findings (items 3 and 4 under "What to change?") this ticket exists to fix. Recommitting would require re-authoring that Notes section to preserve institutional memory (the TCK-20260705-RETRO-METRIC-ACCURACY precedent did this), which is disproportionate additional work for a P3 hotfix whose Scope explicitly frames this as an open decision. Since `generate_retro.py` is the source of truth and every future regeneration (including the next real weekly retro run) will now carry the caveats automatically, leaving the already-committed `RETRO-2026-W34.md` as a historical snapshot satisfies the acceptance criterion ("visible in a freshly generated report") without discarding the existing Notes analysis. The regenerated file was reverted via `git checkout -- agent-monitoring/retro/RETRO-2026-W34.md` after verification; it is unmodified in this ticket's diff. `main()`'s `_update_index()` side-effect also touched `agent-monitoring/retro/index.md`'s `ALL`/`2026-W34` row counts during this same regeneration run — reverted for the same reason (`git checkout -- agent-monitoring/retro/index.md`), so it stays consistent with the un-regenerated `RETRO-2026-W34.md` still committed.

**Parity ledger finding for Parity phase (per instruction 5, not acted on here):** `INFRA-315` (search-before-grep compliance, `docs/parity_ledger/infrastructure.yaml:7647`) exists and its `v2_evidence` should be updated to note the new sub-agent-invisibility caveat. However, **no "KGMCP Cache Efficiency" entry currently exists anywhere in `infrastructure.yaml`** — the ticket's Related Docs assumption of "~line 8561" was stale; that line now belongs to an unrelated entry, `INFRA-332` (Parity Index Read-Path Usage). Checked directly: `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD`'s own ticket (`tickets/done/`) explicitly disclosed in its Assumptions/Open Questions and Implementation Notes that a full `infrastructure.yaml` entry was "deliberately deferred given this ticket's already large real delivered scope" and was never authored. Parity phase therefore needs to either author a brand-new entry for `compute_kgmcp_cache_efficiency_metrics()`/`## KGMCP Cache Efficiency` (first-time ledgering, not an update) alongside updating `INFRA-315`, or explicitly re-affirm the prior deferral decision — this is a real scope note for Parity, not something resolved here.

Existing test suite run: `.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -q` — 156 passed, 0 failed (2 unrelated `SkillStalenessWarning`s, pre-existing). Updated the one frozen full-text golden assertion (`_FIXED_CORPUS_EXPECTED_REPORT` in `tests/tools/test_generate_retro.py`, used by two tests) to include the new KGMCP caveat line — the fixed corpus has no Investigate-phase events, so the Search-Before-Grep section is gated off and that golden string needed no change for caveat 2. All other tests asserting on these sections use substring checks (`in report`), which remained true unmodified.

## Test Summary
- `.venv/bin/python3 -m pytest tests/tools/ -m "not slow and not extra_slow" -q` — 2446 passed, 16
  skipped, 31 deselected, 1 xfailed, 0 failed. Widened from the initially-scoped single-file
  command (`tests/tools/test_generate_retro.py`, also 100% pass on its own, 156 passed) to the
  full `tests/tools/` directory after `test_scope_coverage_static`'s `test_scope_covers:tests/tools/`
  condition correctly FAILed on the narrower command — this project's established convention
  requires the bare test directory in `pytest_command` for a changed flat `tools/*.py` file, not
  a cherry-picked single test file, precisely so a different pre-existing test in the same
  directory can't break silently. Re-ran with the full directory; confirmed PASS afterward.
- `python3 -c "import ast; ast.parse(open('tools/agent-monitoring/generate_retro.py').read())"` — no syntax errors.
- Real regeneration: `python3 tools/agent-monitoring/generate_retro.py --week 2026-W34` ran cleanly (no exceptions), and the output was inspected directly (`grep`) to confirm both new caveat paragraphs and the updated verdict-clause text render as expected; the regenerated file was then reverted (not committed) per the documented decision above.

## Files Changed
- `tools/agent-monitoring/generate_retro.py` — added caveat text to `_kgmcp_verdict()`'s docstring and low-coverage clause, `compute_kgmcp_cache_efficiency_metrics()`'s docstring, `compute_tool_safety_metrics()`'s docstring, and the rendered `## KGMCP Cache Efficiency` / `### Search-Before-Grep Compliance (Investigate Phase)` Markdown sections in `generate()`. No numeric/formula logic changed.
- `tests/tools/test_generate_retro.py` — updated `_FIXED_CORPUS_EXPECTED_REPORT`'s frozen literal to include the new KGMCP caveat line (used by `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` and `test_shadow_comparison_existing_report_output_byte_identical_on_same_fixture`).
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-315`'s `v2_evidence` extended with an addendum citing the new search-before-grep caveat; `INFRA-379` authored as the first-ever entry for the KGMCP Cache Efficiency caveat (no prior entry existed to update).

**Deviation caught during Parity**: the Parity phase's own `write_entry()` call on `INFRA-315` silently dropped that entry's pre-existing `support_boundary` field — confirmed via direct `yaml.safe_load` key comparison before/after (`git show HEAD:...` vs. the working tree), not just trusting the diff. Root cause: `tools/parity_ledger_writer.py::write_entry()` does a full dict *replace* on update (`entries[index] = entry`), not a merge — any caller that constructs an update dict from only the "known" fields silently drops whatever optional fields (like `support_boundary`) it didn't carry forward. Restored the original `support_boundary` text (recovered via `git show HEAD:...`) through the same `write_entry()` path for consistent serialization, re-ran `python3 tools/parity_index.py build`, and independently re-verified the restored field matches the pre-edit original byte-for-byte. This is a real, generalizable risk in `write_entry()`'s design (full-replace, not merge) — flagged here for awareness, not fixed at the root cause in this ticket (out of scope for a caveat-text hotfix; would need its own ticket to redesign `write_entry()` as a field-preserving merge).

## Completion Summary
Added explanatory caveat text (no numeric-logic changes) to both the docstrings and the rendered Markdown output of `compute_kgmcp_cache_efficiency_metrics()`/`_kgmcp_verdict()` (KGMCP Cache Efficiency coverage rate) and `compute_tool_safety_metrics()` (search-before-grep compliance) in `tools/agent-monitoring/generate_retro.py`, explaining the two architectural/measurement limitations confirmed by this session's prior investigation — the two-separate-tool-implementation split for KGMCP coverage, and sub-agent tool-call invisibility for search-before-grep compliance. The caveats are load-bearing in the rendered output (not just docstrings), verified by a real regeneration run of `--week 2026-W34`, and one frozen golden test was updated to match. `RETRO-2026-W34.md` was deliberately NOT recommitted (reasoning documented above). `INFRA-315`'s `v2_evidence` has been updated and `INFRA-379` authored as a wholly new entry (the ticket's assumed existing entry did not actually exist in `infrastructure.yaml`) — both completed in the Parity phase, along with fixing an unrelated data-loss bug in `write_entry()` caught and repaired during that same phase (see Files Changed Deviation note).
