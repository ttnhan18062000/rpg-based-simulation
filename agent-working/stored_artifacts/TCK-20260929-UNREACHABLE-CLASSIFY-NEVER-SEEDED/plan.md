---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED
artifact_type: plan
tags: [investigation, root-cause, corpus, world]
---

# Implementation Plan — TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED

## Summary

This is a scope-only classification ticket, not a fix — no `src/`, `tests/`, or content change
lands under it. The "implementation" is the classification procedure itself, reused from
`TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE`'s (PR #258) own method: for each covered ticket,
execute a real check (a `WorldCompiler.compile()` run against real content, or a direct grep/code
read confirming a claim) rather than accept the covered ticket's own prose, then assign exactly one
verdict from the epic's four-value axis or record a fifth AC-7 outcome.

## Steps taken

1. Read the parent epic (`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`) and this
   ticket's own Scope for the axis definition, evidence bar, and hard constraints (no registry
   edits, no re-deriving combat volume, no forcing an AC-7 case into the nearest bucket).
2. `demographic_cohort_cycle`: ran the decisive `spawn_region`-vs-`RegionSpec.id` key-match
   experiment named in this ticket's own Scope (added after `rpg-feature-planning`'s independent
   cross-check identified the exact fork). Executed, not reasoned from code.
3. `camp`: applied the same registry-dating + real-compile method `rpg-feature-planning` directed
   for this specific ticket (it, unlike the two cognition tickets, cites a 2026-09-16
   `registries/mechanisms.yaml` verdict of the same vintage as the cohort case).
4. `enemy_data`/`region_data`: registry-dating does not apply (no registry entry cited); verified
   each covered ticket's own claims directly instead — a `_ENEMY_DANGER` live-path confirmation and
   a `RouteFamily.SCOUT_LOCATION` generator-absence grep, per `rpg-feature-planning`'s specific
   instruction to check `_ENEMY_DANGER`'s usage before assigning a verdict.
5. Recorded each verdict directly in its own covered ticket's body (epic Deliverable 2), then rolled
   the summary and Acceptance-Criteria checkoff into this ticket's own Implementation Notes.
6. Re-confirmed `registries/mechanisms.yaml` byte-for-byte unchanged against `origin/main` after
   every step (not local `main` — a methodology correction carried forward from
   `rpg-feature-planning`'s own earlier check on this epic).

## Explicitly not done

- The epic's own consolidated classification document under `docs/plans/` (Deliverable 1) —
  deferred to `T06`, which needs all of `T01`–`T04`'s output first, per this ticket's own Scope.
- Any registry or doc correction for the staleness this pass found (`registries/mechanisms.yaml`'s
  `camp`/`demographic_cohort_cycle` entries, `docs/world/raid_boss_camp_contract.md`) — flagged in
  the affected tickets' own bodies and routed to `agent-working-design`/the doc's owner, not
  actioned here.
- Either cognition ticket's own underlying design question (whether to build a combat-outcome
  learning mechanism; whether to build the `SCOUT_LOCATION` generator branch) — this pass answers
  the epic's reachability axis only.
