---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY
date: 2026-09-24
tags: [delivery, hooks, process-improvement]
---

# Test Plan — TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY

`tests/tools/test_delivery_pre_push_advisory.py`, one test per Acceptance Criterion (AC1–AC9) as
detailed in plan.md's Tests section, using the `FakeRunner` pattern for Checks A/B and a real
throwaway git repo (via `tempfile.TemporaryDirectory` + real `git` subprocess calls) specifically
for Check C (AC6), since a faked-output fixture cannot prove the ancestor-vs-content distinction is
real — the exact failure mode AC6 warns against.

## Regression-prone paths
- `test_matcher_regex_against_measured_corpus_shapes`: the 4 shape categories measured in
  investigation.md (bare, `&&`, `;`, newline), embedded as a small fixture list, all match; the one
  confirmed false-positive (`grep` mentioning `git push` in a pattern string) does not match.
- `test_settings_json_new_hook_appended_at_end_not_inserted`: the new entry is at index 6, and
  indices 0–5 are byte-identical to their pre-change values.
- `test_settings_json_hooks_wiring_count_bumped`: `test_existing_hook_writers_untouched`'s own
  assertion now reads `== 7`.
- `test_index_pinning_tests_still_pass`: run `tests/tools/test_bash_secret_scan_hook.py` and
  `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` directly, confirm unaffected.
- `test_detached_head_does_not_traceback`: a fixture simulating a failed `git` call (non-zero exit,
  as a detached HEAD or missing `origin/main` ref would produce) degrades that check to no finding,
  never raises.

## Full regression check
`pytest tests/tools/ -m "not slow"` after the new file and the two touched files pass in isolation.

## Recorded in `## Test Summary` once run
Exact commands and pass/fail counts, including confirmation the two index-pinning tests still pass.
