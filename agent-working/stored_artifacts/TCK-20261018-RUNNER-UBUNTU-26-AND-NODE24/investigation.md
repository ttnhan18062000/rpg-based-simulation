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

## setup-node v4 -> v7: release notes read (2026-10-18, GitHub releases API)
- **v5.0.0 (breaking):** automatic npm/yarn/pnpm caching when `package.json` has a valid `packageManager` field (off with `package-manager-cache: false`); the action runs on node24, which needs a runner >= v2.327.1 (GitHub-hosted runners are). `website/package.json` has no `packageManager` field, and the step sets `cache: npm` explicitly, so this does not change the step.
- **v6.0.0 (breaking):** automatic caching is limited to npm. No effect: the step already uses `cache: npm` with `cache-dependency-path: website/package-lock.json`.
- **v7.0.0:** ESM migration, new `cache-primary-key` and `cache-matched-key` outputs, the dummy `NODE_AUTH_TOKEN` export is removed (the step does not publish or read the token), `mirrorToken` fix. Nothing removed that this step passes; the step passes only `node-version`, `cache` and `cache-dependency-path`. No `always-auth` input is used.
- **v7.1.0:** `mise.toml` support, absolute `node-version-file` paths, Node version validation with a manifest-fetch retry. No breaking change.
- Result: no breaking change affects this step. The bump is validated (static) only.

## TCK-20261014-ACTIONS-MAJORS-COMBINED: evidence check against #588 (merged 2026-10-15, 5324afafe)
- Item 2 (PR-run junit artifacts with files): shown in #588's body (run 38544297527: tools-a-e 1 file, tools-f-z 1 file, api-cli-engine 7 files); testing-planner approved at bc17880a0 and 293425d68.
- Item 3: not applicable; #529 is still OPEN, so no rebase step arose.
- Item 4 (first scheduled slow run): MET. Run 38700638996 (schedule, 2026-10-15T07:43, 62a01febc) is the first after the merge. Artifacts `certification-report-62a01febc...` (3,705 B) and `slow-junit-62a01febc...` (25,907 B) exist and are not expired; steps "Report failing-set changes", "Upload certification report" and "Upload slow JUnit reports" succeeded.
- Item 1 (rpg-gate-report with shard and aggregate executed): NOT MET. Every `rpg-gate-report` schedule run after the merge (38717903321, 38883951584, 39021377963) has "Shard" and "RPG gate report" jobs `skipped`; only "Plan from rpg's config" ran. `download-artifact@v8` and the final `upload-artifact@v7` in that workflow have therefore never run on main. testing-planner accepted this as a post-merge check in #588.
- deploy-docs hidden-file / upload-pages-artifact v5 check: NOT shown (Pages is off; first real run is under TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING).
