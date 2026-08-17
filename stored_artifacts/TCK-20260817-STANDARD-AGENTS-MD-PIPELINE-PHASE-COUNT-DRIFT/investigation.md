---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT
tags: [ai, engine, bug]
---

# Investigation — TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT

## Failing tests
Real CI failure, "API / tools / logging" job:
`tests/agent_orchestration_codex_adapter/test_agents_md_generation.py::test_agents_md_pipeline_note_matches_live_engine_doc`
— `AGENTS.md`'s generated `_AUTHORITATIVE_PIPELINE_NOTE` claims "32-phase"; the live
`docs/engine/authoritative_pipeline.md` says "31 Phases".

## Root cause chain
1. `tools/agent_orchestration_codex_adapter/generator.py:13` hardcodes
   `_AUTHORITATIVE_PIPELINE_NOTE` with "32-phase"/"32 phases", mirroring `CLAUDE.md:258`'s own
   ("32-phase refinement sequence for world mutation") table entry.
2. `docs/engine/authoritative_pipeline.md` currently says "31 Phases" — commit `1825f914`
   ("TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE") deleted the `adventure_decision` phase from
   `src/engine/pipeline.py` and correctly updated this doc's table from 32→31 rows at the time.
3. Two days later, commit `29d78798` (the same commit implicated in the rest of this session's
   fixes) introduced `generator.py` with the hardcoded "32-phase" string — apparently copied from
   CLAUDE.md's own table entry, which was never itself corrected after step 2. Neither source was
   cross-checked against the live doc at authoring time.
4. **Deeper finding**: `docs/engine/authoritative_pipeline.md`'s own 31-row phase table was
   *itself* stale against `src/engine/pipeline.py::refine()` — a direct count of `run_phase(...)`
   call sites in that function yields **37**, not 31. Six phases were missing from the table
   entirely: `faction_awareness`, `diplomatic_transitions`, `military_conflict` (all part of the
   E53B/E53C faction-diplomacy epic), `gold_sink` (E33C), `guild_visit`
   (TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING), `paid_information` (E42C). All 6 were added to
   `pipeline.py` in commits that predate `1825f914`'s table correction, meaning that correction
   itself only fixed the count for the *adventure_decision deletion*, not for phases that had
   accumulated in the file over time without ever being added to this doc's table.

So neither "31" nor "32" was ever the true, current phase count — "31" undercounted the doc's own
table against real source, and "32" (the generator's hardcode) was simply a copy of a number that
was already wrong by the time it was copied.

## Verification
`grep -n 'run_phase(' src/engine/pipeline.py` — counted 37 distinct call sites, all with unique
phase-name string literals, cross-checked one-by-one against the doc's prior 31-row table to
confirm exactly 6 were absent and the remaining 31 correspond 1:1, in the same relative order.

## Fix scope
Per this repo's Authoritative Mechanics Rule (docs and source must be in 100% semantic parity),
the substantive fix is correcting `docs/engine/authoritative_pipeline.md`'s table to the real,
current 37 phases — not just bumping a number in `generator.py` to match an already-wrong doc.
See `plan.md` for the full file list.
