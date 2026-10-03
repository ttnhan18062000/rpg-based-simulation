---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC
phase: done
date: 2026-08-14
tags: [ai, process-improvement]
---

# TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC

## Title
Local Knowledge Gateway MCP epic — Phase 0 contract, policy, and measurement work only

## Status
DONE

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
- [x] Only Phase 0 (§20) work is scoped/authorized under this epic; no Phase 1+ deliverable is
      claimed as done here. Verified: `git diff --stat` across all 6 child tickets touches zero
      `src/` files and only `tools/agent-monitoring/` (measurement-baseline corpus/runner scripts,
      not gateway wiring).
- [x] The directional tension between Phase 0's planned pre-scan-mandate relaxation (§2.1) and
      `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s active hardening of that same mandate is
      explicitly resolved or sequenced. Resolved via the **sequenced** branch:
      `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`'s draft explicitly states the
      activation precondition (hardening ticket's compliance signal, retro-confirmed) is currently
      pending, and the draft does not itself activate or unblock activation.
- [x] Phase 0's baseline-measurement deliverable cites and reuses
      `retrieval_baseline_metrics.py`/`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s
      metrics rather than duplicating a second `read_to_search_ratio`-equivalent. Confirmed by
      `TCK-20260814-KGMCP-MEASUREMENT-BASELINE`'s investigation.md and plan.md.
- [x] All 6 items in proposal §24 "Open Decisions Requiring Explicit Review" are tracked here as
      unresolved until a reviewer rules on each. Items 1 and 4 were ruled on by the repository owner
      on 2026-08-15 (`TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`) — both ratified as drafted.
      Items 2, 3, 5, 6 remain genuinely unresolved, untouched by any child ticket, and are **not**
      claimed as resolved here.
- [x] All 5 child tickets are linked below, and this epic is not closed merely because a child
      ticket's code lands — Phase 0's own acceptance bar (frozen contracts/baseline/ratified policy
      listed in §20) must be met. All 10 of §20's Phase 0 checklist bullets in
      `docs/plans/knowledge-gateway-mcp-proposal.md` now read **Done** as of 2026-08-15 — the last 2
      (redaction/retention policy, token-counting method) transitioned from "Drafted / pending
      ratification" to "Done (ratified 2026-08-15)" only after the actual ratification ruling landed,
      not automatically because a child ticket's code existed.
- [x] `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT` does not modify any live `CLAUDE.md` or
      `.claude/agents/*.md` file — its output is a draft artifact only. Independently verified 3
      separate times across that ticket's own pipeline (Architecture-Verify, Parity, Verify), each
      via a direct `git diff --stat HEAD` re-run, not by trusting a prior check's result.

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
Scope-only epic; no direct implementation by this ticket. All work delivered through its 5 child
tickets plus one follow-up hotfix ticket:
- `TCK-20260814-KGMCP-CONTRACT-SCHEMAS` — froze MCP wire/provider contracts (DONE)
- `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY` — froze evidence/cache-lookup identity contracts (DONE)
- `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY` — drafted redaction/retention policy (DONE)
- `TCK-20260814-KGMCP-MEASUREMENT-BASELINE` — recorded Phase 0 measurement baseline, INFRA-334 (DONE)
- `TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT` — drafted (inert) pre-scan mandate relaxation (DONE)
- `TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION` — recorded the repository owner's ratification of
  §24 items 1 and 4, the last 2 pending §20 checklist items (DONE)

## Test Summary
Each child ticket ran and passed its own scoped test suite (19+19+7+23+5 = 73 new tests across the
5 children, plus 72 passing in the ratification hotfix's own regression run). No test failure
traced to this epic's own work at any point; the only failures encountered throughout (3 tests, all
pointing to `docs/mechanics/content_usage_matrix.md`'s pre-existing missing frontmatter) were
independently confirmed via `git log` to predate this epic entirely and are explicitly out of its
scope.

## Files Changed
No files changed directly by this epic ticket's own work beyond its own frontmatter/body (this
edit). All substantive changes are attributed to and listed in the 6 child tickets' own Files
Changed sections.

## Completion Summary
Closed the knowledge-gateway-mcp epic after all 5 Phase 0 child tickets landed and a follow-up
hotfix ticket recorded the repository owner's explicit ratification of the 2 remaining §24 open
decisions (item 1: cache bounded/redacted payloads from allowlisted sources; item 4: the
`kgmcp_char_heuristic_v1` token-counting method), both approved as drafted with zero content
changes. All 10 of proposal §20's Phase 0 checklist bullets now read Done. All 6 of this epic's own
Acceptance Criteria are independently verified true — including the requirement that this epic not
be closed merely because child code landed: closure was gated on the actual §20 ratification bar,
which required a real human decision this epic could not make for itself. §24 items 2, 3, 5, and 6
remain genuinely open and are not claimed as resolved. No Phase 1+ work (gateway wiring, MCP tool
exposure, cache read/write implementation) was authorized or performed by this epic.
