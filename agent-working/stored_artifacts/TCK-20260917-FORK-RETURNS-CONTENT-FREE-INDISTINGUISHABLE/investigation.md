# Investigation — TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE

## Method

Before writing any check against `tool_response`'s shape for an `Agent` call — explicitly flagged
in this ticket's own Assumptions section as unverified — the shape was confirmed against real, live
payloads rather than assumed from the hook source.

1. Temporarily instrumented `tools/agent-monitoring/post_tool_hook.py`: for `tool_name=="Agent"`,
   appended `{"type": type(tool_response).__name__, "value": tool_response}` to a scratch file
   outside the repo (`/tmp/agent_tool_response_capture.jsonl`), wrapped in its own `try/except` so it
   could never affect the hook's real behavior even if something went wrong. This instrumentation
   was never committed.
2. Dispatched two probe agents to trigger the hook with real `Agent` tool calls:
   - Probe 1: `subagent_type: "fork"`, prompt "Do nothing except respond with exactly the single
     word: OK".
   - Probe 2: plain `Agent()` call (no `subagent_type`), same prompt.
3. Read the captured payloads after each probe completed.
4. Reverted the instrumentation completely (`git checkout -- tools/agent-monitoring/post_tool_hook.py`)
   and deleted the scratch file, before drawing any conclusion or writing any real change.
5. Dispatched a third probe (`subagent_type: "fork"`, prompt "Respond with exactly:
   PROBE_TWO_DONE") to check whether the first fork's own zero-`SubagentHandback` result was
   incidental or reproducible.
6. Cross-checked findings 2 and 3 against the real `agent-monitoring/data/2026-W38/tools.jsonl`
   corpus directly (`grep '"tool":"SubagentHandback"'`), rather than relying only on the temporary
   capture.

## Results

**Probe 1 and 2 (captured `tool_response` for `tool_name=="Agent"`), identical shape both times:**

```json
{"isAsync": true, "status": "async_launched", "agentId": "<id>", "description": "<...>",
 "resolvedModel": "claude-sonnet-5", "prompt": "<...>", "outputFile": "<path>",
 "canReadOutputFile": true}
```

No field carries the eventual answer. This directly contradicts the ticket's own Scope claim that
`post_tool_hook.py` "already receives `payload["tool_response"]`... The needed data is in hand at
the hook and thrown away."

**Corpus check for `SubagentHandback` rows:** exactly one row in `2026-W38/tools.jsonl` at the time
of checking, dated `2026-09-19T06:59:47Z`, with `input_summary` beginning
`"{'message': 'OK\\n\\nNote: I did not start any background..."` — matching Probe 2's own returned
text verbatim. A second real row exists from an earlier, unrelated non-fork dispatch on
`2026-09-18T03:56:11Z`. Probe 1 (the fork) produced no corresponding row.

**Probe 3 (second fork probe, isolated re-test):** completed with `tool_uses: 0` per its own usage
report, and its answer text (`PROBE_TWO_DONE`) arrived directly in the task-notification's own
`<result>` field — not via a separate hand-back message, and with no `SubagentHandback` row
appearing in the corpus afterward. This confirms Probe 1's absence of a handback row was not
incidental: a fork can return its answer having made zero tool calls at all, meaning the answer is
delivered as the natural end of the fork's own conversational turn, not as any kind of tool
invocation — so no hook (`PreToolUse`, `PostToolUse`, or `SubagentStop`, all three of which fire
only around tool calls or session-stop events with their own documented, content-free payload
shapes) is structurally capable of observing it.

## Conclusion

The mechanism the ticket asked for is real and buildable, but only for a class of dispatch
(non-fork `Agent()` calls that complete via an explicit `SubagentHandback` tool call) distinct from
the class that produced all three of this ticket's own motivating incidents (forks). See the
ticket's own "Findings" and "Decision" sections for the full writeup and the closure rationale.
