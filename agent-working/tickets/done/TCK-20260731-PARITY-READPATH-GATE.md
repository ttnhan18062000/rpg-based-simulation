---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-READPATH-GATE
phase: done
date: 2026-07-31
tags: [ai, agent-monitoring, observability, process-improvement, testing, workflows]
---

# TCK-20260731-PARITY-READPATH-GATE

## Title
Run the parity-index read-path payoff gate before adoption work

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Run Gate A as an offline, reproducible review of whether the completed read-only index materially
improves parity selection. This ticket is a decision gate, not permission to integrate the index
into agent context or a workflow.

## Scope
- Predeclare and version a review rubric and corpus: legacy edge fixtures plus immutable,
  ticket-derived cases; include a faction source-path case. Preserve source references/hashes and
  distinguish asserted ground truth from evaluator judgement.
- For each case, capture legacy selection, index selection, expected obligation IDs/shards,
  discrepancy adjudication, candidate count/context-byte or token estimate, and consistently
  measured analyst effort.
- Reproduce results and issue an explicit GO, NO-GO, or INCONCLUSIVE decision with rationale and
  a next action. GO only authorizes later ticket scoping, not implementation.

## Out of Scope
- Any context-packet/retrieval-cache/workflow/gate/config/monitoring mutation or live token-savings claim.
- Implementing Phase 3+ or changing the index/legacy tools to improve the score during the review.

## Acceptance Criteria
- [x] Corpus and rubric are reviewable before results are generated; every case has reproducible
      source references/hashes and expected-set/adjudication fields.
- [x] Legacy and index results are captured for all cases; every mismatch is adjudicated rather
      than silently averaged away.
- [x] The decision reports recall, false positives, selection size/context estimate, and analyst
      effort. It records zero unexplained obligation false negatives against the adjudicated set.
- [x] A GO additionally demonstrates faction/all-shard coverage, fewer false positives, or smaller
      selection size without recall regression. NO-GO/INCONCLUSIVE leaves legacy behavior live and
      files/backlogs only a bounded follow-up if warranted.
- [x] No production consumer, telemetry event, guidance/config/workflow change, or source YAML write occurs.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-IMPACT-PROOF (dependency)
- TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS (decision-gate precedent, distinct scope)

## Related Docs
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md
- docs/engine/contracts/context_packet_contract.md (boundary only)
- docs/observability/retrieval_retention_redaction_policy.md (artifact boundary only)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/context_packet_assembler.py (protected boundary; no edit expected)
- tools/agent-monitoring/generate_retro.py (evaluation precedent only)
- tests/tools/test_context_packet_assembler.py (protected regression boundary)
- tests/tools/test_generate_retro.py (evaluation precedent only)

## Assumptions / Open Questions
- The Gate A decision is human-reviewable evidence, not an automatic promotion threshold.

## Implementation Notes
Executed plan.md's 11 steps exactly, following Decisions 1-4 and the Decisions-Made-During-Human-Review
section (WORLD-076 P0 case) without reopening any of them.

- **Steps 1-3 (corpus + rubric, frozen before results):** Built
  `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` with 6 real,
  git-pinned cases (`FAC-012`@`68f168ff`, `INFRA-296`/`297`/`299`/`300`@`ab06fc10`,
  `WORLD-076`@`46c5ae59`) and 3 freshly-authored synthetic edge cases
  (`SYN-P0PAIR-001`, `SYN-MULTISHARD-001`, `SYN-MALFORMED-001`), each with a
  `canonical_fragment_hash` computed via the literal Decision-2 formula. Every real case's
  `changed_path_query` and `expected_obligation_ids` were derived by applying
  `tools/parity_index.py`'s own `_PATH_REF_RE` to the pinned shard's full `v2_evidence` +
  `legacy_evidence` + `text` fields (not a `v2_evidence`-only substring check, which would have
  missed `INFRA-299`'s genuine citation of `tools/context_packet_assembler.py` and
  `tools/retrieval_events.py` in its own `text` field — corrected mid-construction, before any
  result was computed, once discovered). `gate_a_results.json`'s empty skeleton was committed
  with all rubric fields present and `null`.
- **Step 4 (harness):** `tests/tools/test_gate_a_readpath_review.py`'s
  `_build_temp_index_for_case` writes each case's shard content (git-extracted for real cases,
  literal fixture dicts for synthetic ones) into a `tmp_path` ledger dir and calls the real,
  unmodified `parity_index.build()` — the only place `build()` is invoked, reused by Steps 5-6.
