---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-REPUTATION-LOCALITY-SCOPE
artifact_type: plan
tags: [social, determinism]
---

# Implementation Plan — TCK-20260904-REPUTATION-LOCALITY-SCOPE

## Summary

Add a new `SocialComponent.regional_reputation: Dict[str, float]` field (RegionID → local
reputation value, `default_factory=dict`) alongside the existing, **unchanged**
`public_reputation: float` scalar (`src/core/models/social.py:51`), mirroring the exact shape and
merge pattern already used by `place_attachment: Dict[str, float]` (line 47) and its
`place_attachment_delta`/merge/apply machinery in `SocialUpdate` (`src/core/updates.py:309,
339-341`) and `RelationshipService.process_update()` (`src/systems/social_systems/relationships.py:70-72,
88`). The global scalar keeps being written exactly as today via `heroism_delta`/`notoriety_delta`/
`reputation_set` (`relationships.py:92-95`) for every existing call site; a new
`regional_reputation_delta: Dict[str, float]` field on `SocialUpdate` additionally nudges the
region-keyed entry only when a call site supplies a `region_id`. This is purely additive: zero
existing call site changes shape or behavior, so all 8+ tests that construct/assert a flat float
keep passing unmodified (AC #4). `EntityState.to_canonical_dict()` (`src/core/state.py:892-909`)
and `StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py:69`) are both extended to
cover the new field, following the exact `place_attachment` precedent already in each file. The
pre-existing `SocialMemoryImporter.apply()` direct-`dc_replace` bypass
(`src/domains/campaigns/social_memory.py:522-526`) is fixed in the same ticket by routing it
through `RelationshipService.process_update()`, since investigation confirmed this is a small,
contained, zero-behavior-change refactor (AC #1's literal reading). The shop-discount call sites
(`src/engine/shop.py:84`, `src/town/shop.py:38`) and `appraise_contract()`'s optional
region-blending are explicitly out of scope — both are follow-up work, not required by any AC.

## Design Decisions

### Decision 1 — Retain the scalar unchanged, ADD a new region-keyed field

**Decision:** `SocialComponent.public_reputation: float = 1.0` (`social.py:51`) is retained
byte-for-byte with its current type, default, and every existing read/write behavior. A new field,
`regional_reputation: Dict[str, float] = field(default_factory=dict)` (RegionID → local reputation
value), is added immediately after `place_attachment` in the same dataclass.

**Justification:**
- Verified via direct read of `social.py:31-58`: `place_attachment: Dict[str, float]` (line 47) is
  an existing, fully-wired precedent for exactly this additive pattern in the same dataclass —
  it was added without replacing or repurposing any existing scalar field.
- Verified via direct read of `builder.py:498-518`: `V2EntityBuilder.social(public_reputation=...,
  place_attachment=...)` already accepts both a scalar and a dict kwarg side by side — no
  structural obstacle to adding a third, `regional_reputation`, alongside them.
- 8+ existing tests (`test_relationships.py:62-77`, `test_parity_soc_134.py`,
  `test_reputation_learning.py`, `test_social_memory.py:260-414`) construct/assert a flat float via
  the builder or `process_update()`; AC #4 requires these keep passing unmodified. A replace-in-place
  design would force every one of these tests to change, which is not "without breaking any existing
  test."
- 5 additional real consumers found during investigation but **not named in ticket Scope**
  (`state_presenter.py:99`, `event_extractor.py:927-928`/`event_shapers.py:1515`,
  `campaigns/state.py:101,108`, `campaigns/orchestrator.py:479,654`, `builder.py:512,533`) all read
  the flat scalar today. Retaining it unchanged means none of these five need to change — consistent
  with the ticket's own Scope naming only 3 consumers for update.

### Decision 2 — Composition rule for region-scoped events

**Decision:** A region-scoped reputation-affecting event calls
`RelationshipService.process_update()` exactly as today for the global scalar (zero change to that
half of the call path: `heroism_delta`/`notoriety_delta`/`reputation_set` still update
`social.public_reputation` unconditionally, per `relationships.py:92-95`). **Additionally**, when
the call site supplies a `region_id` via the new `SocialUpdate.regional_reputation_delta: Dict[str,
float]` field, `process_update()` also applies that keyed delta to
`social.regional_reputation[region_id]`, clamped `[0.0, 2.0]` to match the scalar's own clamp
range. When no `region_id` is supplied at a call site (the case for every existing call site today),
only the global scalar updates — unchanged from current behavior.

**Justification:**
- Verified via direct read of `updates.py:325-367` (`SocialUpdate.merge()`): the merge-by-summing
  pattern for `place_attachment_delta` (lines 339-341, `new_places[k] = new_places.get(k, 0.0) + v`)
  is the exact template to reuse for `regional_reputation_delta` — same key type (`str`/RegionID),
  same accumulate-then-apply shape.
- Verified via direct read of `relationships.py:70-72,88`: `place_attachment_delta` is applied with
  `max(0.0, min(1.0, ...))` clamping inside `process_update()` itself, not in the caller — the same
  location `regional_reputation_delta` must be applied, using `[0.0, 2.0]` to match
  `public_reputation`'s own clamp at line 94.
- This preserves 100% backward compatibility for every one of the 8+ existing tests and the 5
  un-named consumers: none of them pass a `region_id`, so none of them observe any behavior change.
- Matches investigation's own recommended resolution (investigation.md, "Risks and Open Questions"
  #1 and #4) and the anti-drift hazard "Do not let a region-scoped write silently stop updating the
  retained global scalar."

## Steps

### Step 1 — Add `regional_reputation` field to `SocialComponent`
**Files:** `src/core/models/social.py`
**Change:** Add `regional_reputation: Dict[str, float] = field(default_factory=dict)  # RegionID -> Local Reputation Score (0.0 to 2.0)` immediately after `place_attachment` (currently `social.py:47`) and before `betrayal_count` (currently line 49-50), keeping it visually grouped with `place_attachment` under the "Domain 4 Hardening: Nemesis & Place Memory" comment block since it follows the identical `Dict[str, float]`/RegionID-keyed shape (verified: `social.py:45-51`, `place_attachment` is `Dict[str, float]` at line 47, `public_reputation` is `float = 1.0` at line 51 — both read directly). Do not rename, remove, or change the type/default of `public_reputation`.
**Do NOT touch:** `public_reputation`'s declaration, type, or default value. `trust_history`, `familiarity_history`, `debt_history`, `fear_history`, `grudge_history`, `combat_loss_counts`, `salience_history`, `bonds`, `nemesis_ids`, `betrayal_count`, `betrayal_records`, `heroism_score`, `notoriety_score`, `last_offer_tick`, `rejection_count` — none of these fields change.
**Verify:** New field constructs with the default empty dict via `SocialComponent()` — covered indirectly by any test in Step 4/5 that constructs an entity via the builder without passing `regional_reputation`.

### Step 2 — Add `regional_reputation_delta` to `SocialUpdate` and its `merge()`/`is_noop()`
**Files:** `src/core/updates.py`
**Change:** Add `regional_reputation_delta: Dict[str, float] = field(default_factory=dict)  # RegionID -> Delta` to `SocialUpdate` (verified current field list at `updates.py:286-313`), placed near `place_attachment_delta` (line 309) since it follows the identical shape. Update `is_noop()` (lines 315-323) to also check `not self.regional_reputation_delta`. Update `merge()` (lines 325-367) to sum-by-key exactly like `place_attachment_delta` (verified pattern at lines 339-341: `new_places = dict(self.place_attachment_delta); for k, v in other.place_attachment_delta.items(): new_places[k] = new_places.get(k, 0.0) + v`) — add an equivalent `new_regional_rep` dict and pass it into the returned `SocialUpdate(...)` constructor call (lines 347-367) as `regional_reputation_delta=new_regional_rep`.
**Do NOT touch:** `reputation_set`'s last-writer-wins merge semantics (line 357), `heroism_delta`/`notoriety_delta`'s summed semantics (lines 358-359), or any other existing field's merge rule.
**Other writers to `SocialUpdate.merge()`:** `merge()` is called wherever multiple `SocialUpdate`s for the same tick/entity are combined before being handed to `process_update()`. Since `regional_reputation_delta` is a brand-new field that defaults to an empty dict on every existing `SocialUpdate` construction site, every pre-existing caller of `merge()` passes an empty dict for this field and the sum-by-key loop is a no-op for them — zero behavior change to any existing merge call site.
**Verify:** Covered by the anti-drift "composition-rule guard" test in Step 5 (asserts existing `reputation_set`/`heroism_delta`/`notoriety_delta` merge semantics unchanged) plus a new assertion that `regional_reputation_delta` sums by key across two merged updates.

### Step 3 — Apply `regional_reputation_delta` in `RelationshipService.process_update()`
**Files:** `src/systems/social_systems/relationships.py`
**Change:** In `process_update()` (verified current body at `relationships.py:16-100`), add a new local dict construction mirroring `place_attachment`'s handling (verified exact pattern at lines 70-72: `new_places = dict(social.place_attachment); for rid, delta in update.place_attachment_delta.items(): new_places[rid] = max(0.0, min(1.0, new_places.get(rid, 0.0) + delta))`). Add `new_regional_rep = dict(social.regional_reputation); for rid, delta in update.regional_reputation_delta.items(): new_regional_rep[rid] = max(0.0, min(2.0, new_regional_rep.get(rid, 0.0) + delta))` — clamp range `[0.0, 2.0]` matches `public_reputation`'s own clamp at line 94, not `place_attachment`'s `[0.0, 1.0]`. Add `regional_reputation=new_regional_rep` to the `replace(social, ...)` call (verified current call at lines 78-99) alongside the existing `public_reputation=...` line (line 93-95), which is left completely untouched — this is the concrete implementation of Design Decision 2 (both the global scalar and the region entry update independently from the same call, driven by whether the caller populated `regional_reputation_delta`).
**Do NOT touch:** The `public_reputation=update.reputation_set if update.reputation_set is not None else (...)` line (93-95) — zero changes to the global scalar's write logic. Do not add a `region_id` parameter to `process_update()`'s own signature; the region key travels inside `SocialUpdate.regional_reputation_delta`'s dict keys, exactly like `place_attachment_delta`.
**Other writers to `SocialComponent` via `process_update()`:** `process_update()` is the sole authoritative writer for every `SocialComponent` field per `SOC-217` (comment at `relationships.py:19`) — this step does not introduce a second writer, it extends the one authoritative writer's coverage to a new field, consistent with how every other field in this function is handled.
**Verify:** New test `test_public_reputation_locality_differs_by_region_after_region_scoped_event` (AC #2, test_plan.md item 2) — asserts two reads at region A vs region B differ after a `SocialUpdate(regional_reputation_delta={"region_a": 0.5})` is applied, and that `test_public_reputation_impact` (`test_relationships.py:62-77`, existing) still asserts `social.public_reputation == 1.5` unchanged.

### Step 4 — Fix `SocialMemoryImporter.apply()`'s direct-`dc_replace` bypass
**Files:** `src/domains/campaigns/social_memory.py`
**Change:** Verified current code at `social_memory.py:489-528`: `apply()` computes `new_reputation` (lines 518-520) then calls `dc_replace(entity.social, trust_history=new_trust, public_reputation=new_reputation)` directly (lines 522-526), bypassing `RelationshipService.process_update()`. Replace this with a call through `RelationshipService.process_update()`: construct `update = SocialUpdate(reputation_set=new_reputation if "default" in record.faction_reputation else None)` and call `new_social = RelationshipService.process_update(entity.social, update)`, then still apply the separately-computed `new_trust` (lines 512-515, which is an additive merge unrelated to any existing `SocialUpdate` field — trust here is a direct full-dict carry-forward, not a per-entity delta, so keep constructing `new_social` via `dc_replace(new_social, trust_history=new_trust)` immediately after the `process_update()` call, since `SocialUpdate.trust_delta` is a *delta* dict keyed by entity id with different semantics than this bulk carry-forward set). Import `RelationshipService` from `src.systems.social_systems.relationships` and `SocialUpdate` (already imported per investigation, `social_memory.py:4`) at the top of the file.
**Do NOT touch:** `SocialMemoryExporter.export()` (lines 433-466) — it is a pure read, not a write path, and needs no change. `SocialMemoryDecay.apply_decay()` (lines 374-409) — decay math is unchanged. Do not route `trust_history`'s bulk carry-forward through `SocialUpdate.trust_delta` — investigation confirmed `process_update()`'s other field reconstructions are no-ops on an empty `SocialUpdate` (verified: every field in `process_update()` defaults to copying `social`'s existing value when the corresponding `SocialUpdate` field is empty/None), so a two-step `process_update()` + `dc_replace(trust_history=...)` is the minimal, zero-behavior-change fix — do not attempt to force `trust_history`'s bulk-set semantics into the delta-shaped `SocialUpdate.trust_delta` field, which would change the merge contract.
**Other writers to `entity.social`:** `RelationshipService.process_update()` is the only other consumer of `SocialComponent` writes (per SOC-217); this step makes `SocialMemoryImporter.apply()` a caller of that same authoritative path instead of a second independent writer, closing the gap AC #1 requires closed. No ordering/race concern: `apply()` runs once per entity at episode-start construction (`CampaignOrchestrator._build_initial_state()`), before any tick-level `process_update()` calls for that episode.
**Verify:** Existing `test_social_memory.py` (lines 260-414) round-trip assertions must still pass unchanged (same computed `new_reputation` value, now routed through `process_update()` instead of `dc_replace` directly — verified no-op equivalence above). New guard test in Step 6 must confirm no direct `dc_replace(..., public_reputation=...)` remains anywhere outside `process_update()`.

### Step 5 — Extend `EntityState.to_canonical_dict()` for `regional_reputation`
**Files:** `src/core/state.py`
**Change:** In the `"social"` sub-dict of `to_canonical_dict()` (verified current content at `state.py:892-909`), add `"regional_reputation": dict(sorted(self.social.regional_reputation.items())),` immediately after the existing `"place_attachment": dict(sorted(self.social.place_attachment.items())),` line (line 902) — same sorted-dict pattern, since both are `Dict[str, float]` RegionID-keyed fields. Leave `"public_reputation": self.social.public_reputation,` (line 905) completely unchanged.
**Do NOT touch:** Any other key in the `"social"` sub-dict (lines 893-909) or any other sub-dict (`"strategic"`, `"combat"`, `"biological"`, `"lifecycle"`, `"navigation"`, etc.) in `to_canonical_dict()`. Do not touch `CanonicalStateHasher` in `src/engine/checkpoint.py` directly — per investigation, it delegates to `to_canonical_dict()` via `to_canonical_data()` (`checkpoint.py:63-108`) and needs no separate change.
**Other writers to the canonical-hash surface:** `to_canonical_dict()` is read by `CanonicalStateHasher.to_canonical_data()` (per-entity, sorted by id), `BudgetedCanonicalHasher`, and `CanonicalHashScheduler` — all delegate to this one function, so this is the single point of change; no other writer touches this dict's construction.
**Verify:** New test `test_social_public_reputation_locality_participates_in_canonical_hash` (AC #3, test_plan.md item 3), modeled on `test_social_seven_newly_covered_fields_participate_in_canonical_hash` (`tests/unit/core/test_entity_integrity.py:270-306`) — asserts the key is present and that diverging `regional_reputation` changes the canonical dict/hash output.

### Step 6 — Extend `StateFingerprinter.get_fingerprint()` for `regional_reputation`
**Files:** `src/replay/fingerprint.py`
**Change:** Verified current per-entity f-string at `fingerprint.py:56-71`, specifically line 69: `f"reputation={ent.social.public_reputation:.3f}:"`. Add a new segment immediately after it, following the file's own `region_ident`/`scar_ident` sorted-join precedent (verified at lines 85-94, e.g. `f"{k}:{v}" for k, v in sorted(...)`): add `f"regional_reputation={'|'.join(f'{k}:{v:.3f}' for k, v in sorted(ent.social.regional_reputation.items()))}:"` as a new line in the `entity_parts.append(...)` f-string, between the existing `reputation=` segment (line 69) and `strategic=` segment (line 70). Leave the `reputation={ent.social.public_reputation:.3f}:` segment itself unchanged.
**Do NOT touch:** Any other fingerprint segment (`resource_ident`, `node_ident`, `region_ident`, `scar_ident`, `group_ident`, `macro_ident`) or the `_inventory_identity`/`_strategic_identity`/`_group_identity` helper methods.
**Other writers to the fingerprint surface:** `StateFingerprinter.get_fingerprint()` is the sole builder of `raw_data`/`state_hash` (lines 104-116) — no other function writes to this string; this is the only change point.
**Verify:** New test confirming `StateFingerprinter.get_fingerprint()["state_hash"]` changes when only `regional_reputation` differs between two otherwise-identical states (AC #3, test_plan.md item 3, second half — "A second test should confirm `StateFingerprinter.get_fingerprint()`'s `state_hash` also changes").

### Step 7 — Add architecture guard test: sole write path
**Files:** New file `tests/architecture/test_social_write_paths.py` (placement follows existing convention — verified `tests/architecture/` already holds source-text/AST guard tests like `test_legacy_enum_usage_boundaries.py`, `test_no_new_hardcoded_gameplay_truth.py`, `test_no_old_structural_content_paths.py`)
**Change:** Add a source-text/AST scan test asserting no assignment to `public_reputation=` or `regional_reputation=` exists anywhere under `src/` outside `RelationshipService.process_update()` (`src/systems/social_systems/relationships.py`). After Step 4, `SocialMemoryImporter.apply()` no longer contains a direct `dc_replace(..., public_reputation=...)` call, so the guard's pattern does not need a documented exception for it — the guard should scan for the literal keyword patterns `public_reputation=` and `regional_reputation=` in `dc_replace(`/`replace(`/dataclass-constructor calls across `src/`, allowlisting only `src/systems/social_systems/relationships.py` (the authoritative writer), `src/core/models/social.py` (the dataclass definition itself, which contains the field declarations, not a write), and `src/core/builder.py` (construction-time seeding, the same accepted exception pattern the investigation confirms is analogous to, not a violation of, the "no second write path" guard for live-tick mutation).
**Do NOT touch:** `src/core/builder.py`'s existing `public_reputation`/`place_attachment` kwargs — these remain the accepted initial-construction exception, same as today; do not attempt to route builder construction through `process_update()`.
**Verify:** This test itself is the verification for AC #1. Confirm it fails if a hypothetical direct-`dc_replace` write is reintroduced (validate the guard's own correctness by temporarily reintroducing the pre-Step-4 bypass locally during implementation, per test-driven development, then removing it once the guard is confirmed to catch it — do not leave any reintroduced bypass in the final diff).

### Step 8 — Parity ledger updates
**Files:** `docs/parity_ledger/social_narrative.yaml`, `docs/parity_ledger/town_resource.yaml`
**Change:**
1. **SOC-005** (verified current entry at `social_narrative.yaml:54-62`): `test_path` currently reads `` '`tests_v2/parity/test_social_parity.py`' `` — confirmed via `find` that this file does not exist. Update `test_path` to point at a real, passing test covering "Public reputation is distinct from private narrative meaning" — use `tests/unit/social/test_relationships.py::test_public_reputation_impact` (existing, verified at `test_relationships.py:62-77`) since it directly exercises `public_reputation` as distinct from `trust_history`/narrative fields. Update `v2_evidence` to also mention the new `regional_reputation` field exists as a structurally separate locality dimension, not a replacement.
2. **SOC-134** (verified current entry at `social_narrative.yaml:1435-1443`): update `v2_evidence` to note `appraise_contract()`'s read (`source_entity.social.public_reputation`) is unchanged by this ticket — the field it reads still exists with identical semantics.
3. **SOC-CROSS-EP-002** (verified current entry at `social_narrative.yaml:2539-2547`): update `v2_evidence`/`divergence_note` to note `SocialMemoryImporter.apply()` now routes its `public_reputation` write through `RelationshipService.process_update()` (Step 4 above) instead of a direct `dc_replace`, and that `regional_reputation` is NOT currently exported/imported across episode boundaries (out of scope per this ticket — only the flat `faction_reputation["default"]` carries forward, unchanged).
4. **TOWN-181** (verified current entry at `town_resource.yaml:1968-1978`): update `divergence_note` to state that a region dimension (`regional_reputation`) now exists on `SocialComponent`, but the discount consumer (`apply_reputation_discount()` and its two callers) does not yet read it — still reads the retained global scalar, unchanged. This documents the scope boundary from Step 9 (Scope Guards) rather than leaving the gap undocumented.
5. **New entry `SOC-266`** (next available id in `social_narrative.yaml`, confirmed via `grep -o "id: SOC-[0-9]*" docs/parity_ledger/social_narrative.yaml | sort -n | tail` → highest existing is `SOC-265`): add a new entry documenting the `regional_reputation` mechanism itself — `text`: "SocialComponent.regional_reputation (Dict[RegionID, float]) provides a region-scoped reputation dimension additive to the retained global public_reputation scalar; both are written by RelationshipService.process_update() from the same SocialUpdate when a region_id is supplied via regional_reputation_delta." `status: verified`, `priority: P1`, `test_path` pointing at the new Step 3 test.
**Do NOT touch:** Any other entry in either file. Use `tools/parity_ledger_writer.py` (the sanctioned schema-validating writer) for these edits, per CLAUDE.md's "Parity-updater full-file YAML rewrite risk" guidance — never a raw full-file Edit/ad-hoc script rewrite of these YAML files.
**Verify:** `docs/parity_ledger/schema.json` validation (via the sanctioned writer tool) passes for both files; SOC-005's new `test_path` exists and passes.

### Step 9 — Docs updates
**Files:** `docs/mechanics/03_economic_laws.md`, `docs/simulation/social_systems_contract.md`, `docs/simulation/domains/social_memory_contract.md`, `docs/brainstorm/rpg_feature_atlas.html`, `docs/brainstorm/simulation_capabilities.html`
**Change:**
1. `docs/mechanics/03_economic_laws.md` §4.1 (verified investigation citation at line 104, "sourced from `SocialComponent.public_reputation`"): no wording change needed to the formula itself — the discount consumer still reads the retained global scalar unchanged (Decision 1); add one sentence noting a region-scoped `regional_reputation` dimension now exists on `SocialComponent` but is not yet consumed by the discount formula (explicit scope-boundary disclosure).
2. `docs/simulation/social_systems_contract.md` "Trust evaluation pipeline" step 1 (verified investigation citation at line 32): no change needed to the described read (`source_entity.social.public_reputation / 2.0`) since `appraise_contract()` is unchanged by this ticket (Step "Do NOT touch" below); add a note that region-scoped blending was considered and deferred as a follow-up.
3. `docs/simulation/domains/social_memory_contract.md` "Export / Import Hooks" section (verified investigation citation at lines 66-80): update the Import Hook description to state the write now goes through `RelationshipService.process_update()` (Step 4) instead of a direct field-seed, and that `regional_reputation` is not part of the cross-episode carry-forward in this ticket.
4. `docs/brainstorm/rpg_feature_atlas.html` idea 60's card (anchor `id="idea-60"`): update badge from `"gap"`/"Aspirational — design only" to built status, following the doc's own append-a-correction-note convention (per investigation's Docs Requiring Update guidance) rather than rewriting history.
5. `docs/brainstorm/simulation_capabilities.html` idea 60's mirrored card (section 14 "Memory, Reputation & Legacy"): update in the same turn as #4, per the repo's atlas↔capabilities-page sync convention, in plain non-dev language describing "reputation now differs by region."
**Do NOT touch:** `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` and `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` — investigation explicitly confirmed both are point-in-time records that do not need editing for this ticket.
**Verify:** `make knowledge-index-update` run after any `docs/` file is created/modified, per CLAUDE.md's After Work step.

## Scope Guards

Explicit list of things this plan must NOT touch, derived from the ticket's Out of Scope section
and the investigation's anti-drift hazards:

- **`src/engine/shop.py:84` and `src/town/shop.py:38`** (the two real callers of
  `apply_reputation_discount()`) — OUT OF SCOPE. `apply_reputation_discount()` itself
  (`src/systems/economy_systems/reputation_discount.py`) is a pure function with zero
  `SocialComponent` access; neither caller is named in this ticket's Related Code Areas. Both
  continue reading `entity.social.public_reputation` (the retained global scalar) exactly as today.
  Wiring region-awareness into the discount path is a natural follow-up ticket, not required by any
  AC — AC #4 only requires this consumer not to BREAK, not to become region-aware.
- **`SocialAppraisalSystem.appraise_contract()`'s region-blending** — OUT OF SCOPE for this ticket
  beyond the zero-change verification in Step 3's test. Investigation confirmed `appraise_contract()`
  reads `source_entity` (the contract's subject), not `entity` (the appraiser), and no `region_id` is
  available at that call site today (`appraisal.py:20-37` takes `entity`, `contract`, `state` — no
  region parameter). Blending in the regional entry is a documented follow-up, not implemented here.
- **`PublicReputationProfile`/`ReputationUpdateService`/`src/engine/quests.py:233-236`** — confirmed
  structurally distinct (different Python attribute path: `entity.cognition.relationships.public_reputation`,
  a per-label dict, vs. `entity.social.public_reputation`, a plain float). Do not merge, consolidate,
  or touch.
- **The 5 already-tracked missing SocialComponent canonical-hash fields** (`debt_history`,
  `salience_history`, `nemesis_ids`, `place_attachment`, `betrayal_records`) — already closed by
  TCK-20260902-SOCIAL-CANONICAL-HASH-GAP; not this ticket's concern.
- **Idea 53's birth-seed write, idea 54's `ClanState.clan_reputation` field, idea 55/58's
  death-and-lineage branch** — sibling child tickets that depend on this ticket landing first, not
  vice versa.
- **`SocialUpdate.merge()`'s existing `reputation_set` (last-writer-wins), `heroism_delta`/
  `notoriety_delta` (summed) semantics** — unchanged; only a new field and its own sum-by-key merge
  rule are added.
- **`state_presenter.py:99`, `event_extractor.py:927-928`/`event_shapers.py:1515`,
  `campaigns/state.py:101,108`, `campaigns/orchestrator.py:479,654`, `builder.py:512,533`** — the 5
  un-named consumers of the retained global scalar. None of these files change; they continue reading
  `public_reputation` unaffected, per Decision 1.
- **`faction_reputation` / `EntityCarryForward.reputation`'s "E43 adds per-faction detail"** — a
  different, unbuilt organizational axis. Do not repurpose the faction-keyed `"default"` dict for
  region keys, and do not export/import `regional_reputation` across episode boundaries in this
  ticket (Step 4 only fixes the write-path bypass for the existing flat scalar; it does not add
  cross-episode carry-forward for the new field).
- **`docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md`,
  `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`** — confirmed by investigation as
  not requiring edits.

## Dependency Map

- Step 1 (add field) has no dependencies — do first.
- Step 2 (SocialUpdate field + merge) depends on Step 1 (references the field name for consistency,
  though technically independent in code — do after Step 1 for review clarity).
- Step 3 (process_update apply logic) depends on Steps 1 and 2 (needs both the `SocialComponent`
  field and the `SocialUpdate` field to exist).
- Step 4 (SocialMemoryImporter fix) depends on Step 3 only insofar as it calls
  `RelationshipService.process_update()` — but does not touch `regional_reputation` at all, so it
  can technically be done independently/in parallel with Steps 1-3. Order after Step 3 for a single
  coherent review pass.
- Step 5 (canonical dict) depends on Step 1 only (reads `self.social.regional_reputation`).
- Step 6 (fingerprint) depends on Step 1 only.
- Step 7 (guard test) depends on Step 4 (the guard's correctness assumes the bypass is fixed) and
  Step 1 (references `regional_reputation=` pattern).
- Step 8 (parity ledger) depends on Steps 3, 4, 5, 6 being implemented (documents their outcomes).
- Step 9 (docs) depends on Steps 3, 4, 8.

Steps 1, 5, and 6 can be implemented and verified in parallel once Step 1 lands; Steps 2-3 are a
tight sequential pair; Step 4 is independent of the regional_reputation mechanism entirely and can
run in parallel with Steps 1-3 if convenient.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — sole write path (no second write path exists) | Steps 4, 7 | `tests/architecture/test_social_write_paths.py` (new) |
| AC #2 — locality-scoped read differs by region after region-specific event | Steps 1, 2, 3 | `test_public_reputation_locality_differs_by_region_after_region_scoped_event` (new, `tests/unit/social/test_relationships.py` or new `tests/unit/social/test_reputation_locality.py`) |
| AC #3 — canonical-hash coverage preserved, shape-correct | Steps 5, 6 | `test_social_public_reputation_locality_participates_in_canonical_hash` (new, `tests/unit/core/test_entity_integrity.py`) + new `StateFingerprinter` `state_hash`-changes test |
| AC #4 — three named consumers (appraise_contract, apply_reputation_discount, social_memory) keep working without breaking existing tests | Steps 1 (no scalar change), 4 (importer fix, zero behavior change) | `test_parity_soc_134.py` (existing, unmodified), `test_macro_economy.py::test_reputation_discount_applies` (existing, unmodified), `test_social_memory.py` (existing, unmodified — plus Step 4's own regression coverage) |
| AC #5 — corrected premise recorded in ticket's Investigation Notes | N/A (already satisfied by investigation.md; ticket's Implementation Notes section must carry the corrected-premise text forward when the ticket is finalized) | done-checker review, not a pytest assertion |

## Anti-Drift Notes

- **Do not let the region-scoped write silently stop updating the retained global scalar.** Step 3's
  `process_update()` change must leave the existing `public_reputation=update.reputation_set if
  update.reputation_set is not None else (...)` line (relationships.py:93-95) completely untouched —
  the new `regional_reputation` write is additive, applied from the same function call, never a
  replacement of the scalar's write logic.
- **Do not conflate this ticket's region-keyed `regional_reputation` with the already-anticipated
  faction-scoped extension** (`SocialMemoryRecord.faction_reputation`, `EntityCarryForward.reputation`'s
  "E43 adds per-faction detail" comment, TOWN-181's `divergence_note`). These are two different axes
  (this ticket = geographic/region; a separate, unbuilt idea = organizational/faction). Do not
  repurpose the `"default"` faction key for region keys anywhere.
- **Keep the new canonical-hash field's serialization sorted-by-key** — Step 5's `dict(sorted(...))`
  and Step 6's `sorted(...)` join must exactly match the `place_attachment` precedent already in both
  files; an unsorted dict would make the hash non-deterministic across runs with identical underlying
  data but different insertion order.
- **`SocialUpdate.merge()`'s existing composition rules for `reputation_set`/`heroism_delta`/
  `notoriety_delta` must not change** while adding `regional_reputation_delta`'s own sum-by-key rule
  — Step 2 adds a new field and its own merge branch without touching the three existing lines
  (updates.py:357-359).
- **Step 4's `SocialMemoryImporter.apply()` fix must remain a zero-behavior-change refactor** — the
  computed `new_reputation` value must be identical before and after the change; only the write
  mechanism moves from `dc_replace` to `RelationshipService.process_update()`. If implementation
  discovers `process_update()`'s reconstruction of any other field (e.g. `trust_history`,
  `betrayal_records`) is NOT actually a no-op on an empty `SocialUpdate` for some edge case not
  caught during Step-3 review, stop and re-verify against the running `entity.social` state before
  proceeding — do not assume no-op behavior without confirming it against the actual code path being
  exercised in `apply()`'s specific call context.
- **`apply_reputation_discount()`'s two callers and `appraise_contract()`'s region-blending are
  explicitly out of scope** — do not add a `region_id` parameter to either shop call site or to
  `appraise_contract()`'s signature as part of this ticket, even though it would be a small, tempting
  addition given the new field's existence. Flag both as disclosed follow-up gaps in the ticket's
  Implementation Notes when it is finalized, per the ticket's own scope boundary and this plan's Scope
  Guards section.
- **Use `tools/parity_ledger_writer.py` for all Step 8 YAML edits** — never a raw full-file Edit/
  ad-hoc script rewrite of `docs/parity_ledger/*.yaml`, per the project's documented corruption risk
  for that class of edit.

## Unresolved Questions

None. Both central open design questions from investigation.md (additive-field-vs-replacement shape,
and the composition rule) are resolved above under "Design Decisions," with evidence-backed
justification. No further human-input-required question remains; investigation's Risk #2 (shop
discount call sites) and the `appraise_contract()` region-blending option are resolved as explicit,
disclosed out-of-scope follow-ups (see Scope Guards), not blocking questions.

## Deviations (recorded during Implement phase)

1. **Step 4's `SocialUpdate` import was NOT already present, contrary to the plan's own text.**
   Plan Step 4 states `SocialUpdate` is "already imported per investigation, `social_memory.py:4`."
   A direct read of `src/domains/campaigns/social_memory.py` at implementation time showed only
   `dataclasses`/`typing` imports at module level — `SocialUpdate` was not imported anywhere in the
   file. Implementation added both `from src.core.updates import SocialUpdate` and
   `from src.systems.social_systems.relationships import RelationshipService` as new module-level
   imports. Verified no circular-import risk: neither `src.core.updates` nor
   `src.systems.social_systems.relationships` (nor `src.core.state`, which the latter imports)
   references `src.domains.campaigns` anywhere.

2. **A second, previously-undisclosed `public_reputation` write-path bypass was found and fixed:
   `CampaignOrchestrator._build_initial_state()`** (`src/domains/campaigns/orchestrator.py`, the
   "Apply carried reputation" block). Plan Step 4 and the investigation named only
   `SocialMemoryImporter.apply()`'s bypass. Step 7's architecture guard test
   (`tests/architecture/test_social_write_paths.py`), once written and run for real, additionally
   caught `orchestrator.py`'s `dc_replace(base.social, public_reputation=cf.reputation)` inside
   `_build_initial_state()` — a second, structurally identical episode-start bypass the
   investigation's own "Additional real consumers" section had mis-classified as a pure read site
   (it cited `orchestrator.py:479,654` together as "construction/read sites" without noticing line
   654 is a write). Per CLAUDE.md's Gate Integrity rule ("never edit an artifact to make a gate
   pass instead of fixing the underlying substance"), this was fixed rather than allowlisted: the
   write now goes through `RelationshipService.process_update(base.social,
   SocialUpdate(reputation_set=cf.reputation))`, a zero-behavior-change refactor (confirmed:
   `base = EntityState(id=eid, kind="entity")` is always a fresh default `SocialComponent`, so
   `process_update()`'s reconstruction of every other field is a no-op on empty defaults). This
   expands Step 4's scope by one additional call site but does not change its design — same fix
   pattern, same authoritative writer, same zero-behavior-change guarantee.

3. **The Step 7 guard test's allowlist required two additional entries beyond the plan's named
   three** (`relationships.py`, `social.py`, `builder.py`), both confirmed false positives rather
   than write-path violations:
   - `src/engine/quests.py` — writes `RelationshipModel.public_reputation`
     (`entity.cognition.relationships.public_reputation`, the `PublicReputationProfile` dict), a
     field that only shares a name with `SocialComponent.public_reputation`. Confirmed
     structurally distinct by the investigation itself and explicitly out of scope per the
     ticket's Out of Scope section.
   - `src/replay/fingerprint.py` — the guard's `regional_reputation=` text pattern matched this
     ticket's own new fingerprint f-string segment label (`f"regional_reputation={...}"`), not a
     write call.
   Both are documented in the guard test file itself with per-entry comments, following the same
   allowlist-with-rationale convention as `tests/architecture/test_legacy_enum_usage_boundaries.py`.
   Verified the guard still catches a real reintroduced bypass: temporarily re-injected a
   `dc_replace(entity.social, public_reputation=0.5)` bypass into `social_memory.py`, confirmed the
   guard test failed, then restored the fix (per Step 7's own TDD verification instruction).
