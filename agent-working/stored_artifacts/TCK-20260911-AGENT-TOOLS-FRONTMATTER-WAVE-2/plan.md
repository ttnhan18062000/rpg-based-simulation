---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2
artifact_type: plan
tags: [governance, ai]
---

# Plan — TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2

Evidence in `investigation.md`. Order: build the measuring tool, define the gate, evaluate Wave 1,
then land Wave 2. Steps 1–3 must be complete before any `.claude/agents/` file changes.

## Step 1 — Caller-level audit tool

Add `tools/agent-monitoring/subagent_tool_audit.py`: read-only, stdlib-only, JSON output (same shape
conventions as `agent_tool_usage_baseline.py`).

- Input: every `subagents/*.meta.json` under `~/.claude/projects/<repo-slug>*/` (all worktrees of this
  repo). Override the root with `--projects-dir` for tests.
- For each `agentType`: invocation count (one per transcript, dated by its first timestamp) and
  per-tool call counts, split at `--since <ISO timestamp>`.
- For agents with a `tools:` line in `.claude/agents/<name>.md`: every post-`--since` call to a tool
  outside that list, and every `tool_result` error matching `No such tool available`.
- The report states which machine and which date range it covers, since transcripts are local and
  can be pruned (investigation.md §1).

Small and read-only — the kind of addition the ticket keeps in scope, not a general denial
instrumentation project.

## Step 2 — Write the gate definition

In `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md` (M3),
replace "clean observation window" with an operational definition:

- **Signal:** `subagent_tool_audit.py --since <wave landing timestamp on main>`, run on the machine
  where the pipeline runs. agent-monitoring's `tools.jsonl` is **not** a valid signal for this, because
  its `agent` field is the pipeline phase (investigation.md §2).
- **Failure (blocks the next wave):** any post-landing call to a tool outside a scoped agent's
  allowlist in a session started after landing (enforcement not working); any `No such tool available`
  error for a tool not in that agent's allowlist (the agent needed a tool it lacks); or any
  failed/blocked event whose summary attributes the failure to a missing tool.
- **Per-agent label:** `confirmed` (≥ 10 post-landing invocations, no failure), `under-exercised`
  (1–9), `dormant` (0 post, but used before landing), `never used`.
- **Rule:** the next wave may proceed when there are zero failures. `under-exercised` and `dormant`
  agents are listed by name in the next wave's ticket as open risk, never folded into "clean".
- **Minimum duration:** none beyond what the exercise counts imply. Calendar days are a poor proxy;
  invocation counts are what the evidence is made of.

The 10-invocation threshold and "proceed with open risk listed" are recommendations; Review may
change them. If it does, apply the changed rule unchanged to Wave 1 in Step 3.

## Step 3 — Evaluate Wave 1 and record the verdict

Run the Step 1 tool with `--since 2026-09-06T04:09:42Z`. Record the verdict table in the epic doc and
in this ticket's Implementation Notes. Expected from investigation.md §3 (re-run, don't copy): 4
`confirmed`, 2 `under-exercised`, 1 `dormant`, 4 `never used`, zero failures. Name the weak parts
plainly.

Investigate any post-landing outside-allowlist call before proceeding: the known one is
mechanics-auditor's 3 `Agent` calls at 04:13Z. Establish whether its session began before 04:09:42Z,
using the transcript's first timestamp. If it began after landing, that is a failure and stops this
plan.

## Step 4 — Wave 2 frontmatter

Add one `tools:` line to each file's frontmatter. Change nothing else in the files.

| Agent | `tools:` | Basis |
|---|---|---|
| planner | `Bash, Read, Edit, Write, ToolSearch, mcp__knowledge-search__search_docs, Agent, Monitor, TaskStop, Skill` | usage-derived (100 invocations) |
| architecture-reviewer | `Bash, Read, Write, ToolSearch, mcp__knowledge-search__search_docs, Agent, Skill, SendMessage, TaskStop` | usage-derived (181 invocations); **`Edit` excluded** |
| security-reviewer | `Bash, Read, Grep, Glob, ToolSearch, mcp__knowledge-search__search_docs` | **policy-derived** (3 invocations) |

Exclusions and why (from investigation.md §4):
- architecture-reviewer `Edit` — inappropriate-legacy: 4 real edits to `src/` and `tests/` during a
  review. `Write` stays for scratch verification scripts. Residual risk: `Write` can still create a
  file anywhere; `tools:` cannot restrict paths.
- architecture-reviewer `Artifact` — accidental (one status call).
- planner `AskUserQuestion`/`TaskUpdate`/`TaskCreate`/`ListAgents`/`SendMessage` — never called by the
  planner itself; phase-attribution artifacts.

## Step 5 — Rollback, written before the change

Record in this ticket's Implementation Notes, before Step 4 is committed:
`git checkout HEAD -- .claude/agents/<name>.md` for each of the three files. First confirm with
`git status --porcelain -- .claude/agents/` that no other uncommitted change sits on those files; if
one does, write a surgical single-line removal instead (Wave 1's `doc-updater` precedent).

## Step 6 — Regression lock

Extend `tests/tools/test_wave1_agent_tools_frontmatter.py`. Don't add a new file with a process label
in its name.

- Add the three Wave 2 scopes to the pinned candidate table.
- Pin the exclusions: `(architecture-reviewer, Edit)`, `(architecture-reviewer, Artifact)`,
  `(security-reviewer, Write)`, `(security-reviewer, Edit)`, `(security-reviewer, Agent)`.
- Narrow `_WAVE2_WAVE3_AGENTS` and its "no `tools:` yet" test to Wave 3 only (`implementer`,
  `parity-updater`). It will fail as soon as Step 4 lands, and that is expected; narrowing it is part of
  this change, not a gate weakening.

## Step 7 — Docs

- Epic doc M3: gate definition (Step 2), Wave 1 verdict (Step 3), Wave 2 landed with its date.
- `roadmap.md` item 1: update the "partial progress" paragraph.

## Follow-ons to file at close (not in this ticket)

1. Re-derive Wave 1 scopes from caller-level data (investigation.md §6.1).
2. agent-monitoring `agent` field: document it as the pipeline phase, or record the real caller (§6.2).
3. Wave 3, gated on Wave 2 under the Step 2 rule.

## Risks

- **Machine-local evidence.** Pipeline runs on the second environment are invisible. State the machine
  in every verdict.
- **Transcript pruning** can erase the evidence for a window. Run the audit soon after a window
  closes and store its JSON output with the verdict.
- **Hot reload.** Wave 2 applies only to sessions started after the merge. Use the merge timestamp on
  `main`, not the commit time on a branch.
