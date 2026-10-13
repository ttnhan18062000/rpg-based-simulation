---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# test_plan — TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD

## Cases
- both classes appear once in the guide and once in the plan, with equal sender and receiver cells
- the status-request row says it never authorizes work
- the board has exactly the header and separator, seven columns
- route names the lead domain for the board; validate and generator check clean

## Proof Plan
- level: docs consistency tests plus registry validation
- proof kind: behavioural tests and tool runs
- oracle source: ticket acceptance criteria 1-5
- expected effect: the protocol is written once, consistently, and the lead owns its board
- selected commands: `python -m pytest -q tests/docs/test_lead_status_protocol.py tests/tools/test_session_*.py`; `python3 -m tools.sessions.validate`; `python3 -m tools.sessions.generate_agents --check`; `python3 -m tools.sessions.route agent-working/lead/board.md`
