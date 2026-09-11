---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS
phase: done
date: 2026-09-09
tags: [ai, mcp, agent-monitoring]
---

# TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS

## Title
Archive 5 KGMCP phase-comparison runner scripts left orphaned by the gateway archival, and widen TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY's verification grep

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (PR #147) archived the Knowledge Gateway MCP
source modules — `git mv tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`
→ `tools/archive/`, plus their test files → `tests/archive/` (excluded from pytest collection via
a new `norecursedirs` entry). It moved every file that ticket's own investigation inventoried
under `tools/` and `tests/tools/`, but never scanned `tools/agent-monitoring/` for consumers of
the same dead paths — 5 one-time measurement-runner scripts there still dynamically load the
now-archived `tools/knowledge_gateway_mcp.py` by its old, pre-archival path and would raise
`FileNotFoundError` (via `importlib.util.spec_from_file_location` on a nonexistent path) if anyone
ever tried to run them again. This went undetected by CI because these 5 scripts' own tests were
*also* archived (excluded from collection) in the same PR, alongside the gateway's own tests —
so the archived tests never actually exercise the broken import today, and nothing else imports
these runner scripts.

Found while starting `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s upcoming verification: that
ticket's own body text (lines 51-52, 74-75, 105) has a grep pattern for "is anything still
importing the old gateway paths" scoped only to `tools/archive/knowledge_gateway\|tools\.archive\.
knowledge_gateway` — the NEW archived-path form — so it would never have caught these 5 files
either, which reference the OLD pre-archival form.

## Scope
- `git mv` the 5 orphaned runner scripts from `tools/agent-monitoring/` to `tools/archive/`
  (matching the flat, subdirectory-agnostic `tools/archive/` convention already used for the
  gateway's own source modules — no `tools/agent-monitoring/archive/` subfolder):
  - `kgmcp_phase1_gateway_runner.py`
  - `kgmcp_phase2_gateway_runner.py`
  - `kgmcp_phase3_gateway_runner.py`
  - `kgmcp_phase4_direct_tool_comparison_runner.py`
  - `kgmcp_phase4_warm_direct_tool_comparison_runner.py`
- Update the already-archived, collection-excluded test files' own path constants
  (`_RUNNER_MODULE_PATH`-style variables and any bare `from kgmcp_phaseN_..._runner import ...`
  cross-imports) to point at the new `tools/archive/` location, matching the exact precedent
  already set when the gateway's own archived tests (e.g. `tests/archive/test_knowledge_gateway_
  router.py`'s `_ROUTER_PATH = ... / "tools" / "archive" / "knowledge_gateway_router.py"`) were
  updated in the same prior PR.
- Widen `tickets/inprogress/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md`'s own verification grep
  pattern (lines 51, 52, 74, 75, 105) from the archived-path-only form to the bare `knowledge_gateway`
  stem (excluding self-references inside `tools/archive/`/`tests/archive/`), so that ticket's own
  future 2-week-window check will actually catch this class of orphaned-reference bug instead of
  missing it the same way again.
- No change to `tools/agent-monitoring/kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`, or
  `kgmcp_phase5_repeated_demand_measurement_runner.py` — independently confirmed none of the three
  reference any dead gateway path (`kgmcp_baseline_runner.py` shells out to the `graphify` CLI and
  `search_mcp.py`, never an in-process gateway import; `kgmcp_phase5_...` reads only frozen JSON
  fixture snapshots and `tools/registry_query.py`, no gateway reference at all).

## Out of Scope
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` itself remains correctly BLOCKED on its 2-week
  monitoring window (ends ~2026-09-22) — this ticket only widens that future ticket's own
  verification grep pattern in its body text; it does not start or unblock that ticket's actual
  delete work.
- No behavior change to any live, currently-runnable code path — `retrieval_cache.py`'s 3 real
  call sites already repointed to `tools/write_path_guard.py` in PR #147 and are unaffected here.
- `tools/agent-monitoring/generate_retro.py`'s 4 `knowledge_gateway` string mentions are inside
  docstring/prose text describing historical behavior, not live imports or path construction —
  independently confirmed via direct read (lines 720-730, 2138-2143); no change needed, not touched
  by this ticket.

## Acceptance Criteria
- [x] All 5 runner scripts relocated to `tools/archive/` via `git mv` (history-preserving rename)
- [x] Their sibling archived test files' path constants updated to the new location; test
      collection still correctly excludes them (no new failures introduced into the active suite)
- [x] `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md`'s verification grep pattern widened and
      manually re-run against the current tree to confirm it now surfaces (rather than misses) this
      exact class of reference
- [x] No remaining reference to the 5 moved files' old `tools/agent-monitoring/` path in any
      ACTIVE (non-archived, non-historical) `tools/`, `tests/`, `docs/`, or `Makefile` location —
      confirmed via a full-repo grep. Remaining hits are all either (a) already-`historical`
      `tickets/done/`/`stored_artifacts/`/`docs/` records of the original, now-closed KGMCP phase
      tickets, correctly describing the path as it existed at that point in time, or (b) the
      deliberately-left-stale secondary/incidental cross-references inside `tools/archive/`
      and `tests/archive/` themselves (the `_FROZEN_FILE_HASHES` sibling entries and one
      `git diff --stat` banned-path string), matching the exact precedent already set by PR #147's
      own archival of the gateway modules — see Implementation Notes.

## Related Tickets
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (done) — the PR #147 work that archived the
  gateway modules and their tests but missed these 5 consumers
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (blocked, in progress) — whose own verification
  grep this ticket widens

## Related Docs
None touched — this is a pure `tools/`-tree relocation plus a `tickets/inprogress/` body-text
grep-pattern edit; no `docs/` behavior description exists for these one-time hand-run scripts.

## Related Stored Artifacts
None — hotfix tier, self-evident intent per project convention; no staging artifacts created.

## Related Code Areas
`tools/agent-monitoring/kgmcp_phase{1,2,3,4}_*runner.py`, `tools/archive/`, `tests/archive/`,
`tickets/inprogress/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md`

## Assumptions / Open Questions
- Assumed archive (not repoint-and-keep-runnable) is correct: these are explicitly documented as
  "run once, by hand, during Implementation — never wired into the fast pytest loop" scripts whose
  originating tickets are all long closed and whose measured results are already recorded in
  `docs/engine/contracts/knowledge_gateway_mcp/phase{1,2,3,4}_*.md`. Repointing them to load
  `tools/archive/knowledge_gateway_mcp.py` would keep them technically importable but pointless —
  the KGMCP gateway itself is deprecated and scheduled for deletion, so a fresh "gateway vs.
  baseline" comparison run has no remaining purpose. Archiving matches their own already-archived
  tests and the disposition of everything else in this deprecation.
- The archived runner scripts' own internal `_GATEWAY_MODULE_PATH` dynamic-sibling-load (pointing
  at `tools/knowledge_gateway_mcp.py`, computed via `Path(__file__).resolve().parent.parent`) is
  left unfixed after the move — same as the precedent set by `tools/archive/knowledge_gateway_mcp.
  py`'s own internal sibling-loading of `knowledge_gateway_router.py`, which was also left pointing
  at the old pre-archival path after that file's own archival. Archived code is a frozen historical
  record, never executed again; internal cross-reference correctness within the archived group is
  not maintained, consistent with how the gateway modules themselves were already handled.

