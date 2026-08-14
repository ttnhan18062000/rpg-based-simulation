---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP
date: 2026-07-18
tags: [data-quality]
---

# Implementation Plan — TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP

## Summary

Fix the 2 confirmed `"P1: High"` → `"P1"` corrections in
`tickets/done/TCK-20260326-HYSTERESIS.md` and
`tickets/done/TCK-20260326-NARRATIVE.md`. No other drift exists per the
real-check full-corpus scan.

## Steps

### Step 1 — Fix both `## Priority` values

`tickets/done/TCK-20260326-HYSTERESIS.md`: `## Priority\nP1: High` →
`## Priority\nP1`. Same edit in `tickets/done/TCK-20260326-NARRATIVE.md`.
Nothing else in either file changes — no `## Tier` heading is added (see
investigation.md's reasoning: these files predate Tier as a tracked field,
and the check function's own "absent = PASS" design already handles this
correctly without needing the file retrofitted).

### Step 2 — Re-verify corpus-wide

Re-run `check_ticket_field_values` across the full corpus (not just the 2
touched files) and confirm 0 remaining findings.

## Scope Guards

- Do not add a `## Tier` heading to either file — out of scope, would be
  forcing a modern convention onto a genuinely older format.
- Do not touch `TCK-20260326-NARRATIVE.md`'s colon-suffixed `## Status:
  DONE` — already a known, deliberately deferred exclusion.
- Do not touch any other ticket — the scan found exactly these 2, nothing
  else.

## Dependency Map

Single step, no internal dependencies.

## Acceptance Criteria Map

- AC "real check function used, not preliminary count" → investigation.md's
  full-corpus scan.
- AC "every finding fixed or exempted with reasoning" → Step 1 (fixed) +
  investigation.md (Tier-absence and colon-Status exemptions documented).
- AC "zero remaining, independently confirmed" → Step 2.

## Anti-Drift Notes

None beyond what investigation.md already covers — this is a minimal, fully
investigated two-file text fix.
