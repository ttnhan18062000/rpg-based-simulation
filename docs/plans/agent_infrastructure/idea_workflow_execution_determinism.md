---
status: idea
layer: ai
authority: P2
audience: developer
maturity: idea
date: 2026-07-10
tags: [idea, agent-infrastructure, observability, determinism]
---

# Idea: The Orchestrator Itself Is Narrated, Not Executed — Close the Gap One Level Above the Sub-Agents

> **Maturity: IDEA — not scheduled.** Raised 2026-07-10 as a follow-on observation while reviewing
> [`idea_agent_bookkeeping_determinism.md`](idea_agent_bookkeeping_determinism.md) and its epic
> ([`TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC`](../../../tickets/todos/agent-bookkeeping-determinism/TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC.md))
> against how popular agent-orchestration tooling (Temporal, LangGraph, Airflow-style DAG engines)
> actually executes workflows. Distinct from, and one architectural layer above, that epic — not a
> child of it, and not folded into its scope.

---

## Problem

The sibling epic fixes a real, reproduced bug: sub-agents were trusted to literally execute a
copy-pasted "Step 0b" bash snippet (`.claude/current_run` sidecar registration) as their first
action, and when one skipped it, `tool_call_count`/`cost_proxy_score` silently zeroed with no error.
The fix moves that mechanical step from the sub-agent's prompt to the orchestrator's own `bash()`
call, on the reasoning that the orchestrator "already knows `run_id` and the upcoming `seq`" and can
just write the sidecar itself, deterministically.

That reasoning implicitly assumes the orchestrator *is* deterministic — a real program executing
real code. **It is not, in this repo today.** Every `.claude/skills/{implement-ticket,implement-epic,
create-tickets}/SKILL.md` file says the same thing explicitly:

> "**Do not call the Workflow tool — it is not available.** Execute the workflow directly: 1. Read
> `.claude/workflows/implement-ticket.js` in full before doing anything else. 2. Execute each phase
> block in order, translating JS constructs to tool calls..."

`.claude/workflows/*.js` is never run by a JavaScript engine. It is prose-shaped pseudocode that an
LLM — the same *kind* of actor as the sub-agents whose fallibility the sibling epic diagnosed — reads
once per invocation and manually re-derives into a sequence of real tool calls: `Agent()` for each
phase, `Bash()` for each static pre-check, `pushEvent()`-equivalent bookkeeping, gate checks, the
whole `writeMonitoring` block. Nothing enforces that this translation is complete or in the right
order except the narrating LLM's own diligence in that single pass.

**This was not hypothetical this session — it happened twice, at the exact layer this idea is about:**
1. While manually orchestrating `TCK-20260710-SECURITY-REVIEWER-AGENT-DOC`, the Step 0b
   sidecar-registration instruction was omitted from all 5 agent prompts issued — the bug that
   produced [`idea_agent_bookkeeping_determinism.md`](idea_agent_bookkeeping_determinism.md) in the
   first place. That bug was a sub-agent-layer symptom, but its root cause — an LLM narrator
   forgetting a mechanical step it was supposed to always include — is exactly the failure mode this
   idea is about, just observed one level down.
2. While manually orchestrating `TCK-20260710-EPIC-STALENESS-CHECK`, the `done-checker` phase caught
   the orchestrating session's own omission: `## Test Summary` was never written to the ticket file,
   and `## Files Changed` was left empty, on the *first* Verify pass — a real, live instance of the
   top-level narrating LLM skipping a mechanical bookkeeping step the workflow spec required, caught
   only because a downstream gate happened to check for it, not because anything enforced the
   omission couldn't happen.

