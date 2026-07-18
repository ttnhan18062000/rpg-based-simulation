---
status: historical
layer: engine
authority: P0
audience: agent
ticket_id: TCK-20260627-P0A-ADVENTURE-FLAG
phase: done
date: 2026-06-27
tags: [feature-flags, adventure-routing, blocker, economic-measurement]
---

# TCK-20260627-P0A-ADVENTURE-FLAG

## Title
Decide and record `ENABLE_ADVENTURE_ROUTING` default policy

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`ENABLE_ADVENTURE_ROUTING` in `src/domains/optimization/feature_flags.py:16` defaults to `FeatureMode.OFF`. The entire adventure decision pipeline — route generation, opportunity scoring, blocker-penalty evaluation, strategic project assignment — is therefore inactive in all default simulation runs. Every economic balance measurement (D04 §6, D06 F1/F4) is running against a disabled pipeline. This is a blocker for all downstream economic and behavioural measurement.

## Scope
- Decide the intended default for `ENABLE_ADVENTURE_ROUTING` (and all 8 flags at lines 14–22):
  - **Option A**: Change default to `FeatureMode.ON` in `feature_flags.py` so non-test runs use the live pipeline.
  - **Option B**: Keep `OFF` as default, but document in `docs/engine/known_limitations.md` that balance/behavioural tests must explicitly set `ON` via their scenario definition or test fixture.
- Record the decision in `docs/guidelines/v2_intentional_divergences.md`.
- Update the parity ledger entry for `ENABLE_ADVENTURE_ROUTING` (`docs/parity_ledger/substrate.yaml` or closest relevant file).

## Out of Scope
- Changes to the adventure routing logic itself.
- Fixing P0-B (resource nodes) or P0-C (region_id assignment) — those are separate tickets.

## Acceptance Criteria
- [ ] `ENABLE_ADVENTURE_ROUTING` has a documented, intentional default state (either changed to `ON` or `OFF` with explicit rationale).
- [ ] If changed to `ON`: `make world-compile WORLD=urban_political && pytest tests/ -k adventure -m "not slow"` passes.
- [ ] If kept `OFF`: `docs/engine/known_limitations.md` documents that balance scenarios must set `ENABLE_ADVENTURE_ROUTING=ON` explicitly.
- [ ] Decision recorded in `docs/guidelines/v2_intentional_divergences.md` with rationale class.
- [ ] Relevant parity ledger entry updated.

## Related Tickets
- TCK-20260627-P0B-URBAN-RESOURCE-NODES (same blocker group)
- TCK-20260627-P0C-ENTITY-REGION-ASSIGN (same blocker group)
- TCK-20260627-P1B-QUEST-ACTIVATION (depends on this)

## Related Docs
- `docs/audits/D04_balance_tuning.md` §6.1
- `docs/guidelines/v2_intentional_divergences.md`
- `docs/engine/known_limitations.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E12A-BALANCE-MEASURE/` — documents root cause discovery

## Related Code Areas
- `src/domains/optimization/feature_flags.py:14–22`
- `src/domains/adventure/phase.py`

## Assumptions / Open Questions
- The audit recommends Option A (enable by default) as the primary fix, but the decision belongs to the project owner.
- All 8 flags at lines 14–22 likely need the same policy decision, not just `ENABLE_ADVENTURE_ROUTING`.

## Implementation Notes
Decision: **Option B** — Keep all 10 flags at `FeatureMode.OFF` (no code change to `feature_flags.py`).

Rationale: The sentinel test `test_adventure_routing_defaults_off()` in
`tests/integration/scenarios/test_balance_regression.py` was intentionally written to guard
this default. Changing to ON requires re-running `tools/balance_measure.py` to regenerate
E12A baseline constants, which is a separate workstream. The current OFF default is a
deliberate gated-rollout policy, not a bug.

Changes made:
- `docs/engine/known_limitations.md` §1.5: New section documenting all 10 flag defaults
  and the canonical opt-in pattern (`_build_kernel(enable_routing=True)`).
- `docs/guidelines/intentional_divergences.md` §DEV-002: Policy decision recorded with
  rationale class **Stabilized** and unblock condition.
- `docs/parity_ledger/infrastructure.yaml` INFRA-221: Parity ledger entry added with
  test_path pointing to the sentinel test.

## Test Summary
- Run existing adventure domain tests after the change: `pytest tests/ -k adventure -m "not slow"`.
- If Option A: run a 100-tick urban_political smoke run and assert `behavioral_event_count > 0`.

## Files Changed
- `docs/engine/known_limitations.md` — Added §1.5 documenting all 10 flag defaults and opt-in pattern
- `docs/guidelines/intentional_divergences.md` — Added DEV-002 with rationale class Stabilized
- `docs/parity_ledger/infrastructure.yaml` — Added INFRA-221 entry

## Completion Summary
Decision: **Option B** — All 10 Phase 10 feature flags remain `FeatureMode.OFF` by default. No code change to `feature_flags.py`. The sentinel test `test_adventure_routing_defaults_off()` already guards this default. Documentation added to `known_limitations.md` §1.5 with the canonical opt-in pattern (`_build_kernel(enable_routing=True)`). Policy decision recorded as DEV-002 in `intentional_divergences.md` (rationale: **Stabilized**). Parity ledger entry INFRA-221 added. All 6 relevant tests pass.
