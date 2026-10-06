---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-SESSION-ROLE-TEMPLATES-OWNERSHIP
phase: done
date: 2026-10-06
tags: [ai, process-improvement, governance]
---

# TCK-20261006-SESSION-ROLE-TEMPLATES-OWNERSHIP

## Title
Give the session role-card templates an owner: add `docs/guidelines/session_roles/**` to agent-working's `owns`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
While drafting `TCK-20261006-RPG-IMPLEMENTER-CONTACT-RULE-REPO-HOME`, design found that
`PYTHONPATH=. python3 tools/sessions/route.py docs/guidelines/session_roles/domains/rpg.md` returns
`status: unowned` on `origin/main` (`40ab9857e`). None of the seven role-card templates under
`docs/guidelines/session_roles/` (`domains/{agent-working,codebase,rpg,testing}.md`,
`functions/{designer,planner,implementer}.md`) matches any domain's `owns`. They are session-layer
config, read at runtime by `tools/sessions/card.py` (`TEMPLATE_DIR`), so agent-working owns them in
practice. The owner chose on 2026-10-06 to make that explicit, answering the batch question with the
option "Rpg.md ownership gap: Add docs/guidelines/session_roles/** to agent-working's owns."

## Scope
1. In `registries/session_roles.yaml`, add `docs/guidelines/session_roles/**` to `domains.agent-working.owns`.
   Put it after `docs/plans/agent_infrastructure/**`. Change nothing else in the file.
2. Check that `route.py` now names agent-working for all seven templates.
3. **Card budget.** The agent-working `Owns:` line prints this glob, so step 1 alone puts the cards over budget.
   Design measured this on a scratch tree from `40ab9857e`: on main the agent-working designer, planner and
   implementer cards are 396 / 400 / 399, and with the glob they are 406 / 409 / 409. The budget is 400. The
   owner chose on 2026-10-06 to fix this with "Trim card + compact globs":
   a. Replace the `## Card` text of `docs/guidelines/session_roles/domains/agent-working.md`, using this exact text (owner-confirmed):
      - Current:
        > Domain: agent-working (process, tooling, monitoring, delivery). Others report process problems here; it decides what to ticket. Owns the tooling around `registries/mechanisms.yaml`, not its content. Designer reviews.
      - New:
        > Domain: agent-working (process, tooling, monitoring, delivery). Process problems come here; it decides what to ticket. Owns `mechanisms.yaml` tooling, not content. Designer reviews.
   b. In `tools/sessions/card.py::_compact_globs`, name a shared **first** path segment once, so that
      `docs/agent-monitoring/**, docs/plans/agent_infrastructure/**, docs/guidelines/session_roles/**`
      becomes `docs/{agent-monitoring,plans/agent_infrastructure,guidelines/session_roles}/**`. The prototype
      changed `_DIR_GLOB` to `^(?P<parent>[^/*]+)/(?P<leaf>[^*]+?)/\*\*$`. With 3a it measured agent-working at
      391 / 395 / 394, and all 354 tests in `tests/tools/test_session_*.py` passed after regeneration.
      **Catch:** first-segment grouping made `rpg-designer` 1 token longer (393 to 394). The rpg owns has
      three `docs/plans/*` leaves, and the old grouping printed them more compactly. Implement it so that no
      card grows. For example, compute both groupings and keep the shorter string, or nest the shared
      sub-parent. Add a unit test for the multi-segment case and one for the "never longer" rule.
   c. Regenerate `.claude/agents/session-*.md` with `generate_agents.py`. The prototype changed the three
      agent-working files and the three rpg files.

## Out of Scope
- Changing any card's text other than the agent-working card in Scope 3a. That includes the rpg card, which
  belongs to `TCK-20261006-RPG-IMPLEMENTER-CONTACT-RULE-REPO-HOME`.
