---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260903-HOTFIX-KGMCP-SHARED-VENV-RESOLUTION
phase: done
date: 2026-09-03
tags: [mcp, setup]
---

# TCK-20260903-HOTFIX-KGMCP-SHARED-VENV-RESOLUTION

## Title
KGMCP (knowledge-search / knowledge-gateway MCP) CONNECTION_CLOSED across all worktrees — launcher scripts never resolve to a real interpreter

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Both `mcp__knowledge-search__*` and `mcp__knowledge-gateway__*` MCP servers showed `CONNECTION_CLOSED`
in every Claude Code session on this machine (confirmed cross-session with a peer session in a
different worktree, which independently reported the identical outage). Root-caused directly: `.mcp.json`'s
launcher scripts (`tools/start_search_mcp.sh`, `tools/start_knowledge_gateway_mcp.sh`) select a Python
interpreter via `$REPO_ROOT/.venv/bin/python3` -> `/home/vboxuser/Work/venv/bin/python3` ->
bare `python3`, where `$REPO_ROOT` is derived from the launcher script's own location
(`dirname` of `dirname` of the script path). In a git-worktree checkout, every worktree has its own
copy of `tools/start_search_mcp.sh`, so `$REPO_ROOT` resolves to that worktree's own root, not the
main checkout — and no worktree has its own `.venv/`. `/home/vboxuser/Work/venv/...` is a different
machine's path entirely (per `docs/guidelines/agent_working_environment.md`'s documented two-environment
split). Both candidates fail on this machine, so every launch fell through to bare system `python3`,
which has none of the `mcp`/`sentence-transformers`/`torch`/`sqlite-vec`/`rank-bm25` packages —
the server process crashed on import before the MCP stdio handshake could even start, which every
client sees as `CONNECTION_CLOSED`.

The actual shared venv with all required packages already installed exists at
`/home/u24desktop/Working/rpg-based-simulation/.venv` (the main checkout root) — confirmed via direct
import checks, not assumed. No package installation was needed; the fix is purely in interpreter
resolution.

## Scope
- Add the absolute path `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` as the
  first candidate in both `tools/start_search_mcp.sh` and `tools/start_knowledge_gateway_mcp.sh`'s
  interpreter-selection fallback chains, so every worktree's MCP launch resolves to the one real,
  populated venv regardless of which worktree/branch triggered it.
