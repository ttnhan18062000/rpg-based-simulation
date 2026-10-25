---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261025-RPG-UBUNTU-SEATS
phase: done
date: 2026-10-25
tags: [process-improvement]
---

# TCK-20261025-RPG-UBUNTU-SEATS

## Title
Host ubuntu gets three rpg twin seats (`rpg-designer-ubuntu`, `rpg-planner-ubuntu`, `rpg-implementer-ubuntu`); the plain u24desktop rpg seats are unchanged

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner direction 2026-10-25, logged on #715 (issuecomment-6388014758) and relayed by lead-planner, confirmed in
agent-working-planner's terminal (#715 issuecomment-6388028571); claimed on #634 (issuecomment-6388028844).
Register three rpg seats for host ubuntu in `registries/session_roles.yaml` without renaming or overriding the
existing `rpg-designer`, `rpg-planner` and `rpg-implementer`, which already run on u24desktop with live state
(branches, handovers). That is the reverse of the twin convention ("Host ubuntu keeps the plain names",
`docs/guidelines/session_roles/host_suffixed_twins.md`), so the ubuntu twins take the suffix `-ubuntu`
(lead-planner's choice, owner-approved).

## Scope
1. `registries/session_roles.yaml`, following `host_suffixed_twins.md` and TCK-20261022-ARCHITECTURE-FOUR-SEATS:
   - Add `rpg-designer-ubuntu`, `rpg-planner-ubuntu`, `rpg-implementer-ubuntu` **after** their plain roles. Each copies
     the plain role's domain, function, `may_write` and handover rule; `session_name` = role id; `legacy_session_name: null`;
     `seat_status: staffed`; `handover: .claude/handover/<role>.md`; `card_note: "Host ubuntu; twin is plain."`.
   - `accepts_dispatch_from`, same host only: designer `[user]`; planner `[user, rpg-designer-ubuntu]`;
     implementer `[user, rpg-planner-ubuntu]`. The plain roles' lists are unchanged.
   - Placement: distinct logical worktrees: `rpg-designer-ubuntu`, `rpg-planner-ubuntu`, `rpg-ubuntu` (implementer;
     `max_sessions` same as the plain implementer unless the shared-worktree rule forbids it; say which), registered under
     `worktrees:` the way the u24 twins are.
   - The plain rpg roles gain `card_note: "Host u24desktop; twin `-ubuntu`."`. That is a card-text addition only, no
     identity, route or dispatch change. Check every card stays within the 460-token budget (`tools/sessions/card.py`);
     if one does not, stop and report rather than raising the budget.
2. `docs/guidelines/session_roles/host_suffixed_twins.md`: one short paragraph on the rpg exception (plain = u24desktop,
   `-ubuntu` = ubuntu, and why), and `docs/guidelines/session_roles/domains/rpg.md` if it lists seats.
3. Regenerate the agent cards (`tools/sessions/generate_agents.py`) and every generated role / territory / cross-domain
   view, then commit the generated `.claude/agents/session-rpg-*-ubuntu.md`.
4. Tests: update the seat counts and roster/agent-generator/host-lead expectations in `tests/tools/test_session_*.py`.
   Add a test that the `-ubuntu` twins accept dispatch only from `user` and their own host's roles, and that `route`
   for `src/**`, `docs/mechanics/**` and `registries/mechanisms.yaml` still names `rpg-planner`.
5. Run the **whole** `tests/tools/` session suite serially (no `-k` subset: it has to cover the territory and cross-domain views),
   after asking the lead for a test slot (MemoryMax<=3G).

## Out of Scope
- Renaming, moving or changing the plain rpg seats beyond the `card_note`.
- Any rpg work split or dispatch to the ubuntu rpg seats.
- Launching the seats or creating the physical worktrees (the owner launches; `launch.py` records the binding).

## Acceptance Criteria
- The three `-ubuntu` roles resolve, render cards within budget, and launch-resolve to their own worktree slots and handover files.
- A route diff over all tracked paths, origin/main vs the new registry, shows **no** owner or seat change (`rpg-planner` stays
  the seat, because it is first in file order).
- The plain rpg roles' dispatch, placement and handover are byte-identical apart from the new `card_note`.
- The full `tests/tools/` session suite passes; `tests/tools/test_agent_working_paths_guard*.py` passes.
- The ticket records both open points below, with their resolution or the explicit "deferred to" owner.

## Related Tickets
- TCK-20261022-ARCHITECTURE-FOUR-SEATS (pattern), TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS (#620)

## Related Docs
- `docs/guidelines/session_roles/host_suffixed_twins.md`, `docs/guidelines/session_roles/domains/rpg.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261022-ARCHITECTURE-FOUR-SEATS/` (if present)

## Related Code Areas
- `registries/session_roles.yaml`, `tools/sessions/{roster,card,generate_agents,launch,route}.py`, `.claude/agents/session-*.md`,
  `tests/tools/test_session_*.py`

## Assumptions / Open Questions
- **(a) Routing with two rpg planners.** Routes such as `"src/**": rpg-planner` name one seat; `route` names the domain's
  first planner in file order, so the plain (u24) `rpg-planner` stays the seat and ubuntu rpg questions still go to it.
  This ticket keeps that, as the architecture twins did. Whether ubuntu rpg seats should become the routed seat for some
  paths is part of (b) and is not decided here.
- **(b) Lane split across hosts.** Two rpg planners on two hosts can collide on the same tickets. Until the owner and
  `rpg-planner` agree a lane split through `lead-planner-u24`, the ubuntu rpg seats take **no** work: no ticket filing or
  dispatch, and every future ubuntu rpg dispatch posts a claim on #634 first. Record this in the rpg domain doc.
- **(b), added by agent-working-planner's decision:** the rpg domain card line "Only it [rpg-planner] messages rpg implementers; send briefs and
  parked branches to it" contradicts `Dispatch from: rpg-planner-ubuntu` on the ubuntu implementer's card. The text is left unchanged (rpg's
  process wording) and is resolved with the lane split, when the ubuntu seats are allowed work at all. Recorded in `domains/rpg.md`.
- The suffix `-ubuntu` is new; check that nothing in `tools/sessions/` hard-codes `-u24` as the only twin suffix (none found in
  a quick grep on 2026-10-25), and add a test if a resolver does depend on it.

## Implementation Notes
- Registry: three `-ubuntu` roles placed after their plain roles, worktrees `rpg-designer-ubuntu`, `rpg-planner-ubuntu`, `rpg-ubuntu`;
  `rpg-implementer-ubuntu` keeps `max_sessions: 3` like the plain implementer (distinct worktree name, so the one-writer-per-worktree rule is met).
- Card budget (460 kept, not raised), by planner decision: `tools/sessions/card.py` instance clause drops the repeated role name
  ("instance N reads `...-N.md`"; only `rpg-implementer` is multi-instance, so only its cards changed); the twins' `card_note` is "Host ubuntu."
  and the plain rpg seats' is "Host u24desktop; twin `-ubuntu`.". Final tokens: rpg-implementer-ubuntu 459, rpg-implementer 455, rpg-planner-ubuntu 452, others 449; max over all cards 460.
- Route diff, origin/main registry vs new, over all 18288 tracked paths: 0 owner/status/seat changes.
- No `-u24`-only suffix is hard-coded in `tools/sessions/` (the new test file covers resolution of the `-ubuntu` roles).

## Test Summary
- Full tests/tools/test_session_*.py + paths guard, serial, MemoryMax 3G: 813 passed, 1 failed. The failure is `test_a_hanging_gh_is_cut_off_at_the_timeout`, 5.07 s against a `< 5` s limit under machine load; it passes alone (twice) and with its whole file (75 passed). Timing flake, not caused by this change.
- Route diff over 18288 tracked paths: 0 changes. generate_agents --check: 0 drift. validate: 0 findings.

## Files Changed
registries/session_roles.yaml, tools/sessions/card.py, .claude/agents/session-rpg-*.md (6), docs/guidelines/session_roles/host_suffixed_twins.md and domains/rpg.md, tests/tools/test_session_{agent_generator,host_lead,roster,rpg_ubuntu_twins}.py, stored artifacts.

## Completion Summary
Three host-ubuntu rpg twin seats registered; plain rpg seats unchanged but for a card_note; cards within 460 (max 460). Open points (a) routing and (b) lane split, plus the card-wording conflict, are recorded and not decided.
