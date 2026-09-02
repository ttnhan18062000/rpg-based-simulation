---
status: active
layer: mechanics
authority: P1
audience: agent
tags: [content, architecture]
---

# Core RPG Social/Relationship Axis Proposal

Date: 2026-09-02

Status: brainstorming proposal for review

Scope: the expected simulation after the proposed core-RPG roadmap and accepted design portfolio are
available, focused specifically on the trust/liking/grudge/reputation dimension every entity, Clan, and
faction relationship touches

Constraint: this document does not approve implementation, change an existing plan, create tickets, or
define a player-control system

## Purpose

The existing roadmap has been reconciled against two other axes this session: space (idea 66's Region/Place
rebuild, the spatial-index hardening pass) and time (the temporal-axis proposal, the calendar-authority
decision). A third cross-cutting dimension has the same shape as those two — every entity has it, dozens of
design ideas across M2, M4, M5, and M6 depend on it, and it has never been given the same "one document,
one clock" treatment. Unlike temporal, it is not aspirational: `SocialComponent`/`SocialBond` are real,
live, and load-bearing today. What's missing is not the mechanism, it's a single coherent account of it —
this session's own hardening-backlog investigation (item 1) already found reputation/relationships/social
consequence has **zero Mechanics Bible chapter**, unlike every other subsystem, and that the one existing
contract doc (`docs/simulation/social_systems_contract.md`) contained two factual errors, since corrected in
the same pass as this document (a false passive-decay claim, and a misdocumented reputation range).

## Executive proposal

Treat trust/liking/grudge/reputation as a third axis alongside space and time: one shared vocabulary
(`SocialComponent`'s 15 fields, `SocialBond`'s 5), owned and mutated only through
`RelationshipService.process_update()`, read by every higher-layer social system (Clan, Culture Drift,
Chronicle, race relations) rather than each reinventing its own trust concept. The real gap this document
names is not a missing mechanism — it's missing decay, missing scoping, an incomplete determinism hash, and
two independent "this relationship is bad" signals with no reconciliation rule.

## Design goals

- Name the real current model precisely enough that every social-adjacent idea (22, 33, 36/40, 53–63, 67,
  68, and whatever M6 eventually needs) can cite one shared vocabulary instead of assuming its own.
- Fix documentation that actively misleads (the decay and reputation-range errors already corrected) before
  building anything new on top of it.
- Resolve the determinism question explicitly rather than leaving it as an open assumption the way the
  temporal proposal initially left several numeric questions open.
- Name every real conflict found, the way the temporal proposal's own §9 did, not just the ones already
  known going in.

## Non-goals

- This document does not build a decay rule, a reputation-locality system, or a modifier-stacking engine —
  it names the gaps idea 67 (Living Relationship Decay), idea 60 (Reputations Are Local), and a future
  stacking-rule ticket would need to fill.
- It does not re-litigate idea 37 (Race Relations) or idea 68 (Inter-Clan Relations) — those are confirmed
  parallel, separate systems (`source`/`target`/`relationship_model`/`axes`), not readers or writers of
  `SocialComponent`, and are out of scope here.
- It does not propose new SimQ pillars or scoring rules.

## 1. The real model, verified directly

### 1.1 `SocialComponent` — 15 fields, not the 13 a prior summary cited

