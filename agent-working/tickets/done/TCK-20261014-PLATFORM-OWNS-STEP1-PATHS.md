---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-PLATFORM-OWNS-STEP1-PATHS
phase: done
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-PLATFORM-OWNS-STEP1-PATHS

## Title
Register step 1's new paths (`publish-images.yml`, `dependabot.yml`) to the platform domain's `owns`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
This replaces the parked `devops-s1` T3. It follows the D8 route agreed by the owner on 2026-10-13: each step's PR
adds only the globs it creates to the platform `owns`, the owner confirms the literal diff on that PR, and
agent-working-planner reviews by comment.

## Scope
- In `registries/session_roles.yaml`, under `domains.platform.owns`, add exactly:
  `.github/workflows/publish-images.yml` and `.github/dependabot.yml`.
- Regenerate the role files with `python3 tools/sessions/generate_agents.py`, and run `python3 tools/sessions/validate.py`.

## Out of Scope
Any other glob from the D8 list. Those are registered by the steps that create them.

## Acceptance Criteria
- `validate.py` passes. Both files exist in the same PR.
- The PR body shows the literal two-line `owns` diff for the owner to confirm. agent-working-planner is asked for
  review by comment.

## Related Tickets
Epic `TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY`; `TCK-20261013-PLATFORM-DOMAIN-SEATS`.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (D8 supersession)

## Related Stored Artifacts
None.

## Related Code Areas
`registries/session_roles.yaml`, generated `.claude/agents/session-*.md`

## Assumptions / Open Questions
None.

## Implementation Notes
`registries/session_roles.yaml` `domains.platform.owns` gains exactly `.github/workflows/publish-images.yml` and `.github/dependabot.yml`; role files regenerated.
## Test Summary
- **validated:** `PYTHONPATH=. python3 tools/sessions/validate.py`: `OK: 0 finding(s), 20 role(s)`; both files exist in this PR.
- Owner confirmation of the literal two-line diff and agent-working-planner review are requested in the PR body.
## Files Changed
- `registries/session_roles.yaml`, `.claude/agents/*` (generated), `tests/tools/test_layer_registry.py`, `tests/tools/test_validate_frontmatter.py` (anti-drift sets gained `platform`)
## Completion Summary
Platform owns the two new paths. Merged in #561.
