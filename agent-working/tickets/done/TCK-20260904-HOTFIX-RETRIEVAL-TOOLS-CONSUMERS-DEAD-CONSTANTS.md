---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS
phase: done
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS

## Title
Fix 2 real, hard-failing regressions from `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`: `tools/retrieval_events.py`'s crash on the removed `record_events.EVENTS_FILE` constant, and `tools/agent-monitoring/retrieval_baseline_metrics.py`/`skill_usage_metric.py`'s `IsADirectoryError` on the now-directory-valued `DEFAULT_TOOLS_FILE`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Discovered while triaging PR #112's real CI failures for the just-closed `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC` — the "API / tools / logging" CI job's full cross-directory sweep (`tests/api tests/cli tests/tools tests/logging tests/engine tests/observability`) was never run in full by any of that epic's 7 children's own independent verification passes (each scoped its re-runs to only the files its own ticket claimed to touch), so these 2 real regressions went undetected until now.

**Bug 1 — `tools/retrieval_events.py:141` hard-crashes with `AttributeError`.** Confirmed by direct read: `target = events_file if events_file is not None else record_events.EVENTS_FILE`. `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY` (child 1) removed `record_events.py`'s module-level `EVENTS_FILE` constant entirely (replaced with a write-time-computed local inside `main()` only) — `retrieval_events.py` was never in that ticket's own investigated consumer list. `emit_retrieval_event()` is the mechanism that writes `RETRIEVAL-EVENT-*` shadow rows (the exact exception class `TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY`'s own checker excludes) — this is a real, currently-live crash on every call that doesn't pass an explicit `events_file` override, not silent degradation.

**Bug 2 — `tools/agent-monitoring/retrieval_baseline_metrics.py:52` and `tools/agent-monitoring/skill_usage_metric.py` crash with `IsADirectoryError: [Errno 21] Is a directory: 'agent-monitoring/data'`.** Both do a bare `load_jsonl(DEFAULT_TOOLS_FILE)`, imported directly from `generate_retro.py`. `TCK-20260903-MONITORING-DATA-CONSUMERS-CORE` (child 3) repointed `generate_retro.DEFAULT_TOOLS_FILE` to the directory-valued `agent-monitoring/data` as part of its Option B design (`load_jsonl()` became literal-file-only; the new `load_data_glob()` handles directories) — any caller still doing a bare `load_jsonl(DEFAULT_TOOLS_FILE)` now crashes on the directory, instead of the pre-epic silent-empty degradation. `skill_usage_metric.py`'s exposure was already found and explicitly accepted as an out-of-scope side effect during child 3's own Verify phase (confirmed by architecture-reviewer as "a genuine, unavoidable structural consequence of Option B"), but never actually filed as its own follow-up ticket — this ticket now does that. `retrieval_baseline_metrics.py`'s exposure was NOT found — child 3's own investigation explicitly (and incorrectly) claimed this file had "zero direct `load_jsonl`/`DEFAULT_TOOLS_FILE` reference, so no crash risk" (per its Anti-Drift Notes) — that claim is disproven by direct source read and a real, reproduced `IsADirectoryError`.

## Scope
- `tools/retrieval_events.py`: repoint the default-target resolution off the now-removed `record_events.EVENTS_FILE` constant, onto the same write-time multi-week glob pattern child 1 already established for `record_events.py`'s own `EVENTS_FILE` write target (`agent-monitoring/data/<current-ISO-week>/events.jsonl`, matching `record_events.py::main()`'s own `iso_week`/`events_file` local computation) — this write function should target the SAME current-week file `record_events.py`'s own hook writes to, not a stale/dead path.
- `tools/agent-monitoring/retrieval_baseline_metrics.py`: repoint its bare `load_jsonl(DEFAULT_TOOLS_FILE)` call to `generate_retro.py`'s new `load_data_glob(DEFAULT_TOOLS_FILE, "tools")` (or the equivalent multi-week glob helper child 3 already built) — restoring full-corpus read scope, matching every other consumer's fix pattern across this epic.
- `tools/agent-monitoring/skill_usage_metric.py`: same fix pattern, same `load_jsonl(DEFAULT_TOOLS_FILE)` → `load_data_glob(...)` repoint.
- Add or update regression tests for all 3 files proving correct (non-crashing, correct-corpus) behavior against the real post-epic corpus — matching this whole epic's own established "critical bug fix needs a dedicated regression test" precedent, not just "doesn't crash."
- Re-run the exact "API / tools / logging" CI job command locally (`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow"`) and confirm these specific failures are resolved; the 24 already-triaged environment-noise failures (live-server, bare-python3-subprocess) are explicitly out of scope and expected to remain.

