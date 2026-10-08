---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING
phase: done
date: 2026-10-08
tags: [workflows, agent-monitoring]
---

# TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING

## Title

The context-search PreToolUse hook fires on almost every Bash call and says nothing useful; narrow it to investigation reads of src/ and docs/ before search_docs

## Status

DONE

## Tier

standard

## Type

chore

## Priority

P3

## Request Summary

Child 5 of TCK-20261007-EPIC-RETRO-READABILITY-AND-MONITORING-DATA-HYGIENE. The inline hook in `.claude/settings.json` fires its "have you called search_docs" reminder on any Bash command containing `grep`, `rg `, `find ` and similar, including pure data analysis and commit messages, so the reminder carries no information. Owner-approved approach: move the logic into a script and fire only for an investigation read of `src/` or `docs/` before this session's first `search_docs`.

## Scope

New `tools/agent-monitoring/context_search_hook.py` (advisory only, always exit 0, fail open), tests, and the exact replacement hook entry for the owner. The script reads the session transcript (cached in a sentinel file once `search_docs` is found).

## Out of Scope

Editing `.claude/settings.json` (the owner's file). The Agent-matcher context-search hook. Any blocking behaviour.

## Acceptance Criteria

- [x] Firing counts measured on the W41 tools shards, old rule vs new rule, recorded here
- [x] git, gh, python, pytest and make commands produce no reminder
- [x] `grep -rn foo src/` before search_docs produces the reminder; the same command after search_docs does not
- [x] Any exception, or an unreadable session, produces no output and exit code 0
- [x] The exact replacement settings entry is recorded here and in the PR body (Owner step after merge)

## Related Tickets

TCK-20261007-EPIC-RETRO-READABILITY-AND-MONITORING-DATA-HYGIENE, TCK-20260923-CD-PREFIX-ADVISORY-HOOK

## Related Docs

CLAUDE.md (Context Scan)

## Related Stored Artifacts

agent-working/stored_artifacts/TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING/

## Related Code Areas

tools/agent-monitoring/context_search_hook.py, tests/tools/test_context_search_hook.py, .claude/settings.json (untouched)

## Assumptions / Open Questions

`input_summary` in the tools shards is cut at 120 characters, so the measurement under-reads long commands for both rules alike.

## Implementation Notes

Measured on the committed W41 tools shards (28 sessions, 2211 Bash rows): the current inline rule would have fired on **482** Bash calls; the new rule fires on **49** (a 90% reduction), 23 of them also matched by the old rule and 26 being `cat`/`sed -n`/`head` reads the old pattern never matched.

The script classifies a command as an investigation read when a segment (split on pipes, `&&`, `;`, newlines) starts with grep/rg/find/fd/ack/ag/cat/head/tail/less/more/bat/awk or `sed -n`, and a later word is a path under `src/` or `docs/` (relative, `./`, or an absolute path inside this repo). Redirect targets and heredoc bodies are ignored. Session state comes from the transcript: a `tool_use` of `mcp__knowledge-search__search_docs` (or the `knowledge_search.py query` CLI fallback) counts as called; on 151 MB the scan takes 0.3 s and a found answer is cached in `$TMPDIR/context_search_hook_<session>`.

**Owner step after merge:** `.claude/settings.json` is not edited here. Replace the existing first hook entry under the `Bash` matcher in `hooks.PreToolUse` (the one whose command starts `CMD=$(python3 -c ...`) with:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "R=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0; test -f \"$R/tools/agent-monitoring/context_search_hook.py\" || exit 0; cd \"$R\" && python3 tools/agent-monitoring/context_search_hook.py 2>/dev/null || true"
    }
  ]
}
```

## Test Summary

`pytest tests/tools/test_context_search_hook.py`: 31 passed.

## Files Changed

tools/agent-monitoring/context_search_hook.py, tests/tools/test_context_search_hook.py

## Completion Summary

The script and tests are in place and the reminder is ready to be switched on. Turning it on is the owner's one-line settings swap above; until then the old inline hook keeps running unchanged.
