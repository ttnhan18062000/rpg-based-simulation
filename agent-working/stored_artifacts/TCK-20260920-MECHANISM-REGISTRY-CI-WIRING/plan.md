---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-CI-WIRING
artifact_type: plan
tags: [architecture, schema, testing]
---

# Plan — TCK-20260920-MECHANISM-REGISTRY-CI-WIRING

## Goal
Wire the mechanism-registry program's real CLI checks into CI, since the tests exercising them as
library calls are not the same claim as a human/CI-auditable gate step.

## Design
1. Add a "Mechanism registry checks (blocking)" step to `arch-docs`, right after its existing
   pytest "Run" step: `make mechanism-registry-validate`, `make mechanism-atlas-check`,
   `make mechanism-capabilities-check`, `make mechanism-wiring-map-classdef-check`, run
   sequentially with GHA's own default `bash -eo pipefail` step shell (first failure stops the
   step and fails the job).
2. Add a "Fetch origin/main for mechanism registry changed-code check" step
   (`git fetch origin main:refs/remotes/origin/main --depth=1`, warning-only on failure) so the
   changed-code-check's own default `--base origin/main` resolves in CI's shallow checkout.
3. Add a "Mechanism registry checks (report-only)" step: the 3 report-only targets, each with
   `|| true`.
4. Fix the stale "6 invariants" Makefile help text to 10.

## Verification plan
For each of the 4 blocking checks: deliberately break the specific condition it checks
(unresolvable `depends_on` id, a registry state changed without regenerating its consumer
artifact, etc.), confirm the check's own real non-zero exit code, then restore via the pristine
backup and re-confirm clean. Simulate the CI shallow-checkout scenario for the changed-code-check's
own fetch step against a real bare-repo fixture (not the working worktree, whose own
remote-tracking refs don't transfer the same way a real `git clone` from a real remote would).

## Non-goals
- Any pipeline, done-checker, or agent-definition change.
- Upgrading any report-only check to blocking.
- Any mechanism-state or registry-content change (simulation behaviour must stay still).
