---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE
artifact_type: test_plan
date: 2026-10-20
tags: [testing, regression, simulation-quality]
---

# Test plan — TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE

- The lint passes on main with V1-V8 mapped.
- Regression cases, each failing the lint: missing entry, nonexistent node id (test and file), no `build_kernel` call, `build_kernel` without `compute`/`pool`, entry for a non-required id, empty entry; and the positive case through a helper and a one-hop import.
