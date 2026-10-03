---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260925-RETRO-WATCHLIST-TABLE
phase: done
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

1. **Whether to seed the table with the delivery epic's outstanding after-measurement.** —
   **RESOLVED: the user has ruled on this, directly, not via this ticket's own proposal path — seed
   it.** Seeded with the exact figure and SHA from `TCK-20260924-DELIVERY-COST-MEASUREMENT`'s Test
   Summary, plus an explicit note that this implementation batch's own corpus is also not a valid
   "after" (same reason the original baseline recorded no "after": the epic's tooling wasn't in
   ordinary day-to-day use while these tickets were built either).
2. Whether the existing sections are all genuinely watchlist entries. — **RESOLVED, see
   investigation.md's classification table.** Read each of the 7 sections' actual content (not just
   its heading) against the test "does it record a specific baseline+ref+check-by-point, or does it
   permanently document a standing tool": 6 of 7 are durable tool documentation and stay as prose,
   unchanged. Only the already-answered, already-pointed-elsewhere Knowledge Gateway MCP stub is
   removed outright (nothing left to check; its historical fact already lives at
   `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`, cited from the
   stub's own text).
3. Where the table belongs within `README.md`'s existing structure. — **RESOLVED**: placed in the
   exact slot the one-off sections already occupied (right after `## What It Does NOT Capture`'s
   cadence material, before the durable standing-tool sections) — a reader who already knows to look
   there for "one-off things to check" finds the same thing in the same place.

## Implementation Notes

Full reasoning in `staging_artifacts/TCK-20260925-RETRO-WATCHLIST-TABLE/{investigation,plan}.md`.
Summary: read all 7 candidate sections' actual content rather than assuming the heading list from
the Request Summary was itself the final migration list — that read is what produced the 6-durable/
1-removed/1-new-table split, not a blanket "migrate everything named" pass. The retro skill's `##
What This Skill Does` gained a 4th numbered step naming `docs/agent-monitoring/README.md`'s watchlist
table explicitly, per AC4/AC5's requirement that this be a real procedure step, not a `## Related`
footer line (confirmed by reading the skill file first: it had zero references to that path
anywhere, exactly as the ticket's Scope item 3 states).

## Test Summary

- New `tests/tools/test_agent_monitoring_readme_watchlist.py` (6 tests, light per the ticket's own
  "not a schema validator" instruction): watchlist heading + non-empty table exist; KGMCP stub
  removed; seeded row carries its baseline number, SHA, and the "not this batch either" caveat; all
  6 durable section headings still present; removal rule stated in the table's preamble; the retro
  skill's numbered procedure (not its `## Related` footer) names the README path. `/home/u24desktop/
  Working/rpg-based-simulation/.venv/bin/python3 -m pytest
  tests/tools/test_agent_monitoring_readme_watchlist.py -v` — **6 passed**.
- Checked for other test coupling to the removed KGMCP stub text or the README's exact structure
  (`grep -rln "agent-monitoring/README.md\|Knowledge Gateway MCP" tests/ ...`) — every other hit is
  about the separate, unrelated Knowledge Gateway MCP project's own docs/contracts, not this specific
  README section. None fail.

## Files Changed

- `docs/agent-monitoring/README.md` — removed the answered KGMCP stub; added `## Measurement
  Watchlist` with its preamble and one seeded row in the same slot.
- `.claude/skills/agent-monitoring-retro/SKILL.md` — `## What This Skill Does` gained step 4.
- `tests/tools/test_agent_monitoring_readme_watchlist.py` (new) — 6 tests.
- `staging_artifacts/TCK-20260925-RETRO-WATCHLIST-TABLE/{investigation,plan,test_plan}.md` (new).
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

Replaced the accreted one-off measurement sections' failure mode (permanent-looking documentation
of an already-answered question, the exact shape that let the Knowledge Gateway MCP section rot
until a whole separate ticket removed it) with a single, structured watchlist table carrying an
explicit removal rule in its own preamble, plus a real numbered step in the retro skill's own
procedure that reads it — not a `## Related` footer pointer, which the ticket's own Scope item 3
names as the reason nothing was ever going to surface the old KGMCP section on its own.

Classified all 7 candidate sections by actual content rather than by name: 6 are durable standing-
tool documentation (left as prose, unchanged) and 1 (KGMCP) was already fully answered and pointed
elsewhere, so it was removed outright rather than given a table row with nothing left to check.
Seeded the table with the one real, ref-pinned commitment on file
(`TCK-20260924-DELIVERY-COST-MEASUREMENT`'s 16.04 `gh` calls/PR baseline at `0e0ff8f21`), per the
user's direct ruling, carrying forward the caveat that this implementation batch's own corpus is
also not a valid "after" measurement, for the identical reason the original baseline recorded none.

No known material gap. `data_runs_clean` is expected to FAIL again on this close for the same
pre-existing, not-this-ticket's-own reason tracked by `TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS`.
