---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT
artifact_type: plan
tags: [rendering, testing, world, investigation]
---

# Plan (Scope step; the live-or-frozen decision goes to rpg-planner first)

Options: (A) frozen reference only; (B) live corpus only; (C) both. After the decision: rename or redocument the six tests, align `docs/visual_quality/{current_state,scoring_contract}.md` and the `src/rendering/{variants,density}.py` docstrings, update INFRA-373 through `parity_ledger_writer`, record the decision in `docs/visual_quality/scoring_contract.md`, and (B/C) add live coverage on a world with a forest and a cave.
