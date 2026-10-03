# Plan: TCK-20260627-P1F-ABANDONMENT-TYPE

## Tier: hotfix

## Unresolved Questions
None.

## Changes

### 1. `src/domains/commitment/abandonment.py`
- Add `from enum import Enum` and `from dataclasses import dataclass`
- Define `AbandonmentCategory(str, Enum)` with members `SURVIVAL`, `GREEDY_DESERTION`, `VOLUNTARY_QUIT`
- Define `AbandonmentClassification` frozen dataclass: `is_betrayal: bool`, `penalty: float`, `category: AbandonmentCategory`
- Change `evaluate_abandonment()` return annotation from `Dict[str, Any]` to `AbandonmentClassification`
- Replace each `return {…}` with `return AbandonmentClassification(…)`
- Remove `from typing import Dict, Any` (no longer needed)

### 2. `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py`
- Add imports: `AbandonmentCategory`, `AbandonmentClassification`
- Change `result["is_betrayal"]` → `result.is_betrayal`
- Change `result["penalty"]` → `result.penalty`
- Add new test `test_evaluate_abandonment_returns_typed_classification` covering all three branches with `isinstance` and `.category` assertions

### 3. `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`
- Change `eval_res["is_betrayal"]` → `eval_res.is_betrayal`

### 4. `docs/parity_ledger/social_narrative.yaml`
- Append new entry `SOC-ABAND-TYPE-01` for typed return contract.

## Deviations
None.
