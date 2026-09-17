---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION

## Trigger

Peer review, after the fifth real state error (`demographic_cohort_cycle`): `orphan` is empirically
the registry's least reliable state (2 of 5 known state errors were wrong `orphan` claims), it is
the only state that is fully mechanically decidable (zero callers, full stop — `done`/`partial` are
completeness judgments, `orphan` is not), and binding every `orphan` mechanism and running the
caller-count check directly tests claims-as-tests phase 2's own premise ("declaring `orphan` *is*
the assertion zero callers"). Requested as one batch, all eleven `orphan` mechanisms.

**Explicit limitation, stated up front per peer's own instruction**: this is a targeted pass at the
state most likely to be wrong. Its defect rate does not generalize to the other 58 mechanisms. An
unbiased estimate of overall registry accuracy needs a random sample — a separate exercise.

## The eleven, and their disposition

Five were already bound and confirmed correct in earlier tickets this epic (`resource_harvesting`,
`strategic_redirection`, `narrative_memory`, `group_coordination`, `quest_reward_distribution`) —
not re-investigated here.

Six were unbound; each was investigated directly (real caller search, flag-gating check), not
assumed from the atlas's own prior narrative:

| id | Verdict | Real evidence |
|---|---|---|
| `genetics_aptitude` | **WRONG** — corrected `orphan` → `gated` | `GeneticsSystem.generate_profile_from_seed()`/`combine_profiles()` called for real from `src/world/reproduction_humanoid.py`'s `HumanoidReproductionService` (real parent-pairing, not a comment/type-hint). Gated behind `ENABLE_REPRODUCTION_HUMANOID_PATH` (default OFF). See "A second correction" below — this also overturns the atlas's own Revision 10 claim that no individual reproduction exists at all. |
| `emotion` | **WRONG** — corrected `orphan` → `done` | `EmotionUpdateService.update_on_event()` called unconditionally (no flag) from `engine/pipeline_phases/hardening.py`'s `NearDeathHardeningPhase`, itself invoked via a plain `run_phase("near_death_hardening", ...)` with no flag argument. Foundation's own investigation.md had already flagged this exact risk ("possibly stale, TCK-20260824 wired a near_death call site") without resolving it. |
| `cross_episode_social_consequences` | **WRONG** — corrected `orphan` → `done` | `evaluate_social_consequence()` called unconditionally (no flag) from `domains/campaigns/orchestrator.py` at episode-entity-spawn time. |
| `declared_cognition_schema` | Confirmed `orphan` | `core/cognition.py`'s own `RiskModel`/`RecoveryState`/`RelationshipModel`/`MotivationModel`/`TemporalModel` — zero real constructor calls anywhere outside the file, matching the atlas's own careful investigation. Bound symbol-level to `RiskModel` specifically (not file-level) since `core/cognition.py` also defines `PerceptionModel`, which IS written — file-level binding here would repeat `demographic_cohort_cycle`'s own aggregation mistake. |
| `committed_intentions` | Confirmed `orphan` | `CommitmentModel`/`CommitmentEntry`/`AbandonedCommitmentEntry` (`core/cognition.py`) — zero real callers; the one hit (`domains/commitment/pressure.py`, a type-hint only) is itself already-confirmed-orphan code. Matches the wiring-map's own "no write path exists" citation. |
| `succession` | **Open, not resolved — flagged to peer** | See below. |

**Net for this batch: 3 of 6 newly-investigated orphans were wrong (50%), plus a 4th (`succession`)
under real, unresolved dispute. Combined with the two errors already known
(`causal_spatial_memory`, `demographic_cohort_cycle`), that is 5 of 11 orphan mechanisms found or
suspected wrong when actually checked — a real, substantial error rate for this one state,
consistent with peer's own hypothesis that `orphan` is the least reliable state in this registry.**

## A second correction found inside the first: the atlas's own Revision 10 claim

`genetics_aptitude`'s atlas card (`entity-profile#7`) states, as of its own "Revision 10": *"checked
directly whether individual reproduction exists at all... it doesn't. There is no parent-child
birth event anywhere in the live simulation."* This is also wrong: `src/world/
reproduction_humanoid.py` (added 2026-09-03, well before Foundation's own 2026-09-15 registry
seed) implements exactly that — `HumanoidReproductionService` pairs adult entities by social bonds
and constructs real offspring via `generator.spawn_humanoid_offspring()`, itself calling
`GeneticsSystem` directly. The path is real; it is gated OFF by default
(`ENABLE_REPRODUCTION_HUMANOID_PATH`), which is not the same claim as "doesn't exist" — a
distinction this project's own registry now treats as load-bearing (`gated` vs. `gap`). Corrected
in the atlas card directly (Revision 11 note appended, badge text corrected).

## Open, unresolved: `succession`

`succession` already carries a `verified` block (dated 2026-09-16, presumably peer's own prior
direct search) stating: *"heir_entity_id confirmed never populated by any write path (repo-wide
search) -- confirms the orphan claim."*

Direct re-check of `src/systems/lifecycle_systems/lifecycle.py::LifecycleSystem.resolve_lifecycle()`
found a real, unconditional fallback heir-selection algorithm:

```python
heir_id = entity.lifecycle.heir_entity_id
if heir_id is None:
    heir_id = LifecycleSystem._select_default_heir(state, entity)  # real social-bond-based algorithm
    if heir_id is not None:
        ...
        lifecycle=replace(life_upd2, heir_entity_id_set=heir_id)   # a real write
```

`_select_default_heir()` (added 2026-08-31, `src/systems/lifecycle_systems/lifecycle.py:121-134`)
scores every bonded, active entity by `0.6*familiarity + 0.4*sentiment` and returns the top
candidate — this IS a real write path, via the `heir_entity_id_set` field name (the "_set" suffix
being this codebase's own convention for a `StateUpdate` patch field, e.g. `death_reason_set`,
`is_permadeath_set` in the same function). `engine/patches.py:86` then applies
`heir_entity_id_set` onto the real `heir_entity_id` state field on entity apply.

**Hypothesis, not yet confirmed as the resolution**: a search for literal `heir_entity_id=`
assignment (matching the field's own bare name) would miss this "_set"-suffixed patch-field write
entirely — the same class of naming-convention trap this epic has found repeatedly elsewhere
(`progression_conversion`/`src/progression/` collision, `FairShareProtocol`'s docstring-only name).
This would mean BOTH the atlas's own investigation and peer's own dated verified block missed the
same real write path for the same structural reason.

**Not corrected in this pass.** This directly contradicts an existing, explicit, dated
peer-authored verified block — flagged to peer with full evidence for their own review/decision
rather than unilaterally overwritten, per this epic's own standing discipline for exactly this
situation (`motivation_doctrine`'s own orphan/gap question was resolved the same way).
