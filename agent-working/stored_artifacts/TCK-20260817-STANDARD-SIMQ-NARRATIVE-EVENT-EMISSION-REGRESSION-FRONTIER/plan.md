---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER
artifact_type: plan
tags: [simulation-quality, calibration, corpus, root-cause]
---

# Plan — TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER

## Original plan (as scoped by the ticket)
1. Reproduce >=2 of the 5 failing tests.
2. Bisect/trace whether a missing `.merge()`/aggregation call (the
   `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS` template) drops
   `world_events_add` population for `world_emergence_event`/`narrative_milestone`.
3. If a real emission-path bug is found, fix it in `src/`, re-verify the 5 tests pass against
   their existing, unmodified anchors.
4. If no real bug is found and real narrative activity cannot be restored, stop and report
   instead of force-adjusting `grade_anchors.json`.

## Deviation: Step 3 did not apply — no fix was implemented

`investigation.md` documents the full bisection: the parent ticket's own "strongest lead" (a
missing `.merge()` analogous to the combat-engagement bug) was checked at every population site
named in the parent ticket and found correct in every case. `git worktree` bisection to the
commit immediately before the suspected migration (`11b83f37`) proved the historical high
NARRATIVE score for these exact tests came from a since-fixed bug
(`TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`, closed 2026-08-07) that mislabeled ordinary AI
strategic goals as fake quests — not from real narrative content that a code fix could restore.
Per the ticket's own explicit fallback instruction and CLAUDE.md's Hard Rule against editing an
artifact to make a gate pass instead of fixing substance, this ticket **stops here**: no `src/`
change was made, and `grade_anchors.json`/`test_corpus_diversity.py` were **not** touched.

## What was actually done
1. Context Scan per CLAUDE.md (search_docs, graphify query) before any investigation.
2. Reproduced 2/5 tests via real `pytest -m slow` (both failed with the exact reported
   `NARRATIVE grade=C vs anchor A` signature).
3. Read every `world_events_add` population site named in the parent ticket
   (`pipeline.py` diplomatic/military phases, `world_dynamics.py` sovereignty,
   `economy.py`) and confirmed each correctly preserves/merges prior-phase state.
4. Live call-count instrumentation confirmed zero `WorldEvent`s are produced in these
   specific runs because the qualifying game-state conditions (war, sovereignty shift) never
   occur within 200 ticks — not because they are being silently dropped.
5. `git worktree` bisection to `12da37db` (pre-migration) reproduced the historical
   NARRATIVE activity and identified its true source: `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`'s
   already-fixed mislabeling bug, compounded by `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s
   already-shipped architecture consolidation.
6. Confirmed the current emission chain (push shaper → `QualityHub._translate_quest_event` →
   `NarrativeScorer`) is intact end-to-end by forcing `ENABLE_GUILD_QUEST_GENERATION=ON` directly
   on `AuthoritativeState` and observing a real quest event fire.
7. Checked the other 9 NARRATIVE event types independently; each is legitimately absent for
   these specific worlds/seeds/tick-budgets, not separately broken.
8. Spot-checked 2 additional worlds (`frontier_extended`, `frontier_marches`) beyond the 2
   pytest-verified ones; both show the identical signature (Step 5 of ticket scope).
9. Wrote this investigation up honestly rather than fabricating a fix or silently recalibrating
   anchors.

## Scope guard
No code, test, or anchor file was modified. `tickets/`, `staging_artifacts/`, `agent-monitoring/`,
`tickets/working_log.csv`, and `docs/REGISTRY.yaml` are the only repo artifacts this ticket
touches, per CLAUDE.md's Finalize checklist for a ticket whose Implement phase produced no code
change.

## Acceptance-criteria map
| Acceptance criterion (from the assigning task) | Status |
|---|---|
| Context Scan run before investigation | Done |
| >=2 of 5 tests reproduced locally | Done (2 real pytest runs) |
| Bisect/trace the real root cause | Done — refutes the "missing merge()" hypothesis with evidence |
| Fix the real bug in `src/` | N/A — no real bug found; fabricating one would violate the Hard Rule |
| Tests pass against existing anchors | Not achieved — correctly, since the anchors are stale, not the code |
| Do not force-adjust anchors to hide a non-restored fix | Done — anchors untouched |
| Check whether other worlds share the same pattern | Done (2 additional worlds spot-checked) |
| Ticket/staging-artifact discipline | Done (this artifact set) |
