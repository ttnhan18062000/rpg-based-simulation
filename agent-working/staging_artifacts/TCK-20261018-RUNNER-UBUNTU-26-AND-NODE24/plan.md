---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24
artifact_type: plan
tags: [platform, delivery]
---

# Plan: TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24

Source: the ticket Scope and platform-planner's dispatch (lead option A: no pre-emptive pins, per `docs/plans/codebase_health/ubuntu_26_runner_precheck.md`).

## Steps (one commit per item, review requested after each)
1. Setup: ticket to `inprogress/`, these three staging files.
2. `deploy-docs.yml`: `actions/setup-node@v4` -> the current major (latest release tag checked with the GitHub API; tag-pin style kept) and `node-version: 20` -> `24`. No other line changes; the disable header and the `workflow_dispatch`-only trigger stay.
3. Roles: move `.github/workflows/deploy-docs.yml` from `lead` to `platform` `owns` in `registries/session_roles.yaml`; regenerate the cards with `tools/sessions/generate_agents.py`; check `tools.sessions.route`.
4. Stale ticket `TCK-20261014-ACTIONS-MAJORS-COMBINED`: check each evidence item against PR #588 and the runs after it. Close with retrospective, labelled artifacts only if all items are shown; otherwise report the missing item.
5. Item 1 (publish-images observation) is after 2026-10-19; it stays open and closes in a short follow-up. Pin only if a step fails because of Ubuntu 26.

## Scope guards
No `runs-on` pins now; no edits to test.yml, slow-regression*.yml, rpg-gate-report.yml, pr-body-lint.yml; no Pages re-enable or dispatch; no SHA re-pin. No push or PR from the implementer (they go through platform-planner and lead).
