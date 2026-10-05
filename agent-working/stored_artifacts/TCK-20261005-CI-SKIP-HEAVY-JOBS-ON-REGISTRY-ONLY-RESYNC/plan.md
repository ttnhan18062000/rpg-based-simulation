---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261005-CI-SKIP-HEAVY-JOBS-ON-REGISTRY-ONLY-RESYNC

Recorded at close; the plan followed was the reviewer's brief with two deviations noted below.

1. `tools/test_architecture/registry_resync_skip.py`: `decide()` returns `unchanged=true` only for `pull_request`/`synchronize` with BEFORE present, an identical `git patch-id --stable` (REGISTRY excluded) before and after, and every `Tests` run on BEFORE green or skipped. Every error is `false`. `main()` always exits 0 and prints the flag first, then a markdown summary naming the deciding rule and the BEFORE SHA.
2. `tests/unit/tools/test_registry_resync_skip.py` with a temp git repo for each required case.
3. Workflow: a `resync-gate` job (blobless full-history clone, `actions: read`) and an `if:` on the jobs the audit found read no real REGISTRY; tools-a-e, tools-f-z, arch-docs, typecheck and code-health keep running.
4. Update the three `tests/static/` workflow-shape pins for the new job.
5. Docs: `docs/testing/migration_ci_lanes.md` (new subsection with the accepted risk and the job table) and the roadmap CI cost row.
6. Live demonstration on PR #338 with negative and positive controls, run IDs from the jobs API.

Deviations from the brief: a separate gate job instead of a `changed-files` output (latency); the Actions API instead of `commits/{sha}/check-runs` (a check run does not name its workflow).
