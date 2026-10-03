---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260925-RETRO-WATCHLIST-TABLE
artifact_type: plan
tags: [agent-monitoring, documentation, process-improvement]
---

# Plan — TCK-20260925-RETRO-WATCHLIST-TABLE

## 1. `docs/agent-monitoring/README.md` edits

1. Remove the `## Knowledge Gateway MCP Phase 0 Measurement Baseline` section outright (already
   answered and already pointed at its historical record; nothing left for a table row to hold —
   see investigation.md).
2. Insert a new `## Measurement Watchlist` section in that same slot (immediately after `## What It
   Does NOT Capture`'s existing content, before `## Baseline Metrics Snapshot`), with:
   - A one-paragraph preamble stating the removal rule in the artifact's own words: once a row's
     check-by condition is met and a verdict is recorded, the row is deleted, not left in place with
     a verdict.
   - A markdown table: `| Ticket | What landed | Metric | Baseline (ref) | Check when | Verdict |`.
   - One seeded row for `TCK-20260924-DELIVERY-COST-MEASUREMENT`, carrying the baseline number, its
     SHA, and the explicit "not from this batch's own corpus either" caveat.
3. Leave the other 6 sections (`Baseline Metrics Snapshot`, `Security Gate Firing Check`, `Skill
   Usage Metric`, `Done-Ticket Monitoring Coverage Audit`, `Agent Tool-Usage Baseline`, `Bash
   Command Mix Baseline`) exactly as they are — durable prose, per the investigation's
   classification. Not reworded, not reordered relative to each other.

## 2. `.claude/skills/agent-monitoring-retro/SKILL.md` edit

Add a new numbered step to `## What This Skill Does` (making it a 4-step list), between the existing
step 3 (fill `## Notes`) and the file's closing prose, reading approximately:

> 4. Read `docs/agent-monitoring/README.md`'s `## Measurement Watchlist` table. For any row whose
>    "Check when" condition is now met, record a verdict in that row (or note it is still not yet
>    checkable) — then, once a verdict is recorded, delete the row per the table's own preamble.

This satisfies AC4/AC5 directly: it is a numbered procedure step (not a `## Related` line), and it
names the exact file path.

## 3. Test (AC7 — light, not a schema validator)

New test file `tests/tools/test_agent_monitoring_readme_watchlist.py`:
- Asserts `docs/agent-monitoring/README.md` contains a `## Measurement Watchlist` heading.
- Asserts the table under it has at least one data row (non-empty).
- Asserts the KGMCP stub heading is gone.
- Asserts `.claude/skills/agent-monitoring-retro/SKILL.md`'s `## What This Skill Does` section
  contains the literal path `docs/agent-monitoring/README.md`.

No parser, no schema, no blocking gate — matches the ticket's explicit Out-of-Scope instruction.

## 4. Order of operations

README edit first (the fact the skill step points at), then the skill edit, then the test (which
checks both). No other files touched — this ticket's Related Code Areas are exactly these two docs
plus their own tests.
