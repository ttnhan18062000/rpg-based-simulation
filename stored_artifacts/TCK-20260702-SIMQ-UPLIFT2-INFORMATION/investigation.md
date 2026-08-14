---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT2-INFORMATION
artifact_type: investigation
tags: [simulation-quality, information, belief, worldbuilder, feature-flags]
---

# Investigation — TCK-20260702-SIMQ-UPLIFT2-INFORMATION

## Current Behavior (file:line refs)

### The two gates the ticket already names

1. `ENABLE_BELIEF_ASSIMILATION` defaults to `FeatureMode.OFF`
   (`src/domains/optimization/feature_flags.py:18`). `run_phase("information_belief", ...)`
   at `src/engine/pipeline.py:152` skips `InformationBeliefPhase.apply()` entirely while OFF.
2. `AuthoritativeState.information_source_profiles: List[Any] = field(default_factory=list, ...)`
   (`src/core/state.py:1145`) is never populated for any calibration world — confirmed by
   grepping `src/worldbuilding/compiler.py`'s single `AuthoritativeState(...)` constructor
   call (lines 412-425): **`information_source_profiles=` is never passed at all.** This is
   the exact same bug class the sibling FACTION ticket found for `factions=` before that
   ticket's fix — except FACTION's compiler call has since been patched
   (`factions=factions` now appears at compiler.py:424); `information_source_profiles` has
   received no equivalent patch. Confirmed: **yes, the FACTION-style "compiler never
   constructs the field at all" bug also applies to `information_source_profiles`,
   unmodified.**

### A third, previously undocumented gate: `InformationBeliefPhase.apply()` has no reachable trigger, even with both of the above fixed

`InformationBeliefPhase.apply()` (`src/domains/information/phase.py:28-110`) only ever
produces a non-empty `StateUpdate` through one of two branches per actor:

- **Branch A — assimilate a pending response** (`phase.py:54-81`): requires
  `pending_responses` (sourced from `state.pending_information_responses`,
  `pipeline.py:151`) to contain an entry keyed by `actor.id`.
  **`state.pending_information_responses` is declared at `state.py:1144` and read at
  `pipeline.py:151`, but grepping all of `src/` found zero writers anywhere in the engine.**
  It is permanently `[]`. Branch A is dead in every current calibration run and would
  remain dead even after this ticket's Scope items 1-4 are implemented exactly as written.
- **Branch B — route a new query** (`phase.py:83-105`): requires
  `actor.self_model.knowledge.unknowns` to be non-empty. `self_model.knowledge.unknowns`
  (`src/core/self_model.py:179`) defaults to `{}` at entity build time (no seeding found in
  `src/core/builder.py`). The only two writers found:
  - `KnowledgeModelService.assimilate()` (`src/cognition/knowledge_model.py:93-101`) adds
    unknowns **from an already-received `InformationResponse`** — i.e. it requires Branch A's
    data to already exist, which it never does.
  - `SelfModelUpdatePhase.apply()` (`src/cognition/self_model_phase.py:32-56`), the class
    gated by the *separate* `ENABLE_SELF_MODEL_COGNITION` flag (also `OFF` by default,
    `feature_flags.py:15`, and **not** set in `config/simulation_quality/profiles/urban_political.yaml`),
    calls `SelfModelUpdatePhase.run(entity=entity, state=state, events=[], tick=state.tick)`
    with **`events` hardcoded to `[]`** (`self_model_phase.py:47`). `run()`'s loop that calls
    `KnowledgeModelService.assimilate(temp_entity, event, tick)` (`self_model_phase.py:104`)
    therefore never executes even if the flag were turned ON.

  **Net effect: `self_model.knowledge.unknowns` is unreachable dead state in the current
  engine wiring — no code path in the standard pipeline ever populates it.** Branch B is
  also permanently dead in every current calibration run.

Because both branches are unreachable, **`InformationBeliefPhase.apply()` always returns an
empty `StateUpdate()` regardless of `ENABLE_BELIEF_ASSIMILATION` or
`information_source_profiles` content.** Seeding two `InformationSourceProfile` entries per
the ticket's Scope item 3 and flipping the flag per Scope item 4 will not, by themselves,
produce a single `belief_assimilated` event. `last_assimilated_tick` (the property
`event_extractor.py:286` reads to emit `belief_assimilated`) is set only inside Branch A
(`phase.py:76-78`), which nothing ever reaches.

