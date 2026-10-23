---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261023-SESSION-ROLES-PLATFORM-OWNS-SECURITY-MD
phase: done
date: 2026-10-23
tags: [ai, governance]
---

# TCK-20261023-SESSION-ROLES-PLATFORM-OWNS-SECURITY-MD

## Title
`SECURITY.md` (repo root) gets an owner: platform

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
lead-planner-u24 (2026-10-23) reports that the user enabled private vulnerability reporting and Dependabot alerts, and
that `SECURITY.md` routes as **unowned** (`tools.sessions.route`). The file doesn't exist on main yet. The user decided
on 2026-10-23 in agent-working-planner-u24's terminal that **platform** owns it (logged on #715,
issuecomment-6357027725). Platform already owns `security-scan.yml` and `dependabot.yml`, and `platform-planner-u24`
runs on u24desktop.

## Scope
- `registries/session_roles.yaml`: add `SECURITY.md` to `domains.platform.owns`, with a short comment (owner 2026-10-23,
  #715).
- Regenerate the cards. Platform cards grow by about 4 tokens. Everything must fit 460, so report the worst card before
  and after, and don't raise the budget.

## Out of Scope
- Writing `SECURITY.md` itself. That's platform's job; the owner tells platform-planner-u24.
- Any other ownership change.

## Acceptance Criteria
1. `python -m tools.sessions.route SECURITY.md` names platform. A route diff over all tracked paths shows no other owner
   change (`SECURITY.md` isn't tracked yet, so the route call itself is the check).
2. The cards are regenerated (`generate_agents --check` is clean), and all cards fit 460.
3. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes, run serially.
4. The PR body carries the literal YAML diff. platform-planner-u24 confirms on the PR.

## Related Tickets
- TCK-20261023-SEMGREP-SEARCH-DOCKERFILE-USER-AND-TRANSIT-SHA1 (same batch).

## Related Docs
- `docs/guidelines/session_roles/`

## Related Stored Artifacts
None.

## Related Code Areas
- `registries/session_roles.yaml`, `.claude/agents/session-platform-*.md`

## Assumptions / Open Questions
- None.

## Implementation Notes
- Stub added by agent-working per owner 2026-10-23 (the user chose option (a) on #715, comment 6357234011); platform owns it and may rewrite it. The first attempt (owns line without the file) was rejected by the roster validator (`glob-matches-nothing`), so the minimal root `SECURITY.md` lands in the same PR. It has no frontmatter (root policy file, like CONTRIBUTING.md and README.md).

## Test Summary
- `route SECURITY.md` -> platform / platform-planner. `tools.sessions.validate`: 0 findings, 29 roles. `generate_agents --check`: 0 drift. Worst card before 460 (agent-working-implementer, agent-working-planner-u24), after 460; budget not raised.
- Serial `pytest tests/tools -k "session or route or roster or card"` run after the stub landed; see the PR body.

## Files Changed
SECURITY.md (new), registries/session_roles.yaml, .claude/agents/session-platform-*.md (generated).

## Completion Summary
`SECURITY.md` is owned by platform.
