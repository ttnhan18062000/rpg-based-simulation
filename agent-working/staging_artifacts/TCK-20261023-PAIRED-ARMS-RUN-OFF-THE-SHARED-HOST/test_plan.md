---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST
phase: open
date: 2026-10-26
tags: [testing, performance, determinism]
---

# TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST: test_plan

tests/static/test_ci_paired_arms_workflow_shape.py (10): dispatch-only (no pull_request, push, schedule, workflow_run...); inputs; concurrency group and cancel-in-progress false; pin guard and context guard cover the file; plan/arms/aggregate with contents: read; matrix per (world, seed), both arms in the same job via paired_arms run-arm; one checkout of the dispatched ref per job; artifact names; assemble before the paired --collected call, which has --verdict-json and no --jobs/--clean-cache; no `| tee`.
tests/unit/tools/test_paired_arms.py (~30 cases): world constants equal paired.py's; plan sets, modes, terrain, refusals, slug, CLI lines; run_arm with paired faked (cache key, cost file shape, cached, repeat); assemble merge, python/os mismatch refused, cpu/name/image across jobs allowed, within-key image refused, pair job missing an arm refused, missing/invalid runner record refused, differing bytes refused, empty and bad sha refused, CLI exit 2/0.
