# Investigation - Milestone 12: Rule Engine Infrastructure with Core Rules

## Current Capabilities
- The previous implementation uses the `AnomalyRule` and `Anomaly` classes.
- Standard rules like `NavigationStuckRule` and `QuestStalledRule` evaluate events but do not have formal signal requirement declaration, status tracking (skipped, failed, passed), target scenarios gating, or robust data configuration support.

## Gap Analysis
- There is no unified `RuleEngine` that takes `AnalysisContext` and executes rules in a highly deterministic way with standard skipped status signals.
- `ResourceProductionZero` and `GovernorDegradedTooLong` rules require scanning `metric_windows.jsonl` data structures, which was not previously modeled inside individual rules.
- A central JSON rules config mapping threshold overrides does not exist yet.
