---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT
phase: open
date: 2026-09-16
tags: [ai, process-improvement, setup]
---

# TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT

## Title
Establish per-session isolation and a *proven* revert path for Headroom before anything is enabled —
its state is machine-wide, so an unisolated trial affects every concurrent session at once

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
First child of `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`, and it **blocks every other child**.

Headroom's state is per-user and machine-wide, not per-session or per-worktree: `~/.headroom`
(`HEADROOM_WORKSPACE_DIR`), `~/.headroom/config` (`HEADROOM_CONFIG_DIR`), plus the savings-ledger
(`HEADROOM_SAVINGS_PATH`) and learned-pattern (`HEADROOM_TOIN_PATH`) locations. Upstream
configuration docs state config "applies globally to the proxy instance or SDK client — not
per-user, per-project, or per-directory."

This machine routinely runs several concurrent Claude sessions across worktrees. One shared store,
one shared config, and one shared learned-pattern set across all of them is **structurally the same
hazard as the confirmed `.claude/current_run` sidecar contamination**, which misattributed
monitoring data to an already-closed ticket for two days
(`project_sidecar_cross_session_contamination`). That precedent is why isolation is a prerequisite
rather than a later refinement.

The user's explicit requirement (2026-09-16): *"make sure we can revert the change if observe the
result is not good enough."* A revert path that has been written but never executed is not evidence
that it works — this repo has catalogued 13+ mechanisms that exist, have tests, and do not do what
they claim.

## Scope
- Determine and record where Headroom actually stores state, **verified from source or `--help`**,
  not from documentation. The CCR page documents behaviour but no paths, TTL, or purge command.
- Establish explicit isolation for any trial session: dedicated `HEADROOM_WORKSPACE_DIR` and
  `HEADROOM_CONFIG_DIR` outside the default `~/.headroom`, so a trial cannot read or write state
  shared with concurrent non-trial sessions.
- Write a revert runbook: exact commands to fully disable Headroom and purge its state.
- **Execute the revert runbook at least once** and record the result. This is the acceptance bar.
- Confirm whether MCP mode shares state with proxy mode, or is independently isolatable.

## Out of Scope
- Installing Headroom into any default or shared configuration, or pointing any existing session at
  it. This ticket establishes the safety envelope; the trial itself is
  `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`.
- `headroom learn` — off for the entire epic (auto-writes to `CLAUDE.md`).
- Proxy mode configuration. Phase 2, and separately BLOCKED.
- Any change to `.claude/settings.json` permissions or `CLAUDE.md`.

## Acceptance Criteria
- [ ] Headroom's real state locations are recorded, each with the source that confirmed it (source
      file, `--help` output, or observed filesystem behaviour) — never a doc page alone.
- [ ] A trial session can run with state confined to a dedicated directory, **demonstrated** by
      showing writes landing there and `~/.headroom` remaining untouched.
- [ ] The revert runbook exists and has been executed at least once, with before/after evidence that
      state is gone and no repository file was modified.
- [ ] The `ccr_store.db` / `HEADROOM_CCR_BACKEND=memory` question is resolved either way and the
      finding recorded — currently unconfirmed, appearing only in third-party summaries.
- [ ] Confirmed whether MCP-mode state is shared with, or independent of, proxy-mode state.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` — the prior confirmed instance of shared-state
  contamination across concurrent sessions; the reason this ticket exists first

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Isolation and
  reversibility section

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.mcp.json` — where an MCP-mode registration would land
- No repository source is modified by this ticket; all state is external (`~/.headroom` or an
  isolated equivalent)

## Assumptions / Open Questions
- Assumed that `HEADROOM_WORKSPACE_DIR` and `HEADROOM_CONFIG_DIR` fully redirect state. If some
  component ignores them and writes to `~/.headroom` regardless, isolation is not achievable as
  designed — **report that rather than working around it**, since it would change the epic's
  viability, not just this ticket's approach.
- Whether an isolated trial is achievable at all while other sessions run concurrently is the real
  question this ticket answers. A negative answer is a valid, useful outcome.

## Implementation Notes
Prefer observing actual filesystem behaviour over trusting either the upstream docs or this ticket.
Several upstream details are absent from authoritative pages or differ between them.

Do not enable anything beyond what is needed to observe where state lands.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
