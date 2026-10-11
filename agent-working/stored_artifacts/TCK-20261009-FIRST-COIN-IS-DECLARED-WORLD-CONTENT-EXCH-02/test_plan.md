---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02
artifact_type: test_plan
tags: [economy, content, resource]
---

# test_plan — TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02

## Tests
tests/unit/worldbuilding/test_first_coin_is_declared_content.py

## Acceptance map
- [ ] A compiled world's buildings and residents start with their declared coin and stock (tests/unit/worldbuilding/test_first_coin_is_declared_content.py).
- [ ] Conservation holds with the declared coin.
- [ ] Pinned paired measurement (arm1 vs arm6 vs arm7 profiles-off ablation) reported to rpg-planner.

## Gates
mypy, ratchet, import-linter (17 kept), mechanism completeness pin, scoped unit sweeps, CI matrix sweep.
