# Implementation Sequence — simq-pillar-lifecycle-depth

Started from a 2026-08-06 session discussion on SimQ's black-box/observational architecture and
COMBAT/PROGRESSION scope separation. Escalated through real investigation into a corpus-wide
data-validity question, a confirmed bug, and a full observability-architecture question (post-tick
diffing vs. push-based emission). The push-based migration itself has since been promoted to its
own gated epic — user-designated top priority — filed separately at
`tickets/todos/simq-observability-push-migration/` (includes the hazard-misclassification hotfix,
which moved there as that epic's first child ticket). This folder now tracks the remaining 3
tickets from the original pillar-lifecycle-depth thread.

## Order

1. **TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC** (hotfix, doc-only) — **DONE.**
2. **TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY** (standard, investigation-first) —
   **DONE.** Produced the observability-architecture investigation (also DONE, see below) and the
   3 tickets remaining in this folder.
3. **TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE** (standard, investigation-first) —
   **DONE.** Recommended the phased push-based migration, now tracked as its own epic — see
   `tickets/todos/simq-observability-push-migration/SEQUENCE.md`.
4. **TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE** (standard, investigation-first, P2) —
   **DONE.** Confirmed NOT a pacing artifact (0 `quest_reward_dispensed` across 3 worlds at
   2000 ticks). Traced to 3 real, independent defects via real-kernel evidence: the real quest
   system (`QuestState`/`QuestKind`) is unreachable from live gameplay at all (`GuildAction.
   visit()`, the only construction path, has zero callers anywhere — confirmed 0 `QuestState`
   instances after 300 real ticks scanning every entity's projects across 2 worlds);
   `event_extractor.py`'s "quest_event" has no quest-type filter, mislabeling unrelated AI
   `GoalKind` strategic-goal activity as quest activity; `QuestResolutionSystem` has
   progress-evaluators for only 2 of 5 quest kinds (`HUNT`/`EXPLORE`). Investigation-only per
   explicit user decision — filed 3 scoped follow-ups into `tickets/todos/tech-debt/`
   (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`, `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`,
   `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP`), not fixed inline.
5. **TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE** (standard, investigation-first) —
   **DONE.** Implemented `capability_growth_stalled` + `life_arc_incoherent` directly in
   `event_extractor.py`, unconditionally (not flag-gated behind the Phase 2 push-shaper flag —
   a brand-new signal with no migration/rollback obligation, and `ScoringContext` itself was
   found to have no entity-state access at all, correcting the ticket's own premise). Verified
   via 12 new unit tests plus a real 500-tick kernel run showing genuine signal activity (24/32
   entities). `PROG-118` parity entry.
6. **TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY** (standard, investigation-first) — **DONE.**
   Implemented `faction_trajectory_stagnant` directly in `FactionShaper` (FACTION's own
   live-by-default path since Phase 1), mirroring WORLD's `trauma_hazard_broken` pattern — the
   first cross-tick state `FactionShaper` carries, `reset_run_state()` wired into
   `Kernel.__init__`. Found and disclosed a separate, pre-existing `faction_territory_pct`
   payload gap (`faction_monopoly`/`faction_conquest_degenerate` can never fire in either
   delivery path), filed as `TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP`, not fixed inline.
   Verified via 6 new unit tests plus real-kernel runs across 2 worlds; zero-firing in both
   explained (diplomatic activity front-loaded at spawn, not ongoing), not a defect.

**All 6 tickets in this folder are now DONE.**

## Notes

- The push-based migration epic (`tickets/todos/simq-observability-push-migration/`) is a strictly
  sequential 5-ticket chain — see its own `SEQUENCE.md` for that internal ordering.
- #5 and #6 are the original pair from the pillar-boundary finding; #5 is now blocked by the
  migration epic, #6 is not.
- Each ticket's own Investigate phase is authorized to flag a new finding and stop, rather than
  silently expand scope — this is exactly how #2 produced #3, and #3 produced the migration epic.
