---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX
phase: open
date: 2026-08-24
tags: [testing, debugging]
---

# TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX

## Title
Make terminal-status call-site tests structurally robust to line drift

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P0

## Request Summary
Two tests hardcode the literal call_sites == [1546, 1558] line-number pair where FINALIZE_INCOMPLETE's writeMonitoring calls appear in .claude/workflows/implement-ticket.js: test_terminal_status_extractor.py::test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count (line 101) and test_terminal_status_conformance.py::test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides (line 69). This exact drift has forced 8 separate hotfix tickets since 2026-08-02 (2 on Aug 02, 1 each on Aug 17 and Aug 18, and 4 more on Aug 24 alone). The fix replaces the literal-line assertions with structural invariants (exactly 2 distinct, strictly-ascending call sites) so the tests survive unrelated line insertions in the workflow script, without requiring a JS AST parser (none exists in this repo).

## Scope
- Replace the two hardcoded literal call_sites == [1546, 1558] assertions in test_terminal_status_extractor.py and test_terminal_status_conformance.py with structural invariants: exactly 2 distinct, strictly-ascending call sites for FINALIZE_INCOMPLETE
- Add or adjust a stable, content-based marker (e.g. the distinct preceding pushEvent message text) in terminal_status_extractor.py so the two FINALIZE_INCOMPLETE call sites remain distinguishable from each other without relying on absolute line position
- Keep extract_literal_statuses' return shape ({value, kind, line} plus any added marker field) consistent across both consuming test files
- Re-verify the current live line numbers in .claude/workflows/implement-ticket.js at implementation time, since they may have drifted again since this investigation
- Confirm via a repo-wide check that no other test file hardcodes an absolute line number tied to a mutable location in implement-ticket.js

## Out of Scope
- A full JS AST/parser rewrite of terminal_status_extractor.py -- no precedent in this repo (tools/gate_checks/workflow_meta_conformance.py also relies on regex-over-raw-text, not a parser), and would be a larger change than warranted
- Changes to terminal-statuses.yaml's authoritative value/kind/phases fields -- only the non-binding line-provenance handling is affected by this fix
- Changes to test_terminal_status_schema.py -- it validates schema/shape only and is unaffected by this issue

## Acceptance Criteria
- [ ] test_terminal_status_extractor.py:101 and test_terminal_status_conformance.py:69 no longer assert an exact literal call_sites line-number list; instead assert structural invariants (exactly 2 distinct, strictly-ascending call sites for FINALIZE_INCOMPLETE) that hold regardless of absolute line index
- [ ] extract_all_terminal_statuses()/extract_literal_statuses() still distinguish the two FINALIZE_INCOMPLETE call sites from each other via a stable, content-based marker (e.g. the distinct preceding pushEvent message text), not absolute line position
- [ ] Inserting a synthetic extra line above both FINALIZE_INCOMPLETE call sites in a test fixture does not change either test's pass/fail outcome, demonstrating tolerance of unrelated line insertions
- [ ] pytest tests/agent_orchestration_claude_adapter tests/agent_orchestration -m "not slow and not extra_slow" passes after the change, and a repo-wide check confirms no other test file hardcodes an absolute line number tied to a mutable source location in implement-ticket.js

## Related Tickets
- TCK-20260802-TERMSTATUS-DRIFT-FIX
- TCK-20260802-DOC-COVERAGE-CHECK
- TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS
- TCK-20260818-HOTFIX-TERMINAL-STATUS-CONTRACT-DRIFT
- TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT
- TCK-20260824-HOTFIX-TERMINAL-STATUS-EXTRACTOR-DRIFT
- TCK-20260824-PARITY-NEXT-ID-LOOKUP
- TCK-20260824-HOTFIX-FINALIZE-INCOMPLETE-LINE-DRIFT

## Related Docs
- agent-orchestration/terminal-statuses.yaml
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent_orchestration_claude_adapter/terminal_status_extractor.py
- tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py
- tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py
- tests/agent_orchestration_claude_adapter/test_terminal_status_schema.py
- tools/agent_orchestration_claude_adapter/terminal_status_loader.py
- tools/agent_orchestration/terminal_statuses.py
- agent-orchestration/terminal-statuses.yaml
- tools/gate_checks/workflow_meta_conformance.py
- .claude/workflows/implement-ticket.js

## Assumptions / Open Questions
- No JS AST/parser tooling exists in this repo; the fix mirrors workflow_meta_conformance.py's own precedent of regex-over-raw-text rather than introducing one
- Both FINALIZE_INCOMPLETE call sites live in flat top-level procedural script code, not inside any named JS function/block, so the realistic structural marker is nearby distinguishing text (differing preceding pushEvent message), not a function name
- extract_literal_statuses' return shape is consumed by both test files; any added context/marker field must stay consistent across both call sites in the same ticket
- terminal-statuses.yaml already documents line citations as 'best-effort provenance only' while treating only value/kind/phases as authoritative -- this fix mirrors that same authoritative-data vs non-binding-provenance split
- The count/distinctness invariant (exactly 2 call sites) must remain just as strict after removing the line-number assertion -- must not be weakened
- This is the 8th occurrence since 2026-08-02; live line numbers in implement-ticket.js must be re-verified at implementation time since they may have drifted again
- layer assigned as `testing` (rather than `ai`) since the scope and acceptance criteria center on test structural robustness rather than the agent-orchestration tooling's own behavior; flagged here per ticket-format guidance for a non-obvious layer call

