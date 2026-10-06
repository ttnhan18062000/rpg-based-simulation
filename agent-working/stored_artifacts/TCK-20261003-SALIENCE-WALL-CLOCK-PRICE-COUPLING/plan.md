---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING
artifact_type: plan
tags: [determinism, economy, engine]
---

# Plan

Owner decision 2026-10-04 supersedes the ticket's "work-debt term stays": drop `global_salience` and the buy-price multiplier entirely.

1. `src/engine/kernel.py`: delete the `debt_ratio` / `compute_ratio` / `global_salience` computation and the `pressure_signals_set=` write.
2. `src/systems/economy_systems/economy.py`: `DynamicPriceService.calculate_buy_price(base_value)` returns `max(1, int(base_value))`; delete the cap constant and the state/mode parameters. Update the call in `src/town/shop.py`.
3. Tests: new `tests/unit/resource/test_buy_price_independent_of_host_timing.py` (`audit_mode=False`, faked `time.perf_counter_ns`; must fail on the pre-fix tree); rewrite the two tests in `test_economy_hardening.py` that pinned the multiplier.
4. Docs in the same change: divergence 2.75, Bible 03 §4, `resource_governor_contract.md`, `resource_conservation_contract.md` pricing formula, PERF-D1 amendment A1 status, `deterministic_execution.md` (input 4 closed, PERF-D5 coverage finding), `wall_clock_inventory.md` (regenerated with the tool), `compliance/checklist.md` ECON-095, parity entry TOWN-196.
5. Out of scope, kept: proof digest unchanged (finding only), `audit_mode` unchanged, no price rebalancing.
