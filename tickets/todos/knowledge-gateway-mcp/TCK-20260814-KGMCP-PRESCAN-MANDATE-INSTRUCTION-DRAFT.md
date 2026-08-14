---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT
phase: open
date: 2026-08-14
tags: [ai, claude-md, process-improvement]
---

# TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT

## Title
Draft (do not activate) the agent-instruction change replacing the blanket search-before-grep
pre-scan mandate with a cheapest-reliable-source/ambient-utility rule, explicitly sequenced against
the pre-scan hardening ticket

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §2.1 and §20 (Phase 0's final bullet) call for
drafting a generated-agent-instruction change that replaces `CLAUDE.md`'s current blanket "call
`search_docs` + `graphify query` before grep/raw reads" mandate with an ambient-utility,
cheapest-reliable-source policy — explicitly **not activated before review**.

This directly touches the same instruction surface that
`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (sibling epic `agent-tooling-integrity-hardening`,
OPEN as of this ticket's creation) is actively hardening: that ticket is closing a real compliance
gap where hand-orchestrated (`agent=claude`) Investigate-phase work skips the mandate entirely (3
confirmed post-fix violations in the 14-day audit window). Drafting a relaxation of the same rule
whose enforcement is mid-repair is not unsafe by itself — the proposal already requires the draft
stay inert until separately activated — but the two tickets must not proceed in ignorance of each
other, and `TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC`'s Assumptions/Open Questions flags this
sequencing as unresolved.

## Scope
- **Investigate (mandatory before Plan):** check the real current status of
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`. Record whether it has landed, and if so,
  whether a follow-up retro window has confirmed its fix holds (per that ticket's own Acceptance
  Criteria, which defers long-term compliance proof to
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation section).
- Based on that finding, choose one of:
  - if the hardening fix has landed and held through a retro window: draft the relaxation with
    explicit non-regression wording that preserves the now-hardened entry point's callout;
  - if the hardening fix has not yet landed or not yet held: draft the relaxation anyway (Phase 0 is
    contract-drafting, not activation) but explicitly record in this ticket that activation must
    wait for the hardening ticket's retro-confirmed fix, and do not treat this ticket as unblocking
    activation on its own.
- Draft the replacement instruction language per §2.1's substance: the gateway (and, generally,
  `rg`/Graphify/Context Search direct calls) is an ambient, phase-agnostic repository utility, not a
  mandatory workflow phase, gate, or Definition-of-Done item; ticket ID/workflow/phase/changed-paths/
  agent-role/run-ID metadata are optional ranking hints only; agents should use the cheapest reliable
  source (a direct `rg` lookup or Graphify query remains preferable when it safely answers the
  question with less work).
- Store the draft as a reviewable artifact (e.g. in this ticket's stored artifacts or a docs/ai/
  proposal doc), explicitly marked not-yet-applied to `CLAUDE.md`.
- Do **not** edit the live `CLAUDE.md` Context Scan section, the Proactive Tool Use table, or any
  agent `.md` file's search-before-grep callout as part of this ticket.

## Out of Scope
- Activating the drafted instruction change (editing live `CLAUDE.md` or `.claude/agents/*.md`) —
  a separate, later ticket per the proposal's own maturity gate.
- Any change to `.claude/agents/investigator.md` (already fixed and verified,
  `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`) or to
  `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s own fix — this ticket only drafts a future
  policy change, it does not touch that ticket's in-flight work.
- Resolving §24's other 5 open decisions — only the sequencing of this specific instruction draft.

## Acceptance Criteria
- [ ] `investigation.md` records the real, current status of
      `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP` (and, if relevant,
      `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation data), not an assumption.
- [ ] The drafted instruction text exists as a reviewable artifact, explicitly labeled not-yet-
      activated, and is not applied to any live `CLAUDE.md` or `.claude/agents/*.md` file.
- [ ] The draft or this ticket's notes explicitly state the activation precondition relative to the
      hardening ticket's status found during Investigate.
- [ ] No `CLAUDE.md` or `.claude/agents/*.md` diff appears in this ticket's `Files Changed` other
      than the new draft-artifact location itself.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (OPEN; hardens the exact mandate this ticket
  drafts a relaxation of — check status before Plan)
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (OPEN; its correlation section is the
  evidence source for whether the hardening fix is holding)
- TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP (DONE; predecessor fix this ticket must not
  regress)
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (sibling epic; parent of the tickets above)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §2.1, §20
- `CLAUDE.md` (§Context Scan, §Proactive Tool Use — reference only, not modified by this ticket)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `CLAUDE.md` (reference only — not modified)
- `.claude/agents/investigator.md` (reference only — not modified)

## Assumptions / Open Questions
- Whether the drafted instruction change should be scoped narrower than §2.1's full ambient-utility
  language (e.g. carve out an explicit exception preserving the hardened `agent=claude`
  hand-orchestration entry point) or left general with an activation precondition — not decided
  here; Investigate's finding on the hardening ticket's status should drive this choice.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