`src/core/models/social.py`: `trust_history: Dict[int,float]` (−1.0 to 1.0), `familiarity_history: Dict[int,float]`
(0.0 to 1.0), `debt_history: Dict[int,float]` (−1.0 to 1.0), `fear_history: Dict[int,float]` (0.0 to 1.0),
`grudge_history: Dict[int,float]` (0.0 to 5.0), `combat_loss_counts: Dict[int,int]`,
`salience_history: Dict[int,float]` (0.0 to 1.0), `bonds: Dict[int,SocialBond]`, `nemesis_ids: Set[int]`,
`place_attachment: Dict[str,float]`, `betrayal_count: int`, `betrayal_records: List[BetrayalRecord]`,
`public_reputation: float` (**0.0 to 2.0** — confirmed directly against `relationships.py:94`'s real clamp,
correcting the contract doc's prior 0.0–1.0 claim), `heroism_score: float`, `notoriety_score: float`.

### 1.2 `SocialBond` — the real directed relationship record

5 fields: `target_id`, `familiarity`, `sentiment` (−1.0 to 1.0), `last_interaction_tick: int`,
`role: RelationshipRole` (`NEUTRAL` / `FRIEND` / `RIVAL`, SOC-247). `last_interaction_tick` already exists
as exactly the anchor a future decay rule needs — it is not something idea 67 would need to add.

### 1.3 The single authoritative write path

`RelationshipService.process_update()` (`src/systems/social_systems/relationships.py:16-100`) is the only
place these fields are mutated. This matches the shared-calculation/domain-owned-state shape the temporal
proposal argued for (§7.1 of that document) — one write path, many readers — already true here without
anyone having named it as a deliberate architecture choice.

## 2. Real, currently-live consumers (read vs. write, verified directly)

- **`SocialAppraisalSystem`** (read): trust pipeline — `public_reputation/2.0` baseline → `SocialBond.sentiment`
  override `(sentiment+1)/2` → blended fallback `public_trust×0.7 + history_trust×0.3` → hard-reject gates
  (`trust<0.2` = TOTAL_DISTRUST, `betrayal_count>0 AND trust<0.4` = BETRAYAL_HISTORY). Governs contract kinds
  RECRUITMENT, LOAN, POSITION_SWAP, MERCHANT, TEAM_UP, PAID_INFORMATION, TEACH.
- **`PartyCompositionScorer`** (read): `0.6×role_diversity + 0.4×OCEAN_compatibility`, plus (when an actor is
  supplied) `+0.15×mean(trust/bond)` and `+0.10×mean(RelationshipRole affinity: FRIEND=+1, RIVAL=−1)`.
- **`ReputationUpdateService.process_witnessed_event()`** (write): escort completed → `+0.1` + RELIABLE
  label; betrayal witnessed → `−0.2` + BETRAYER label; camp cleared → `+0.05` + COMBATANT label.
- **Contract breach** (write): `betrayal_count += 1`, triggers `ReputationUpdateService`.
- **`SocialMemoryService`** (write): `place_attachment += 0.001`/tick while present in a region; nemesis
  promotion at `grudge_history[id] >= 3.0`, confirmed directly against `check_nemesis_promotion()`.
- Higher layers built on top, not independently re-verified this pass: `ClanState.tension_level` (confirmed
  earlier this session to have no external driver — see the culture-drift hardening item and idea 68),
  Culture Drift's `region_cultures`, `faction_relationships.yaml`/`race_relations.yaml` diplomacy — all
  parallel or downstream, not readers of `SocialComponent` itself.

## 3. Conflicts and required changes

Five findings, in the same spirit as the temporal proposal's own §9 — concrete, evidenced, not
re-statements of what was already known going in.

### 3.1 Determinism: `CanonicalStateHasher` covers 10 of 15 fields, not all or none

`EntityState.to_canonical_dict()` includes a real `"social"` sub-dict, but only 10 of 15
`SocialComponent` fields: `trust_history`, `familiarity_history`, `fear_history`, `grudge_history`,
`combat_loss_counts`, `bonds` (full), `betrayal_count`, `public_reputation`, `heroism_score`,
`notoriety_score`. **Missing**: `debt_history`, `salience_history`, `nemesis_ids`, `place_attachment`,
and `betrayal_records` (only the count is hashed, the detailed list is not). A divergence in any of these
5 fields between two runs of the same seed would go undetected by the canonical hash — a real determinism
gap, distinct from `StateFingerprinter`'s already-known, explicitly-non-canonical near-zero coverage.

Required direction: either add the 5 missing fields to `to_canonical_dict()`, or explicitly document why
each is intentionally excluded (e.g. `place_attachment` may be judged non-authoritative-enough to matter) —
silence is the only wrong answer here.

### 3.2 The "Decay" section was factually wrong, not just stale (corrected in this pass)

`docs/simulation/social_systems_contract.md` claimed passive decay exists with a configurable per-field
rate. Direct verification: zero decay logic anywhere in `src/systems/social_systems/`, no "social config"
file anywhere in the repo. The only real decay mechanism, `SocialMemoryDecay.apply_decay()`
(`src/domains/campaigns/social_memory.py:355-390`, real tuned constants `FRIENDSHIP_DECAY=0.40`/episode,
`GRUDGE_DECAY=0.10`/episode), operates on a separate structure (`SocialMemoryRecord`, Campaign cross-episode
memory) and only fires at episode boundaries — the same specialized, rarely-exercised path this session's
Culture Drift hardening item found for `CultureDeriver`. It does not affect live `SocialComponent` state.
This directly confirms idea 67's premise and independently confirms M5's idea 53 scope note. **Already
corrected in `social_systems_contract.md` in the same session pass as this document** — recorded here for
the axis-level record, not as a still-open item.

### 3.3 `public_reputation`'s documented range was wrong (corrected in this pass)

The contract doc stated 0.0–1.0; the real clamp is 0.0–2.0 (`relationships.py:94`), matching the field's own
comment in `social.py`. The doc's Reputation section and its own Relationships section (which correctly
listed the real clamp table) contradicted each other. Already corrected in the same pass as this document.

