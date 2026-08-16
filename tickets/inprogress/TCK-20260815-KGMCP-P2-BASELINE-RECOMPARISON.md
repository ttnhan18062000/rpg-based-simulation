---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON
phase: open
date: 2026-08-15
tags: [ai, mcp, testing]
---

# TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON

## Title
Honestly re-measure the real cache-hit path against Phase 0's baseline and predeclared thresholds

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` honestly found all 3 §4 thresholds FAIL against
Phase 1's necessarily-cold gateway. This ticket is the other half of Phase 2's own bargain: once
`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` lands a real cache, run the same 7-entry corpus
through the gateway twice per entry (first call cold, second call warm/cached) and report,
honestly, whether §4.1's latency threshold is now met on the warm path — and, separately and
without assuming caching fixes it, whether §4.2's token-reduction threshold is met.

## Scope
- Reuse the exact same frozen 7-entry corpus (`tools/agent-monitoring/kgmcp_baseline_corpus.py`)
  and the exact same Phase 0 baseline fixture as the comparison target — never a modified corpus,
  never a different baseline.
- For each corpus entry, run the real gateway TWICE: once cold (first call, cache miss expected),
  once warm (second call, cache hit expected) — recording real `time.perf_counter()` timings for
  both, and recording whether the second call was genuinely served from cache (not just assumed).
- Compute §4.1 (latency) against the WARM path numbers — this is the fair comparison Phase 1's own
  cold-only measurement couldn't make. Report honestly whether the threshold is now met.
- Compute §4.2 (token reduction) against BOTH the cold and warm path numbers — do not assume the
  warm path automatically satisfies this threshold; report the real numbers for both.
- Compute §4.3 (no-regression-recall) again, reusing `TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-
  TRUNCATION`'s now-fixed evidence-ID normalization — expect recall for the single-provider-routed
  entries (Q2/Q5) to still structurally miss for the same, already-documented architectural reason
  (routing, not caching) — report this honestly again, do not expect Phase 2 to fix it.
- Write a new results doc and committed fixture, following
  `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s own established pattern (never editing that
  ticket's historical record).

## Out of Scope
- Redefining any threshold to force a pass, or excluding any of the 7 entries — the same Gate
  Integrity discipline `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` established applies here with
  equal force.
- Fixing the token-reduction threshold if it's still missed after this measurement — this ticket
  measures and reports; if a fix is warranted, that's a separate, later ticket a human reviewer
  scopes based on this ticket's honest findings.
- Fixing the routing-caused recall miss on Q2/Q5 — architectural, out of Phase 2's scope entirely
  (as the Phase 2 epic's own text already states).
- Any change to `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or the cache read/write code built by the
  dependency ticket — this ticket is measurement-only.

## Acceptance Criteria
- [x] Each of the 7 corpus entries is run twice (cold + warm) against the real gateway, with the
      warm call's cache-hit status independently verified (not assumed) via a real check (e.g. a
      spy/counter proving the provider round-trip was skipped).
- [x] §4.1 is computed against the warm-path numbers and reported honestly, whatever the result.
- [x] §4.2 is computed against both cold and warm numbers separately — no assumption that caching
      alone satisfies it.
- [x] §4.3 is recomputed with the now-fixed evidence-ID normalization; the Q2/Q5 architectural
      miss (if still present) is reported with the same honest routing-design narrative Phase 1's
      own results doc used, not silently dropped or re-explained away.
- [x] If any threshold is missed, the ticket's own Completion Summary states this plainly — no
      threshold is redefined, no entry excluded, and Phase 2 is not characterized as more successful
      than the real numbers support.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (parent; this ticket closes its acceptance loop)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (dependency; supplies the real cache-hit path to
  measure)
- TCK-20260815-KGMCP-P1-BASELINE-COMPARISON (DONE; supplies the corpus, Phase 0 baseline fixture,
  and the honest all-FAIL cold-path result this ticket extends with a warm-path measurement)
- TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION (DONE; the evidence-ID fix this ticket's §4.3
  recomputation relies on)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (the Phase 1 result
  this ticket extends, never edits)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (frozen corpus, reused verbatim)
- `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` (the Phase 1 runner this ticket's own
  runner mirrors the shape of, extended for cold+warm double-calling)

## Assumptions / Open Questions
- Whether this ticket's own runner should be a new file or an extension of
  `kgmcp_phase1_gateway_runner.py` — Investigate should decide based on how much of the existing
  runner's logic is directly reusable versus needing a genuinely different cold/warm double-call
  shape.

## Implementation Notes

Implemented exactly per the approved `plan.md`'s 7 steps. **DD1 was ruled by Architecture Review in
favor of option (b) — exact Phase 1 request-shape parity, no `budget_tokens` override — before
Implement began**, and this is the only shape implemented; no fallback to option (a) was written
anywhere, at any point.

- **Step 1/Step 2/Step 3 (`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`, new file):**
  new `sys.modules` key `"kgmcp_phase2_recomparison_gateway"` (DD8), imports only
  `_normalize_phase1_source_id`/`_path_only`/`_compute_threshold_4_3` from
  `kgmcp_phase1_gateway_runner.py` (DD7) plus `kgmcp_baseline_corpus.CORPUS`/`CORPUS_VERSION` and
  `tools.knowledge_gateway_redaction` (plain package import, DD3). Per-entry cold+warm double-call
  loop (`_run_single_entry()`) installs two plain-Python attribute-reassignment spies — one on
  `_kgpa.assemble_packet` (provider-round-trip count) and one on
  `_kgr_redaction.evaluate_write_candidate` (captures the real `WriteDecision.rejection_category`,
  since `perform_cache_write()` itself always returns `None` and discards it, DD3) — both restored
  in `finally`. `cache_status_warm` requires BOTH the spy count (`== 1`) AND a direct SQL
  `hit_count` delta read (`== 1`) to agree (DD2); any disagreement is recorded in a `signal_anomaly`
  field, never silently resolved one way. `compute_lookup_identity()` is called (never
  reimplemented, DD4) to derive the exact `(query_hash, repo_branch_scope)` key for the SQL reads.
  §4.1 computed against `warm_call_wall_time_ms` only (never cold). §4.2 computed independently for
  cold and warm via `_kgpa.kgmcp_char_heuristic_v1()` on each response's own `json.dumps()`. §4.3
  computed once, from the cold response, via the imported `_compute_threshold_4_3` (Plan Step 3's
  decision — a genuine hit's content equals its cold source, and no entry ever reached a genuine
  hit in the real run anyway). A `built_at` snapshot of `knowledge-index/manifest.json` is taken
  before and after the full 7-entry loop; the runner raises if it changed (Risk #6 guard).
- **Real run executed by hand** (`python3 tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`),
  once, writing the committed fixture. **Real, measured result: 0/7 genuine cache hits.** Every one
  of the 7 entries' cold response payload exceeded `MAX_PAYLOAD_BYTES = 8192`, and
  `evaluate_write_candidate` rejected every write with `rejection_category ==
  "oversized_payload"` — captured by the spy on all 7 entries, with zero `signal_anomaly`/
  `cold_call_anomaly` occurrences (both cache-hit-verification signals agreed on every entry: spy
  count 2, SQL delta 0, for all 7). This exactly matches the plan's Anti-Drift Notes prediction.
- **Step 4 (`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`, new):** written
  directly by the real run above, `json.dumps(..., indent=2, sort_keys=True)`. Every entry carries
  `budget_tokens_used: 4000`, `cache_status_warm`, `cache_write_rejection_reason`, both
  `hit_count_*`/`cache_hit_count_delta` fields, `threshold_4_1_latency` (warm-only),
  `threshold_4_2_cold_tokens`/`threshold_4_2_warm_tokens` (independent), `threshold_4_3_recall_cold`,
  and a non-empty `derivation` string.
- **Step 5 (`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`, new):**
  mirrors `phase1_baseline_comparison.md`'s structure; states DD1's Architecture Review ruling,
  the real per-entry `oversized_payload` finding with byte-size-vs-cap table, per-threshold
  PASS/FAIL tables with real numbers, the Q1 warm-speedup honest caveat (a real but
  caching-unrelated warm-process effect on an entry that structurally never cached), the DD5
  cold-vs-warm token comparison (no entry reached a genuine hit, so DD5's prediction was never put
  to the test; Q2's warm token count came in below its cold count, explained as ordinary
  `graphify` run-to-run variation, not a DD5 violation since DD5 only applies to genuine hits), and
  the Q1/Q3/Q4/Q6/Q7 recall-count comparison against Phase 1's own recorded counts (identical,
  since the doc_id fix was already fully reflected by Phase 1's own measurement).
- **Step 6 (`tests/tools/test_kgmcp_phase2_baseline_recomparison.py`, new):** all 17 tests named in
  `test_plan.md`'s "New Tests Required" section (the ticket brief's "15" was an approximate recap;
  `test_plan.md` itself — the literal spec — names 17). 16/17 pass; see Test Summary for the one
  pre-existing, non-regression failure and its root cause.
- **Step 7:** `docs/plans/knowledge-gateway-mcp-proposal.md` — appended a new results-narrative
  paragraph after the Phase 2 section's final bullet (before the Phase 3 header), stating this
  ticket's real §4.1/§4.2/§4.3 outcome, citing the new doc/fixture by path. **The parity ledger
  entry (`INFRA-344`, `docs/parity_ledger/infrastructure.yaml`) was deferred to the Parity phase**,
  per the orchestrator's explicit instruction overriding Step 7's literal text for that one file —
  not opened or edited by Implement.

See `staging_artifacts/TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON/plan.md`'s new "Deviations"
section (appended, bottom of file) for full detail on: (1) DD1's confirmed resolution, (2) a
docstring-only fix to avoid literally spelling `MagicMock` (tripped the runner's own AST/string
guard against its own prose, not against real mocking usage — fixed by rephrasing), and (3) the one
pre-existing, non-regression test failure explained in Test Summary below. No frozen file listed in
Scope/Out-of-Scope/Anti-Drift Hazards was edited; no threshold formula was redefined; no corpus
entry was excluded, substituted, or cherry-picked.

## Test Summary

Scoped command run: `pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py -v` —
**16 passed, 1 failed** (45.96s; includes a full real 7-entry cold+warm run inside
`test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`, which passed).

The one failure, `test_no_frozen_kgmcp_dependency_edited`, is a **pre-existing, non-regression
condition, not caused by this ticket**: `git diff --stat HEAD` already includes
`tools/knowledge_gateway_mcp.py`/`tools/knowledge_gateway_redaction.py`/
`tools/knowledge_gateway_cache.py`/`tools/retrieval_cache.py` from already-`Done`, uncommitted
sibling Phase 2 tickets that landed *before* this ticket's own work began — confirmed via
`git status --porcelain` scoped to exactly those 4 paths, which shows zero contribution from this
ticket's own diff. Independently confirmed by running Phase 1's own, previously-passing, identical
guard (`test_kgmcp_phase1_baseline_comparison.py::test_no_frozen_kgmcp_dependency_edited`) in
isolation: it **also** fails today, for the identical reason, with zero involvement from this
ticket. Per CLAUDE.md's Gate Integrity Hard Rule, this was left exactly as speced (mirroring Phase
1's own `git diff --stat HEAD` convention verbatim per test_plan.md) rather than weakened to force
a pass — see plan.md's Deviations item 3 for full detail and the open question this raises for
Verify (whether the guard's git-diff base assumption needs revisiting given this branch's
multi-ticket uncommitted-accumulation workflow, a repo-wide condition, not specific to this ticket).

Broader regression surface run: `pytest tests/tools/test_kgmcp_phase1_baseline_comparison.py
tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_knowledge_gateway_mcp.py
tests/tools/test_knowledge_gateway_cache.py tests/tools/test_retrieval_cache.py
tests/tools/test_knowledge_gateway_redaction.py tests/tools/test_knowledge_gateway_router.py
tests/tools/test_knowledge_gateway_packet_assembly.py
tests/tools/test_knowledge_gateway_failure_semantics.py
tests/tools/test_knowledge_gateway_contract_schemas.py -q` (the full test_plan.md "Scoped Pytest
Commands" list) — **285 passed, 1 failed** (88.13s). The single failure is
`test_kgmcp_phase1_baseline_comparison.py::test_no_frozen_kgmcp_dependency_edited` itself — the
exact same pre-existing condition described above, confirming it is not introduced by this ticket
and pre-dates it. Every other file in the regression surface, including all of Phase 1's, Phase
0's, and every `knowledge_gateway_*`/`retrieval_cache` unit/integration suite, is fully green.

## Files Changed
- `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` (new)
- `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` (new — real, measured data)
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` (new)
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` (new)
- `docs/plans/knowledge-gateway-mcp-proposal.md` (edited — appended Phase 2 results paragraph only)
- `staging_artifacts/TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON/plan.md` (edited — appended
  Deviations section)
- `tickets/inprogress/TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON.md` (this file — Implementation
  Notes/Test Summary/Files Changed/Acceptance Criteria updated)

- `docs/parity_ledger/infrastructure.yaml` (Parity phase — added `INFRA-344`, `status: verified`,
  `priority: P1`, `proof_type: regression`; certifies this ticket's measurement tool/methodology
  and honest reporting as correct and tested, not the measured cache/gateway performance, which
  is the real, honest 0/7-genuine-hits / all-3-thresholds-FAIL result mirroring INFRA-339's own
  Phase 1 precedent)

**Document-Update phase:** sanity-checked `docs/engine/contracts/knowledge_gateway_mcp/
phase2_baseline_recomparison.md` and `docs/plans/knowledge-gateway-mcp-proposal.md`'s appended
paragraph against this ticket's real Implementation Notes/Test Summary numbers (0/7 hits, §4.1/
§4.2-cold/§4.2-warm/§4.3 all FAIL, 935.32 ms and 1263.57 token thresholds, oversized_payload
rejections) — both accurate and complete, no edits needed. Checked
`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4 for "pending
Phase 2 recomparison" placeholder language — none exists; §4's thresholds are frozen formulas over
the Phase 0 fixture and never reference Phase 1/Phase 2 by name, so no update was needed there.
- `tickets/todos/knowledge-gateway-mcp-phase2/TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC.md`
  (edited — added a Related Docs entry for the new `phase2_baseline_recomparison.md`, alongside the
  existing `phase1_baseline_comparison.md` entry; epic remains OPEN, not closed by this edit)

## Completion Summary

Implemented and ran the real Phase 2 cold+warm recomparison exactly per the approved plan, with DD1
resolved by Architecture Review in favor of option (b) (no request-shrinking fallback, ever). The
honest, real, measured result: **0/7 genuine cache hits** — every one of the 7 corpus entries'
default-budget response payload exceeds the deployed cache's 8192-byte write size cap, so
`perform_cache_write()` rejected every write (`"oversized_payload"`, independently confirmed by two
agreeing real signals on all 7 entries, never inferred from `response["cache"]` alone). **§4.1 FAIL
(0/7, warm-path only). §4.2 FAIL (0/7 cold, 0/7 warm, computed independently). §4.3 FAIL (0/7)** —
Q2/Q5 miss for the same documented single-primary-provider routing reason as Phase 1, and the other
5 entries' recall counts are unchanged from Phase 1's own recorded numbers. This is not
characterized as a partial success or as "Phase 2 succeeding" in any sense — every threshold misses,
for every entry, and this is stated plainly in the results doc, the proposal doc's appended
paragraph, and here. No threshold formula was redefined, no corpus entry was excluded, and no result
was assumed rather than measured. One test (`test_no_frozen_kgmcp_dependency_edited`) fails today
for a confirmed pre-existing, non-regression, repo-state reason shared identically with Phase 1's
own already-`Done` sibling test — not a defect introduced by this ticket's own diff.

**Parity phase complete:** added `INFRA-344` to `docs/parity_ledger/infrastructure.yaml`
(`status: verified`, `priority: P1`, `proof_type: regression`) via the schema-validating writer,
followed by a separate `python3 tools/parity_index.py build`. Per the same reasoning INFRA-339
(the Phase 1 sibling's own parity entry) established, `verified` here certifies this ticket's
measurement tool and its honest reporting — not the measured cache/gateway performance, which
remains the real 0/7-genuine-cache-hit, all-3-thresholds-FAIL result. Citation-drift check
confirmed clean: this ticket's diff touches none of the files INFRA-341/342/343 cite by line
number (`tools/knowledge_gateway_cache.py`, `tools/retrieval_cache.py`,
`tools/knowledge_gateway_redaction.py`, `tools/knowledge_gateway_mcp.py`); no correction to those
entries was needed. Ticket remains INPROGRESS pending Verify and Finalize.
