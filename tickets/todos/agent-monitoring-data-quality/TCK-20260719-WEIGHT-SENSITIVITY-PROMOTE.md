---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE
phase: open
date: 2026-07-19
tags: []
---

# TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE

## Title
Promote validate_rank_order.py into tools/agent-monitoring/ as a tested CLI

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants experiments/cost_proxy_calibration/validate_rank_order.py moved into tools/agent-monitoring/, with its two compared weight sets parameterized as CLI args instead of hardcoded, test coverage added, and documentation added to docs/agent-monitoring/README.md marking it as the required check before ever proposing a cost_proxy.py weight change.

## Scope
- New module under tools/agent-monitoring/ (e.g. weight_sensitivity_check.py, matching the sibling *_check.py naming convention of epic_scope_orphan_check.py/epic_staleness_check.py/status_drift_check.py)
- Refactor validate_rank_order.py's main() to separate pure computation (accepts tool_rows + a weights dict, returns a testable report object) from file I/O and printing
- CLI accepts two weight sets as arguments instead of hardcoded W_SHIPPED/W_FITC dicts; default invocation (no args) compares against currently-shipped cost_proxy.py weights with no baked-in second comparand, or errors clearly
- New unit tests in tests/tools/test_weight_sensitivity_check.py mirroring test_cost_proxy.py's fixture-dict style, no subprocess/real-file dependency
- docs/agent-monitoring/README.md gains a line identifying the promoted tool's path and stating it is the required check before proposing any cost_proxy.py weight change
- New Makefile target following the agent-monitoring-validate/agent-monitoring-query pattern
- Update RESULTS.md's tool-path references (lines 19, 115) to the new location

## Out of Scope
- Endorsing or shipping Fit C weights — both weight sets remain purely CLI-supplied comparands, never a baked-in default
- Any change to cost_proxy.py's shipped W_BASH/W_AGENT/W_EDIT constants
- C5's docstring/README calibration-provenance note — separate concern; coordinate sequencing with C5 if both land close together to avoid conflicting README edits

## Acceptance Criteria
- [ ] New module under tools/agent-monitoring/ exports a pure function (accepts tool_rows + a weights dict, returns a testable report object), matching the *_check.py naming convention
- [ ] tests/tools/test_weight_sensitivity_check.py covers the pure function with fixture-dict-style tests, no subprocess/real-file dependency
- [ ] CLI accepts two weight sets as arguments instead of hardcoded dicts; default invocation reads real agent-monitoring/tools.jsonl and events.jsonl (no fixture substitution required for normal use) and compares against currently-shipped cost_proxy.py weights, never silently reintroducing a hardcoded Fit C default
- [ ] docs/agent-monitoring/README.md documents the promoted tool's path and states it is the required check before proposing any cost_proxy.py weight change
- [ ] New Makefile target added following the agent-monitoring-validate/agent-monitoring-query pattern
- [ ] experiments/cost_proxy_calibration/RESULTS.md's tool-path references (lines 19, 115) updated to the new location

## Related Tickets
- TCK-20260708-AGENT-COST-OBSERVABILITY
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

## Related Docs
- docs/agent-monitoring/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/cost_proxy_calibration/validate_rank_order.py
- expected: tools/agent-monitoring/weight_sensitivity_check.py
- expected: tests/tools/test_weight_sensitivity_check.py
- tools/agent-monitoring/cost_proxy.py
- tools/agent-monitoring/query.py
- tools/agent-monitoring/validate.py
- tests/tools/test_cost_proxy.py
- tests/tools/test_validate_agent_monitoring.py
- docs/agent-monitoring/README.md
- Makefile
- experiments/cost_proxy_calibration/RESULTS.md

## Assumptions / Open Questions
- CLI serialization format for two weight sets (key=value pairs vs JSON string vs multiple flags) is genuinely new — no existing tools/agent-monitoring/*.py CLI takes a dict-shaped argument; needs an explicit Plan-phase decision
- Whether experiments/cost_proxy_calibration/validate_rank_order.py is deleted after promotion or left as a thin pointer — no repo precedent found either way; Plan-phase decision
- C4 and C5 both touch docs/agent-monitoring/README.md's same area — sequence/coordinate to avoid conflicting edits if both land close together
- `layer: observability` chosen as the best registry fit (agent monitoring, dashboards, event bus, telemetry) since this ticket promotes an agent-monitoring tool; no better match found in `docs/guidelines/layer_registry.jsonl`

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