### 3.4 Two independent "this relationship is bad" signals, no reconciliation rule

`RelationshipRole.RIVAL` (settable only via `SocialBondUpdate.role_set`) and `nemesis_ids` (grudge-promoted
at `>=3.0`) are explicitly independent per the contract doc's own text. An entity can be a `RIVAL` by role
without being a nemesis, or a nemesis without a `RIVAL` role, with no stated rule for which one a given
consumer should prefer when both exist — `PartyCompositionScorer` reads role affinity, `SocialMemoryService`'s
routing-avoidance reads nemesis, and nothing reconciles the two. Not a confirmed bug — no consumer was found
reading both and producing a contradictory result — but a real unreconciled seam a coherent axis design
should name rather than leave implicit.

### 3.5 `public_reputation` has no location/observer scoping (idea 60's own finding, reconfirmed)

A single global float, read identically everywhere it's consumed — `ReputationUpdateService` takes no
location or observer parameter anywhere. Idea 60 (Reputations Are Local) already names this; reconfirmed
directly in this pass, not assumed from the idea's own card text.

## 4. Per-idea integration

| Idea | Relationship to `SocialComponent` |
|---|---|
| 22 (Relationship Roles) | Direct — `RelationshipRole` already shipped as a derived reasoning layer on `SocialBond`'s existing enum |
| 33 (Marriage) | Read — `eligibility_gate` on `SocialBond.sentiment`/`familiarity`; not independently re-verified in code this pass |
| 36/40 (Clan) | Adjacent, not core — `ClanState.tension_level` has no driver reading `SocialComponent` directly |
| 37 (Race Relations) | Parallel system, same `source`/`target`/`relationship_model`/`axes` shape, does **not** read/write `SocialComponent` — a race-level layer, not this axis |
| 53 (Inherited Reputation) | Write — birth-seed of `public_reputation`; M5's own scope note already correctly assumes no decay interferes |
| 54 (Guilt by Association) | Would read `SocialComponent` reputation via a not-yet-built Clan-scoped path |
| 55 (Inherited Feuds) | Extends `nemesis_ids`/grudge — today strictly same-individual, doesn't survive death |
| 56 (Drifting Loyalty) | Reads Culture Drift's `region_cultures`, not `SocialComponent` directly — a different layer |
| 57/62 (Legacy/Misremembering) | Chronicle-adjacent, not `SocialComponent` |
| 58 (Dying Wish) | New field, not yet on `SocialComponent` |
| 60 (Reputations Are Local) | Direct conflict with §3.5 above |
| 63 (Belief Grows) | Chronicle/Clan composite, not `SocialComponent` directly |
| 67 (Living Relationship Decay) | Direct — the missing within-episode decay identified in §3.2 |
| 68 (Inter-Clan Relations) | Adjacent, reuses idea 37's pattern, not `SocialComponent` |

No two ideas were found competing to own the same field's semantics — the closest is §3.4's
`RelationshipRole`/`nemesis_ids` seam, a real-code gap rather than a roadmap-idea conflict.