## Implementation Notes
- Independently confirmed (direct `grep -l` before any change) that all 5 runners reference one or
  more of `knowledge_gateway_mcp.py`/`knowledge_gateway_redaction.py`/`knowledge_gateway_router.py`/
  `knowledge_gateway_cache.py`/`knowledge_gateway_packet_assembly.py` via
  `_GATEWAY_MODULE_PATH = _TOOLS_DIR / "knowledge_gateway_mcp.py"` (`importlib.util.
  spec_from_file_location`), and that `kgmcp_baseline_corpus.py`, `kgmcp_baseline_runner.py`, and
  `kgmcp_phase5_repeated_demand_measurement_runner.py` do not (the first two use only the
  `graphify` CLI and `search_mcp.py`; phase5 reads only frozen JSON fixtures + `registry_query.py`).
  Also confirmed `generate_retro.py`'s 4 `knowledge_gateway` mentions are all inside docstring/
  string-literal prose, not live imports.
- `git mv` all 5 to `tools/archive/` (flat, matching the existing gateway-module convention — no
  `tools/agent-monitoring/archive/` subfolder).
- **Self-inflicted regression found and fixed before it shipped**: each runner computes
  `_MONITORING_TOOLS_DIR = Path(__file__).resolve().parent` to locate its still-live sibling
  `kgmcp_baseline_corpus.py` import. After the move this would have silently pointed at
  `tools/archive/` instead of `tools/agent-monitoring/` — breaking a currently-working import that
  had nothing to do with the dead gateway path. Fixed by explicitly computing
  `_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"` and adding a separate `_ARCHIVE_DIR` for
  the sibling-runner cross-imports (e.g. phase2/phase3/phase4 importing `kgmcp_phase1_gateway_runner`;
  phase4_warm importing phase3 and phase4). Verified via a direct `importlib` load: `kgmcp_phase1_
  gateway_runner` and `kgmcp_phase4_direct_tool_comparison_runner` now import cleanly; the other 3
  fail only on `from tools import knowledge_gateway_redaction as _kgr_redaction`, a reference that
  was ALREADY dead (pointing at a path archived by PR #147, before this ticket ever touched these
  files) — left unfixed, consistent with treating archived code as a frozen historical record whose
  internal cross-reference correctness is not maintained (same disposition PR #147 itself gave
  `tools/archive/knowledge_gateway_mcp.py`'s own now-dead sibling-loading of
  `knowledge_gateway_router.py`).
