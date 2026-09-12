---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2
artifact_type: test_plan
tags: [governance, ai]
---

# Test Plan — TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2

## Step 1 — `subagent_tool_audit.py` (fixture-based, `tmp_path` projects dir)

Build a fake `projects/<slug>/<session>/subagents/` tree with hand-written `.meta.json` + `.jsonl`
pairs.

- Tool calls are counted under the `.meta.json` `agentType`, not under anything in the transcript body.
- Invocation count = one per transcript; split before/after `--since` by the transcript's first timestamp.
- A call to a tool outside the agent's `tools:` list after `--since` is reported; one before `--since`
  is not.
- A `tool_result` with `is_error` and `No such tool available: X` is reported, with agent and tool name.
- An agent with no `tools:` line reports usage but no outside-allowlist section.
- Malformed JSON lines and a transcript missing its `.meta.json` are skipped, not fatal.
- Read-only: fixture file mtimes and contents unchanged after a run.
- Output states the projects root and date range covered.

## Step 3 — Wave 1 verdict

Record the tool's real output (JSON) with the verdict. Check it against investigation.md §3. Any
difference must be explained, not overwritten.

## Step 6 — frontmatter regression lock

- Each Wave 2 agent's `tools:` equals its pinned list exactly (order-insensitive).
- Every pinned exclusion pair is absent.
- `implementer` and `parity-updater` still have no `tools:` field.
- All existing Wave 1 assertions still pass unmodified.

## Regression

```
pytest tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_concern_investigator_agent_definition.py tests/tools/test_subagent_tool_audit.py -q
```

(`test_subagent_tool_audit.py` is the new module from Step 1.)

## Manual, after merge (recorded, not automated)

In a **new** session started after the merge: dispatch `architecture-reviewer` once and confirm from
its transcript that `Edit` is not offered, the same method as Wave 1 Step 0 Method A.
