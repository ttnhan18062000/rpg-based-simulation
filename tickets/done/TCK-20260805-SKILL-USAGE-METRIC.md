---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-SKILL-USAGE-METRIC
phase: done
date: 2026-08-05
tags: [skills, agent-monitoring]
---

# TCK-20260805-SKILL-USAGE-METRIC

## Title
Add a real agent-monitoring metric for raw Skill-tool-invocation counts by skill name

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child ticket #8 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. Confirmed via grep across
`tools/agent-monitoring/*.py` and `tools/*.py`: no existing script or `generate_retro.py` section
filters on `tool == 'Skill'` — this question currently requires ad hoc regex against raw
`tools.jsonl` (as this session did to produce the 71/66/26/11/9/5/3 usage counts). What already
exists (`TCK-20260708-RETRO-TAG-BREAKDOWN`) is a *different* metric: tag-based gate-hit breakdown,
not per-skill invocation counts — it cannot answer "was `/api-design-principles` ever actually
invoked" for a tag with no gate.

## Scope
- Add a new function following `tools/agent-monitoring/retrieval_baseline_metrics.py`'s exact
  pattern: a frozen constant, a `build_*_section()` function with a mandatory `derivation` string,
  per-run grouping via `defaultdict(int)`, `"unattributed"` bucket for `None` run_ids.
- `tools.jsonl`'s `input_summary` field is a Python-dict-repr string, not JSON — use regex
  extraction (`re.search(r"'skill':\s*'([^']*)'", input_summary)`), never `json.loads` on that
  sub-field (confirmed by direct inspection this session).
- Decide (Plan phase): a new `generate_retro.py` section (recurring, alongside the existing Tag
  Breakdown sections) vs. a new standalone script (one-off/periodic, mirroring
  `retrieval_baseline_metrics.py`'s own shape) — both acceptable, Plan picks one with reasoning.
- Output confined to `agent-monitoring/` (via `generate_retro.py`'s `RETRO_DIR` or a dedicated
  script's stdout/`--output`) — never `docs/`, `data/`, or `config/`, which serve unrelated
  concerns in this repo.

## Out of Scope
- Rebuilding or modifying `generate_retro.py`'s existing `## Tag Breakdown` sections — this metric
  must be additive, in its own clearly-distinguished section heading and `derivation` string.

## Acceptance Criteria
- [x] New metric function (`build_skill_usage_section`) exists, correctly counts real `Skill`
      tool invocations by name from live `tools.jsonl` — 207 total, 71 implement-ticket / 67
      graphify / 26 create-tickets / 12 implement-epic / 9 agent-monitoring-retro / 5 simq-audit
      / ... (drifted from the ticket's originally-cited 71/66/26/11/9/5/3 as expected — corpus
      grows every session; see Implementation Notes).
- [x] Uses regex extraction (`_SKILL_NAME_RE`) on `input_summary`, never `json.loads` — AST-guarded.
- [x] Output confined to `agent-monitoring/` — no hardcoded write path; `--output` is caller-supplied.
- [x] Does not duplicate or modify `RETRO-TAG-BREAKDOWN`'s existing sections — `generate_retro.py`
      untouched, its 121-test suite re-run clean.
- [x] Test coverage: live-corpus test independently re-derives counts via a separate regex pass
      (not a frozen hardcoded fixture — see Implementation Notes on why that would be brittle) and
      asserts equality with the function's real output.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260708-RETRO-TAG-BREAKDOWN (adjacent existing metric, do not duplicate)
- TCK-20260728-RETRIEVAL-BASELINE-METRICS (the pattern this ticket's tool follows)

## Related Docs
None new.

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (pattern reference)
- `tools/agent-monitoring/generate_retro.py` (possible integration point)
- `agent-monitoring/tools.jsonl` (read-only data source)

## Assumptions / Open Questions
Whether this becomes a `generate_retro.py` section or a standalone script — Plan phase decides.

## Implementation Notes
Built `tools/agent-monitoring/skill_usage_metric.py`, following `retrieval_baseline_metrics.py`'s
house pattern (frozen regex constant with load-bearing comment, `build_skill_usage_section()`
returning a `derivation` string, `unattributed` bucketing, `unparseable` counted not dropped).
Standalone script decision, same reasoning as `SECURITY-GATE-FIRING-MONITOR`: one-off/periodic
tool, not part of the weekly retro cadence.

Real ground-truth independently derived (a separate ad hoc regex pass, before writing the module)
found 207 total `Skill` invocations, top counts: 71 implement-ticket / 67 graphify / 26
create-tickets / 12 implement-epic / 9 agent-monitoring-retro / 5 simq-audit / 3 each
dataviz/brainstorming/claude-in-chrome / 2 each update-config/fewer-permission-prompts/run / 1
each artifact-design/claude-api. This has already drifted from the ticket's own originally-cited
71/66/26/11/9/5/3 figures (graphify 66→67, implement-epic 11→12) — expected, since the corpus
grows every session. Rather than hardcode a fixture that would immediately go stale, the live-
corpus test independently re-derives the same counts via its own separate regex implementation
and asserts equality with the function's real output — catches real logic bugs without being
brittle against corpus growth.

Added a "Skill Usage Metric" section to `docs/agent-monitoring/README.md`, mirroring the existing
Baseline Metrics Snapshot / Security Gate Firing Check sections' shape.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_skill_usage_metric.py` — 12 tests, all passing: 2 reuse-not-reimplement
guards (AST-checked imports, AST-checked absence of any `json.loads(...)` call — not a substring
check, since the module's own docstring legitimately mentions "json.loads" in prose explaining why
it's not used); 6 synthetic-fixture unit tests (basic counting, `None`/missing `run_id` bucketing,
unparseable handling, empty input, derivation string presence); 1 live-corpus test asserting
equality against an independently-derived regex pass; 1 CLI JSON-shape test; 1 zero-mutation test.
Regression check: `pytest tests/tools/ -k "generate_retro or retro or retrieval_baseline"` — 121
passed. `doc_staleness_check.py` → PASS. `clean_data_runs_early()` → PASS.
`expected_subsystems_for_files()` → `{}` — no parity entry needed.
`run_static_precheck('standard', ...)` — all 7 conditions PASS.

## Files Changed
- `tools/agent-monitoring/skill_usage_metric.py` (new) — the metric.
- `tests/tools/test_skill_usage_metric.py` (new) — 12 tests.
- `docs/agent-monitoring/README.md` — added "Skill Usage Metric" section.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Built a per-skill raw invocation-count tool that finally makes "was `/api-design-principles` ever
invoked" a direct query instead of ad hoc regex against raw `tools.jsonl` (exactly what this
session's own earlier skill-usage audit had to do manually). Real ground-truth counts independently
derived before implementation, confirmed by the function's real output, and by a genuinely separate
regex re-derivation in the test suite (not a frozen fixture, which would already be stale). No
duplication of `RETRO-TAG-BREAKDOWN`'s existing tag-driven aggregate — `generate_retro.py`
untouched. No known material gap.
