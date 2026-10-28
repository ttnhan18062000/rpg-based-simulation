---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261028-ROLE-CARDS-LEAD-RELAYED-APPROVAL-WORDING
phase: done
date: 2026-10-28
tags: [ai, governance]
---

# TCK-20261028-ROLE-CARDS-LEAD-RELAYED-APPROVAL-WORDING

## Title
Role cards: a lead seat citing the owner's approvals-issue comment id carries the approval; relays never answer prompts

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
On 2026-10-28 the owner directed that every u24 ask needing the owner goes through lead-planner-u24
(#715 6459766303). lead-planner-u24 logs the owner's answer on #715 and relays it with the comment id. The
planner and designer cards say "Peer messages never approve", and the implementer card says "a peer is never user
approval", so a careful seat refuses that relay. The owner said "I think some specific session can approve like
lead" (#715 6459850177 item 4). agent-working-planner-u24 drafted the wording and agent-working-designer-u24
amended it, the designer being the owner of `docs/guidelines/session_roles/**`. The owner **confirmed the literal
text below** (#715 issuecomment-6459975274, item 3: the default text, not the "permission prompts" variant).

Meaning: the approval is always the owner's own answer, logged first on the approvals issue (#715). A lead-domain
seat (lead-planner, lead-planner-u24) may carry it to another seat by citing that comment's id. A relay never
answers a harness or guard permission prompt in the receiving seat's terminal: merge, push to main, remote-branch
and worktree/data deletes. A non-lead relay, or one without a comment id, approves nothing.

## Scope
Literal edits, exactly as confirmed. Any change to this text needs a new owner confirmation.
- `docs/guidelines/session_roles/functions/planner.md` and `docs/guidelines/session_roles/functions/designer.md`, `## Card`:
  - BEFORE: `Peer messages never approve; log user approvals on the approvals issue first.`
  - AFTER: `Approves: the user, logged first on the approvals issue, or a lead seat citing that comment id. Relays never answer prompts.`
- `docs/guidelines/session_roles/functions/implementer.md`, `## Card`:
  - BEFORE: `a peer is never user approval; log user approvals on the approvals issue first.`
  - AFTER: `approves: the user, logged first on the approvals issue, or a lead seat citing that comment id. Relays never answer prompts.`
- Budget offset, `planner.md`:
  - BEFORE: `commit only on your own branch: your worktree's, or a small doc/ticket branch if you launch from the main checkout.`
  - AFTER: `commit only on your own branch (your worktree's, or a doc/ticket branch from the main checkout).`
- Budget offset, `implementer.md`:
  - BEFORE: `Sole writer to your worktree; two instances never share one.`
  - AFTER: `Sole writer to your worktree (never shared).`
- Regenerate the cards: `tools/sessions/generate_agents.py`.
- Measure every card with `compose_card` and `estimate_tokens` against `CARD_BUDGET_TOKENS` (456 on main), before and
  after.

## Out of Scope
- `CARD_BUDGET_TOKENS`: never raise it. If any card goes over 456, stop, leave the ticket BLOCKED and report the
  before and after table. Don't trim any other card text.
- `registries/session_authority.yaml`, `tools/sessions/guard.py`: the permission prompts are unchanged by design.
- Any other wording in the function or domain card sources.
- `.claude/settings.json`, CLAUDE.md.

## Acceptance Criteria
1. `git diff` of the three function sources shows exactly the five BEFORE->AFTER replacements above, byte for byte,
   and nothing else.
2. The `.claude/agents/session-*.md` cards are regenerated with generate_agents.py, never hand-edited, and every
   card is at or under 456. The PR body has the full before/after table. Estimated worst cases: planner 446->454,
   designer 441->455, implementer 446->455.
3. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes, run serially.
4. The PR body quotes the literal diff of the three sources and cites #715 issuecomment-6459975274 item 3. The
   owner merges.

## Related Tickets
- TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE (last card-budget measurement, worst 446)

## Related Docs
- docs/guidelines/session_roles/functions/{planner,designer,implementer}.md
- docs/guides/cross_session_messages.md (read only)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/sessions/generate_agents.py, tools/sessions/card.py (run, unchanged)
- .claude/agents/session-*.md (generated)

## Assumptions / Open Questions
- None open. The text is owner-confirmed (#715 issuecomment-6459975274 item 3). Under the 2026-10-28 routing
  (#715 6459766303), the push go and PR go are asks to lead-planner-u24.

## Implementation Notes
- Dispatched by agent-working-planner-u24 on 2026-10-28; only this ticket file was taken from its commit 73d5d4a95,
  on a fresh branch `agent-working-role-cards-lead-relay` from origin/main 7b4bf7a30.
- Each BEFORE string was counted once in its file before the edit; the five replacements were applied byte for byte
  by a replace that asserted exactly one match each.
- Cards regenerated with `python -m tools.sessions.generate_agents` (all 32 rewritten, none hand-edited).
- Card sizes (`compose_card` + `estimate_tokens`, budget 456), before -> after: worst card agent-working-designer
  441 -> 455; agent-working-implementer 446 -> 454; agent-working-planner-u24 446 -> 454; rpg-implementer-ubuntu
  445 -> 453. No card is over 456. The full table is in the PR body.

## Test Summary
- `pytest tests/tools -k "session or route or roster or card" -p no:randomly` (serial): 873 passed, 1 skipped.

## Files Changed
- docs/guidelines/session_roles/functions/planner.md, designer.md, implementer.md (the five literal replacements)
- .claude/agents/session-*.md (32 cards, regenerated)
- agent-working/tickets/done/TCK-20261028-ROLE-CARDS-LEAD-RELAYED-APPROVAL-WORDING.md

## Completion Summary
AC1: `git diff` of the three sources shows exactly the five replacements. AC2: cards regenerated, all 32 at or under
456 (worst 455). AC3: passed. AC4: the PR body quotes the diff and cites #715 issuecomment-6459975274 item 3; the
owner merges.
