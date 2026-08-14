---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE
phase: done
date: 2026-07-19
tags: []
---

# TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE

## Title
Promote validate_rank_order.py into tools/agent-monitoring/ as a tested CLI

## Status
DONE

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
New module `tools/agent-monitoring/weight_sensitivity_check.py` — pure function
`compute_weight_sensitivity_report(tool_rows_by_group, phase_of, agent_of, baseline_weights,
candidate_weights)` (no file I/O), plus `_load_tool_rows_and_events()` as the only file-reading
function, matching this repo's established separation-of-computation-from-I/O convention. Two
Plan-phase decisions the ticket's own Assumptions section required, made and documented: (1) CLI
weight-set serialization is a JSON-string flag (`--candidate-weights`/`--baseline-weights`),
matching the existing `--data '<json>'` convention already used throughout
`tools/agent-monitoring/*.py`; (2) the old experiment script was deleted after promotion (not left
as a thin pointer) — no repo precedent found requiring either choice, and the promoted module is a
strict superset of the old script's behavior.

`SHIPPED_WEIGHTS` reads `cost_proxy.py`'s live `W_BASH`/`W_AGENT`/`W_EDIT` constants directly
(import, never a second hardcoded literal copy) as the default baseline comparand.
`--candidate-weights` has no default, ever, and no baked-in Fit C literal is shipped anywhere in
this module — every invocation must explicitly supply a candidate, exactly matching the ticket's
Out of Scope statement. Spearman rank correlation reimplemented in pure Python (closed-form
tie-free formula: `1 - 6*sum(d²) / (n*(n²-1))`) rather than reusing the original experiment
script's `import numpy as np` — `tools/agent-monitoring/*.py` scripts run via bare `python3`, not
guaranteed a numpy-equipped interpreter, and no other module in this directory has an external
dependency.

`_score_with_weights()` is a deliberate, separate implementation from
`cost_proxy.py::compute_cost_proxy_score()` — that function hardcodes the module-level shipped
constants by design (the real production write path, wired into `record_events.py` by the sibling
`TCK-20260719-COST-PROXY-WRITE-PATH` ticket earlier in this same batch); this tool needs to score
the same tool-row group under two *arbitrary* CLI-supplied weight sets, a genuinely different
contract, not a duplicate to merge.

`docs/agent-monitoring/README.md`: new paragraph placed immediately after
`TCK-20260719-COST-PROXY-CALIBRATION-NOTE`'s existing calibration-finding note (confirmed no edit
conflict — verified that note ends before the Navigation section) documenting the promoted tool's
path and its "required check before proposing any weight change" role, plus a Quick Start example.
New `Makefile` target `agent-monitoring-weight-check`, `$(ARGS)` passthrough mirroring
`agent-monitoring-query`'s existing shape — not added to `.PHONY` (confirmed via grep that no
other `agent-monitoring-*` target is listed there either, so this follows the existing, if
unusual, precedent rather than introducing a new one).

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering, self-flagged per this
project's traceability rule**: a session-limit stall interrupted the original pipeline run
partway through — real, correct implementation (`weight_sensitivity_check.py`,
`test_weight_sensitivity_check.py`, 10/10 tests passing) landed on disk before
`staging_artifacts/` or any monitoring records existed for this run. Staging artifacts were
written retroactively (describing the real, already-verified implementation, not a prospective
plan for unwritten code) and monitoring events for Scope/Investigate/Plan were backfilled — same
pattern as `TCK-20260719-AGENT-ROLE-GLOSSARY` earlier in this same session.

## Test Summary
- `python3 -m pytest tests/tools/test_weight_sensitivity_check.py -q` — 10/10 passing.
- `python3 -m pytest tests/tools/test_weight_sensitivity_check.py tests/tools/test_cost_proxy.py tests/tools/test_validate_agent_monitoring.py -q` — 26/26 passing.
- `python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard or generate_retro or validate_agent or weight_sensitivity"` — 179/179 passing.
- Manual CLI verification against the real live corpus (Fit C candidate weights) — output
  consistent with the original experiment's findings. All 3 bad-input paths verified: missing
  `--candidate-weights` → argparse exit 2; invalid JSON → clear `ERROR:` + exit 1; missing
  required keys → clear `ERROR:` + exit 1. `make agent-monitoring-weight-check ARGS='...'`
  verified working end to end.

## Files Changed
- tools/agent-monitoring/weight_sensitivity_check.py (new)
- tests/tools/test_weight_sensitivity_check.py (new)
- experiments/cost_proxy_calibration/validate_rank_order.py (deleted, promoted)
- experiments/cost_proxy_calibration/RESULTS.md (2 references updated to new location)
- docs/agent-monitoring/README.md (new paragraph + Quick Start line)
- Makefile (new `agent-monitoring-weight-check` target)
- docs/parity_ledger/infrastructure.yaml (new entry INFRA-285)

## Completion Summary
`experiments/cost_proxy_calibration/validate_rank_order.py` promoted into
`tools/agent-monitoring/weight_sensitivity_check.py` — a real, tested CLI tool comparing
`cost_proxy_score` rank order under two weight sets, with the currently-shipped weights read
directly from `cost_proxy.py` as the default baseline and the candidate always required
explicitly on the CLI (never a baked-in Fit C default). This is the last of the 5 sibling tickets
in the `agent-monitoring-data-quality` batch, closing out the epic. Documented as the required
check before proposing any future `cost_proxy.py` weight change, with a new Makefile target and
README section. Verified working end to end against the real production corpus, consistent with
the original experiment's findings.
