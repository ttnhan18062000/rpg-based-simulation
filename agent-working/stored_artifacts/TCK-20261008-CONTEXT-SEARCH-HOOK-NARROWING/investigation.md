---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING
artifact_type: investigation
tags: [workflows, agent-monitoring]
---

# Investigation

- The inline hook in `.claude/settings.json` (matcher `Bash`, first entry) fires `context-search: Have you called search_docs ...` on any command whose text contains `grep`, `rg `, `ripgrep`, `find `, `fd `, `ack ` or `ag `, whatever the command does and whatever the session already did. It adds a graphify sentence only when `graphify-out/graph.json` exists.
- **Measured on the committed W41 tools shards** (28 sessions, 2211 Bash rows; `input_summary` is cut at 120 characters, so a target past that point is invisible to both counts): the current rule would have fired on **482** Bash calls; the new rule (an investigation read of `src/` or `docs/` before this session's first `search_docs`) fires on **49**; 23 of those 49 were also hit by the old rule, the other 26 are `cat`/`sed -n`/`head` reads the old pattern never matched. That is a **90% reduction** (482 to 49) while adding the reads the old rule missed.
- Session state: the tools shard rows carry `session_id` and the tool name, but a hook cannot cheaply read a 270k-row corpus; the session transcript (`transcript_path` in the hook payload) is the direct source. A scan of the largest local transcript (151 MB) takes 0.3 s, and a found answer is cached in a sentinel file (`$TMPDIR/context_search_hook_<session>`) so later calls cost one stat. A session that never calls `search_docs` rescans on each matching read only (about 49 such calls in a week), never on ordinary commands.
- Fail-open choices: no transcript path, unreadable file or any exception means no reminder. A tool name that only appears in a tool list (not in a `tool_use` block) is not counted as a call.
