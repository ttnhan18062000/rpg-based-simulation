---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-RETRO-INDEX-REPORTS-ZERO
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality, reporting]
---

# TCK-20260915-RETRO-INDEX-REPORTS-ZERO

## Title
`agent-monitoring/retro/index.md` shows 0 runs for every period report — including ones containing 69, 249 and 300 runs — because rows are keyed by ISO week and never read the reports they link to

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
The retro index is the first file a reader opens, and it contradicts the documents it links to:

| Row | Index claims | The linked report says |
|---|---|---|
| `LAST7D` | 0 runs, 0 DONE | **69 runs** |
| `LAST14D` | 0 runs, 0 DONE | **249 runs, 233 DONE** |
| `LAST28D` | 0 runs, 0 DONE | **300 runs** |
| `ALL` | 1609 runs, 1383 DONE | **1149 runs, 962 DONE (83%)** |

Cause is `tools/agent-monitoring/generate_retro.py::_update_index` (:1885-1925). Every row is
computed from the live corpus at generation time and never parses the report it links to:

```python
week_runs = all_runs if name == "ALL" else runs_by_week.get(name, [])
```

- `runs_by_week` is keyed by **ISO week string**. `"LAST7D"`/`"LAST14D"`/`"LAST28D"` are not ISO
  weeks, so the lookup misses and the row renders as zeros. There is an explicit special case for
  `"ALL"` and none for any other non-week scope, so **every `--days N` report indexes as 0**.
- The `ALL` row uses the unfiltered `all_runs` (1609) while `RETRO-ALL.md`'s own body reports 1149
  after `main()`'s filtering — same label, two populations.

`RETRO-LAST7D.md` and `RETRO-LAST28D.md` have been **tracked in git since 2026-09-06**, so the index
has been reporting "nothing here" over reports containing real work for nine days. Because it never
parses the reports, it cannot notice the disagreement.

## Scope
- Make each index row reflect the report it links to. Either parse the report's own Run Summary, or
  have `main()` hand `_update_index` the per-report figures it already computed.
- Fix the `ALL` row's population mismatch so it matches `RETRO-ALL.md`'s body.

## Out of Scope
- Redesigning the index's columns or the retro report format.
- The weekly (`RETRO-2026-Wnn`) rows, which appear correct — verify before changing them.

## Acceptance Criteria
- [ ] Every index row matches the Run Summary of the report it links to, verified for at least one
      week report and all four non-week reports.
- [ ] A test pins this — the defect is a silent disagreement between two files, so the test must
      compare them rather than checking the index in isolation.
- [ ] Regenerating the index does not change numbers in unrelated rows.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)

## Related Docs
- `agent-monitoring/retro/index.md`
- `agent-monitoring/retro/RETRO-LAST14D.md` (its addendum documents this finding)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` (`_update_index`, :1885-1925; called at :1882)

## Assumptions / Open Questions
- Whether non-week reports were ever intended to appear in the index at all is worth confirming —
  "exclude them" is a legitimate alternative fix to "compute them correctly", though it loses
  visibility for exactly the reports a fortnightly review uses.

## Implementation Notes
Cheap fix, high visibility. Straightforward to verify by regenerating and diffing against each
report's own header.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
