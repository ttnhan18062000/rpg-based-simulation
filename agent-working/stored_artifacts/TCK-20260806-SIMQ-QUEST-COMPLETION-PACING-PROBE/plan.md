---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE
artifact_type: plan
tags: [simulation-quality, progression]
---

# plan.md — TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE

## Ordered Steps

1. Document the 3 findings in `investigation.md` (done).
2. File 3 follow-up tickets into `tickets/todos/tech-debt/`, each scoped to exactly one finding:
   - `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` (Finding 1 — the real blocker: wire quest
     generation into the live strategic-decision/action-selection layer)
   - `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` (Finding 2 — event_extractor.py's missing
     `isinstance(QuestState)` filter)
   - `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` (Finding 3 — missing progress
     evaluators for 3 of 5 quest kinds)
3. Update this ticket's own Completion Summary with the full finding + follow-up-ticket account,
   move to `tickets/done/`.
4. No `src/` files are changed by this ticket — Files Changed lists only ticket/staging-artifact
   paths.

## Files to Change

- `tickets/inprogress/TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE.md` (Completion Summary etc.)
- `tickets/todos/tech-debt/TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING.md` (new)
- `tickets/todos/tech-debt/TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG.md` (new)
- `tickets/todos/tech-debt/TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP.md` (new)

## Scope Guards

- Do NOT implement any of the 3 fixes in this ticket — user explicitly chose the
  investigation-only/file-follow-ups path over fixing any of it inline.
- Do NOT touch `src/town/guild.py`, `src/engine/domain/action_router.py`,
  `src/engine/quests.py`, `src/observability/event_extractor.py`, or
  `src/worldbuilding/compiler.py` — all are diagnosis targets only, confirmed via read-only
  tracing and real (but non-mutating) kernel runs.
- Do NOT recalibrate `grade_anchors.json` — no behavior changed.

## Dependency Map

Step 2's 3 follow-up tickets are independent of each other in principle, but
`TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP`'s practical value is gated on
`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` landing first (per investigation.md Finding 3: "this
gap is currently masked/unreachable... would become a real blocker the moment Finding 1's fix
lands") — noted in that follow-up ticket's own Related Tickets, not enforced by any SEQUENCE.md
here since these 3 are filed as independent tech-debt items, not a gated epic.

## Acceptance Criteria Map

- AC "1000t/2000t runs completed... raw event capture preserved" → real-kernel evidence section
  in investigation.md (satisfied via a 2000t run superseding the need for a separate 1000t run —
  the full tick-by-tick event log through 2000t already contains everything a 1000t run would show)
- AC "concrete tick range... or specific blocking cause identified" → Finding 1 (the specific
  blocking cause: `GuildAction` dead wiring)
- AC "conclusion documented: pacing artifact vs. real defect" → investigation.md's opening
  conclusion line
- AC "if real defect found, Plan/Implement fix it; if pacing, no code change" → deliberate
  investigation-only path per user decision — fix work deferred to 3 follow-up tickets, not
  silently absorbed into this one