- Keep the existing `$REPO_ROOT/.venv/bin/python3` and `/home/vboxuser/Work/venv/bin/python3`
  candidates as lower-priority fallbacks, preserving portability to other machines/setups (matching
  both scripts' own stated "works across machines with different venv paths" design intent).

## Out of Scope
- Installing any new packages — the shared venv already had everything needed.
- Building/refreshing the knowledge-search SQLite index — already present and current
  (`knowledge-index/knowledge.db`, per-worktree gitignored build artifact) in every worktree checked.
- Fixing the unrelated `docs/testing/regression_policy.md`-documented flaky/slow test category
  (`@pytest.mark.extra_slow`) hit incidentally while verifying this fix — pre-existing, unrelated to
  interpreter resolution, not touched.

## Acceptance Criteria
- [x] `bash tools/start_search_mcp.sh --test` run from this worktree returns real search results
      (verified directly: 3 real results for query "damage formula", not an error).
- [x] `bash tools/start_knowledge_gateway_mcp.sh` launches without a `ModuleNotFoundError` and enters
      the real MCP stdio JSON-RPC loop (verified: process starts, imports succeed, and it correctly
      validates/rejects malformed stdio input rather than crashing on import).
- [x] `tests/tools/test_search_mcp.py`, `tests/tools/test_knowledge_gateway_mcp.py` still pass (60/60).
- [x] The full previously-failing set (`test_kgmcp_measurement_baseline.py`,
      `test_kgmcp_phase3_pilot_acceptance_measurement.py`,
      `test_knowledge_gateway_failure_semantics.py`, `test_knowledge_gateway_mcp.py`) now passes when
      the shared venv is used — 65/66 (the 1 exception is `@pytest.mark.extra_slow`/`@pytest.mark.slow`,
      unrelated, hits this environment's resource-time budget on real heavy work, same category as the
      pre-existing `test_long_run_stability` case documented earlier this session).
- [x] Full `tests/tools/` suite with the shared venv: 2579 passed, 11 skipped, 31 deselected
      (`-m "not slow and not extra_slow"`), 1 xfailed, 0 failed — up from 2569 passed / 5 failed before
      this fix.

## Related Tickets
- TCK-20260814-KGMCP-CONTRACT-SCHEMAS (precedent for `layer: ai`, first KGMCP ticket)
- TCK-20260816-HOTFIX-KGMCP-LOCAL-DATA-BOOTSTRAP-DOCS (precedent hotfix, local dev-environment bootstrap)

## Related Docs
- docs/guidelines/agent_working_environment.md (two-environment split: u24desktop / vboxuser)
- requirements-knowledge.txt
- pyproject.toml (`knowledge`/`search-mcp` extras)

## Related Stored Artifacts
None. (hotfix tier — no staging artifacts required)

## Related Code Areas
- tools/start_search_mcp.sh
- tools/start_knowledge_gateway_mcp.sh

## Assumptions / Open Questions
- This fix hardcodes an absolute, machine-specific path (`/home/u24desktop/...`) as the first
  candidate, matching the existing script's own precedent of hardcoding `/home/vboxuser/Work/venv/...`
  unconditionally (relying on `[ -x "$py" ]` to naturally skip it on machines where the path doesn't
  exist) — not a new pattern, just a new entry in the same list.
- Whether other worktrees on this machine need anything beyond this fix (e.g. their own local
  `knowledge-index/`) was checked directly for this worktree only (confirmed present and current);
  not exhaustively checked for every other worktree on the machine.

## Implementation Notes
Root-caused via direct verification at every step, not assumed:
1. Confirmed both MCP servers were down cross-session (a peer session in a different worktree
   independently reported the identical `CONNECTION_CLOSED` state).
2. Read `.mcp.json` and both launcher scripts directly.
3. Confirmed `.venv/bin/python3` does not exist in this worktree, `/home/vboxuser/...` does not exist
   on this machine, and even the fallback venv this session had used all along for pytest
   (`/home/u24desktop/Working/venv/bin/python3`) was ALSO missing `mcp`/`sentence_transformers` — three
   separate confirmed dead ends before finding the real, populated venv at the main checkout root.
4. Confirmed the shared venv (`/home/u24desktop/Working/rpg-based-simulation/.venv`) already has
   `sentence_transformers 5.6.0`, `mcp`, `torch 2.12.1+cpu`, `sqlite_vec`, `rank_bm25` all installed —
   no install step needed.
5. Confirmed the knowledge-search index (`knowledge-index/knowledge.db`) already exists and is current
   in this worktree — not the blocker.
6. Edited both launcher scripts to check the absolute shared-venv path first.
7. Verified both launchers directly (not just trusted the edit): `start_search_mcp.sh --test` returned
   real search results; `start_knowledge_gateway_mcp.sh` launched into the real MCP stdio loop.
8. Ran the full relevant test suite before and after, confirming a real improvement (2569/5-failed ->
   2579/0-failed) and root-causing the one remaining failure as an unrelated, pre-existing
   `@pytest.mark.extra_slow` resource-budget case, not a regression from this fix.

## Test Summary
- `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_search_mcp.py tests/tools/test_knowledge_gateway_mcp.py -q` — 60 passed, 0 failed.
- `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py tests/tools/test_knowledge_gateway_failure_semantics.py -q` — 65 passed, 1 failed (the 1 failure is `@pytest.mark.extra_slow`/`@pytest.mark.slow`, a pre-existing resource-budget timeout unrelated to this fix, confirmed via direct marker inspection).
- `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/ -m "not slow and not extra_slow" -q` — 2579 passed, 11 skipped, 31 deselected, 1 xfailed, 0 failed.

## Files Changed
- `tools/start_search_mcp.sh` (added the shared absolute venv path as the first interpreter candidate)
- `tools/start_knowledge_gateway_mcp.sh` (same fix)

## Completion Summary
Fixed a real, repo-wide MCP outage (confirmed cross-session, not a local fluke) affecting every
worktree on this machine. Root cause was interpreter-resolution, not a missing dependency install —
the shared venv at the main checkout root already had every required package. Both launcher scripts
now check that absolute shared path first, before their existing relative/other-machine fallbacks, so
every worktree's `.mcp.json`-driven MCP launch resolves consistently to the one real interpreter.
Verified directly (not assumed) via both launchers' actual output and a full before/after test-suite
comparison (2569/5-failed -> 2579/0-failed, excluding the pre-existing unrelated slow-test category).