### A fourth dead pathway found while checking whether `lead_certainty_updated` is reachable another way

`lead_certainty_updated` (`src/observability/event_extractor.py:415-428`) fires purely from
a **state diff**: it compares `entity.strategic.leads[lid].certainty` between the prior and
current tick for the *same lead id*. It does not require `InformationBeliefPhase` at all —
any system that mutates an existing lead's certainty in place would trigger it. Three
candidate systems were checked:

- `InformationNeedDetector.detect_and_generate()` (`src/engine/domain/cognition_extras.py:36-98`)
  — creates an `INFORMATION_SEEKING` `ProjectState` from a high-priority `UnknownFact`. Its
  own docstring admits it is **not wired**: *"Wire-up: call detect_and_generate() in
  CognitionDomain.execute_brain() ..."* — grepping all of `src/` outside this file found zero
  callers. It also depends on `self_model.knowledge.unknowns` (dead, per above), so even if
  wired it would not fire in current calibration worlds.
- `PaidInformationTransactionSystem.enforce()` (`src/engine/pipeline_phases/paid_information.py:74-183`)
  — **is** wired unconditionally at `pipeline.py:296-297` (no feature flag), but requires (a)
  `state.information_providers` non-empty (a *separate* durable field from
  `information_source_profiles`, `state.py:1150`, Epic 4.2B) and (b) an entity with an active
  `ProjectKind.INFORMATION_SEEKING` project — which only `InformationNeedDetector` (dead,
  above) or `GuildAction.visit()` (below) ever create. Additionally, each `LeadState` it
  creates uses `id=f"lead_info_{entity.id}_{provider_id}_{state.tick}"` — **a unique id every
  tick** — so even if it fired, `event_extractor`'s prior/current lead-id diff would never see
  a repeat id and `lead_certainty_updated` would still not fire from this path (only
  `paid_information_transaction`/`paid_info_transaction` would, on first purchase).
- `GuildAction.visit()` (`src/town/guild.py:11-`) — also creates `LeadState` entries, but has
  **zero callers anywhere in `src/`** (confirmed via graphify + grep); it is orphaned code,
  not reachable from the pipeline.

`StrategicIntelligenceSystem.fused_strategic_pass()`'s belief confirmation/contradiction
block (`src/systems/strategic_systems/intelligence.py:314-347`) *can* mutate an existing
lead's certainty in place via `BeliefCycleSystem.process_observation`/`apply_contradiction`,
which **would** trigger `lead_certainty_updated` — but only for leads that already exist with
`kind == "location"`, requiring physical proximity to the lead's stored coordinates plus a
hostile-detection check. Since no lead-creation path in this system's reach is itself wired,
this block currently never has a lead to operate on either.

**Conclusion: as of this investigation, every code path that could ever produce
`belief_assimilated`, `lead_certainty_updated`, or `paid_information_transaction` in a
calibration run is either flag-gated OFF, reads permanently-empty state, or is orphaned
code with no caller.** This matches `docs/simulation_quality/event_type_coverage.md`
showing `calibration_hits: 0` for all of `belief_assimilated` (line 61), `belief_updated`
(62), `paid_information_transaction` (70), `paid_info_transaction` (71),
`lead_certainty_updated` (78), `lead_contradiction_resolved` (79), `paid_info_changed_goal`
(80), `belief_stale` (81), `lead_certainty_changed` (96).

### World-content plumbing gap (UQ-1)

`data/worlds/urban_political/world.yaml` is a **composition** file
(`schema_version: "worldcomposition.v1"`), not a raw `WorldSpec`. It is resolved by
`WorldAssemblyResolver.assemble()` (`src/worldassembly/resolver.py`) into
`data/worlds/urban_political/resolved/world.resolved.yaml` (a `WorldSpec`), which
`WorldCompiler.compile()` then consumes to build `AuthoritativeState`.

- `src/worldbuilding/schema.py`'s `WorldSpec` (lines 128-146) has no
  `information_source_profiles` field of any kind.
- `src/worldassembly/schema.py`'s `WorldCompositionSpec` / `NormalizedWorldComposition` have
  no `information_source_profiles` field either (grep for `information` in both files: zero
  hits).
