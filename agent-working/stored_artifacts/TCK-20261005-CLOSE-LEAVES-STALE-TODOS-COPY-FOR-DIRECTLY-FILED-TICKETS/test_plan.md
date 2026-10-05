---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS
artifact_type: test_plan
tags: []
---

# Test plan
`tests/tools/test_close_sequence_repairs.py`:
- finalize fails naming a stale `todos/` copy and passes without it; also catches a copy inside a `todos/` subfolder;
- an unrelated `todos/` ticket does not fail finalize;
- the closure tool removes stale copies only for a closed ticket and never touches an unclosed one.

## Proof Plan

- level: unit (checker condition, closure-tool helper)
- proof kind: regression tests with a failing and a passing case
- oracle source: ticket acceptance criteria; `find_closed_ticket_resurrections` semantics
- expected effect: a stale `todos/` copy fails at close time locally, or is removed and reported
- selected commands: `pytest tests/tools/test_close_sequence_repairs.py tests/tools/test_done_checker_static.py`
