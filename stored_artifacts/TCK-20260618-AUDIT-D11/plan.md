# D11 Audit Plan

## Approach
Measure method. Import graph via grep for each top-level src/ directory.
Characterise each orphan cluster by V1 pattern and V2 supersession.

## Data Sources
- grep import surveys per top-level directory
- src/ file enumeration for naming/marker patterns
- D09/D12 prior findings for V1→V2 mapping
- src/ai/goals/scorers.py sample to confirm GoalScorer pattern

## Output
- docs/audits/D11_dead_code.md
