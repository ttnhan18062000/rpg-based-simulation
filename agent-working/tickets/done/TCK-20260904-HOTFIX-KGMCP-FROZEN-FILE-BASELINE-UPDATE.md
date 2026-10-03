---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE
phase: done
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE

## Title
5 KGMCP baseline-comparison tests assert `tools/retrieval_events.py` is permanently git-diff-frozen; update the check now that a legitimate, invariant-preserving edit has landed

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Discovered while implementing `TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS`, whose
real Bug 1 fix (repointing `tools/retrieval_events.py::emit_retrieval_event()`'s default `events_file`
resolution off a removed `record_events.py` constant) requires editing `tools/retrieval_events.py`.

5 unrelated tests, all from earlier KGMCP measurement/baseline tickets, each independently assert:
```python
result = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "tools/retrieval_events.py"], ...)
assert result.stdout == "", "tools/retrieval_events.py must be fully frozen for this ticket"
```
(`tests/tools/test_kgmcp_measurement_baseline.py`, `test_kgmcp_phase1_baseline_comparison.py`,
`test_kgmcp_phase2_baseline_recomparison.py`, `test_knowledge_gateway_mcp.py` — 2 occurrences in the
last file).

`test_knowledge_gateway_mcp.py`'s own module docstring names the real invariant this proxy check
exists to protect: **"Design Decision D1"** — none of `retrieval_events.py`'s 3 `wrap_*()` wrapper
functions has a real call site anywhere in the KGMCP pipeline; that module doesn't import or call
`retrieval_events.py` at all. The `git diff --stat` check is a coarse proxy for "nothing changed that
could invalidate D1's zero-invocation finding" — it is stricter than what actually matters, since it
fires on ANY edit to the file, even one that never touches the 3 wrapper functions D1's own
spy-based instrumentation (test 7 in that file) actually monitors.

**Confirmed this session, by direct diff read**: the sibling hotfix's edit to
`tools/retrieval_events.py` is entirely confined to `emit_retrieval_event()`'s private default-
argument fallback (repointing a dead constant reference) — none of the 3 `wrap_*()` functions
changed at all. D1's real, underlying invariant (zero invocation from the KGMCP pipeline) is
structurally unaffected and still provably true.

## Scope
- Confirm D1's real invariant (zero invocation of `retrieval_events.py`'s 3 `wrap_*()` functions
  from the KGMCP pipeline) still holds by actually running `test_knowledge_gateway_mcp.py`'s own
  spy-based test 7 with the frozen-file assertion temporarily bypassed — do not just assume it
  holds because this ticket's own investigation says so; re-verify directly.
- Update all 5 occurrences of the `git diff --stat`-based frozen-file check to something that
  verifies the invariant that actually matters, not merely "this file has never been touched since
  some baseline commit." Options to weigh (decide and record which, don't default silently):
  (a) narrow the check to only the 3 `wrap_*()` function bodies (e.g. via AST inspection or a
  targeted `git diff` on specific line ranges), or (b) replace the freeze check with a direct
  re-run of the zero-invocation spy test itself (already exists in this file) as the real
  regression guard, dropping the coarser file-freeze proxy entirely, or (c) capture a new baseline
  (accept the current, post-hotfix content of `retrieval_events.py` as the new frozen reference
  point) if these tests' real purpose is "hasn't changed since the LAST TIME we checked," not
  "hasn't changed since day one."
