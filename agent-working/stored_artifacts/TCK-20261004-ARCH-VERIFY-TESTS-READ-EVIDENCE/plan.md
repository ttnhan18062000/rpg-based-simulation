---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-ARCH-VERIFY-TESTS-READ-EVIDENCE
phase: open
date: 2026-10-04
tags: [ai, agent-monitoring, testing]
---

# plan — TCK-20261004-ARCH-VERIFY-TESTS-READ-EVIDENCE

1. Checker: changed_test_sources (untracked, working-tree, committed) + verify_event + UNVERIFIED comparison; render shows sources.
2. Schema: optional tests_read on ARCH_VERIFY_SCHEMA, carried by pushEvent, validated in record_events.py, carried by the closure tool.
3. One prompt line in architecture-reviewer.md; schema description reworded; schema.md documents tests_read.
4. No verdict or gate change. Hand-orchestrated path: prompt-only (open question left as noted in the ticket).
