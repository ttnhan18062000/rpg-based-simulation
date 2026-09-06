---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260905-DRIFTING-LOYALTY-SIGNAL
artifact_type: plan
date: 2026-09-05
tags: [world, faction]
---

# Plan — TCK-20260905-DRIFTING-LOYALTY-SIGNAL

## Ordered Steps

1. **New file `src/systems/social_systems/loyalty_drift.py`** — `LoyaltyDriftService`, a pure static
   service (mirrors `PartyLifecycleService`'s own style). One method:
   `compute_loyalty_pressure(campaign_state, region_id) -> float`, reading
   `CultureDriftImporter.get_culture(campaign_state, region_id)` and returning
   `.faction_conflict_exposure` if present, else `0.0`. No new Culture Drift derivation logic.
2. **Extend `PartyLifecycleService.effective_defection_threshold()`** (`party_lifecycle.py`) with a new
   optional `loyalty_pressure: float = 0.0` parameter. Formula: the existing composition bonus stays;
   subtract `round(loyalty_pressure * 2)` (mirrors the existing bonus's own `round(x * 2)` shape,
   opposite sign), floor the result at `1` (a group can never be defection-proof from grievances alone
   staying at threshold 0 — matches the pre-existing implicit floor of `DEFECTION_GRIEVANCE_THRESHOLD`
   never going below a sane minimum). Default `0.0` reproduces the exact pre-ticket behavior —
   backward-compatible, no behavior change for the one live caller until it's explicitly updated.
3. **Do NOT modify `GroupPhase.resolve()`'s live call site** (`groups.py:123`) — it has no
   `CampaignState` to supply a real `loyalty_pressure` value; passing a fabricated one would be worse
   than not wiring it at all. Disclose this explicitly in Implementation Notes.
4. **Tests** (new file `tests/unit/social/test_loyalty_drift.py` + additions to
   `tests/unit/social/test_party_lifecycle.py`) — per test_plan.md items 1-4, 6.
5. **Integration test** (new file `tests/integration/culture/test_loyalty_drift_campaign.py`) — item 5,
   against the real `campaign_life_arc.yaml` profile.
6. **Docs**: new subsection in `docs/world/culture_drift_contract.md` describing the read-side
   consumer and the disclosed live-wiring gap; status annotation on the M6 epic doc.
7. **Parity**: new entry in `docs/parity_ledger/social_narrative.yaml` via `tools/parity_ledger_writer.py`
   (never hand-edited), citing the real `test_path`s from steps 4-5.
8. **Disclosed follow-up**: file a small standalone ticket for "bridge `CampaignState` into the
   per-tick Kernel pipeline for `GroupPhase.resolve()`" if time permits — the real, larger gap this
   ticket's own scope correctly does not attempt to close.

## Files to Change

- `src/systems/social_systems/loyalty_drift.py` (new)
- `src/systems/social_systems/party_lifecycle.py` (extend `effective_defection_threshold`)
- `tests/unit/social/test_loyalty_drift.py` (new)
- `tests/unit/social/test_party_lifecycle.py` (extend)
- `tests/integration/culture/test_loyalty_drift_campaign.py` (new)
- `docs/world/culture_drift_contract.md`
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`
- `docs/parity_ledger/social_narrative.yaml`

## Explicit Scope Guards (what NOT to touch)

- No changes to `CultureDeriver`/`CulturalBiasApplicator`/`CultureDriftExporter` — read-only consumer.
- No changes to `GroupPhase.resolve()`'s live call — the disclosed gap stays disclosed, not papered over.
- No changes to `IdentityUpdate.faction_set`'s own semantics (idea 39's own shipped shape, `Faction.NEUTRAL`
  sentinel) — this ticket only modulates *when* defection triggers, not *what* it does on trigger.
- No changes to `home_region_id`/idea 59's own scope.

## Dependency Map

Step 1 → Step 2 (threshold extension needs the service to exist) → Steps 4/5 (tests need both) →
Steps 6/7 (docs/parity cite the real shipped shape) → Step 8 (optional, time-permitting).

## Acceptance Criteria Map

- AC1 (real, tested per-region signal, read-only) → Steps 1, 4, 6.
- AC2 (wired as real input to idea 39's trigger) → Step 2, 4 (test proving the threshold shifts).
- AC3 (integration test against `campaign_life_arc.yaml`) → Step 5.
- AC4 (determinism) → Step 4 (repeated-call guard test).

## Unresolved Questions

None — the two open design questions the ticket itself flagged (per-entity vs. per-region granularity;
`home_region_id` vs. current region) are both resolved with real evidence in investigation.md.
