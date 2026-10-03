---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC
artifact_type: plan
tags: [ai, agent-monitoring, governance]
---

# Plan — TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC

## Approach
Write one new doc, `docs/plans/agent_infrastructure/ai_first_hardening_epics/model_routing_mechanical_agents_experiment.md`,
mirroring `agent_evaluation_foundation_experiment.md`'s exact section shape. No code, no agent-file
edits — a pure spec document. Update `bucket_c_future_options.md`'s item-18 entry with a one-line
link once the doc exists, matching how item 13's own entry was updated.

## Steps

1. **Header block**: Tracking ticket (none — Bucket-B items never convert directly to a production
   ticket), Source (`AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Bucket-C item 18, cleared per
   item 13's MET exit criteria), Roadmap (Horizon 2 per `roadmap.md`'s Bucket-C placement — confirm
   exact horizon label by reading `roadmap.md` before writing), Priority (P2 — quality-of-life for
   two mechanical agents, not a structural risk item like the shadow-reviewer work).
2. **Hypothesis**: a `model:` frontmatter override on `done-checker.md`/`ticket-scoper.md` alone
   (candidate model, distinct family from the two agents' current inherited model) can be evaluated
   against item 13's own baseline scoring without introducing an undetected quality regression —
   framed as testable, not assumed true.
3. **Baseline**: item 13's own real results (`stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md`)
   — cite the actual figures (27 sampled tickets, 5 real fixtures, M2/M3 detection rates, 3-tier
   metrics) rather than re-deriving new baseline numbers; this pilot's whole point is reusing that
   baseline, not building a second one.
4. **Method**: (a) apply `model:` override to `done-checker.md` and `ticket-scoper.md` only, no
   other agent files; (b) replay a comparable ticket sample through both agents under the current
   model and the candidate model, using `tools/agent_replay/`'s existing sampler/fixture-converter/
   replay infrastructure (item 13's own build) rather than a new harness; (c) score both runs with
   item 13's own metric vocabulary (gate-outcome/defect-class flag rate) so results are directly
   comparable to the baseline, not a new incompatible metric; (d) explicitly describe the
   regression-detection mechanism the named risk requires: a candidate score materially worse than
   baseline on either agent is the fail signal, checked before any cutover consideration — never
   assumed absent.
5. **Metrics**: mirror item 13's tiered shape — Primary (does the candidate agent produce the same
   DoD/ticket-conflict verdicts as baseline on the same sample?), Safety (does the pilot itself
   avoid contaminating live session state, same isolation requirement as item 13's Method step 3),
   Efficiency (wall-clock/cost difference — informative, not pass/fail).
6. **Exit criteria**: candidate matches baseline verdict rate within an explicit, small tolerance
   on both agents, with no regression on either target's own known failure modes.
7. **Kill criteria**: any material verdict divergence that can't be attributed to legitimate
   model-quality improvement (i.e., looks like the named "masking a real quality regression" risk)
   — explicitly instructs stopping and reporting negative, not silently re-scoping.
8. **Out of scope**: no `.claude/agents/*.md` edit in this ticket; no routing dispatcher/config
   mechanism; no candidate model chosen here (deferred to implementation time, same deferral pattern
   `review_independence_epic.md` used).
9. **References**: `bucket_c_future_options.md`, `agent_evaluation_foundation_experiment.md`,
   `roadmap.md`, the two target agent files, `tools/agent_replay/`.
10. **Update `bucket_c_future_options.md`**: item-18 entry gets one sentence linking the new spec
    doc, mirroring the precedent already set for item 13's own entry once its pilot ticket landed
    (check how, if at all, item 13's entry in this doc was updated — if it wasn't, this ticket
    still adds the link for item 18 since the ticket's own acceptance criteria require it).

## Risk / Rollback
Pure documentation addition (one new file, one small edit to an existing doc) — no code path, no
test dependency, trivially revertible via `git revert`.

## Test Plan Reference
See `test_plan.md` in this same directory.
