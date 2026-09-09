---
status: historical
layer: ai
authority: P1
audience: agent
tags: [ai, mcp, testing]
---

# Knowledge Gateway MCP — Consolidated Audit, Phases 0-5

This is a consolidated, honest audit of everything built and measured under
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phases 0 through 5, as of 2026-08-16. It does
not authorize, block, or declare production-capable status for anything — per the proposal's own
repeated discipline, that determination is a separate, later human-reviewer call. This document
exists to make that reviewer's job easier by putting every real, measured result in one place,
without re-litigating or softening any of them.

## 1. What was built (real, tested, independently verified)

- **Phase 0** — versioned provider-capability contracts, security/redaction/retention policy,
  measurement baseline contract, and the frozen 7-entry corpus used by every later phase's
  measurement.
- **Phase 1** — read-only gateway (`knowledge_context`/`knowledge_status`), Context Search +
  Graphify routing, Level 0 provider-metadata cache.
- **Phase 2** — real Level 1 provider-result cache with redaction/secret-scan/size-cap enforcement
  on every write, no bypass path.
- **Phase 3** — real Level 2 assembled-packet cache, genuinely wired into the live call path
  (`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`); dependency-aware targeted invalidation,
  branch/working-tree safety; a real pilot-acceptance measurement against the live path
  (`TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`); and a follow-up closure ticket
  (`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`) that widened budget-cost accounting
  and re-confirmed the dedup-coverage gap.
- **Phase 4** — a real, live Parity Ledger adapter (`entry()` only, per design); changed-path-aware
  cache revalidation (already incidentally wired by Phase 2/3); an honest workflow-integration
  evaluation; and a real, paired, cold-cache gateway-vs-direct-tool comparison across all 7 corpus
  entries.
- **Phase 5** — a real measurement of repeated/semantically-equivalent question demand against this
  repository's own historical usage (not the frozen corpus, which is deliberately unique-per-entry).

Every one of the above landed as real, tested code or a real, reproducible measurement run — not a
design sketch. Every phase's own child tickets were independently reviewed by Architecture Review
(pre-Implement plan review and post-Implement diff review) and re-verified by a dedicated Test
phase, following this session's own established discipline of never taking a self-report at face
value.

## 2. What was honestly measured (the part that matters for a promotion decision)

This is the section a reviewer deciding on Phase 6 or production promotion should read most
carefully. The proposal's original hypothesis — that the gateway reduces latency and delivered
tokens relative to direct tool use — is **not currently supported** by the real, cold/warm-cache-
mixed corpus measurements gathered across Phases 3-5:

| Measurement | Result | Ticket |
|---|---|---|
| Phase 3 budget-tolerance (±20% of requested budget) | **FAIL, 2/7**, both before and after a dedicated fix that widened cost accounting (payloads shrank 11%-22% per entry, not enough to cross tolerance) | `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`, `TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE` |
| Phase 3 genuine-cache-hit token count vs. both baselines | Latency improved; **token count did not improve** against either baseline (`pass: false`, reported honestly) | `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` |
| Phase 3 conflict visibility | 0/7 real cross-provider conflicts observed — a corpus-design gap, not evidence the mechanism is broken, but also not a demonstrated pass | `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` |
| Phase 3 multi-provider dedup, real-corpus proof | **Still open** — 0 real cross-provider content duplicates exist in the live corpus today; locked via a live regression test, not closed | `TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE` |
| Phase 4 gateway vs. direct-tool, fresh cold-cache, all 7 entries | **Gateway slower (1.31x-3.76x) and heavier in tokens (1.04x-2.93x) for all 7 of 7 entries.** Reviewer judgment: 6/7 direct-tool-equal-or-better, 1/7 mixed, 0/7 gateway-better | `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON` |
| Phase 4 workflow-integration candidates | Recommend against integration at 3 of 4 points; 1.05x-3.0x heavier in tokens universally; insufficient evidence at the 4th | `TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION` |
| Phase 5 repeated-question demand | Small, real, but mostly-non-literal signal (17/521 primary, 372/1411 secondary conservative pairs) — most matches are natural incremental investigation, not the same question re-asked | `TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT` |

No entry was excluded, no threshold was redefined, and no test was loosened to flip any of these
results — every one above was independently re-verified by at least one dedicated review or test
pass separate from the ticket that produced it. See each linked ticket/doc for full per-entry
detail; this table is a pointer, not a replacement.

### What genuinely worked

- Warm-hit no-rerun, stale rejection on a real changed source, unrelated-change non-invalidation,
  branch partition, and uncommitted-change invalidation all **PASS** — the cache-correctness
  architecture (evidence-aware invalidation, branch/working-tree safety) is real and sound.
