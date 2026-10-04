---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-OWNER-DECISIONS
phase: done
date: 2026-10-04
tags: [architecture, documentation, planning]
---

# TCK-20261004-VISUAL-ASSETS-M1-OWNER-DECISIONS

## Title
Record the owner's `AM-M1` decisions (roles, key derivation, retirement, ranges, variant axes, retention) in the ADR, the register and the docs they touch

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child 2 of `TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK`. The user answered eight blocking questions on 2026-10-04; the
parent's table is the exact text. Record them where the repo keeps decisions, and update the register rows that
they resolve.

## Scope
- `docs/architecture/visual_asset_foundation_adr.md` "Decisions": new rows after D12, same columns (decision, status
  `**decided (user, 2026-10-04)**`, why, reverse when). Suggested grouping, adjust if the table reads better:
  - D13 roles: nhan (owner) holds every role (`W03.4`, `W05.4`, `W08.5`); approver/audit separation accepted as a
    stated limit. Reverse when a second person joins.
  - D14 key derivation (`W02.2`): frontend, from read-model fields, owner nhan; the API never carries visual keys;
    built at `AM-M6`. `TERRAIN_DRAFT_KEYS` stays the dev-only draft page's mapping until then.
  - D15 retirement (`W07.7`): never retire candidates or primitive fallbacks; old client paths retire by deploying a
    newer frontend. Reverse when release count matters.
  - D16 ranges (`W03.5`, `W07.3`): not needed under Profile A. Reverse on Profile B or a second renderer.
  - D17 variant axes (`W03.1`): frozen empty; the detail axis (D11) is the only variant mechanism; a context axis
    needs its own decision; `verify` enforcement is a parked code follow-up.
  - D18 retention operations (`W10.4`, `W10.6`, `W10.7`): single operator, no lock; `gc --delete` prints what it
    removed and keeps no record (it cannot delete tracked state); owner reviews growth by hand above 50 MB tracked
    catalog. Reverse when a second operator or automation runs store commands.
- `docs/assets/m1_contract_register.md`: each resolved row re-judged with the ADR row as evidence:
  `W02.2`, `W03.4`, `W05.4`, `W07.7`, `W08.5`, `W10.4`, `W10.6`, `W10.7` to `MET` where the decision meets the clause;
  `W03.5`, `W07.3` to `N/A` citing D16; `W03.1` judged on its clause (a frozen-empty decision may meet "deterministic
  axes/precedence" or may not; say which and why). `W13.3`, `W13.4`, `W13.6` stay `GAP` with a note "carried to
  `AM-M6` (owner, 2026-10-04)". Summary table counts and the "Follow-ups" list updated (resolved lines removed or
  marked; new parked line: `verify` rejects a non-empty `variant_axes`). The "Result" section is **not** touched
  here (child 3).
- `docs/assets/retention_and_rollback.md`: the single-operator rule, the `gc` output note and the 50 MB review line.
- `docs/assets/store_contract.md` "Known gaps": approver/audit separation now an accepted limit (D13); no lock by
  rule (D18).
- `docs/assets/pilot_charter_am6.md`: **section 2 (agent-filled facts) only**, a line pointing at D13 (roles decided,
  charter still to be signed). Sections 3 and 5 stay `TO BE SIGNED BY OWNER`.
- `make knowledge-index-update` (worktree env var as in child 1).

## Out of Scope
- Any change outside `docs/` and `agent-working/`, including the parked code follow-ups.
- The charter's human fields and signature; the `AM-M1` result; any decision not in the parent's table.

## Acceptance Criteria
- [x] Each of the eight decisions appears once in the ADR with date and source, and each resolved register row cites
  its ADR row.
- [x] No `GAP` row changes without a decision or evidence that meets its clause; `W13.3/4/6` unchanged in verdict.
- [x] Register summary counts add up to 68 clauses.
- [x] Frontmatter valid; knowledge index updated.

## Related Tickets
- Parent: TCK-20261004-EPIC-VISUAL-ASSET-M1-UNBLOCK

## Related Docs
- docs/architecture/visual_asset_foundation_adr.md, docs/assets/m1_contract_register.md,
  docs/assets/retention_and_rollback.md, docs/assets/store_contract.md, docs/assets/pilot_charter_am6.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-M1-OWNER-DECISIONS/ (plan, investigation, test_plan)

## Related Code Areas
- Read only: visual_assets/store/cli.py (`gc` branch prints each removed item), visual_assets/store/gc.py

## Assumptions / Open Questions
- 50 MB is the default the user accepted in the option text; it is a review trigger, not an enforced limit.

## Implementation Notes
ADR rows D13-D18 added after D12; register rows re-judged. `GAP` to `MET`: `W02.2`, `W03.4`, `W05.4`, `W07.7`, `W08.5`, `W10.4`, `W10.6`, `W10.7`. `GAP` to `N/A`: `W03.5`, `W07.3` (D16). Totals now 55 MET, 7 GAP, 6 N/A (was 47/17/4), 68 rows.
Judgments the planner should check: `W03.1` **stays `GAP`** (D17 freezes `variant_axes` empty but nothing rejects a non-empty one, so determinism rests on a rule, not code); `W05.4` and `W08.5` are `MET` as "named, one person holds every role", with separation stated as not achieved; `W10.4`/`W10.6` are `MET` by decision with the note that code and records do not enforce or keep them. `W13.3/4/6` stay `GAP`, carried to `AM-M6`.
Also: `retention_and_rollback.md` "Store operations" section, `store_contract.md` known gap, one charter section 2 line (roles decided, not signed). Register "Result" and the charter's section 1 `AM-M1` row are untouched (child 3). New parked line: `verify` rejects a non-empty `variant_axes`.

## Test Summary
Docs-only. Row recount by script: 68 rows, 55/7/6, equal to the Summary. Frontmatter, docs/static tests and the index: see the commit.

## Files Changed
- `docs/architecture/visual_asset_foundation_adr.md`, `docs/assets/m1_contract_register.md`, `docs/assets/retention_and_rollback.md`, `docs/assets/store_contract.md`, `docs/assets/pilot_charter_am6.md` (section 2 only)
- `agent-working/tickets/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-M1-OWNER-DECISIONS/`, `docs/REGISTRY.yaml`, monitoring shards

## Completion Summary
Done. Eight decisions recorded (six ADR rows, plus the M0 authorization in its record and the W13 carry in the register). `GAP` rows changed only where a decision met the clause. `AM-M1` result untouched.
