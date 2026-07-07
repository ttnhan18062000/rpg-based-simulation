---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC
phase: open
date: 2026-07-07T16:31:09Z
tags: [simulation-quality, documentation, world]
---

# TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC

## Title
Document the pillar-completeness research conclusion: no new top-level SimQ pillar is justified

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2 performed pillar-completeness
research (per user request: "consideration of new pillars if warranted") and reached a conclusion
that is not yet recorded anywhere durable: **no new top-level pillar is justified.** Four candidate
dimensions were checked and each is already owned by a dedicated system outside SimQ:

- **Determinism/replay-fidelity** — owned by `tests/certification/`, `tests/integration/kernel/`
  (including a dedicated `test_long_run_determinism.py`), `tests/integration/observability/
  test_phase28_observability_determinism.py`, `tests/unit/kernel/test_replay_determinism.py`
  (investigation.md §2.2)
- **Performance/tick-time budget** — owned by `tests/perf/` (14+ files) plus per-phase budget tests,
  tied to `docs/engine/performance_contract.md`'s hardware classes; SimQ's own overhead is separately
  budgeted in `tests/simulation_quality/test_performance.py` (investigation.md §2.3)
- **Save/checkpoint integrity** — owned by `tests/integration/kernel/
  test_checkpoint_reproducibility.py` and `tests/unit/engine/test_scenario_checkpointer.py`
  (investigation.md §2.4)
- **Content/catalog health** — owned by `src/content/validator.py`'s `CAT-REL-001` through
  `CAT-REL-011` rules (investigation.md §2.5)

The contract's own §1 ("What this module is NOT") already scopes SimQ away from determinism and
performance explicitly; a SimQ pillar covering either would duplicate existing test domains and
violate that scope boundary.

One genuine, narrow gap **was** found (investigation.md §2.6): `building_sabotage` (pipeline phase
15, `src/engine/sabotage.py::BuildingSabotageSystem.resolve()`) is a live, non-dead mechanic —
mutates `building_updates` (hp_delta, functional_set) on `SABOTAGE`/`ENTITY_ACT` intents — exercised
by real corpus content (`urban_political`'s resolved world spec and
`data/content/world_modules/trading_company_hub.yaml`), but emits no
`ObservabilityEventEnvelope`/`SimulationEvent` and is invisible to all 10 pillars'
event-type/tag lists, including WORLD's. Per the contract's own §7.1 vs §7.2 extensibility
distinction, this is a **new scoring rule under the existing WORLD pillar**, not grounds for an 11th
top-level pillar — `FACTION` is a plausible secondary owner (given `urban_political`'s
faction-conflict framing) but WORLD is the cleaner primary per the §7.3 conflict-detection rule (no
existing pillar currently claims building-state events). This finding is tracked separately as
`TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`, which cites this ticket's output as its evidence
source.

## Scope
1. Read `docs/simulation_quality/quality_scoring_contract.md` §7 (Extensibility Protocol, lines
   1008-1067: §7.1 Adding a New Pillar, §7.2 Adding a Scoring Rule to an Existing Pillar, §7.3
   Conflict Detection Rules, §7.4 Configuring Quality Profiles) to confirm the natural home for this
   conclusion. Per that read (already performed during epic scoping): §7 is the extensibility
   protocol itself — a completed pillar-completeness audit is a direct, citable precedent for how
   that protocol was applied, so add a new **§7.5 "Pillar Completeness Audit (2026-07)"** subsection
   to `quality_scoring_contract.md` rather than creating a new standalone doc. This keeps the
   authoritative extensibility section self-documenting with its own precedent case, avoiding a
   second doc that could drift out of sync with §7's rules over time.
2. In the new §7.5 subsection, document:
   - The 4 candidate dimensions checked and exactly which existing system owns each (cite the file
     lists above / investigation.md §2.2-2.5 directly, verified against current repo state — do not
     just copy the investigation's text without re-confirming the cited files still exist).
   - The `building_sabotage` finding and why it is a WORLD-pillar rule addition, not a new pillar
     (cite investigation.md §2.6 and the contract's own §7.1/§7.2/§7.3 rules being applied).
   - The overall conclusion: no new top-level pillar is justified at this time.
3. Cross-reference `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL` from the new §7.5 subsection as the
   ticket implementing the one identified follow-up.
4. Run `make knowledge-index-update` since this modifies a file under `docs/`.

## Out of Scope
- Implementing the `building_sabotage` event emission or WORLD-pillar scoring rule itself — that is
  `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`'s scope; this ticket is documentation-only.
- Re-running the pillar-completeness research itself — investigation.md §2 already performed it;
  this ticket transcribes and durably records the conclusion, re-verifying only that cited file
  paths still exist (not re-deriving the analysis from scratch).
- Any change to `quality_scoring_contract.md` outside the new §7.5 subsection.
- Creating a second, separate doc under `docs/simulation_quality/` — Scope item 1 already decided
  against this in favor of extending §7 in place.

## Acceptance Criteria
- [ ] `docs/simulation_quality/quality_scoring_contract.md` has a new §7.5 subsection documenting
      the pillar-completeness conclusion
- [ ] All 4 candidate dimensions and their owning systems are cited with currently-valid file paths
      (re-verified, not just copied from investigation.md)
- [ ] The `building_sabotage` finding is documented with a cross-reference to
      `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`
- [ ] `make knowledge-index-update` run successfully after the doc change
- [ ] `python3 tools/validate_frontmatter.py docs/simulation_quality/quality_scoring_contract.md
      --content-type doc` passes (frontmatter unaffected by a body-only addition, but re-verify)

## Related Tickets
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC (parent epic)
- TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL — depends on this ticket's output for citation; must
  land after this one

## Related Docs
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §2 (full pillar-completeness
  research: method §2.1, 4 redundant candidates §2.2-2.5, the `building_sabotage` finding §2.6,
  overall conclusion §2.7)
- `docs/simulation_quality/quality_scoring_contract.md` §1 ("What this module is NOT" scope table),
  §7 (Extensibility Protocol — target location for this ticket's new §7.5)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` (see Related Docs)

## Related Code Areas
None — documentation-only ticket. (`src/engine/sabotage.py` is cited but not modified here; its
modification is `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`'s scope.)

## Assumptions / Open Questions
- Assumes the 4 "owning system" file lists from investigation.md §2.2-2.5 still accurately reflect
  the repo at implementation time — Scope item 2 requires re-confirming these paths exist, not
  trusting the investigation's snapshot blindly (self-evident intent, hence hotfix tier; if
  re-verification finds a cited file has moved/been deleted, correct the citation rather than
  treating it as a scope-invalidating surprise).

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