## Implementation Notes
Re-verified live line numbers before touching anything (`grep -n "FINALIZE_INCOMPLETE"
.claude/workflows/implement-ticket.js`): still 1546/1558, unchanged since scoping — no re-drift in
the interim.

Added a content-based distinctness marker to `terminal_status_extractor.py`:
`_MESSAGE_CONTEXT_RE = re.compile(r"message:\s*'([^']*)'")` searches a bounded 400-char lookahead
window after each literal call site for the nearby `message: '...'` string-literal prefix (stops
at the first closing quote, so a `+ variable` concatenation suffix on one of the two real call
sites is harmlessly ignored). `extract_literal_statuses()` now returns `context` per entry;
`extract_all_terminal_statuses()`'s aggregated dict gained a parallel `contexts` list alongside the
existing `call_sites` list — verified against the real live file: the two real FINALIZE_INCOMPLETE
call sites produce two genuinely distinct contexts ("Finalize self-check output could not be
parsed..." vs "Finalize completed its steps but the post-migration self-check found a
discrepancy..."), confirming the marker is meaningful, not just present. `call_sites`' own
`list[int]` shape is unchanged — purely additive, backward compatible.

Replaced both hardcoded `== [1546, 1558]` assertions (test_terminal_status_extractor.py:101,
test_terminal_status_conformance.py:69) with structural invariants: exactly 2 call sites, strictly
ascending, mutually distinct, plus 2 non-None mutually-distinct context markers. A pure
count/ascending check alone would not have caught an accidental duplicate of the same call site
replacing the other real one (still 2 ascending ints) — the context-distinctness check closes that
gap, making the new assertion strictly stronger than a naive line-number-agnostic rewrite, not just
weaker-but-safer than the original.

Added `test_call_site_detection_tolerates_unrelated_line_insertion_above` (synthetic `tmp_path`
fixture, not the real file) proving the fix's own assertions survive an unrelated line inserted
above both call sites — confirms raw line numbers genuinely shift by 1 while every structural
invariant (count, ascending, distinctness, context values themselves) stays identical between the
base and shifted fixture.

Repo-wide check (`grep -rln "implement-ticket.js" tests/ --include="*.py" | xargs grep -lE "==
*\[[0-9]+"`) re-run post-implementation: only these same two files match — no other latent instance
of this drift class exists elsewhere in the test suite.

`docs/parity_ledger/infrastructure.yaml` gained INFRA-384 (`verified`/P2/regression,
`support_boundary`: pure Claude-agent-workflow tooling, mirroring INFRA-263/264/265/315/379/381's
existing precedent for this shard) via `tools/parity_ledger_writer.py::write_entry()` — real ID
obtained live from `tools/gate_checks/parity_updater_static.py::next_available_id('infrastructure.yaml')`
(returned `INFRA-384`), not guessed or copied from a stale prior citation.

No doc under `docs/` needed updating: `agent-orchestration/terminal-statuses.yaml`'s own header
already documents line citations as "best-effort provenance only" (unaffected by this change,
since `call_sites`' shape is unchanged); no other doc references `call_sites`/`contexts` by name
(confirmed via `grep -rln "call_sites" docs/` — the one match, in the parity ledger, is an unrelated
test name substring match, not a real reference to this field).

## Test Summary
`pytest tests/agent_orchestration_claude_adapter tests/agent_orchestration -m "not slow and not
extra_slow" -q` → **98 passed**, 0 failed (includes the 2 modified assertions + 1 new test).
Narrower re-run of just the 3 directly-affected files (`test_terminal_status_extractor.py`,
`test_terminal_status_conformance.py`, `test_terminal_status_schema.py`) → **20 passed**,
confirming `test_terminal_status_schema.py` (a separate data path, validates the committed YAML
file) is genuinely unaffected.

## Files Changed
- `tools/agent_orchestration_claude_adapter/terminal_status_extractor.py` — added `context`/
  `contexts` fields (additive, `call_sites` shape unchanged)
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py` — replaced the
  hardcoded line-number assertion with structural invariants; added
  `test_call_site_detection_tolerates_unrelated_line_insertion_above`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` — replaced the
  hardcoded line-number assertion with structural invariants
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-384

## Completion Summary
Closed the 9th occurrence of a recurring drift pattern (8 prior hotfix tickets since 2026-08-02)
by replacing two hardcoded `FINALIZE_INCOMPLETE` call-site line-number literals with structural
invariants that survive unrelated edits to `.claude/workflows/implement-ticket.js`. The fix adds a
genuinely stronger check than a naive "just drop the line-number assertion" rewrite would have: a
content-based distinctness marker (the nearby `message:` string-literal prefix) ensures the two
call sites are verified as distinct code paths, not merely "2 ascending integers" that could
silently pass even if one real call site were accidentally duplicated over the other. A new
synthetic-fixture test proves the invariants are genuinely line-position-independent. No other test
in the repo hardcodes a line number tied to this same mutable file (re-confirmed post-implementation).
No `src/` behavior changed; `docs/parity_ledger/infrastructure.yaml` gained INFRA-384 for the
tooling-only behavior change. 98/98 scoped tests pass.
