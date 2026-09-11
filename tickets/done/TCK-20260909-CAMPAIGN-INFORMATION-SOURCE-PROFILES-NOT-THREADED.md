---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED
phase: done
date: 2026-09-09
tags: [world, content]
---

# TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED

## Title
`CampaignOrchestrator._build_initial_state()` compiled `information_source_profiles`/`pending_information_responses` but never threaded them into the returned state — CLOSED PARTIAL: `information_source_profiles` fixed and shipped; `pending_information_responses` split out to `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` after a real actor-ID mismatch made the obvious naive fix unsafe

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own investigation, at peer
review's explicit request to check whether these Pattern-6 fields actually reach their consumers.
`WorldCompiler.compile()` (called by `_build_initial_state()` in both its episode-0 and
survivor-reconstruction branches, for `regions`/`places`) genuinely computes
`information_source_profiles`/`pending_information_responses` from the world composition's own
declared data (`src/worldassembly/resolver.py:681`; `src/worldbuilding/compiler.py:643-732`) — but
neither branch's own final `AuthoritativeState(...)` construction
(`src/domains/campaigns/orchestrator.py`, both the episode-0 return around line 766 and the
survivor-branch return around line 958) threads `information_source_profiles=`/
`pending_information_responses=` from the compiled result. Only `regions=`/`places=` are threaded.

This is a real, live gap: `src/engine/pipeline.py:199`'s `information_belief` phase reads
`state.information_source_profiles` directly every tick
(`source_profiles = getattr(state, "information_source_profiles", [])`, feeding
`InformationBeliefPhase.apply()`), and `src/engine/apply.py:500` genuinely carries the field
forward tick-to-tick once set (`information_source_profiles=prior_state.information_source_profiles`)
— but for every Campaign-mode episode, it starts at its dataclass default (`[]`, per
`src/core/state.py:1361`) regardless of what the world composition declares, and stays empty for
the entire episode. `frontier_living_world` (the real `campaign_life_arc` world) does declare a
real `information_source_profiles` entry (`town_notice_board`) — so this is not a moot/empty-input
question, it's a genuine "declared but never delivered" gap.

## Scope
- Confirm the gap directly (a real test: build a Campaign episode's initial state for a world
  composition with a non-empty `information_source_profiles`, assert the compiled value is
  actually present in the returned `AuthoritativeState` — expect it to fail before any fix).
- Thread `information_source_profiles=compiled_state.information_source_profiles` and
  `pending_information_responses=compiled_state.pending_information_responses` (confirm exact
  field names on the compiled `AuthoritativeState`/`WorldSpec` result during Investigate) into
  both branches' own `AuthoritativeState(...)` construction, alongside the existing `regions=`/
  `places=` threading.
- Confirm no downstream consumer assumes these fields stay empty for Campaign mode specifically
  (check `information_belief`'s own feature flag — `ENABLE_BELIEF_ASSIMILATION` — is not itself
  gated OFF for Campaign in a way that makes this moot; if it is, note that instead of threading
  dead data).

## Out of Scope
- Any other Pattern-6 field's own carry-forward correctness (the survivor branch already threads
  several — `region_loyalty_pressure`, `region_culture_states`, `entity_legend_facts`,
  `entity_belief_institutions`, `event_fidelity` — not re-audited here unless this investigation
  surfaces a reason to).
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own entity-spawn scope — this is a
  sibling, independently-scoped gap found during that ticket's own investigation, not merged into
  it.

## Acceptance Criteria
- [x] Real test evidence confirms the gap (fails before fix, passes after). — Confirmed via a
      direct probe against a real `frontier_living_world` episode before any fix: both fields
      empty on the returned state despite real declared content. Fixed for
      `information_source_profiles`; re-probed after the fix, non-empty and correct.
- [x] Both `_build_initial_state()` branches thread the compiled `information_source_profiles`
      into the returned state. — **Scope narrowed during implementation, per peer review**: only
      `information_source_profiles` is threaded. `pending_information_responses` is deliberately
      NOT threaded — real evidence (below) showed the obvious identical fix would silently
      misdeliver seeded facts to the wrong entity. Split into
      `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` rather than shipped
      naively or quietly dropped.
