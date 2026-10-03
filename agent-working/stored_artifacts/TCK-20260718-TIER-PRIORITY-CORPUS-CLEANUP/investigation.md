---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP
date: 2026-07-18
tags: [data-quality]
---

# Investigation — TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP

## Current Behavior (file:line refs)

Ran the real `tools/ticket_field_values.py::check_ticket_field_values`
(shipped by the now-DONE prerequisite ticket
TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM) against every `*.md` file under
`tickets/done/`, `tickets/inprogress/`, `tickets/todos/` (recursive).
**2 FAIL findings, both `## Priority = 'P1: High'`** — exactly matching the
preliminary count from the epic proposal, no additional drift found beyond
it (the "re-scan fresh, don't trust the preliminary count" instruction in
this ticket's own Request Summary was followed and confirmed the same 2).

Both findings: `tickets/done/TCK-20260326-HYSTERESIS.md`,
`tickets/done/TCK-20260326-NARRATIVE.md`. Both are same-era (2026-03-26)
sub-tickets using a genuinely older, simpler section structure — `## Title`
→ `## Priority` → `## Description` → `## Scope` → `## Acceptance Criteria`
→ `## Related Tickets`, with **no `## Tier` heading at all** (confirmed via
`grep -n "^## "` on both files). This is why the check's evidence string
also says `## Tier not present`: `check_body_field_enum`'s "absent section
= PASS" design (a deliberate choice made during
TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM, proven correct by this real-world
case) correctly does *not* flag the missing Tier heading as drift — these
files simply predate Tier being a tracked field, same as
`resource_v2_*.md`'s pre-TCK-naming exemption from earlier drift-cleanup
tickets, and forcing a `## Tier` heading onto them would be exactly the kind
of "retrofit new conventions onto genuinely old files" this session's
established precedent avoids.

`TCK-20260326-NARRATIVE.md` additionally has `## Status: DONE` (same-line
colon-suffixed format) — out of scope, already a known, deliberately
deferred exclusion from `TCK-20260718-STATUS-DRIFT-REPAIR`'s "Colon-Suffixed
Files Decision"; not touched by this ticket.

## Mechanics/Engine Constraints

None — ticket-schema data hygiene, not simulation gameplay.

## Parity Ledger Overlap (IDs + status)

None expected — no `src/` file is touched by this ticket (only two
`tickets/done/*.md` body-text edits), matching the skip-eligibility pattern
every prior pure-data-cleanup ticket this session used
(`parityNoSrcChange && !behavior_changed` → Parity phase skips the
parity-updater agent call).

## Prior Work

- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (this epic, prerequisite,
  DONE) — the check function this ticket runs.
- TCK-20260718-STATUS-DRIFT-REPAIR / -SUFFIX-TRIM / -MULTILINE-FIX (earlier
  today) — the investigation discipline this ticket follows: read the
  actual file before fixing, don't blindly regex-replace, document any
  exemption's reasoning.

## Risks and Open Questions

None remaining — the fix is a clean, mechanical one-line-per-file
correction (`P1: High` → `P1`), both files independently confirmed to have
no other drift, and the scan is corpus-wide, not limited to a preliminary
guess.

## Anti-Drift Hazards

None — this ticket makes no code change, only ticket-body text corrections,
verified via the real (not ad-hoc) check function both before and after.
