---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC
artifact_type: investigation
tags: [ai, agent-monitoring, governance]
---

# Investigation — TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC

## Context scan performed
`mcp__knowledge-search__search_docs` (query: "model routing mechanical agents experiment override
pilot done-checker ticket-scoper") and `graphify query` run before file reads, per CLAUDE.md's
Context Scan rule (shared scan covering this ticket and its sibling in the same batch turn). Top
hit: `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md`'s
"Model-based routing for mechanical agents" entry — the direct source for this spec.

## Prerequisite status (confirmed, not re-derived)
`agent_evaluation_foundation_experiment.md` (item 13) — Hypothesis/Baseline/Method/Metrics/Exit/
Kill Criteria doc, executed by `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT` (done 2026-09-07). Read
the frozen spec's own appended `## Results`/`## Decision` sections directly: all 3 Exit Criteria
MET (repeatable scoring, sample quality accepted for the 2 target defect classes, contamination
risk controlled), neither Kill Criterion fired. `bucket_c_future_options.md`'s own text states this
explicitly unblocks item 18: "Blocked on: `agent_evaluation_foundation_experiment.md` producing a
trusted baseline... When it clears: revisit as a Bucket-B experiment (not straight to a ticket) —
pilot `model:` overrides on `done-checker.md`/`ticket-scoper.md` only, A/B against the eval
baseline's scoring."

## Six-section shape source
Read `agent_evaluation_foundation_experiment.md` in full as the template: header block (Tracking
ticket / Source / Roadmap / Priority), "Why this is an experiment, not an epic", Hypothesis,
Baseline, Method (numbered steps), Metrics (tiered, not one global number), Exit criteria, Kill
criteria, Out of scope, References, and (once executed) Results/Decision appended by the executing
ticket. This ticket's spec reuses the same shape but does not add Results/Decision — no execution
happens in this ticket.

## The named risk this spec must make concrete
`bucket_c_future_options.md`: "there would be no way to detect a quiet quality regression from
routing otherwise... the frozen proposal calls this out as the one place a real risk exists if
sequencing is ignored: 'Model-routing pilot masking a real quality regression'." This is not a
generic caution to restate — the spec's Method/Metrics sections must describe a concrete detection
mechanism: comparing the routed-model agent's real output quality (gate verdicts, defect-class
flag rate) against item 13's own baseline scoring for the SAME two agents, using the same
replay/scoring infrastructure item 13 built (`tools/agent_replay/`), so a regression shows up as a
baseline-vs-candidate score delta rather than going unnoticed.

## The two target agents
`.claude/agents/done-checker.md` (13 DoD conditions verification) and `.claude/agents/ticket-scoper.md`
(ticket creation + conflict-flagging) — read both files' frontmatter directly: neither currently
declares a `model:` override (confirmed: `grep "^model:" .claude/agents/*.md` returns zero matches
across all 16 agent files, per `review_independence_epic.md`'s own already-recorded finding, spot-
checked again here for these two specifically). Both are "mechanical" in the sense
`bucket_c_future_options.md` uses the word: rule-following/checklist-style agents (13 DoD
conditions; ticket-format + conflict rules) rather than open-ended judgment agents like
`architecture-reviewer`/`security-reviewer` — a plausible reason routing is being considered for
them first, though the source doc does not state the reasoning explicitly (not invented here, just
noted as unstated).

## Scoring baseline available to A/B against
`stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md` and the frozen spec's own
`## Results` section — real, checked-in evidence: 27 sampled tickets, 5 converted to real fixtures,
M2/M3 defect-class detection rates, replayed twice under isolation with the 3-tier metrics computed
(Primary/Safety/Efficiency). This is the "eval baseline's scoring" `bucket_c_future_options.md`
names as the A/B comparand.

## Two distinct existing mechanisms — the spec must name the right one
`bucket_c_future_options.md`'s own words are "pilot `model:` overrides on `done-checker.md`/
`ticket-scoper.md` only" — this is the per-agent-file frontmatter field (`model:` alongside `name:`/
`description:`/`tools:` in each `.claude/agents/*.md` file), the same mechanism that sets each
agent type's model today (confirmed: 0 of 16 agent files currently declare one). This is distinct
from `.claude/workflows/implement-ticket.js`'s own `agent()` call-level `model:` parameter (used
today only by the shadow-reviewer's second, advisory call, e.g. `{ ..., agentType:
'architecture-reviewer', model: 'claude-fable-5-1' }`) — a lower-level, per-call override, not a
standing per-agent-type default. The spec must scope the pilot to the frontmatter mechanism named
in the source doc, not conflate it with the call-level one the shadow-reviewer path uses.
