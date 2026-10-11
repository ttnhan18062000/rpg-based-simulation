---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-SESSION-START-FOR-ROLE-ISSUES
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# test_plan — TCK-20261011-SESSION-START-FOR-ROLE-ISSUES

## Cases
- stubbed `gh` with one issue: listed after the handover note; only `for:<role>` requested, no `body` field, `--limit 11`
- second instance requests its role's label
- `gh` failing (exit 1), bad JSON, wrong JSON shape, empty list, missing, and hanging: output equals the output without the feature; the hang case finishes within seconds
- 11 issues show 10 plus the "and more" line
- `compact` makes no call
- age rendering (days, hours, minutes, unreadable)

## Proof Plan
- level: unit/integration with a stubbed `gh` on PATH
- proof kind: behavioural tests
- oracle source: ticket acceptance criteria 1-6
- expected effect: a session sees its role's open issues at start, and a broken or slow GitHub never changes or delays the start beyond the timeout
- selected commands: `python -m pytest -q tests/tools/test_session_resolve_and_hook.py tests/tools/test_session_*.py`
