---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-HOST-LEAD-PLANNER-U24
artifact_type: test_plan
tags: [ai, governance, process-improvement]
---

# test_plan — TCK-20261013-HOST-LEAD-PLANNER-U24

## Cases
- validator: 0 findings, 18 roles; the u24 seat is a main-checkout planner nobody dispatches to
- u24 grants are exactly its page + drafts + monitoring + REGISTRY; writing the page is clean; board.md, Makefile, .mcp.json, stack_seed_review.md are crossings naming `lead-planner`
- lead-planner writes board.md and Makefile cleanly; the u24 page is a crossing naming `lead-planner-u24`
- a role with no override keeps the domain exemption
- u24 card has the note and every card is within 400 tokens; generated files current; launch resolves to the main checkout; non-string card_note rejected

## Proof Plan
- level: unit tests on the real manifest plus validator and generator checks
- proof kind: behavioural tests and tool runs
- oracle source: ticket acceptance criteria AC1-AC7
- expected effect: neither lead can write the other's file without a boundary warning; the u24 seat launches without a worktree or lease
- selected commands: `python -m pytest -q tests/tools/test_session_*.py tests/docs`; `python3 -m tools.sessions.validate`; `python3 -m tools.sessions.generate_agents --check`; `python3 -m tools.sessions.launch lead-planner-u24 --dry-run --allow-stale`
