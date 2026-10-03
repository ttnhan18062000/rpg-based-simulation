---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-OBSERVABILITY-SKILL
artifact_type: plan
tags: [skills, observability]
---

# Plan — TCK-20260805-OBSERVABILITY-SKILL

## New skill: `.claude/skills/observability/SKILL.md`
`source: project` frontmatter (bespoke, repo-specific — matches `backend-testing`'s precedent from
the sibling swap ticket). Sections:
1. **When to use** — editing/debugging `src/observability/`, a failing `HardLawMonitor` check, a
   backpressure/mode question, event-pipeline work.
2. **The 7 Hard Laws** — table sourced verbatim-in-spirit from `hard_law_monitor.md` §1
   (Law ID, DirtySet scope, constraint, severity).
3. **ObservabilityMode policy** — the 4-mode table + the disclosed `LONG_RUN` fall-through gap,
   stated plainly (not hidden) since it's a real gotcha someone debugging a "missing" violation
   log needs to know about.
4. **Backpressure (`ObservabilityController`)** — the 4 queue-fill-ratio modes from
   `observability_hot_path_safety_contract.md` §5.
5. **Kernel integration** — one paragraph: runs during Advancement, before commit; cross-references
   `docs/engine/kernel.md`'s Hard Law Compliance Guard and `docs/core/dirty_state_and_dependency.md`
   for what `DirtySet` actually is (this skill assumes that context, doesn't re-explain it).
6. **Debugging a failing check** — practical steps: which Prometheus metrics to check
   (`sim_hard_law_violations_total`, `sim_hard_law_last_violation_tick`), which real test files to
   run/read first (`tests/engine/test_hard_law_monitor.py`, `tests/perf/test_hard_law_monitor_overhead.py`).

## `docs/ai/skills.md` update
Add the new skill to whatever skill-listing section exists there, following the file's own
established format (checked before writing — matches the existing entries' shape).

## `.agents/` mirror regeneration
Run `render_codex_guidance(ROOT, ROOT)` after writing the new skill.

## Tests
New `tests/tools/test_observability_skill_content.py`:
- Skill file exists, valid frontmatter.
- Contains all 7 real Law IDs (a source-text guard against a future accidental partial-copy).
- Contains the real 4 `ObservabilityMode` values and the disclosed `LONG_RUN` gap.
- Contains the real 4 backpressure mode names and their fill-ratio bounds.
- Cites `docs/engine/kernel.md` and `docs/core/dirty_state_and_dependency.md` by path.
- `docs/ai/skills.md` lists the new skill.
- `.agents/skills/observability/SKILL.md` mirror body matches `.claude/`'s source body.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (sourced from real docs, cross-references kernel pipeline) → investigation.md's citations,
  Plan's sections 3/5.
- AC2 (covers backpressure, HardLawMonitor pattern, event pipeline) → Plan sections 3, 2, and the
  event-pipeline mention folded into section 1/6 (EventRecorder is the backpressure controller's
  own home, already covered by section 4 — a separate "event pipeline" section would duplicate it).
- AC3 (`docs/ai/skills.md` updated) → Document-Update step.
