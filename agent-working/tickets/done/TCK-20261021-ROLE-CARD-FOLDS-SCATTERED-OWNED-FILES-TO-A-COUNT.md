---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT
phase: done
date: 2026-10-21
tags: [ai, governance]
---

# TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT

## Title
Role cards show a role's single files in a folder it doesn't otherwise own as "dir/ (N files)", so the card budget can come back down from 440

## Status
DONE

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
- The owner released the 10-21 hold on 2026-10-26 (#715 issuecomment-6401480227, relayed by lead-planner). Dispatched in the agent-working ubuntu batch with TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION and TCK-20261015-SESSION-BINDINGS-TORN-TAIL.
- Since filing, the budget went to 460 (2026-10-22) and three rpg `-ubuntu` twins were added (#737), and the lead card gained a cross-host clause (#742). The 415 target may not be reachable: lower to the measured worst card + at least 10, and say in the PR what the worst card is and why.

## Implementation Notes
`tools/sessions/card.py`: `_count_scattered_files` turns two or more plain files in a directory the role does not own as a whole (no `dir/**` or ancestor `**`) into one `dir/ (N files)` entry at the first member's place, when that is shorter than both the brace and the merged-sibling form. Wildcard globs and a file alone in its directory are untouched. The note ``(N files: a count; exact list via `route`)`` is added once per card, and only when it pays for itself (counted owns text plus the note shorter than the plain text), so no card grew: the three testing cards would have by +23 tokens with an unconditional note.
Budget: worst card before 460 (agent-working-implementer, agent-working-planner-u24), after 446 (same two). `CARD_BUDGET_TOKENS` 460 -> 456 (worst + 10). The 415 target was not reachable: 3 `-ubuntu` twins and the lead clause came after the ticket was filed, and the longest cards are mostly function and domain text, not owns lines. The owner confirms 456 on the PR.

## Test Summary
- `route` diff over all 18,368 tracked paths (status, domains, seats, matched glob), before vs after: identical (`registries/`, `route.py`, `roster.py` also have no diff against origin/main).
- Cards: 32 measured with `compose_card` + `estimate_tokens`, before (origin/main `card.py`) and after; none grew; 16 shrank (-13 to -21 tokens) and 16 are unchanged (see the PR table); `generate_agents --check` 0 drift.
- New tests in `tests/tools/test_session_cards.py`: grouping, single file, owned directory, brace-shorter, wildcards, note only when it pays. Full `tests/tools` + `tests/docs` + `tests/codebase/test_repo_root_allowlist.py`, serial, on the tree merged with origin/main 3533fde71 (2026-10-26, MemoryMax 3G): 5338 passed, 58 skipped, 2 xfailed, 4 failed in 32 min. All four were the 60 s resource-budget timeout on a loaded host: three session validation tests (fixed by TCK-20261026-VALIDATE-SPLIT-GLOBS-EXPANDED-ONCE, rerun green) and `test_wall_clock_inventory.py::test_cli_runs_are_byte_identical_and_do_not_import_src` (parses all of src/ twice; not touched by this batch; passed in a 4-test rerun, 60 s again under load).

## Files Changed
tools/sessions/card.py, tests/tools/test_session_cards.py, tests/tools/test_session_platform_domain.py, docs/guidelines/session_roles/host_suffixed_twins.md, .claude/agents/session-*.md (16 regenerated)

## Completion Summary
Scattered single files render as `dir/ (N files)`; the worst card fell from 460 to 446 tokens and the budget from 460 to 456, pending the owner's confirmation on the PR. Routing is unchanged.

