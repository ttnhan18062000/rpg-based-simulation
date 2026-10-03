---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY
date: 2026-10-03
tags: [performance, architecture, determinism]
---

# Plan: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY

## Summary
Add `tools/perf/hash_callsite_inventory.py` (stdlib `ast`, no engine import), tests, and the document
`docs/performance/hash_callsite_inventory.md` (generated tables between markers plus a hand-written
analysis) with a committed JSON. Evidence only (PA-03A call-site half); no measurement, no `src/` edit.

## Steps
1. Survey hash and fingerprint references in `src/`; read `checkpoint.py`, `fingerprint.py`, the kernel
   regions, the compiler and certification harness regions, and the consumers.
2. Write the scanner: resolved calls by mechanism, guard expressions, direct hashlib digests of canonical
   data, digest-producing functions, unresolved candidates, `tests/` references; `--check`, `--update-doc`.
3. Tests; scope-map entry.
4. Write the hand-written sections (per site, governance, schemes, contradictions, limits).
5. Send the document to perf-planner; close after review.

## Scope guards
No `src/` edit; no edit to the three compared documents; no measurement; PERF-D5 is the planner's.
`--check` is not wired into CI. `.claude/agents/test-scoper.md` is not touched.

## Acceptance-criteria map
AC1 -> subprocess test and `cmp`; AC2 -> table G1 plus the grep comparison in the test plan;
AC3 -> document section 3; AC4 -> section 4; AC5 -> section 6; AC6 -> test run; AC7 -> diff scope.
