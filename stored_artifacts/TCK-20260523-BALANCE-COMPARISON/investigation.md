---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-BALANCE-COMPARISON
artifact_type: investigation
tags: [balance, comparison]
---

# Balance Comparison Engine - Investigation

## 1. Goal and Core Mechanics
The Balance Comparison Engine takes performance/observability metrics from a baseline variant and a mutated variant, performs differential analysis, aggregates metamorphic rule outcomes, and produces a structured scorecard of the overall balance shift.

---

## 2. Classification Rules and Logic

We define a deterministic, multi-dimensional classification model based on the metric shifts:

### A. Crucial Metrics and Direction
1. **Health Score** (`health_score`): Higher is better.
2. **Hard Law Violations** (`hard_law_violations` / `hard_law_violation_count`): Lower is better.
3. **Critical Anomalies** (`critical_anomalies` / `critical_count` / `critical_anomalies_count`): Lower is better.
4. **Stuck Ratio** (`stuck_ratio` / `stuck_entity_ratio`): Lower is better.
5. **Resource Production** (`resource_production` / `resource_production_rate`): Higher is better.
6. **Quest Completion** (`quest_completion` / `quest_completion_rate`): Higher is better.
7. **Combat Resolution** (`combat_resolution`): Higher is better (or custom direction).
8. **Runtime Performance** (`runtime_performance` / `execution_time_seconds`): Lower is better.
9. **Memory Usage** (`memory_usage` / `memory_usage_mb`): Lower is better.
10. **Event Volume** (`event_volume`): Lower/stable is better.

### B. Classification Protocol
For any comparison:
1. **Missing Data Gate**: If baseline or compared metrics are missing completely or lack essential metrics (like `health_score`), class is `INSUFFICIENT_DATA`.
2. **Hard Regression Gate**: If compared variant has `hard_law_violations > 0` (or greater than baseline), class is strictly `REGRESSED`.
3. **Metamorphic Failure Gate**: If any associated metamorphic rule failed (`status="FAILED"`), class is `REGRESSED`.
4. **Differential Shift Count**:
   We compare all present dimensions:
   - For each dimension where compared is better than baseline: `better += 1`
   - For each dimension where compared is worse than baseline: `worse += 1`
   - For each dimension where they are equal: `stable += 1`
5. **Final Class Decision**:
   - If `worse > 0` and `better > 0`: `MIXED`
   - If `worse > 0` and `better == 0`: `REGRESSED`
   - If `better > 0` and `worse == 0`: `IMPROVED`
   - If `better == 0` and `worse == 0`: `UNCHANGED`

---

## 3. Scientific Humility in Explanation
To satisfy the "does not claim root cause" requirement, the engine's text explanation must use correlative phrasing:
- **Correlative Phrasing**: Use terms like "is associated with", "correlates with", "co-occurs with", "indicates a correlation".
- **Avoid**: Words indicating absolute causality such as "caused by", "proves that", "is the root cause of", "directly resulted from".
- **Validation**: We will add a parser check in the engine to guarantee no causal claim strings are printed in the explanation, ensuring absolute compliance with scientific humility guidelines.