- `src/worldassembly/resolver.py` has zero references to `information` anywhere.
- `src/worldbuilding/compiler.py`'s `AuthoritativeState(...)` call (lines 412-425) passes
  `entities`, `resource_nodes`, `buildings`, `regions`, `terrain`, `global_resources`,
  `blocked_tiles`, `town_tiles`, `town_entity_ids`, `factions` — **no**
  `information_source_profiles`.

**There is no existing world-YAML → compile → `AuthoritativeState.information_source_profiles`
path at any layer.** This must be built net-new: a `InformationSourceProfileSpec`-equivalent
Pydantic model on `WorldSpec` (worldbuilding/schema.py), compiler seeding logic that
constructs `InformationSourceProfile` domain objects and passes
`information_source_profiles=` into the `AuthoritativeState(...)` call, and — because
`urban_political/world.yaml` is a *composition*, not a raw spec — a mirrored field on
`WorldCompositionSpec`/`NormalizedWorldComposition` plus resolver plumbing to carry
composition-level content through to the resolved `WorldSpec`. This is the exact same shape
of change the FACTION ticket made for `faction_tension_overrides`
(`stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/plan.md` Steps 1-4), and the FACTION
plan's hazard notes apply equally here: editing `module_refs`-referenced module YAML
(`frontier_village_core.yaml`, `trading_company_hub.yaml`, etc.) directly is **not**
appropriate unless a catalog-merge precedent for information sources already exists (it does
not — there is no `data/content/*/information_sources.yaml` catalog, confirmed by absence of
any `information` hit in `worldassembly/resolver.py`), so a composition-level field
(mirroring `faction_tension_overrides`) on `urban_political/world.yaml` is the safer,
scope-contained mechanism — but this must be confirmed during planning, not assumed, since
unlike factions there is no pre-existing catalog to collide with, which may mean a
module-level list field is actually safe here (no catalog pre-seed to be silently
overridden). **This is a real fork the plan phase must resolve with evidence, not
preference** (see Risks/Open Questions).

### `knowledge_scopes` matching semantics (UQ-2)

`InformationQueryRouter.route()`'s `matches_scope()` helper (`src/domains/information/router.py:46-53`)
hard-codes a **different vocabulary** than `InformationQuery.kind`:

```python
def matches_scope(kind: str, scopes: Tuple[str, ...]) -> bool:
    if kind == "material_source" and "common_resource_sources" in scopes: return True
    if kind == "recipe_definition" and "recipe_requirements" in scopes: return True
    if kind == "danger_rating" and "regional_danger" in scopes: return True
    return False
```

`knowledge_scopes` are **not free-form** and **not an enum** — they are matched against three
specific hard-coded literal strings: `"common_resource_sources"`, `"recipe_requirements"`,
`"regional_danger"`. **The ticket's own Scope item 3 example values —
`knowledge_scopes: ["danger_rating", "material_source"]` for the GUIDE profile and
`["material_source", "recipe_definition"]` for the TRAVELER profile — use the wrong
vocabulary and would silently fail to match for the GUIDE profile.** (`query.kind` values are
`"material_source"`, `"recipe_definition"`, `"danger_rating"` — literally reused as the
`knowledge_scopes` strings in the ticket's example, which is exactly what `matches_scope`
does *not* check for.)

