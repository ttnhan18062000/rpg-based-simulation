---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260926-HOTFIX-AGENT-MONITORING-SCOPE-BOUNDARY-DOC
phase: done
date: 2026-09-26
tags: [agent-monitoring, observability, documentation]
---

# TCK-20260926-HOTFIX-AGENT-MONITORING-SCOPE-BOUNDARY-DOC

## Title

Document which `.claude/workflows/*.js` files instrument `agent-monitoring/` and why the rest don't

## Status

DONE

## Tier

hotfix

## Type

chore

## Priority

P2

## Request Summary

A read-only investigation during `github-delivery-process-epic` (PR #246, merged as `a5b22a4b5`)
found that 7 of the repo's 11 `.claude/workflows/*.js` files emit zero `agent-monitoring/` run/event
records (`compact-simulation-result.js`, `generate-simulation-setup.js`,
`investigate-simulation-result.js`, `prepare-simulation-execution.js`,
`propose-simulation-enhancements.js`, `register-simulation-result.js`,
`update-knowledge-store.js` — confirmed again directly here via
`grep -c "record_run\.py\|record_events\.py" .claude/workflows/*.js`, same 7-of-11 split). No
evidence of accidental wiring failure was found for any of them, but the boundary was also nowhere
written down as a deliberate design choice — an unnamed gap `docs/agent-monitoring/README.md`'s own
`**Scope:**` line already gestures at ("Claude Code agents only... Not the RPG simulation engine's
Grafana/Loki/Prometheus stack") without naming the actual files on either side of that line. The
user accepted the standing recommendation from that investigation: add one line naming the real
boundary, not instrument the uncovered files sight-unseen.

## Scope

1. Expand `docs/agent-monitoring/README.md`'s `**Scope:**` bullet to name the 4 workflows that
   instrument this system (`create-tickets.js`, `implement-ticket.js`, `implement-epic.js`,
   `simq-audit.js` — the ticket-delivery pipeline) and the 7 that deliberately don't (the
   simulation-lab tooling chain, listed above), stating why: the lab workflows aren't part of the
   agent-orchestration delivery pipeline this system measures.
2. No code change — documentation only, since the boundary is being named, not altered.

## Out of Scope

- Instrumenting any of the 7 uninstrumented workflows — explicitly declined; the investigation
  found no evidence any of them accidentally lost monitoring wiring, and wiring them sight-unseen
  risks recording noise for a subsystem this system was never scoped to measure.
- `docs/agent-monitoring/README.md`'s accreted one-off measurement `##` sections
  (`## Baseline Metrics Snapshot`, `## Skill Usage Metric`, etc.) — `TCK-20260925-RETRO-WATCHLIST-TABLE`
  (filed, unimplemented, in `tickets/todos/`) already owns restructuring those into a watchlist
  table. This ticket only touches the `**Scope:**` bullet near the top of the file, a different
  region than that ticket's restructuring target, so the two do not textually collide — confirmed
  by reading both regions before editing (see Implementation Notes).

## Acceptance Criteria

1. `docs/agent-monitoring/README.md`'s `**Scope:**` bullet names all 4 instrumented workflows and
   all 7 uninstrumented ones, with a one-line reason for the split.
2. No workflow file under `.claude/workflows/` is modified.
3. `grep -c "record_run\.py\|record_events\.py\|recordRun\|recordEvent" .claude/workflows/*.js`
   still shows the exact same 4-instrumented/7-not split after this change (proves the doc edit
   changed nothing about actual behavior).

## Related Tickets

- `TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP` — its own Out of Scope section names this same
  7-file list as "reported separately, not implemented, per the user's explicit instruction that
  this is investigate-and-report only."
- `TCK-20260925-RETRO-WATCHLIST-TABLE` — filed, unimplemented; restructures a different region of
  the same file (the one-off measurement `##` sections). Sequencing note recorded here so a future
  implementer of that ticket isn't surprised by this one's prior edit to the `**Scope:**` line.

## Related Docs

- `docs/agent-monitoring/README.md`

## Related Stored Artifacts

None (hotfix tier, no staging artifacts required).

## Related Code Areas

- `docs/agent-monitoring/README.md`

## Assumptions / Open Questions

None — the 4-vs-7 split was reconfirmed directly against the current `.claude/workflows/*.js` files
before writing the doc line, not taken from the prior investigation's report alone.

## Implementation Notes

Reconfirmed the split directly rather than trusting the prior investigation's report verbatim:
`grep -c "record_run\.py\|record_events\.py\|recordRun\|recordEvent" .claude/workflows/*.js` shows
`create-tickets.js` (2), `implement-epic.js` (7), `implement-ticket.js` (6), `simq-audit.js` (2) as
non-zero, and the other 7 files at 0. Matches the prior report exactly.

Read `docs/agent-monitoring/README.md` in full before editing to confirm the `**Scope:**` bullet
(line 13, above `## What It Captures`) and `TCK-20260925-RETRO-WATCHLIST-TABLE`'s restructuring
target (the `##`-level one-off sections starting at `## Baseline Metrics Snapshot`, well below line
13) are non-overlapping regions of the file — a real git merge between this ticket's branch and
that ticket's eventual implementation branch will not conflict at the text level, even though both
touch `README.md`.

## Test Summary

Documentation-only change; no code behavior changed. Verification is AC3's grep re-run
(see Implementation Notes) — same 4/7 instrumentation split before and after.

## Files Changed

- `docs/agent-monitoring/README.md` — `**Scope:**` bullet expanded to name the 4 instrumented and 7
  uninstrumented `.claude/workflows/*.js` files and the reason for the split.
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

Named a previously-undocumented but deliberate boundary: only the 4 ticket-delivery-pipeline
workflows (`create-tickets.js`, `implement-ticket.js`, `implement-epic.js`, `simq-audit.js`)
instrument `agent-monitoring/`; the 7 simulation-lab workflows don't, and no evidence from the
prior investigation suggested that was accidental. Doc-only change, matching the user's explicit
instruction not to instrument any of the 7 sight-unseen. No known material gap.
