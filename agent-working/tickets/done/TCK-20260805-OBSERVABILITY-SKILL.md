---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-OBSERVABILITY-SKILL
phase: done
date: 2026-08-05
tags: [skills, observability]
---

# TCK-20260805-OBSERVABILITY-SKILL

## Title
Author a bespoke skill for working in src/observability/

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Domain-coverage sweep child ticket, from `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`.
`src/observability/` is large and mature (11 subdirectories: alerts, analytics, anomaly, budget,
cognition, live, mining, performance, personality, readiness; 8 top-level modules including
`event_recorder.py`, `hard_law_monitor.py`, `queue.py`, `prometheus_collector.py`), has 8 real
contract/rulebook docs (`docs/observability/*.md`), and 55 tickets reference it — yet zero skill
or agent targets it (`world-debugger` is scoped only to world-assembly/content resolution, not
observability). Confirmed real, non-generic domain logic: `event_recorder.py`'s backpressure
`ObservabilityController` (real fill-ratio thresholds, PRESSURE/DEGRADED/SURVIVAL modes) and
`hard_law_monitor.py`'s `HardLawMonitor` (DirtySet-scoped invariant checks against
`AuthoritativeState`, integrated into the kernel's Advancement phase per `docs/engine/kernel.md`'s
"Hard Law Compliance Guard"). Per the user's stated preference, this is a genuine bespoke-skill
case — no popular skill would capture a deterministic-tick-integrated observability pipeline with
backpressure modes and DirtySet-scoped invariant checking.

## Scope
- Author `.claude/skills/observability-debugging/SKILL.md` (or similar name — Plan decides exact
  naming/scope boundary), sourced from the existing real contract docs (`docs/observability/*.md`
  — hard_law_monitor, decision_trace_contract, prometheus_metrics, loki_label_policy,
  read_model_service_contract, etc.) rather than authored from scratch.
