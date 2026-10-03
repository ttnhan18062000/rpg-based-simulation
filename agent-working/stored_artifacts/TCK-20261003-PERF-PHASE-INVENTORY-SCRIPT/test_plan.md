---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT
date: 2026-10-03
tags: [performance, architecture, engine]
---

# Test Plan: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT

`python3 -m pytest tests/tools/test_phase_inventory.py tests/tools/test_test_scope_coverage_static.py -q`

Covers a synthetic pipeline (conditional, loop, flagged, dynamic-name, direct operation, direct call),
document extractors, declaration parsing, deterministic output, `--check` pass and fail for an added,
removed and reordered phase, unreadable committed file, a no-`src`-import subprocess check, and the
real pipeline (parses, non-empty, duplicate-free ordinals only; no fixed count).

## Proof Plan
- level: unit plus one CLI integration over the real pipeline
- proof kind: behavioral tests and a byte-identity check of two runs
- oracle source: the ticket's acceptance criteria and synthetic fixtures
- expected effect: report-only tooling, no engine behavior change
- selected commands: the pytest command above; `phase_inventory.py --check docs/performance/phase_inventory.json`
