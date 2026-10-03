---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING

Written at closure.

## Proof Plan
- level: measurement only (no test added or changed)
- proof kind: executed runs under coverage; collect-only marker census
- oracle source: the selected tests as they stand; `docs/testing/test_taxonomy.md` for placement
- expected effect: counts and percentages reproducible from the stated commands at the stated SHA
- selected commands:

| Check | Command | Observed |
|---|---|---|
| Social unit tests | `python -m coverage run --source=src/systems/social_systems -m pytest -q tests/unit/social` | 296 passed |
| With social-importing files elsewhere | same, plus the 20 files | 372 passed |
| Marker census | collect-only with a plugin over the same 372 | 238 + 66 unmarked; no domain/level |
| Diff gate | `git diff --name-only origin/main` | no test file from this ticket |
