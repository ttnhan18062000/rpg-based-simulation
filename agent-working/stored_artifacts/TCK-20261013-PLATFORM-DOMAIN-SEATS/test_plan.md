---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-PLATFORM-DOMAIN-SEATS
artifact_type: test_plan
tags: [ai, governance, process-improvement]
---

# test_plan — TCK-20261013-PLATFORM-DOMAIN-SEATS

## Cases
- compose.yaml and docker/backend.Dockerfile route to platform, not lead-planner; Makefile and pyproject.toml stay lead
- platform has exactly a planner and an implementer; the implementer takes dispatch from the user and its planner
- both platform cards exist and fit 400 tokens; role counts are 20

## Proof Plan
- level: unit tests on the real manifest plus validator and generator checks
- proof kind: behavioural tests and tool runs
- oracle source: ticket acceptance criteria AC1-AC5
- expected effect: compose and Docker edits are attributed to platform; the registry validates with 20 roles
- selected commands: `python -m pytest -q tests/tools/test_session_*.py`; `python3 -m tools.sessions.validate`; `python3 -m tools.sessions.generate_agents --check`
