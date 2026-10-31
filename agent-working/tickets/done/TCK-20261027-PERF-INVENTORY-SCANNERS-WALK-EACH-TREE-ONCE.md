---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261027-PERF-INVENTORY-SCANNERS-WALK-EACH-TREE-ONCE
phase: done
date: 2026-10-27
tags: [performance]
---

# TCK-20261027-PERF-INVENTORY-SCANNERS-WALK-EACH-TREE-ONCE

## Title
Make the perf inventory scanners at least 2x faster: an iterative AST walk, each file parsed once (wall_clock_inventory, hash_callsite_inventory, phase_inventory), with byte-identical output

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P2

## Request Summary
agent-working-planner reported (2026-10-27) that `tools/perf/wall_clock_inventory.py` takes about 8 s per run on an idle host. Its CLI test, `tests/tools/test_wall_clock_inventory.py::test_cli_runs_are_byte_identical_and_do_not_import_src`, is owned by agent-working. That test still takes 58.55 s against its 60 s budget under loadavg ~5.6, even after `TCK-20261027-WALL-CLOCK-CLI-TEST-RUNS-THE-TOOL-FOUR-TIMES-NOT-SIX` cut it from six tool runs to four. agent-working asked for about a 2x speed-up.

perf-planner profiled `build_report` with cProfile on 2026-10-27, at loadavg 5.4 (812 files, 39.8 s under the profiler):
- `hash_callsite_inventory._dfs` (recursive `yield from`): 24.3 s cumulative, 24.5 M calls. Each node is re-yielded through every generator frame above it, so a walk costs O(nodes × depth), not O(nodes).
- Each module's tree is walked about 6 times: `_parent_map` (which also calls `_children` again for every node), `_import_aliases`, `_psutil_instances`, the two loops in `scan_source`, and `_imports_of`.
- `ast.parse`: 4.5 s for 1122 parses. Of those, 310 are re-parses, because `scan_source` parses the text again after `build_report` has already parsed it.

## Scope
1. Replace `_dfs` in `tools/perf/hash_callsite_inventory.py` with an iterative preorder walk using an explicit stack. It must yield the same nodes in the same order. `_parent_map` builds its map in that same single pass.
2. Pass the tree `build_report` already has into `scan_source` (an optional argument, so callers that pass only the text keep working). No second `ast.parse`.
3. Where it is cheap, collect the aliases, psutil instances and imports in one pass per tree. Don't restructure beyond what the measurement needs.
4. `phase_inventory.py` uses the same helpers and gets the speed-up for free. Check that its output is unchanged too.

## Out of Scope
- Changing any report field, ordering or wording.
- `tests/tools/test_wall_clock_inventory.py` (agent-working owns it) and its time budget.
- A combined json+md mode. This ticket asks for speed only; a new CLI flag would be a separate decision.

## Acceptance Criteria
- Byte-identical output from before and after on origin/main's tree for all three tools: `wall_clock_inventory.py --format json` and `--format md`, `hash_callsite_inventory.py`, and `phase_inventory.py` in each of their output modes (read their argparse in the source, never run them with `--help`). `--check` against the committed reports passes.
- On the same host and in the same window, alternating before/after runs (3 each) show `wall_clock_inventory.py --format json` at least 2x faster by median.
- The existing tests pass: `tests/tools/test_wall_clock_inventory.py`, plus the hash_callsite and phase_inventory tests under `tests/tools/` and `tests/unit/perf/`.
- No new dependencies.
- The PR names agent-working-planner, who confirms the CLI test's timing there.

## Related Tickets
- `TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY` (the tool)
- `TCK-20261027-WALL-CLOCK-CLI-TEST-RUNS-THE-TOOL-FOUR-TIMES-NOT-SIX` (agent-working's test-side cut)

## Related Docs
- `docs/performance/wall_clock_inventory.md` (its generated block must not change)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/perf/hash_callsite_inventory.py` (`_dfs`, `_children`, `_parent_map`, `_import_aliases`)
- `tools/perf/wall_clock_inventory.py` (`scan_source`, `build_report`, `_imports_of`)
- `tools/perf/phase_inventory.py`

## Assumptions / Open Questions
- The profile was taken under load with cProfile overhead. The 2x target is to be confirmed on an idle host. If the iterative walk alone gets past 2x, steps 2 and 3 are still worth doing, since they are cheap.

## Implementation Notes
- The cProfile read in the ticket overstated the recursive `_dfs`: with the iterative walk alone, wall_clock_inventory went from about 8.1 s to 7.9 s (no gain). The real cost was `ast.iter_child_nodes` (pure Python) called for each node about five times per module, plus a second `ast.parse` and a full walk of all 798 modules only to find imports.
- `tools/perf/hash_callsite_inventory.py`: `_dfs` is an explicit-stack preorder; children are computed once per node (`_CHILDREN`, inline `_child_nodes` skipping the field-less operator/context nodes `Load`, `Add`, `And`, `Eq`, ...) and each module's preorder list is kept (`_MODULE_ORDER`); both caches are dropped by `forget_children()` at the end of `build_report` and after a standalone `scan_source`. `_parent_map` is built from the same walk. `scan_source` takes an optional `tree`.
- `tools/perf/wall_clock_inventory.py`: `build_report` passes the tree it already parsed to `scan_source` (no re-parse); `_imports_of` walks statements only (`_statements`), because an import is a statement; an unused local was dropped.
- `phase_inventory.py` has its own small walker and was not changed (0.1 s).

## Test Summary
- Byte-identical output, before vs after on the same tree (this branch: origin/main plus fingerprint Part 1, so `src/` differs from main by the new `src/perf/dependency_fingerprint.py` only): `wall_clock_inventory.py --format json` and `md`, `hash_callsite_inventory.py --format json` and `md`, `phase_inventory.py --format json` and `md` (cmp, all identical); `--check` against the committed `docs/performance/{wall_clock,hash_callsite,phase}_inventory.json` passes for all three.
- Speed (`wall_clock_inventory.py --format json`, alternating before/after, 3 each, load1 1.2-1.3, wall s): before 7.84, 8.12, 8.05; after 4.10, 3.39, 3.85. Median 8.05 vs 3.85 = 2.09x (user CPU median 7.66 vs 3.63 = 2.1x). The margin over 2x is small and the host was not idle (loadavg 1.2-1.3), so it is a median of three, not a distribution. The earlier iterations measured 1.45x, 1.9x and 1.9x.
- Tests: `tests/tools/test_wall_clock_inventory.py` 16 passed in 23 s (the CLI byte-identical test was 58.55 s against its 60 s budget before this change); `tests/tools/test_hash_callsite_inventory.py` and `test_phase_inventory.py` 49 passed. `codebase.health check` OK, 0 new, 0 worse.

## Files Changed
- tools/perf/hash_callsite_inventory.py
- tools/perf/wall_clock_inventory.py

## Completion Summary
Done as a hotfix. Output is byte-identical for all three tools and `wall_clock_inventory.py --format json` is 2.09x faster by median of three alternating runs. agent-working-planner to confirm the CLI test's timing in the PR (named there per the AC).
