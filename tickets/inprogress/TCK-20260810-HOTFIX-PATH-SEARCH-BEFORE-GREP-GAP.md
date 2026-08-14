---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP
phase: open
date: 2026-08-10
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP

## Title
Close the search-before-grep gap for Investigate-phase work that never spawns the `investigator`
subagent

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP` added an explicit search-before-grep callout to
`.claude/agents/investigator.md` (commit `9d9ed87db7a`, 2026-08-08 12:55 UTC), root-causing the
original gap as "an instruction living only in global `CLAUDE.md` context, with no explicit
callout in the specific agent's own definition, gets skipped under real task pressure." The fix
worked exactly where it was applied: recomputing `compute_tool_safety_metrics` over the 14-day
window post-commit shows **zero** `investigator`-agent Investigate-phase violations.

But 3 post-fix violations remain in the same window, and **all 3 are `agent=claude`**, not
`investigator`:

| run_id::seq | first tool ts (UTC) |
|---|---|
| `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD::2` | 2026-08-08T15:30:09 |
| `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION::2` | 2026-08-08T19:04:19 |
| `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE::2` | 2026-08-09T05:07:49 |

Direct inspection of `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION::2`'s full
tool sequence in `agent-monitoring/tools.jsonl` confirms: 100+ tool calls, straight into
`Read`/`grep`-flavored `Bash`, zero `mcp__knowledge-search__search_docs` or `graphify` call
anywhere in the phase, later hand-editing `docs/parity_ledger/combat_movement.yaml` and
`substrate.yaml` directly. This is Investigate-phase work done directly by the top-level
orchestrating session (`agent=claude`) rather than delegated to the `investigator` subagent — the
identical failure mode the epic-gap ticket already proved, just recurring in a path that
`investigator.md`'s fix structurally cannot reach.

## Scope
- **Investigate (mandatory before Plan):** Determine exactly which real entry point drives this
  `agent=claude` Investigate-phase work — hotfix-tier pipeline routing (per CLAUDE.md's Tier
  Routing table: `hotfix | Scope → Implement → Test → Parity → Verify → Finalize`, which has no
  explicit Investigate phase name at all — confirm whether these 3 runs are actually hotfix-tier,
  or a different hand-orchestration path), or something else. Do not assume; find the real
  dispatch mechanism in `.claude/workflows/implement-ticket.js` or wherever `agent=claude` phase
  labeling originates.
- Add an explicit, non-optional search-before-grep callout at that confirmed real entry point,
  mirroring `investigator.md`'s fix in substance (not necessarily verbatim — the entry point may
  be a workflow prompt template, not an agent `.md` file).
- If the entry point turns out to be "no dedicated instruction surface exists at all for this
  path" (i.e. it's genuinely just the top-level session with only `CLAUDE.md` to rely on), decide
  and document how a per-task-relevant reminder gets surfaced there without hand-rolling a new
  agent definition for a case that may not warrant one.

## Out of Scope
- Any change to `.claude/agents/investigator.md` itself — that fix is verified working; this
  ticket covers a different, non-overlapping path.
- Re-running or re-litigating the 3 already-affected tickets above — they are already closed/done;
  this is forward-looking.
- Redesigning hotfix-tier's pipeline stages — only the search-before-grep instruction gap within
  whatever the real dispatch mechanism is.

## Acceptance Criteria
- [ ] `investigation.md` identifies the real, confirmed dispatch mechanism for `agent=claude`
      Investigate-phase work, sourced from `.claude/workflows/implement-ticket.js` (or equivalent)
      and real `events.jsonl` records — not assumed.
- [ ] An explicit search-before-grep callout exists at that entry point.
- [ ] `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (sibling epic child) can measure
      whether this fix holds in the next retro window — this ticket does not itself need to prove
      long-term compliance, only that the callout is real and reachable.

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP (DONE; predecessor fix, same root-cause class,
  different entry point)
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP (DONE; same shape — hand-orchestration
  bypassing an agent-specific instruction)

## Related Docs
None yet — Investigate phase must confirm the real dispatch mechanism before any doc gets touched.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `.claude/agents/investigator.md` (reference only — not modified by this ticket)
- `agent-monitoring/tools.jsonl`, `agent-monitoring/events.jsonl`

## Assumptions / Open Questions
- Whether all 3 flagged runs share the same dispatch mechanism, or are 3 unrelated hand-orchestration
  shapes that happen to look similar — not assumed; Investigate must confirm before Plan, following
  the same honest-verdict discipline `TCK-20260807-DOC-UPDATER-FIRST-ATTEMPT-BLOCKED-RATE` used
  ("if 3 genuinely unrelated causes are found, that is a valid, honest terminal state").

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
