---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24
artifact_type: investigation
tags: [platform, delivery]
---

# Investigation: TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24

- `deploy-docs.yml` today: `actions/setup-node@v4` with `node-version: 20` (L40-43); trigger `workflow_dispatch` only; all actions tag-pinned.
- Other `setup-node@v4` uses are in `test.yml` (L727, L1046), testing-planner's; not touched here (issue #631).
- Latest `actions/setup-node` release at 2026-10-18: v7.1.0 (GitHub releases API), so the tag-pin style becomes `@v7`.
- `deploy-docs.yml` is in `lead`'s `owns` (session_roles.yaml L134); the owner decided on #560 (2026-10-16) that it moves to platform.
- `TCK-20261014-ACTIONS-MAJORS-COMBINED` sits in `inprogress/` although its bumps landed in #588 (5324afafe); its evidence items 1-4 are checked in item 4 of the plan (findings go in the ticket).
