---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E32A-RENAME-RUNNER
phase: done
date: 2026-06-20
tags: [campaign-runtime, rename, refactor, phase-3]
---

# TCK-20260619-E32A-RENAME-RUNNER

## Title
Epic 3.2A · Rename CampaignRunner → SimulationAnalysisRunner

## Status
DONE

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
- `grep -rn "CampaignRunner" src/ tests/` returns zero results ✓
- All existing tests pass after rename (no behavior change) ✓
- `SimulationAnalysisRunner` importable from original module path ✓

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (parent epic)
- TCK-20260619-E32B-CAMPAIGN-STATE (blocked on this)

## Test Summary
6 tests passed (tests/integration/campaigns/ × 5, tests/perf/test_phase9_campaign_semantic_budget.py × 1).

## Files Changed
- `src/domains/campaigns/runner.py` — renamed class `CampaignRunner` → `SimulationAnalysisRunner`; updated module docstring
- `tests/integration/campaigns/test_phase9_campaign_runner.py` — updated import + 3 instantiations
- `tests/integration/campaigns/test_phase9_life_arc_campaigns.py` — updated import + 2 instantiations
- `tests/perf/test_phase9_campaign_semantic_budget.py` — updated import + 1 instantiation
- `docs/simulation/domains/campaigns_contract.md` — updated lifecycle diagram, running state description, determinism contract, and boundary table

## Completion Summary
Mechanical rename only — no behavior change. `CampaignRunner` is now `SimulationAnalysisRunner` across all src, test, and contract-doc references. The `campaign` namespace is now free for `CampaignOrchestrator` (E32C). `grep -rn "CampaignRunner" src/ tests/` returns zero results. 6/6 tests pass.
