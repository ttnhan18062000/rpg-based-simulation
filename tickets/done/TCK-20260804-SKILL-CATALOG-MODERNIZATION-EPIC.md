---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC
phase: open
date: 2026-08-04
tags: [skills, workflows, process-improvement]
---

# TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC

## Title
Epic: Skill catalog modernization — real triggering, popular-content sourcing, agent-monitoring usage tracking, and documentation

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Prompted by a session finding: of the 16 skills in `.claude/skills/`, 6 have real, heavy usage
(`implement-ticket` 71, `create-tickets` 26, `implement-epic` 11, `agent-monitoring-retro` 9,
`simq-audit` 5, `brainstorming` 3, per `agent-monitoring/tools.jsonl`'s full history), and 10 have
**zero invocations ever recorded**.

**Corrected after Investigate (2026-08-05) — this ticket's own original framing was stale.** The
mandatory Context Scan (`search_docs`) surfaced 6 more done tickets this ticket originally never
cited, all directly on-topic, all landed between 2026-07-05 and 2026-07-20:

- **`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`** already root-caused "why doesn't
  `suggested_skills` ever fire": it is **advisory by design** — logged, never consumed by any
  later phase — a deliberate decision, not a bug. It assessed 4 candidate tunings and recommended
  building a hard `security` gate now, deferring blanket auto-invoke (no JS-callable
  skill-invocation primitive existed).
- **`TCK-20260705-WORKFLOW-SECURITY-GATE`** built exactly that: a mandatory `Security-Review`
  phase in `implement-ticket.js`, triggered by the `security` tag or `suggested_skills` —
  converting that one tag from advisory to binding. 2 real, clean `Security-Review` fires exist
  since.
- **`TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK`** added a pytest drift-check across the mapping.
- **`TCK-20260708-RETRO-TAG-BREAKDOWN`** already shipped 2 `generate_retro.py` sections
  (`## Tag Breakdown — Subsystem/Topic`, `## Tag Breakdown — Process/Skill-signal`) — the latter
  cross-references `security`-tagged runs against `Security-Review`/`SECURITY_BLOCKED` hits. This
  is a real, already-shipped agent-monitoring metric, though distinct from (and narrower than)
  Scope item 4 below (it's tag-based, not `Skill`-tool-invocation-count-based).
- **`TCK-20260720-SKILL-MAPPING-DEDUP`** already resolved the "4 independent hand-copied mapping
  tables" hazard `TAG-SKILL-SUGGEST` flagged: the mapping now lives as `triggers_skill` data on
  `tag_registry.jsonl` rows, read live via `tools/tag_registry.py::get_skill_mapping()` — all 4
  consumers read this single source today.
- **`TCK-20260720-TAG-RELEVANCE-VERIFY`** added `tag_relevance_flags` (advisory tag-fit
  self-check) and a Finalize-time `check_tag_drift()`.

`TCK-20260705-SIX-SKILLS-INVESTIGATION` (also cited originally) still stands as-is — its 6
"correctly redundant" verdicts were re-confirmed with no new evidence found to change them.

**What is genuinely new after this correction, not covered by any of the 9 prior tickets:**

1. **A real, newly-found bug in the exact class fixed twice today, in a location today's fixes
   didn't touch.** `TCK-20260731-GATE-BYPASS-HARDENING` (hotfix tier, `security` tag) never got
   its `Security-Review` phase, despite the gate's code being tier-unconditional. Root cause:
   `.claude/skills/implement-ticket/SKILL.md` line 70's "Hotfix tier skips..." summary paragraph
   omits `Security-Review` from its "still runs for hotfix" enumeration, even though the same
   file's step 11 correctly states "not tier-gated" two paragraphs earlier. This already caused a
   real miss.
2. **Mechanism 1 (CLAUDE.md file-path auto-invoke row) is still genuinely unresolved** — unlike
   mechanism 2, this is not "advisory by design," it's a standing instruction with zero real
   invocations despite confirmed real `src/api/` edits since it was wired. Evidenced pattern:
   unconditional every-task rules (search_docs, graphify) get followed reliably; conditional,
   situational rows do not, even correctly worded. The more promising fix direction (per
   Investigate) may be converting these to binding gates via the now-proven `security` pattern,
   not further doc/table tweaks — but this carries a real design risk (see Risks).
3. **Popular/community skill sourcing** — genuinely untouched by any prior ticket.
   `api-design-principles` and `architecture` carry explicit `source: community` frontmatter (and
   `architecture` references 3 sibling skills that don't exist in this repo — clearly unadapted
   paste-in). 4 more (`backend-testing`, `python-performance-optimization`,
   `python-testing-patterns`, `debugging-strategies`) share the identical undisclosed structural
   fingerprint. These 6 overlap heavily with the zero-invocation set.
4. **No agent-monitoring tracking exists for raw `Skill`-tool-invocation counts by name** —
   `RETRO-TAG-BREAKDOWN`'s tag-breakdown section is real but answers a different question (tag →
   gate-hit), not "was `/api-design-principles` ever actually invoked."
5. **Related agents/workflows updates**, scoped now to what Investigate actually found needs
   updating (the SKILL.md:70 fix; docs/ai/skills.md's stale description of the advisory mechanism,
   which predates the security hard-gate and the mapping dedup).

## Scope
- **Fix the `Security-Review`-skipped-on-hotfix bug** (`.claude/skills/implement-ticket/SKILL.md`
  line 70) — small, real, already caused a live miss. Likely its own hotfix-tier child ticket,
  same discipline as today's `SKILL-JS-PHASE-SYNC`.
- **Decide the mechanism-1 fix direction** (CLAUDE.md file-path auto-invoke rows for
  `api-design-principles`/`debugging-strategies`/`python-performance-optimization`): convert to
  binding gates mirroring `security`'s proven pattern, vs. some other fix — with explicit
  reasoning about the asymmetry these 3 skills have vs. `security` (no clean pass/fail verdict
  shape). Not a blanket "convert all to gates" — a per-skill judgment call.
- **Ticket-metadata-driven triggering, re-evaluated against the now-corrected picture**: the
  mapping is already cheap to extend (one `tag_registry.jsonl` row via `SKILL-MAPPING-DEDUP`'s
  live mechanism, not 4 hand-edits) — decide whether the real lever is expanding which tags are
  mapped, or converting already-mapped-but-still-advisory tags to gates (the evidenced-stronger
  option, given `security`'s 2 clean fires vs. 0 real invocations across every advisory-only tag).
- **Popular/community skill sourcing**: for the 6 skills flagged as strong swap candidates
  (`api-design-principles`, `architecture` — both disclosed `source: community`; `backend-testing`,
  `python-performance-optimization`, `python-testing-patterns`, `debugging-strategies` — same
  undisclosed fingerprint), research whether a current, well-maintained popular alternative exists
  and is worth adopting, per the user's stated preference. Scope per-skill; `frontend-design`/
  `doc-coauthoring`/`brainstorming` are a different, smaller-risk category (first-party-style
  content with some dangling cross-references, not a paradigm swap) — investigate separately, not
  blanket.
- **Agent-monitoring usage tracking**: add a genuinely new metric — raw `Skill`-tool-invocation
  counts by skill name (not the tag-based gate-hit breakdown `RETRO-TAG-BREAKDOWN` already built) —
  following `retrieval_baseline_metrics.py`'s exact pattern (frozen constant, `derivation` string,
  per-run grouping, `"unattributed"` bucket). Output confined to `agent-monitoring/` (via
  `generate_retro.py`'s `RETRO_DIR` or a dedicated one-off script's stdout/`--output`), never
  `docs/`, `data/`, or `config/` — those serve unrelated concerns in this repo.
- **Documentation**: `docs/ai/skills.md`'s "Tag-Based Skill Suggestions" section is stale (predates
  the security hard-gate and the mapping dedup) — fix regardless of which other child ticket lands.
  DONE via `TCK-20260805-SKILLS-DOC-STALENESS-FIX`.