- `_GATEWAY_MODULE_PATH` itself (`_TOOLS_DIR / "knowledge_gateway_mcp.py"`) is left unfixed for the
  same reason — the module it points at is permanently gone, deliberately never repointed at
  `tools/archive/`, since these scripts have no remaining purpose to actually run.
  **Governing rule, stated explicitly** (raised by peer review of the PR — the two calls above read
  as inconsistent without it): fix only breakage this ticket's own `git mv` would introduce into
  code that was working immediately before the move (`_MONITORING_TOOLS_DIR`/`kgmcp_baseline_corpus.py`);
  never repair breakage that already existed in code being archived (`_GATEWAY_MODULE_PATH`,
  `from tools import knowledge_gateway_redaction`). Note this means the `_MONITORING_TOOLS_DIR` fix
  buys no functional runnability by itself — with `_GATEWAY_MODULE_PATH` still dead, none of these
  5 scripts can actually execute either way. The fix is still correct: it restores each script to
  exactly the state PR #147 itself left it in (broken only on the gateway import, not on anything
  this hotfix's own move would have additionally broken), rather than leaving this ticket
  responsible for a second, unrelated breakage on top of the first.
- Updated the 5 already-archived, collection-excluded sibling test files' PRIMARY module-under-test
  path (`_RUNNER_MODULE_PATH`, read via `.read_text()` at module level in all 5, so an unfixed path
  would raise even at collection time if ever un-excluded) to `_ARCHIVE_DIR / "kgmcp_phase*.py"`,
  mirroring the exact precedent already set for `tests/archive/test_knowledge_gateway_router.py`'s
  own `_ROUTER_PATH`. Left the SECONDARY/incidental references — `test_kgmcp_phase3_...`'s
  `_FROZEN_FILE_HASHES` dict entries for sibling phase1/phase2 runners, and
  `test_kgmcp_phase2_...`'s one `git diff --stat`-based banned-path string literal — pointing at the
  old `tools/agent-monitoring/` location, because that exact same class of reference
  (`knowledge_gateway_router.py`/`knowledge_gateway_cache.py` entries in `test_kgmcp_phase4_direct_
  tool_comparison.py`'s own `_FROZEN_FILE_HASHES`) was ALREADY left unfixed by PR #147 itself when it
  archived those gateway modules — this ticket matches that established precedent rather than
  auditing/fixing every secondary reference across the whole archived test suite, which was out of
  scope for PR #147 and stays out of scope here too.
- Widened `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md`'s Scope bullet (verification grep
  pattern) from `tools/archive/knowledge_gateway\|tools\.archive\.knowledge_gateway` (archived-path
  form only) to a bare `knowledge_gateway` stem excluding `tools/archive/`/`tests/archive/`
  self-references. Left the 3 other `knowledge_gateway` occurrences in that ticket's own body text
  (Scope's hard-delete-target line, and 2 AC/Related-Code-Areas lines) unchanged — those correctly
  name the exact files to be hard-deleted at their real `tools/archive/` location, not a
  verification-grep pattern, so widening them would be wrong.
- All 5 relocated runner files and all 5 updated test files pass `python3 -m py_compile`.

## Test Summary
- `pytest tests/tools/test_write_path_guard.py tests/tools/test_retrieval_cache.py
  tests/tools/test_knowledge_gateway_archival.py tests/tools/test_test_scope_coverage_static.py -m
  "not slow" -q` — 189/189 passed.
- `pytest tests/tools/ tests/docs/ tests/static/ tests/architecture/ tests/integrity/ -m "not slow
  and not extra_slow" -q` — 2765 passed, 19 skipped, 29 deselected, 3 xfailed, 0 failed.
- Doc-staleness gate: `PASS` (`behavior_changed=False, 0 src/config/workflow path(s) flagged, 0
  docs/ path(s) present`).
- Parity: skip-eligible (no `src/` path changed, `behavior_changed=False`); `find_p0_intersection()`
  safeguard scan against the 10 changed `tools/`/`tests/` files returned `[]` — no P0 intersection.
- Post-Test cleanup checkpoint: `CLEANED` (489 stale `data/runs/` artifacts from this and concurrent
  sessions' test activity removed, mtime-gated).
- Full-repo grep confirms zero remaining reference to the 5 files' old `tools/agent-monitoring/`
  path outside already-historical ticket/doc records and the deliberately-left-stale secondary
  archived-test cross-references documented above.

## Files Changed
- `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` -> `tools/archive/kgmcp_phase1_gateway_runner.py` (moved, path-fix)
- `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` -> `tools/archive/kgmcp_phase2_gateway_runner.py` (moved, path-fix)
- `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py` -> `tools/archive/kgmcp_phase3_gateway_runner.py` (moved, path-fix)
- `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py` -> `tools/archive/kgmcp_phase4_direct_tool_comparison_runner.py` (moved, path-fix)
- `tools/agent-monitoring/kgmcp_phase4_warm_direct_tool_comparison_runner.py` -> `tools/archive/kgmcp_phase4_warm_direct_tool_comparison_runner.py` (moved, path-fix)
- `tests/archive/test_kgmcp_phase1_baseline_comparison.py` (path constant fix)
- `tests/archive/test_kgmcp_phase2_baseline_recomparison.py` (path constant fix)
- `tests/archive/test_kgmcp_phase3_pilot_acceptance_measurement.py` (path constant fix + documented-stale comment)
- `tests/archive/test_kgmcp_phase4_direct_tool_comparison.py` (path constant fix)
- `tests/archive/test_kgmcp_phase4_warm_direct_tool_comparison.py` (path constant fix)
- `tickets/inprogress/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md` (widened verification grep)

## Completion Summary
Archived the 5 orphaned KGMCP phase-comparison runner scripts that PR #147's gateway archival left
behind, fixed a real regression the move would otherwise have introduced (broken
`kgmcp_baseline_corpus.py` sibling import), kept the already-archived sibling tests' primary
module-under-test paths consistent with the move, and widened the follow-on delete ticket's own
verification grep so this exact class of bug can't slip through undetected again. No behavior
change to any live/currently-runnable code path. Full relevant regression suite (2765 tests) green.
