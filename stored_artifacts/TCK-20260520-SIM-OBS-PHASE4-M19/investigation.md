# Investigation Notes - Minimal Balance Envelope Config

## Design Phase Analysis
- Analyzed integration of scenario-specific expectations with existing baseline stats.
- Discovered that comparing limits using multiplier multipliers (e.g. `max_multiplier_from_baseline`) requires multiplying against either recommended baseline thresholds or falling back to raw distribution mean values.
- Analyzed mapping between telemetry metrics and Rule Engine rule IDs. Created mapping table within the rules engine to translate metric keys (e.g. `stuck_ticks`) into rule names (e.g. `NavigationStuckBasic`).

## Refactoring Impacts
- CLI entrypoint requires filtering out non-string path arguments (e.g. MagicMock attributes in integration test runs). Resolved via type-checking.
- Rule Engine dynamically scales existing configurations non-destructively, preserving baseline fallback settings.
