---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED
date: 2026-10-05
tags: [ai, process-improvement]
---

# Test Plan: TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED

Existing done_checker tests stay green except the six whose meaning changed (reasons recorded in each test). New tests listed in the ticket's Test Summary.

## Proof Plan

- Level: unit with a CLI case.
- Proof kind: executable tests.
- Oracle source: the ticket's acceptance criteria and the owner's 2026-10-05 direction.
- Expected effect: `pytest tests/tools/test_done_checker_static.py` passes; the cleaner deletes nothing; scoped delete removes only the named directory.
- Selected commands: `pytest tests/tools/test_done_checker_static.py`; `pytest tests/tools tests/docs -k "done_checker or lifecycle or workflow or skill or agent"`.
