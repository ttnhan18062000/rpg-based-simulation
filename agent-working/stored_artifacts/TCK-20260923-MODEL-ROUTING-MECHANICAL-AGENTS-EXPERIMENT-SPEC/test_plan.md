---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC
artifact_type: test_plan
tags: [ai, agent-monitoring, governance, testing]
---

# Test Plan — TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC

## Scope
This ticket produces a documentation artifact only — no code changes, so no `pytest` coverage
applies. Verification is a structural/content review of the spec doc itself.

## Checks (manual, not automated)
1. The new doc at
   `docs/plans/agent_infrastructure/ai_first_hardening_epics/model_routing_mechanical_agents_experiment.md`
   contains all six required sections (Hypothesis, Baseline, Method, Metrics, Exit criteria, Kill
   criteria) plus Out of scope and References, matching `agent_evaluation_foundation_experiment.md`'s
   shape — verified by direct read-through after writing.
2. The Method section names exactly `done-checker.md` and `ticket-scoper.md` as pilot targets, and
   explicitly distinguishes the per-agent-file `model:` frontmatter mechanism from
   `implement-ticket.js`'s own call-level `model:` parameter (the investigation's own finding) —
   verified by grep for both agent names and both mechanism descriptions in the finished doc.
3. The spec makes the "detectable against baseline" risk concrete (not a restated warning) —
   verified by confirming the Method/Metrics sections name a specific comparison mechanism (score
   delta against item 13's baseline) rather than only repeating the source doc's caution sentence.
4. `bucket_c_future_options.md`'s item-18 entry links to the new spec doc — verified by grep.
5. `docs/REGISTRY.yaml` will regenerate automatically at Finalize per CLAUDE.md's "After Work"
   convention (docs were created) — no manual step needed here, called out so Finalize isn't
   surprised by a docs/ change with no corresponding registry update yet.

## Out of Scope
- No automated test file — nothing here exercises code, so there is no `pytest` target for this
  ticket's own diff. `make knowledge-index-update` runs at Finalize per the standard "docs changed"
  rule, itself validated by that tool's own existing test suite (unaffected, unmodified by this
  ticket).
