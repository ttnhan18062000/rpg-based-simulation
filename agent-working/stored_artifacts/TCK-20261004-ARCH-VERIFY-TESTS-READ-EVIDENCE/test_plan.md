---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-ARCH-VERIFY-TESTS-READ-EVIDENCE
phase: open
date: 2026-10-04
tags: [ai, agent-monitoring, testing]
---

# test_plan — TCK-20261004-ARCH-VERIFY-TESTS-READ-EVIDENCE

Real-git tests for committed/working-tree/untracked/deleted and both-sources; UNVERIFIED vs read-backed vs no claim; render sources; node-executed pushEvent carrying tests_read (quote swap, non-string dropped, absent when none); record_events validation; closure carry; prompt and schema wording pins.

## Proof Plan
- level: unit with real git repos in tmp_path and node-executed workflow helpers
- proof kind: automated tests
- oracle source: git's own file lists; the events row shape
- expected effect: uncommitted and untracked tests listed; empty findings with an unread test reported unverified; no verdict change
- selected commands: `pytest tests/tools/test_arch_verify_read_check.py tests/tools/test_arch_verify_test_quality_findings.py` plus every test referencing the touched files (634 passed)
