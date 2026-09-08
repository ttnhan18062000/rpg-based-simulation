---
status: historical
layer: ai
authority: P1
audience: agent
tags: [ai, mcp]
---

# Knowledge Gateway MCP — Keep, Invest Further, or Deprecate: The Decision

Every phase of this proposal (0 through 5, plus the follow-up efficiency-remediation epic)
deliberately deferred this exact call to a human reviewer, per the proposal's own repeated
discipline (`audit_phase0_5.md` §5: "the decision of what to do next... is a human reviewer's
call"). This document records that the call has now been made, and what was weighed to make it.
It does not re-derive any measurement — every number below is cited from an already-real, already
-verified result.

## 1. The three options, with their real tradeoffs

**Option A — Keep as-is, no further investment.** KGMCP stays available, optional, and ambient
(never mandatory, per `tmp/mcp-followup-instruction.md`'s own constraint, unchanged since Phase 0).
No further engineering effort goes into it. Tradeoff: the gateway continues to lose to direct tool
calls on every measured query type (§2 below), so leaving it available costs nothing beyond its
existing maintenance/test surface, but it also does not proactively help unless an agent happens to
hit one of the narrow cases outside the 7-entry measurement corpus's coverage.

**Option B — Invest further.** Close Phase 5's remaining scope (canonical entity IDs, conservative
semantic candidate matching to raise cache-hit rates) now that Phase 3's accounting gaps are closed
(`TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING`: §21 #12 moved 2/7 → 7/7 PASS). Tradeoff: this
is exactly the precondition Phase 5's own "wait, not now, not never" recommendation was gated on —
but even with that precondition met, Phase 4's warm-path re-comparison (§2 below) already shows the
gateway losing on cost even when caching works perfectly, so broadening the hit rate would not by
itself close that gap; it would need to be paired with a real reduction in per-call routing/assembly
overhead, which no phase to date has measured or attempted.

**Option C — Deprecate/remove.** Retire `tools/knowledge_gateway_mcp.py` and the modules built
around it. Tradeoff: justified by the 7/7 warm-path losses and the weak repeated-demand signal
below, but this discards real, tested infrastructure (versioned provider contracts, evidence-aware
invalidation, branch/working-tree safety) that Architecture Review independently verified sound at
every phase — the failure is in cost-competitiveness against direct tool calls, not in the
architecture's own correctness.

## 2. The real evidence weighed

- **Phase 2** (`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`,
  `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`): the cache mechanism itself is
  confirmed genuinely working — 0/7 cache hits (payload-size-cap bug) fixed and re-verified 7/7
  genuine hits on a clean cold-cache run.
- **Phase 3** (`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`,
  `TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING`): budget-tolerance accounting closed from
  2/7 to 7/7 PASS on live re-measurement.
- **Phase 4 cold-cache** (`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`): gateway slower
  (1.31x-3.76x) and heavier in tokens (1.04x-2.93x) than direct tool calls on all 7/7 corpus
  entries; direct tools judged equal-or-better 6/7 times, gateway never judged better.
- **Phase 4 warm-cache re-comparison** (`TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`, documented
  in `phase4_warm_direct_tool_comparison.md`): with caching genuinely working, the gap narrows
  substantially but **the gateway still loses on all 7/7 entries** — latency 1.06x-1.34x slower,
  tokens 1.05x-1.98x heavier.
- **Phase 5** (`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`): real repeated-question demand
  in this repository's own history is real but small and mostly non-literal — 17/521 conservative
  pairs in `agent-monitoring/events.jsonl` (3.3%), 372/1411 in `tickets/working_log.csv` (26.4%,
  mostly incremental investigation not literal repeats); commonly summarized as a 5.8%-18.5% range
  depending on which conservative-pair definition is used.
- **Efficiency-remediation epic** (`TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC`): its own net,
  stated verdict: "the mechanisms now work correctly as designed, but the gateway's own
  routing/assembly overhead is large enough that it is not yet cost-competitive with an agent
  calling the underlying tools directly."

## 3. Ratification

**Ratified by the repository owner on 2026-08-24: Option A — keep as-is, no further investment.**

No changes to `tools/knowledge_gateway_mcp.py` or any related module are authorized by this
decision. KGMCP remains available, optional, and ambient exactly as it is today. Phase 5's
remaining two bullets (canonical entity IDs, conservative semantic candidate matching) and any
Phase 6 work remain unauthorized — this ratification does not open them, and any future proposal to
build them would need its own separate review against real evidence at that time, per the same
discipline this arc has followed throughout.

This mirrors `TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`'s own precedent: a real human
decision, recorded plainly, with no re-derivation of the measurements that informed it.

## 4. Re-ratification (2026-09-07)

A month of real usage data since the 2026-08-24 ratification, plus fresh external research, was
brought back to the repository owner as new evidence Option A's own reviewer never had:

- **Usage gap widened, not narrowed.** Exactly 1 real `knowledge_gateway__knowledge_context`
  content-retrieval call exists in the project's entire recorded monitoring history (2026-08-17,
  predating this ratification) against 3,375 real calls to the direct `search_docs` tool it sits
  alongside (re-counted live against `agent-monitoring/data/*/tools.jsonl` at re-ratification
  time — it was 2,259 when the epic that re-opened this question was first scoped days earlier).
- **The `done-checker`/`test-scoper` tool-allowlist grant was an accident**, not a deliberate
  design choice — sourced from `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`'s historical-usage-
  derived scoping pass; no considered rationale exists anywhere for it.
- **External research** (Cursor, Windsurf, Sourcegraph Cody, Aider, Devin/Cognition's own removal
  of an embeddings-based retrieval layer in favor of direct search, Anthropic's internal Claude
  Code usage study, Sourcegraph/Amp, the Zup internal-agent case study) found no production or
  AI-first-development system building a live routing/caching context gateway in front of direct
  retrieval tools — the consistent pattern is direct tools plus routing guidance expressed as
  prompts/instructions (which this project already has, in CLAUDE.md's Proactive Tool Use table).
- **The measured overhead is the wrapping/routing cost, not caching** — the warm-cache
  re-comparison in §2 above still lost 7/7 even with caching fully realized, confirming a partial
  fix (better cache-hit rates) would not by itself close the gap.

**Re-ratified by the repository owner on 2026-09-07: Option C — deprecate/remove.** This
supersedes the 2026-08-24 Option A ratification above. Execution proceeds per
`TCK-20260907-KGMCP-DEPRECATION-EPIC`'s M2: extract `scan_for_secrets()` to a location independent
of the gateway (a real cross-epic dependency), archive (not hard-delete) the remaining gateway
modules and deregister `.mcp.json`, monitor 2 weeks for zero renewed calls, then delete.

## 5. Related tickets and docs

Decision ticket: `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` (original ratification),
`TCK-20260907-KGMCP-DEPRECATION-EPIC` (re-ratification and execution).

Evidence cited: `TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC`,
`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`, `TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`,
`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`,
`TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING`, `TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`
(ratification-pattern precedent).

Docs: `docs/plans/knowledge-gateway-mcp-proposal.md` §25, `audit_phase0_5.md` §5,
`phase4_warm_direct_tool_comparison.md`, `docs/parity_ledger/infrastructure.yaml` (INFRA-344
through INFRA-356).