- Raising `CARD_BUDGET_TOKENS`. If a card is still over 400 after Scope 3, stop and report.
- An `ownership_splits` entry that gives each domain its own `domains/<d>.md` card. A card's content is
  still changed the usual way: send the owner of that domain the exact before and after text
  (`docs/guides/cross_session_messages.md`, "Out-of-boundary edits"). If M7 evidence shows that is not
  enough, a split is a follow-up.
- `routes`, `accepts_dispatch_from`, and any other domain's `owns`.

## Acceptance Criteria
1. The one-line diff to `registries/session_roles.yaml` matches Scope 1.
2. `route.py` returns agent-working as the owner of each of the seven template paths. Record the output.
3. The roster validator reports no new finding: no overlap with another domain's `owns` and no glob that
   matches nothing. Run `tests/tools/test_session_*.py` and confirm it passes.
4. After regeneration, `generate_agents.py --check` reports 0 drift findings.
5. The agent-working card text equals the Scope 3a literal.
6. Every role's composed card is at most 400 tokens, and no card is longer than it is on `40ab9857e` except
   because of an intended text change. Record a before and after table for all 12 roles. If the contact-rule
   ticket lands in the same batch, its rpg numbers count as the intended change.
7. New unit tests for `_compact_globs` cover multi-segment leaves under a shared first segment and the "never
   longer than the old grouping" rule.

## Related Tickets
- `TCK-20261006-RPG-IMPLEMENTER-CONTACT-RULE-REPO-HOME` (found there, under Assumptions / Open Questions)
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (closed by #353)

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md`
- `docs/guides/cross_session_messages.md`

## Related Stored Artifacts
None.

## Related Code Areas
`registries/session_roles.yaml`, `tools/sessions/route.py`, `tools/sessions/roster.py`,
`tools/sessions/card.py` (`TEMPLATE_DIR`), `tools/sessions/generate_agents.py`.

## Assumptions / Open Questions
- `registries/session_roles.yaml` is a governing file. The owner's batch answer above approved this exact
  one-line change, and the owner's budget answer approved the Scope 3a card text. Any wider change goes back
  to the owner.
- Ordering with the contact-rule ticket: both change card budgets. Land this one second, and measure the
  rpg cards with both changes applied. The contact-rule draft estimated rpg-designer at 398. With
  first-segment grouping it would be 399, so the "never longer" rule in 3b matters.
- `manifest_diff.py` reports the change as an `owns` delta. This is expected, so record it; it is not a
  finding.

## Implementation Notes
Drafted by agent-working-design (interim planner), 2026-10-06, and dispatched in the same batch as
`TCK-20261006-RPG-IMPLEMENTER-CONTACT-RULE-REPO-HOME`.

## Test Summary
- `route.py`: all seven template paths return `status: owned`, `domain: agent-working`.
- `tests/tools/test_session_*.py`: 359 passed (354 plus 5 new `_compact_globs` cases). `generate_agents.py --check`: 0 drift.
- Card tokens, before (40ab9857e, plus intended rpg change from the contact-rule ticket) -> after:

| role | before | after |
|---|---|---|
| rpg-designer / planner / implementer | 393 / 382 / 377 (398 / 386 / 382 with the contact-rule text) | 398 / 386 / 382 |
| agent-working-designer / planner / implementer | 396 / 400 / 399 | 391 / 395 / 394 |
| testing-* (3) | 377 / 356 / 351 | unchanged |
| codebase-* (3) | 377 / 366 / 363 | unchanged |

All 12 are at most 400. The rpg cards did not grow from the grouping change: `_compact_globs` keeps the shorter of the full-parent and first-segment groupings, the full-parent one on a tie.

## Files Changed
- `registries/session_roles.yaml` (one line)
- `tools/sessions/card.py`, `tests/tools/test_session_cards.py`
- `docs/guidelines/session_roles/domains/agent-working.md`
- `.claude/agents/session-agent-working-*.md` (regenerated)
- this ticket

## Completion Summary
Glob added, card trimmed to the Scope 3a literal, `_compact_globs` picks the shorter grouping. ACs 1-7 met. `manifest_diff.py` is expected to show the `owns` delta for agent-working.
