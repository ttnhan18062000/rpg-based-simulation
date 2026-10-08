---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING
artifact_type: test_plan
tags: [workflows, agent-monitoring]
---

# Test plan

`tests/tools/test_context_search_hook.py` (31 tests): git/gh/python/pytest/make commands, redirects, heredoc bodies, `sed -i`, reads of `tests/`, and a `find .` give no reminder; `grep -rn foo src/`, `rg` and `cat` of `docs/`, `head`, `sed -n`, an env-prefixed grep and a pipeline give the reminder before `search_docs` and none after; a tool name in a tool list is not a call; the CLI fallback counts; the cached answer survives the transcript disappearing; missing session, transcript or command gives silence; `main` prints advisory JSON with no decision field and exits 0, and prints nothing and exits 0 on garbage input or an exception; the script runs as a subprocess.
