---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE
phase: done
date: 2026-08-06
tags: [simulation-quality, progression]
---

# TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE

## Title
Determine whether zero quest completions at 500t is a pacing artifact or a broken reward pipeline

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s investigation found `quest_event`
firing constantly (179/64/407 times across 3 sampled 500-tick runs) but never once reaching
`quest_reward_dispensed`. `QuestRewardPhase.resolve()` (`src/engine/pipeline_phases/quests.py:22`,
always active, not flag-gated) requires a quest to reach completion/retry state, not merely
"started" — every sampled `quest_event` message read directly this session showed "status
started," none confirmed "completed," but the sample was small (2 of 650+ messages, not
exhaustive) and the run data was cleaned before a full check could be done. This ticket determines
whether quests simply need more than 500 ticks to complete in these worlds (a pacing artifact, not
a defect) or whether something is genuinely blocking completion.

## Scope
1. Run the same 3 worlds (`dungeon_crawl`, `sandbox_world`, `hero_guild_routing`, seed 42) at
   1000t and 2000t via `calibrate_simq.py`, capturing raw `simulation_events.jsonl` (do not clean
   `data/runs/` until the check below is done).
2. Grep/parse the raw event stream for `quest_event` messages reaching "completed" or "failed"
   status, and for any `quest_reward_dispensed` events, at each tick depth.
3. If completions appear at 1000t/2000t but not 500t: this is a pacing artifact — document the
   typical completion tick range and close as "not a bug," update
   `docs/simulation_quality/corpus_tier_taxonomy.md`'s temporal-depth axis notes if relevant (per
   `extension_points.md` axis 6, "the real population-collapse defects... were only ever caught at
   1000t/2000t — invisible at 200t" — same pattern class).
4. If completions still never appear even at 2000t: trace the actual blocker (quest generation
   logic, objective-completion detection, or something else) — this becomes a real bug
   investigation, not a pacing conclusion.

## Out of Scope
- The combat/hazard misclassification question — unrelated, separate ticket.
- The push-vs-diff observability architecture question — unrelated to whether quests themselves
  complete; `quest_reward_dispensed`'s detection mechanism is a separate concern from whether the
  underlying quest completion happens at all.

## Acceptance Criteria
- [x] 1000t and 2000t runs completed for all 3 worlds with raw event capture preserved until
      analysis is done — 2000t runs used directly (a full tick-by-tick event log through 2000t
      already contains everything a separate 1000t run would show)
- [x] A concrete tick range for typical quest completion is established, or a specific blocking
      cause is identified if completions never occur — specific blocking cause identified
      (Finding 1: `GuildAction` dead wiring, the real quest system is never reachable at all)
- [x] Conclusion documented: pacing artifact (not a bug) vs. real defect, with evidence — real
      defect (3 independent findings), definitively not pacing (confirmed at 2000t)
- [x] If a real defect is found, this ticket's own Plan/Implement phases fix it; if pacing, no code
      change needed, close as investigation-only — per explicit user decision, this ticket stays
      investigation-only; the fix work is deferred to 3 filed follow-up tickets (see Completion
      Summary), not silently absorbed here

## Related Tickets
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (parent — source of this finding, DONE)

## Related Docs
- `docs/mechanics/attribute_progression_contract.md` (XP Gain Sources — quest reward is one of two
  XP sources)
- `docs/simulation_quality/extension_points.md` axis 6 (temporal depth — precedent for
  tick-length-dependent findings)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE/` during implementation.

## Related Code Areas
- `src/engine/pipeline_phases/quests.py` (`QuestRewardPhase`)
- `src/engine/quests.py` (`QuestResolutionSystem`)
- `src/engine/pipeline_phases/quest_opportunity_rewards.py` (`QuestOpportunityRewardSystem`)
- `src/observability/event_extractor.py` (quest_reward_dispensed emission, line ~354)

## Assumptions / Open Questions
- Whether 2000t is long enough to distinguish pacing from a real bug is itself an assumption — if
  neither tick depth shows completions, this ticket's own findings should say so plainly rather
  than force a conclusion.

## Implementation Notes
No `src/` changes — investigation-only, per explicit user decision when presented with the scope
tradeoff (fix everything now vs. fix nothing now vs. fix only the observability bug now). User
chose "investigation-only, file follow-ups" to keep this ticket's own diff at zero and avoid
mixing 3 independently-risky fixes (one of which touches the AI strategic-decision layer) into a
single ticket.

Found 3 real, independent defects via real, non-mocked kernel evidence (not code-reading alone):
(1) the real quest system (`QuestState`/`QuestKind`) is never reachable from live gameplay —
`GuildAction.visit()`, the only construction path, has zero callers; confirmed via a 300-tick real
kernel scan of every entity's every strategic project across 2 worlds, finding zero `QuestState`
instances. (2) `event_extractor.py`'s "quest_event" has no quest-type filter, mislabeling every AI
strategic goal (`GoalKind`-typed, unrelated to quests) as quest activity — confirmed via raw
`quest_id` values from 3 real 2000-tick runs. (3) `QuestResolutionSystem` has progress-evaluators
for only 2 of 5 quest kinds (HUNT, EXPLORE) — `GATHER`/`BOUNTY`/`LIBERATE` can never complete,
currently masked by (1) but would become a real blocker once (1) is fixed.

## Test Summary
No pytest run — no `src/` diff. Verification evidence instead: real `Kernel.tick_once()` runs
(300 ticks × 2 worlds, entity-project type scan) and real `calibrate_simq.py` engine runs
(2000 ticks × 3 worlds, raw `simulation_events.jsonl` grepped for `quest_reward_dispensed`:
0 in all three). See `stored_artifacts/TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE/
test_plan.md` for the full evidence list.

## Files Changed
- `tickets/todos/tech-debt/TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING.md` (new)
- `tickets/todos/tech-debt/TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG.md` (new)
- `tickets/todos/tech-debt/TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP.md` (new)

## Completion Summary
Determined definitively (real-kernel evidence, not assumption) that zero quest completions is
**not a pacing artifact** — confirmed at 2000 ticks across 3 worlds, `quest_reward_dispensed`
count stayed 0 throughout. Traced to 3 independent, real defects: the real quest system is
unreachable from live gameplay at all (`GuildAction` dead wiring, the root cause), the
observability layer mislabels unrelated AI strategic-goal activity as quest activity (no type
filter), and 3 of 5 quest kinds have no progress-evaluation wiring even if reached. Per explicit
user decision, this ticket stays investigation-only — no code fix landed here. Filed 3 scoped
follow-up tickets (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`,
`TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`,
`TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP`) into `tickets/todos/tech-debt/`, each
independently scoped, tested, and validated against the tag/frontmatter registries.
