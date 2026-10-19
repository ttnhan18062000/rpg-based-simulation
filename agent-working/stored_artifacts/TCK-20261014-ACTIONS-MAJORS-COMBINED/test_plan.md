---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261014-ACTIONS-MAJORS-COMBINED
artifact_type: test_plan
tags: [platform]
---

# test_plan — TCK-20261014-ACTIONS-MAJORS-COMBINED

- rpg-gate-report dispatch on the branch: the report lists per-world docs, with no empty or no-data rows (artifact content, not job status).
- PR run of test.yml: the artifact list shows all 3 artifacts with their files; `perf-tripwire` shows both arms measured.
- pr-body-lint and slow-regression-watchdog: checkout v7 steps succeed on the PR run.
- Post-merge (not provable on the PR): deploy-docs' first main run publishes Pages; testing-planner checks slow-regression's `certification-report-<sha>` and `slow-junit-<sha>` on the first scheduled run, and the merge gets reverted if both are missing.
Evidence label: validated (CI).

## Restated evidence (testing-planner, 2026-10-14)
1. The dispatched `rpg-gate-report` report lists the per-world docs; check the artifact content, not just the status (upload :124, download :149, final upload :187).
2. On the PR run: `tools-a-e-junit-<sha>`, `tools-f-z-junit-<sha>`, `api-cli-engine-junit-<sha>` present AND with files; list the file counts.
3. If this merges before #529 there is no item 3 (#529 bumps its own steps). If #529 merges first: rebase, bump its new steps, show `perf-tripwire` with both arms measured.
4. Post-merge: first scheduled slow run has `certification-report-<sha>` and `slow-junit-<sha>`, both with files, or revert. deploy-docs runs on main only; its first main run is watched.


## Proof Plan
**Written retrospectively at ticket close (2026-10-18).** The proofs were the evidence list above; this table records how each was shown at close.
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| junit artifacts present with files on the PR run | CI | artifact content | testing-planner's restated evidence list, 2026-10-14 | three artifacts, each with files | file counts listed in #588's body (run 38544297527) |
| first scheduled slow run has both artifacts with files | CI | artifact content | testing-planner's restated evidence list | `certification-report-<sha>` and `slow-junit-<sha>` exist with files | `gh api repos/<repo>/actions/runs/38700638996/artifacts`; `gh run view 38700638996 --json jobs` |
| rpg-gate-report shard and aggregate run on main | CI | job conclusions | testing-planner's restated evidence list | shard and aggregate executed | `gh run view <id> --json jobs` for 38717903321, 38883951584, 39021377963: skipped (not shown) |
| deploy-docs upload-pages-artifact v5 | CI | first main run | owner's re-enable ticket | Pages artifact uploaded | not run (Pages off) |