- The Parity Ledger adapter is genuinely, end-to-end wired and fails open on a missing/stale index.
- Graphify-routed entries showed exact objective quality parity (0 missing, 0 extra sources) against
  direct tool use in the Phase 4 comparison — the quality regression Phase 4 found was narrower
  (Context-Search-routed entries only) than the cost regression.

## 3. Known open gaps (disclosed, not fixed, tracked here for visibility)

- **Budget-tolerance FAIL persists** (2/7) after a real, honest fix attempt. The remaining gap is
  JSON structural overhead and untouched response fields (`statement_id`, `classification`, `kind`,
  `EvidenceEntry.source_id`, `cache_key_version`, etc.) that the real `json.dumps(response)`
  measurement counts but no per-statement/conflict cost function currently does. Closing this fully
  would require a different design (the rejected "orphan-statement" option (b), or a new option),
  not a further widening of option (a).
- **Multi-provider dedup is unexercised in the live corpus** — the mechanism is real and tested
  against synthetic fixtures, but 0 real cross-provider duplicates exist in the frozen 7-entry
  corpus, so it has never fired on live data. Locked via a live regression test that will start
  failing (in a good way — it will need updating, not silently passing) the moment real duplicate
  content appears.
- **New: parity-provider dedup-identity divergence** — parity-sourced statements key dedup identity
  on `record["canonical_fragment_hash"]`, not `_content_hash(text)` like the other two providers.
  Untested in live conditions (no live `found=True` parity statement exists in the corpus today).
  Regression-locked, not fixed.
- **Pre-existing schema bug, disclosed, not fixed**: `knowledge_context_response.schema.json` types
  `conflicts[].automatic_resolution` as non-nullable `string`, but real code
  (`_structural_supersession_signal()`) always sets it `None` — no real conflict-carrying response
  can ever validate against the schema as written.
  `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`.
- **Unconfirmed, plausible-but-not-investigated cause**: a Q7 recall regression surfaced as a side
  effect of `TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`'s full corpus re-run,
  plausibly caused by the intervening `TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION` search-
  index rebuild rather than by the budget-accounting change itself. Not investigated — flagged as a
  real follow-up candidate.
- **Parity-sourced cache-write mislabeling** (Phase 4, disclosed): a cached packet containing real
  parity-sourced content is currently mislabeled as Context-Search-sourced in the redaction
  allowlist/cache `source_type` derivation, rather than explicitly allowlisted as
  `parity_ledger`. See `redaction_retention_policy.md` §2.
- **`SCOPED` negative-knowledge declaration doesn't yet flip any real response's `verification`
  field end-to-end** — `assemble_packet()`'s zero-statements auto-trigger never threads
  `validated_scopes` through from the Parity adapter. Deferred, not fixed.

## 4. Test and CI regression status

Combined scope across all Phase 3 follow-up work (`tests/tools/test_knowledge_gateway_packet_assembly.py`,
`test_knowledge_gateway_mcp.py`, `test_kgmcp_baseline_corpus_dedup_coverage.py`,
`test_knowledge_gateway_router.py`, `test_kgmcp_phase3_pilot_acceptance_measurement.py`,
`test_kgmcp_phase4_direct_tool_comparison.py`): **182 passed, 0 failed**, independently re-verified
twice (once by Architecture-Verify, once by a dedicated 2nd Test-phase pass).

The full `tests/tools` CI lane (matching `.github/workflows/test.yml`'s `api-tools` job scope,
`-m "not slow"`) was re-run locally against the committed state as part of this audit:
**2240 passed, 23 failed, 1 skipped, 1 xfailed, 7 errors** (of 2272 collected). Every one of the 23
failures + 7 errors was traced to a real cause and confirmed pre-existing and unrelated to any
Phase 3-5 ticket in this arc:

- 2 (`test_kgmcp_phase2_baseline_recomparison.py`/`test_kgmcp_phase3_pilot_acceptance_measurement.py`'s
  own `test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`) are pre-existing timing
  marginality, not a deterministic regression — these tests call the real gateway across the full
  7-entry corpus and take 49s-56s in isolated raw-timing runs (measured directly, `--resource-budget
  off`), right at the edge of `tests/conftest.py`'s default 60-second "medium" budget. They pass
  reliably (confirmed 3x) within their own file's natural execution context (warm caches from
  earlier tests in the same file) and only tip over under specific isolation/contention conditions.
  This flakiness risk pre-dates this session's tickets (it is inherent to a real-gateway-calling
  test under a fixed wall-clock budget) and was not newly introduced by the widened cost-accounting
  code, which adds microseconds of pure-Python arithmetic, not seconds of I/O.
