---
status: historical
layer: simulation
authority: P2
audience: developer
maturity: shipped
date: 2026-07-03
archived: 2026-08-04
tags: [idea, information, belief, simulation_quality, dead-code, cognition, self-model]
---

# Idea: Wire a Reachable Trigger for InformationBeliefPhase

> **Maturity: IDEA** — Not scheduled. Blocks INFORMATION pillar activation beyond scaffolding
> (`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`) and is the direct scope of the follow-up ticket
> `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`.

---

## Problem

The INFORMATION pillar grades C across all 30 SimQ calibration runs. The original diagnosis
(`TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`) named a "dual gate": `ENABLE_BELIEF_ASSIMILATION=OFF`
short-circuits `InformationBeliefPhase`, and `AuthoritativeState.information_source_profiles` is
never populated in any compiled world. `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` was scoped to lift
both gates.

Investigation on 2026-07-03 (see `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/investigation.md`)
found this diagnosis is incomplete: **even with both named gates lifted, `InformationBeliefPhase.apply()`
has zero reachable trigger conditions in the current engine.** Seeding profiles and flipping the flag
compiles cleanly and passes `make evaluate --dry-run`, but produces **zero** `belief_assimilated` /
`lead_certainty_updated` events — the same C grade, just with previously-dead scaffolding now present
but still unused.

## Current Behavior (as of 2026-07-03)

`InformationBeliefPhase.apply()` (`src/domains/information/phase.py:28-110`) has two branches, both dead:

- **Branch A — assimilate a pending response** (`phase.py:54-81`): requires a non-empty entry in
  `state.pending_information_responses` (`src/core/state.py:1144`, read at `src/engine/pipeline.py:151`).
  Grepping all of `src/` found **zero writers** to this field anywhere in the engine. It is permanently `[]`.
- **Branch B — route a new query** (`phase.py:83-105`): requires `actor.self_model.knowledge.unknowns`
  (`src/core/self_model.py:179`) to be non-empty. The only writer, `KnowledgeModelService.assimilate()`
  (`src/cognition/knowledge_model.py:93-101`), is called from `SelfModelUpdatePhase.apply()`
  (`src/cognition/self_model_phase.py:32-56`) — but that call hardcodes `events=[]`
  (`self_model_phase.py:50`, re-verified 2026-07-03 during
  `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` Step 9 — line shifted from the original `:47`
  citation), so the assimilation loop inside `run()` never executes. `unknowns` is
  unreachable dead state; no code path in the standard pipeline ever populates it.

Only `belief_assimilated` is emitted from Branch A (`phase.py:76-78`, `last_assimilated_tick`, read by
`src/observability/event_extractor.py:286`); Branch B never sets it, so `belief_assimilated` is doubly
unreachable. `lead_certainty_updated` (`event_extractor.py:415-428`) fires from a lead-certainty state
diff, independent of `InformationBeliefPhase` — but every candidate producer of that diff is itself dead
or orphaned:

- `InformationNeedDetector.detect_and_generate()` (`src/engine/domain/cognition_extras.py:36-98`) —
  docstring admits it is not wired; zero callers found anywhere in `src/`. Also depends on `unknowns`
  (dead, above).
- `PaidInformationTransactionSystem.enforce()` (`src/engine/pipeline_phases/paid_information.py:74-183`)
  — wired unconditionally, but requires `state.information_providers` (a separate durable field from
  `information_source_profiles`, Epic 4.2B) and an active `INFORMATION_SEEKING` project, which only the
  dead `InformationNeedDetector` or the orphaned `GuildAction.visit()` (`src/town/guild.py:11-`, zero
  callers) ever create. Its `LeadState.id` is also unique-per-tick, so even firing once would never
  trigger `lead_certainty_updated`'s prior/current-id diff — only `paid_information_transaction` could
  fire from this path, on first purchase.
- `StrategicIntelligenceSystem.fused_strategic_pass()`'s belief confirmation/contradiction block
  (`src/systems/strategic_systems/intelligence.py:314-347`) can mutate lead certainty in place, but only
  for pre-existing `kind == "location"` leads — and nothing in its reach creates such leads either.

**Conclusion**: every code path that could ever produce `belief_assimilated`, `lead_certainty_updated`,
or `paid_information_transaction` in a calibration run is either flag-gated OFF, reads permanently-empty
state, or is orphaned code with no caller. This matches `docs/simulation_quality/event_type_coverage.md`
showing `calibration_hits: 0` for all nine related event types.

## Options Considered

