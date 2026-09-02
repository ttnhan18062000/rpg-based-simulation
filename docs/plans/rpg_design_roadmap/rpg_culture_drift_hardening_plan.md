---
status: active
layer: world
authority: P1
audience: agent
tags: [content, architecture]
---

# Plan — Culture Drift Hardening: correcting the "dormant substrate" framing

**Status:** high-level plan, not yet ticketed. Item 3 of the 5-item hardening backlog (see the parent
roadmap's "Hardening backlog" section). **This item turned out smaller than the other two** — the finding
is a documentation correction, not a new-architecture scoping task, because the thing being described as
dormant turns out to already be built, live, tested, and documented.

**Source:** direct investigation, 2026-09-02, of `docs/world/culture_drift_contract.md`,
`docs/mechanics/05_world_evolution.md` §7, `docs/parity_ledger/world_dynamics.yaml` (`WORLD-CULT-001/002/003`),
`src/domains/culture/{model,deriver,exporter,applicator}.py`, `src/domains/campaigns/orchestrator.py`,
`src/domains/campaigns/state.py`.

## Problem

`docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`, `rpg_m5_memory_reputation_epic.md`, and
`rpg_m6_political_identity_epic.md` all describe `CultureDeriver`/`CulturalBiasApplicator` as a "dormant
substrate" that M4 must "activate" before M5's ideas 57/62 and M6's idea 56 can build on it. **This framing
is false.** Direct investigation found:

- `docs/world/culture_drift_contract.md` is marked `Status: AUTHORITATIVE — E62A–E62C complete`, and the
  Mechanics Bible itself already documents the same formulas/axes independently
  (`docs/mechanics/05_world_evolution.md` §7 "Cultural Drift (E62)").
- Real code exists at `src/domains/culture/{model,deriver,exporter,applicator}.py`.
- Three parity-ledger entries (`WORLD-CULT-001/002/003`) are `status: verified` with real, checkable
  citations — unlike hardening item #2's fabricated `SUB-327`, these cite real file:line evidence and real
  test files, all confirmed to exist on disk (`tests/unit/domains/culture/test_culture_deriver.py`,
  `test_culture_applicator.py`, `tests/integration/culture/test_culture_drift_acceptance.py`).
- M4's own specific claim — *"Culture Drift's `CultureDeriver`/`CulturalBiasApplicator`... has zero live
  callers anywhere"* (`rpg_m4_beyond_city_epic.md:63`) — is directly falsifiable and false:
  `src/domains/campaigns/orchestrator.py:226-230` calls `CultureDriftExporter.export()` from
  `_advance_state()`, a real, live call site, with an explicit `# E62B: derive and persist culture drift at
  episode boundary` comment.

## The real, narrower gap

The live call site only fires inside `CampaignOrchestrator._advance_state()` — multi-episode Campaign
episode-boundary logic, not ordinary continuous-tick simulation. This session's own M9 corpus-test-coverage
investigation already found: *"4 ideas (53, 55, 58, 62) can only be tested by a real multi-episode Campaign
run, and `CampaignScorecardEvaluator` itself has zero fields today that would even catch a failure in any of
them."* So the defensible finding is: **the substrate is live and correct, but reachable only through a
specialized, undertested Campaign-mode path, not the default simulation mode** — a reachability/testing
question, not a "build it" question.

`region_cultures: Dict[str, CultureCarryForward]` (`src/domains/campaigns/state.py`) is real, populated,
durable state whenever a Campaign actually runs multi-episode. M5's idea 57's own doc already independently
confirms the writer side works ("`CultureDeriver` already does [read Chronicle's output back]"). This means
ideas 56 (M6), 57/62 (M5), and 61 (M4) most likely need only a **read-side consumer** of `region_cultures`,
not new derivation/bias-application machinery — though this is not independently confirmed against each
idea's exact needs; that check belongs to this plan's own scope, not assumed here.

## Scope (not yet broken into child tickets)

1. **Correct the "dormant"/"zero live callers"/"needs activation" language** in
   `rpg_m4_beyond_city_epic.md`, `rpg_m5_memory_reputation_epic.md`, `rpg_m6_political_identity_epic.md`,
   and the parent roadmap wherever they currently assert this — replace with the real finding: live,
   correct, but Campaign-mode-only reachable.
2. **Answer the real open question: does any of the 21 real corpus worlds ever run multi-episode
   Campaign mode?** If none do, Culture Drift is code-correct but never actually exercised in practice
   today — a real gap, but a testing/corpus gap, not an implementation gap. This determines whether M9's
   already-documented `CampaignScorecardEvaluator` gap needs to be closed before M5/M6's culture-dependent
   ideas can be trusted in practice.
3. **Scope each of ideas 56 (M6), 57/62 (M5), and 61 (M4) against `region_cultures` directly** — confirm
   each is a straightforward read-side consumer of existing state, and name the specific field(s)/method(s)
   each would read, rather than leaving "culture drift as an input" as a vague dependency.
4. **Reassign the word "activate."** M4's epic doc should no longer claim ownership of "activating" a
   dormant substrate — if any of ideas 56/57/61/62 need something Culture Drift doesn't yet provide (e.g. a
   direct non-Campaign-mode trigger), name that specifically rather than reusing the generic "activation"
   framing that turned out to be inaccurate.

## Out of Scope

- Building any new Culture Drift mechanism — the substrate is confirmed complete and correct as-is.
- Building a non-Campaign-mode trigger for `CultureDriftExporter.export()` unless step 3 above finds a real
  idea that needs one — not assumed necessary by this plan.
- Closing `CampaignScorecardEvaluator`'s field gap (M9's own finding) — this plan only determines whether
  that gap blocks M5/M6's culture-dependent ideas in practice; closing it is M9's own scope.

## Acceptance Signal

- `rpg_m4_beyond_city_epic.md`, `rpg_m5_memory_reputation_epic.md`, `rpg_m6_political_identity_epic.md`, and
  the roadmap no longer describe Culture Drift as dormant or needing activation.
- A definite answer exists for whether any real corpus world runs multi-episode Campaign mode today.
- Ideas 56, 57, 61, and 62 each have a named, specific `region_cultures` read requirement recorded, not a
  vague "depends on Culture Drift" pointer.

## References

- `docs/world/culture_drift_contract.md` — `AUTHORITATIVE`, E62A-E62C complete
- `docs/mechanics/05_world_evolution.md` §7 — Cultural Drift (E62), Bible-level formula documentation
- `docs/parity_ledger/world_dynamics.yaml:1195-1234` — `WORLD-CULT-001/002/003`, real citations, confirmed
  test files exist
- `src/domains/culture/{model,deriver,exporter,applicator}.py` — real implementation
- `src/domains/campaigns/orchestrator.py:226-230` — the real, live call site (`_advance_state()`)
- `src/domains/campaigns/state.py` — `region_cultures: Dict[str, CultureCarryForward]`
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` — `CampaignScorecardEvaluator`'s
  field gap, the real reachability question this plan depends on
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Hardening backlog section
