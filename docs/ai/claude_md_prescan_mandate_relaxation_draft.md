---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, claude-md, process-improvement]
---

# CLAUDE.md Pre-Scan Mandate Relaxation — Proposed Replacement Instruction (Draft for Human Review)

This document is **for human review only**. Nothing in this repository parses it as agent
instructions, nothing in `CLAUDE.md` or any `.claude/agents/*.md` file references it, and no
code or agent behavior in this repository implements or executes what it describes. It exists so
the owner has a concrete, reviewable proposal to evaluate before the current blanket pre-scan
mandate is relaxed — not something already built or activated. This draft is **not activated** and
is **not applied** to any live `CLAUDE.md` or `.claude/agents/*.md` file. Publishing this draft
does not itself decide or imply activation.

## Activation Precondition

This draft's replacement text may not begin to replace any live instruction surface until the
following precondition is satisfied:

`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s compliance fix must be **retro-confirmed** by
`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation section — i.e. a real,
hand-orchestrated Investigate-phase run must recur after the fix shipped, and a subsequent retro
window must show the fix holding.

As of this ticket (`TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT`), that precondition is
**currently pending, not satisfied**. This is not an assumption; it is the freshly regenerated
`agent-monitoring/retro/RETRO-LAST14D.md`'s own finding (`## Notes` section, 2026-08-15T02:24
regeneration): the most recent `agent=claude` Investigate-phase event in the entire corpus predates
the fix landing, so "no hand-orchestrated Investigate-phase run has occurred since the fix shipped,
so there is no real data yet confirming compliance improved for the specific gap this ticket
closed — only that the callout is present and reachable... This is a genuine, honest gap, not a
fabricated pass." This draft cites that report as the source of truth and does not recompute or
fork a parallel compliance metric.

Until a future retro window retro-confirms the fix holding, this draft's Proposed Replacement
Instruction Text below remains inert prose. This document does not itself unblock or advance that
pending signal — it can only move when a real hand-orchestrated Investigate-phase run recurs
naturally and a future retro window picks it up.

## Proposed Replacement Instruction Text

Source: `docs/plans/knowledge-gateway-mcp-proposal.md` §2.1 ("Ambient Utility Positioning"),
lines 93-117.

The gateway (and, generally, direct `rg`, git history, Graphify, and Context Search calls) is a
general repository **ambient utility** — the same conceptual category as `rg`, git history,
Graphify, and Context Search — available during investigation, implementation, debugging,
documentation work, review, refactoring, ad-hoc exploration, and non-ticket sessions.

Ticket ID, workflow name, phase, changed paths, agent role, and run ID are **optional ranking hints**
only. Their absence must never prevent a query or reduce the response to an error.
Workflow integrations may recommend or opportunistically call the gateway, but the gateway is
**not itself a workflow phase, gate, Definition-of-Done item, or mandatory ticket step**.

The tool should reduce the cost of curiosity, not increase the ceremony of investigation. Agents
remain free to bypass it, and remain free to bypass any pre-scan requirement generally, when a
cheaper reliable source is obvious:

- use `rg` for a simple exact text check,
- use Graphify directly for a focused code-reference or dependency question,
- use Context Search directly for a focused document lookup,
- and use the gateway (once it exists) when routing, cross-provider reconciliation, bounded
  context, or safe reuse would provide material value.

This positioning is a prospective policy change from the repository's current blanket Context
Search-plus-Graphify pre-scan rule. It must be proposed as the exact agent-guidance amendment and
reviewed through the repository's normal instruction-generation process before it takes effect.
**Until that amendment is approved and generated, current repository instructions remain in
force; merely drafting or implementing the MCP does not silently override them.** The
`rg`/Graphify/Context Search direct-call bypass guidance above describes tools that are callable
today; the gateway itself (`knowledge_context`/`knowledge_status` MCP tools) is not yet
implemented in `tools/` — only Phase 0 (contract/schema/policy work) is complete for this epic as
of this draft.

## Non-Regression Cross-Reference

A future activation ticket must check this replacement text against **all three** live
instruction surfaces that carry today's blanket mandate. This draft references each for that
future ticket's use and does **not** edit any of them now:

- **`CLAUDE.md`'s `## Context Scan (Mandatory)` section** (currently at `CLAUDE.md:29-40`): the
  numbered 4-step order (`search_docs` → `graphify query` → `knowledge_search.py` fallback →
  check tickets/docs/stored_artifacts), with "Raw grep and direct file reads are follow-up steps
  only — they narrow down what the semantic tools already surfaced. Never start with grep." Not
  edited by this draft.
- **`CLAUDE.md`'s `## Proactive Tool Use` table, "Any investigation" row** (currently at
  `CLAUDE.md:320`): the Step 1/Step 2/Step 3 ordering (`search_docs` → `graphify query` →
  fallback), "never skip it." Not edited by this draft.
- **`.claude/skills/implement-ticket/SKILL.md`'s Step 2 ("Investigate") phase-scoped callout**
  (currently at `SKILL.md:58`): "Search-before-grep is phase-scoped, not satisfied by Step 0 ...
  Step 0's one-time upfront call does not substitute for this phase-scoped call" — the exact,
  currently-hardened mechanism built by `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`, whose
  retro-confirmed compliance is the pending signal this draft's own Activation Precondition is
  conditioned on. Not edited by this draft.

## What This Draft Does Not Do

This document does not modify `CLAUDE.md`, any `.claude/agents/*.md` file, or
`.claude/skills/implement-ticket/SKILL.md`. Activation requires a separate, later ticket, run
through the repository's normal instruction-generation and review process. This document does not
itself unblock or close the pending compliance signal it describes above — that signal can only
move when a real hand-orchestrated Investigate-phase run recurs naturally and a future retro
window confirms it.