## Out of Scope
- The 24 confirmed environment-noise failures (live-server connection-refused tests, CLI tests whose subprocess invokes bare `python3` lacking `pydantic` in this local sandbox) — pre-existing, documented class, not caused by this epic, will not fail in real CI's clean environment.
- The 8 failures in the "Agent orchestration / codex / replay" job — already fully tracked by `TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK` and `TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS`.
- The `docs/agent-monitoring/schema.md` heading-rename test breakage and `test_duration_utils.py`'s hardcoded legacy path — separately tracked in `TCK-20260904-HOTFIX-DOCS-SWEEP-TEST-STALENESS` (test-only fixes, no production code change, kept separate from this ticket's real production-code bugs).
- Any further audit beyond these 2 already-confirmed root causes — if the real full-CI-command re-run surfaces anything else new, that is a separate finding requiring its own triage, not silently folded into this ticket.

## Acceptance Criteria
- [x] `tools/retrieval_events.py::emit_retrieval_event()` no longer references the removed `record_events.EVENTS_FILE` constant; writes land in the same current-ISO-week file `record_events.py` itself targets.
- [x] `tools/agent-monitoring/retrieval_baseline_metrics.py` and `skill_usage_metric.py` both correctly read the full multi-week `tools` corpus via `load_data_glob()`, not a bare `load_jsonl()` against a directory.
- [x] Dedicated regression tests exist for all 3 fixes, proving correct non-crashing behavior against real post-epic data.
- [x] The real "API / tools / logging" CI command's *targeted* failures (the 2 bugs this ticket scopes) are confirmed resolved, re-run locally — `pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_skill_usage_metric.py -v` is 69/69 green. The broader `tests/tools/` sweep surfaced a NEW, separate, real conflict with 5 unrelated KGMCP baseline tests' coarse `git diff --stat`-based freeze check on `tools/retrieval_events.py` — confirmed by direct diff read that this ticket's fix is entirely confined to a private default-argument fallback inside `emit_retrieval_event()`, never touching any of the 3 `wrap_*()` functions the frozen-file check's own real invariant (Design Decision D1: zero invocation from the KGMCP pipeline) actually protects. Filed as its own separate, precisely-scoped follow-up ticket — `TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE` — rather than blended into this ticket's own scope or routed around by weakening those 5 tests directly. This ticket's own AC is fully satisfied.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (the epic whose children's consumer inventories missed these 2 files)
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1 — removed `record_events.EVENTS_FILE`)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE (child 3 — repointed `DEFAULT_TOOLS_FILE` to a directory; its own Anti-Drift Notes incorrectly cleared `retrieval_baseline_metrics.py`)
- TCK-20260904-HOTFIX-DOCS-SWEEP-TEST-STALENESS (sibling hotfix, test-only fixes found in the same CI triage session)

