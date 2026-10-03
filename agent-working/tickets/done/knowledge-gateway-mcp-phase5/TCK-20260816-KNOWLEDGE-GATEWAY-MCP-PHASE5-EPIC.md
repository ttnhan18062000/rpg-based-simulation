---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE5-EPIC
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE5-EPIC

## Title
Local Knowledge Gateway MCP — Phase 5: Entity-Aware Reuse

## Status
DONE (closed on its own gating ticket's honest "wait" finding — see Completion Summary)

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC` closed Phase 4 with all 4 children DONE: the
Parity Ledger is a real, live, third gateway provider; `changed_paths` is a genuine, tested caller
option; and — critically for this epic's own scoping — the epic's two honest-evaluation
deliverables both returned real, negative findings. `TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-
EVALUATION` found the gateway is 1.05x-3.0x heavier in tokens (universal, all 7 corpus entries) and
slower for 4 of 7 entries at real call sites, because Level 2 caching structurally never pays off on
per-ticket-unique queries. `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON` then ran a fresh, live,
paired comparison and found the gateway slower and heavier in tokens than direct tool use for **all
7 of 7** corpus entries, with hand-written quality judgments favoring direct tools 6 of 7 times.

Proposal §20 Phase 5's own three bullets ("Add canonical entity IDs and aliases," "Reuse results
across compatible phrasings," "Add conservative semantic candidate matching with deterministic
validation") are all, by design, mechanisms to broaden the definition of "the same question" so more
real calls become cache hits. §11.2 of the proposal explicitly frames this as the intended
resolution for exactly the "per-ticket-unique-query" problem Phase 4's own honest measurement just
confirmed is real and costly. This is the correct diagnosis of the right problem — but Phase 1-4's
own cumulative, honestly-measured evidence (0/7 → 7/7 hits only after a hotfix in Phase 2; Phase 3's
own real FAIL on token-budget enforcement and on the closing latency/token criterion's token half;
Phase 4's own 7/7 negative comparison even on a warm-adjacent measurement) has never yet shown that
*even a genuine cache hit* reliably beats direct tool cost on tokens, only sometimes on latency. This
epic's own first child ticket must therefore honestly re-examine, with real evidence rather than
assumption, whether broadening the hit-rate (Phase 5's whole premise) is worth building before
Phase 3's own two disclosed-and-still-open gaps (budget-tolerance FAIL; dedup never real-corpus-
proven) are closed — building more infrastructure to hit a cache whose own per-hit economics are not
yet proven favorable would repeat the exact "invest before measuring" mistake this repo's own Gate
Integrity discipline has caught and corrected four times already this project (Phase 2's original
0/7 finding, Phase 3's real FAIL disclosures, and two Phase 4 Architecture-Review-caught overclaims).

**This is not a new gate invented for this epic** — `tmp/mcp-followup-instruction.md` §7 ("Measure
Repeated Knowledge Demand") already establishes the exact precedent for this discipline, applied
there to Phase 6: "Before investing heavily in the future... layer, measure how often agents ask
semantically repeated project questions... Repeated cache misses should also be treated as
documentation/terminology telemetry." This epic's own first child ticket applies the identical
measurement-before-investment discipline to Phase 5, using real data this repo already has
(`tickets/working_log.csv`, `agent-monitoring/retro/`) rather than assumption.

## Scope
- This epic's own first child ticket honestly measures real repeated/semantically-equivalent
  question demand using real historical data already in this repository (`tickets/working_log.csv`
  ticket titles/summaries, `agent-monitoring/retro/` skill/tool-usage data, or any other real signal
  the child ticket's own Investigate phase identifies) — not the frozen 7-entry corpus alone, since
  that corpus was deliberately built to be unique-per-entry and cannot itself demonstrate repeated
  demand. Reports honestly whether real evidence supports investing in Phase 5's three bullets now.
- If (and only if) that measurement finds real, demonstrated repeated-question demand: scope and
  build canonical entity IDs and alias consolidation (proposal §11.2's "canonical cross-provider
  entity IDs and alias consolidation," deferred from Phase 0-4's own provider-native-ID-only
  identity scheme).
- If warranted by the same evidence: scope and build conservative semantic candidate matching with
  deterministic validation (proposal §11.2 step 5 — "semantic similarity later as a candidate
  generator, followed by deterministic compatibility checks," never semantic similarity alone).
- If the first child ticket's own honest measurement does NOT find real demand: this epic's real,
  honest deliverable is that finding itself, reported plainly — mirroring
  `TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`'s own precedent of a negative result
  being a complete, valid outcome for an "evaluate before building" ticket. The remaining two
  candidate child tickets are scoped only if warranted, not built regardless.

## Out of Scope
- Phase 6 (verified reusable knowledge) — deferred, contingent on Phase 6's own repeated-demand
  measurement per `tmp/mcp-followup-instruction.md` §7's own explicit text (a separate, later
  measurement from this epic's own Phase-5-scoped one).
- Closing Phase 3's own two disclosed-and-still-open gaps (budget-tolerance FAIL; dedup never
  real-corpus-proven) — those remain a separately-scoped follow-up ticket per Phase 3's own explicit
  Completion Summary, not this epic's to close, though this epic's own first child ticket's honest
  measurement may reference them as context for why per-hit economics remain unproven.
- Any change to Level 1/Level 2 cache mechanics, dedup/budget-enforcement logic, or the Parity
  adapter Phase 3/Phase 4 already built and shipped — this epic (if warranted) adds an identity-
  resolution/matching layer in front of existing lookup identity, it does not modify existing
  cache read/write/invalidation code paths.
- Building canonical entity IDs or semantic matching "regardless of the evidence" — this epic's own
  AC list requires the first child ticket's real finding to genuinely gate the other two, not be a
  formality en route to predetermined implementation.
- Any new MCP tool beyond `knowledge_context`/`knowledge_status` — per `tmp/mcp-followup-
  instruction.md` §9's "prefer keeping" constraint, unchanged from Phase 4's own scoping.
- Making the Knowledge Gateway a mandatory phase, gate, or ticket step in any workflow — per §1's
  explicit prohibition, unchanged from every prior phase's own scoping.
- Any change to `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md`.

## Acceptance Criteria
- [x] The first child ticket honestly measures real repeated/semantically-equivalent question demand
      using real historical data, reporting whichever result is real — including a finding that
      demand is insufficient to justify Phase 5's investment, if that is what the real data shows.
      (Real, honest result: a small, mostly-non-literal repeated-demand signal — 17/521 conservative
      pairs in `agent-monitoring/events.jsonl`, 372/1411 in `tickets/working_log.csv` — cross-
      referenced against Phase 3/4's own real negative cache economics, yielding "proceed only after
      Phase 3's own disclosed gaps close — not now, not never," not a flat yes or no.)
- [x] If canonical entity IDs/alias consolidation is built, it is built only because the first child
      ticket's own real measurement genuinely warranted it — not built by default regardless of the
      measurement's outcome. (Not built — the real measurement did not warrant it now.)
- [x] If conservative semantic candidate matching is built, it uses semantic similarity only as a
      candidate generator followed by deterministic compatibility checks (proposal §11.2 step 5) —
      never semantic similarity alone as a sufficient match. (Not built — same reasoning; the
      measurement ticket's own equivalence-detection method already followed this conservative,
      multi-signal discipline as its own methodology, not as a built product.)
- [x] Every built child ticket writes a real, schema-valid `docs/parity_ledger/infrastructure.yaml`
      entry for its own behavior change, per this repo's own CLAUDE.md governance rule.
      (INFRA-355, the epic's one child ticket.)
- [x] `docs/plans/knowledge-gateway-mcp-proposal.md` §20's Phase 5 bullets are annotated Done only
      where a real, live, verified capability genuinely supports it — or, if the first child ticket's
      honest measurement finds insufficient demand, the bullets remain honestly unmarked with the
      real finding recorded, mirroring Phase 3/4's own precedent of never overclaiming. (All 3 Phase
      5 bullets remain unmarked; a real, honest narrative paragraph records the actual finding.)
- [x] `tmp/mcp-followup-instruction.md`'s constraints (gateway stays optional/ambient, MCP surface
      stays small, gateway never becomes the source of truth, semantic matching stays conservative
      with deterministic validation) are respected by every built child ticket — verified by explicit
      scope-guard checks in each ticket's own Architecture Review, not merely assumed. (N/A in the
      strictest sense — nothing was built to check against these constraints — but the one child
      ticket's own Architecture Review twice confirmed zero gateway/cache/router source was touched.)
- [x] `CLAUDE.md`, `.claude/agents/*.md`, and `.claude/skills/*.md` remain byte-unchanged by every
      child ticket in this epic — confirmed via `git diff --stat HEAD` returning empty for all three
      paths.
- [x] This epic is not closed merely because a child ticket's code lands — if the first child
      ticket's honest measurement finds real demand and the other two are built, all three must be
      genuinely verified; if it finds insufficient demand, the epic closes honestly on that single
      finding without needing to build anything further, and this is treated as full success, not an
      incomplete epic. **This is exactly what happened.** The gating ticket's own real,
      independently-re-verified recommendation — wait, not now — is the epic's real, complete
      deliverable.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC (DONE; parent Phase 4 epic — supplies the real,
  cumulative negative cache-value evidence this epic's own first child ticket must honestly weigh)
- TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION (DONE; the direct methodological
  precedent this epic's own first child ticket follows — honest evaluation before investment)
- TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON (DONE; supplies the real 7/7 negative gateway-vs-
  direct-tool comparison this epic's own first child ticket must reference as context)
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (DONE; the two still-open, disclosed gaps —
  budget-tolerance FAIL, dedup never real-corpus-proven — this epic does not close but must weigh)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §11.2 (Cache Identity and Equivalent Questions —
  the frozen design this epic implements if warranted), §20 Phase 5 bullets
- `tmp/mcp-followup-instruction.md` §7 (Measure Repeated Knowledge Demand — the direct precedent for
  this epic's own measurement-before-investment discipline)
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md`,
  `phase4_direct_tool_comparison.md` (the real, negative cache-value evidence this epic must weigh)

## Related Stored Artifacts
None yet — scope-only epic, no staging artifacts per the Phase 0-4 epics' own precedent.

## Related Code Areas
- `tickets/working_log.csv`, `agent-monitoring/retro/` (candidate real-data sources for the
  repeated-demand measurement — the first child ticket's own Investigate phase decides which, if
  any, is the right real signal)
- `tools/knowledge_gateway_cache.py` (`compute_lookup_identity()`, `compute_context_packet_lookup_
  identity()` — the existing provider-native-ID-only identity functions this epic would extend, if
  warranted, with canonical entity IDs)
- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (the frozen 7-entry corpus — explicitly NOT a
  valid repeated-demand signal on its own, since it was deliberately built unique-per-entry)

## Assumptions / Open Questions
- Whether real repeated-question demand exists in this repository's actual usage history is the
  central, genuinely open question this epic's own first child ticket must answer with real data —
  not assumed either way here. A negative finding is an explicitly acceptable, complete outcome.
- If demand IS found, whether canonical entity IDs or semantic matching should be built first (or
  both together) is left to the first child ticket's own Plan phase, informed by whatever the real
  measurement shows about the shape of the repeated demand (e.g. entity-alias mismatches vs.
  phrasing variance).

## Implementation Notes
Scope-only epic; no direct implementation. This epic's own single child ticket
(`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`) landed with a real Architecture Review
correction cycle before implementation: a confirmed-live self-contamination bug, where the ticket's
own mandatory pipeline monitoring write would have landed in the exact dataset it was measuring
(521 real records vs. a contaminated 522), was caught, fixed with an explicit, permanently-tested
exclusion, and independently re-verified genuine by two later phases (Architecture-Verify and
Verify). The ticket's own real, honest recommendation — proceed with Phase 5's remaining capability
only after Phase 3's own disclosed gaps close, not now, not never — is exactly the kind of outcome
this epic's own Scope and AC8 explicitly anticipated and accepted as complete, not a shortfall.

## Test Summary
`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`: 12/12 new tests passing (10 in
`tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py`, 2 in
`tests/docs/test_phase5_repeated_demand_measurement_doc.py`), plus 142/142 regression-surface tests
(frozen Phase 1-4 measurement fixtures, `test_registry_query.py`, `test_tag_registry.py`) passing
unmodified.

## Files Changed
Aggregate — see the one child ticket's own Files Changed for exact line-level detail:
- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` — new, one-time
  measurement runner (imports `candidate_tags_from_text` from `tools/registry_query.py`, never
  reimplements).
- `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json`,
  `kgmcp_phase5_working_log_snapshot.json`, `kgmcp_phase5_repeated_demand_measurement_results.json`
  — new, frozen input snapshots and committed result fixture.
- `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` — new results
  doc.
- `docs/parity_ledger/infrastructure.yaml` — INFRA-355.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — a real, honest narrative paragraph after §20
  Phase 5's 3 bullets; no bullet marked Done.
- Various test files across `tests/tools/` and `tests/docs/` — 12 new tests total.

## Completion Summary
This epic's single, real child ticket honestly measured repeated/semantically-equivalent question
demand in this repository's own actual history — not the frozen 7-entry corpus, which was
deliberately built unique-per-entry and could never have answered this question — and found a real,
if small and mostly-non-literal, signal: 17 conservative pairs among 521 tickets in
`agent-monitoring/events.jsonl`, 372 among 1,411 in `tickets/working_log.csv`. Cross-referenced
against Phase 3's own disclosed budget-tolerance FAIL and Phase 4's own real finding that the
gateway underperforms direct tool use on all 7 of 7 fresh, live comparisons, the honest, real
recommendation is to wait: proceed with Phase 5's remaining capability (canonical entity IDs,
conservative semantic matching) only once Phase 3's own disclosed gaps are closed — not now, and
not never.

Architecture Review caught and required a fix for a genuinely subtle problem before implementation:
the measurement ticket's own mandatory pipeline monitoring write would have counted as evidence of
the very thing it was measuring, contaminating its own primary data source. This was fixed with an
explicit, permanently-tested exclusion and independently re-verified twice more before closure.

**Because this epic's own gating ticket found real demand exists but the case to act on it now is
not yet made, the epic's remaining two candidate child tickets (canonical entity IDs/alias
consolidation; conservative semantic candidate matching) are not created.** This is not an
incomplete epic — the epic's own Scope and AC8 explicitly anticipated and accepted exactly this
outcome as a complete, valid result: "if it finds insufficient demand, the epic closes honestly on
that single finding without needing to build anything further, and this is treated as full success,
not an incomplete epic." Building broader cache-hit-matching infrastructure now, on top of a cache
mechanism whose own per-hit economics remain unproven or measurably negative in every honest test
run so far, would have repeated the exact "invest before measuring" pattern this project's own Gate
Integrity discipline has now caught and corrected multiple times across Phases 2 through 5.

This epic does not declare Phase 5 complete in any broader capability sense, and does not close
Phase 3's own two still-open, disclosed gaps (budget-tolerance FAIL; dedup never real-corpus-
proven) — those remain a separately-scoped follow-up ticket's job, referenced here only as the real
context for why this epic's own recommendation is to wait.
