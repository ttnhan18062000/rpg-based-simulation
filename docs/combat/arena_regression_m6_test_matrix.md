# Arena Regression Test Matrix (Milestone 6)

This document maps arena scenarios to exact automated regression checks.

## Harness Contract Tests
These tests verify the integrity of the arena runner itself.

| Test | Input | Expected Rule |
| --- | --- | --- |
| `test_determinism` | Scenario `1v1-01` | 3 runs with same seed must have byte-identical `ScenarioReport` |
| `test_stop_condition_wipe` | 1v1 fight to the death | Runner stops immediately when one entity `alive=False` |
| `test_stop_condition_timeout` | Non-aggressive entities | Runner stops at `max_ticks` |
| `test_metric_generation` | Completed run | JSON output contains `win_rate`, `avg_ttk`, `stall_rate` |

## Core Scenario Regression Tests
These tests assert behavioral patterns.

| Scenario Group | Focus | Regression Caught |
| --- | --- | --- |
| `Swarm (1vm)` | Efficiency of many vs one | Caught: Target selection loops or pathing congestion |
| `Kiting (1v1-02)` | Movement vs Range | Caught: Melee speed buffs breaking engagement distance |
| `Stall (All)` | Stalemate Detection | Caught: Entities stuck in targeting loops without damage |

## Balance Signal Tests
These are "smoke tests" for the simulation feel.

| Group | Threshold | Purpose |
| --- | --- | --- |
| `Engagement Resolution` | Mean TTK < 2000 ticks | Ensures combat is active and not an endless chase |
| `Role Performance` | Ranger Win Rate > Melee in Open | Validates the "Ranged beats Melee in kiting" design principle |
| `Group Density` | Clumping Factor < 0.3 | Validates that entities seek space and don't clump excessively |
