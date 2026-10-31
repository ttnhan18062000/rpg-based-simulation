---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-REGISTRY-CHECK-NAMES-AN-UNSTAGED-CLOSING-TICKET
phase: done
date: 2026-10-31
tags: [agent-monitoring, data-quality]
---

# TCK-20261031-REGISTRY-CHECK-NAMES-AN-UNSTAGED-CLOSING-TICKET

## Title
`registry_entry_regenerated` (read-only) fails with `ticket_not_staged` and the working order when the closing `done/` ticket isn't tracked or staged, not with a misleading `entry_absent`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
The design is by agent-working-designer-u24, from a lead-planner-u24 finding (rpg-planner and lane A, #779 closing transcript).
The full draft, with before/after code, is in the main checkout:
`.claude/handover/drafts/registry-check-untracked-closing-ticket-2026-10-31.md`. Dispatch: S4. The owner notes the hotfix is
filed and dispatched once agent-working-planner-u24 OKs it, and chose to skip the optional CLAUDE.md line
(#715 issuecomment-6546038861).

On 2026-10-28, three #779 hand closes FAILed Finalize on `registry_entry_regenerated` alone, with sub-reason `entry_absent`
(gv-9abfa37c0bcd4715, gv-c014c428edd04937, gv-5b86c97e1c394481; recorded as overridden). `generate_registry()` indexes only
`git ls-files` paths unless `include=` names more (by design, TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE).
The read-only branch (`regenerate=False`, the CLI default for every hand run) builds its fresh comparison registry without
`include=`. So an unstaged `done/` ticket is missing from that registry too, and the check says `entry_absent`. That sounds
like a frontmatter or location defect. Running `make docs-registry` alone wouldn't clear it either. The order that works is:
`git add` the ticket, then regenerate, then stage the registry.

Blocking was correct, because the on-disk registry really lacked the entry. The reason and the remedy were wrong. This keeps
the FAIL.

## Scope
Draft §3 and §5, verbatim in substance:
- `tools/gate_checks/done_checker_static.py`:
  - import `indexable_paths` from `generate_registry`.
  - add the helper `_unstaged_closing_ticket(root, ticket_id)`. It returns the `done/` path when the file exists but git
    neither tracks nor stages it, and None when `root` isn't a git top level.
  - in `check_registry_entry_regenerated`, read-only branch, after the `found` PASS return and before the fresh-registry
    block: FAIL with reason class `ticket_not_staged`. The evidence names the path and the order
    `git add <path>` -> `make docs-registry` -> `git add docs/REGISTRY.yaml` -> re-run.
  - the `regenerate=True` path is unchanged.
- `docs/agent-monitoring/schema.md` (~l.716, the `sub_reasons` row for `registry_entry_regenerated`): add `ticket_not_staged`
  with its meaning, as in the draft's AFTER text.
- `tests/tools/test_done_checker_static.py`: the draft's 5 tests (untracked -> `ticket_not_staged`; staged ->
  `registry_stale_on_disk`; staged + regenerated -> PASS; non-git root -> unchanged; `regenerate=True` + untracked -> PASS).
- `docs/parity_ledger/infrastructure.yaml` (~l.4310, the entry whose test_path is the entry_absent test): extend
  `v2_evidence` to mention the new class.

## Out of Scope
- The CLAUDE.md line (draft §4). The owner chose to skip it (#715 6546038861), so don't offer it in the PR body either.
- Making the check include untracked tickets and PASS (draft §6).
- The #779 override records.
- The other causes in #761's retro proposal "Finalize self-check ordering". Of W43's 33 `registry_entry_regenerated`
  FAILs, this ticket answers only the 7 `entry_absent` ones. The 9 `registry_stale_on_disk` and the 17 with no reason
  recorded stay open under that proposal.

## Acceptance Criteria
1. The 5 tests pass. `pytest tests/tools/test_done_checker_static.py tests/tools/test_gate_verdicts.py -q -p no:randomly`
   passes.
2. For an already-staged ticket, the existing reason classes and messages are byte-identical (the test 2 and 5 guards).
3. schema.md lists `ticket_not_staged`, and the parity entry's `v2_evidence` names it.
4. Cross-domain: `docs/parity_ledger/infrastructure.yaml` is rpg's, and `tests/tools/test_done_checker_static.py` is split
   rpg/agent-working (`route`). The PR body names both, and rpg-planner agrees on the PR before merge.

## Related Tickets
- TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE
- TCK-20261020-FINALIZE-SELFCHECK-RECORDS-FAIL-REASON-CLASS
- TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY

## Related Docs
- docs/agent-monitoring/schema.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- tools/generate_registry.py (read only: `indexable_paths`)

## Assumptions / Open Questions
- None open.

## Implementation Notes
- Dispatched by agent-working-planner-u24 (S4, #715 6546038861); design by agent-working-designer-u24 (draft sections 3 and 5). The CLAUDE.md line is skipped by the owner and not offered.
- `done_checker_static.py`: `indexable_paths` is imported, `_unstaged_closing_ticket(root, ticket_id)` added, and the read-only branch of `check_registry_entry_regenerated` FAILs with `ticket_not_staged` after the `found` PASS and before the fresh-registry block, naming `git add <path>` -> `make docs-registry` -> `git add docs/REGISTRY.yaml` -> re-run. The `regenerate=True` path is untouched; a non-git root returns None and keeps today's behaviour.
- `schema.md` sub_reasons row and the `docs/parity_ledger/infrastructure.yaml` entry's `v2_evidence` name the new class (cross-domain: the ledger is rpg's, `test_done_checker_static.py` is split rpg/agent-working).
- This answers only the 7 W43 `entry_absent` blocks; the 9 `registry_stale_on_disk` and 17 with no reason stay open under #761's ordering proposal.

## Test Summary
- `pytest tests/tools/test_done_checker_static.py tests/tools/test_gate_verdicts.py -q -p no:randomly`: 219 passed. The 5 new tests: untracked -> `ticket_not_staged` with the order, staged -> `registry_stale_on_disk`, staged + regenerated -> PASS, non-git root unchanged, `regenerate=True` + untracked -> PASS.

## Files Changed
- tools/gate_checks/done_checker_static.py
- docs/agent-monitoring/schema.md
- docs/parity_ledger/infrastructure.yaml (rpg-owned)
- tests/tools/test_done_checker_static.py (split rpg/agent-working)

## Completion Summary
AC1-3 met: the 5 tests and the scoped pytest pass, staged tickets keep byte-identical reason classes and messages, schema.md and the parity entry name `ticket_not_staged`. AC4: the PR body names both cross-domain paths; rpg-planner agrees on the PR before merge.
