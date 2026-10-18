---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24
phase: open
date: 2026-10-18
tags: [platform, delivery]
---

# TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24

## Title
Platform workflows on the Ubuntu 26 runner migration (observe publish-images, pin only reactively) and deploy-docs off Node 20 (setup-node bump, Node 24, roles move to platform)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Every PR's CI annotations say "ubuntu-latest will migrate to Ubuntu 26 beginning October 19, 2026" and warn that
`actions/setup-node@v4` runs on the deprecated Node 20. lead-planner asked platform to cover its own workflows and
raise one issue for the others (2026-10-18).

The recorded decision for the runner is `docs/plans/codebase_health/ubuntu_26_runner_precheck.md`
(`TCK-20261009-UBUNTU-26-RUNNER-PRECHECK`): a probe of `test.yml` on `ubuntu-26.04` matched main in every job, and the
recommendation is **no pin**. Let `ubuntu-latest` migrate, and if a job fails after the rollout, pin only that job to
`ubuntu-24.04`, with a comment naming the ticket and a dated exit. lead-planner chose to follow it (option A,
2026-10-18). This ticket applies that rule to the platform-owned workflows.

`deploy-docs.yml` is still lead-owned in `registries/session_roles.yaml`. The owner decided on #560 (2026-10-16) that
it moves to platform; the roles diff is in this ticket, and the owner confirms it in the PR.

## Scope
1. **publish-images.yml: observe, don't pin.**
   - After 2026-10-19, read the first `publish-images` run on main through the Actions API.
   - Record the runner image name and version from the job log, every step's conclusion, and the annotations.
   - Record any step that fails or newly warns, including buildx, cosign and Trivy. The precheck didn't probe
     those steps on 26.
   - The label can resolve to either image until 2026-11-19. If the first run is still on 24.04, record that, and read
     the next run that reports 26.
   - If a step fails because of 26, pin only that job to `ubuntu-24.04`. Add a comment naming this ticket and a dated
     exit (re-check by 2026-11-19, or the date in the actions/runner-images issue). Otherwise leave `ubuntu-latest`.
2. **deploy-docs.yml: Node bump.**
   - `actions/setup-node@v4` → the current major. Keep the tag-pin style of that file (no SHA re-pin).
   - `node-version: 20` → `24`. That matches `docker/frontend.Dockerfile` on Node 24 since
     `TCK-20261014-FRONTEND-NODE-24-LTS`.
   - Change no other line. Keep the disable header comment and the `workflow_dispatch`-only trigger. No pin, no
     dispatch: Pages is off, and re-enabling it is `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING`.
3. **Roles diff.**
   - Move `.github/workflows/deploy-docs.yml` from lead-planner's `owns` to platform's `owns` in
     `registries/session_roles.yaml`.
   - Regenerate the cards with `tools/sessions/generate_agents.py`.
   - Check with `python3 -m tools.sessions.route .github/workflows/deploy-docs.yml`.
   - The PR body states that the owner decided this on #560 (2026-10-16) and asks the owner to confirm.
4. **Stale ticket check: `TCK-20261014-ACTIONS-MAJORS-COMBINED`.**
   - It is still in `agent-working/tickets/inprogress/`, but its bumps are on main: PR #588 (5324afafe, "no tickets").
   - Check its evidence items against #588 and the runs after it, including testing-planner's artifact proofs and the
     first scheduled slow run's artifacts.
   - If they are met, close it truthfully, with retrospective staging artifacts labelled as such. If an item was never
     shown, close it with the gap stated, or leave it open, and report which to platform-planner. Don't invent evidence.
5. **Issue for the other owners** (filed by platform-planner, not part of the implementer's diff). The routing came from
   lead-planner on 2026-10-18:
   - `test.yml` (setup-node@v4 at L727 and L1046, node-version 20; all jobs on `ubuntu-latest`),
     `slow-regression.yml` and `slow-regression-watchdog.yml` → testing-planner. Per the precheck, read their first
     runs after 2026-10-19 and pin reactively.
   - `rpg-gate-report.yml` → testing-planner. `route.py` reports it **unowned**: no domain's owns glob matches. That
     registry gap is the owners' to close.
   - `pr-body-lint.yml` → agent-working-planner.

## Out of Scope
- Pre-emptive `runs-on` pins on any workflow (the precheck decision).
- Edits to `test.yml`, `slow-regression*.yml`, `rpg-gate-report.yml` and `pr-body-lint.yml`: their owners'.
- Re-enabling Pages or dispatching `deploy-docs.yml`.
- SHA-pinning `deploy-docs.yml`'s actions.

## Acceptance Criteria
- `deploy-docs.yml`: only the setup-node major and `node-version` lines change. Check with `git diff`. YAML parses.
  `tests/static` passes, including `test_ci_step_summary_reporting.py`, which references deploy-docs.
- The roles diff moves exactly the one path. `route.py` returns platform for it. The generated cards are in sync
  (generator check or its static test passes).
- publish-images: the first post-10-19 run on main is recorded in the Test Summary. Record the image name/version from
  the log, the step conclusions and the annotations (the run URL, not just a green colour). A pin is added only if a
  step failed because of 26, with the ticket comment and a dated exit.
- ACTIONS-MAJORS-COMBINED: closed (done_checker_static PASS) or reported as not closable, with the missing evidence
  named.
- The issue exists and is linked in Related Tickets.

## Related Tickets
- `TCK-20261009-UBUNTU-26-RUNNER-PRECHECK` (done: the "no pin" decision and the probe, PR #477).
- `TCK-20261014-ACTIONS-MAJORS-COMBINED` (stale in inprogress; PR #588).
- `TCK-20261014-FRONTEND-NODE-24-LTS` (done: the frontend image on Node 24).
- `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING` (deploy-docs re-enable conditions).
- Owner decision #560 (2026-10-16): deploy-docs.yml moves to platform.
- Issue #631 (other workflow owners).

## Related Docs
`docs/plans/codebase_health/ubuntu_26_runner_precheck.md`

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20261009-UBUNTU-26-RUNNER-PRECHECK/`

## Related Code Areas
`.github/workflows/publish-images.yml`, `.github/workflows/deploy-docs.yml`, `registries/session_roles.yaml`,
generated session cards

## Assumptions / Open Questions
- The publish-images observation can't happen before 2026-10-19. Items 2-4 can land first. If so, item 1 stays open in
  this ticket and closes with a short follow-up PR.
- Pushes and the PR go through lead-planner to the owner.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
