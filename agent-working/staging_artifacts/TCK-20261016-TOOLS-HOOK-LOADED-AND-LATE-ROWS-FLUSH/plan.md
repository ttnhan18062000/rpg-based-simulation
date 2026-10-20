---
status: active
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
2. **Late rows (scope 2), pick one by the numbers.** The gap is one mechanism: main-checkout sessions write `main.tools.jsonl`,
   which no PR carries (investigation finding 3).
   - (a) commit-time reminder: the pre-push advisory already names a dirty shard, but main-checkout sessions do not push through a
     PR branch, so it never fires for them. Not enough.
   - (b) flush at the next hook call: the hook would have to commit or push, which is a second write path and a git write from the
     hottest path. Rejected (the ticket forbids a second write path).
   - (c) **recommended:** have the existing week-close (`tools/agent-monitoring/week_close.py`) sweep `*.tools.jsonl` shards of the
     main checkout whose branch key is `main` into the canonical week file, the way it already consolidates the other shard kinds,
     and tell the closer when it found some. One owner of consolidation, no new writer. Needs: where week-close runs (a worktree
     reaches the main checkout through the git common dir) **[decide]**, and that it dedups by (session_id, ts) so a re-run or the
     side branch's copy cannot double count.
3. **Back-fill is out of scope** (ticket). The side branch `lead-planner-monitoring-shards` holds the W41-W43 copy; this ticket does
   not merge it. **[decide]** whether lead merges it separately so the re-measured coverage can include it.
4. **Re-measure** with `measure.py` after 1-2 and record the numbers beside the 27% (W41: 15/41 committed or local today).
5. Docs: `docs/agent-monitoring/README.md` (where main-checkout rows go), `schema.md` only if a field changes (none planned).
6. Any `.claude/settings.json` change: none planned. If one becomes necessary it goes to the owner as a literal diff first.
