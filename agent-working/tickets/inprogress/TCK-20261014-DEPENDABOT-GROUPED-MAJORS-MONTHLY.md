---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY
phase: inprogress
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY

## Title
Dependabot: monthly schedule, one grouped majors PR and one grouped minor/patch PR per ecosystem, Node held to LTS

## Status
INPROGRESS

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Dependabot's first run after #561 opened 21 PRs (#562-#582) and hit `open-pull-requests-limit`. The owner decided on 2026-10-14 to **stay current on majors** rather than ignore them, but in fewer, grouped PRs on a monthly schedule.

## Scope
- `.github/dependabot.yml`, for every ecosystem:
  - `schedule.interval: monthly`;
  - two groups: `<eco>-major` (`update-types: [major]`) and `<eco>-minor-patch` (`[minor, patch]`), so each ecosystem
    opens at most 2 PRs a month;
  - keep the labels.
- `docker` ecosystem: `ignore` Node versions that are not LTS
  (`{dependency-name: node, versions: [">=25"]}`, widened deliberately when the next even LTS line matures), so
  Dependabot does not re-propose Node 26 after the owner chose 24.
- PR body: a per-PR table for the open Dependabot PRs, saying which tickets supersede them. The user closes them.

## Out of Scope
Merging or closing any Dependabot PR (user). Version upgrades themselves (sibling tickets).

## Acceptance Criteria
- dependabot.yml parses; after merge, GitHub's Dependabot config check shows no error (validated).
- The next Dependabot run opens grouped PRs only (observed after merge, then recorded).

## Related Tickets
`TCK-20261014-DEPENDABOT-AND-BASE-IMAGE-PINS` (#561); siblings `TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13`, `TCK-20261014-FRONTEND-NODE-24-LTS`, `TCK-20261014-ACTIONS-MAJORS-COMBINED`.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1, step 2)

## Related Stored Artifacts
None.

## Related Code Areas
`.github/dependabot.yml`

## Assumptions / Open Questions
Security updates are not governed by the version-update schedule.

## Implementation Notes
`.github/dependabot.yml`: all five ecosystems are monthly, each with a `<eco>-major` group and a `<eco>-minor-patch` group (at most 2 PRs a month per ecosystem); the docker ecosystem ignores `node >=25`. Labels kept. The superseded `TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS` was started and dropped before shipping when the owner chose to stay current; its closure-tool records remain in the append-only monitoring shards and no `working_log.csv` row was written for it.
## Test Summary
- **validated (schema):** the file parses with 5 ecosystems, monthly, 2 groups each, and the node ignore. GitHub's own config check and the first grouped run are observed after merge (not yet).
## Files Changed
- `.github/dependabot.yml`
## Completion Summary
Dependabot now opens grouped major and minor/patch PRs monthly and does not propose Node 25+.

Supersedes TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS (dropped before merge on the owner's 2026-10-14 decision); its record in the W42 platform-implementer-step1-closure.working_log.jsonl shard is superseded, not a closed ticket.