- **Domain-coverage sweep (2026-08-05, docs+graphify+search_docs only, no source reads)**: user
  asked to look beyond the web API layer at backend engine subsystems (simulation quality, logging/
  observability, resource management/economy, debugging) and RPG gameplay domains (cognition,
  combat, etc.). Findings, cross-referenced against the same "real Mechanics Bible/contract doc +
  zero skill/agent coverage" pattern:
  - `src/observability/` — **real gap**, confirmed via deep read (backpressure thresholds,
    `HardLawMonitor`'s DirtySet-scoped invariant checks; 8 real contract docs, 55 ticket
    references, zero skill/agent coverage).
  - `src/simulation_quality/` — **partially covered**: `simq-audit` (5 real invocations) only
    covers the audit/governance workflow (drift, calibration, grading), not the
    development/debugging side (writing a new scorer, debugging a wrong pillar score).
  - `src/systems/` — **real gap, largest surface** (70 files, 6635 lines: economy, crafting,
    quests, guild, market; `docs/mechanics/03_economic_laws.md` governs it, uncaptured by any skill).
  - `src/domains/combat_engagement/` (**combat**) — **real gap**: `docs/mechanics/02_combat_laws.md`
    (Mechanics Bible ch.2) + a dedicated `docs/simulation/domains/combat_engagement_contract.md`
    (10-file domain contract), zero skill coverage.
  - `src/cognition/`, `src/strategy/`, `src/ai/goals/` (**cognition/strategy**) — **real gap,
    high-value**: `docs/cognition/README.md` + `docs/strategy/bounded_cognition_decision_flow.md`
    explicitly warn "cognition is NOT strategy, NOT domain decision-making" — a subtle,
    repo-specific boundary a generic community skill would get actively wrong, not just fail to
    help with.
  - `src/entities/`, `src/progression/` (**progression/entities**) — **real gap**:
    `docs/mechanics/01_entity_anatomy.md` (ch.1) + `docs/mechanics/attribute_progression_contract.md`
    (exact XP formulas), zero skill coverage.
  - `src/quests/`, `src/town/` — weaker signal, smaller, not as clear-cut as the above; needs a
    lighter follow-up check rather than a confirmed-gap child ticket yet.
  - `src/engine/`, `src/core/`, `src/runtime/`, `src/platform/`, `src/replay/`, `src/certification/`
    — **adequately covered**, confirmed via a deep read of `docs/engine/kernel.md`,
    `docs/engine/authoritative_pipeline.md`, `docs/core/dirty_state_and_dependency.md`,
    `docs/engine/candidate_selection.md` (the 7-phase kernel tick loop, the 32-phase
    `AuthoritativeApplyPipeline`, the `DirtySet` optimization layer, and 3-tier candidate
    selection) — this is the single most thoroughly documented area of the repo (6+ dedicated
    P1-authority docs with their own Extension Rules sections), and is foundational to the combat/
    progression/cognition gaps above (their real logic executes as named phases inside this exact
    32-phase pipeline, e.g. `combat_engagement`, `progression_conversion`, `strategic_intelligence`
    — any bespoke skill for those domains must correctly reference this pipeline, not duplicate or
    risk contradicting it).
  - `src/worldassembly/`, `src/worldbuilding/`, `src/worldgeneration/`, `src/worldmodules/`,
    `src/content/` — already covered by the `world-debugger` agent (confirmed, no action needed).
  - `src/actions/`, `src/ai/`, `src/cli/`, `src/lab/`, `src/scenarios/`, `src/views/`, `src/config/`,
    `src/testing/` — dev-tooling/support code, not core domain logic, lowest priority, not
    investigated further.
