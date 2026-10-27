---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE
phase: done
date: 2026-10-22
tags: [ai, governance]
---

# TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE

## Title
`tools/rpg_measure/**` (the paired-run measurement tool) gets an owner: rpg

## Status
DONE

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
Unblocked 2026-10-27: #754 merged on origin/main as 3cf79fa05 (card fold, CARD_BUDGET_TOKENS 460 -> 456). Merged origin/main (no rebase), re-applied only the owns line, regenerated, re-measured every card (agent-working-planner-u24 re-dispatch, owner go #715).

Earlier: BLOCKED (waiting on ubuntu's card-fold batch to land on main; owner decision relayed by agent-working-planner-u24, 2026-10-26).
When it lands: merge origin/main, re-apply the owns line, regenerate with `python3 -m tools.sessions.generate_agents`, re-measure. Do not push before then.

First attempt (2026-10-26, reverted, nothing committed):
- Added `- tools/rpg_measure/**  # the paired-run measurement tool the v1 runs depend on` after `docs/guides/feature_flags.md` in `domains.rpg.owns`.
- Routing is right: `route tools/rpg_measure/paired.py` names rpg (seat rpg-planner, longest owns glob). A whole-tree route diff over 18,414 tracked paths changes only the 4 `tools/rpg_measure/*` files, from unowned to rpg.
- Worst rpg card (`rpg-implementer-ubuntu`) went 459 -> 466 tokens; `CARD_BUDGET_TOKENS` is 460. Budget not raised (owner's call).
- 6 tests failed with the edit: `test_session_cards.py::test_composed_card_is_within_the_token_budget[rpg-implementer]` and `[rpg-implementer-ubuntu]`, `test_session_cards.py::test_search_mcp_files_route_to_agent_working_and_every_card_stays_in_budget`, `test_session_host_lead.py::test_the_u24_card_carries_its_note_and_every_card_stays_in_budget`, `test_session_rpg_ubuntu_twins.py::test_every_rpg_card_exists_names_its_host_and_fits_the_budget[rpg-implementer]` and `[rpg-implementer-ubuntu]`.

## Test Summary
- AC1 met: `python -m tools.sessions.route tools/rpg_measure/paired.py` names rpg (seat rpg-planner, longest owns glob `tools/rpg_measure/**`). A route diff over all 18,461 tracked paths changes only the 4 `tools/rpg_measure/*` files, all from unowned to rpg.
- AC2 met against 456, not 460: `CARD_BUDGET_TOKENS` on main changed from 460 to 456 under #754. Worst card is 446 (agent-working-planner-u24, unchanged); worst rpg card is rpg-implementer-ubuntu, 438 -> 445. Every card (estimate_tokens(compose_card(...))):

| card | before | after | delta |
|---|---|---|---|
| agent-working-planner-u24 | 446 | 446 | +0 |
| agent-working-implementer | 446 | 446 | +0 |
| rpg-implementer-ubuntu | 438 | 445 | +7 |
| agent-working-implementer-u24 | 443 | 443 | +0 |
| agent-working-designer | 441 | 441 | +0 |
| rpg-implementer | 434 | 440 | +6 |
| agent-working-planner | 440 | 440 | +0 |
| agent-working-designer-u24 | 438 | 438 | +0 |
| rpg-planner-ubuntu | 431 | 437 | +6 |
| rpg-planner | 428 | 435 | +7 |
| rpg-designer-ubuntu | 428 | 434 | +6 |
| rpg-designer | 428 | 434 | +6 |
| lead-planner | 428 | 428 | +0 |
| lead-planner-u24 | 427 | 427 | +0 |
| testing-designer | 404 | 404 | +0 |
| codebase-designer | 400 | 400 | +0 |
| testing-planner | 395 | 395 | +0 |
| asset-planner | 395 | 395 | +0 |
| platform-planner-u24 | 394 | 394 | +0 |
| perf-planner | 391 | 391 | +0 |
| platform-implementer-u24 | 390 | 390 | +0 |
| codebase-planner | 390 | 390 | +0 |
| platform-planner | 389 | 389 | +0 |
| asset-implementer | 387 | 387 | +0 |
| testing-implementer | 384 | 384 | +0 |
| perf-implementer | 384 | 384 | +0 |
| architecture-planner-u24 | 384 | 384 | +0 |
| platform-implementer | 383 | 383 | +0 |
| architecture-implementer-u24 | 382 | 382 | +0 |
| architecture-planner | 380 | 380 | +0 |
| codebase-implementer | 379 | 379 | +0 |
| architecture-implementer | 376 | 376 | +0 |

- AC3 met: `pytest tests/tools -k "session or route or roster or card" -p no:randomly`, serial: 873 passed, 1 skipped.
- **Scope check 3 NOT met.** The new owns entry does not win over other domains' `tools/**` routes. `route tools/rpg_measure/paired.py --from <domain>`:
  - codebase, testing, lead, platform, architecture -> agent-working-designer ("<domain> routes this path to agent-working-designer")
  - rpg, agent-working, asset, perf -> rpg (longest owns glob)
  Cause: in `tools/sessions/route.py::route()`, an asking domain that does not claim the path applies its own `routes` before any other domain's owns. This predates the ticket and hits every non-agent-working tools owner: from codebase, `tools/perf/**`, `tools/loadtest/**` and `tools/visual_assets_*.py` also go to agent-working-designer. Only `tools/test_architecture/**` and `tools/release/**` escape, through explicit testing-planner routes. Follow-up: TCK-20261027-SESSION-ROUTE-OTHERS-OWNS-BEAT-CATCHALL-ROUTE (agent-working-planner-u24). Not fixed here: a per-domain route would patch one path and grow 5 cards; a route.py precedence change is a behavior change needing its own ticket and the owner's go.

## Files Changed
- `registries/session_roles.yaml` (one owns line in `domains.rpg.owns`)
- `.claude/agents/session-rpg-{designer,planner,implementer}{,-ubuntu}.md` (regenerated)

## Completion Summary
rpg owns `tools/rpg_measure/**`; the four files route to rpg instead of unowned. All 32 cards fit the current 456 budget (worst 446, worst rpg 445). Scope check 3 NOT met: from codebase/testing/lead/platform/architecture the path still routes to agent-working-designer, because an asking domain's own routes apply before others' owns (pre-existing, also affects tools/perf/**, tools/loadtest/**, tools/visual_assets_*.py); follow-up TCK-20261027-SESSION-ROUTE-OTHERS-OWNS-BEAT-CATCHALL-ROUTE. AC4/AC5 sit with the PR: the owner confirms the diff and decides when rpg's v1 record has landed; rpg-planner confirms on the PR.