## 5. A contract shape for future social features

Mirroring the temporal proposal's own §10, a coherent social contract should require every social-adjacent
feature to declare:

1. Which field(s) it reads/writes and their real clamp range (§1.1/§1.2 above as the canonical table).
2. Whether it's subject to decay, and at what trigger — per-tick live vs. episode-boundary are **not**
   interchangeable today (§3.2); a feature must say which regime it assumes.
3. Scope/locality — global vs. observer/location-scoped (§3.5); most fields today are global by default,
   and a feature that needs locality must say so explicitly rather than assuming it.
4. Composition rule when multiple sources touch the same field — no stacking-group concept exists today,
   unlike temporal's modifier catalog (§7.2 of that document); a feature introducing a second writer to an
   existing field should state the composition order.
5. Canonical-hash coverage — a new durable field must be added to `EntityState.to_canonical_dict()`
   explicitly as part of the same ticket, not assumed covered by analogy to existing fields (§3.1 shows 5
   real fields already aren't).

## 6. Status: existing, planned, and new

- **Existing and live**: the full read/write map in §2; `RelationshipService.process_update()` as the sole
  write path; `SocialBond.last_interaction_tick` as a real, reusable decay anchor.
- **Existing but now corrected**: `social_systems_contract.md`'s decay and reputation-range claims (§3.2,
  §3.3) — fixed in this session, not left as open document debt.
- **Existing but incomplete**: `CanonicalStateHasher`'s 10-of-15-field coverage (§3.1) — a real, unresolved
  gap, not yet fixed pending a decision on which of the 5 missing fields should count.
- **Planned, not built**: idea 67's decay rule, idea 60's locality scoping, idea 54's Clan-scoped reputation
  read, idea 58's dying-wish field.
- **Genuinely new, not previously named anywhere**: the `RelationshipRole`/`nemesis_ids` reconciliation
  question (§3.4).

## Decisions accepted in this brainstorm

- `SocialComponent`/`SocialBond`/`RelationshipService` is confirmed as the shared vocabulary and single
  write path every social-adjacent idea should cite, the same role the temporal proposal's shared
  calendar/duration calculation plays for time.
- The two documentation errors (§3.2, §3.3) are corrected as part of this pass, not deferred.
- Idea 37 and idea 68 are confirmed structurally parallel to this axis, not part of it — no merge or
  reconciliation between the two systems is proposed.

## Decisions still requiring review

- Whether all 5 missing canonical-hash fields (§3.1) should be added, or whether some are legitimately
  non-authoritative enough to exclude — a real determinism-vs-cost tradeoff this document does not resolve.
  **Promoted to `TCK-20260902-SOCIAL-CANONICAL-HASH-GAP` (2026-09-02).**
- Which of `RelationshipRole` or `nemesis_ids` should take precedence when a consumer needs one answer and
  both are set (§3.4) — or whether the two should be unified into one signal instead.
- Whether `public_reputation` locality (idea 60) should be a full per-observer ledger or a coarser
  per-region approximation — not scoped by this document, an idea-60-ticket-time decision.
- Exact decay rate(s) for idea 67 — the Campaign-mode constants (`FRIENDSHIP_DECAY=0.40`/episode,
  `GRUDGE_DECAY=0.10`/episode) are a real calibration anchor, not a settled live-gameplay rate; a live-tick
  decay rate needs its own balance pass, the same caution the temporal proposal gave its own new numeric
  territory (e.g. `birth_cooldown_ticks`).

## References

- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` — the structural template this
  document follows
- `docs/simulation/social_systems_contract.md` — corrected in this session pass (§3.2, §3.3)
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md` — the narrower
  "write the missing Bible chapter" plan this document's findings feed into
- `docs/brainstorm/rpg_feature_atlas.html` — ideas 22, 33, 36, 37, 40, 53–63, 67, 68
- `docs/brainstorm/rpg_expected_schemas.html#schema-67` — idea 67's schema section
- `src/core/models/social.py`, `src/systems/social_systems/relationships.py`,
  `src/systems/social_systems/memory.py`, `src/domains/campaigns/social_memory.py`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Hardening backlog section
