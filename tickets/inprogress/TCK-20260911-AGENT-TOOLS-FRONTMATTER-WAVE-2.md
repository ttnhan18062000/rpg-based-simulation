---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2
phase: inprogress
date: 2026-09-11
tags: [governance, ai]
---

# TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2

## Title
Least-privilege `tools:` scoping — Wave 2, and define the wave gate that Wave 1 left unmeasurable

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE` shipped Wave 1 (11 read-oriented agent roles) on
2026-09-05 and explicitly deferred Wave 2 (`architecture-reviewer`, `security-reviewer`,
`planner`) and Wave 3 (`implementer`, `parity-updater`). Its design states each wave is "gated on
the prior wave's clean observation window."

**That gate has no operational definition, and with current instrumentation it cannot be
measured.** Verified 2026-09-11:

- Wave 1's ticket references the gate five times but never defines a duration, a "clean"
  criterion, or a signal that would prove it.
- A tool denied by a `tools:` allowlist never executes, so no `PostToolUse` hook fires and no
  `tools.jsonl` row is written. There is no denial record.
- `git grep -lE "denied|denial|permission_denied|tool_denied"` across `tools/agent-monitoring/`
  and `.claude/settings.json` returns **nothing** — no denial concept exists anywhere in the
  monitoring stack.

So "Wave 1's window was clean" currently means only "nobody reported a problem." That is an
advisory gate that cannot fail — the exact pattern this roadmap's own guardrail work exists to
convert into something deterministic. Proceeding to Wave 2 on that basis would be a rubber stamp,
and Wave 3 (`implementer`, `parity-updater`) carries the highest blast radius of all and would
inherit the same unfalsifiable gate.

## Scope
- **Step 0, blocking, before any Wave 2 frontmatter change** — mirroring Wave 1's own precedent of
  a blocking empirical Step 0 (it verified `tools:` was harness-enforced rather than assuming it
  from docs). Define what "clean observation window" means operationally and evaluate Wave 1
  against it. Establish the duration, the signal, and the failure condition explicitly.
- Determine whether a real denial signal can be obtained at all. Candidate approaches to assess,
  not a prescribed answer: compare each Wave 1 agent's post-2026-09-05 tool usage against its
  pre-Wave-1 baseline using the existing `tools/agent-monitoring/agent_tool_usage_baseline.py` —
  an agent that abruptly stopped using a tool it previously used is a candidate denial; or
  determine whether the harness surfaces denials anywhere observable at all.
- If no real signal is obtainable, say so plainly and record the gate as satisfied by
  absence-of-incident, **explicitly labelled as a weak signal** — do not present it as empirical
  verification. An honest weak gate is acceptable; a weak gate described as strong is not.
- Then execute Wave 2 for `architecture-reviewer`, `security-reviewer`, `planner`, following Wave
  1's established method: offline candidate-policy replay per agent against real usage data, the
  5-way "would deny" taxonomy (legitimate-but-rare / obsolete / inappropriate-legacy / accidental
  / unclear-needs-review), and the sizing rule of *smallest confident scope, not theoretical
  minimum*.
- Write the per-agent rollback (single-file frontmatter revert) **before** the wave lands, as Wave
  1 did.

## Out of Scope
- **Wave 3 (`implementer`, `parity-updater`)** — highest blast radius, must land last and only
  after Wave 2's own observation window. Separate future ticket, opened only once this one's gate
  has been evaluated.
- Re-scoping any Wave 1 agent's existing `tools:` list — unless Step 0's analysis surfaces a real
  denial, in which case fixing that specific agent is in scope and the finding must be recorded.
- Building general denial instrumentation as a project in its own right. If Step 0 concludes real
  denial observability is needed and is more than a small addition, file it as its own ticket
  rather than absorbing it here.

### Scope amendment (Investigate, 2026-09-11)
- **A real denial signal exists** — in Claude Code's subagent transcripts
  (`~/.claude/projects/<repo>/<session>/subagents/*.jsonl` + `.meta.json` naming the real
  `agentType`). They record calls made by the agent itself and `No such tool available` errors.
  Machine-local and prunable, so the verdict must state its machine and date range.
- **agent-monitoring's `agent` field is the pipeline phase, not the caller** (`post_tool_hook.py`
  reads it from the sidecar). It overstates, e.g. architecture-reviewer `Edit` 545 vs 5 real. It is
  not a valid gate signal, and Wave 1's scopes were sized from it (follow-on).
- **Step 0 therefore adds a small read-only tool**, `tools/agent-monitoring/subagent_tool_audit.py`,
  so the gate can be re-run for Wave 3 unchanged.
- **Wave 1 verdict (caller-level):** zero failures; 4 agents confirmed, 7 unconfirmed
  (under-exercised, dormant, or never used), listed by name.
- **architecture-reviewer loses `Edit`:** 4 real edits to `src/`/`tests/` during a review.
- Full evidence: `staging_artifacts/TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2/`.

## Acceptance Criteria
- [x] "Clean observation window" has a written operational definition — duration, signal, and
      failure condition — recorded where a future wave can apply it unchanged.
- [x] Wave 1 is evaluated against that definition, with the verdict and its evidence recorded. If
      the signal is weak, it is labelled weak.
- [x] `architecture-reviewer`, `security-reviewer`, and `planner` carry a `tools:` allowlist
      derived from real usage data via the 5-way taxonomy, not from theoretical minimums.
- [x] A documented single-file rollback exists for each of the three, written before the change
      landed.
- [x] `tests/tools/test_wave1_agent_tools_frontmatter.py`'s equivalent guard is extended to cover
      Wave 2, so the scoping is regression-locked rather than convention-only, and its "Wave 2/3 have
      no `tools:`" guard is narrowed to Wave 3.
- [x] `subagent_tool_audit.py` exists with fixture tests, and the Wave 1 verdict records its real output.

## Related Tickets
- `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE` (done) — Wave 1; established the method, the wave
  gating, and the Step 0 precedent this ticket follows.
- `TCK-20260904-AGENT-TOOL-USAGE-BASELINE` (done) — the usage table Wave 1's replay consumed;
  the same source this ticket's gate evaluation should use.
- `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE` (done) — sibling governance milestone (M2).

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  (M1/M3) — the epic this completes the next milestone of.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — item 1; its "Item 1 —
  partial progress (2026-09-05)" paragraph needs updating when this lands.
- `docs/ai/capability_envelope_baseline.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE/` — Wave 1's investigation, replay
  method, and per-agent candidate scopes. Reuse the method; do not re-derive it.

## Related Code Areas
- `.claude/agents/architecture-reviewer.md`, `.claude/agents/security-reviewer.md`,
  `.claude/agents/planner.md`
- `tools/agent-monitoring/agent_tool_usage_baseline.py`
- `tests/tools/test_wave1_agent_tools_frontmatter.py`

## Assumptions / Open Questions
- The central open question is Step 0's: is a real denial signal obtainable, or is
  absence-of-incident the only thing available? Resolve it with evidence before touching any
  frontmatter — the answer determines whether every subsequent wave gate means anything.
- Wave 1's own note that the harness does not hot-reload `.claude/agents/` mid-session (requires
  restart) still applies and affects how any observation window must be interpreted.

## Implementation Notes
Investigate and Plan are complete; see the staging artifacts. Implementation is handed to
`agent-working-implementer`. The per-agent rollback must be written here before Step 4 is committed.

### Step 1 — `subagent_tool_audit.py`
Added `tools/agent-monitoring/subagent_tool_audit.py` (read-only, stdlib + PyYAML only). Reads
Claude Code's own subagent transcripts under `~/.claude/projects/<repo-slug>*/<session>/subagents/
agent-<id>.{meta.json,jsonl}` (repo-slug derived from the *main* repo root, stripping any
`.claude/worktrees/<name>` suffix, so it correctly covers every worktree of this repo, not just the
one it runs from). 12 fixture tests in `tests/tools/test_subagent_tool_audit.py` (`tmp_path`
synthetic trees only, never real `.claude/agents/` or real transcripts).

### Step 2 — Gate definition
Written into `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`'s
M3 section, replacing the undefined "clean observation window" phrase with an operational
definition: signal (`subagent_tool_audit.py --since <landing ts>`), failure conditions, the
`confirmed`/`under-exercised`/`dormant`/`never used` labels with the 10-invocation `confirmed`
threshold, the proceed rule (zero failures; weak labels stay open-risk, never folded into
"clean"), and the machine/transcript-pruning limitation stated plainly. Not modified from
investigation.md's own recommendation — Review did not change the threshold.

### Step 3 — Wave 1 verdict, re-run (not copied from investigation.md)
`python3 tools/agent-monitoring/subagent_tool_audit.py --since 2026-09-06T04:09:42Z`, run on
`u24desktop`, 2026-09-11/12 (transcripts_seen: 940, transcripts_skipped_unmatched_or_missing_meta:
185, date_range_covered: 2026-08-31T08:35:47Z to 2026-09-11T10:37:31Z):

| Agent | pre | post | outside-allowlist (post) | no-such-tool (post) | Verdict |
|---|---|---|---|---|---|
| done-checker | 90 | 26 | 0 | 1 (`ListAgents`, session-level disable, pre-existing known case) | confirmed |
| investigator | 60 | 17 | 0 | 0 | confirmed |
| doc-updater | 53 | 17 | 0 | 0 | confirmed |
| test-scoper | 68 | 14 | 0 | 0 | confirmed |
| ticket-scoper | 90 | 3 | 0 | 0 | under-exercised |
| mechanics-auditor | 1 | 3 | 3 (`Agent`) | 0 | under-exercised, investigated below |
| concern-investigator | 54 | 0 | 0 | 0 | dormant |
| spec-document-reviewer, simulation-analyst, world-debugger, world-render-reviewer | 0 | 0 | 0 | 0 | never used |

Differences from investigation.md §3's counts (e.g. done-checker 23→26 post, doc-updater 14→17,
test-scoper 11→14) are explained, not overwritten: this re-run is 1 day later and this session
alone closed 9 more tickets in that window, each dispatching these same Wave 1 agents again — more
elapsed activity, not a discrepancy in the tool. `ticket-scoper`/`mechanics-auditor`/
`concern-investigator`/the 4 never-used agents match investigation.md exactly.

**mechanics-auditor's 3 `Agent` calls investigated, not assumed clean:** all 3 are in one
transcript (`agent-ac7abc41fd34e6ec8.jsonl`) at `2026-09-06T04:13:07Z`–`04:13:37Z`. Its parent
session directory is `8553c310-aa3d-4e2b-ad90-19452165200a`; that session's own transcript's first
real timestamp is `2026-08-29T03:44:08.385Z` — 8 days *before* Wave 1 landed
(`2026-09-06T04:09:42Z`). Confirms (not assumes) the pre-restart-session explanation: `.claude/
agents/` definitions do not hot-reload mid-session, so a session already running before landing
still saw the old, unrestricted `mechanics-auditor.md` 4 minutes after the merge. Zero failures per
the Step 2 rule — proceeding to Step 4.

**Overall verdict: zero failures. 4 confirmed, 2 under-exercised, 1 dormant, 4 never used —
matches investigation.md's expected shape exactly.** Per the Step 2 rule, Wave 2 may proceed;
`ticket-scoper`, `mechanics-auditor`, and `concern-investigator` remain open risk for Wave 3's own
future evaluation, not folded into "clean" here.

### Step 5 — Rollback (written before Step 4 is committed)
Confirmed via `git status --porcelain -- .claude/agents/` immediately before this Step 4 change:
no other uncommitted change sits on any of the three files, so the clean-revert precondition holds
and each is a plain single-file revert:
```
git checkout HEAD -- .claude/agents/architecture-reviewer.md
git checkout HEAD -- .claude/agents/security-reviewer.md
git checkout HEAD -- .claude/agents/planner.md
```

## Test Summary
```
pytest tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_concern_investigator_agent_definition.py tests/tools/test_subagent_tool_audit.py -q
```
71 passed (55 in the extended frontmatter file — 44 pre-existing Wave 1 assertions unchanged plus
11 new Wave 2 assertions; 12 new fixture tests in `test_subagent_tool_audit.py`; the concern-investigator
file's own tests unaffected). All fixture tests use synthetic `tmp_path` trees only — never real
`.claude/agents/*.md` or real `~/.claude/projects/` transcripts, matching this repo's established
convention for structural/architecture tests.

## Files Changed
- `tools/agent-monitoring/subagent_tool_audit.py` (new) -- Step 1, caller-level audit tool
- `tests/tools/test_subagent_tool_audit.py` (new) -- Step 1, 12 fixture tests
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md` --
  Step 2 (gate definition), Step 3 (Wave 1 verdict), Step 7 (Wave 2 landed status update)
- `.claude/agents/planner.md` -- Step 4, one `tools:` line added
- `.claude/agents/architecture-reviewer.md` -- Step 4, one `tools:` line added
- `.claude/agents/security-reviewer.md` -- Step 4, one `tools:` line added
- `tests/tools/test_wave1_agent_tools_frontmatter.py` -- Step 6, Wave 2 candidate-scope +
  forbidden-pair pins added; `_WAVE2_WAVE3_AGENTS`/its test narrowed to `_WAVE3_AGENTS`
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` -- Step 7, item 1's
  Wave 2 landing status update
- `tickets/inprogress/TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2.md` -- this file
- `staging_artifacts/TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2/` -- no changes needed; Investigate
  and Plan were already complete before this Implement pass

## Completion Summary
(filled in at close)
