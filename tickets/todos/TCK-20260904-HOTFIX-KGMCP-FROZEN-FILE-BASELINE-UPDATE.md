---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE
phase: open
date: 2026-09-04
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE

## Title
5 KGMCP baseline-comparison tests assert `tools/retrieval_events.py` is permanently git-diff-frozen; update the check now that a legitimate, invariant-preserving edit has landed

## Status
OPEN

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
- [ ] D1's real invariant (zero invocation) is confirmed still true against the post-hotfix
      `retrieval_events.py`, via the existing spy-based test, not by assumption.
- [ ] All 5 occurrences of the coarse `git diff --stat`-based freeze check are replaced with (or
      supplemented by) a check that verifies what actually matters, with the decision recorded.
- [ ] `pytest tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase1_baseline_comparison.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_knowledge_gateway_mcp.py -v` passes.
- [ ] The full `tests/tools/` broader sweep is clean (no new failures introduced by this change).

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

## Test Summary

## Files Changed

## Completion Summary
