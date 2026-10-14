---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS
phase: open
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS

## Title
Dependabot: ignore semver-major version updates and move to a monthly schedule

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Dependabot's first run after #561 opened 21 PRs (#562-#582). Most of them are major bumps (node 20→26,
grafana 10→13, prometheus v2→v3, redis 7→8, actions/checkout 4→7, starlette 0.x→1.x, mcp 1→2 and others), and the
run hit `open-pull-requests-limit`, which shows as a red warning. Each PR runs the full CI. A major upgrade should be
a deliberate ticket owned by the file's domain, not a weekly automated PR.

## Scope
- `.github/dependabot.yml`, for every ecosystem:
  - add `ignore: [{dependency-name: "*", update-types: ["version-update:semver-major"]}]`;
  - change `schedule.interval` from `weekly` to `monthly`, to cut CI cost. Security updates are not governed by
    this schedule.
  - Keep the grouped minor/patch PRs and the labels.
- In the PR body, give a per-PR recommendation for the open Dependabot PRs. The user closes or merges them;
  nothing is merged before rpg-next.
  - Close (major, platform): #563 prometheus v3, #564 grafana 13, #566 redis 8, #577 node 26.
  - Close (major, actions; touch workflows owned by others, including test.yml/testing): #572, #573, #574, #575.
  - Owner's call (rpg majors): #567, #568, #569, #570, #579, #580, #581, #582.
  - Keep for review after rpg-next (minor/patch groups): #562, #571, #576 (platform), #565, #578 (rpg; #578 likely
    carries the anyio CVE-2026-63374 fix).

## Out of Scope
Upgrading any major version (each is its own future ticket in its owner's domain). Merging or closing PRs (user).

## Acceptance Criteria
- dependabot.yml parses, and GitHub's Dependabot config check shows no error after merge (validated).
- The PR body carries the recommendation table above.

## Related Tickets
`TCK-20261014-DEPENDABOT-AND-BASE-IMAGE-PINS` (#561).

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1)

## Related Stored Artifacts
None.

## Related Code Areas
`.github/dependabot.yml`

## Assumptions / Open Questions
Dependabot may not close the PRs that are already open when an ignore rule is added. The user closes them, or
comments `@dependabot ignore this major version` on each one.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