- **Open judgment calls for Plan, not pre-decided**: whether `frontend-design`'s exclusion should
  reopen given 4 real-but-maintenance-shaped frontend tickets since 07-17; whether the 2
  `CODEX-PILOT-ENTRYPOINT`/`CODEX-POSTTOOL-HOOK-COMMAND` incomplete event traces are the same bug
  class or an unrelated monitoring-write gap (flagged, not diagnosed).
- Break down into child tickets once Plan sizes each piece — do not implement anything directly in
  this epic ticket itself. **DONE (2026-08-05)**: all 15 remaining child tickets filed to
  `tickets/todos/skill-catalog-modernization/`, with `SEQUENCE.md` establishing implementation
  order. See that folder for the full, real ticket set — not re-enumerated here to avoid drift
  between this summary and the actual files.

## Out of Scope
- Re-litigating `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s "correctly redundant" verdicts — 
  re-confirmed with no new evidence to change them (usage counts unchanged).
- Re-building anything `WORKFLOW-SECURITY-GATE`, `SKILL-MAPPING-DEDUP`, `RETRO-TAG-BREAKDOWN`, or
  `TAG-RELEVANCE-VERIFY` already shipped — see Related Tickets. A child ticket expanding the
  mapping adds a `triggers_skill` field via `tag_registry.py::add_tag()`, never touches 4 files by
  hand; a new usage-tracking child ticket is additive to `RETRO-TAG-BREAKDOWN`'s section, in its
  own clearly-distinguished heading, never a re-implementation of it.
- Removing any skill outright — user's explicit framing is "we want to use them to improve the
  current working," not prune.
- `prompt-builder` — Copilot-specific, not this project's concern, already correctly excluded,
  no new evidence changes this.
- Diagnosing the `CODEX-PILOT-ENTRYPOINT`/`CODEX-POSTTOOL-HOOK-COMMAND` event-trace gap in this
  epic — flagged as a possible related finding, would need its own targeted investigation (full
  session history, not available from `tools.jsonl`/`events.jsonl` alone).

## Acceptance Criteria
- [x] Root cause of the 3-skill dual-mechanism non-firing identified with real evidence — DONE via
      `TCK-20260805-SKILL-GATE-CONVERSION-DECISION`: `api-design-principles`/`debugging-strategies`
      have no checkable verdict shape (left advisory, no gate); `python-performance-optimization`
      does, but was already reachable via the existing Test-phase gate once `test-scoper`'s real
      gap (file-path-only mapping missing performance-motivated changes outside `src/perf/`) was
      found and fixed with a tag-driven prompt enrichment, not a duplicate new gate.
- [x] A decision, with reasoning, on expanding ticket-metadata-driven skill triggering — DONE via
      the same ticket: `performance`-tag routing is the first real instance of tag-driven routing
      beyond `security`'s full gate conversion, documented in `docs/guidelines/tag_taxonomy.md`.
- [x] Per-skill assessment of whether popular/community-sourced content should replace
      project-original content — DONE via `TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED`
      (`api-design-principles`/`architecture`: adapted, no swap found via real WebSearch) and
      `TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED` (`backend-testing`: bespoke-replaced,
      confirmed actively misleading; `python-testing-patterns`/`python-performance-optimization`/
      `debugging-strategies`: adapted).
- [x] A real agent-monitoring skill-usage metric exists — DONE via `TCK-20260805-SKILL-USAGE-METRIC`
      (`tools/agent-monitoring/skill_usage_metric.py`, real per-skill invocation counts from
      `tools.jsonl`).
- [x] Child tickets created for each distinct, evidenced piece of work identified — 15 tickets
      filed to `tickets/todos/skill-catalog-modernization/`, `SEQUENCE.md` establishes order.
- [x] `docs/ai/skills.md` (and CLAUDE.md if changed) updated to stay accurate — DONE via
      `TCK-20260805-SKILLS-DOC-STALENESS-FIX` and every domain-skill child ticket's own
      Document-Update step.
- [x] Child tickets filed AND completed for the domain-coverage sweep's confirmed real gaps — all
      6 done: `TCK-20260805-OBSERVABILITY-SKILL`, `TCK-20260805-SIMQ-DEV-SKILL`,
      `TCK-20260805-SYSTEMS-SKILL`, `TCK-20260805-COMBAT-SKILL`,
      `TCK-20260805-COGNITION-STRATEGY-SKILL`, `TCK-20260805-PROGRESSION-ENTITIES-SKILL`.

## Related Tickets
- TCK-20260704-SKILL-TRIGGER-COVERAGE (wired the 3-skill CLAUDE.md rows this epic re-examines)
- TCK-20260705-TAG-SKILL-SUGGEST (built the original tag-based suggestion mechanism)
- TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION (already root-caused mechanism 2 as advisory-by-design — not re-litigated)
- TCK-20260705-WORKFLOW-SECURITY-GATE (already converted `security` tag to a binding gate — the proven pattern for any mechanism-1 gate-conversion child ticket)
- TCK-20260705-SIX-SKILLS-INVESTIGATION (settled the 6-skill redundancy question; not re-litigated here)
- TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK (pytest drift-check across the mapping)
- TCK-20260708-RETRO-TAG-BREAKDOWN (already shipped a tag-based gate-hit breakdown — distinct from and not to be re-built by this epic's Item 4)
- TCK-20260720-SKILL-MAPPING-DEDUP (already resolved the 4-hand-copy hazard — the mapping is now single-sourced via `tag_registry.jsonl`)
- TCK-20260720-TAG-RELEVANCE-VERIFY (advisory tag-fit self-check, relevant context for metadata-signal decisions)
- TCK-20260804-SKILL-JS-PHASE-SYNC, TCK-20260804-CREATE-TICKETS-SKILL-SYNC, TCK-20260804-SKILL-DRIFT-DETECTION (same session, same "documented-but-unexecuted behavior" bug class as the newly-found `SKILL.md:70` Security-Review gap)
- TCK-20260805-SKILLS-DOC-STALENESS-FIX (DONE — closed the docs/ai/skills.md staleness scope item)
- TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX (unrelated sibling fix from the same day, no dependency)

## Related Docs
- `docs/ai/skills.md`
- `docs/guides/ticket_tagging.md`
- CLAUDE.md ("Proactive Tool Use" table)
- `docs/mechanics/02_combat_laws.md`, `docs/simulation/domains/combat_engagement_contract.md` (combat gap evidence)
- `docs/cognition/README.md`, `docs/strategy/bounded_cognition_decision_flow.md` (cognition/strategy gap evidence)
- `docs/mechanics/01_entity_anatomy.md`, `docs/mechanics/attribute_progression_contract.md` (progression/entities gap evidence)
- `docs/mechanics/03_economic_laws.md` (systems gap evidence)
- `docs/engine/kernel.md`, `docs/engine/authoritative_pipeline.md`, `docs/core/dirty_state_and_dependency.md`, `docs/engine/candidate_selection.md` (tick/entity-resolve pipeline — foundational context any bespoke combat/progression/cognition skill must correctly reference)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SKILL-TRIGGER-COVERAGE/` (none — hotfix tier)
- `stored_artifacts/TCK-20260705-SIX-SKILLS-INVESTIGATION/`
- `stored_artifacts/TCK-20260705-TAG-SKILL-SUGGEST/`

