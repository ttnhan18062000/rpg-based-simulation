---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC
phase: open
date: 2026-08-14
tags: [ai, process-improvement]
---

# TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC

## Title
Local Knowledge Gateway MCP epic — Phase 0 contract, policy, and measurement work only

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` (2026-08-11, synthesized from
`tmp/knowledge-mcp-audit.md` and `tmp/mcp-followup-instruction.md`) proposes a thin Knowledge
Gateway MCP — a routing/coordination facade with a local SQLite cache over the repository's
existing Context Search, Graphify, and (later) Parity Ledger providers. It is explicitly an
optimization/coordination layer, never a source of project truth, and the proposal's own "Proposal
Maturity" section states approval authorizes **Phase 0 contract, policy, and measurement work
only** — production gateway wiring and cached-payload retention require Phase 0's versioned
contracts, security ruling, and measured acceptance thresholds to be approved first.

This is a **scope-only epic**: it tracks the proposal and Phase 0 (§20) as the currently-authorized
unit of work. It does not implement any phase directly. Phase 0's ~14 line items are now broken out
into 5 child tickets below, grouped by the proposal's own structure (contract schemas, evidence/
cache identity, measurement baseline, redaction/retention policy, and the pre-scan-mandate
instruction draft); the §24 Open Decisions remain unresolved reviewer questions tracked across
those children and this epic.

## Scope
- Track `docs/plans/knowledge-gateway-mcp-proposal.md` as this epic's source proposal.
- Gate all work strictly to Phase 0 (§20 "Phase 0: Contract and Measurement Baseline") until its
  deliverables are reviewed and measured acceptance thresholds exist — no Phase 1+ implementation
  (routing, caching, MCP tool exposure) is authorized by this epic.
- Track the §24 "Open Decisions Requiring Explicit Review" as unresolved until a reviewer rules on
  each.
- Require Phase 0's baseline-measurement work (§18.1, §20) to reuse
  `tools/agent-monitoring/retrieval_baseline_metrics.py`'s existing `raw_investigation_count`/
  `search_count`/`read_to_search_ratio` metrics rather than build a parallel measurement path —
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` is already wiring this exact metric family
  into the recurring retro.
- Require Phase 0's planned agent-instruction change (§2.1, §20: "Draft the generated-agent-
  instruction change replacing the blanket pre-scan mandate with the cheapest-reliable-source and
  ambient-utility rule; do not activate it before review") to be explicitly sequenced against
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` before it is drafted or activated — see
  Assumptions/Open Questions below.

## Out of Scope
- Any Phase 1+ implementation (deterministic routing, `knowledge_context`/`knowledge_status` MCP
  tools, SQLite payload cache, provider-result caching).
- Activating the Phase 0-drafted agent-instruction change that relaxes the blanket Context
  Search-plus-Graphify pre-scan mandate — the proposal itself says not to activate it before
  review, and this epic requires that review to explicitly account for
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`.
- Re-litigating or duplicating `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC` (backlog) — the
  proposal explicitly builds on that epic's `ContextPacket`, hybrid retrieval fusion, and
  `retrieval_cache.db` substrate rather than replacing it.

## Acceptance Criteria
- [ ] Only Phase 0 (§20) work is scoped/authorized under this epic; no Phase 1+ deliverable is
      claimed as done here.
- [ ] The directional tension between Phase 0's planned pre-scan-mandate relaxation (§2.1) and
      `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s active hardening of that same mandate is
      explicitly resolved or sequenced (e.g. hardening ticket lands and its retro window closes
      first, or the instruction-change draft is written to explicitly not regress the hardened
      entry point) before the drafted instruction change is activated.
- [ ] Phase 0's baseline-measurement deliverable cites and reuses
      `retrieval_baseline_metrics.py`/`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s
      metrics rather than duplicating a second `read_to_search_ratio`-equivalent.
- [ ] All 6 items in proposal §24 "Open Decisions Requiring Explicit Review" are tracked here as
      unresolved until a reviewer rules on each.
