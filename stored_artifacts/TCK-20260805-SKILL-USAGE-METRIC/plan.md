---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-SKILL-USAGE-METRIC
artifact_type: plan
tags: [skills, agent-monitoring]
---

# Plan — TCK-20260805-SKILL-USAGE-METRIC

## New file: `tools/agent-monitoring/skill_usage_metric.py`
Follows `retrieval_baseline_metrics.py`'s exact house pattern:
- Frozen constant: `_SKILL_NAME_RE = re.compile(r"'skill':\s*'([^']*)'")` with a load-bearing
  comment (per the ticket's own explicit finding: `input_summary` is a Python-dict-repr string,
  never `json.loads`).
- `build_skill_usage_section(tools: list) -> dict` — filters `tool == 'Skill'`, extracts skill name
  via regex, counts per skill name and per run_id (`"unattributed"` bucket for `None` run_id, same
  convention as `build_search_count_section`), reports an `unparseable` count (regex miss) rather
  than silently dropping those records.
- `derivation` string documenting the extraction method and its `input_summary`-is-dict-repr basis.
- `main()` CLI: prints JSON to stdout, optional `--output` path (reuses `manifest._assert_safe_output_path`).
- Imports `load_jsonl`/`DEFAULT_TOOLS_FILE` from `generate_retro.py` by direct import, not
  reimplemented (same reuse pattern as `retrieval_baseline_metrics.py`).

## Tests: `tests/tools/test_skill_usage_metric.py`
- Synthetic-fixture unit tests: correct per-skill counting, `unattributed` bucketing, unparseable
  handling (a `Skill` record whose `input_summary` doesn't match the regex).
- Live-corpus test: independently re-derive counts via the test's own separate regex pass over the
  real `tools.jsonl` (not by calling the function twice) and assert equality with
  `build_skill_usage_section`'s real output — catches real bugs, not stale-fixture drift (see
  investigation.md's test-design note).
- Zero-mutation test (mirrors `retrieval_baseline_metrics.py`'s own `test_..._causes_zero_diff_on_real_corpus`).
- Reuse-not-reimplement guard (AST-checked imports of `load_jsonl`/`DEFAULT_TOOLS_FILE`).
- CLI test confirming stdout JSON shape and `--output` path safety.

## Output confinement
`main()` writes only to stdout or an explicit `--output` path under the caller's control — never
hardcodes a write into `docs/`, `data/`, or `config/`. If a caller wants a persisted snapshot, it's
their responsibility to pass `--output agent-monitoring/...` explicitly; this script never assumes
a destination.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (correctly counts real invocations) → live-corpus independent-re-derivation test.
- AC2 (regex, never `json.loads`) → source-text guard test (`json.loads` never called on
  `input_summary`).
- AC3 (output confined to `agent-monitoring/`) → no hardcoded write path in the script itself;
  `--output` is caller-supplied.
- AC4 (no duplication of RETRO-TAG-BREAKDOWN) → `generate_retro.py` untouched; its own tests
  re-run unchanged as a regression check.
- AC5 (test coverage against real counts) → live-corpus independent-re-derivation test, not a
  frozen hardcoded fixture (see investigation.md's note on why that would be brittle).
