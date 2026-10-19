---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-TEST-YML-NODE-24-IN-FRONTEND-AND-JSCPD-LANES
phase: open
date: 2026-10-19
tags: [testing, workflows]
---

# TCK-20261019-TEST-YML-NODE-24-IN-FRONTEND-AND-JSCPD-LANES

## Title
test.yml's Frontend and jscpd steps run Node 24, the same as the frontend image, instead of Node 20.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Issue #631 (platform-planner, routed by lead-planner, 2026-10-18): CI annotations warn that `actions/setup-node@v4` runs on the deprecated Node 20, and `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19. The runner gets no pre-emptive pin (`docs/plans/codebase_health/ubuntu_26_runner_precheck.md`). In `test.yml` both `setup-node` steps also request `node-version: 20`:
- the Frontend job (~L727);
- the jscpd step (~L1046).

The frontend image is already on Node 24 (TCK-20261014-FRONTEND-NODE-24-LTS), so CI tests the frontend on a different Node from the one it ships on.

The action major (`setup-node@v4` -> `@v7`) is Dependabot #609, CI green. testing-planner approves #609's `test.yml` side by comment. This ticket is only the `node-version` change, made after #609 merges.

## Scope
1. In `.github/workflows/test.yml`, set `node-version: 24` on both `setup-node` steps. Keep `cache: npm` and `cache-dependency-path` as they are.
2. Update the comment beside the jscpd step only if it names a Node version.
3. If any test under `tests/static/` pins the Node version or the setup-node ref by an exact literal, change it to match by action name, as TCK-20261015-SETUP-UV-PIN-IN-SPLIT-TOOLS-JOBS-TEST-BLOCKS-DEPENDABOT did for setup-uv. `tests/static/test_ci_step_summary_reporting.py` lists `actions/setup-node` by name only; confirm it.

## Out of Scope
- The `setup-node` major itself (Dependabot #609).
- `runs-on` pins. These are reactive only, per the precheck: pin one job to `ubuntu-24.04` only if it fails on 26, with a ticket and a dated exit.
- `deploy-docs.yml` (platform's) and `rpg-gate-report.yml` (ownership being added to testing in `registries/session_roles.yaml`, agent-working's file).

## Acceptance Criteria
- [ ] AC1: both `setup-node` steps in `test.yml` request Node 24. `grep -n 'node-version' .github/workflows/test.yml` shows no 20.
- [ ] AC2: the Frontend job and the jscpd step pass on the PR. The job logs show Node v24.x. Quote the line in the Test Summary.
- [ ] AC3: no static test pins a setup-node version by exact literal, or one that did is changed to match by name, with a regression case.
- [ ] AC4: no other job or step changes.

## Related Tickets
- TCK-20261014-FRONTEND-NODE-24-LTS (frontend image on Node 24)
- TCK-20261009-UBUNTU-26-RUNNER-PRECHECK (no pre-emptive pin)
- TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24 (platform's side)
- TCK-20261015-SETUP-UV-PIN-IN-SPLIT-TOOLS-JOBS-TEST-BLOCKS-DEPENDABOT (the match-by-name pattern)

## Related Docs
- docs/plans/codebase_health/ubuntu_26_runner_precheck.md

## Related Stored Artifacts
- None.

## Related Code Areas
- .github/workflows/test.yml
- tests/static/test_ci_step_summary_reporting.py

## Assumptions / Open Questions
- Dependabot #609 merges first. If it hasn't merged when this is picked up, change only `node-version` on `@v4`. The two changes are independent.
- jscpd's pinned version runs on Node 24. If it doesn't, stop and report; do not keep Node 20 for jscpd alone without a ruling.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
