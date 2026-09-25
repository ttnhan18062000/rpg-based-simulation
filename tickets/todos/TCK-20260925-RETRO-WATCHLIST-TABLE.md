---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260925-RETRO-WATCHLIST-TABLE
phase: open
date: 2026-09-25
tags: [agent-monitoring, documentation, process-improvement]
---

# TCK-20260925-RETRO-WATCHLIST-TABLE

## Title

Give `docs/agent-monitoring/README.md`'s accreted one-off measurement sections a single structured
watchlist table, with a removal discipline

## Status

OPEN

## Tier

standard

## Type

refactor

## Priority

P2

## Request Summary

When a change lands whose effect is only observable later in agent-monitoring data, there is no
single place that says "check this at the next retro." The commitment gets written wherever the
work happened — a closed ticket's Completion Summary, a plan section, a one-off `##` heading in
`docs/agent-monitoring/README.md` — and is never surfaced again.

**This is not a missing capability so much as an unnamed one.** `docs/agent-monitoring/README.md`
has already accreted roughly seven sections that are each an instance of exactly this pattern:

- `## Baseline Metrics Snapshot (one-off)`
- `## Knowledge Gateway MCP Phase 0 Measurement Baseline (one-time, separate from both cadences)`
  — since **removed** by `TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL`
- `## Security Gate Firing Check`
- `## Skill Usage Metric`
- `## Done-Ticket Monitoring Coverage Audit`
- `## Agent Tool-Usage Baseline`
- `## Bash Command Mix Baseline`

They share a purpose but no shape: no ticket reference, no baseline SHA in several cases, no "when
is it fair to check this", and no verdict once checked. Each reads as permanent documentation even
after it has been answered. The KGMCP section is the proof of the failure mode — it remained until a
whole ticket was spent removing it.

This ticket gives that set one structure and an explicit removal step. It does **not** introduce a
new document; the information stays where it already lives.

## Scope

1. **Replace the one-off sections with a single watchlist table** in
   `docs/agent-monitoring/README.md`. Each row carries, at minimum:
   - what landed, and the ticket ID that landed it
   - the metric to read, and **its baseline value with the ref/SHA that baseline was measured at**
     (a baseline without its ref is not a valid before/after datapoint —
     `TCK-20260924-DELIVERY-COST-MEASUREMENT` made this its own AC2)
   - when it is fair to check (a date, a week, or a precondition such as "after N PRs have been
     delivered through the new tools")
   - a verdict field, filled once checked
2. **An explicit removal step**: once a row has a verdict and the question is answered, the row is
   deleted. State this in the table's own preamble so it is part of the artifact, not folklore.
3. **A numbered step in the retro skill's own procedure**
   (`.claude/skills/agent-monitoring-retro/SKILL.md`, `## What This Skill Does`) that reads the
   table and checks any row whose check-by condition is now met, recording a verdict.

   **This must be a procedure step, not a `## Related` pointer — verified, and the distinction is
   the whole ticket.** The skill's `## Related` section is a footer of pointers, not
   read-instructions: it lists `docs/guides/agent_monitoring.md` and
   `docs/agent-monitoring/schema.md` and neither is read as part of the numbered procedure.
   `docs/agent-monitoring/README.md` — where all seven existing measurement sections live — **is not
   referenced by the skill anywhere, in any form.** That is the most likely reason the KGMCP
   section rotted until a whole ticket was spent removing it: nothing in the retro workflow was ever
   going to surface it. Adding one more pointer to `## Related` would reproduce exactly that
   failure.
4. Migrate the existing sections into rows, preserving every fact they currently carry. Where a
   section lacks a baseline SHA or a check-by date, record that it is unknown rather than inventing
   one.

## Out of Scope

- **Any blocking gate, ratchet, or threshold on watchlist rows.** Agent-monitoring data is a side
  effect of how work happens, not a simulation feature; a gate over it is disproportionate and turns
  the table into a thing to satisfy rather than a thing to read
  ([[feedback_agent_tooling_checks_proportionate]]). Report-only, always.
- **A new standalone document.** The information already lives in `README.md` and stays there — one
  fact, one place ([[feedback_define_information_once_never_repeat]]).
- **Putting the watchlist in a retro report.** `generate_retro.py` regenerates reports and preserves
  only `## Notes`; a watchlist in a report body would be clobbered. This hazard is real, not
  theoretical — it destroyed 177 lines of a peer's hand-authored review before
  `TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES` fixed the unconditional overwrite.
- **Automating the check itself.** A row says what to read and when; a human or an agent reads it.
  No generator, no scheduled job.
- Changing what the monitoring tools capture, or any existing metric's definition.

## Acceptance Criteria

1. `docs/agent-monitoring/README.md` contains one watchlist table replacing the one-off measurement
   sections; no measurement commitment previously documented there is lost.
2. Every row has a ticket reference, a metric, and either a baseline-with-ref or an explicit note
   that no baseline exists.
3. The table's preamble states the removal rule: answered rows are deleted, not left with a verdict
   in place.
4. The retro skill reads the table as a **numbered step in `## What This Skill Does`** — not as a
   `## Related` footer entry. A reviewer can point at the step that opens it.
5. The file holding the table is reachable from the skill's own procedure. If the table stays in
   `docs/agent-monitoring/README.md`, the step names that path explicitly, since the skill currently
   has no reference to that file at all.
6. Nothing added is blocking; the table has no gate, exit code, or threshold attached.
7. A test or doc check confirms the table exists and is non-empty — light, matching the
   proportionality rule above, not a schema validator.

## Related Tickets

- `TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL` — removed one such section; evidence of the
  accretion problem.
- `TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES` — why this cannot live in a retro report.
- `TCK-20260924-DELIVERY-COST-MEASUREMENT` — recorded a baseline (16.04 `gh` calls/PR at SHA
  `0e0ff8f21`) and explicitly deferred the "after"; the clearest current example of a commitment
  with nowhere to live. See Open Question 1.
- `TCK-20260704-RETRO-LOOP-ENFORCEMENT` — the retro cadence rule this table feeds.

## Related Docs

- `docs/agent-monitoring/README.md` — the sections being restructured
- `docs/guides/agent_monitoring.md` — retro cadence, "Investigate-Step Search-Before-Grep Callout"
- `.claude/skills/agent-monitoring-retro/SKILL.md`

## Related Stored Artifacts

_None yet._

## Related Code Areas

- `docs/agent-monitoring/README.md`
- `.claude/skills/agent-monitoring-retro/SKILL.md`
- `tools/agent-monitoring/generate_retro.py` — read-only context; not modified by this ticket

## Assumptions / Open Questions

1. **Whether to seed the table with the delivery epic's outstanding after-measurement.**
   `TCK-20260924-DELIVERY-COST-MEASUREMENT` recorded 16.04 `gh` calls/PR at SHA `0e0ff8f21` and
   deliberately attempted no "after", because the epic's own tools were not in use while it was
   built. That commitment currently exists only in a closed ticket's Completion Summary. It is the
   most natural first row, but the user scoped this ticket to the restructure itself rather than to
   seeding it — so **propose it, do not add it unilaterally**, and let the user decide.
2. Whether the existing sections are all genuinely watchlist entries. Some (e.g. `Skill Usage
   Metric`) may be durable documentation of a metric rather than a one-time check. Migrating a
   durable section into a table whose rule is "delete when answered" would lose it. Classify each
   before moving it, and leave genuinely durable ones as prose sections.
3. Where the table belongs within `README.md`'s existing structure. It should sit near the cadence
   material rather than at the end, but confirm against the file's actual navigation.

## Implementation Notes

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._
