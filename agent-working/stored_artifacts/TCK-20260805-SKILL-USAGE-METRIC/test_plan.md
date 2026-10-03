---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-SKILL-USAGE-METRIC
artifact_type: test_plan
tags: [skills, agent-monitoring]
---

# Test Plan — TCK-20260805-SKILL-USAGE-METRIC

## Normal Flow
- Real corpus run: per-skill counts match an independently-derived regex pass over the same real
  `tools.jsonl`, total Skill-tool count matches, top skill is `implement-ticket` (or whichever is
  genuinely highest at run time — asserted via equality with the independent count, not a
  hardcoded name/number).

## Edge Cases
- A `Skill`-tool record with an `input_summary` that doesn't match the regex is counted under
  `unparseable`, not silently dropped and not crashing.
- `run_id=None` records bucket under `"unattributed"`, not a `None` dict key (would break
  `json.dumps(sort_keys=True)`).
- Zero `Skill` tool records in the input → empty counts dict, not an error.

## Failure Modes
- Malformed `input_summary` (missing `skill` key entirely, or a differently-shaped dict-repr
  string) is handled by the `unparseable` bucket, not an uncaught exception.

## Regression-Prone Paths
- `generate_retro.py`'s own test suite re-run unchanged after this ticket lands (confirms
  `tag_breakdown_skill` untouched).
- Zero-mutation test against real `agent-monitoring/` (this is a read-only tool).
- Source-text guard: `json.loads` never appears applied to `input_summary` anywhere in the new
  module.
