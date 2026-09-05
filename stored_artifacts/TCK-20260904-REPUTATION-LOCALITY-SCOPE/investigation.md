---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-REPUTATION-LOCALITY-SCOPE
artifact_type: investigation
tags: [social, determinism]
---

# Investigation — TCK-20260904-REPUTATION-LOCALITY-SCOPE

## Context Scan Note

Both mandated Step-0 tools were run before any grep/file read, per Hard Rule:

- `mcp__knowledge-search__search_docs(query="Reputations Are Local public_reputation region scoping
  SocialComponent")` → returned 8 hits, none a direct pre-existing investigation of this exact ticket
  (expected — the ticket is new). Useful hits: `docs/guidelines/intentional_divergences.md#DEV-001`
  (faction-scoped discount gating divergence, TCK-20260619-E33D-REP-DISCOUNTS),
  `docs/simulation/domains/social_memory_contract.md` (Export/Import Hooks, SOC-CROSS-EP-002),
  `docs/engine/known_limitations.md` §1.4, `docs/simulation/social_systems_contract.md`'s Trust
  evaluation pipeline section. All confirmed and re-verified directly against source below.
- `graphify query "SocialComponent public_reputation RelationshipService locality"` → BFS depth=2,
  355 nodes (269 truncated by budget). Confirmed `SocialAppraisalSystem`, `SocialComponent`,
  `SocialBond`, `RelationshipService`'s neighborhood; used as a seed list, not relied on alone —
  every file below was independently read from source.

## Current Behavior

### `SocialComponent.public_reputation` — current shape

