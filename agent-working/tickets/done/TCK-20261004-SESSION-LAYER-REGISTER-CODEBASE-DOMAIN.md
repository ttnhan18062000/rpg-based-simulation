---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-REGISTER-CODEBASE-DOMAIN
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-REGISTER-CODEBASE-DOMAIN

## Title
Register the codebase domain in the session-layer manifest and authority file

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The owner created a `codebase/` domain root on 2026-10-03; `registries/session_roles.yaml` and `session_authority.yaml` do not mention it (verified `git grep codebase` on `origin/main`: no hits).

Source: `docs/plans/codebase_health/handoffs/handoff_to_agent_working.md` (PR #322, codebase-planner, 2026-10-04); structure re-read on `origin/main` by `agent-working-design`.

## Scope
- Add a `codebase` domain overlay owning `codebase/**`, `docs/plans/codebase_health/**`, `docs/guidelines/python_code_standard.md`, `.pre-commit-config.yaml` (and `tests/codebase/**`, with the `ownership_splits` entries the validator requires for overlaps with `tests/**` and `docs/**`).
- Roles per the plan's three-seat model: `codebase-designer` (unstaffed, interim holder recorded), `codebase-planner`, `codebase-implementer`; `codebase` worktree entry with the implementer as the single writer; handover paths; `accepts_dispatch_from`.
- Generated agent files (M1c generator) and cards regenerate; card budget stays unchanged.
- `session_authority.yaml`: function defaults inherit; no grants.

## Out of Scope
- Staffing decisions, launcher behaviour, other domains' overlays.

## Acceptance Criteria
1. The validator passes (globs resolve, no unsplit overlap, one writer, handovers exist) and `generate_agents --check` is clean.
2. Existing role cards unchanged; new cards within budget.
3. Owner confirmed the literal `session_authority.yaml` diff (governing file); recorded in the ticket. Scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- PR #322 handoff; `TCK-20260904-*` monitoring-anomaly ratchet tickets where cited in the validator

## Related Docs
- `docs/plans/codebase_health/handoffs/handoff_to_agent_working.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `registries/session_roles.yaml`, `registries/session_authority.yaml`, `.claude/agents/session-codebase-*.md` (generated), `tools/sessions/`, tests.

## Assumptions / Open Questions
- Two seats versus three: drafted three; the codebase-planner may ask for two. The codebase sessions run on another machine, so their handover note paths need confirming with them.

## Implementation Notes
- `registries/session_roles.yaml` (governing file, owner approved the literal diff directly in this terminal on 2026-10-05): new `codebase` domain owning `codebase/**`, `docs/plans/codebase_health/**`, `docs/guidelines/python_code_standard.md`, `.pre-commit-config.yaml` and `tests/codebase/**`, with routes for `src/**` (rpg-planner), `agent-working/**` and `tools/**` (agent-working-designer) and `tests/architecture/**` (testing-planner); an `ownership_splits` entry for `tests/codebase/**` (rpg and codebase); three roles `codebase-designer`, `codebase-planner`, `codebase-implementer`; and `worktrees: codebase: {writer: codebase-implementer}`.
- **Seat status (owner decision, approved knowing the sessions were unverified):** `ListAgents` showed no codebase session running, so all three seats are `unstaffed`, with interim holders `agent-working-designer`, `agent-working-planner` and `agent-working-implementer` respectively (the validator requires an unstaffed seat to name an existing role). Staffing a seat later is a one-word `seat_status` edit. The owner should know: no `codebase-planner` or `codebase-implementer` session exists today.
- `registries/session_authority.yaml` is unchanged: function defaults inherit and no grants are needed, so the draft's "owner confirms the `session_authority.yaml` diff" had nothing to confirm.
- New `docs/guidelines/session_roles/domains/codebase.md` (card template, not a governing file); `tools.sessions.generate_agents` wrote three new `.claude/agents/session-codebase-*.md`. All existing cards are byte-identical. The first card text was 403 tokens (over the 400 budget), so the template sentence was shortened rather than the budget loosened.
- The `tools/**` route matches the existing `testing` domain's, though `agent-working` itself owns only six `tools/` subdirectories; kept for consistency.

## Test Summary
`tools.sessions.validate`: 0 findings, 12 roles. `generate_agents --check`: no drift. `tests/tools/test_session_*.py` and the capability and settings tests pass. Two pinned counts changed with stated reasons: the roster test now expects twelve seats and five unstaffed (was nine and two), and the generator test expects twelve files (was nine). No budget or validation rule was weakened.

## Files Changed
- registries/session_roles.yaml
- docs/guidelines/session_roles/domains/codebase.md
- .claude/agents/session-codebase-designer.md
- .claude/agents/session-codebase-planner.md
- .claude/agents/session-codebase-implementer.md
- tests/tools/test_session_roster.py
- tests/tools/test_session_agent_generator.py

## Completion Summary
The codebase domain is registered with three unstaffed seats held by the agent-working roles until real codebase sessions exist.
