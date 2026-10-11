---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS
phase: done
date: 2026-10-11
tags: [testing, regression]
---

# Investigation
- Loader and kernel recipe from rpg-planner (pinned tests on main), plus audit_mode, which the protocol requires.
- Kernel writes data/runs/<run_id>; the harness passes a gate-prefixed id and removes exactly that directory.
- Events must be flushed before the metrics read them, so the child shuts the kernel down before calling compute.
- rpg's module does not exist yet; planned path and signature are from rpg-planner.
