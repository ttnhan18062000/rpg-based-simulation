---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
artifact_type: plan
tags: [agent-monitoring, hooks, data-quality]
---

# plan — TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

Measurement first (done; see investigation.md). Decisions for the planner are marked **[decide]**.

1. **Hook-not-loaded line (scope 1).** Extend `tools/sessions/settings_freshness.py` so the SessionStart freshness line also says
   when this worktree's `.claude/settings.json` has no PostToolUse hook whose command names `post_tool_hook.py`. Report-only,
   one line, no settings.json change. Test with a fixture settings file (hook present: no line; absent: one line; unreadable
   settings: no line and no crash). **[decide]** keep or drop: the data shows no measured case, but the acceptance criteria ask for it.
2. **Late rows (scope 2): option (c), approved by the planner with conditions.** `week_close.py` sweeps the main checkout's
   `*.tools.jsonl` shards keyed `main` into the canonical week file for the week being closed.
   - Locate the main checkout with `git rev-parse --git-common-dir`; its parent is the main worktree. If it is not there, skip with
     one line.
   - Strictly read-only on the main checkout: never truncate, rewrite or stage its `main.tools.jsonl`.
   - Dedup on full-row identity, i.e. `(session_id, ts, tool, tool_use_id when present)`, against rows already in the canonical
     file and within the sweep, so a re-run or the side branch's copy cannot double count.
   - Sweep only the week being closed; skip a torn line; print one line with the swept count.
   - README limits: u24's main checkout is another host and is not swept; an already-closed week only gains rows on a re-close
     (that is back-fill, out of scope).
3. **Back-fill** (merging `lead-planner-monitoring-shards`) is lead's call; the re-measure says which refs it included.
4. **Re-measure** with `measure.py` after 1-2 on whatever is merged, and record the numbers beside the 27%. Finding 4 is stated
   in the Completion Summary: (c) improves row coverage, not duration coverage.
5. Docs: `docs/agent-monitoring/README.md` (where main-checkout rows go, the two limits).
6. No `.claude/settings.json` change planned; if one becomes necessary it goes to the owner as a literal diff first.