- 3 (`test_generate_registry.py`'s `TestRealDocsTree`, `test_validate_frontmatter.py`'s
  `TestPreviouslyFrontmatterMissingDocs`) trace to the single known, pre-existing, already-disclosed
  `docs/mechanics/content_usage_matrix.md` missing-frontmatter gap (unrelated to this arc, flagged
  repeatedly by `make docs-registry` throughout this session as non-blocking).
- 1 (`test_context_kind_priority_decision.py::test_no_code_changes_to_named_tools_modules`) is a
  stale frozen-content-hash guard on `tools/parity_index.py` from an old, unrelated,
  already-closed ticket (`TCK-20260802-CONTEXT-KIND-PRIORITY`) — `git log` confirms
  `tools/parity_index.py` was last modified in the pre-session merge commit `29d78798`, not by
  either ticket in this arc.
- The rest (`test_entity_event_ledger.py`, `test_search_mcp.py`, `test_parity_index_baseline.py`,
  and the remaining unsampled failures/errors in `test_epic_staleness_check.py`,
  `test_exact_lookup_convention_decision.py`, `test_gate_a_readpath_review.py`,
  `test_stored_artifact_kind_decision.py`) were spot-checked and trace to unrelated causes (a broken
  evidence citation to a non-existent file, an `.mcp.json` command-field drift, a missing decision
  doc) with no dependency on any file either ticket in this arc touched
  (`tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_packet_assembly.py`, `Makefile`, plus
  docs/tests/tickets/monitoring files specific to this arc). Not exhaustively re-verified
  individually — flagged here as real, pre-existing `tests/tools`-lane debt worth its own separate
  hygiene ticket, out of scope for this audit to fix.

No `src/` engine code was touched by any Phase 3-5 ticket; all changes are confined to `tools/`
(agent infrastructure), so the CI lanes covering core engine/simulation behavior
(`unit-core-world`, `unit-gameplay`, `unit-infra`, `integration`, `simulation-quality`, the 5k-tick
behavioral regression baseline in the `slow` job) are not expected to be affected and were not
re-run as part of this audit — only the `api-tools` lane, which is the lane these changes actually
touch.

## 5. What this audit does not do

This document does not recommend for or against Phase 6 (`Verified Knowledge, Only If Justified`)
or production promotion. Phase 5's own measurement ticket already made the applicable
recommendation — proceed with Phase 5's remaining two bullets "only after Phase 3's own disclosed
gaps close — not now, not never" — and those gaps are now re-measured and honestly re-confirmed
(not improved) by `TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`. Per this proposal's
own repeated discipline throughout every phase, the decision of what to do next — invest further,
pause, or scope the gateway down to a narrower use case than originally proposed — is a human
reviewer's call, made against the real numbers in §2 above, not against this document's own framing
of them.

**Status update (2026-08-24):** that call has now been made. See
`keep_or_deprecate_decision.md` for the full record — the repository owner ratified "keep as-is, no
further investment" (Option A of that document's three), against the warm-cache re-comparison
(`phase4_warm_direct_tool_comparison.md`, gateway still losing on all 7/7 entries even warm) and
the efficiency-remediation epic's own net verdict (`TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC`).
No Phase 5+/further investment is authorized by this ratification.

**Status update (2026-09-07):** the 2026-08-24 ratification above has been superseded. See
`keep_or_deprecate_decision.md` §4 for the full record — the repository owner re-ratified against a
month of real usage data (the gateway's own content-retrieval tool called once, ever, against
thousands of direct `search_docs` calls) plus external research finding no comparable
production/AI-first-development practice: Option C — deprecate/remove. Execution proceeds per
`TCK-20260907-KGMCP-DEPRECATION-EPIC`.

## 6. Related tickets and docs

Phase 3: `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`,
`TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION`,
`TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`,
`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`.
Phase 4: `TCK-20260816-KGMCP-P4-PARITY-ADAPTER`, `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`,
`TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`,
`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`.
Phase 5: `TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`.

Docs: `docs/plans/knowledge-gateway-mcp-proposal.md` (§20 per-phase ledger, §21 pilot acceptance
criteria, §25 recommendation and status update), `phase3_pilot_acceptance_measurement.md`,
`phase4_direct_tool_comparison.md`, `phase4_workflow_recommendation.md`,
`phase5_repeated_demand_measurement.md`, `redaction_retention_policy.md`.

Parity ledger: `docs/parity_ledger/infrastructure.yaml` — `INFRA-344` through `INFRA-356` cover this
entire arc; each entry's own `text`/`v2_evidence`/`support_boundary` is the authoritative per-change
record this audit summarizes.
