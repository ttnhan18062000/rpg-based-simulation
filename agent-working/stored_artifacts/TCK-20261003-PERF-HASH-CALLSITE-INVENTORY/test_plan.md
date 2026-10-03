---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY
date: 2026-10-03
tags: [performance, architecture, determinism]
---

# Test Plan: TCK-20261003-PERF-HASH-CALLSITE-INVENTORY

`python3 -m pytest tests/tools/test_hash_callsite_inventory.py tests/tools/test_test_scope_coverage_static.py -q`

Synthetic source covers direct, aliased-import (`as`), module-attribute, instance (`self.x = Class()`),
guarded (if, conditional expression, short-circuit), hand-rolled digest, an unresolved receiver, the
hasher's own implementation, deterministic output, `--check` pass / added / removed / unreadable, doc
block replacement, and a subprocess check that `src` is never imported. The real-source test finds the
kernel call sites by mechanism and enclosing function, never by line or total count.

## Manual grep comparison (AC2)
Command: `grep -rnE "(get_hash|compute_hash|get_fingerprint)\(|\.fingerprint\(\)" src --include=*.py`,
minus docstring and comment lines. Real calls found by grep: `state.py:1641`; `harness.py:186, 311`;
`compiler.py:792, 803`; `kernel.py:397, 710, 1151, 1186, 1255`; `checkpoint.py:188, 191, 280`: 13 calls.
The scanner reports those 13 plus `harness.py:257`, which grep for those names cannot see (it is a
`hashlib.sha256` over canonical data): 14. Remaining grep hits (`checkpoint.py:21, 151, 171, 268`) are
docstrings. No call was missed.

## Proof Plan
- level: unit plus CLI integration over the real tree
- proof kind: behavioral tests, byte-identity of two runs, and the manual grep comparison above
- oracle source: the ticket's acceptance criteria and the grep of `src/`
- expected effect: report-only tooling, no engine behavior change
- selected commands: the pytest command above; `hash_callsite_inventory.py --check docs/performance/hash_callsite_inventory.json`