## Related Code Areas
- `.claude/skills/*/SKILL.md`
- `.claude/agents/ticket-scoper.md`, `.claude/agents/investigator.md`
- `.claude/workflows/create-tickets.js`, `.claude/workflows/implement-ticket.js`
- `tools/agent-monitoring/`
- CLAUDE.md

## Assumptions / Open Questions
Whether the root cause of the dual-mechanism non-firing is a hand-orchestration gap (same class
as this session's SKILL.md fixes) or something else (e.g. genuinely no applicable work has
occurred since 2026-07-04) is the central open question Investigate must resolve with real
evidence, not assumed here.

## Implementation Notes
(epic — no direct implementation; child tickets carry implementation)

## Test Summary
(epic — no direct implementation)

## Files Changed
(epic — no direct implementation)

## Completion Summary
All 15 child tickets landed DONE, hand-orchestrated directly (no subagents, after the session's
hard 200-agent spawn cap was hit and the user explicitly chose to continue solo). Delivered:

- **Real bug fixed**: `implement-ticket/SKILL.md`'s hotfix-summary paragraph, which had already
  caused a real Security-Review miss on `TCK-20260731-GATE-BYPASS-HARDENING`.
- **Gate-conversion decision**: investigated all 3 candidate skills individually rather than
  blanket-copying `security`'s pattern; only `python-performance-optimization` had a real
  checkable verdict shape, and even that was routed through the existing Test-phase gate rather
  than a duplicate new phase.
