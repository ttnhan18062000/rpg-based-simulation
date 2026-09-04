---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-09-04
tags: [ai, agent-monitoring]
---

# Future Options — Preserved, Not Planned

**No tracking ticket. No epic. No experiment specification.** Per the freeze verdict's Bucket-C
rule: these directions are worth preserving as possibilities, but nothing here is committed,
designed, or scheduled. Each is blocked on a **named prerequisite**, not a calendar date — this
doc exists so the full brainstorm stays visible, not to start planning any of it now.

**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, Bucket C, plus the separate
"Not Recommended" list (explicitly rejected, not merely blocked).

## Blocked — revisit when the named prerequisite clears

### Model-based routing for mechanical agents (done-checker, ticket-scoper)

**Blocked on**: `agent_evaluation_foundation_experiment.md` producing a trusted baseline. Do not
start before that experiment's exit criteria are met — there would be no way to detect a quiet
quality regression from routing otherwise. This is a hard sequencing rule, not a soft preference
(the frozen proposal calls this out as the one place a real risk exists if sequencing is ignored:
"Model-routing pilot masking a real quality regression").

**When it clears**: revisit as a Bucket-B experiment (not straight to a ticket) — pilot `model:`
overrides on `done-checker.md`/`ticket-scoper.md` only, A/B against the eval baseline's scoring.

### Task-success-rate metric closing the improvement loop

**Blocked on**: `agent_evaluation_foundation_experiment.md`'s scoring approach proving repeatable
— this metric would extend that scoring, not invent its own.

**When it clears**: extend `tools/agent-monitoring/cost_proxy.py`'s existing before/after
comparison pattern (already used for cost-proxy weight changes) to agent-prompt changes generally.

### Full agent-behavior eval platform

**Blocked on**: the pilot in `agent_evaluation_foundation_experiment.md` proving its signal is
real. Widening sample coverage or defect-class taxonomy before that pilot's exit criteria are met
is exactly the "elaborate benchmark before establishing usefulness" trap the source proposal (§69)
warns against — this is not a bigger version of the pilot, it is a categorically bigger commitment
that needs its own justification once real pilot evidence exists.

**When it clears**: re-scope from the pilot's actual findings, not from this doc's speculation.

### Live Codex provider pilot

**Blocked on**: the provider-portability conformance test (`standalone_items.md`, item 4) existing
and passing — this is the primary prerequisite regardless of pilot objective. Already correctly
sequenced by the repo's own prior design (`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`,
deliberately `BLOCKED` by human decision, not by failure) — this doc does not accelerate that
sequencing, only records it alongside the rest of the brainstorm.

**Two distinct pilot objectives this item could mean** — the existing epic does not yet commit to
which, so both are recorded rather than assuming one:

- **Runtime / contract pilot** — "Can Codex execute the shared orchestration contract correctly?"
  Prerequisite: the conformance test alone. An eval baseline (item 13,
  `agent_evaluation_foundation_experiment.md`) is not required for this objective.
- **Comparative quality pilot** — "Does Codex perform better/worse than the current provider?"
  Prerequisite: the conformance test **plus** item 13's trusted evaluation baseline, since judging
  relative quality needs the same repeatable scoring the eval pilot exists to establish.

**When it clears**: the existing epic's own child tickets resume from where they were paused, once
whichever objective is intended has its prerequisite(s) satisfied.

## Explicitly not recommended (rejected, not merely blocked — re-evaluated independently, not inherited)

These were re-examined during the next-evolution review, not assumed unnecessary because an
earlier document said so:

- **Workflow-engine migration (Temporal/LangGraph)** — the 1:1 agent-call-to-phase ratio measured
  in `implement-ticket.js` confirms the custom orchestrator is lean, not bloated. Reconsider only
  if workflows need distributed, multi-machine execution, which nothing in this repo's usage
  pattern currently requires.
- **A2A protocol adoption** — no separately-deployed agent runtime exists to serve. Reconsider only
  if the Codex pilot goes live and needs cross-runtime coordination beyond the shared monitoring
  schema it already has.
- **Full container/VM sandboxing at the repo level** — a harness-level capability, not something
  this repo can build for itself. Reconsider only if the harness itself ships sandboxed execution
  — adopt that, don't build a parallel one.
- **A general AI-configuration management platform** — Git commit hashes on `.claude/agents/*.md`,
  workflow files, and the orchestration contract already answer "which config version produced
  this result" for every case this repo currently has. Reconsider only if model-routing or a live
  second provider makes config combinations numerous enough that git-blame stops being a
  fast-enough answer.
- **Always-on / event-driven agents** — no production surface, no external event source. Reconsider
  only if the repo gains an external issue tracker or a second concurrent team generating a real
  event stream.
- **A general dangerous-command / command-injection policy** beyond the Bash secret-exposure hook
  in `governance_capability_policy_epic.md` — explicitly out of scope for that hook and not
  designed here either; the freeze pass's own instruction was not to design or commit this without
  evidence the repository's risk profile justifies it. Destructive filesystem/Git commands, Docker
  host-wide operations, remote script execution, suspicious piping, privilege escalation, and
  network exfiltration all remain unaddressed. Reconsider only with its own evidence-backed
  proposal, should a concrete incident or risk assessment ever justify one.

## References

- `roadmap.md` — how this doc relates to the Horizon-0/1/2 committed and experimental work.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` — §"Not recommended for the next evolution",
  Change Inventory `Blocked`/`Reject` rows, §"Post-freeze observations" for the two items the
  freeze pass explicitly declined to resolve now (`graphify-out/`/`knowledge-index/` git-tracking,
  `cost_proxy_score`'s non-dollar-proxy caveat) — those live in
  `telemetry_retention_epic.md`'s M2, not repeated here since they're partially-blocked
  sub-questions rather than whole blocked initiatives.
