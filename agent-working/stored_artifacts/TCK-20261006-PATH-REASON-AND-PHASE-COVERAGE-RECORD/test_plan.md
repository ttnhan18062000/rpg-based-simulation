---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test plan
Unit: `build_records` for standard, hotfix and epic; enum validators; plan edit changes the result (tmp yaml); unreadable plan gives `None`. CLI in a scratch git repo: reason written, no-flag hint count and exit code, bad value and `other` without note write nothing. Source-level fixture for the pipeline (the script cannot run here): run write carries `pipeline_default`, every skip site carries a reason.

## Proof Plan
- level: unit
- proof kind: pytest
- oracle source: records written to a scratch cwd and read back
- expected effect: omitted phases follow the plan file; bad values exit non-zero with nothing written
- selected commands: `pytest tests/tools/test_path_reason_and_phase_coverage.py tests/tools/test_record_hand_orchestrated_closure.py tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py`