- Investigate whether `test_kgmcp_measurement_baseline.py`/`test_kgmcp_phase1_baseline_comparison.py`/
  `test_kgmcp_phase2_baseline_recomparison.py` have the same D1-style underlying rationale, or a
  different one (they may be checking something else about this file — confirm before assuming
  they share `test_knowledge_gateway_mcp.py`'s exact reasoning).

## Out of Scope
- Any change to `tools/retrieval_events.py` itself — already correctly fixed by the sibling ticket.
- Any change to the actual KGMCP measurement/baseline numbers these tests compare against, unless
  investigation finds the real invariant genuinely was affected (expected: it was not).

## Acceptance Criteria
- [x] D1's real invariant (zero invocation) is confirmed still true against the post-hotfix
      `retrieval_events.py`, via the existing spy-based test, not by assumption.
- [x] All 5 occurrences of the coarse `git diff --stat`-based freeze check are replaced with (or
      supplemented by) a check that verifies what actually matters, with the decision recorded.
- [x] `pytest tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase1_baseline_comparison.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_knowledge_gateway_mcp.py -v` passes.
- [x] The full `tests/tools/` broader sweep is clean (no new failures introduced by this change).

## Related Tickets
- TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS (the sibling hotfix whose real,
  necessary fix to `retrieval_events.py` first exposed this coarse-guard conflict)
- TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE (owns `test_knowledge_gateway_mcp.py`'s own Design
  Decision D1)

## Related Docs
None yet — investigate whether Design Decision D1 is documented anywhere beyond the test file's own
docstring.

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `tests/tools/test_kgmcp_measurement_baseline.py`
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py`
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`
- `tests/tools/test_knowledge_gateway_mcp.py`

## Assumptions / Open Questions
- Assumes all 5 occurrences share a similar underlying rationale to D1 — must be confirmed per-file,
  not assumed uniformly.
- `layer: observability` matches this repo's established pattern.

## Implementation Notes
Investigated all 5 occurrences (not assumed uniform). All 5 share the same real underlying reason
Design Decision D1 already established: `retrieval_events.py`'s 3 `wrap_*()` functions
(`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) have zero
call sites anywhere in the live KGMCP pipeline — confirmed by re-running
`test_wrapper_functions_genuinely_not_applicable_zero_invoked`'s spy-based assertions before making
any change (AC #1). Since the file is provably not part of what any of the 5 tests' own pipelines
actually execute, edits to it cannot affect measurement/baseline reproducibility for any of them —
the coarse `git diff --stat HEAD` freeze check was always a strictly broader-than-necessary proxy.

Chose the fix pattern this exact codebase already has 5+ precedents for in these same test files
(`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
`tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_cache.py`,
`tools/knowledge_gateway_redaction.py`, `tools/retrieval_cache.py` were each previously removed
from a `banned_path` tuple with an inline comment once a later, reviewed ticket had a legitimate
reason to touch that file): removed `tools/retrieval_events.py` from the `banned_path` tuple in
all 4 test files (5 occurrences), each with an inline comment citing this ticket and the D1
rationale — this directly satisfies "verifies the invariant that actually matters" (recorded
decision, not silent): the real invariant (zero invocation) is independently verified by
`test_wrapper_functions_genuinely_not_applicable_zero_invoked`'s spy assertions, which remain
in place; the freeze-check's own byte-identity proxy for that invariant is no longer needed and is
dropped, not replaced with a narrower AST-based check (Scope option (a)) or a new frozen-baseline
recapture (option (c)) — neither adds real protection beyond what the spy test already provides.

`test_wrapper_functions_genuinely_not_applicable_zero_invoked`'s own trailing `git diff --stat
HEAD -- tools/retrieval_events.py` assertion was removed outright (not just narrowed) since it was
directly redundant with the spy assertions three lines above it in the same function — a docstring
was added explaining why. The other 3 occurrences (`test_no_live_gateway_code_or_search_mcp_edits_introduced`,
2x `test_no_frozen_kgmcp_dependency_edited`, `test_search_mcp_py_provably_untouched`) had
`tools/retrieval_events.py` removed from their respective `banned_path` tuples with an inline
comment; `test_search_mcp_py_provably_untouched`'s docstring was also updated (it previously said
"the remaining two paths stay genuinely frozen," which is now just one).

## Test Summary
- `pytest tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase1_baseline_comparison.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_knowledge_gateway_mcp.py -v` —
  93 passed, 2 skipped, 1 failed. The 1 failure
  (`test_knowledge_gateway_mcp.py::test_only_knowledge_context_and_knowledge_status_registered`) is
  a pre-existing, unrelated local-sandbox gap (`ModuleNotFoundError: No module named 'mcp'` — the
  `mcp` package isn't installed in this venv) — confirmed by stashing this ticket's own changes and
  re-running the same test, which fails identically without any of this ticket's edits applied.
  Real CI's clean `pip install -r requirements.txt` environment installs this dependency and does
  not hit this gap.
- `pytest tests/tools/ -m "not slow and not extra_slow" -q` (broader sweep) — 2634 passed, 1
  failed, 35 skipped, 31 deselected, 1 xfailed in 376.17s. The 1 failure is the same pre-existing,
  unrelated `mcp`-module environment gap noted above — no new failures introduced by this change.

## Files Changed
- `tests/tools/test_kgmcp_measurement_baseline.py` — removed `tools/retrieval_events.py` from
  `test_no_live_gateway_code_or_search_mcp_edits_introduced`'s `banned_path` tuple.
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py` — removed `tools/retrieval_events.py`
  from `test_no_frozen_kgmcp_dependency_edited`'s `banned_path` tuple.
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` — removed `tools/retrieval_events.py`
  from `test_no_frozen_kgmcp_dependency_edited`'s `banned_path` tuple.
- `tests/tools/test_knowledge_gateway_mcp.py` — removed `tools/retrieval_events.py` from
  `test_search_mcp_py_provably_untouched`'s `banned_path` tuple (docstring updated) and dropped
  `test_wrapper_functions_genuinely_not_applicable_zero_invoked`'s redundant trailing freeze-check
  assertion (docstring added explaining why).

## Completion Summary
All 5 occurrences of the coarse `git diff --stat`-based frozen-file check on
`tools/retrieval_events.py` updated. Investigated per-file (not assumed uniform) and confirmed all
5 share Design Decision D1's rationale: the file's 3 `wrap_*()` functions have zero real call
sites in the KGMCP pipeline, re-verified directly via the existing spy-based test before any edit.
Followed this exact codebase's own established precedent (5+ prior instances in these same test
files) for retiring a stale `banned_path` entry once a later ticket has a legitimate reason to
touch it: removed the path with a documented per-occurrence rationale rather than inventing a new
narrower mechanism, since the real invariant is already independently verified elsewhere. Target
test files pass (93/93 real assertions; 1 unrelated pre-existing environment gap confirmed via
stash-and-rerun); broader `tests/tools/` sweep is clean.