- Must correctly reference the kernel tick pipeline (`docs/engine/kernel.md`'s "Hard Law
  Compliance Guard", `docs/core/dirty_state_and_dependency.md`) since `HardLawMonitor` operates on
  the tick's `dirty_set` — the skill cannot stand alone from this context.
- Cover: backpressure/`ObservabilityMode` thresholds, `HardLawMonitor`'s invariant-check pattern,
  the event pipeline (`EventRecorder`/`event_extractor.py`), and how to debug a failing
  observability check (which docs to consult, which tests exist).
- Decide (Plan phase): should this be one skill or split (e.g. a narrower "debugging observability
  failures" skill vs. a broader "working in observability" skill)?

## Out of Scope
- Building new observability code or fixing any real bug found while authoring the skill — file a
  separate ticket if one is found.
- The `src/simulation_quality/` dev-side gap — related but distinct, covered by its own sibling
  ticket (`TCK-20260805-SIMQ-DEV-SKILL`).

## Acceptance Criteria
- [x] New skill authored (`.claude/skills/observability/SKILL.md`), sourced from
      `docs/observability/hard_law_monitor.md` and
      `docs/architecture/observability_hot_path_safety_contract.md`, cross-referencing
      `docs/engine/kernel.md` and `docs/core/dirty_state_and_dependency.md`.
- [x] Covers all 4 backpressure modes, all 7 HardLawMonitor laws + the 5 ObservabilityMode
      values (including the disclosed `LONG_RUN` fall-through gap), and the event pipeline
      (folded into the backpressure section, since `EventRecorder` owns both).
- [x] `docs/ai/skills.md` updated to list the new skill.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-SIMQ-DEV-SKILL (sibling domain-gap ticket)

## Related Docs
- `docs/observability/hard_law_monitor.md`, `docs/observability/decision_trace_contract.md`, `docs/observability/prometheus_metrics.md`, `docs/observability/loki_label_policy.md`, `docs/observability/read_model_service_contract.md`
- `docs/engine/kernel.md` (Hard Law Compliance Guard)
- `docs/core/dirty_state_and_dependency.md` (DirtySet — what HardLawMonitor operates on)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `src/observability/` (all subdirectories)
- `.claude/skills/` (new skill target)

## Assumptions / Open Questions
Exact skill naming/scope boundary (one skill vs. split) — Plan phase decides.

## Implementation Notes
Authored `.claude/skills/observability/SKILL.md`, `source: project`, sourced from real docs (not
written from scratch): the 7 `HardLawMonitor` laws with exact Law IDs/scopes/severities
(`docs/observability/hard_law_monitor.md` §1), the 5 `ObservabilityMode` values including the
disclosed `LONG_RUN` fall-through gap (§2, stated plainly rather than hidden — a real gotcha),
the 4 `EventRecorder` backpressure modes with fill-ratio bounds
(`docs/architecture/observability_hot_path_safety_contract.md` §5), Prometheus metric names, and
6 real, `find`-confirmed test file paths as debugging starting points. Cross-references
`docs/engine/kernel.md`'s Hard Law Compliance Guard and `docs/core/dirty_state_and_dependency.md`
for the DirtySet context this skill assumes rather than re-explains. Named `observability` (not
`observability-debugging`) — decided one skill, not split, since authoring and debugging share the
same grounding (the 7 laws/5 modes/4 backpressure modes) a split would duplicate for no benefit.

**Real finding during Implement**: `.agents/` Codex mirror regeneration silently produced 0 new
files for the new skill on the first attempt — `render_codex_guidance()` only mirrors skills
listed in `agent-orchestration/skills.yaml`'s validated contract, not everything under
`.claude/skills/`. Registered `observability` in that contract. This in turn required updating
`tests/agent_orchestration_codex_adapter/test_generator_traceability.py`'s
`test_skills_yaml_sixteen_entry_set_is_not_expanded` — a hardcoded `== 16` assertion that would now
fail on a legitimate, deliberate 17th entry. Renamed to
`test_skills_yaml_entry_set_excludes_known_contamination_ids` and refocused on the property it
actually protects (the specific known-bad skill-pack IDs from a previously-rejected marketplace
must never reappear), dropping the count assertion rather than bumping it to 17 — a fixed count
that must be manually incremented every legitimate addition is itself a maintenance hazard, and
the test's own excluded-ID list is the real regression guard, not the count.

Updated `docs/ai/skills.md`'s "Project-Level Skill Files" table with the new entry.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_observability_skill_content.py` — 8 tests, all passing: valid frontmatter;
all 7 real Law IDs present; all 5 `ObservabilityMode` values + the disclosed `LONG_RUN` gap
present; all 4 backpressure modes present; kernel/DirtySet docs cited; 2 cited test paths verified
to actually exist on disk (not just asserted present as text); `docs/ai/skills.md` genuinely lists
the skill; `.agents/` mirror body matches `.claude/` source. Regression check:
`pytest tests/agent_orchestration_codex_adapter/` — 27 passed (including the renamed contamination
guard test). `doc_staleness_check.py` → PASS. `clean_data_runs_early()` → PASS.
`expected_subsystems_for_files()` → `{}` — no parity entry needed.
`run_static_precheck('standard', ...)` — all 7 conditions PASS.

## Files Changed
- `.claude/skills/observability/SKILL.md` (new) — the skill.
- `.agents/skills/observability/SKILL.md` (new) — Codex mirror.
- `agent-orchestration/skills.yaml` — registered the new skill in the contract.
- `docs/ai/skills.md` — added to the Project-Level Skill Files table.
- `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` — renamed/refocused
  the stale fixed-count test.
- `tests/tools/test_observability_skill_content.py` (new) — 8 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Authored a genuinely bespoke, docs-grounded skill for the largest previously-uncovered subsystem
in this repo's domain sweep — real Law IDs, real mode semantics (including a disclosed known gap,
not hidden), real backpressure thresholds, real test-file citations. Discovered and fixed a real
process gap along the way: the Codex mirror generator requires explicit contract registration, not
automatic discovery, and the existing regression test guarding that contract had a hardcoded count
that would have blocked any future legitimate skill addition — fixed by refocusing it on the
property it actually protects. No known material gap.
