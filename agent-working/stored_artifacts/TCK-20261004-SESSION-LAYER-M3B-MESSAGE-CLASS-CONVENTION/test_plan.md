---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M3B-MESSAGE-CLASS-CONVENTION
phase: open
date: 2026-10-05
tags: [ai]
---

# test_plan — TCK-20261004-SESSION-LAYER-M3B-MESSAGE-CLASS-CONVENTION

`test_session_cards.py` (budget test, unchanged `CARD_BUDGET_TOKENS`), roster/generator suites and `tests/docs` green; `validate_frontmatter.py` OK on the new guide.

## Proof Plan
- level: unit and integration with real temporary git repositories
- proof kind: automated tests, plus a run against this repository as a positive control
- oracle source: git itself, the real manifest
- expected effect: as stated in the ticket's acceptance criteria
- selected commands: `pytest tests/tools/test_session_route.py tests/tools/test_session_status.py tests/tools/test_session_prune_branches.py tests/tools/test_session_cards.py tests/tools/test_session_roster.py`
