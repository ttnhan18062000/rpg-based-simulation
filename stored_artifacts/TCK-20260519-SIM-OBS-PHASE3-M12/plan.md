# Implementation Plan - Milestone 12: Rule Engine Infrastructure with Core Rules

## Proposed Architecture

1. **`AnomalyRecord`**:
   - Pydantic model encapsulating full anomaly metadata:
     * `anomaly_id`: str (uuid.hex)
     * `rule_id`: str
     * `severity`: str ("WARNING", "ERROR", "CRITICAL")
     * `domain`: str (e.g. "combat", "movement", "economy", "quest", "system")
     * `message`: str
     * `tick_start`: int
     * `tick_end`: int
     * `affected_entity_ids`: List[int]
     * `affected_resource_ids`: List[str]
     * `affected_region_ids`: List[str]
     * `affected_quest_ids`: List[str]
     * `evidence`: Dict[str, Any]
     * `suggested_causes`: List[str]

2. **`RuleResult` and `RuleStatus`**:
   - `RuleStatus` enum: `PASSED`, `FAILED`, `SKIPPED_MISSING_SIGNAL`, `SKIPPED_SCENARIO_TYPE`, `ERROR`.
   - `RuleResult` model containing the rule ID, evaluation status, detected anomalies, and error message.

3. **`BaseRule` Interface**:
   - Abstract class with standard metadata and lifecycle methods:
     * `rule_id`: str
     * `required_signals`: List[str]
     * `valid_scenarios`: List[str] (empty list means all)
     * `evaluate(self, context: AnalysisContext, config: RuleConfig) -> RuleResult`

4. **Five Core Rules**:
   - `HardLawViolationDetected`:
     * Checks `hard_law_violations` or event stream for invariant breaches.
   - `NavigationStuckBasic`:
     * Evaluates agent freeze lengths based on movement events.
   - `QuestStalledBasic`:
     * Analyzes quest lifecycle durations.
   - `ResourceProductionZero`:
     * Looks at `metric_windows.gold_total_avg` or harvest events. Returns `SKIPPED_MISSING_SIGNAL` if required indicators are not active/present in light or off modes.
   - `GovernorDegradedTooLong`:
     * Monitors `metric_windows.governor_mode_dominant` (survival/degraded) or mode changes. Returns `SKIPPED_MISSING_SIGNAL` if metric windows are missing.

5. **`RuleEngine` and Config Loader**:
   - Loads optional `config/observability/rules_core.json` overrides.
   - Runs enabled rules deterministically, sorting output anomalies by rule ID and tick.
