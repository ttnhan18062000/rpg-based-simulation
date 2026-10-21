---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT
phase: open
date: 2026-10-21
tags: [ai, governance]
---

# TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT

## Title
Role cards show a role's single files in a folder it doesn't otherwise own as "dir/ (N files)", so the card budget can come back down from 440

## Status
OPEN

## Tier
hotfix

## Type
refactor

## Priority
P3

## Request Summary
Owner decision of 2026-10-21, relayed by lead-planner: file this as a follow-up and don't dispatch it yet.

Every new explicit `owns` entry in `registries/session_roles.yaml` makes the generated role cards longer. The card budget was raised from 400 to 415 on 2026-10-20 (TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS). It was raised again from 415 to 440 on 2026-10-21 (TCK-20261021-SESSION-ROLES-OWN-OBSERVABILITY-DOCS-AND-UNOWNED-ROOTS). That second ticket added explicit file entries under `docs/observability/` and pushed 9 of 25 cards over 415. Brace folding barely helps, because the files share no parent glob.

## Scope
1. `tools/sessions/card.py`: when rendering a role's `Owns:` line, group the explicit single-file entries that sit in a directory the role does not own as a whole (no `dir/**` in its owns). If a group has two or more files and rendering it as `dir/ (N files)` is shorter than the brace form, render it that way. Single files in a directory the role already owns, and files alone in their directory, render as today.
2. The card tells the reader where the exact list lives: `route.py` stays authoritative. One short phrase for the whole card, not one per group. Keep the wording within budget.
3. Regenerate `.claude/agents/`. Measure every card before and after with `compose_card` + `estimate_tokens`.
4. Lower `CARD_BUDGET_TOKENS` as far as the measured worst card allows, with headroom of at least 10 tokens. The target is 415 or less. Update the docs and tests that quote the number.

## Out of Scope
- Any change to `registries/session_roles.yaml` ownership or `route.py` behaviour.
- Trimming the domain or function card text.

## Acceptance Criteria
1. A unit test covers grouping (2+ files in an unowned dir -> count), a single file (unchanged), files in an owned dir (unchanged), and the brace-shorter case (unchanged).
2. `generate_agents --check`: no drift. The card-budget test passes at the lowered budget.
3. The PR body has a per-card before/after token table and the new budget. The owner confirms the budget number on the PR.
4. `route.py` output for every tracked path is unchanged (diff before/after).

## Related Tickets
- TCK-20261021-SESSION-ROLES-OWN-OBSERVABILITY-DOCS-AND-UNOWNED-ROOTS (raised 415 -> 440; parent)
- TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (400 -> 415)
- TCK-20261013-SEARCH-MCP-FILES-OWNED (`_fold_same_dir_files` brace folding)

## Related Docs
- `docs/guidelines/session_roles/`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/sessions/card.py`, `tools/sessions/generate_agents.py`, `tests/tools/test_session_cards.py`, `.claude/agents/session-*.md`

## Assumptions / Open Questions
- Not dispatched yet, by the owner's decision. Dispatch it when the owner or lead says so, and claim it on #634 first.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