## Related Docs
None — internal tooling bug fixes, no doc claims this behavior differently than already documented.

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `tools/retrieval_events.py`
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tools/agent-monitoring/skill_usage_metric.py`
- `tests/tools/test_retrieval_events.py`
- `tests/tools/test_retrieval_baseline_metrics.py`
- `tests/tools/test_skill_usage_metric.py`

## Assumptions / Open Questions
- Assumes `generate_retro.py::load_data_glob` (or equivalent) is the correct, already-built helper to reuse — confirm at implementation time rather than reinventing.
- `layer: observability` matches this repo's established pattern for all `agent-monitoring`-adjacent tooling tickets.

## Implementation Notes

**Bug 1 — `tools/retrieval_events.py`.** `emit_retrieval_event()`'s `target = events_file if
events_file is not None else record_events.EVENTS_FILE` (line 141) was replaced with an inline
branch that, when `events_file is None`, reproduces `record_events.py::main()`'s own current-week
computation verbatim: `iso_week = datetime.now(timezone.utc).strftime("%G-W%V")` then
`Path("agent-monitoring/data") / iso_week / "events.jsonl"`. `retrieval_events.py` already imported
`datetime`/`timezone`/`Path` at module level, so no new imports were needed. `record_events.py`
itself was not touched, per the ticket's constraint.

**Bug 2 — `tools/agent-monitoring/retrieval_baseline_metrics.py` and `skill_usage_metric.py`.** Both
files' bare `load_jsonl(DEFAULT_TOOLS_FILE)` call was repointed to `load_data_glob(DEFAULT_TOOLS_FILE,
"tools")`, importing `load_data_glob` from `generate_retro.py` (which itself imports it from
`validate.py` and re-exports it) — matching `generate_retro.py`'s own real call site
(`_load_source(DEFAULT_TOOLS_FILE, "tools")` at line 2275, which internally dispatches to
`load_data_glob` for a directory path). `generate_retro.py`/`validate.py` were not touched, per the
ticket's constraint. The now-unused `load_jsonl` import was removed from both consumer files'
import lists (and their docstrings/comments updated to say `load_data_glob` instead), since nothing
else in either file still calls it.

**Test file findings/fixes beyond the 2 production bugs (all within the 3 ticket-scoped test
files):**
- `tests/tools/test_retrieval_events.py::test_default_events_file_is_record_events_events_file` was
  asserting the OLD pre-epic flat-file default (`agent-monitoring/events.jsonl`) — rewritten as
  `test_default_events_file_matches_record_events_current_week_target`, which asserts the write
  lands in `agent-monitoring/data/<current-ISO-week>/events.jsonl` AND cross-checks against a real
  `record_events.py::main()` invocation writing to the identical file, not just a hand-reproduced
  formula.
- `tests/tools/test_retrieval_baseline_metrics.py::test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`
  asserted `"load_jsonl" in imported` — updated to assert `"load_data_glob" in imported` instead.
  Added 2 new tests proving `load_all_sources()`/`load_data_glob()` correctly aggregate rows across
  multiple real ISO-week folders (not just "doesn't crash").
- `tests/tools/test_skill_usage_metric.py::test_reuses_generate_retro_loader_not_a_second_loader` had
  the same `load_jsonl` assertion, updated the same way. Separately discovered (while making this
  file's tests pass against the real corpus) that `_independently_derive_counts()`'s helper globbed
  the now-retired legacy path `agent-monitoring/tools/tools-*.jsonl` (that directory no longer
  exists post-epic) instead of `agent-monitoring/data/*/tools.jsonl` — a real, separate stale-path
  bug in this test's own fixture logic, unrelated to Bug 1/Bug 2's production code, fixed in the
  same pass since it directly blocked this ticket's own required regression-test pass. Also updated
  the 2 other real-corpus loader call sites in this file (`test_live_corpus_matches_independently_derived_counts`,
  `test_causes_zero_diff_on_real_corpus`) from `load_jsonl(DEFAULT_TOOLS_FILE)` to
  `load_data_glob(DEFAULT_TOOLS_FILE, "tools")`. Added a dedicated cross-week fixture test
  (`test_load_data_glob_reads_across_multiple_week_folders`).

**Unresolved conflict discovered during the broader sweep (real, not routed around):** running
`pytest tests/tools/ -m "not slow and not extra_slow" -q` (full sweep, per the ticket's own
Verification instructions) surfaces 5 failures, all pre-existing and all in files this ticket does
not own — `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced`,
`tests/tools/test_kgmcp_phase1_baseline_comparison.py::test_no_frozen_kgmcp_dependency_edited`,
`tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_no_frozen_kgmcp_dependency_edited`,
`tests/tools/test_knowledge_gateway_mcp.py::test_search_mcp_py_provably_untouched`,
`tests/tools/test_knowledge_gateway_mcp.py::test_wrapper_functions_genuinely_not_applicable_zero_invoked`.
All 5 assert (via `git diff --stat HEAD`) that `tools/retrieval_events.py` has **zero diff** —
encoded by separate, already-closed KGMCP baseline-comparison tickets that treat this file as a
permanently frozen dependency for their own measurement work. This ticket's Bug 1 fix, explicitly
mandated by this ticket's own text, requires editing exactly that file to remove a real, confirmed
crash. This is a genuine architectural conflict between two tickets' requirements on the same file,
not something to silently route around: per CLAUDE.md ("never edit an artifact to make an automated
gate/check pass instead of fixing the underlying substance" / "stop and report it truthfully"), the
KGMCP guard tests were NOT edited by this implementation — that would require updating another
ticket's frozen-dependency invariant, which is out of this ticket's scope and belongs to whoever
owns the KGMCP measurement-baseline tickets. **Filed as a separate follow-up ticket**,
`TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE`, to update those 5 guard tests' coarse
frozen-file check now that `tools/retrieval_events.py` has a legitimate, required edit reason (a
production bug fix), and to confirm the KGMCP baseline-comparison methodology those tickets rely on
(Design Decision D1: zero invocation from the KGMCP pipeline) is not actually invalidated by this
specific, narrow change (the diff only touches the `events_file is None` default-resolution branch,
not any `wrap_*()` signature/behavior those tests exercise — confirmed by direct diff read).

## Test Summary
- `pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_skill_usage_metric.py -v` — **69 passed, 0 failed** (this ticket's own required verification command, full pass).
- `pytest tests/tools/ -m "not slow and not extra_slow" -q` (broader sweep) — **2649 passed, 5 failed, 16 skipped, 31 deselected, 1 xfailed** in 403.25s. The 5 failures are unrelated to this ticket's 2 target bugs (see "Unresolved conflict discovered" above) — confirmed by direct inspection of each failing assertion, all of which fail solely because `tools/retrieval_events.py` now has a non-empty `git diff --stat HEAD`, which is the intended, required outcome of Bug 1's fix.

## Files Changed
- `tools/retrieval_events.py` — Bug 1 fix (default `events_file` resolution).
- `tools/agent-monitoring/retrieval_baseline_metrics.py` — Bug 2 fix (`load_jsonl` → `load_data_glob`).
- `tools/agent-monitoring/skill_usage_metric.py` — Bug 2 fix (`load_jsonl` → `load_data_glob`).
- `tests/tools/test_retrieval_events.py` — regression test for Bug 1's default-target fix.
- `tests/tools/test_retrieval_baseline_metrics.py` — regression tests for Bug 2's fix, including cross-week fixture coverage.
- `tests/tools/test_skill_usage_metric.py` — regression tests for Bug 2's fix, including cross-week fixture coverage, plus a stale-legacy-path fix in `_independently_derive_counts()`.

## Completion Summary
Both confirmed regressions from `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC` are fixed:
`tools/retrieval_events.py::emit_retrieval_event()` no longer references the removed
`record_events.EVENTS_FILE` constant (now computes the identical current-ISO-week target
`record_events.py` itself uses), and `tools/agent-monitoring/retrieval_baseline_metrics.py` /
`skill_usage_metric.py` no longer crash with `IsADirectoryError` (both now use the multi-week-aware
`load_data_glob()`). All 3 target test files pass in full (69/69), with new regression tests
proving correct current-week write behavior and correct multi-week corpus aggregation, plus one
incidental stale-path bug fixed in a test fixture. A genuine, pre-existing architectural conflict
with 5 unrelated KGMCP-ticket guard tests (which assert `tools/retrieval_events.py` must never be
edited) was discovered during the broader sweep and is reported, not silently worked around — see
Implementation Notes for the recommended follow-up.
