---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260921-CAVEMAN-CLOSE-OUT
phase: done
date: 2026-09-21
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260921-CAVEMAN-CLOSE-OUT

## Title
Close out Caveman's output-side/input-side proxy as a follow-up: record the verdict against the
real token telemetry, not a re-derived guess

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/plans/agent_infrastructure/headroom_context_compression_trial.md` (lines 29-32, in the
"What doesn't get picked up automatically" note) leaves Caveman's proxy as a "possible follow-up,
deliberately left unticketed" when the Headroom trial concluded. The 14-day real-token retro
recorded in `tickets/done/TCK-20260921-REAL-TOKEN-TELEMETRY.md` (Request Summary, ~line 38) already
settles the question: cache-read tokens are ~78% of cost, average context is 481k/request, and
Bash/grep/git housekeeping (not tool-output size or output tokens) dominates context-attributed
spend. Caveman's proxy targets exactly the two things the retro shows are not the cost lever
(input-side tool-output size, and output-side prose — the latter already ruled out by this same
plan doc's own "Alternate candidate" section, lines 111-116). This ticket records that verdict and
removes the dangling "possible follow-up" note so it stops reading as an open question.

## Scope
- Ticket file recording the verdict, citing the retro figures from `TCK-20260921-REAL-TOKEN-TELEMETRY.md`
  by reference (not re-derived).
- Replace the "What doesn't get picked up automatically" note (plan doc lines 29-32) with a short
  dated verdict line: "Caveman proxy: closed 2026-09-21, not worth it for cost", one-sentence
  reason, and a pointer to the telemetry ticket. Leave the "Alternate candidate" section
  (lines ~85-116) exactly as originally written — it is explicitly preserved as-authored. At most
  add a one-line forward pointer from that section to the new verdict line.
- Standard hand-orchestrated close: `record_hand_orchestrated_closure.py`, `make
  knowledge-index-update` (docs/ changed), stage `docs/REGISTRY.yaml` and `agent-monitoring/`,
  `done_checker_static.py`, mechanism-registry changed-code advisory.

## Out of Scope
- Any new token-reduction mechanism. The real levers identified by the telemetry retro (context
  size, grep/git housekeeping) are a separate conversation, not addressed here.
- Re-opening or re-measuring the Headroom trial itself (already concluded, epic closed).
- Any change to `docs/plans/agent_infrastructure/headroom_context_compression_trial.md`'s
  "Alternate candidate" section content beyond the one-line forward pointer.

## Acceptance Criteria
- Plan doc's "What doesn't get picked up automatically" note replaced with the dated verdict,
  citing `TCK-20260921-REAL-TOKEN-TELEMETRY.md` for the numbers instead of restating them inline
  with new derivation.
- No new numbers are computed or asserted anywhere in this ticket or the doc edit that aren't
  already stated in the cited telemetry ticket.
- "Alternate candidate" section content unchanged except for at most one forward-pointer line.
- Ticket closed per the hand-orchestrated hotfix checklist (monitoring run+event, working_log row,
  registry regenerated and staged, done-checker static conditions pass, mechanism-registry
  advisory run).

## Related Tickets
- TCK-20260921-REAL-TOKEN-TELEMETRY (source of the cited figures)
- TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC (the concluded trial this follow-up hangs off of)

## Related Docs
- docs/plans/agent_infrastructure/headroom_context_compression_trial.md

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
None — documentation-only change.

## Assumptions / Open Questions
None. Scope and verdict are fully specified by the batch brief and the cited telemetry ticket.

## Implementation Notes
Replaced the "What doesn't get picked up automatically" note (plan doc lines 29-32) with a dated
verdict paragraph citing `tickets/done/TCK-20260921-REAL-TOKEN-TELEMETRY.md` by reference only —
no figures re-derived or restated with new computation. The "Alternate candidate" section (which
already separately ruled out the output-side skill) was left untouched, since the brief's own
scope only asked for a one-line forward pointer *if* needed, and the existing verdict paragraph
already links there implicitly via the doc's own structure — no forward pointer was needed since
the "Alternate candidate" section already stands on its own explanation and isn't the section a
reader lands on first.

## Test Summary
Documentation-only change (frontmatter + prose). No code paths touched; no test suite applies.
Verified `docs/REGISTRY.yaml` regenerates cleanly and `make knowledge-index-update` completed
(9 changed files re-embedded, 0 errors).

## Files Changed
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — replaced the dangling
  "possible follow-up" note with a dated closure verdict.
- `docs/REGISTRY.yaml` — regenerated (unconditional post-migration self-check per closure process).
- `tickets/inprogress/TCK-20260921-CAVEMAN-CLOSE-OUT.md` → `tickets/done/`

## Completion Summary
Caveman's context-compression proxy is closed as not worth pursuing for cost, on the evidence
already gathered by the real-token telemetry retro (cache-read ~78% of cost, Bash/grep/git
housekeeping dominating context-attributed spend, not tool-output size or output tokens). The plan
doc no longer reads as leaving an open follow-up; the record now matches the epic's actual
disposition (fully concluded, nothing outstanding).
