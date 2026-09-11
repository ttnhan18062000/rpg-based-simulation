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
- [ ] "Clean observation window" has a written operational definition — duration, signal, and
      failure condition — recorded where a future wave can apply it unchanged.
- [ ] Wave 1 is evaluated against that definition, with the verdict and its evidence recorded. If
      the signal is weak, it is labelled weak.
- [ ] `architecture-reviewer`, `security-reviewer`, and `planner` carry a `tools:` allowlist
      derived from real usage data via the 5-way taxonomy, not from theoretical minimums.
- [ ] A documented single-file rollback exists for each of the three, written before the change
      landed.
- [ ] `tests/tools/test_wave1_agent_tools_frontmatter.py`'s equivalent guard is extended to cover
      Wave 2, so the scoping is regression-locked rather than convention-only, and its "Wave 2/3 have
      no `tools:`" guard is narrowed to Wave 3.
- [ ] `subagent_tool_audit.py` exists with fixture tests, and the Wave 1 verdict records its real output.

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

## Test Summary
(filled in during implementation)

## Files Changed
(filled in during implementation)

## Completion Summary
(filled in at close)
