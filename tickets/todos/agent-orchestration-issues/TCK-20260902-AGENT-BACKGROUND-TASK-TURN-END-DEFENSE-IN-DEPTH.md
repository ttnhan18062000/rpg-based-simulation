---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH
phase: open
date: 2026-09-02
tags: [workflows, process-improvement]
---

# TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH

## Title
Propagate the "never end turn while your own run_in_background command is still running" warning to all dispatched-agent role files, not just implementer.md/test-scoper.md

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
CLAUDE.md's Hard Rules section already states, project-wide: "If you are a dispatched sub-agent
(not the top-level orchestrator), never end your turn while your own `run_in_background` command
is still running." — and explicitly says this "generalizes" a warning that previously lived only
in `implementer.md`/`test-scoper.md` to every dispatched agent role, since most other role files
have no equivalent of their own.

That generalization was written into CLAUDE.md, but never propagated into the individual
`.claude/agents/*.md` role files themselves. As of this ticket, only 2 of 16 files under
`.claude/agents/` actually mention `run_in_background`:
- `.claude/agents/implementer.md`
- `.claude/agents/test-scoper.md`

The other 14 (`architecture-reviewer.md`, `concern-investigator.md`, `doc-updater.md`,
`done-checker.md`, `investigator.md`, `mechanics-auditor.md`, `parity-updater.md`, `planner.md`,
`security-reviewer.md`, `simulation-analyst.md`, `spec-document-reviewer.md`, `ticket-scoper.md`,
`world-debugger.md`, `world-render-reviewer.md`) carry no explicit reinforcement of this rule in
their own agent-definition text, relying entirely on the dispatching orchestrator's CLAUDE.md
context reaching the sub-agent indirectly.

**Evidence this is a real, recurring, observed failure — not a hypothetical:** during the
2026-09-01 M2 Foundational Systems batch implementation session, a `test-scoper` sub-agent (one of
the 2 files that DOES already carry the warning) still started a `run_in_background` pytest run,
set a Monitor, and ended its turn mid-wait anyway — requiring the orchestrator to detect the stall
and resume it via `SendMessage`. This is at least the 4th distinct occurrence of this exact failure
mode across two sessions (3 earlier instances referenced in `feedback_worktree_by_default`-adjacent
session notes; this 4th instance is the most recent). Since the failure recurred even on a role
file that already has the warning, propagating the warning to the other 14 files is not guaranteed
to fully close the gap — but it closes the largest known blast-radius disparity (14 of 16 role
files currently have zero explicit reinforcement at all) and is the only piece of this actionable
from within the repository (the underlying behavior is a Claude Code model/product tendency, not a
bug in this codebase's own logic — separate `SendFeedback` reports on that behavior have already
been queued from within the sessions that observed it).

## Scope
- Add a short, explicit warning to each of the 14 `.claude/agents/*.md` files listed above,
  matching the substance (not necessarily verbatim wording) of the existing warning in
  `implementer.md`/`test-scoper.md`: never end your turn while your own `run_in_background`
  command is still running; poll it to completion within the same turn instead.
- Keep each addition short (1-3 sentences) and placed consistently across all 14 files (e.g. same
  heading/section position relative to each file's existing structure), so it reads as one
  coherent convention, not 14 independently-worded warnings.
- Do not rewrite or restructure any other part of these 14 files — this is an additive,
  narrowly-scoped insertion only.

## Out of Scope
- Any change to CLAUDE.md itself — its Hard Rules section is already correct and is the source of
  truth this ticket is propagating from, not editing.
- Any attempt to programmatically detect or prevent the underlying behavior at the harness/tool
  level — that is outside this repository's control surface (a Claude Code product/model
  characteristic, not a bug in this repo's own code or workflows).
- Investigating *why* the warning didn't prevent the 4th occurrence on `test-scoper.md` despite
  already being present there — that is a separate, harder investigation (possibly requiring
  product-side changes) and not something a `.claude/agents/*.md` wording tweak can be expected to
  fully solve. This ticket only closes the known files-without-any-warning gap.

## Acceptance Criteria
- [ ] All 16 files under `.claude/agents/*.md` contain an explicit `run_in_background` /
      "never end your turn while a background command is running" warning (verified via
      `grep -L "run_in_background" .claude/agents/*.md` returning zero files).
- [ ] The wording is consistent in substance and placement across all 16 files (spot-checkable by
      a human diff-read, not just grep presence).
- [ ] No other content in any of the 14 newly-touched files was altered.

## Related Tickets
None — this is a fresh, standalone finding from the 2026-09-01 M2 batch implementation session,
not a continuation of an existing ticket.

## Related Docs
- CLAUDE.md (Hard Rules section — source of truth this ticket propagates from)

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/architecture-reviewer.md
- .claude/agents/concern-investigator.md
- .claude/agents/doc-updater.md
- .claude/agents/done-checker.md
- .claude/agents/investigator.md
- .claude/agents/mechanics-auditor.md
- .claude/agents/parity-updater.md
- .claude/agents/planner.md
- .claude/agents/security-reviewer.md
- .claude/agents/simulation-analyst.md
- .claude/agents/spec-document-reviewer.md
- .claude/agents/ticket-scoper.md
- .claude/agents/world-debugger.md
- .claude/agents/world-render-reviewer.md
- .claude/agents/implementer.md (reference precedent — do not modify)
- .claude/agents/test-scoper.md (reference precedent — do not modify)

## Assumptions / Open Questions
- This ticket assumes propagating the warning textually to all agent-definition files is a
  worthwhile defense-in-depth step even though it did not fully prevent a 4th recurrence on a file
  that already had it. If a future occurrence shows the wording itself is not the limiting factor
  at all (e.g. it recurs identically on files that now also carry the warning), that would be
  evidence this ticket's whole approach is insufficient and the real fix lives outside this repo —
  worth revisiting then, not something to solve preemptively here.
- Not yet triaged for tier: filed as `hotfix` (small, mechanical, additive text change with
  self-evident intent across 14 files) — reconsider if scoping/investigation surfaces meaningful
  per-file nuance that would justify `standard` tier instead.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
