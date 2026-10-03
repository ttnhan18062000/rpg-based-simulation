---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING
artifact_type: investigation
tags: [social, simulation-quality]
---

# Investigation — TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING

## Context-Scan Note

Step 0c required calling `mcp__knowledge-search__search_docs` and the `python3
tools/knowledge_search.py` fallback before any grep/file read. Both were invoked first and both
returned `{"error": "index not found", "action": "run make knowledge-index"}` /
`knowledge index not found — run make knowledge-index` — the same failure the orchestrator hit
pre-dispatch. This is a real environment gap (the knowledge index has not been built in this
worktree), not a skipped step. `graphify query "cooperation offer retry cooldown expired offer"`
was also run and returned 171 traversed nodes (truncated at ~2000 tokens); all code files read
below were selected from that node list plus the orchestrator's own pre-surfaced precedent
(`CooldownEntry`/`TemporalPressureService`).

## Current Behavior

**The reported bug, confirmed by direct read of the entire `src/domains/cooperation/` package:**

- `CooperationDecisionService.select()` (`src/domains/cooperation/services.py:26-133`) scores SOLO
  vs. cooperation every tick from scratch. It reads `help_needs`, `candidates`, `fit_reports`, and
  `entity`/`state` — **nothing in this function reads any existing/prior offer state**. There is no
  check anywhere for "did I just have an offer to this partner (or any partner) rejected/expired."
- `CooperationIntentBridge.map_decision()` (`services.py:136-196`), when posture is
  `REQUEST_HELP`/`HIRE_SUPPORT` with a `partner_id`, unconditionally calls
  `ContractService.create_recruitment_contract()` (`src/systems/social_systems/contracts.py:110-133`)
  with `expiry_tick=tick+10`, and merges it into `StrategicUpdate.contracts_add_or_update`. No
  existing-offer lookup against `entity.strategic.contracts` occurs first.
- `SocialContractSystem.reap_expired_offers()` (`contracts.py:304-331`) removes any `OFFERED`
  contract whose `expiry_tick <= current_tick` via `contracts_remove` — a **full removal**, not a
  status transition to a terminal "rejected" record. Once reaped, `entity.strategic.contracts` has
  zero trace that this (entity, partner) pair was just rejected.
