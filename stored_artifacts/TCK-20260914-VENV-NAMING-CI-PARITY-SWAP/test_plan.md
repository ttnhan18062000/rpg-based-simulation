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

1. **[x] Executed 2026-09-21.** `.venv/bin/python3 --version` → `Python 3.13.14` (AC #1, PASS).
2. **[x]** Real `search_docs` query via `bash tools/start_search_mcp.sh --test <<< '{"query":
   "damage formula", "top_k": 3}'` → 3 real, non-empty results returned (AC #2, PASS — not just
   server startup).
3. **[x]** `grep -rn "/home/u24desktop/Working/rpg-based-simulation/\.venv[^-]"` across live
   tooling/config (excluding `tickets/done/`, staging/stored artifacts, `.git/`, and the identified
   historical records — `tickets/working_log.csv`, `docs/parity_ledger/`,
   `registries/capability_envelope_registry.jsonl`,
   `docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md`) → **zero** remaining wrong-env
   references. Only hit is `Makefile`'s general-purpose `$(PYTHON3)`, correctly still pointing at
   `.venv` (AC #3, PASS).
4. **[x]** `make knowledge-index-update` ran clean via `.venv-knowledge/bin/python3` (confirmed in
   the command's own echoed output) — 4 files re-embedded, 0 errors. `make mcp-server-test` also
   re-verified clean via the same variable (AC #4-adjacent, PASS).
5. **[x]** `docs/guidelines/agent_working_environment.md`'s table updated to match: `.venv` = 3.13.14
   (CI-matching), `.venv-knowledge` = 3.12.3 (knowledge-only) — matches `--version` reality confirmed
   in step 1 above (AC #4, PASS).

## Regression check: existing test suite

- `tests/tools/test_dashboard_makefile_targets.py` — 1 test genuinely needed updating
  (`test_knowledge_index_targets_use_python3_variable` → renamed and re-pointed at
  `$(PYTHON_KNOWLEDGE)`, extended to also cover `eval-search`/`mcp-server-test`); all 5 tests in the
  file pass after the update.
- `tests/tools/ -k "codebase_health or knowledge or agent_codex_posttool or dashboard_makefile"` — 123
  passed, 7 skipped, 0 failed (post-fix).
- `tests/tools/test_generate_registry.py`/`test_done_checker_static.py`/`test_done_checker_audit.py`/
  `tests/docs/` — 261 passed, 1 skipped, 1 xfailed (1 test deselected: the real-registry drift check,
  expected-stale mid-implementation from this ticket's own in-progress ticket-location move, resolved
  by the registry regeneration at Finalize).

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
