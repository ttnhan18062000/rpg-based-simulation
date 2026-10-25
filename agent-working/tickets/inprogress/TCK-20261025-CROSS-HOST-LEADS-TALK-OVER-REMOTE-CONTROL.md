---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261025-CROSS-HOST-LEADS-TALK-OVER-REMOTE-CONTROL
phase: open
date: 2026-10-25
tags: [ai, process-improvement, governance]
---

# TCK-20261025-CROSS-HOST-LEADS-TALK-OVER-REMOTE-CONTROL

## Title
The two leads message each other across hosts over Remote Control, and every other seat reaches the other host only through its own lead

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner direction 2026-10-25, logged on #715 (issuecomment-6396617829), relayed by lead-planner (host ubuntu) as a
finding to agent-working-planner. Both leads now run `/remote-control`. `lead-planner` and `lead-planner-u24` can
SendMessage each other in both directions (trial done 2026-10-25). The docs still say a session on another host
cannot receive a message (`docs/guides/cross_session_messages.md`, "Acting on a user approval" and "Cross-host
handoffs"), which is now false for the two leads.

The convention to document:
1. Live cross-host coordination goes lead to lead only, over Remote Control SendMessage.
2. Each lead delegates to its own host's seats. A session never messages the other host's domain sessions
   directly, even when `ListAgents` shows them as Remote Control rows.
3. #715 still records owner approvals before anyone acts, and a peer message never approves (unchanged).
4. `for:<role>` GitHub issues stay the channel for durable handoffs, or when the target is offline (unchanged).
5. Remote Control gives no read receipt from another machine, and the docs don't say whether a message waiting
   for an offline session survives that session's `/clear` or restart. Anything that must not be lost also goes
   on GitHub.

## Scope
1. `docs/guides/cross_session_messages.md`:
   - Add a section `## Cross-host: lead to lead over Remote Control`, placed before the `for:<role>` section and
     holding points 1, 2 and 5 above. Date it (owner, 2026-10-25, #715 issuecomment-6396617829).
   - Rewrite the first sentence of `## Cross-host handoffs: for:<role> issues`. Issues now carry durable
     handoffs, anything that must not be lost, and messages to an offline target; they are no longer the only
     cross-host path. Keep the rest of that section.
   - "Acting on a user approval": replace "The other host's lead cannot be messaged (`ListAgents` is same-host
     only), which is why the record is an issue." with text that is true now: the record is an issue because it
     must be durable and both hosts must see it. A Remote Control message carries no read receipt and may not
     survive a `/clear`. Keep the order (comment, then own-host lead, then act) unchanged.
   - Define the convention once, here. Other files point to this section and don't repeat it.
2. Lead card: `docs/guidelines/session_roles/domains/lead.md` `## Card`. Add one short clause: cross-host
   coordination goes lead to lead over Remote Control, and the lead never messages the other host's domain
   seats.
3. Function cards: in the `## Card` text of `docs/guidelines/session_roles/functions/{planner,designer,implementer}.md`,
   add a short clause after the Messages sentence. Suggested wording: "Other host: only via your lead." The two
   lead cards get it too, through the planner function, and it holds for them as well: a lead reaches the other
   host only lead to lead.
4. `docs/plans/agent_infrastructure/session_layer_working_process.md`: add one dated "Decided by the owner
   (2026-10-25)" line next to the 2026-10-09/10 decision (around line 779), pointing to the new guide section.
   Don't restate the rules there.
5. Regenerate the cards (`python3 tools/sessions/generate_agents.py`, then `--check`). Card budget: every card
   must stay within `CARD_BUDGET_TOKENS = 460`. If any card goes over, **don't raise the budget and don't trim
   other card text**. Stop and report which cards are over and by how much. The planner then decides: shorter
   wording, or the clause on the lead card only.
6. Run the session-card and roster tests that pin card text and budget (`tests/tools/test_session_*.py`) and the
   docs tests that cover `docs/guides/` (if any). Get a lead slot first, MemoryMax at most 3G.

## Out of Scope
- Any hook, guard or lint that enforces the convention. It stays advisory, like the rest of
  `cross_session_messages.md`.
- `accepts_dispatch_from` and route changes in `registries/session_roles.yaml`. Dispatch is unchanged.
- The owner's /clear-advice rule (the lead tells the owner to clear a seat only after it completes a batch and
  is over 250k context). The owner asked for no doc change.
- Telling the u24 seats. lead-planner-u24 does that.
- `docs/guides/agent_session_reset_boundaries.md`.

## Acceptance Criteria
1. `cross_session_messages.md` has the new section with points 1, 2 and 5 and the owner date and #715 link. It no
   longer says a cross-host session cannot be messaged, in either section.
2. The `for:<role>` section still says issues are for durable handoffs and offline targets, and that an issue
   never approves.
3. The approvals section still requires the #715 comment before acting, and still says a peer message never approves.
4. The lead card and every function-derived card carry the clause. `generate_agents.py --check` is clean, and
   every card stays at or under 460 tokens.
5. The plan doc carries one dated decision line that points to the guide.
6. Scoped tests pass. `docs/REGISTRY.yaml` is regenerated after the last `docs/` edit, and `generate_registry --check` is clean.

## Related Tickets
- TCK-20261022-APPROVALS-NOTIFY-BOTH-LEADS-BEFORE-ACTING (approvals issue #715; wrote the "cannot be messaged" sentence)
- TCK-20261013-HOST-LEAD-PLANNER-U24 (second lead seat)
- TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS
- TCK-20261025-RPG-UBUNTU-SEATS (#737, merged bd296f58a: last card-budget change)

## Related Docs
- docs/guides/cross_session_messages.md
- docs/guidelines/session_roles/domains/lead.md
- docs/guidelines/session_roles/functions/{planner,designer,implementer}.md
- docs/plans/agent_infrastructure/session_layer_working_process.md
- docs/guidelines/session_roles/host_suffixed_twins.md (dispatch stays same-host; no change expected)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/sessions/generate_agents.py, tools/sessions/card.py (`CARD_BUDGET_TOKENS`)
- .claude/agents/session-*.md (generated)
- tests/tools/test_session_*.py

## Assumptions / Open Questions
- Assumed: the clause belongs in the function cards, so domain seats on both hosts see it. If the budget forbids
  that, the fallback is the lead card only, with the guide carrying the rule for everyone else (planner decides,
  see Scope 5).
- Unknown (stated in the guide, not resolved): whether a queued Remote Control message survives the target's
  `/clear` or restart.

## Implementation Notes
Hand-orchestrated hotfix. Record the closure with `record_hand_orchestrated_closure.py`.

## Test Summary

## Files Changed

## Completion Summary
