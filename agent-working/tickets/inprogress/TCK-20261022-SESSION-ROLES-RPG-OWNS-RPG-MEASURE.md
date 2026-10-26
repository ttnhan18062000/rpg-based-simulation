---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE
phase: open
date: 2026-10-22
tags: [ai, governance]
---

# TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE

## Title
`tools/rpg_measure/**` (the paired-run measurement tool) gets an owner: rpg

## Status
BLOCKED

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
This is a finding from lead-planner-u24 (2026-10-22), verified by agent-working-planner-u24 on origin/main.
`python3 -m tools.sessions.route tools/rpg_measure/paired.py` reports **unowned**. The directory holds `__init__.py`,
`arm_child.py`, `paired.py` and `stats.py`: rpg's measurement tool, which the v1 paired runs depend on. rpg-planner
confirmed via lead-planner-u24 (2026-10-22) that it claims `tools/rpg_measure/**`. The roles registry is agent-working's.

**Timing:** do not merge during rpg's v1 record window (lead-planner-u24, rpg-planner). Dispatch waits for the user.

## Scope
- `registries/session_roles.yaml`: add `tools/rpg_measure/**` to `domains.rpg.owns`, with a short comment.
- Regenerate the cards (`tools/sessions/generate_agents.py`). The rpg cards grow by about 7 tokens. The worst rpg
  card must stay at or under `CARD_BUDGET_TOKENS` (460). If it doesn't, stop and report the before and after sizes;
  don't raise the budget.
- Check that the `tools/**` route to agent-working-designer in other domains' `routes` doesn't win over the new owns
  entry for this path. owns should win; confirm with route.

## Out of Scope
- Any change to `tools/rpg_measure/` itself.
- Any other ownership change.
- `.claude/settings.json` and CLAUDE.md.

## Acceptance Criteria
1. `python -m tools.sessions.route tools/rpg_measure/paired.py` names rpg. A route diff over all tracked paths shows
   only the four `tools/rpg_measure/*` files changing owner, from unowned.
2. The cards are regenerated, and the worst card is reported before and after, within 460.
3. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes, run serially.
4. The PR body carries the literal `session_roles.yaml` diff for the owner to confirm. rpg-planner confirms on the PR.
5. The PR is not merged until rpg's v1 record has landed.

## Related Tickets
- TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (#701), TCK-20261021-SESSION-ROLES-OWN-OBSERVABILITY-DOCS-AND-UNOWNED-ROOTS (#711).

## Related Docs
- `docs/guidelines/session_roles/`

## Related Stored Artifacts
None.

## Related Code Areas
- `registries/session_roles.yaml`, `tools/sessions/{route,card,generate_agents}.py`, `.claude/agents/session-rpg-*.md`

## Assumptions / Open Questions
- None.

## Implementation Notes
BLOCKED (waiting on ubuntu's card-fold batch to land on main; owner decision relayed by agent-working-planner-u24, 2026-10-26).
When it lands: merge origin/main, re-apply the owns line, regenerate with `python3 -m tools.sessions.generate_agents`, re-measure. Do not push before then.

First attempt (2026-10-26, reverted, nothing committed):
- Added `- tools/rpg_measure/**  # the paired-run measurement tool the v1 runs depend on` after `docs/guides/feature_flags.md` in `domains.rpg.owns`.
- Routing is right: `route tools/rpg_measure/paired.py` names rpg (seat rpg-planner, longest owns glob). A whole-tree route diff over 18,414 tracked paths changes only the 4 `tools/rpg_measure/*` files, from unowned to rpg.
- Worst rpg card (`rpg-implementer-ubuntu`) went 459 -> 466 tokens; `CARD_BUDGET_TOKENS` is 460. Budget not raised (owner's call).
- 6 tests failed with the edit: `test_session_cards.py::test_composed_card_is_within_the_token_budget[rpg-implementer]` and `[rpg-implementer-ubuntu]`, `test_session_cards.py::test_search_mcp_files_route_to_agent_working_and_every_card_stays_in_budget`, `test_session_host_lead.py::test_the_u24_card_carries_its_note_and_every_card_stays_in_budget`, `test_session_rpg_ubuntu_twins.py::test_every_rpg_card_exists_names_its_host_and_fits_the_budget[rpg-implementer]` and `[rpg-implementer-ubuntu]`.

## Test Summary

## Files Changed

## Completion Summary