- [ ] All 5 child tickets are linked below, and this epic is not closed merely because a child
      ticket's code lands — Phase 0's own acceptance bar (§21 lists the *Phase 3* pilot bar, not
      Phase 0's; Phase 0's bar is the frozen contracts/baseline/ratified policy listed in §20) must
      be met.
- [ ] `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT` does not modify any live `CLAUDE.md` or
      `.claude/agents/*.md` file — its output is a draft artifact only.

## Related Tickets
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (child; Phase 0 MCP wire + provider adapter/capability
  contracts)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (child; Phase 0 lookup vs. validity identity, evidence
  identity kinds, cache migration plan)
- TCK-20260814-KGMCP-MEASUREMENT-BASELINE (child; Phase 0 representative-query baseline and
  promotion thresholds)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (child; Phase 0 redaction/retention policy and
  SQLite operational limits)
- TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT (child; drafts, does not activate, the
  pre-scan-mandate relaxation — explicitly sequenced against the hardening ticket below)
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (sibling epic; parent of the two tickets
  below, unrelated proposal but overlapping instruction surface)
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (OPEN; hardens the same search-before-grep
  mandate this epic's Phase 0 plans to relax — see Assumptions/Open Questions)
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (OPEN; owns the
  `read_to_search_ratio`/compliance-correlation metric this epic's Phase 0 baseline work must reuse)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (BACKLOG; supplies the `ContextPacket`, hybrid
  retrieval fusion, and `retrieval_cache.db` substrate this proposal explicitly builds on top of,
  not a duplicate)
- TCK-20260612-LOCAL-CTX-MCP (DONE; built the existing `search_mcp.py`
  `search_docs`/`search_health` MCP server this proposal's gateway sits above)
- TCK-20260731-PARITY-READPATH-GATE (DONE; source of the Parity Ledger read-path this proposal's
  Phase 4 adapter would use)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` (source proposal)
- `tmp/knowledge-mcp-audit.md`, `tmp/knowledge-mcp-audit-report.md`, `tmp/mcp-followup-instruction.md`
  (drafting history the proposal was synthesized from)
- `docs/engine/contracts/context_packet_contract.md`
- `docs/ai/parity_readpath_gate_a_decision.md`
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`

## Related Stored Artifacts
None yet — scope-only epic, no staging artifacts per hotfix/epic precedent
(`TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC`).

## Related Code Areas
- `tools/search_mcp.py`
- `tools/hybrid_retrieval.py`, `tools/knowledge_search.py`
- `tools/context_packet_assembler.py`
- `tools/retrieval_cache.py`
- `tools/retrieval_events.py`
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tools/parity_index.py`
- `CLAUDE.md` (§Context Scan — the instruction surface Phase 0's drafted change would edit)

## Assumptions / Open Questions
- **Sequencing of the pre-scan-mandate relaxation vs. the hardening ticket.** The proposal's Phase 0
  drafts an agent-instruction change replacing the current blanket "search_docs + graphify before
  grep" mandate with a cheaper-source/ambient-utility rule, but does not activate it. Concurrently,
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` is closing a compliance gap in that exact
  mandate for hand-orchestrated (`agent=claude`) Investigate-phase work. Not resolved here: whether
  the drafted instruction change should wait until the hardening ticket's fix is verified in a
  retro window (avoiding drafting a relaxation of a rule whose enforcement is still being repaired),
  or whether the two can proceed independently because the drafted change is inert until separately
  activated. Flagged for the reviewer who ratifies Phase 0's instruction-change draft.
- All 6 items in proposal §24 remain open: (1) whether to ratify caching bounded/redacted
  answer/context payloads from allowlisted source types, (2) canonical repository/branch identity
  format, (3) which Graphify relation types are eligible for deterministic answers, (4) the packet
  token-counting method/budget classes/tolerance, (5) whether `data/lab_knowledge` is eligible for a
  future read adapter, (6) the authoritative committed location for future human-approved reusable
  knowledge.

## Implementation Notes
(pending — scope-only epic; no direct implementation)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
