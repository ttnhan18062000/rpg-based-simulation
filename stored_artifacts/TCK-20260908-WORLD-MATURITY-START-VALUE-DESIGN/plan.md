---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN
artifact_type: plan
tags: [world, architecture]
---

# Plan — TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN

Decision already made — this ticket's own plan is documentation-only:

1. Survey `state.maturity` consumers across `src/` (Investigate).
2. Record the accept-and-disclose decision in `docs/guidelines/intentional_divergences.md` with
   the full survey, a rationale class (Bounded), and a verification path.
3. Fix the directly-adjacent doc/code inconsistency found during the survey
   (`raid_boss_camp_contract.md`'s `camp.maturity` → `state.maturity` typo).
4. No schema change, no gate-value change, no other production code change.
