# Test Plan — TCK-20260917-FORK-RETURNS-CONTENT-FREE-INDISTINGUISHABLE

No code was produced, so no unit tests apply. Verification instead focused on two things: that the
premise-check evidence is real (not reasoned about), and that the probing left no trace in
production code.

| Case | Verification |
|---|---|
| `tool_response` shape for `tool_name=="Agent"` is the async-launch confirmation, not return content | Captured directly from two independent live probe dispatches (one fork, one plain `Agent()`), identical shape both times — see `investigation.md` |
| A real, hook-visible signal exists for non-fork dispatches | Found via a real corpus row (`SubagentHandback`, `2026-09-19T06:59:47Z`) whose `input_summary` matches Probe 2's own returned text verbatim, plus one earlier independent row (`2026-09-18T03:56:11Z`) |
| Forks make no `SubagentHandback` call | Two independent fork probes, zero resulting rows in either the temporary capture or the real corpus; the second probe's own `tool_uses: 0` usage report rules out "the first probe just didn't get logged yet" as an explanation |
| The temporary probe instrumentation left no trace | `git diff origin/main -- tools/agent-monitoring/post_tool_hook.py` returns empty — confirmed at closure time, not merely asserted |
| Ticket's Acceptance Criteria correctly reflect nothing was delivered | Each left unchecked with an explicit infeasibility reason, not marked N/A or silently removed |

Executed: `git diff origin/main -- tools/agent-monitoring/post_tool_hook.py` — empty output,
confirming the hook that runs on every tool call in every session is unchanged.
