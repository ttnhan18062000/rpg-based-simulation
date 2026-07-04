---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260704-RETRO-LOOP-ENFORCEMENT
phase: open
date: 2026-07-04
tags: [agent-monitoring, retro, process-improvement, hooks]
---

# TCK-20260704-RETRO-LOOP-ENFORCEMENT

## Title
Add /agent-monitoring-retro skill and a cadence nudge hook — the retro loop has never actually run

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
`docs/guides/agent_monitoring.md` documents the retro cadence rule: run `make agent-monitoring-retro` weekly, after every 5+ completed tickets, or before changing any agent prompt/phase/tier rule. Direct data investigation found this has **never actually happened**: 299 `implement-ticket` runs have completed since `agent-monitoring/` was built (2026-06-12), but `agent-monitoring/retro/RETRO-ALL.md` is a zero-data smoke-test artifact from the tool's initial build day, never regenerated since. Concrete, measurable cost of this gap: 13.3% of events (246/1845) have empty `summary` fields — precisely the "Summary Quality" issue the retro report is designed to surface — and nobody has ever looked, because the report has never been generated for real.

The cadence rule has no enforcement mechanism — it's a sentence in a doc, competing with nothing that would actually remind anyone to act on it. Gate failures are rare (3 total across all history: 2 `DOD_BLOCKED`, 1 `NEEDS_HUMAN_INPUT`), so this isn't about a missed failure pattern — it's that the entire "what to improve" feedback loop this observability system exists to feed has been collecting data into a void.

User decisions (2026-07-04): add a real `/agent-monitoring-retro` skill (not just rely on the `make` target), and add a proactive nudge hook rather than relying on manual cadence discipline or `/loop` setup.

## Scope
- Add `.claude/skills/agent-monitoring-retro/SKILL.md` wrapping `make agent-monitoring-retro` — triggered by `/agent-monitoring-retro`, following the existing skill format (see `python-performance-optimization/SKILL.md` for the frontmatter/structure pattern).
- Add a `PostToolUse` hook to `.claude/settings.json` (mirrors the existing graphify/context-search nudge hooks) that:
  - Counts completed (`final_status`/`status` == `DONE`) `implement-ticket` runs in `agent-monitoring/runs.jsonl` with a `start_ts`/`ts` later than the newest file's mtime under `agent-monitoring/retro/RETRO-*.md` (excluding `RETRO-ALL.md`, which is not a dated weekly report).
  - Once that count crosses 5, injects `additionalContext` reminding to run `/agent-monitoring-retro` — advisory, not blocking, consistent with this repo's existing hook philosophy (nudge, don't halt the workflow).
- Update `docs/ai/skills.md` to list the new skill under "Built-in Skills" or a new "Observability" section.
- Update `docs/guides/agent_monitoring.md` if the enforcement mechanism changes how the cadence rule should be described (e.g., "the hook will remind you" rather than pure human discipline).

## Out of Scope
- Actually running the retro right now to generate a real report over the 299 accumulated runs — that's a one-time catch-up action, not part of building the tooling; can be done manually once this ticket's skill exists, or as a follow-on.
- Fixing the 13.3% empty-summary rate itself — that's a downstream finding a real retro run would surface and prioritize; this ticket only makes it possible to see it going forward.
- A hard block (rejecting further ticket work until retro runs) — explicitly rejected in favor of a nudge, matching this repo's established "hooks nudge, don't block" pattern (see `idea_agent_gate_determinism.md`'s more deliberate discussion of when escalation to a hard block is and isn't warranted).

## Acceptance Criteria
- [ ] `/agent-monitoring-retro` skill exists and runs `make agent-monitoring-retro` when invoked.
- [ ] A new hook counts completed `implement-ticket` runs since the last dated retro report and injects a reminder once the count crosses 5, without blocking any tool call.
- [ ] The hook correctly handles the "no dated retro report has ever existed" case (treats it as if the threshold was already crossed, since 299 runs already exceed 5).
- [ ] `docs/ai/skills.md` and `docs/guides/agent_monitoring.md` reflect the new skill and hook.
- [ ] Existing hooks in `.claude/settings.json` are not modified or reordered — this is purely additive.

## Related Tickets
None.

## Related Docs
- docs/guides/agent_monitoring.md (the documented, never-enforced cadence rule)
- docs/agent-monitoring/README.md
- docs/ai/skills.md
- docs/ai/agent_infrastructure_audit.md (originally flagged hooks as "nudge, don't block" as a governance characteristic — this ticket extends that same pattern to a new case rather than introducing a new philosophy)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- .claude/skills/ (new: agent-monitoring-retro/SKILL.md)
- .claude/settings.json (new PostToolUse hook)
- tools/agent-monitoring/generate_retro.py (existing — wrapped, not modified)
- agent-monitoring/retro/ (existing — where the hook checks for the last dated report)
- docs/ai/skills.md
- docs/guides/agent_monitoring.md

## Assumptions / Open Questions
- The hook's ticket-count check requires reading `runs.jsonl` on relevant tool calls — this should be cheap (small file, simple JSON parse) but worth confirming it doesn't add noticeable latency to every tool call the way the existing hooks don't.
- Whether the reminder should fire on every subsequent tool call once the threshold is crossed (noisy) or only once per session — leaning toward "once per session" but left for the implementer to decide against the existing hook patterns' precedent.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
