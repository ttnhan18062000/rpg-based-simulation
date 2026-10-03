---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE
artifact_type: test_plan
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE

## Existing tests to update (`tests/tools/test_generate_retro.py`)

1. `test_parity_write_safety_zero_violations_on_clean_fixture` — unaffected (no yaml write present
   at all, stays 0 under old and new logic). Verify it still passes unmodified.
2. `test_parity_write_safety_detects_edit_targeting_parity_ledger_yaml` — currently asserts a LONE
   yaml edit (no co-occurring build call) counts as a violation. Under the new semantics this must
   change: rename intent to "detects edit co-occurring with a same-run parity_index.py build call"
   and add a `parity_index.py build ...` Bash row with the same `run_id` so the test demonstrates
   the NEW real-risk-detection behavior, not the old lone-edit behavior.
3. `test_parity_write_safety_detects_build_targeting_real_repo_path` — unaffected, tests
   `_is_unsafe_parity_build_call` only, not touched by this rescope.
4. `test_tool_safety_function_never_crashes_on_malformed_rows` — unaffected (no yaml-write rows in
   its fixture).

## New tests to add

1. `test_parity_write_safety_lone_yaml_edit_no_longer_counts` — a `docs/parity_ledger/*.yaml` Edit
   with the SAME `run_id` as other rows but NO `parity_index.py build` call anywhere in that
   `run_id`'s tool history → `parity_ledger_yaml_write_count == 0`. This is the ticket's own core
   fix, must be directly tested.
2. `test_parity_write_safety_yaml_edit_and_build_different_run_ids_not_flagged` — a yaml edit under
   `run_id="A"` and a `parity_index.py build` call under `run_id="B"` → count stays 0 (co-occurrence
   is per-run, not global).
3. `test_parity_write_safety_help_call_does_not_count_as_build` — a yaml edit plus a
   `parity_index.py --help` call (no `build` subcommand) in the SAME run → count stays 0 (confirms
   the corrected narrow co-occurrence signal, not a broad filename-substring match — this exact
   case was found as a real corpus false-positive during Investigate).

## Real-corpus re-verification

`python3 tools/agent-monitoring/generate_retro.py --all` (not committed — matches
`TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`'s own precedent) must show
`parity_ledger_yaml_write_count == 0` corpus-wide, confirmed already via direct investigation
(121 yaml-write run_ids, 0 overlap with the 1 real build-call run_id).

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -q`