- [x] `information_belief` phase confirmed to actually consume the now-populated data in a real
      Campaign episode run (not just that the field is non-empty on the constructed state). — A
      full real-episode run doesn't reliably exercise the routing branch (it depends on an
      unrelated strategic-cognition precondition, an actor having an unresolved "unknown" —
      confirmed empirically: a real 70-tick run produced zero routing activity even with the
      fix applied, because no actor happened to have an unknown in that window). Instead proved
      the real consumer function directly: `InformationQueryRouter.route()` (the exact function
      `InformationBeliefPhase.apply()` calls) genuinely returns a `town_notice_board` candidate
      from the now-threaded `state.information_source_profiles` for a real `material_source`
      query — the data path is live and consumable, isolated from the separate, out-of-scope
      question of when an actor organically triggers it.
- [x] No regression in `tests/unit/domains/campaigns/ tests/integration/campaigns/` or the
      `information_belief`/`InformationBeliefPhase` own test suite. — 158 passed (campaigns
      scope), 40 passed (`tests/unit/domains/information/ tests/integration/domains/information/`),
      0 failed.

## Related Tickets
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (origin of this finding)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (new — the real fix for
  the field split out of this ticket's own scope, carrying the `actor_id=9`-resolves-to-a-
  goblin-not-the-guard evidence)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()`, both branches)
- `src/engine/pipeline.py` (`information_belief` phase, the real consumer)
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, where the data is genuinely computed)

## Assumptions / Open Questions
~~None — scope is a straightforward, well-evidenced fix once picked up.~~ **This assumption was
wrong for `pending_information_responses`** — real evidence found during implementation, not
predicted here. `information_source_profiles` genuinely was straightforward; its sibling field
was not, for a reason the original investigation had no way to anticipate (a completely separate
entity-numbering scheme). See Completion Summary and
`TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH`.

## Implementation Notes
Also verified, per peer review, whether `information_source_profiles`/`pending_information_responses`
were the deliberately-"Bounded/single-fire" category (not meant to be carried forward) before
treating "not threaded" as a bug — `docs/guidelines/design_patterns.md`'s own Pattern 6 table
(INFRA-256/INFRA-257) settles this directly: `information_source_profiles` is carried forward
every tick by `apply.py:500`, same category as `regions`/`places`; `pending_information_responses`
is genuinely single-fire (fires exactly once at tick 0, confirmed absent from `apply.py`'s own
tick-to-tick `AuthoritativeState(...)` reconstruction call) — which makes its absence at episode
start *more* consequential, not less, since tick 0 is its only chance to ever fire. Both belong in
Campaign's initial state; the original ticket's diagnosis was correct on this point.

1. **`src/domains/campaigns/orchestrator.py`** — threaded
   `information_source_profiles=compiled_state.information_source_profiles` into both
   `_build_initial_state()` branches (episode-0 and survivor-reconstruction).
2. **Discovered and reverted an unsafe naive fix before shipping it**: initially threaded
   `pending_information_responses=compiled_state.pending_information_responses` identically,
   matching the ticket's own original Scope. Verified with a real probe (not assumed) that
   `WorldCompiler.compile()` resolves each entry's `target_population_id` into an `actor_id` by
   matching `population_id` against **its own internal, separate entity-compilation pipeline**
   (`compiler.py:546`/`660-664`) — completely different from Campaign's actual catalog-native
   spawn pipeline (`WorldEntitySpawner`), which never sets `population_id` at all. Confirmed the
   real consequence with real data: for `frontier_living_world`, the compiler resolves
   `target_population_id='frontier_village_population_frontier_guard'` to `actor_id=9`; in
   Campaign's own real spawned roster for the identical composition/seed, `entity_id=9` is a
   **goblin_raider**, not the guard. Reverted this half of the fix (left commented, explaining
   why) rather than shipping a silent-misdelivery bug or quietly dropping the field with no
   record. Filed `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` per peer
   review, framed as a tripwire (leads with "the obvious fix is wrong," not "this field isn't
   threaded") so the next person who spots this doesn't independently rediscover and ship the
   same unsafe fix.
3. **Cross-referenced with `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`**
   (Batch B): both are instances of the same root cause — the catalog spawn path
   (`WorldEntitySpawner`) doesn't carry `PopulationSpec` identity through (no `population_id` tag,
   no `count` expansion into individuals) — recorded in both tickets' own Related Tickets so
   whoever picks up either one can see a single fix to `WorldEntitySpawner`'s own output might
   close both.

## Test Summary
- Real pre-fix confirmation: direct probe against a real `frontier_living_world`
  `CampaignOrchestrator._build_initial_state()` call — both fields empty despite real declared
  content (`town_notice_board`, a real `pending_information_responses` entry).
- New tests, `tests/unit/domains/campaigns/test_campaign_orchestrator.py` (4 new):
  `information_source_profiles` threaded correctly in both branches; `pending_information_responses`
  deliberately still empty (negative assertion, not an oversight); the threaded profile is
  genuinely consumable by the real `InformationQueryRouter.route()` function.
- `pytest tests/unit/domains/campaigns/ tests/integration/campaigns/ -m "not slow and not extra_slow"`
  — 158 passed, 0 failed.
- `pytest tests/unit/domains/information/ tests/integration/domains/information/ -m "not slow and not extra_slow"`
  — 40 passed, 0 failed (the `information_belief`/`InformationBeliefPhase` own suite, per AC4).

## Files Changed
- `src/domains/campaigns/orchestrator.py` — `information_source_profiles` threaded into both
  `_build_initial_state()` branches; `pending_information_responses` left commented-out with
  rationale
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — 4 new tests
- `tickets/todos/TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH.md` — new
  follow-up ticket
- `tickets/todos/TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE.md` — added a
  cross-reference to the new ticket, naming the shared root cause

## Completion Summary
**Closed partial, by design, not by running out of scope.** `information_source_profiles` is
fixed and shipped — a genuine, real, well-evidenced hotfix exactly as originally scoped, closing a
gap that left this field permanently empty for every Campaign-mode episode regardless of declared
content. `pending_information_responses` was NOT shipped: implementing it directly surfaced a real
correctness bug the original investigation had no way to anticipate — the obvious, identical fix
would resolve `target_population_id` against a completely different, unused entity-numbering
scheme and silently deliver seeded knowledge to an unrelated entity (proven with real data, not
theorized). Reverting a fix that compiles, passes a naive test, and looks identical to its correct
sibling was the harder call than shipping it, and the right one — a visible "never fires" gap gets
noticed; a bug that fires and silently misdelivers plausible data looks like emergent behavior and
could survive undetected indefinitely. The real fix is split into its own ticket, deliberately
framed to lead with the proof that the obvious fix is wrong, and cross-referenced with a sibling
finding from Batch B that shares the same underlying root cause (the catalog spawn path not
carrying population identity through) — so whoever picks up either ticket can see one fix to
`WorldEntitySpawner` might close both rather than scoping each narrowly.

**One more distinction worth recording explicitly, per peer review** (not filed as its own
ticket — thin evidence, not a confirmed defect): AC3's own test proves
`information_source_profiles` is **threaded and consumable** (the real `InformationQueryRouter`
returns a real candidate from it) — it does NOT prove the data is **actually consumed in
practice** during a normal episode. A real 70-tick `frontier_living_world` run produced zero
routing activity even with the fix applied, because no actor happened to have an unresolved
`self_model.knowledge.unknowns` entry in that window — a separate strategic-cognition
precondition this ticket's own scope never claimed to guarantee. This batch has largely been
about exactly this gap (declared/threaded vs. actually observed), so it's worth stating rather
than leaving implicit: if a future investigation finds the router never fires in real play,
this note — not a fresh trace — is the starting point.
