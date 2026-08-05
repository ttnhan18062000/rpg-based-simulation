---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN
phase: open
date: 2026-08-05
tags: [skills, workflows]
---

# TCK-20260805-FRONTEND-DESIGN-TRIGGER-REOPEN

## Title
Decide whether frontend-design's CLAUDE.md exclusion should be reopened given renewed real frontend work

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child ticket #9 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. `TCK-20260704-SKILL-TRIGGER-COVERAGE`
explicitly declined to wire `frontend-design` into CLAUDE.md's auto-invoke table, citing "zero
evidence of any frontend/ work in this repo to date." Investigate found 4 real, dated tickets
touching `dashboard-frontend/src/*.tsx`/CSS since 2026-07-17 (CSS cascade fix, table pagination,
dropdown fix, tooltip wiring) — real activity that didn't exist when the original exclusion was
made. However, these are maintenance/bugfix-shaped work, not "build a new distinctive interface,"
which is `frontend-design`'s own stated trigger condition per its `SKILL.md` — so it's not
automatically clear the new evidence changes the original verdict.

## Scope
- Read `frontend-design`'s actual trigger wording in its `SKILL.md` directly.
- Read each of the 4 tickets' real scope (not just titles) to assess whether any of them
  genuinely match the trigger condition, or are all maintenance-shaped as suspected.
- Decide explicitly: reopen (add a CLAUDE.md row) or confirm the exclusion stands, with reasoning
  either way — do not silently carry forward the stale framing.

## Out of Scope
- Re-litigating `SKILL-TRIGGER-COVERAGE`'s original exclusion decision wholesale — only assess
  whether the new evidence changes it.
- Conflating with `SKILL-GATE-CONVERSION-DECISION`'s scope — that's "should an already-included
  skill become a hard gate"; this is "was a skill wrongly excluded," a disjoint question.

## Acceptance Criteria
- [x] Explicit decision recorded: **confirm exclusion stands, do not reopen** — reasoning in
      `investigation.md`, grounded in reading all 4 real tickets' actual scope (not titles).
- [x] N/A (not reopened) — confirmed `SKILL-GATE-CONVERSION-DECISION` never touched CLAUDE.md's
      table either, so no coordination conflict existed regardless.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260704-SKILL-TRIGGER-COVERAGE (the original exclusion decision this ticket re-examines)
- TCK-20260805-SKILL-GATE-CONVERSION-DECISION (soft-coordinate only, no dependency)

## Related Docs
- CLAUDE.md ("Proactive Tool Use" table)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `.claude/skills/frontend-design/SKILL.md`
- CLAUDE.md

## Assumptions / Open Questions
Whether the 4 real tickets actually match the trigger condition is the central open question this
ticket's own investigation resolves — not assumed here.

## Implementation Notes
Read `frontend-design/SKILL.md`'s real trigger wording directly, then read all 4 real tickets'
full Request Summary/Scope (not just titles, per the ticket's own explicit instruction): identified
via `search_docs` + `grep` as `TCK-20260717-CSS-LAYER-PADDING-FIX` (a CSS cascade bug — Tailwind
v4's layer ordering silently zeroing padding utilities app-wide),
`TCK-20260717-TICKETS-TABLE-PAGINATION` (pagination added to an already-built table),
`TCK-20260718-FILTER-SELECT-DROPOUT` (a dropdown state bug fix), and
`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND` (wiring hover tooltips onto existing labels via a new
API). All 4 confirmed maintenance/bugfix/wiring work on an already-built, already-styled
dashboard — none require the aesthetic-direction decision that is `frontend-design`'s own explicit
trigger condition. Decision: **confirm the exclusion stands**, no CLAUDE.md row added — the
original `SKILL-TRIGGER-COVERAGE` verdict's stated evidence ("zero frontend work") is now
technically outdated, but its underlying conclusion (this skill wouldn't apply to this repo's real
frontend activity) is unchanged by the new evidence. Explicitly confirmed
`SKILL-GATE-CONVERSION-DECISION` never touched CLAUDE.md's table either, so no coordination
conflict existed regardless of this decision.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
No code/doc change made — nothing to test beyond confirming the "no reopen" decision was actually
followed through. `git status --porcelain -- CLAUDE.md` → empty, confirming zero diff.
`doc_staleness_check.py` (behavior_changed=False, no files) → PASS. `clean_data_runs_early()` →
PASS. `run_static_precheck('standard', ...)` — all 7 conditions PASS.

## Files Changed
None — this ticket's deliverable is a documented, reasoned decision, not a code/doc change.

## Parity
No files touched at all. No parity ledger entry needed.

## Completion Summary
Resolved the ticket's central open question by reading all 4 real tickets' actual scope, not
assuming from titles — confirmed the suspected hypothesis (all maintenance-shaped, none matching
`frontend-design`'s real trigger) rather than either blindly reopening on the new-activity headline
or blindly trusting the stale original verdict's now-outdated evidence claim. No known material
gap.
