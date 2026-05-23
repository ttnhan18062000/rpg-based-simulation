# Balance Comparison Engine - Implementation Plan

We will implement **Milestone 88 — Balance Comparison Engine** by introducing modular differential metric comparison, automated scorecard reporting, and rigorous humility constraints.

---

## Proposed Changes

### Lab Component

#### [NEW] [comparison.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/comparison.py)
Create a new domain file containing:
1. `BalanceComparisonReport`: Pydantic model carrying the scorecard and data:
   - `status`: `"IMPROVED"` | `"REGRESSED"` | `"UNCHANGED"` | `"MIXED"` | `"INSUFFICIENT_DATA"`
   - `evidence`: Dictionary mapping metric details `{metric_name: {"baseline": val, "compared": val, "shift": float}}`
   - `explanation`: Correlative explanation string
2. `BalanceComparisonEngine`: Main logic evaluating metric comparisons, aggregating metamorphic results, and writing files (`balance_comparison.json`, `balance_comparison.md`).

#### [MODIFY] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/__init__.py)
- Import and export `BalanceComparisonReport` and `BalanceComparisonEngine` in the package API.

---

## Verification Plan

### Automated Tests
We will add:
- `tests/unit/lab/test_balance_comparison_engine.py`

Run command:
```bash
pytest tests/unit/lab/test_balance_comparison_engine.py -v
```
