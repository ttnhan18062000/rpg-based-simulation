---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32A-RENAME-RUNNER
phase: open
date: 2026-06-20
tags: [campaign-runtime, rename, refactor, phase-3]
---

# TCK-20260619-E32A-RENAME-RUNNER

## Title
Epic 3.2A · Rename CampaignRunner → SimulationAnalysisRunner

## Status
OPEN

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
`CampaignRunner` in `src/domains/campaigns/runner.py` is analysis-only but the "campaign" namespace is needed for the new `CampaignOrchestrator` (E32C). This ticket frees the namespace by renaming all usages.

**Blocks:** All other E32 child tickets (naming collision)

## Scope

1. Rename `class CampaignRunner` → `class SimulationAnalysisRunner` in `src/domains/campaigns/runner.py`
2. Find all import/usage sites: `grep -rn "CampaignRunner" src/ tests/ scripts/ docs/`
3. Update every reference — imports, type hints, doc strings, test names
4. Update `docs/simulation/domains/campaigns_contract.md` boundary table to use new name

## Acceptance Criteria
- `grep -rn "CampaignRunner" src/ tests/` returns zero results
- All existing tests pass after rename (no behavior change)
- `SimulationAnalysisRunner` importable from original module path

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (parent epic)
- TCK-20260619-E32B-CAMPAIGN-STATE (blocked on this)

## Test Summary
```bash
pytest tests/ -x -q -k "not slow"  # all must pass after rename
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
