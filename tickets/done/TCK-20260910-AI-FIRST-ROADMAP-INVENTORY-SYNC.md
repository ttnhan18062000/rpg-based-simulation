---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260910-AI-FIRST-ROADMAP-INVENTORY-SYNC
phase: done
date: 2026-09-10
tags: [ai, documentation]
---

# TCK-20260910-AI-FIRST-ROADMAP-INVENTORY-SYNC

## Title
Sync `roadmap.md`'s 21-row inventory table with real shipped state

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`'s inventory table is the
intended authoritative "what's left" index for the AI-First Hardening track, but it has drifted:
several items shipped in PRs #141/#145/#149 without their rows being updated, so the table
reports work as outstanding that is actually done.

This is not cosmetic. Determining true status now requires cross-checking `tickets/done/`
against the table item by item — that has been done at least twice in the last few days to
answer "what's next," each time re-deriving what the table was supposed to record. The table
misreporting its own subject matter is the cost being fixed here.

Confirmed drifted as of 2026-09-10 (verify each rather than trusting this list — other sessions
may land changes in the interim):

| Item | Table says | Actually |
|---|---|---|
| 3 — Versioned capability-envelope baseline | outstanding | shipped, `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE` |
| 9 — Model-diverse reviewer, shadow logging | outstanding | shipped, `TCK-20260904-SHADOW-REVIEWER-LOGGING` (PR #141) |
| 11 — `working_log.csv` parser | outstanding | shipped, `TCK-20260904-WORKING-LOG-CSV-PARSER` (PR #141) |
| 12 — Provider-portability conformance test | outstanding | shipped, `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST` (PR #141) |
| 14 — Ticket-claim detection logging | outstanding | shipped, `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` (PR #145) |
| 15 — Phase-level resume design | outstanding | shipped, `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN` (PR #145) |

## Scope
- Update each drifted row to the same `~~struck~~ **SHIPPED** — <ticket>` convention rows 4, 5, 7,
  8, and 10 already use, so the table stays internally consistent rather than gaining a second
  notation style.
- Re-verify every remaining row's status against `tickets/done/` while in there — the six above
  are the ones found on 2026-09-10, not necessarily the complete set by the time this runs.
- Update the running counts in the prose beneath the table (the "N remaining to implement" /
  "still Horizon-2-only" sentences), which are derived from the table and will be wrong once the
  rows change.
- Preserve the distinction rows 10 and 6 already draw between "code shipped" and "acceptance
  signal confirmed" — item 10's real-run confirmation is still genuinely outstanding, so it must
  not be flattened to plain SHIPPED.

## Out of Scope
- Implementing any of the still-outstanding roadmap items themselves (item 1's Waves 2/3, item
  10's real-run confirmation, Bucket B/C items).
- Restructuring the table, changing its columns, or re-bucketing items — status accuracy only.
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` / item 6's own row, which is being handled by the
  KGMCP completion work and will need its own final update when that lands.