Compounding this: per the C2 investigation for the sibling epic, **no automated test harness exists
for `.claude/workflows/*.js` at all** ("no `*.test.js` under the repo outside `venv/`/`node_modules`
... any change to Step 0 blocks in these workflow files can only be verified by live/manual workflow
execution or code review, not automated pytest"). This is not an oversight — it is the direct,
structural consequence of the workflow not being real, testable code. You cannot unit-test a
narration.

---

## Idea

**This is not immediately fully fixable** — the skill files are explicit that a real `Workflow` tool
execution surface "is not available" in this harness today. This idea is therefore split into a
long-horizon aspiration (blocked on platform capability, not on this repo's choices) and a
near-horizon mitigation (actionable now, without any new execution surface).

### Long-horizon: execute, don't narrate

If/when a genuine workflow-execution surface becomes available in this harness (a real
`Workflow` tool, or a Claude Agent SDK `tool_runner`-style agentic loop that can run real
TypeScript/Python and call tools from within it), `.claude/workflows/*.js` should be ported to run
*as actual code* under that runtime — phase sequencing, gate branching, and `writeMonitoring` calls
executed deterministically by the runtime, with sub-agent `Agent()` calls as the only place genuine
LLM judgment enters the loop. This closes the gap for good, the same way the sibling epic closes it
for sub-agents: by making the mechanical parts un-skippable rather than trusting a narrator to
remember them. **Explicitly not actionable today** — flagged here so the intent isn't lost, not as
a task to schedule now.

### Near-horizon: a workflow-conformance self-check (actionable now)

Every workflow file already exports a `meta.phases` array — a declarative list of every phase the
workflow is supposed to execute (`{ title, detail }` pairs; e.g. `implement-ticket.js`'s `meta.phases`
lists Scope/Investigate/Plan/.../Finalize). And every phase already pushes an event to
`agent-monitoring/events.jsonl` with a `phase` field. These two things are never cross-checked against
each other today.

Add a static verifier — `tools/gate_checks/workflow_meta_conformance.py`, mirroring the existing
`expected_subsystems_for_files`/`run_finalize_selfcheck` precedent shape — that, given a completed
run's `run_id`, parses the workflow's `meta.phases` list (from the `.js` source; a small regex/AST-lite
extraction, not a full JS parser) and cross-references it against that run's actual `events.jsonl`
entries. Flag any phase declared in `meta.phases` with **zero** matching events — a phase the
narrating LLM silently skipped entirely, not just under-instrumented. This is the direct structural
analog of `parity_updater_static.py`'s `cross_reference_touched` (which already catches "a `src/`
file mapped to a ledger subsystem had no corresponding ledger touch" the same way) — applied one
layer up, to phases instead of files.

This does not make the orchestrator deterministic. It makes a *specific, cheap, high-value class of
its failures* — an entire phase silently vanishing — detectable after the fact, the same way
`done-checker`'s static pre-check already makes "did Finalize actually move the ticket" detectable
rather than trusted. It would have caught neither of this session's two reproduced incidents directly
(both were sub-ticket-level omissions, not missing phases) — but it closes the *next* rung of the same
ladder: a workflow silently skipping an entire phase (e.g. Parity, Security-Review) with no event at
all, which today would be invisible unless someone happened to notice the gap in `events.jsonl` by
eye.

---

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `.claude/workflows/{implement-ticket,implement-epic,create-tickets}.js`'s `meta.phases` | Already a declarative source of truth for "what phases should exist" — just never read by anything except a human/LLM eyeballing the file |
| `agent-monitoring/events.jsonl` | Already has the `phase` field needed for cross-reference — no schema change required |
| `tools/gate_checks/parity_updater_static.py`'s `cross_reference_touched` | Direct structural precedent: "expected mapping vs. actual diff" cross-reference, applied to files→ledger there, phases→events here |
| `tools/gate_checks/done_checker_static.py`'s `run_finalize_selfcheck` | Same "verify the narrated steps actually landed" philosophy, applied post-Finalize rather than mid-run |
| [`idea_agent_bookkeeping_determinism.md`](idea_agent_bookkeeping_determinism.md) (sibling, SCHEDULED) | That epic fixes sub-agent-layer mechanical-step reliability; this idea is the same principle one layer up, at the orchestrator/narrator layer — related, not a duplicate, and deliberately not folded into that epic's scope |

---

## Open Questions

- Is a real `Workflow`/tool-runner execution surface plausible on any roadmap for this harness, or is
  "an LLM narrates a `.js` spec into tool calls" the permanent shape of this system? Genuinely
  unknown from inside this repo — the long-horizon section above is written to survive either answer
  without needing to be rewritten.
- Should a missing-phase-event finding from the proposed conformance check be advisory (a nudge,
  like `retro_nudge_hook.py`) or a hard block at Finalize? CLAUDE.md's Hard Rule that "monitoring
  write failure must never fail the workflow" governs *monitoring writes*; a silently-skipped phase
  is arguably a workflow-integrity failure, not a monitoring-write failure — this distinction should
  be decided deliberately if this idea is ever scheduled, not defaulted either way.
- Should this be scoped as its own epic when scheduled, given it operates one architectural layer
  above `TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC` (orchestrator-as-narrator vs.
  sub-agent-as-worker), or treated as a fourth child of that same epic? Leaning toward "own epic" —
  named here as an open question rather than decided unilaterally.

---

*Raised: 2026-07-10, as a direct follow-on to reviewing the bookkeeping-determinism idea/epic against
popular agent-orchestration design (orchestrator-workers pattern, Temporal/LangGraph-style
execute-don't-narrate workflow engines), and confirmed live by two reproduced incidents in this same
session at the orchestrator-narration layer itself. Not yet scoped as a ticket.*
