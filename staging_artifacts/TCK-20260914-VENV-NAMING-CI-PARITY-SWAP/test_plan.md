---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260914-VENV-NAMING-CI-PARITY-SWAP
phase: open
date: 2026-09-15
tags: [ai, process-improvement]
---

# Test Plan — TCK-20260914-VENV-NAMING-CI-PARITY-SWAP

This ticket has no automated test suite of its own — it renames host filesystem state and updates
a handful of tracked files that reference it. Verification is the Step 3 checklist in `plan.md`,
run manually immediately after the rename (Step 2), once that step is confirmed and executed:

1. `.venv/bin/python3 --version` → `3.13.x` (AC #1).
2. A real `search_docs` query (not just MCP server startup) returns non-empty results (AC #2).
3. `grep -rn "/home/u24desktop/Working/rpg-based-simulation/\.venv[^-]"` across live tooling/config
   (excluding `tickets/done/`, staging/stored artifacts, `.git/`) returns zero remaining wrong-env
   references (AC #3).
4. `make knowledge-index-update` runs without an import error — proves the Makefile's new
   `PYTHON_KNOWLEDGE` resolution actually works against the renamed env, not just that the variable
   was added.
5. `docs/guidelines/agent_working_environment.md`'s table matches reality (AC #4).

## Regression coverage for Step 1's file edits (before the rename itself)

- `tools/start_search_mcp.sh` — no existing test file for this shell script found; verify by
  reading the diff carefully (absolute path is the one line that matters) rather than inventing a
  test harness for a 20-line launcher script.
- `Makefile` — no existing Makefile test harness in this repo; verify the new
  `PYTHON_KNOWLEDGE` variable's discovery-loop syntax matches the established pattern already used
  for `PYTHON3`/`PYTHON` (same three-way fallback shape), and confirm via `make -n knowledge-index`
  (dry run) that it expands to a sane command before the rename makes the real run possible.
- `docs/guidelines/agent_working_environment.md` — read back after editing to confirm the table and
  every prose reference stay internally consistent (no stale name left in one place while another
  place already reflects the swap).

## What is explicitly NOT tested here

Whether the rename itself is safe to execute at a given moment (no concurrent session mid-command)
is not a testable condition from inside this session — it depends on the live state of other
sessions on the machine at execution time, which is why plan.md defers that decision to the user
rather than a check this test plan could assert.
