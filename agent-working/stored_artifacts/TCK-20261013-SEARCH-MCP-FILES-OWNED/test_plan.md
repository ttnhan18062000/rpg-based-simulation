---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-SEARCH-MCP-FILES-OWNED
artifact_type: test_plan
tags: [ai, governance]
---

# test_plan — TCK-20261013-SEARCH-MCP-FILES-OWNED

## Cases
- the five files route to agent-working (OWNED)
- every role's card is within the 400-token budget
- same-directory file globs fold into one brace group; lone files, files in different directories and directory globs are left alone

## Proof Plan
- level: unit tests plus the validator and the generator's drift check
- proof kind: behavioural tests
- oracle source: ticket acceptance criteria AC1-AC3
- expected effect: validate reports 0 findings, generate_agents --check is clean, all cards within budget
- selected commands: `pytest tests/tools/test_session_cards.py`; `python3 -m tools.sessions.validate`; `python3 -m tools.sessions.generate_agents --check`
