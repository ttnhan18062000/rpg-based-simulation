---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS
phase: done
date: 2026-10-19
tags: [ai, governance]
---

# TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS

## Title
Five paths that route as unowned get an owner in session_roles.yaml: testing takes rpg-gate-report.yml and the two ci_junit tools, and agent-working takes handover_transit.py and tools/search/**

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The report-only Semgrep scan (#665, security-scan.yml) reported baseline findings on paths that `tools.sessions.route`
reports as **unowned**, so nobody is responsible for triaging them:

- `.github/workflows/rpg-gate-report.yml`: 9 findings. testing asked for it earlier, and rpg-planner agrees it isn't theirs
  (relayed via platform-planner-u24). TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24 already names testing-planner for it.
- `tools/ci_junit_merge.py`, `tools/ci_junit_summary.py`: CI-lane tooling read by test.yml (testing's). testing wired
  ci_junit_merge.py in #659.
- `tools/handover_transit.py`: session/handover tooling, in the session-lead epic's scope.
- `tools/search/**` (Dockerfile etc.): the search server image. agent-working already owns `tools/search_*.py`.

lead-planner-u24 recommended this split (2026-10-19, advice). The roles registry is agent-working's file. The owner
confirms the literal diff in the PR body, and testing-planner confirms its entries on the PR.

## Scope
- `registries/session_roles.yaml`: add to `domains.testing.owns`: `.github/workflows/rpg-gate-report.yml`,
  `tools/ci_junit_*.py`. Add to `domains.agent-working.owns`: `tools/handover_transit.py`, `tools/search/**`.
- Regenerate the role cards (`tools/sessions/generate_agents.py`). Stay within the 400-token card budget, folding
  into existing brace globs on the card line if needed.
- Update any test that pins the owns lists or the card text.

## Out of Scope
- Fixing the Semgrep findings themselves. Each new owner triages its own (my triage notes went to lead-planner-u24
  and platform-planner-u24).
- Any other ownership change.
- `.claude/settings.json`, CLAUDE.md.

## Acceptance Criteria
1. `python -m tools.sessions.route <path>` names testing for rpg-gate-report.yml and both ci_junit tools, and names
   agent-working for tools/handover_transit.py and tools/search/Dockerfile. Record the output in Test Summary.
2. No path changes owner except these five. Run route on each path both domains already own, before and after, and
   check that the results are identical. Alternatively, rely on the existing roster/route tests if they cover this.
3. The cards are regenerated, and the card-budget test passes.
4. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes.
5. The PR body carries the literal session_roles.yaml diff for the owner to confirm. testing-planner's confirmation is
   requested on the PR.

## Related Tickets
- TCK-20261019-SEMGREP-BASELINE-AGENT-WORKING-PATHS (agent-working's own two findings)
- TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24 (names testing-planner for rpg-gate-report.yml)
- TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS (previous roles change)

## Related Docs
- `docs/guidelines/session_roles/`

## Related Stored Artifacts
None.

## Related Code Areas
- `registries/session_roles.yaml`
- `tools/sessions/route.py`, `tools/sessions/generate_agents.py`
- `.claude/agents/session-*.md` (generated)

## Assumptions / Open Questions
- Before the PR, check #634 that no ubuntu agent-working seat has a roles PR touching the same owns lists. If one
  does, rebase onto it.

## Implementation Notes
`registries/session_roles.yaml`: `domains.testing.owns` gains `.github/workflows/rpg-gate-report.yml` and `tools/ci_junit_*.py`; `domains.agent-working.owns` gains `tools/search/**` and `tools/handover_transit.py` (placed after `tools/*_search.py`, with the other plain `tools/*.py` globs). The regenerated agent-working cards no longer fit 400 tokens (worst 408), so, on the owner's decision relayed by agent-working-planner-u24 (2026-10-20), `CARD_BUDGET_TOKENS` goes 400 -> 415 in `tools/sessions/card.py`; `test_session_platform_domain.py` and two session_roles docs that quoted 400 were updated. Cards regenerated with `python3 -m tools.sessions.generate_agents`; only the agent-working and testing cards changed.

## Test Summary
Route (`python3 -m tools.sessions.route <path>`) after the change: `.github/workflows/rpg-gate-report.yml`, `tools/ci_junit_merge.py`, `tools/ci_junit_summary.py` -> `domain: testing seat: testing-planner`; `tools/handover_transit.py` -> `domain: agent-working seat: agent-working-planner`; `tools/search/Dockerfile` -> `domain: agent-working` (matched `tools/search/**`). All five were `unowned` before.
Before/after route diff over 976 tracked paths (tools, .github, tests/tools, registries, docs/guidelines, agent-working/agent*): exactly six paths change, the five above plus `tools/search/docker-compose.yml`; nothing else moves.
Worst card, measured with `compose_card` + `estimate_tokens`: origin/main 400 (agent-working-implementer, agent-working-planner-u24); now 408, within the new 415 budget.
`pytest tests/tools -k "session or route or roster or card" -p no:randomly`: 802 passed, 1 skipped.

## Files Changed
- `registries/session_roles.yaml`
- `tools/sessions/card.py` (budget 400 -> 415)
- `tests/tools/test_session_platform_domain.py`
- `docs/guidelines/session_roles/host_suffixed_twins.md`, `docs/guidelines/session_roles/functions/designer.md`
- regenerated `.claude/agents/session-agent-working-*.md`, `session-testing-*.md`

## Completion Summary
Five named paths now have an owner; `tools/search/docker-compose.yml` is a sixth path that changes owner (agent-working), caught by `tools/search/**` -- intended. The card budget rise (400 -> 415) is the owner's decision and is stated in the PR body for confirmation, as is the literal yaml diff; testing-planner confirms its two entries on the PR.
