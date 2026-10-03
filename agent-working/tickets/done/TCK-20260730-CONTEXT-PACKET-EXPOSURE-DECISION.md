---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION
phase: done
date: 2026-07-30
tags: [ai, workflows]
---

# TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION

## Title
Resolve Open Decision 6: should context packets be exposed as an MCP tool, a provider-adapter library, or both?

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Produce a written, reviewable decision document — matching the shape of the epic's prior Open
Decision docs (`docs/ai/default_packet_scenarios_decision.md`,
`docs/ai/shadow_promotion_gate_thresholds_decision.md`) — that resolves Open Decision 6 from
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`:
"Should context packets be exposed as an MCP tool, a provider-adapter library, or both after the
provider-neutral contract is implemented?" This is a decision-document deliverable only — no new
MCP tool, no new adapter library module, no wiring change to any `.claude/workflows/*.js` or
`tools/context_packet_assembler.py` call site.

## Scope
- Author a new `docs/ai/*_decision.md` doc resolving Open Decision 6, grounded in the two real
  precedents that already exist in this repo (`tools/search_mcp.py`'s MCP-tool exposure of
  `search_docs`/`search_health`; the Provider-Adapter Boundary section of
  `docs/architecture/agent_orchestration_contract.md`, status "Decided") rather than reasoning
  from the two option names alone
- Directly verify and state the current status of the decision's own stated precondition
  ("after the provider-neutral contract is implemented") — cite each of the ADR's per-decision
  status lines (`Decided` vs. `Proposed-pending-implementation-evidence`), not just the two
  parent epics' own `DONE` ticket status
- Directly verify and state whether Codex (the second provider) has any live runtime presence in
  this repo today, citing `tickets/todos/codex-runtime-activation/` and
  `docs/ai/codex_capability_matrix.md` §3 (no `.codex/` directory exists in this repo)
- Give a concrete recommendation (not a non-answer) while explicitly flagging which parts of that
  recommendation are contingent on evidence that does not exist yet — mirroring Open Decision 5's
  "recall/provider-parity not fully defensible a priori" framing rather than inventing false
  certainty
- Update `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Assumptions/Open Questions to mark
  Open Decision 6 RESOLVED with a pointer to the new doc, mirroring the Open Decisions 1-5
  convention exactly

## Out of Scope
- No new MCP tool implementation
- No new provider-adapter library module
- No change to `tools/context_packet_assembler.py`, `tools/search_mcp.py`, or any
  `.claude/workflows/*.js` file
- No `.codex/` directory creation or trust decision
- No promotion of any Phase 6 selective-workflow-adoption work — this ticket resolves only the
  exposure-mechanism question, not when/whether it is wired in
- No src/ or workflow code created or modified — Files Changed lists only the new doc plus the
  epic ticket edit

## Acceptance Criteria
- [x] New `docs/ai/*_decision.md` gives a concrete recommendation for MCP tool vs. provider-adapter
  library vs. both, grounded in the two real in-repo precedents (`search_mcp.py`,
  `agent_orchestration_contract.md`'s Provider-Adapter Boundary decision)
- [x] Doc states the current status of each of the ADR's relevant sub-decisions
  (`Contract Representation and Format`, `Provider-Adapter Boundary`, `Conformance Mechanism`) by
  direct citation, not assumption
- [x] Doc states plainly that Codex has no live runtime presence in this repo as of this decision
  (citing `tickets/todos/codex-runtime-activation/` and the capability matrix's "no `.codex/`
  directory" finding), and that this limits how defensible a final, non-contingent answer can be
- [x] Doc explicitly separates what is decided now (the default/primary integration pattern) from
  what remains contingent on future evidence (full production promotion), rather than presenting a
  false-certainty final answer
- [x] `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Assumptions/Open Questions is updated to
  mark Open Decision 6 RESOLVED with a pointer to the new doc, mirroring Decisions 1-5's exact
  convention
- [x] No src/ or workflow code is created/modified — Files Changed lists only the new doc + epic
  ticket edit

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260729-CONTEXT-PACKET-ASSEMBLY
- TCK-20260729-SHADOW-PACKET-CALL-SITE
- TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260721-CODEX-CAPABILITY-MATRIX

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/codex_capability_matrix.md
- docs/ai/shadow_promotion_gate_thresholds_decision.md
- docs/ai/default_packet_scenarios_decision.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/search_mcp.py (read-only reference)
- tools/context_packet_assembler.py (read-only reference)
- tools/hybrid_retrieval.py (read-only reference)
- .claude/workflows/implement-ticket.js (read-only reference — Phase 5's existing shadow-packet
  call-site precedent)
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md

## Assumptions / Open Questions
- The decision's own precondition ("after the provider-neutral contract is implemented") is only
  partially satisfied: the Provider-Adapter Boundary sub-decision in
  `docs/architecture/agent_orchestration_contract.md` is `Decided`, but `Contract Representation
  and Format` and `Conformance Mechanism` remain `Proposed-pending-implementation-evidence` — this
  ticket treats the recommendation below as directional, not final, for that reason
- Codex has zero live runtime presence in this repo as of this decision (no `.codex/` directory;
  real activation work is still in `tickets/todos/codex-runtime-activation/`), so no exposure
  mechanism can be validated against a second real provider yet — mirrors Open Decision 5's
  provider-parity gap

## Implementation Notes

Authored `docs/ai/context_packet_exposure_mechanism_decision.md`, matching
`docs/ai/shadow_promotion_gate_thresholds_decision.md`'s shape (frontmatter, numbered
decision/evidence sections, closing Resolution section).

**Evidence gathered directly, not assumed:**
- Read `tools/search_mcp.py` in full: its own module docstring states "Transport: stdio (Claude
  Code spawns this as a subprocess)" and "Claude Code registers via `.claude/settings.json`" —
  i.e. today's one real in-repo MCP-tool precedent (`search_docs`/`search_health`) is wired
  Claude-specifically, even though the MCP protocol itself is provider-neutral by design.
- Read `docs/architecture/agent_orchestration_contract.md` in full: three per-decision status
  lines cited directly — `Contract Representation and Format` and `Conformance Mechanism` are
  both `Proposed-pending-implementation-evidence`; `Provider-Adapter Boundary` alone is `Decided`,
  with a concrete quoted rule ("adapters may contain provider-specific payload parsing,
  invocation, permissions, and hook registration. They may not silently redefine workflow phases,
  terminal statuses, gate policy, or artifact requirements").
- Read `docs/ai/codex_capability_matrix.md` §1 and §3: Codex's `PermissionRequest`/`PreToolUse`
  hook matchers explicitly support "MCP tool names" as a matcher value (manual lines 9443-9454,
  quoted verbatim in that doc) — direct evidence Codex's hook framework is MCP-tool-aware, i.e.
  Codex can act as an MCP client in principle. §3 separately confirms this repo currently has
  **no** `.codex/` directory — no live Codex runtime presence exists here to test that capability
  against in practice.
- Confirmed via `ls tickets/todos/codex-runtime-activation/` that real second-provider runtime
  activation (`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` and its 4 child tickets) is still
  entirely in `tickets/todos/` — not started, not done.
- Read `tools/context_packet_assembler.py`'s and the Phase 5 shadow-packet call site's own
  precedent (`TCK-20260729-SHADOW-PACKET-CALL-SITE`, `.claude/workflows/implement-ticket.js`):
  the one real integration that exists today is neither an MCP tool nor a formal "provider-adapter
  library" in the ADR's sense — it is a direct in-process Python call from a Claude-specific
  workflow script, gated behind `SHADOW_CONTEXT_PACKET_ENABLED`. This is documented as the
  closest real precedent for the "library" side of the decision, while noting it has not yet been
  generalized into a reusable, provider-neutral library module.

**Recommendation given in the doc (see Resolution section there for full reasoning):**
"Both, but not symmetric" — a provider-adapter library is the default/primary integration
(matches the ADR's one already-`Decided` sub-decision and the one real Phase 5 precedent), MCP
tool exposure is a secondary, optional interface for ad-hoc/interactive queries (matches
`search_mcp.py`'s existing precedent and Codex's confirmed matcher-level MCP awareness). This is
stated as directional, not final, because two of the three ADR sub-decisions remain
`Proposed-pending-implementation-evidence` and zero real Codex executions exist in this repo to
validate provider parity against — the same class of honest limitation Open Decision 5 already
established as this epic's norm rather than an exception.

No deviation from the ticket's Scope/Acceptance Criteria. No `src/`, `tools/`, or
`.claude/workflows/*.js` file was touched. No `.codex/` directory was created.

## Test Summary
Documentation-only ticket — no `src/` or test code was added or modified, so no pytest run
applies. Verification performed instead:
- `python3 tools/validate_frontmatter.py docs/ai/context_packet_exposure_mechanism_decision.md` → OK
- `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` → OK
- `python3 tools/validate_frontmatter.py tickets/done/TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION.md` → OK
- `python3 tools/ticket_field_values.py tickets/done/TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION.md` → no violations
- All factual claims in the new doc were verified against a fresh, direct read of the cited source
  files in this session, not assumed from memory of the prior Phase 2/5 decision docs.

## Files Changed
- `docs/ai/context_packet_exposure_mechanism_decision.md` (new)
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (modified — Open Decision 6
  marked RESOLVED)
- `tickets/done/TCK-20260730-CONTEXT-PACKET-EXPOSURE-DECISION.md` (this ticket, modified — Status/
  AC/Implementation Notes/Test Summary/Files Changed/Completion Summary)

## Completion Summary
Resolved Open Decision 6 with a new decision doc,
`docs/ai/context_packet_exposure_mechanism_decision.md`. The recommendation ("both, not symmetric" —
provider-adapter library as the default/primary path, MCP tool exposure as a secondary/optional
interface) is grounded in two real in-repo precedents (`tools/search_mcp.py`'s existing MCP-tool
exposure of `search_docs`/`search_health`; the `Decided` status of
`docs/architecture/agent_orchestration_contract.md`'s Provider-Adapter Boundary sub-decision) rather
than reasoned from the two option names alone. The doc is explicit that this answer is directional,
not final: two of the three relevant ADR sub-decisions remain
`Proposed-pending-implementation-evidence`, and Codex — the second provider named in the decision's
own precondition — has zero live runtime presence in this repo today (`tickets/todos/
codex-runtime-activation/` is not started; no `.codex/` directory exists), so no exposure mechanism
can be validated against real second-provider evidence yet. `tickets/inprogress/
TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Open Decision 6 entry was updated to RESOLVED,
completing all 6 Open Decisions this epic tracks. No `src/`, `tools/`, or `.claude/workflows/*.js`
file was created or modified, and no `.codex/` directory was created.