- **Steps 5-6 (capture):** Ran `find_p0_intersection`, `derive_mapping`, and `entry`/`impact`
  against every case via a module-scoped `gate_a_full_run` fixture, persisting raw results into
  `gate_a_results.json`. `health()` was run once each for `faction`/`infrastructure` and recorded
  under `health_snapshots`, never folded into recall/false-positive arithmetic.
- **Step 7 (adjudication):** Every real discrepancy was named and explained in
  `_Adjudications` (P0-only filter, faction-exclusion, a new `derive_mapping` src/\*.py-only
  scope finding, a new `.claude/`-prefix index blind spot, and a new three-way malformed-shard
  behavior difference — see Deviations below for the two new findings beyond the four
  originally-catalogued divergence shapes). No discrepancy was patched away.
- **Step 8 (metrics):** `_compute_aggregate_metrics` computed per-case and aggregate recall
  (14/21 = 66.7%), zero unexplained false positives, per-case context-byte estimates
  (`is_estimate: true`), and the analyst-effort proxy totals.
- **Step 9 (no-mutation guard):** `TestNoMutation` hashes all six protected surfaces
  (`tools/parity_index.py`, `tools/parity_ledger_scan.py`,
  `tools/gate_checks/parity_updater_static.py`, every `docs/parity_ledger/*.yaml`,
  `tools/context_packet_assembler.py`, `.claude/workflows/implement-ticket.js`) at module import
  time and re-hashes after the full suite runs — confirmed byte-identical.
- **Step 10 (decision doc):** `docs/ai/parity_readpath_gate_a_decision.md`, mirroring
  `docs/ai/shadow_promotion_gate_thresholds_decision.md`'s shape.
  **Verdict: GO** (narrowly scoped — see the doc's §5-6). Real-case aggregate recall is 14/21
  (66.7%) vs. legacy's 1/21 (4.8%), with **zero recall regression on any of the 6 real cases**
  (index ties or beats legacy on every one). Next action is scoping-only: a future Phase-3
  ticket must resolve two structural gaps this review surfaced (§6.2's `.claude/`-prefix
  blind spot, §6.4's single-shard-per-case scope limitation) before any implementation.
- **Step 11 (regression):** All scoped pytest commands green (57/57 for the four pre-existing
  parity suites, 16/16 for `test_context_packet_assembler.py`, 16/16 for this ticket's own new
  suite); `validate_frontmatter.py` and `ticket_field_values.py` both exit 0.

## Test Summary
- `pytest tests/tools/test_gate_a_readpath_review.py -v` — 16/16 passed (new suite, this ticket).
- `pytest tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v` — 57/57 passed, unmodified.
- `pytest tests/tools/test_context_packet_assembler.py -v` — 16/16 passed, protected boundary untouched.
- `python3 tools/validate_frontmatter.py <staging artifacts + decision doc>` — all OK.
- `python3 tools/ticket_field_values.py tickets/inprogress/TCK-20260731-PARITY-READPATH-GATE.md` — exit 0.
- Protected-file byte-identity confirmed both by `TestNoMutation` (in-test hashing) and a manual
  `git status --porcelain` check of the six protected paths/globs (no diff attributable to this
  ticket's work; an unrelated pre-existing uncommitted change to `.claude/workflows/
  implement-ticket.js` from prior, unrelated session work was already present before this
  ticket's work began and was never touched during it).

## Files Changed
- `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` (new)
- `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_results.json` (new)
- `tests/tools/test_gate_a_readpath_review.py` (new)
- `docs/ai/parity_readpath_gate_a_decision.md` (new)
- `tickets/inprogress/TCK-20260731-PARITY-READPATH-GATE.md` (this file, updated)

## Completion Summary
Gate A is resolved with an explicit **GO** verdict, narrowly scoped: `tools/parity_index.py`'s
unmodified `impact()`/`entry()`/`health()` read path demonstrated a 66.7% aggregate recall
(14/21) against 21 real, git-pinned expected obligations across 6 real cases, versus legacy's
4.8% (1/21), with zero recall regression on any single real case and zero unexplained false
positives. The GO is explicitly scoped to future ticket-*scoping* only (never implementation),
and carries two real, honestly-adjudicated limitations forward: (1) `WORLD-076`'s ledger
`status` is `divergent`, not `verified` — the case proves read-path retrieval of a real P0
obligation, not that `WORLD-076`'s own `src/` behavior is parity-clean; (2) a genuine,
previously-undocumented `.claude/`-prefix blind spot (`INFRA-299`, 0/7 recall on all three
surfaces — a shared gap, not an index regression) that a future Phase-3 ticket must resolve
before wiring `impact()` into any real workflow. No `tools/parity_index.py`,
`tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`, or
`docs/parity_ledger/*.yaml` file was modified; no workflow/config/telemetry surface was touched.