`src/core/models/social.py:51` — `public_reputation: float = 1.0` (comment: "Unified reputation
score (0.0 to 2.0)"). A single unscoped scalar, no region/observer parameter anywhere in its type or
any read/write call site. `place_attachment: Dict[str, float]` (line 47, `RegionID -> Attachment
Score`) sits two fields above it in the same dataclass and is the ticket's recommended shape
precedent.

### Write paths — one authoritative, one pre-existing bypass (new finding)

- **`RelationshipService.process_update()`** (`src/systems/social_systems/relationships.py:78-100`,
  specifically lines 92-95) is the one write path the ticket's AC names as sole-authoritative. It
  either directly overrides (`update.reputation_set`) or increments
  (`social.public_reputation + update.heroism_delta - update.notoriety_delta`, clamped `[0.0, 2.0]`)
  the flat scalar. `SocialUpdate` (`src/core/updates.py:286-323`) carries `reputation_set: Optional[float]`,
  `heroism_delta: float`, `notoriety_delta: float` — no region/observer field exists on it today.
  `SocialUpdate.merge()` (`updates.py:325-367`) merges `reputation_set` as "last writer wins"
  (line 357) and sums `heroism_delta`/`notoriety_delta` (lines 358-359) — this composition rule
  would need an equivalent for any new region-keyed delta, mirroring `place_attachment_delta`'s
  sum-by-key merge (`updates.py:339-341`).
- **`SocialMemoryImporter.apply()`** (`src/domains/campaigns/social_memory.py:489-528`, specifically
  line 518-526) — **confirmed to bypass `RelationshipService.process_update()` entirely**: it calls
  `dc_replace(entity.social, ..., public_reputation=new_reputation)` directly. This is a real,
  pre-existing second write path to `public_reputation` that already exists today, independent of
  this ticket. It runs at episode-start construction (`CampaignOrchestrator._build_initial_state()`),
  analogous in spirit to `V2EntityBuilder.social(public_reputation=...)` (`src/core/builder.py:512,533`,
  initial-construction seeding, not a live-tick mutation) — but unlike the builder, `SocialMemoryImporter`
  already imports `SocialUpdate` (`social_memory.py:4`) and could trivially route through
  `RelationshipService.process_update(entity.social, SocialUpdate(reputation_set=new_reputation))`
  instead of the direct `dc_replace`, at effectively zero behavior change (verified:
  `process_update()`'s other field reconstructions are no-ops on an empty `SocialUpdate` — they copy
  existing dict/list values unchanged). **This is a concrete, low-risk fix Plan should consider** if
  AC #1's "no second write path exists" guard is meant literally; if episode-boundary seeding is
  meant to be an accepted exception (like `V2EntityBuilder`), the guard test's exact scope must say so
  explicitly rather than leaving it ambiguous.

### Three known consumers — one has an untracked call-site gap (new finding)

1. **`SocialAppraisalSystem.appraise_contract()`** (`src/systems/social_systems/appraisal.py:30-37`)
   — `public_trust = source_entity.social.public_reputation / 2.0` (line 37), blended with
   `history_trust` at 0.7/0.3 (line 45) into `trust_score`, gating `TOTAL_DISTRUST`/`BETRAYAL_HISTORY`
   (lines 48-54) and feeding every `_appraise_*` kind handler. Reads `source_entity` (the contract
   initiator), not `entity` (the appraiser) — i.e. today's read is about the *subject's* reputation,
   not scoped to the *appraiser's* location. A locality-scoped read here would naturally be keyed by
   **where the appraiser currently is** (the observer's region), reading `source_entity`'s
   region-keyed reputation entry for that region — mirroring how `place_attachment` is keyed by the
   *owning* entity's region-of-presence, not an observer's.
2. **`apply_reputation_discount()`** (`src/systems/economy_systems/reputation_discount.py:8-27`) — a
   **pure function with zero `SocialComponent` access**; it only takes `public_reputation: float` as
   a parameter. The ticket's Scope names this file as one of "the three known live consumers ... to
   update", but the actual `entity.social.public_reputation` reads happen at its two real callers:
   `src/engine/shop.py:84` (`legal_total = apply_reputation_discount(legal_price * quantity,
   entity.social.public_reputation)`, enforcement layer) and `src/town/shop.py:38` (`total_cost =
   apply_reputation_discount(total_cost, entity.social.public_reputation)`, proposal layer) —
   **neither file is in this ticket's Related Code Areas.** Both callers already have a nearby
   building/position in scope (`building`/`shop.position`, `entity.position`) that could resolve a
   region id the same way `SocialMemoryService.tick_place_attachment()` does (`src/systems/social_systems/memory.py:22-29`,
   iterating `state.regions` bounds) — but whether that resolution is needed at all depends on the
   open design question below (does the discount consumer read a per-region value, or does it keep
   reading a retained global scalar unaffected by this ticket?). Flagged as a Risk/Open Question, not
   assumed.
3. **`campaigns/social_memory.py`** — `SocialMemoryExporter.export()` (lines 433-466, specifically
   455-457) snapshots `entity.social.public_reputation` into `SocialMemoryRecord.faction_reputation["default"]`;
   `SocialMemoryImporter.apply()` (lines 489-528, specifically 518-526) seeds it back from that same
   `"default"` key, decayed via `SocialMemoryDecay.apply_decay()` (lines 374-409,
   `FRIENDSHIP_DECAY=0.40`/`GRUDGE_DECAY=0.10` per episode). Both treat `public_reputation` as one
   flat float under a single `"default"` faction key — the ticket's own comment at
   `social_memory.py:293-294`/`426` already flags this as "Replaces the per-episode-only
   `public_reputation` float for cross-episode continuity... Per-faction breakdown deferred to a
   future E43 child ticket" — i.e. a *faction*-scoped extension was already anticipated here, not a
   *region*-scoped one. Consuming a new region-keyed shape means deciding what a single scalar
   `faction_reputation["default"]` should carry forward across episodes (an aggregate/average? the
   value at the entity's last-known region? the retained global scalar only?) — an open question, not
   resolved by existing code.

### Additional real consumers NOT named in ticket Scope (found during investigation)

Confirmed via `grep -rn "public_reputation" src/`:

- `src/api/presenters/state_presenter.py:99` — exposes the flat float directly in the read-model API
  response (`"public_reputation": entity.social.public_reputation`).
- `src/domains/campaigns/state.py:101,108` and `orchestrator.py:479,654` —
  `EntityCarryForward.reputation: float` (single score; the class docstring at line 108 already notes
  "E43 adds per-faction detail", again *faction*-scoped, not region-scoped) and its construction/read
  sites.
- `src/observability/event_extractor.py:927-928` and `event_shapers.py:1515` — diff `curr_rep`
  vs `prior_rep` (both read via `getattr(..., "public_reputation", None)`) between ticks to emit a
  `reputation_delta` observability event (parity entries reference `REPUTATION_DELTA_THRESHOLD=0.05`).
- `src/core/builder.py:512,533` — `V2EntityBuilder.social(public_reputation: Optional[float] = None, ...)`,
  the initial-construction path, structurally identical in kind to `place_attachment`'s own builder
  kwarg (line 509) — i.e. builder support for a second locality-scoped kwarg is a direct, existing
  precedent to extend, not a redesign.

None of these five are named in the ticket's Scope/Related Code Areas as needing updates — which is
consistent with (and only safe under) keeping `public_reputation` as a retained global scalar
alongside a new locality-scoped structure, rather than replacing/repurposing the scalar's meaning.
See "Central open design question" below.

### `PublicReputationProfile` / `ReputationUpdateService` — confirmed structurally distinct (corrected premise, per ticket's own AC #5)

`src/core/cognition.py:535` — `PublicReputationProfile` lives at
`entity.cognition.relationships.public_reputation` (nested under `RelationshipModel`/`CognitionModel`),
a per-label `Dict[str, float]` (`"reliable"`, `"betrayer"`, `"camp_clearer"`, `"heroic"`) — a
completely different Python attribute path and shape from `SocialComponent.public_reputation`
(`entity.social.public_reputation`, a single float). As of 2026-09-04 it has exactly one real call
site: `src/engine/quests.py:233-236` (`QuestResolutionSystem.enforce()`, wired by
TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING, DONE 2026-08-28), gated to `QuestKind.ESCORT`'s
`"successful_escort"` event kind only, mutating `RelationshipModel.public_reputation` via
`EntityUpdate.cognition_bundle_set` whole-bundle replace — a different write path entirely
(`src/core/updates.py:655`, not `RelationshipService.process_update()`). This ticket's own Scope
already correctly excludes this system; this investigation independently re-confirms the exclusion is
still correct on 2026-09-04, and that the one real call site does not change idea 60's scope (the M5
epic doc's stale "zero call sites anywhere" premise, as the ticket text already notes, is corrected
here as required by AC #5 — see `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`
lines 72-73 for the stale text this investigation supersedes).

## Mechanics / Engine Constraints

- **`docs/mechanics/03_economic_laws.md` §4.1 "Reputation Discount"** (lines 84-111): documents the
  exact formula `entity_rep = clamp(public_reputation, 0.0, 2.0) / 2.0; discount = entity_rep * 0.20`
  and states "`public_reputation` sourced from `SocialComponent.public_reputation`". Whatever value
  Plan routes into `apply_reputation_discount()` must stay within the documented `0.0–2.0` clamp
  semantics — the formula itself does not change, but its "sourced from" line becomes imprecise if the
  discount consumer moves to a region-resolved read.
- **Durable State Rule / Authoritative Application (CLAUDE.md Architecture Rule; `docs/core/state.md`
  immutability law)**: `SocialComponent` is a frozen, `slots=True` dataclass; all field changes must
  go through `dataclasses.replace()`, exactly as `RelationshipService.process_update()` already does
  for every existing field (including `place_attachment`, lines 70-72, 88). A new locality-scoped
  field must follow the identical functional-update pattern — no direct mutation, no bypass beyond
  the one pre-existing gap flagged above (`SocialMemoryImporter.apply()`).
- **Determinism (CLAUDE.md Hard Rule "Do not break determinism")**: both `CanonicalStateHasher`
  (`src/engine/checkpoint.py`) and `StateFingerprinter` (`src/replay/fingerprint.py`) must cover the
  new shape in the same ticket per AC #3 — see next section for the exact mechanics.
- **Composition rule (unresolved, flagged by the ticket's own source proposal)**:
  `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` §5.4 names "composition
  rule when multiple sources touch the same field" as a required declaration for any social feature
  that introduces a second writer to an existing field — directly applicable here since `heroism_delta`/
  `notoriety_delta` currently update the flat scalar unconditionally. Plan must state explicitly
  whether a region-scoped reputation-affecting event also updates the retained global scalar (keeping
  the discount/observability/campaign-carry-forward consumers correct without any code change) or
  only the region-keyed entry (in which case those consumers silently go stale unless separately
  migrated) — this is the single highest-leverage design decision left open. Not resolved by this
  investigation, per the Uncertainty Rule ("vague leads stay vague until evidence narrows them").

### `CanonicalStateHasher` / `StateFingerprinter` — exact current mechanics

- `EntityState.to_canonical_dict()` (`src/core/state.py:846-920`) builds a `"social"` sub-dict
  (lines 892-909) with one key per `SocialComponent` field; `"public_reputation": self.social.public_reputation`
  is line 905, a bare float next to `"place_attachment": dict(sorted(self.social.place_attachment.items()))`
  at line 902 — the exact precedent pattern (`dict(sorted(...))`) a new `Dict[str, float]` field
  should follow. `CanonicalStateHasher.to_canonical_data()` (`checkpoint.py:63-108`) calls this per
  entity (line 81, sorted by id) and JSON-serializes with `sort_keys=True` (lines 59-60) —
  deterministic today, and stays deterministic under the same pattern (dict keys are `str`, sorted).
  `CanonicalStateHasher.get_hash()`/`BudgetedCanonicalHasher`/`CanonicalHashScheduler` all delegate to
  this same `to_canonical_data()` — no separate change needed in `checkpoint.py` itself beyond
  `state.py`'s `to_canonical_dict()`.
- `StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py:32-125`) is a **separate**,
  lighter, non-canonical fingerprint (explicitly documented, lines 13-16, as not a full serializer).
  Line 69: `f"reputation={ent.social.public_reputation:.3f}:"` is one segment of a per-entity f-string
  (lines 56-71) joined into `entity_parts`, then MD5-hashed (line 116). This line only captures the
  flat scalar today — a locality-scoped change must also serialize the new field's contents
  deterministically into this string (the file's own `region_ident`/`scar_ident` builders, lines
  85-94, are the precedent: `"|".join(f"{k}:{v}" for k, v in sorted(...))`), or region-scoped
  reputation changes become invisible to replay-parity fingerprinting — exactly the "fraud this
  catches" failure mode the file's own docstring (lines 25-29) warns against.

## Docs Requiring Update

- `docs/mechanics/03_economic_laws.md`: §4.1's "sourced from `SocialComponent.public_reputation`"
  line (line 104) becomes imprecise once the discount consumer's actual read value is resolved
  through a locality-scoped path (exact wording depends on Plan's design decision above).
- `docs/parity_ledger/social_narrative.yaml`: SOC-005 (P0, "Public reputation is distinct from
  private narrative meaning", `v2_evidence` cites the plain-float `SocialComponent.public_reputation`
  shape) and SOC-134 (P0, `appraise_contract`'s `public_trust = source.social.public_reputation / 2.0`
  read, `v2_evidence` quotes the exact pre-change line) both need `v2_evidence`/status review; and
  SOC-CROSS-EP-002 (P1, SocialMemoryExporter/Importer public_reputation read/write) needs the same
  once `campaigns/social_memory.py` is updated.
- `docs/parity_ledger/town_resource.yaml`: TOWN-181 (P1, reputation discount) — its
  `divergence_note` already states "no per-faction reputation dict on SocialComponent" as a known gap;
  once a locality (region) dimension exists, this note needs to be revisited even if the specific
  faction-scoping gap it names remains separately true.
- `docs/simulation/social_systems_contract.md`: "Trust evaluation pipeline" step 1 (line 32,
  "`source_entity.social.public_reputation / 2.0` → 0.0–1.0 baseline") documents the exact
  pre-change `appraisal.py:37` read verbatim; must be updated to describe the region-resolved read.
- `docs/simulation/domains/social_memory_contract.md`: the "Export / Import Hooks" section (lines
  66-80) states, verbatim, "Pure read of `entity.social.trust_history` and
  `entity.social.public_reputation`" and "Seeds `entity.social.public_reputation` from
  `record.faction_reputation["default"]`" — both lines describe the exact pre-change behavior of the
  named consumer (`campaigns/social_memory.py`) and must be updated to match its new shape.
- `docs/brainstorm/rpg_feature_atlas.html`: idea 60's own card (search anchor `id="idea-60"`,
  the `"60. Reputations Are Local..."` entry) currently carries badge `"gap"`/text `"Aspirational —
  design only"`. Once implemented, the badge/desc must be updated to reflect built status, following
  this doc's own established pattern of appending a `<strong>...found during...</strong>` correction
  note rather than rewriting history.
- `docs/brainstorm/simulation_capabilities.html`: idea 60's mirrored non-dev card (section 14
  "Memory, Reputation & Legacy", "A Reputation That Depends on Where You're Standing"-equivalent
  entry, currently under the section-level `badge planned`) must be updated in the same turn as the
  atlas edit above, per this repo's own established atlas↔capabilities-page sync convention.

The following docs were considered and are **not** required to change as part of this ticket:

`docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` (path:
`docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md`) is a point-in-time design
analysis/decision-record — its §6 "Decisions still requiring review" bullet naming idea 60's locality
granularity as an open, ticket-time decision is itself the historical record of *why* this ticket
exists; resolving that decision belongs in this ticket and the parity ledger, not in a rewrite of the
proposal doc's own analysis after the fact. Its `status: active` frontmatter marks it as a currently
valid reference for the analysis it contains, not a live-state doc that must track current
implementation.

`docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` (path:
`docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`) is a roadmap sequencing document;
its existing text about idea 60 (lines 72-73) already correctly states the "zero call sites" finding
was independently re-checked and downgraded, framed as risk analysis, not an implementation-status
claim — it does not need editing for this ticket to land (per-child-ticket implementation status is
tracked via `Related Tickets`/the parity ledger/`tickets/done/`, not by rewriting the epic doc after
every child ships).

`docs/mechanics/04_strategic_cognition.md` (path: `docs/mechanics/04_strategic_cognition.md`) is not
required to change: it governs the unrelated `GroupState.escort_target_id`-driven route-scoring
mechanism and `PublicReputationProfile`/`ReputationUpdateService`, neither of which this ticket
touches (see "confirmed structurally distinct" above).

## Parity Ledger Overlap

- **SOC-005** (P0, `verified`) — "Public reputation is distinct from private narrative meaning."
  `test_path: tests_v2/parity/test_social_parity.py` — **this file does not exist** (confirmed via
  `find . -iname "test_social_parity.py"`, zero results). This is a pre-existing broken P0 parity
  entry, not caused by this ticket, but the Authoritative Mechanics Rule requires P0 entries to have a
  passing `test_path`, and this ticket directly changes the field this entry is about — its
  `test_path` must be corrected (pointed at a real, passing test) as part of this ticket's parity
  ledger update, not left broken.
- **SOC-134** (P0, `verified`) — `test_social_appraisal_with_narrative`, `appraise_contract`'s
  public-reputation-informs-trust behavior. `test_path: tests/unit/social/test_parity_soc_134.py` —
  confirmed exists and currently passes against the flat-scalar shape (uses
  `.social(public_reputation=2.0)`/`.social(public_reputation=0.0)` via the builder). Must keep
  passing per AC #4 ("without breaking any existing test") — only satisfiable if the builder's
  `public_reputation` kwarg continues to seed whatever value these tests' default-region reads resolve
  to (supports keeping the flat scalar as a retained default/global baseline, see open design
  question above).
- **SOC-CROSS-EP-002** (P1, `verified`) — SocialMemoryExporter/Importer round-trip.
  `test_path: pytest tests/unit/social/test_social_memory.py tests/integration/scenarios/test_social_memory.py`
  — confirmed exists (`tests/unit/social/test_social_memory.py` has extensive `public_reputation`
  coverage, lines 260-414). `divergence_note` already documents the single-"default"-key faction
  proxy; needs revisiting alongside the region dimension.
- **TOWN-181** (P1, `verified`) — reputation discount. `test_path:
  tests/integration/scenarios/test_macro_economy.py::test_reputation_discount_applies` — confirmed
  exists (asserts exact discount percentages at `public_reputation=1.6`/default `1.0`, lines
  196-212). Must keep passing per AC #4.
- No entry found anywhere in `docs/parity_ledger/` that already anticipates a *region*-scoped
  `public_reputation` (only *faction*-scoped anticipation exists, at SOC-CROSS-EP-002's docstring and
  `campaigns/state.py:108`'s "E43 adds per-faction detail" — a different, unbuilt axis this ticket
  does not build). A **new** parity entry is warranted for the locality mechanism itself once
  implemented; next available id in `social_narrative.yaml` is `SOC-266` (highest existing numeric id
  confirmed as `SOC-265` via `grep -o "id: SOC-[0-9]*" ... | sort -n | tail`).

## Prior Work

- `stored_artifacts/TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING/investigation.md` — sibling
  reputation-wiring ticket (DONE 2026-08-28). Confirms `PublicReputationProfile`/
  `ReputationUpdateService`'s one real call site (`src/engine/quests.py:233-236`) and the
  merge-safety hazard around `cognition_bundle_set` — independently re-verified above as still
  structurally unrelated to this ticket's `SocialComponent.public_reputation` scope.
- `stored_artifacts/TCK-20260902-SOCIAL-CANONICAL-HASH-GAP/investigation.md` and `test_plan.md`
  (DONE) — the sibling canonical-hash-coverage ticket that added `place_attachment` (among 6 other
  fields) to `EntityState.to_canonical_dict()`'s `"social"` sub-dict. Its test file,
  `tests/unit/core/test_entity_integrity.py` (specifically
  `test_social_seven_newly_covered_fields_participate_in_canonical_hash`, lines 270-306, and
  `test_social_nemesis_ids_participates_in_canonical_hash_end_to_end`, lines 308-331), is the direct
  precedent and template for this ticket's own new canonical-hash test. Its scoped pytest command
  (`pytest tests/unit/core/ tests/unit/engine/test_hash_scheduler.py
  tests/unit/engine/test_resource_budget_gate.py tests/unit/kernel/ tests/certification/ -m "not slow"`)
  is reused below.
- `stored_artifacts/TCK-20260619-E33D-REP-DISCOUNTS/` — original reputation-discount ticket; confirms
  `apply_reputation_discount()`'s pure-function boundary and the two symmetric call sites
  (`ShopService.buy_item`/`ShopSystem.enforce`) already existed as designed, matching this
  investigation's independent re-confirmation above. `docs/guidelines/intentional_divergences.md`
  DEV-001 documents the faction-scoped-gating divergence from that ticket's original pseudocode —
  relevant context but not itself requiring an update from this ticket (it documents an already-shipped
  divergence, not the new region dimension).

## Risks and Open Questions

1. **Central open design question — additive field vs. replacement, and composition rule (blocks
   implementation, must be resolved by Plan, not assumed here)**: should the locality-scoped structure
   *replace* `public_reputation`'s role for the 3 named consumers while `public_reputation` itself is
   *retained unchanged* as the global scalar the 5+ un-named consumers (shop discount call sites,
   presenter, observability delta events, campaign `EntityCarryForward`, builder default) keep
   reading — or does the flat scalar's meaning change entirely? The evidence favors "retain and add":
   (a) `V2EntityBuilder.social(public_reputation=...)` and 8+ existing tests
   (SOC-134, TOWN-181's macro-economy test, `test_relationships.py:77`, `test_reputation_learning.py`)
   all construct/assert against a flat float and must keep passing per AC #4; (b) `place_attachment`
   itself is precedent for an *additive* field, not a replacement of any existing scalar; (c) the
   ticket's own Scope names only 3 consumers to update, implying the rest are meant to be unaffected.
   If Plan instead decides to replace the scalar's semantics, every un-named consumer above becomes an
   undeclared scope expansion.
2. **`apply_reputation_discount()`'s two real callers (`src/engine/shop.py:84`, `src/town/shop.py:38`)
   are absent from Related Code Areas** despite the pure function itself never touching
   `SocialComponent` — see Current Behavior above. Plan must either explicitly decide these two files
   need no change (discount keeps reading the retained global scalar) or add them to scope.
3. **`SocialMemoryImporter.apply()` is a pre-existing, real second write path to `public_reputation`**
   that bypasses `RelationshipService.process_update()` today (confirmed, `social_memory.py:518-526`).
   AC #1's literal "no second write path exists" guard test will need to either treat episode-boundary
   seeding as an accepted exception (and say so explicitly) or this ticket must also route
   `SocialMemoryImporter.apply()` through `RelationshipService.process_update()` — a small, low-risk
   change (recommended above) but one not currently named in ticket Scope.
4. **Composition rule for `heroism_delta`/`notoriety_delta` vs. a region-keyed delta is undefined** —
   does a global reputation-affecting event also touch the retained scalar, a specific region, or
   both? `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` §5.4 names exactly
   this class of question as required-but-unanswered for any new social feature.
5. **SOC-005's `test_path` is already broken** (file does not exist) independent of this ticket — must
   be fixed as part of this ticket's required parity-ledger touch on that entry, not silently left
   pointing at a nonexistent file.
6. Exact locality granularity (per-region vs. per-observer vs. per-settlement) remains, per the
   ticket's own Assumptions section and the source proposal's §6, explicitly a Plan-phase decision —
   this investigation recommends per-region (`Dict[RegionID, float]`, mirroring `place_attachment`
   exactly) as the evidence-backed default given it is the only shape with a fully-wired, tested,
   canonical-hash-covered precedent already in the same dataclass, but does not mandate it.

## Anti-Drift Hazards

- **Do not let a region-scoped write silently stop updating the retained global scalar** (if Plan
  decides to retain it) — this would silently break the discount call sites, the observability
  `reputation_delta` diff, and `EntityCarryForward`'s cross-episode carry, none of which are in this
  ticket's Related Code Areas and therefore would not be caught by editing them directly; only a
  regression test run across those areas would catch silent staleness.
- **Do not conflate this ticket's region-keyed locality with the already-anticipated *faction*-scoped
  extension** (`SocialMemoryRecord.faction_reputation`, `EntityCarryForward.reputation`'s "E43 adds
  per-faction detail" comment, TOWN-181's `divergence_note`) — these are two different axes (idea 60
  = geographic, a separate not-yet-built idea = organizational/faction), both already independently
  named in code comments as future work. Do not repurpose the faction-keyed `"default"` dict for
  region keys.
- **Do not touch `PublicReputationProfile`/`ReputationUpdateService`/`src/engine/quests.py:233-236`**
  — confirmed structurally distinct, explicitly out of scope, has its own real (if narrow) call site
  as of the sibling wiring ticket; do not merge or consolidate with it.
- **Do not expand the compiler-mapping / quest-metadata gaps** documented in the sibling
  TCK-20260828 investigation — unrelated pre-existing gaps, not this ticket's concern.
- **Preserve `SocialUpdate.merge()`'s existing semantics for `reputation_set`/`heroism_delta`/
  `notoriety_delta`** (last-writer-wins for `reputation_set`, summed for the deltas) when adding a new
  region-keyed delta field — follow `place_attachment_delta`'s sum-by-key merge pattern
  (`updates.py:339-341`), not a new/different composition rule, unless Plan explicitly justifies one.
- **Keep the new canonical-hash field's serialization sorted-by-key** (`dict(sorted(...))`, matching
  `place_attachment`'s existing line 902 exactly) — an unsorted dict would make the canonical JSON
  hash non-deterministic across runs with the same underlying data but different insertion order.
