---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261022-APPROVALS-NOTIFY-BOTH-LEADS-BEFORE-ACTING
phase: done
date: 2026-10-22
tags: [ai, governance, process-improvement]
---

# TCK-20261022-APPROVALS-NOTIFY-BOTH-LEADS-BEFORE-ACTING

## Title
Before acting on a user approval, a session records it on one approvals-log issue and tells its own host's lead; both leads acknowledge there, and an acknowledgment is not an approval

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The user's decision of 2026-10-22, made in lead-planner-u24's terminal and relayed by lead-planner-u24 as a finding, was
confirmed by the user in agent-working-planner-u24's terminal on 2026-10-22 ("File and dispatch"):

> Before acting on any user approval (merge, push, scope change, freeze exception, STOP acceptance), a session first
> messages both leads (lead-planner-u24 and lead-planner on the other machine) with what was approved, when, and where
> it's recorded. The leads acknowledge. An acknowledgment is not an approval.

A u24 session cannot message ubuntu's `lead-planner`, and an ubuntu session cannot message `lead-planner-u24`:
`ListAgents` lists only same-host sessions, and `docs/guides/cross_session_messages.md` sends cross-host traffic through
GitHub issues. The user chose the channel on 2026-10-22 in agent-working-planner-u24's terminal: **one standing tracking
issue**. The session comments there, then messages its own host's lead with the comment link. Both leads acknowledge on
the issue.

## Scope
1. **The log issue.** Open one GitHub issue titled "Approvals log (both leads acknowledge; an ack is not an approval)",
   with the format below in its body, and pin it if `gh` allows. Record its number in the guide. Check first that no such
   issue already exists.
2. **The comment format,** one comment per approval:
   ```
   approval: <merge #N | push <branch> | scope change <ticket> | freeze exception <what> | STOP accepted <what>>
   by: user, in <session name>'s terminal, at <YYYY-MM-DD HH:MM host-local>
   recorded: <where: PR/issue comment link, ticket section, handover line>
   acting session: <session name> (host <host>)
   ```
3. **`docs/guides/cross_session_messages.md`:** a new short section, "Acting on a user approval". It covers:
   - the rule;
   - which approvals it covers;
   - the order: comment on the log issue, then message your own host's lead with the link, then act;
   - that the session does not wait for the acknowledgment, and an acknowledgment approves nothing;
   - that a peer still never relays an approval: the approval has to have been given in the acting session's own
     terminal or on the PR by the user;
   - that leads acknowledge on the issue with a comment or a 👍 reaction.
   Add a row to the Classes table, or a line under it, if that reads better.
4. **The cards:** one short clause in the Card section of each of `docs/guidelines/session_roles/functions/{planner,implementer,designer}.md`.
   Example: "Before acting on a user approval, log it on the approvals issue and tell your host's lead (an ack is not an
   approval)." Regenerate with `tools/sessions/generate_agents.py`.
5. **Ownership:** `docs/guides/cross_session_messages.md` routes as **unowned** today (`tools.sessions.route`). Add it to
   `domains.agent-working.owns` in `registries/session_roles.yaml`, since it is the guide behind the role cards, which
   agent-working owns. If the card line gets long, fold it into an existing brace group.

## Out of Scope
- Enforcing the rule in a hook or `guard.py`. The rule is advisory, like the rest of the message conventions.
- `.claude/settings.json` and CLAUDE.md.
- Changing who may approve. The user still approves; leads only acknowledge.
- Shrinking the cards in general. That is ubuntu's TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT
  (filed, not dispatched). If it is in flight when this starts, check #634 and rebase onto it.

## Acceptance Criteria
1. The issue exists, carries the format, and its number is in the guide. Record the link in Implementation Notes.
2. The guide section states the rule, the five covered approval kinds, the order (log, tell own lead, act), "no wait"
   and "an ack is not an approval".
3. All three function cards carry the clause, and the generated `.claude/agents/session-*.md` are regenerated with no
   other drift.
4. The card-budget test passes at the current `CARD_BUDGET_TOKENS` (440 on main). If it can't, the PR body shows the
   worst card's size before and after, and names the number for the owner to confirm. Don't raise it silently.
5. `python -m tools.sessions.route docs/guides/cross_session_messages.md` names agent-working. A before/after route diff
   over all tracked paths shows that only this path changes owner.
6. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes.
7. The PR body carries the literal `session_roles.yaml` diff and the literal card-clause text for the owner to confirm.
8. Dogfood it: the first log comment on the new issue records this PR's own merge approval when it comes.

## Related Tickets
- TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT (ubuntu, filed): the same card files.
- TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (#701), TCK-20261021-SESSION-ROLES-OWN-OBSERVABILITY-DOCS-AND-UNOWNED-ROOTS (#711): earlier owns changes.

## Related Docs
- `docs/guides/cross_session_messages.md`
- `docs/plans/agent_infrastructure/session_layer_working_process.md` sections 9.0 to 9.3
- `docs/guidelines/session_roles/functions/`

## Related Stored Artifacts
None.

## Related Code Areas
- `registries/session_roles.yaml`, `tools/sessions/generate_agents.py`, `tools/sessions/card.py` (budget; read only unless AC 4)
- `.claude/agents/session-*.md` (generated)

## Assumptions / Open Questions
- Assumed: the session does not wait for the leads' acknowledgment before acting. The decision says the leads
  acknowledge, not that the session waits. The owner confirms this on the PR.
- Assumed: the two lead seats acknowledge themselves when they next read the issue. The SessionStart issue list shows
  `for:<role>` issues, so label the log issue `for:lead-planner` and `for:lead-planner-u24` and both leads see it at start.

## Implementation Notes
- Log issue: https://github.com/ttnhan18062000/rpg-based-simulation/issues/715 (opened by agent-working-planner-u24 at the user's request; my own create call was denied by the classifier). Labels for:lead-planner and for:lead-planner-u24.
- Cards carry the short clause "log user approvals on the approvals issue first" folded into the existing never-approve sentence; the full rule is in the guide section only. The cards do not name the issue number or the guide; a session finds it by title (`gh issue list --search "Approvals log in:title"`).
- Budget: owner decision "raise to 460, 2026-10-22" (via agent-working-planner-u24); worst card 437 on main (rpg-implementer), 460 now (agent-working-implementer, agent-working-planner-u24). Hard-coded 440 in test_session_platform_domain.py and host_suffixed_twins.md updated.
- Route diff over 18,140 tracked paths: only docs/guides/cross_session_messages.md changes owner (unowned to agent-working).

## Test Summary
Scoped `pytest tests/tools -k "session or route or roster or card"`: 822 passed; the two budget-constant failures were fixed, test_session_platform_domain.py and test_session_cards.py pass (73).

## Files Changed
docs/guides/cross_session_messages.md, docs/guidelines/session_roles/functions/{planner,implementer,designer}.md, docs/guidelines/session_roles/host_suffixed_twins.md, registries/session_roles.yaml, tools/sessions/card.py, tests/tools/test_session_platform_domain.py, .claude/agents/session-*.md (generated).

## Completion Summary
User approvals are logged on #715 before acting; the three function cards carry the clause; the guide is owned by agent-working; card budget 460.