1. **Wire a minimal reachable trigger for Branch B.** Seed at least one entity's
   `self_model.knowledge.unknowns` at compile time (mirrors how the FACTION ticket seeded
   `tension_level` directly into durable state), or fix `SelfModelUpdatePhase.apply()`'s hardcoded
   `events=[]` so the existing assimilation loop can run. Most surgical — reuses Branch B without
   touching the two separately-gated systems below it. **Risk**: `SelfModelUpdatePhase` and the
   self-model cognition pipeline are shared across every world, not just `urban_political` — a fix
   there needs its own regression sweep across all calibration worlds, and interacts with the
   separately-gated `ENABLE_SELF_MODEL_COGNITION` flag (also OFF by default, not set in
   `urban_political`'s profile).
2. **Retarget the acceptance criterion to `paid_information_transaction`.** This path is already
   wired unconditionally (no feature flag) but requires: (a) seeding `state.information_providers`
   (`InformationProviderState`, a *different* field from `information_source_profiles` — see
   Anti-Drift note below) and (b) wiring `InformationNeedDetector.detect_and_generate()` into
   `CognitionDomain.execute_brain()` per its own docstring's instructions, or reachability via
   `GuildAction.visit()` (currently orphaned). Different domain (information *providers*, not
   *sources*) and a different orphaned entry point, but also confined to the information domain
   rather than touching shared self-model cognition code.
3. **Ship scaffolding only, defer trigger wiring.** (Chosen for `TCK-20260702-SIMQ-UPLIFT2-INFORMATION`,
   per user direction 2026-07-03.) Ship the schema/compiler/resolver plumbing for
   `information_source_profiles` and the corrected world content — real, needed groundwork regardless
   of which trigger-wiring option is eventually chosen — without touching shared engine paths
   (`SelfModelUpdatePhase`, `InformationNeedDetector`) under a ticket that wasn't scoped or
   architecture-reviewed for that work. Mirrors the `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` precedent
   (document a structurally-inactive pillar honestly rather than force-activating it under time
   pressure).

## Recommendation

Do not decide between options 1 and 2 inside this idea doc — that is exactly the kind of judgment call
that needs its own investigation → plan → architecture-review cycle, run as
`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`. This doc's job is to make sure that ticket starts from
the evidence above instead of re-discovering it. A rough lean: option 1 (Branch B / self-model wiring)
is more architecturally central (self-model cognition arguably *should* populate `unknowns` regardless
of INFORMATION-pillar scoring) but has wider blast radius across every world; option 2 (paid-information
path) is more contained to the information domain but requires wiring two separate orphaned pieces
(`InformationNeedDetector` + `information_providers` seeding) to reach a single event type. Whoever picks
this ticket up should re-verify both are still accurate against current `src/` before committing to a
plan — this investigation is a snapshot as of 2026-07-03, immediately after the FACTION ticket's
compiler-plumbing pattern was established as a reusable template.

## Anti-Drift Hazards

- Do not conflate `state.information_providers` (`InformationProviderState`, `state.py:1150`, consumed
  by `PaidInformationTransactionSystem`) with `state.information_source_profiles`
  (`InformationSourceProfile`, `state.py:1145`, consumed by `InformationBeliefPhase`/
  `InformationQueryRouter`) — two separate durable registries feeding two separate, independently-gated
  systems. Seeding one does not seed the other.
- Any fix to `SelfModelUpdatePhase.apply()`'s `events=[]` must be regression-tested against every
  calibration world, not just `urban_political` — it is shared cognition-pipeline code.
- Do not widen either option into "the full belief-assimilation response cycle" — the original
  ticket's Out of Scope excluded a full information marketplace / NPC query-response loop, and that
  boundary should hold for the follow-up too unless a human decision explicitly widens it.

## Related

- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/investigation.md` — full investigation
  writeup with file:line references (source of truth for this doc's claims)
- `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` — shipped the scaffolding (schema/compiler/resolver plumbing
  + corrected world content); did not attempt trigger wiring. Recalibrated 2026-07-03 across all 7
  `urban_political_*` scenarios: confirmed `information_source_profiles` compiles with 2 entries and
  `ENABLE_BELIEF_ASSIMILATION=ON`, and confirmed `belief_assimilated`/`lead_certainty_updated`
  calibration_hits remain 0 in every run (expected). Parity ledger entry
  `docs/parity_ledger/infrastructure.yaml::INFRA-256` documents the scaffolding as
  scaffolding-verified/pillar-inactive (extends `INFRA-245`) — this is the concrete ID referenced
  by the follow-up ticket below (no longer a placeholder).
- `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` — follow-up ticket scoped to resolve this idea doc's
  open question
- `TCK-20260702-SIMQ-UPLIFT2-FACTION` — sibling ticket; established the schema/compiler/resolver
  plumbing template this idea doc's option 1/2 analysis assumes as a starting point
- `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` — precedent for "document honestly, don't force-activate"

---

*Raised: 2026-07-03. Blocks INFORMATION pillar grade improvement beyond scaffolding.*