## Acceptance Criteria
- [ ] Every inventory row's status reflects real `tickets/done/` state, verified item by item.
- [ ] The struck/**SHIPPED** notation matches the existing convention; no second style introduced.
- [ ] Derived counts in the surrounding prose are recomputed and consistent with the table.
- [ ] Item 10's "shipped code, unconfirmed acceptance signal" distinction is preserved, not
      flattened.

## Related Tickets
- `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE`, `TCK-20260904-SHADOW-REVIEWER-LOGGING`,
  `TCK-20260904-WORKING-LOG-CSV-PARSER`, `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`,
  `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`,
  `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN` — the shipped work the table misses.
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` — item 6's own arc, excluded per Out of Scope.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/`

## Assumptions / Open Questions
- The six drifted rows were identified by cross-checking `origin/main` on 2026-09-10; re-derive
  at implementation time rather than trusting the table above, since it is itself a snapshot of
  the thing being fixed.

## Implementation Notes
- Re-verified all six drifted rows independently against `tickets/done/` before touching anything
  (per the ticket's own Assumptions note not to trust the pre-listed set): all six confirmed
  `## Status: DONE` in their own ticket files, and each `## Completion Summary` genuinely matches
  the roadmap item's described scope (not a partial/adjacent match).
- Also re-verified every OTHER row not flagged by this ticket (item 1's Wave 2/3, item 6, items
  16-21) for additional drift beyond the six listed — found none, except one: **item 7's own
  inventory row already read SHIPPED** (since `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` landed
  2026-09-04), but the surrounding prose's "N remaining to implement" tally had never dropped it —
  a second, independently-found drift instance beyond the ticket's original six. Fixed as a
  documented correction (not a new ship), matching this ticket's own stated purpose.
- Updated rows 3, 9, 11, 12, 14, 15 to the existing `~~struck~~ **SHIPPED** — <ticket>` convention
  (matching rows 2, 4, 5, 7, 8's existing style exactly — no second notation style introduced).
- Added one new dated prose paragraph (2026-09-10) after the existing "Item 2 — shipped
  (2026-09-08)" paragraph, following the doc's own established additive-correction convention
  (each prior status change gets its own dated paragraph rather than rewriting history) —
  recomputed the "remaining to implement" and "still Horizon-2-only" counts from scratch rather
  than incrementally patching the old numbers, to avoid compounding the exact kind of drift this
  ticket exists to fix.
- Updated the Horizon-0/1/2 "Epics and detail docs" section's per-epic status prose (items 3, 7, 9,
  14, 15) and the Horizon-2 standalone-items bullet (11, 12) for consistency with the table and the
  new dated paragraph — left `## Cross-item dependencies`, `## Sequencing rules`, and `##
  References` untouched (none make a status claim that drifted; they describe dependency shape, not
  current status).
- Left item 6's row and all item-6-adjacent prose completely untouched, per this ticket's own
  explicit Out of Scope — that row is being updated by the separate, concurrent KGMCP completion
  work (`TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`).
- Left the original PR #124 investigation-pass snapshot paragraph (lines 51-60, "As of the
  2026-09-04 `create-tickets` investigation pass") and the item-1/item-10 dated paragraphs
  completely unchanged — they are historical, point-in-time records the doc's own convention
  already preserves via additive correction, not something to rewrite.

## Test Summary
- `python3 tools/validate_frontmatter.py docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md --content-type doc` — OK, no violations (frontmatter untouched, `status: active` unchanged).
- `python3 tools/gate_checks/doc_staleness_check.py false <changed files>` — `PASS` (`behavior_changed=False, 0 src/config/workflow path(s) flagged, 1 docs/ path(s) present`).
- `pytest tests/docs/ tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -m "not slow" -q` — 203 passed, 1 skipped, 1 xfailed, 0 failed. No test file references `roadmap.md` directly (confirmed via grep), so no test-content coupling risk from this doc-only change.
- Confirmed via `grep`/manual re-read that no other row's status claim contradicts `tickets/done/` after the edit.

## Files Changed
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (6 table rows updated, 1 new dated prose paragraph, 3 supporting prose sections updated for consistency; frontmatter unchanged)

## Completion Summary
Synced `roadmap.md`'s 21-row inventory table with real `tickets/done/` state: 6 rows (3, 9, 11, 12,
14, 15) flipped to the existing SHIPPED convention, plus one additional drift instance found during
re-verification (item 7's row was already SHIPPED but the surrounding "remaining" count prose had
never been updated) — fixed as a documented correction. Recomputed the remaining-to-implement and
still-Horizon-2-only counts from scratch. Item 10's "shipped code, unconfirmed acceptance signal"
distinction preserved, not flattened. Item 6's row (KGMCP) left untouched per Out of Scope —
handled separately by the concurrent KGMCP completion work.
