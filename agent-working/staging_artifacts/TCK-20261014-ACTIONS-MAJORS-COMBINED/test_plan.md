---
status: active
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
