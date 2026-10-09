---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02
artifact_type: test_plan
tags: [economy, resource, legality]
---

# test_plan — TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02

## Tests
tests/unit/world/test_sell_is_a_chosen_act.py, tests/unit/world/test_building_services_land_with_their_action.py, tests/unit/kernel/test_building_services_executor_parity.py, tests/unit/world/test_shop_resolves_through_service_reach.py, tests/integration/optimization/test_force_full_scan_*.py

## Acceptance map
- [ ] SELL executes as a chosen act and is priced by `MarketSystem.calculate_price` (tests/unit/world/test_sell_is_a_chosen_act.py).
- [ ] Services land with their action (tests/unit/world/test_building_services_land_with_their_action.py) and the executor parity test passes.
- [ ] The shop phase still visits an entity under force_full_scan with an empty dirty set (rewritten integration test, with a default-scan control).

## Gates
mypy, ratchet, import-linter (17 kept), mechanism completeness pin, scoped unit sweeps, CI matrix sweep.