- **Content sourcing**: 6 skills investigated for popular-vs-bespoke sourcing; `backend-testing`
  bespoke-replaced (confirmed actively misleading Node/Express content); 5 others adapted with
  real in-repo cross-references; zero skills swapped for an unverified external source (real
  WebSearch consistently found no clearly-superior, verifiable alternative).
- **New agent-monitoring tooling**: `security_gate_firing_check.py` and `skill_usage_metric.py`,
  both following `retrieval_baseline_metrics.py`'s established house pattern.
- **6 new bespoke domain skills** authored, each sourced from real Mechanics Bible/contract docs,
  correctly cross-referencing the 32-phase authoritative pipeline's relevant phases: observability,
  simq-dev, systems-economy, combat-mechanics, cognition-strategy, progression-entities — closing
  every confirmed gap from the domain-coverage sweep.
- **2 decision-only tickets** (frontend-design trigger, Codex event-trace gap) resolved with real
  evidence rather than either reflexively reopening/fixing or silently deferring.
- **A real, previously-undocumented mechanism discovered mid-epic**: `.agents/skills/` is a
  generated Codex-provider mirror requiring explicit `agent-orchestration/skills.yaml` contract
  registration — applied consistently across all 6 new skills, and incidentally caught up 4 other
  skills' mirrors that had silently drifted from earlier-session edits.
- **A real, disclosed, unresolved gap found and escalated, not fixed inline**: 2 `DONE` tickets
  with zero `agent-monitoring/runs.jsonl` records — filed as
  `TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT` rather than guessed at or silently ignored.

Real process errors caught and fixed along the way, disclosed rather than hidden: 2 instances of
conflating a registered *tag* value with an unregistered *layer* value in staging-artifact
frontmatter (caught at Verify both times); 1 missed todos→inprogress file move (caught at Verify).
No known material gap remains in the epic's own scope. `tickets/todos/skill-catalog-modernization/`
moved to `tickets/done/skill-catalog-modernization/` (only `SEQUENCE.md` remained).
