---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-CI-WIRING
artifact_type: test_plan
tags: [architecture, schema, testing]
---

# Test Plan — TCK-20260920-MECHANISM-REGISTRY-CI-WIRING

## Normal flow
All 4 blocking + 3 report-only `make` targets run clean against the current, committed registry
state (already proven true earlier this session — this ticket does not change registry content).

## Failure-mode proof (the load-bearing part of this ticket, per its own AC #3)

For each blocking check, deliberately broke its specific condition, captured the real (non-piped)
exit code, confirmed non-zero, then restored from a pristine backup and re-confirmed clean:

| Check | Break applied | Real exit code |
|---|---|---|
| `mechanism-registry-validate` | Added an unresolvable `depends_on` id to `combat_resolution` | 2 (make) — `registry.py` itself printed `FAIL: 1 violation(s)` |
| `mechanism-atlas-check` | Changed `combat_resolution`'s `state` to `gap` without touching the atlas | 2 — `DRIFT: 1 mapped badge(s) disagree` |
| `mechanism-capabilities-check` | Same registry change as above | 2 — `DRIFT: 1 mapped card(s) disagree` |
| `mechanism-wiring-map-classdef-check` | Changed `belief_cycle`'s `state` to `gap` without touching the wiring map | 2 — `DRIFT: 1 node(s)... disagree` |

Each restore verified via `git diff --stat registries/mechanisms.yaml` showing no diff before
moving to the next check, so no break bled into the next test.

## Report-only never-fails proof
Ran all 3 report-only targets against the real, clean registry: each exits 0. Read each tool's own
`main()` to confirm the 0-exit is unconditional by design, not merely true on today's clean input —
the `|| true` in the CI step is an added, independent safety net on top of that.

## Shallow-checkout fetch-step proof
See investigation.md's own bare-repo fixture — a real single-branch depth-1 clone with zero prior
knowledge of `main`, the fetch step's exact command creates a resolvable `origin/main`, and the
changed-code-check tool runs correctly against it afterward.

## Coverage delivered
No new Python test file — this ticket is CI/Makefile configuration, verified by direct command
execution and a realistic clone-topology fixture rather than pytest (the existing 241
`tests/unit/tools/` tests are unaffected and still pass). `tests/unit/tools/` 241 passed
(unchanged) confirms no regression from touching `Makefile`'s help text.