- Net effect (confirmed by the filing ticket's own event-trace evidence, re-cited below): the same
  entity re-proposes and re-fails every single tick with zero gaps — entity 13: ticks 50–72 (23
  consecutive), entity 8: ticks 54–73 (20 consecutive), in `highland_traverse_seed42_200t`.
- Pipeline order (`src/engine/pipeline.py:189`, `:367-368`; `docs/engine/authoritative_pipeline.md`
  phases 7–8, 37): `cooperation` (phase 7) runs before `active_contracts`/`expired_offers` (phase 8
  region) in the **same** authoritative-pipeline pass, but all phases in one tick read the **same**
  pre-tick `state` snapshot (kernel.md's Collection→Resolution ordering) — so within one tick the
  cooperation phase cannot see contracts reaped later that same tick; it only ever sees the
  post-prior-tick state. This confirms the loop is purely tick-to-tick, not an artifact of
  intra-tick phase ordering.

**Precedent search — is there an existing cooldown/backoff mechanism to reuse?**

Two typed cooldown-shaped structures exist in the codebase; only one is actually wired end-to-end:

1. `CooldownEntry` (`src/core/cognition.py:153`, frozen dataclass `target_id: str, ready_tick: int`)
   held in `TemporalModel.cooldowns: Mapping[str, CooldownEntry]`
   (`entity.cognition.subjective.time.cooldowns`). Consumed by
   `TemporalPressureService.calculate_urgencies()` (`src/domains/time/service.py:14-46`), which
   returns `urgency=0.0` while `current_tick < cd.ready_tick`. **Confirmed dead/orphaned as a
   decision input**: `calculate_urgencies()` has exactly one production caller —
   `MemoryUpdatePhase.run()` (`src/domains/memory/phase.py:75`) — which writes the result into
   `entity.cognition.subjective.time.urgency`. Grepping the entire `src/` tree for any read of
   `subjective.time.urgency` returns **zero matches**. Grepping for any production writer of
   `TemporalModel.cooldowns`/`CooldownEntry(...)` also returns **zero matches** — the only place
   `CooldownEntry` is ever constructed is the unit test
   `tests/unit/domains/time/test_phase13_temporal_pressure_service.py::test_active_cooldown_prevents_immediate_retry`.
   So this entire `cooldowns → urgency` pipeline is fully wired end-to-end mechanically but has
   **no production producer and no production consumer** — it is scaffolding for a Phase 13
   feature that was never connected to any decision logic. Building on it here would mean adding
   the cooperation domain as this pipeline's first-ever real producer *and* still needing a brand
   new consumer, since nothing reads `time.urgency` today. Not recommended (see Recommendation
   below).
2. `IdentityComponent.cooldowns: Dict[str, int]` (`src/core/state.py:486`, `# skill_id -> tick when
   ready`) is a **live, fully-wired mechanism** for skill cooldowns: set via
   `IdentityUpdate.cooldown_updates: Dict[str, int]` (`src/core/updates.py:237`), merged
   authoritatively in `apply.py`/`patches.py` (`src/engine/apply.py:527`,
   `src/engine/patches.py:188,227`), serialized in `state.py:829`, and **read as a real legality
   gate** in three separate call sites: `src/engine/legality.py:349`
   (`SocialContractSystem`-adjacent `verify_skill_legality`: `actor.identity.cooldowns.get(skill_id,
   0) > 0`), `src/engine/tactical.py:686`, and `src/engine/domain/skill_actions.py:48`. This is a
   proven, minimal-risk pattern: a plain `Dict[str, int]` of `key -> tick_when_ready`, checked with
   a simple `current_tick < ready_tick` comparison, already exercised by
   `tests/unit/progression/test_rpg_advancement.py`,
   `tests/integration/pipeline/test_combat_legality_matrix.py`, and
   `tests/unit/observability/test_event_extractor_identity.py`.

**Note on `IdentityComponent.to_canonical_dict()`** (`src/core/state.py:494-511`): `cooldowns` is
**not** included in the canonical dict used for state hashing — this is a pre-existing gap that
already applies to skill cooldowns today, not something this ticket introduces. Reusing the same
field inherits the same pre-existing gap (see Risks below) rather than creating a new one.

## Recommendation — Concrete Mechanism

**Reuse `IdentityComponent.cooldowns` (option 2 above), not `TemporalModel.cooldowns`.** The
Temporal pipeline is orphaned scaffolding with no live consumer; adopting it here would require
building both a producer and a consumer from scratch, with zero test/observability precedent for
either. `identity.cooldowns` is a proven, live pattern already used for exactly this
shape of problem (a durable "not before tick N" gate on a proposal-like action).

**Scope: per-entity blanket cooldown, not per-(entity, partner) pair.** The ticket's own Scope
text explicitly allows this ("does not immediately re-propose a cooperation offer to the same
**(or any)** target"), and it is the lower-risk choice: a per-partner-pair map would grow
unboundedly over a long run (every distinct partner ever proposed-to leaves a permanent dict
entry, and nothing currently evicts old skill-cooldown-style entries either), while a single fixed
key directly breaks the reported every-tick retry loop regardless of whether the entity is cycling
through one partner or several in the small local candidate pool
(`PartnerCandidateProvider.get_candidates`, capped at `max_candidates=5`,
`spatial_radius=15.0`).

**Concrete plan:**

1. **Key**: `"cooperation_offer_retry"` — a fixed, namespaced string key added to the *same*
   `entity.identity.cooldowns: Dict[str, int]` map used for skill cooldowns. It never collides
   with a real `skill_id` (checked against `SKILL_REGISTRY` — skill ids are snake_case skill
   names, not this literal string). Reusing the identical field/plumbing rather than adding a new
   `EntityState` field is the minimal-diff choice: no new dataclass field, no new
   canonicalization/patch/apply-path code, no new serialization path — all of that machinery
   already exists and is tested for this exact `Dict[str, int]` shape.
2. **Set point**: `SocialContractSystem.reap_expired_offers()`
   (`src/systems/social_systems/contracts.py:304-331`) — the sole authoritative point where an
   `OFFERED` contract is reaped post-expiry. When an entity's reaped contract has
   `kind == ContractKind.RECRUITMENT` (i.e., it's a cooperation offer, not a `LOAN` or other
   contract kind — scoping the write to `RECRUITMENT` only keeps this change confined to
   cooperation, per the ticket's Out of Scope), also merge
   `IdentityUpdate(cooldown_updates={"cooperation_offer_retry": current_tick + COOPERATION_OFFER_COOLDOWN_TICKS})`
   into that entity's `EntityUpdate.identity`, alongside the existing `strategic.contracts_remove`
   write, in the same authoritative `StateUpdate`. Recommend
   `COOPERATION_OFFER_COOLDOWN_TICKS = 15` as a module-level constant in `contracts.py` (offer
   duration is already 10 ticks — a 15-tick post-expiry cooldown puts the next allowed proposal
   roughly 25 ticks after the failed attempt's creation, comfortably breaking a 20-23-consecutive-tick
   streak while remaining short relative to 200-500t scenario lengths, so legitimate
   later-tick cooperation is not permanently suppressed).
3. **Check point**: `CooperationDecisionService.select()` (`src/domains/cooperation/services.py:26-133`).
   This keeps the check inside pure decision logic that already reads `entity`/`state` and returns
   a `CooperationDecisionResult` — it does not itself mutate durable state (Core Boundaries rule).
   Add, near the top (after the `if not help_needs` early return):
   `on_offer_cooldown = state.tick < entity.identity.cooldowns.get("cooperation_offer_retry", 0)`.
   Then gate the "Good partner exists" branch (currently `if best_report:` at line 90) with
   `if best_report and not on_offer_cooldown:` so that, while on cooldown, execution falls through
   to the **existing** `solo_score >= 0.5` / `DEFER_NO_PARTNER` branches unchanged (lines 114-133) —
   i.e., the exact same fallback path already used today when no suitable partner exists. This
   means `CooperationIntentBridge.map_decision()` never receives a `REQUEST_HELP`/`HIRE_SUPPORT`
   decision while on cooldown, so no new contract is created, with **zero changes required** in
   `services.py`'s intent-bridge or `phase.py`.
4. **Why not gate in `CooperationIntentBridge.map_decision()` instead**: the same fix could be
   applied there (skip contract creation when on cooldown), but that would leave
   `CooperationDecisionResult.selected_posture` reporting `REQUEST_HELP`/`HIRE_SUPPORT` to the
   emitted `CooperationDecisionSelectedEvent`/`PartnerSelectedEvent` timeline events
   (`phase.py:96-113`) even though no contract was actually created — a misleading trace. Gating
   in `select()` keeps the reported posture and the actual contract-creation behavior consistent.

## Mechanics / Engine Constraints

- `docs/engine/authoritative_pipeline.md` phase 7 (`cooperation`) and phase 8 region
  (`contracts`/`active_contracts` at line 57) govern where this logic legally runs — both proposal
  (phase 7) and reap/expiry (phase 8/37) already exist as named authoritative phases; this ticket
  adds a durable side-effect to the existing `expired_offers` phase rather than introducing a new
  phase, so no phase-sequence change is needed.
- `docs/engine/architecture_reference.md:82-90` ("Social cooperation must be explicit, not
  inferred from proximity" / "if cooperation matters beyond the current moment, represent it as a
  contract or party record") directly supports representing the retry-throttle as durable typed
  state (`identity.cooldowns`) rather than as an ephemeral local variable or `reason` string — this
  satisfies the Durable State Rule in `CLAUDE.md`.
- Core Boundaries rule (`CLAUDE.md`): decision logic (`CooperationDecisionService.select()`) must
  read state, not mutate it; the durable cooldown write must go through the authoritative
  `EntityUpdate.identity` path (`IdentityUpdate.cooldown_updates`) applied by `apply.py`, exactly
  as skill cooldowns already do. The recommended design in this doc satisfies this directly.
- No `docs/mechanics/04_strategic_cognition.md` law currently documents a cooperation-offer retry
  cooldown at all (confirmed by grep across the whole file — the only "retry" pattern documented
  there is the unrelated Committed-Intentions "Retry-on-loss" behavior at lines 244-249, which is
  deliberately retry-forever with no cooldown, a different mechanic). This is a **new** mechanic
  being introduced, not a divergence from an existing documented law.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: add a subsection (e.g. under a new "Cooperation
  Offer Retry Cooldown" heading, sibling to "Committed Intentions") documenting the new
  `cooperation_offer_retry` cooldown mechanic — key, set point (`reap_expired_offers`), check
  point (`CooperationDecisionService.select()`), and the `COOPERATION_OFFER_COOLDOWN_TICKS`
  constant value, once implemented with its final chosen value.
- `docs/engine/authoritative_pipeline.md`: phase 8's `contracts`/`expired_offers` row (line 28,
  "Expires stale social and legal contracts before system consumption") should note that expiry of
  a `RECRUITMENT` offer now also sets a retry cooldown on the proposing entity, since this is now
  part of what that phase authoritatively does.
- `docs/parity_ledger/social_narrative.yaml`: add a new entry (next available `SOC-2xx` id)
  documenting the new cooperation-offer-retry-cooldown behavior, `status: verified`, `priority:
  P2`, pointing at `CooperationDecisionService.select()` and
  `SocialContractSystem.reap_expired_offers()` as `v2_evidence`, and the new regression test (see
  test_plan.md) as `test_path`. This is additive (a new mechanic, not a change to SOC-233/234/240,
  which describe event *emission* correctness and are unaffected — `contract_expired_offer` still
  fires exactly the same way when an offer expires; only the *rate* at which new offers get
  created changes).

The following docs were considered and are **not** required to change: `docs/parity_ledger/social_narrative.yaml`'s
existing entries `SOC-233` (`cooperation_event` emission), `SOC-234` (contract event
fixes including `contract_expired_offer`), and `SOC-240` (SocialShaper's 10 SOCIAL event types) —
all three describe how `contract_expired_offer`/`cooperation_event` are *derived from state
diffs*, which this ticket does not change; it only changes how often an `OFFERED` contract gets
created in the first place. `docs/testing/regression_policy.md` (listed in the ticket's own
`## Related Docs`) does not need further edits from this ticket specifically — the filing ticket
(`TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE`) already scoped a `doc-updater` follow-up
there for the broader re-baseline worked example; this ticket's own grade-anchor update (see Prior
Work) is a data-only fixture change, not a policy-document change.

## Parity Ledger Overlap

- `SOC-233` (`status: verified`, `priority: P1`) — `cooperation_event` emission. Overlaps by
  subject matter (cooperation domain) but not by mechanism; not touched by this fix.
- `SOC-234` (`status: verified`, `priority: P1`) — `contract_expired_offer`/`contract_lapsed`/
  `contract_completed` event-type correctness. Overlaps by subject matter; not touched — this
  ticket does not change when/how `contract_expired_offer` fires, only how often a new offer gets
  created after one fires.
- `SOC-240` (`status: verified`, `priority: P1`) — apply-layer `SocialShaper`'s 10 SOCIAL event
  types including `contract_expired_offer`, and the double-fire fix
  (`ContractLifecycleSystem.check_expirations()` + `reap_expired_offers()` same-tick interaction).
  Directly relevant context: confirms `reap_expired_offers()` is the authoritative removal path
  this ticket's cooldown-set logic should hook into, and confirms it already coexists safely with
  a status-transition-based expiry path in the same tick. No P0 entries found for cooperation/
  contract offer subsystem — no `test_path` gating required before this ticket can proceed.
- No entry currently exists for a cooperation-offer retry cooldown; a new entry should be added
  (see Docs Requiring Update).

## Prior Work

- `stored_artifacts/TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE/investigation.md` — the
  filing ticket. Confirmed via real event-trace evidence (`highland_traverse_seed42_200t`, entity
  13 ticks 50-72, entity 8 ticks 54-73) and a full code read of `src/domains/cooperation/*` that
  there is no cooldown/backoff/pending-offer tracking anywhere in the package. Deliberately left
  `highland_traverse_seed42_200t`'s SOCIAL anchor un-rebaselined pending this ticket. Confirms only
  1 of 3 candidate run_keys with the same `loop_flags` diagnostic (`urban_political_seed42_200t`,
  `highland_traverse_seed42_200t`, `lifecycle_full_coverage_world_seed42_200t`) is an actual test
  failure — the other two stay within the 20% score-tolerance band and are explicitly **not**
  touched by any anchor update.
- `stored_artifacts/TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION/investigation.md` —
  independently found the same missing-cooldown mechanism explains SOCIAL drift on
  `urban_political_selfmodel*_probe` run keys, and deliberately left those un-re-anchored pending
  this exact fix. Those run_keys are explicitly **out of scope** here (see ticket's Out of Scope
  and this ticket's own scope note above) — the filing ticket, not this one, owns re-litigating
  them, and its own investigation already disclosed they were left open.
- `TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY` (referenced in
  `src/core/strategic.py`'s `BlockerState.target_quantity` docstring, lines 240-244) — a close
  structural precedent for "prevent immediate re-bidding of a flat/repeating utility signal after
  a failed resolution attempt," though for `ResolveBlockerScorer` rather than cooperation offers.
  Not directly reusable code, but confirms the general pattern (add a bounded suppression window
  after a repeated-failure signal) is an established fix shape in this codebase.
- `identity.cooldowns` skill-cooldown machinery itself (`TCK` origin not identified in this pass —
  predates the tickets read here) is the direct code precedent being reused; see Recommendation.

## Risks and Open Questions

- **`COOPERATION_OFFER_COOLDOWN_TICKS` exact value is an implementer judgment call**, informed
  but not dictated by this investigation. 15 ticks is a reasoned starting point (offer duration 10
  + margin), but the *only* way to confirm it actually reduces `contract_expired_offer` density
  enough for `highland_traverse_seed42_200t` to pass its grade-anchor band/tolerance check is a
  real corpus trial re-run (`python3 tools/evaluate_simq.py`) after implementation — **do not
  assume the fix works or tune the anchor from a hypothesis**. If 15 ticks is insufficient (streak
  still exists, just shorter), the implementer should increase the constant and re-run, not adjust
  the anchor to mask a still-present rapid-retry pattern.
- **Reusing `identity.cooldowns` inherits its pre-existing canonical-hash gap**: the field is
  absent from `IdentityComponent.to_canonical_dict()` (`state.py:494-511`), so a
  `cooperation_offer_retry` cooldown entry (like all skill cooldowns today) will not affect
  determinism/replay state-hash comparisons. This is not a new gap introduced by this ticket — it
  already exists for skill cooldowns — but the implementer should not silently "fix" it as part of
  this ticket (that would be an unrelated architecture change, out of this ticket's scope); if it
  is judged worth fixing, it should be filed as a separate ticket.
- **Scoping the cooldown-set write to `ContractKind.RECRUITMENT` only, inside
  `reap_expired_offers()`, is a judgment call, not dictated by the ticket text.** `reap_expired_offers()`
  currently operates on all `OFFERED` contracts regardless of kind (it also reaps `LOAN` offers
  from `SocialAppraisalSystem`/other paths). Scoping to `RECRUITMENT` keeps this fix confined to
  cooperation per the ticket's Out of Scope ("Any other SOCIAL/cooperation scoring or weighting
  change" is out of scope) — but this should be flagged to the implementer explicitly rather than
  assumed, since it is easy to accidentally widen to all contract kinds.
- **Per-entity blanket vs. per-partner-pair remains a real design choice**, not a hard requirement.
  The filing investigation's own "Disclosed finding" note says "Recommend a follow-up ticket to
  add a minimum retry interval (**or** per-partner-pair backoff)" — both are explicitly sanctioned.
  This investigation recommends blanket for the stated reasons (simplicity, no unbounded growth,
  ticket AC's own "(or any) target" phrasing), but if the post-fix corpus trial shows the blanket
  cooldown suppresses too much legitimate `cooperation_active` density (net SOCIAL score moves the
  wrong direction, e.g. by blocking a different, viable partner for 15 ticks after one partner's
  offer failed), the implementer should consider per-`{entity_id}_{partner_id}` keys instead
  before assuming the blanket design failed outright.

## Anti-Drift Hazards

- **Do not touch `LOAN`-kind contract expiry cadence.** `reap_expired_offers()` is shared
  machinery across all `ContractKind` values; the cooldown-set logic must be conditioned on
  `contract.kind == ContractKind.RECRUITMENT`, not applied unconditionally to every reaped
  `OFFERED` contract.
- **Do not touch `contract_expired_offer` event emission logic** (`src/observability/event_extractor.py:1000-1035`,
  `src/observability/event_shapers.py:1400-1630`). Both are explicitly read-only observability
  derived from contract state diffs; this ticket's fix changes offer-creation *frequency*, not
  contract lifecycle *semantics* — the event should keep firing exactly as before whenever an
  offer does still expire.
- **Do not weaken or remove the existing `solo_score >= 0.5` / `DEFER_NO_PARTNER` fallback logic**
  in `CooperationDecisionService.select()` (lines 114-133) — the cooldown gate should fall through
  to this existing logic unchanged, not replace it with new bespoke cooldown-specific branching.
- **Do not re-baseline any run_key's SOCIAL anchor other than `highland_traverse_seed42_200t`.**
  In particular, `urban_political_selfmodel*_probe` entries are explicitly owned by
  `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` and deliberately deferred there;
  touching them here would be scope creep across tickets even though they're affected by the same
  root cause.
- **A real corpus trial re-run is mandatory before touching `grade_anchors.json`.** Do not compute
  or guess an updated SOCIAL score/grade for `highland_traverse_seed42_200t` from first principles
  — re-run `python3 tools/evaluate_simq.py` (or the scenario-specific calibration path used by the
  filing ticket) post-fix and read the fresh `data/calibration/*/quality_report.json` the same way
  the filing investigation did (not `quality_scores.jsonl`, which is append-only and was already
  found to double-count — see that investigation's own Anti-Drift Hazards).
- **Do not widen `PartnerCandidateProvider`/`PartnerFitEvaluator` scoring logic.** The ticket's Out
  of Scope explicitly excludes "any other SOCIAL/cooperation scoring or weighting change" — this
  fix must be additive (a new gate before offer creation), not a rebalancing of trust/fit/severity
  weights even if such a rebalancing might also reduce `offer_dead` density.
