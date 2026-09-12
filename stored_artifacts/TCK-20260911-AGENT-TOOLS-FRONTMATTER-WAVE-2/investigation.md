---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2
artifact_type: investigation
tags: [governance, ai]
---

# Investigation — TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2

Step 0 evidence, gathered 2026-09-11 on this machine (u24desktop). `search_docs` has no index in this
worktree; duplicate-work detection used the `docs/REGISTRY.yaml` fallback and Wave 1's stored artifacts.
Wave 1 landed on `main` at **2026-09-06T04:09:42Z** (PR #132, `cf703779`) — not 2026-09-05 as the
Wave 1 ticket's close date suggests. Every "post-landing" figure below uses that timestamp.

## 1. The ticket's premise is partly wrong: a denial signal exists

The ticket says a denied tool leaves no record. That holds for agent-monitoring, but **not for Claude
Code's own subagent transcripts**:

- Every subagent run is stored as `~/.claude/projects/<repo-slug>/<session>/subagents/agent-<id>.jsonl`,
  with a sibling `agent-<id>.meta.json` that names the real **`agentType`**. 1095 transcripts exist
  for this repository on this machine.
- A tool call that fails because the tool is not available is recorded verbatim as a `tool_result`
  error, e.g. `<tool_use_error>Error: No such tool available: ListAgents. …</tool_use_error>`
  (done-checker, 2026-09-06T04:55:07Z).

Wave 1's own Step 0 found that tools absent from `tools:` are **not offered** to the model at all, so
the usual failure mode is not an attempted-and-refused call but a model that silently lacks the tool.
Transcripts catch both forms that can be observed: an explicit "No such tool available" error, and
calls made outside the allowlist (which would show enforcement is not working).

**Limits, stated up front:** transcripts are local to one machine (the second environment,
`vboxuser`, is invisible from here). They can be pruned by Claude Code's transcript-retention cleanup.
They are not checked into the repo. They are good evidence for a gate evaluated on this machine, not a
durable, shared record.

## 2. agent-monitoring's `agent` field is the pipeline phase, not the caller

`tools/agent-monitoring/post_tool_hook.py:122-126` takes `agent` from the run sidecar
(`.claude/current_run[.<session>]`) — the phase the orchestrator last announced. Every tool call made
while that sidecar is current is attributed to that agent, including the orchestrator's own calls.

Evidence of the size of the distortion:

| Agent | Tool | tools.jsonl (phase-attributed) | Transcripts (caller-level) |
|---|---|---|---|
| architecture-reviewer | Edit | 545 | **5** |
| architecture-reviewer | Write | 112 | 10 |
| planner | AskUserQuestion | 15 | **0** |

The 24 post-landing tools.jsonl rows that looked like Wave 1 agents calling tools outside their
allowlists (test-scoper `Edit` ×20, investigator `SendMessage`/`TaskOutput`, doc-updater
`SendFeedback`) come from **two sessions whose rows span every pipeline agent** — orchestrator sessions
(`7276a580`, `1666c9a3`). They are attribution artifacts, not enforcement failures.

Consequence beyond this ticket: `tools/agent-monitoring/agent_tool_usage_baseline.py` reads this field,
and **Wave 1's candidate scopes were derived from it**. Those scopes are therefore likely broader than
the agents' real usage (see §6).

## 3. Wave 1 evaluated at caller level

| Wave 1 agent | Invocations pre | Invocations post | Post tool calls | Calls outside allowlist | Verdict |
|---|---|---|---|---|---|
| done-checker | 90 | 23 | 796 | 0 | confirmed |
| investigator | 60 | 17 | 762 | 0 | confirmed |
| doc-updater | 53 | 14 | 376 | 0 | confirmed |
| test-scoper | 68 | 11 | 223 | 0 | confirmed |
| ticket-scoper | 90 | 3 | 87 | 0 | under-exercised |
| mechanics-auditor | 1 | 3 | 168 | 3 (`Agent`) | under-exercised; see below |
| concern-investigator | 54 | 0 | 0 | 0 | dormant (only runs via `create-tickets`, which has not run since 2026-09-06) |
| spec-document-reviewer, simulation-analyst, world-debugger, world-render-reviewer | 0 | 0 | 0 | 0 | never used |

- **No capability-shortfall denials of an allowlisted agent.** The one post-landing "No such tool
  available" error (done-checker, `ListAgents`) names a tool that **is** in done-checker's allowlist.
  The message says it was disabled for the whole session, so it is a session-level setting, not the
  `tools:` field. The four other permission errors found are auto-mode classifier denials from before
  landing (2026-09-01/03) and unrelated to `tools:`.
- **mechanics-auditor's 3 `Agent` calls** happened at 04:13Z, four minutes after the merge, in a session
  that had started earlier. Agent definitions do not hot-reload mid-session (Wave 1 investigation), so
  this is consistent with a pre-restart session, not an enforcement gap. It should be re-checked in the
  next evaluation rather than assumed.
- **Event-level signal agrees.** Post-landing `events.jsonl` rows for Wave 1 agents: 43, of which 2 are
  `failed` — both real work findings (a pinned-adjacency regression, a disclosure gap), neither
  tool-related.

Verdict: **Wave 1 is clean for the 4 agents with real post-landing volume. For the other 7 it is
unconfirmed, not clean.** Honest label: strong for 4, absent for 7.

## 4. Wave 2 caller-level usage and 5-way classification

Source: transcripts, all history (earliest 2026-08-12 on this machine).

**planner** — 100 invocations. Bash 1124, Read 882, Edit 172, Write 77, ToolSearch 32,
search_docs 12, Agent 2, Monitor 2, TaskStop 1, Skill 1.
- Edit/Write: every target is `staging_artifacts/<ticket>/…` except one scratchpad write — **core**.
- Agent (`fork`, 2), Monitor + TaskStop (waiting on and stopping its own background pytest), Skill
  (`workflow-authoring` reference) — **legitimate-but-rare**.
- tools.jsonl also shows `AskUserQuestion`, `TaskUpdate`, `TaskCreate`, `ListAgents`, `SendMessage` for
  planner. None appear at caller level, so they are **phase-attribution artifacts** and are excluded.

**architecture-reviewer** — 181 invocations. Bash 2309, Read 711, ToolSearch 58, Write 10,
search_docs 7, TaskStop 6, SendMessage 5, Edit 5, Agent 4, Skill 4, Artifact 1.
- Write (10): 9 scratchpad verification scripts, 1 scratch file at a worktree root — **legitimate**.
- **Edit (5): 4 of 5 modified `src/content/…` and `tests/unit/con…` during the SPECIES-INTELLIGENCE-TIER
  re-review (2026-09-01) — inappropriate-legacy.** A reviewer changing the code it is reviewing
  undermines the review, the same judgment Wave 1 made for test-scoper's `Edit`. The fifth was a
  scratchpad edit, which `Write` covers.
- SendMessage (answering its parent as a background agent), TaskStop (its own background tasks), Agent
  (`Explore`), Skill (`workflow-authoring`) — **legitimate-but-rare**.
- Artifact (1, `{"action": "status"}`) — **accidental**.

**security-reviewer** — 3 invocations. Bash 22, Read 8, ToolSearch 1. **Too little data for a
usage-derived scope.** It is a report-only reviewer, like Wave 1's mechanics-auditor and
spec-document-reviewer, so the scope must be **policy-derived** and labelled as such.

## 5. Constraints carried from Wave 1

- No hot reload: a changed `tools:` line applies only to sessions started after the change.
- `tests/tools/test_wave1_agent_tools_frontmatter.py` contains `_WAVE2_WAVE3_AGENTS` and a test asserting
  those five agents have **no** `tools:` field. Landing Wave 2 makes that test fail by design. It must be
  narrowed to Wave 3 in the same change, not deleted.
- Revert: each Wave 2 file is a single added `tools:` line. `git checkout HEAD -- <file>` is a clean
  revert only if no other uncommitted change sits on that file (verify at implementation time).

## 6. Findings for follow-on tickets (not this ticket's scope)

1. **Wave 1 scopes were sized on phase-attributed data.** Example: done-checker's allowlist has 22
   tools. Re-derive at caller level and tighten where the transcripts show no use.
2. **tools.jsonl `agent` cannot identify callers.** Either document it as "phase" and stop using it for
   per-agent capability questions, or record the real caller. Whether the PostToolUse hook payload
   carries subagent identity was not established here.
3. **Wave 3** (`implementer`, `parity-updater`), after Wave 2's window.
