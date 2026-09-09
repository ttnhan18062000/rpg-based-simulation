---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED
phase: open
date: 2026-09-09
tags: [world, content]
---

# TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED

## Title
`CampaignOrchestrator._build_initial_state()` compiles `information_source_profiles`/`pending_information_responses` but never threads them into the returned state

## Status
OPEN

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
- [ ] Real test evidence confirms the gap (fails before fix, passes after).
- [ ] Both `_build_initial_state()` branches thread the compiled `information_source_profiles`/
      `pending_information_responses` into the returned state.
- [ ] `information_belief` phase confirmed to actually consume the now-populated data in a real
      Campaign episode run (not just that the field is non-empty on the constructed state).
- [ ] No regression in `tests/unit/domains/campaigns/ tests/integration/campaigns/` or the
      `information_belief`/`InformationBeliefPhase` own test suite.

## Related Tickets
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (origin of this finding)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()`, both branches)
- `src/engine/pipeline.py` (`information_belief` phase, the real consumer)
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, where the data is genuinely computed)

## Assumptions / Open Questions
None — scope is a straightforward, well-evidenced fix once picked up.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
