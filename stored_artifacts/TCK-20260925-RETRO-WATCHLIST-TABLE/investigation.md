---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260925-RETRO-WATCHLIST-TABLE
artifact_type: investigation
tags: [agent-monitoring, documentation, process-improvement]
---

# Investigation — TCK-20260925-RETRO-WATCHLIST-TABLE

## Current state of `docs/agent-monitoring/README.md`

Read the file in full. Between `## What It Does NOT Capture` and `## Recording coverage for a
hand-orchestrated closure` there are 7 `##`-level sections matching the accretion pattern the
ticket names:

1. `## Baseline Metrics Snapshot (one-off)`
2. `## Knowledge Gateway MCP Phase 0 Measurement Baseline` — already reads "Removed by
   `TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL`"
3. `## Security Gate Firing Check`
4. `## Skill Usage Metric`
5. `## Done-Ticket Monitoring Coverage Audit`
6. `## Agent Tool-Usage Baseline`
7. `## Bash Command Mix Baseline`

## Per-section classification (ticket's Open Question 2)

Read each section's actual content, not its heading, against the test: does it record *a specific
baseline value, at a specific ref, with an intended future check-by point*, or does it *permanently
document a standing tool's existence and behavior*?

| Section | Content shape | Classification |
|---|---|---|
| Baseline Metrics Snapshot | Describes `retrieval_baseline_metrics.py`'s purpose and report sections. No baseline value or check-by point stated. | **Durable** — tool documentation |
| KGMCP Phase 0 Baseline | States the tool was removed; points to a historical doc. Fully resolved already, nothing left to check. | **Answered, and already pointed elsewhere** — remove the stub, not migrate it |
| Security Gate Firing Check | Describes a standing pass/fail script, rerun indefinitely. No one-time check-by point. | **Durable** |
| Skill Usage Metric | Ticket's own text names this one explicitly as a likely-durable example. Confirmed: describes a standing per-skill metric with two already-integrated recurring-cadence feeds. | **Durable** |
| Done-Ticket Monitoring Coverage Audit | Two dated re-run snapshots (2026-08-05, 2026-09-04) of an ongoing, rerunnable-indefinitely audit — not a single measured baseline with one future check-by point. | **Durable** |
| Agent Tool-Usage Baseline | Documents a standing sizing tool plus 2 already-shipped rollout waves built on it. No unresolved future check-by point stated. | **Durable** |
| Bash Command Mix Baseline | Documents the tool's *capability* to do a before/after comparison for the two Batch-B advisory-hook tickets. No specific baseline number + ref is actually recorded in the prose (unlike the delivery-cost case below) — nothing concrete to put in a table row yet. | **Durable** (the tool's existence is documented; a future before/after measurement, if taken, would be a new watchlist row filed at that time) |

Net: 6 of 7 sections are durable tool documentation and stay as prose, unchanged in substance. Only
the KGMCP stub is removed outright (its "fact" — that it was removed, and why — already lives at
`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`, cited from the
stub's own text, so nothing is lost by deleting the stub). **No prior AC1 commitment is lost**: none
of the 6 durable sections carried an actual measurement-commitment fact that the table needs to
hold; they document standing tools, which is what durable prose is for.

## Seed row (Open Question 1 — user has ruled: seed it)

`tickets/done/TCK-20260924-DELIVERY-COST-MEASUREMENT.md`'s Test Summary records the one qualifying
commitment in this whole file: a real, ref-pinned baseline —

```
gh_calls_per_pr: 16.04 @ SHA 0e0ff8f2172634226b1e8a04338fec8b5972a2c6 (W30–W39, origin/main)
```

— with an explicit statement that no "after" was attempted, because the epic's own delivery tooling
(`gh pr create` via `pr_render.py`, `pr_status.py` for CI polling) was not in use while the tickets
that produced this baseline were themselves being built. That caveat must travel with the row: an
"after" measured from *this same implementation batch's* corpus would still not be a valid
comparison, for the identical reason — this batch also predates real day-to-day use of the epic's
tooling by anyone other than its own implementers.

## Retro skill (`.claude/skills/agent-monitoring-retro/SKILL.md`)

`## What This Skill Does` is a 3-step numbered list (run `make agent-monitoring-retro`, read/
summarize sections, fill `## Notes`). `## Related` is a footer of plain links
(`docs/guides/agent_monitoring.md`, `docs/agent-monitoring/schema.md`, `tools/agent-monitoring/
query.py`, the retro-nudge hook) — confirmed: **no mention of `docs/agent-monitoring/README.md`
anywhere in the skill file**, exactly as the ticket states. Adding the watchlist-check as a new
numbered step (not a `## Related` entry) is a real, mechanical, low-risk edit to an existing
markdown list.

## Placement (Open Question 3)

The 7 one-off sections currently sit directly after the recurring-cadence material (`## What It
Does NOT Capture`'s `cost_proxy_score` calibration note, and the `weight_sensitivity_check.py`
paragraph) and before the durable standing-tool sections. Placing the new watchlist table in that
same slot — replacing the KGMCP stub's old position — means a reader who already knows to look
there for "one-off things to check" finds the same thing in the same place, just correctly shaped
now.
