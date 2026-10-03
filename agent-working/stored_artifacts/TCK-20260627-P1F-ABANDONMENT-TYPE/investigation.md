# Investigation: TCK-20260627-P1F-ABANDONMENT-TYPE

## Source Analysis

### Primary File
`src/domains/commitment/abandonment.py` — single class `AbandonmentEvaluator`, single static method
`evaluate_abandonment(hp, max_hp, is_party_in_combat, is_greed_driven) -> Dict[str, Any]`.

Returns three dict keys:
- `"is_betrayal"` (bool)
- `"penalty"` (float)
- `"reason"` (str: `"survival"` | `"greedy_desertion"` | `"voluntary_quit"`)

### Callers (production only)

| File | Access pattern |
|---|---|
| `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py` | `result["is_betrayal"]`, `result["penalty"]` |
| `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` | `result["is_betrayal"]` |

`reviews/src_export.py` and `reviews/test_export.py` are generated read-only exports — not updated manually.

### Category Mapping

| Condition | Category | is_betrayal | penalty |
|---|---|---|---|
| `hp_ratio < 0.2` | `SURVIVAL` | False | 0.0 |
| `is_party_in_combat and is_greed_driven` | `GREEDY_DESERTION` | True | 0.8 |
| else | `VOLUNTARY_QUIT` | False | 0.2 |

The `reason` string in the current dict maps 1-to-1 to the `AbandonmentCategory` enum values.

## Parity / Doc Check

- `docs/parity_ledger/social_narrative.yaml` — no existing entry for `AbandonmentEvaluator` return type.
- Abandonment entries in ledger are about party dissolution and contract breach outcomes, not type safety of this evaluator.
- A new parity entry `SOC-ABAND-TYPE-01` will be added.

## No Prior Work Found

Working log has no prior abandonment typing ticket. This is first time this specific refactor is being done.

## No Conflicts

No architectural mismatches. Change is contained to one source module and two test files.
