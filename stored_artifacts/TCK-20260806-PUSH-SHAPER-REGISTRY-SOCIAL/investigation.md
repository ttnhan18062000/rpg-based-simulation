---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL

## Current Behavior — field-mapping confirmation, including the epic's one open question

Confirmed all 10 events' exact source, per `event_extractor.py:565-722`:

| Event | Source field |
|---|---|
| `group_joined`/`group_expelled` | `EntityUpdate.group_id_set: Optional[int]` — resolves the epic's one genuinely-unconfirmed field. Traced the actual materialization code (`src/engine/patches.py:210-211`: `gid = None if self.group_id_set == -1 else self.group_id_set`) and finds a real `-1` sentinel convention: `None` = not touched this tick, `-1` = left the group, any other int = joined that group ID. |
| `reputation_delta` | `SocialUpdate.reputation_set: Optional[float]` — absolute new value |
| `social_memory_created` | `SocialUpdate.trust_delta: Dict[int, float]` — genuine per-other-entity delta, reconstructed against `prior_ent.social.trust_history` |
| `contract_offer_created`/`_accepted`/`contract_completed`/`contract_lapsed`/`contract_expired_offer` | `StrategicUpdate.contracts_add_or_update: list[ContractState]` — each entry's `.status` is the new value |
| `contract_expired_offer` (reap path) | `StrategicUpdate.contracts_remove` against `prior_ent.strategic.contracts` for an `OFFERED`-status match |
| `contract_milestone_completed` | purely time-based, needs the full current-contracts reconstruction pattern (see below) |

## Key finding 1: `contract_milestone_completed` needs the same reconstruction pattern as `belief_stale`

Same category of gap Children 2/3 already found: this event re-scans ALL of an entity's currently
ACTIVE contracts every visited tick (a purely time-based `elapsed = tick - created_tick` check),
not just contracts touched this tick. Solved with the identical technique: merge
`prior_ent.strategic.contracts` (full prior snapshot) with this tick's `contracts_add_or_update`/
`contracts_remove` deltas, then scan the merged set. This is now the 3rd confirmed instance of
this exact pattern (after `belief_stale`, `progression_plateau_detected`) — a genuinely recurring
architectural shape for "purely time-elapsed" events in this codebase, not a one-off.

## Key finding 2 (real bug, fixed): `contract_expired_offer` double-fires on same-tick reap-and-transition

Found via real, non-mocked kernel run (`urban_political_seed42_500t`,
`ENABLE_SOCIAL_COOPERATION=ON`): `ON` mode showed `event_shapers` delivering ~2x
`event_extractor`'s `contract_expired_offer` count (1991 vs 996) — investigated before assuming
either side was correct.

Root cause: traced the actual mutation code (`src/systems/social_systems/contracts.py`) and found
**two independent functions both produce a signal for the same expiring `OFFERED` contract in the
same tick**: `check_expirations()` (lines 64-76) transitions it to `EXPIRED` status via
`contracts_add_or_update`, and `reap_expired_offers()` (lines 316-343) separately adds its ID to
`contracts_remove`. The old extractor is naturally immune to this — it reads one materialized
dict, where a contract is either present-with-a-new-status or absent, never both. A shaper reading
the two raw update-record lists independently is not immune, and must reconcile them itself.

**Fix**: the status-transition loop now skips any contract ID that also appears in this tick's
`contracts_remove` — same-tick removal wins, deferring to the separate reap-path loop, which
already handles that case correctly. **Verified the fix directly**: re-ran the same comparison,
`contract_expired_offer` went from a ~2x mismatch (1991 vs 996) to 1019 vs 1022 — within normal
run-to-run noise (0.3%), and `contract_offer_created` matched exactly (1049/1049).

## Docs Requiring Update

- `docs/parity_ledger/social_narrative.yaml`: new entry for the shaper build.

## Parity Ledger Overlap

`social_narrative.yaml` — `SOC-239` already exists (cross-reference for `cooperation_event`,
implemented in `StrategyShaper`); this ticket adds a new, separate entry for `SocialShaper` itself.

## Prior Work

- `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY`/`-PROGRESSION`/`-WORLD-DYNAMICS` (Phase 2, DONE) —
  the `PHASE2_SHAPER_REGISTRY` mechanism and the reconstruction/any-update-gating patterns this
  ticket reuses and extends.

## Risks and Open Questions

None left open — this ticket closes the epic's one previously-unconfirmed field
(`group_id_set`'s `-1` sentinel).

## Anti-Drift Hazards

- `SocialShaper.reset_run_state()` must stay wired into `Kernel.__init__` — omitting it would leak
  `_emitted_social_memory`/`_emitted_contract_milestones` across separate runs within the same
  process.
- The `removed_this_tick` same-tick-reconciliation check must be preserved if this shaper's
  contract-lifecycle logic is ever refactored — it's not obviously necessary from reading the
  status-transition loop in isolation, only from tracing the actual mutation pipeline.
