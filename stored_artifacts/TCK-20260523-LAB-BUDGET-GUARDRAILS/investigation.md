# Investigation - Resource, Storage, and Runtime Guardrails (Milestone 82)

## Context
Scenario Lab execution is highly parameterizable. High seed numbers (e.g. 50+ seeds) combined with many ticks (e.g. 1000+ ticks) and complex worlds containing dozens of entities could generate millions of ticks and hundreds of megabytes of event logs. In CI profiles, this must be aggressively capped to avoid exhausting worker nodes. In local profiles, developers need flexible but safe warnings.

## Findings
- `ExperimentBudgetsSpec` originally only defined `max_runtime_minutes` and `max_total_artifact_mb`.
- Custom matrix properties (such as run matrix count or accumulated ticks) were not validated.
- `ScenarioLabOrchestrator.run_lab` originally created directory structures *before* verifying any simulation properties. If a simulation execution was unsafe, the directories were already left behind as clutter.

## Design Decision
- Add limits check *pre-flight* right after loading schemas.
- Implement strict failure mapping so that CI blocks oversized sweeps immediately, while local devs can confirm warnings via CLI options.