There is one bypass: `router.py:57` — `if not matches_scope(...) and prof.source_kind !=
"traveler": continue` — any profile with `source_kind == "traveler"` skips the scope check
entirely and is always a candidate regardless of its `knowledge_scopes` content. This means
Profile 2 (`traveling_merchant_rumors`, `source_kind="traveler"`) in the ticket's Scope item 3
would work as a candidate regardless of its scope values, but **Profile 1
(`town_notice_board`, `source_kind="guide"`) would never match any query** with the scopes
given in the ticket, because `"common_resource_sources"` is not in
`["danger_rating", "material_source"]`. This must be corrected in the plan/implementation:
Profile 1's `knowledge_scopes` should be `["common_resource_sources", "regional_danger"]` (or
similar, matching the router's literal vocabulary), not `["danger_rating",
"material_source"]` as the ticket currently specifies. This finding does not block
investigation but is a concrete correction the plan phase must make to Scope item 3's literal
YAML content — otherwise Profile 1 would be world content that compiles cleanly but never
actually gets selected by the router.

### Emission condition for `belief_assimilated` (UQ-3)

Resolved above in "A third, previously undocumented gate": `belief_assimilated` fires **only**
when `InformationBeliefPhase.apply()`'s Branch A executes for an actor on the current tick —
i.e. only when a pending response was assimilated (`property_updates["last_assimilated_tick"]
= state.tick`, `phase.py:76-78`, read by `event_extractor.py:286`). It is **not** emitted on
every tick the phase runs, and Branch B (routing a new query) never sets
`last_assimilated_tick`, so it never triggers `belief_assimilated` even when it does fire.
As established above, Branch A's only data source (`state.pending_information_responses`) is
never written anywhere in the engine, so — independent of this ticket's stated fix — the
emission condition for `belief_assimilated` is currently **unreachable** in any calibration
world.

## Mechanics/Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` documents strategic-lead decay (`Info Decay`
  bullet, line 78: leads demote APPROXIMATE → VAGUE → EXHAUSTED after 50 ticks without
  refresh, `BeliefCycleSystem.decay_stale_beliefs`, `src/systems/strategic_systems/belief.py:47`)
  but has **no chapter or section documenting `InformationSourceProfile`,
  `InformationBeliefPhase`, or the belief-assimilation query/response cycle at all**. This is
  a genuine Mechanics Bible coverage gap the plan phase should flag (not necessarily fix in
  this ticket, per Out of Scope's "no full marketplace" clause) — there is no authoritative
  chapter this ticket's world-content change can cite for the shape of
  `InformationSourceProfile` fields; the dataclass in `src/domains/information/schema.py` is
  the only source of truth.
- `docs/audits/D19_domain_phase_inventory.md` §3 (line 84) documents PP-04 /
  `information_belief` as `feature-gated (flag: ENABLE_BELIEF_ASSIMILATION)` with the
  suggested acceptance criterion *"With flag ON an entity receiving a high-trust information
  response updates its belief store; with flag OFF belief state is unchanged."* This
  documentation implicitly assumes the flag alone gates the phase's effect — it does **not**
  mention that `unknowns`/`pending_responses` are also dead upstream, i.e. the existing audit
  itself is incomplete relative to this investigation's findings.
- Engine kernel phase ordering (`docs/engine/kernel.md`): `information_belief` (PP-04) runs
  in the same tick pass as `self_model` (PP-02, gated by the separate
  `ENABLE_SELF_MODEL_COGNITION` flag) — both are Enhanced RPG phases inserted into the
  6-phase kernel's Resolution stage. No ordering conflict was found; the blocker is upstream
  data availability, not phase sequencing.

## Parity Ledger Overlap (IDs + status)

- `docs/parity_ledger/infrastructure.yaml` (~line 3008-3017): existing entry for
  `InformationScorer` — *"InformationScorer covers all contract §5 INFORMATION & BELIEF
  rules: belief_active, subjective_divergence, belief_pipeline_deaf, ... paid_info_memory_failure.
  paid_information_transaction scored here (not in EconomyScorer) per SQ-16."*
  `v2_evidence: src/simulation_quality/scorers/information.py::InformationScorer.score`,
  `test_path: tests/simulation_quality/test_information_scorer.py`. This entry documents the
  *scorer*, not the event-emission reachability gap found in this investigation — it should
  be extended (not replaced) with a note that `belief_assimilated` /
  `lead_certainty_updated` / `paid_information_transaction` emission requires
  `information_source_profiles` seeding + `ENABLE_BELIEF_ASSIMILATION=ON` at minimum, and (per
  this investigation's new finding) that Branch A/Branch B of `InformationBeliefPhase` remain
  unreachable without additional wiring beyond this ticket's originally scoped world-content
  change.
- `docs/parity_ledger/social_narrative.yaml` (~lines 3023-3035): entries for
  `paid_information_transaction` and `paid_info_transaction` emission conditions
  (`src_kind == INFORMATION_PURCHASE`) — these describe the *emitter*, already correct per
  this investigation; no `status: divergent` needed there, but a new/extended entry should
  record that the emitter is currently unreachable (`INFORMATION_SEEKING` project creation is
  dead code) pending this ticket's decision on scope.
- No existing parity ledger entry documents `information_source_profiles` compile-time
  seeding (the FACTION-equivalent of `FAC-012`) — a new entry is required once compiler
  wiring exists, analogous to `docs/parity_ledger/faction.yaml`'s `FAC-012` added by the
  sibling ticket.
- The ticket's own Related Docs section names `docs/parity_ledger/social_narrative.yaml` and
  `infrastructure.yaml` as candidate files for the new entry — both already contain
  INFORMATION-pillar-adjacent entries (above), so extending one of these (recommend
  `infrastructure.yaml`, since that is where the `InformationScorer` contract entry already
  lives) is consistent with existing placement, rather than creating a third file.

## Prior Work

- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/investigation.md` (§ "INFORMATION
  Pillar", lines 67-78, and § "INFORMATION (c3 ...)", lines 104-105) is the direct ancestor
  of this ticket. It correctly identified root cause (c3) as "dual gate: flag OFF AND no data
  pathway to produce responses" and explicitly flagged: *"Even if it ran, `state.pending_information_responses`
  is populated only by the information sub-system response cycle, which itself requires
  either the adventure routing pipeline (OFF) or explicit pending_responses injection."* This
  investigation confirms and sharpens that finding: the "information sub-system response
  cycle" referenced there does not exist as a wired code path at all (Branch A is dead;
  Branch B is also dead via the separate `ENABLE_SELF_MODEL_COGNITION` gate's `events=[]`
  bug). SOCIAL-ZERO's investigation flagged this as a *deferred* follow-up — this ticket
  (INFORMATION) is that follow-up, but its Scope section, as literally written, only
  addresses the two gates SOCIAL-ZERO named in the root-cause table, not the "no data pathway"
  caveat SOCIAL-ZERO's own prose already warned about.
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` (investigation.md, plan.md,
  test_plan.md) — sibling ticket, same batch, completed 2026-07-03. Confirmed exact template
  match for the "compiler never constructs the field at all" bug class (`factions=` was
  missing from `AuthoritativeState(...)` before that fix; `information_source_profiles=` is
  missing now, unfixed). The FACTION plan's Step 1-4 pattern (schema field on `FactionSpec` +
  `WorldCompositionSpec`/`NormalizedWorldComposition` mirror + compiler seeding + resolver
  override application + composition-level `world.yaml` content, never module YAML or global
  catalog) is the directly reusable template for this ticket's schema/compiler/resolver
  plumbing — with the caveat above that there is no existing information-source catalog to
  collide with, so the module-vs-composition fork must be independently verified rather than
  copied blindly.
- `docs/systems/faction_contract.md` exists as the FACTION-pillar system contract doc; no
  analogous `docs/systems/information_contract.md` or `belief_contract.md` exists. If the plan
  phase decides to formalize the new compile-time seeding contract (as FACTION's
  `FAC-012`/`faction_contract.md` did), there is no existing INFORMATION-pillar system contract
  doc to extend — this would need to be net-new or the parity ledger entry alone may suffice
  (matching the ticket's own Scope, which does not ask for a new contract doc).

## Risks and Open Questions

1. **[BLOCKING] The ticket's stated fix (seed `information_source_profiles` + flip
   `ENABLE_BELIEF_ASSIMILATION`) is necessary but not sufficient to satisfy AC-3** ("At least
   one of `belief_assimilated` or `lead_certainty_updated` has `calibration_hits > 0`").
   `InformationBeliefPhase.apply()` has zero reachable trigger conditions in the current
   engine (both `pending_information_responses` and `self_model.knowledge.unknowns` are
   permanently empty in every calibration run, for reasons independent of this ticket's two
   named gates). Without additional plumbing beyond Scope items 1-4, seeding profiles and
   flipping the flag will compile cleanly and pass `make evaluate --dry-run` with **zero**
   INFORMATION-pillar events — the same C grade, just with the flag now ON and unused. This
   is a genuine scope gap that needs a human/DA decision: either (a) expand scope to also wire
   a minimal reachable trigger (e.g. seed at least one entity with a non-empty
   `self_model.knowledge.unknowns` at compile time, mirroring how FACTION seeded
   `tension_level` directly into durable state — this is the most surgical option since it
   reuses Branch B without touching the two separately-gated dead systems), or (b) accept that
   `paid_information_transaction` (reachable via `PaidInformationTransactionSystem`, which
   already runs unconditionally) is the realistic near-term target and request an AC wording
   change, since that path still requires wiring `InformationNeedDetector` into the pipeline
   (currently orphaned) plus seeding `state.information_providers` (a different field from
   `information_source_profiles`). **This must be surfaced to the ticket owner/DA before
   implementation planning proceeds** — it is not resolvable by "follow existing patterns"
   per the Clarification Rule (conflicts with existing system: the phase the ticket assumes
   "already exists" and works is functionally inert).
2. **UQ-1 fork not yet resolved with evidence** (composition-level field on `world.yaml` vs.
   module-level field on `frontier_village_core.yaml`/`trading_company_hub.yaml`/etc.): unlike
   FACTION, there is no global information-source catalog for a module-level declaration to
   collide with, so a module-level field *might* be safe here — but this must be verified
   during planning (e.g. does `hero_adventurers` or `trading_company_hub` module already
   reference the `traveling_merchant` entity the ticket wants Profile 2 tied to? If so, a
   module-level declaration co-located with that entity's definition may be more coherent than
   a composition-level list of profiles referencing an entity ID sourced from another module).
3. **Ticket's Scope item 3 literal `knowledge_scopes` values are wrong** per the UQ-2 finding
   above — Profile 1's scopes must be corrected to the router's actual vocabulary
   (`"common_resource_sources"`, `"regional_danger"`) or it will never be selected as a
   candidate for any query, silently defeating the ticket's intent for that profile.
4. Confirm whether `traveling_merchant_rumors`' `source_id` should be the literal string
   `"traveling_merchant_rumors"` (as the ticket specifies) or the actual entity ID of the
   `traveling_merchant` NPC — `InformationQueryRouter.route()` (`router.py:66-72`) looks up
   `state.entities.get(prof.source_id)` to compute a real proximity `dist_cost`; if
   `source_id` is a non-entity string, `source_entity` is `None` and `dist_cost` silently
   stays `0.0` (no proximity penalty ever applied, effectively free travel). This may be
   intentional given the ticket's "tied to the existing `traveling_merchant` entity" prose,
   but the literal string value given in Scope item 3 does not achieve that tie unless it is
   replaced with the entity's actual numeric/string ID as assigned by the compiler. Needs
   plan-phase confirmation of what ID `traveling_merchant` actually resolves to in
   `urban_political`'s compiled entity roster.

## Anti-Drift Hazards

- Do **not** copy the FACTION ticket's catalog-merge-avoidance logic verbatim without
  verification — FACTION's hazard (module YAML edits being silently discarded in favor of a
  global catalog) applies specifically because a `factions.yaml` catalog exists; no equivalent
  `information_sources.yaml` catalog was found, so the same conclusion cannot be assumed here
  without checking `src/worldassembly/resolver.py`'s module-contribution merge logic for
  whatever field name is chosen.
- Do **not** implement Branch A/Branch B wiring fixes (Risk 1 above) as an unscoped drive-by —
  this is explicitly flagged as needing a human decision on scope expansion before
  implementation, not a "fix it anyway" default.
- Do **not** conflate `state.information_providers` (Epic 4.2B, `InformationProviderState`,
  `state.py:1150`, consumed by `PaidInformationTransactionSystem`) with
  `state.information_source_profiles` (this ticket's target,
  `InformationSourceProfile`/`InformationSourceKind`, `state.py:1145`, consumed by
  `InformationBeliefPhase`/`InformationQueryRouter`) — they are two separate durable
  registries feeding two separate, independently-gated systems. Seeding one does not seed
  the other.
- Do **not** hand-edit `data/worlds/urban_political/resolved/world.resolved.yaml` or any
  other file under `resolved/` — always regenerate via
  `python -m src.worldbuilding.cli resolve urban_political`, per the FACTION plan's
  established precedent.
- Do **not** widen this ticket into "wire the full belief-assimilation response cycle" beyond
  what's needed to produce `calibration_hits > 0` — the ticket's Out of Scope explicitly
  excludes "a full information marketplace or NPC query-response loop." Risk 1's minimal
  option (seed one entity's `unknowns` at compile time to reach Branch B) stays inside that
  boundary; wiring `InformationNeedDetector` + `SelfModelUpdatePhase`'s `events=[]` bug fix +
  `PaidInformationTransactionSystem`'s provider registry does not.
- `router.py`'s `matches_scope()` hard-coded vocabulary and the `traveler`-bypass (`router.py:57`)
  are existing, unrelated-to-this-ticket logic — do not "fix" the router's scope-matching
  design as part of this ticket; only correct the ticket's own profile content to match the
  router's existing (if awkwardly named) vocabulary.
