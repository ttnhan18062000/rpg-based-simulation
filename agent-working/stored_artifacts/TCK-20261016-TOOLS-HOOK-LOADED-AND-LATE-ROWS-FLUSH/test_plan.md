---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH
artifact_type: test_plan
tags: [agent-monitoring, hooks, data-quality]
---

# test_plan — TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH

- Scope 1: fixture settings with the PostToolUse monitoring hook -> no line; without it -> exactly one line; settings missing or
  malformed -> no line, no exception; the existing freshness tests stay unchanged.
- Scope 2 (c): fixture main checkout with `main.tools.jsonl` rows for week Wnn and a canonical `tools.jsonl`: after week-close the
  canonical file has the rows once, in order; a second run adds nothing (dedup by session_id+ts); a torn last line is skipped, not
  fatal; a non-`main` branch shard is untouched; no `main.tools.jsonl` -> no change and no message.
- Closer message test: week-close prints one line naming the number of swept rows.
- Existing week-close, consolidation and post_tool_hook tests pass unchanged (targeted files only; no full tests/tools run
  without a lead slot).
- Proof of measurement: `measure.py` re-run after the change; the before/after table goes into the Completion Summary.
