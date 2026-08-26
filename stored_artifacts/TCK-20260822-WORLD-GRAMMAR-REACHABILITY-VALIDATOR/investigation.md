---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR
artifact_type: investigation
tags: [world, content]
---

# Investigation — TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR

> **Note on Context Scan**: `mcp__knowledge-search__search_docs` returned `{"error": "index not
> found"}` and the `python3 tools/knowledge_search.py query ...` fallback returned `knowledge index
> not found — run make knowledge-index`. `graphify query` failed (`graph file not found` — no
> `graphify-out/graph.json` in this worktree; the main checkout's `graphify-out/GRAPH_REPORT.md` was
> read instead for community structure, per the fallback instruction). This matches the ticket's own
> "Assumptions / Open Questions" note that semantic search was unavailable during the source
> investigation too — it remains unavailable now. All findings below come from direct source/doc/data
> reads and `docs/REGISTRY.yaml` querying. Re-run semantic search once the index is rebuilt
> (`make knowledge-index`) to confirm nothing was missed.

## Current Behavior

**`WorldValidator` rule engine** (`src/worldbuilding/validator.py`):
- `ValidationIssue` (lines 20-27): frozen Pydantic model with exactly `rule_id`, `severity`,
  `message`, `path`. **No `source_entity` or `source_file` field exists today.**
- `WorldValidationRule` base class (29-52): `applicable_contexts` (a `set[ValidationContext]`,
  default excludes `MODULE`), `severity_overrides: dict[ValidationContext, str]`, `is_applicable()`,
  `get_severity()`, `validate(spec, context)`.
- 8 concrete rules registered by default in `WorldValidator.__init__` (339-351):
  `FactionExistenceRule`, `SpawnRegionExistenceRule`, `ResourceRegionExistenceRule`,
  `BuildingRegionExistenceRule`, `RegionBoundsWithinTopologyRule`, `NoResourcesWarningRule`,
  `HighEntityDensityWarningRule`, `BudgetGuardrailRule(profile=profile)`. Every one of these
  compares fields that live entirely inside `WorldSpec` itself (region ids, faction ids, bounds,
  counts) — **none of them touch the content catalog** (`CatalogRepository`). `BudgetGuardrailRule`
  is the only rule taking constructor args (`profile: str`), the established pattern for
  parameterizing a rule.
- `WorldValidator.validate(spec, raw_data, strict, context)` (355-391): runs applicable rules, adds
  an "unexpected top-level section" check, raises `InvalidWorldSpecError` on any ERROR (or on
  WARNING under `strict=True`), else returns issues sorted by `(severity, rule_id, path)`.
- `WorldValidator()` is constructed with **zero catalog/context argument** at every real call site
  found: `src/worldbuilding/cli.py:101,262`, `src/worldgeneration/generator.py:307`,
  `src/worldassembly/resolver.py:89` (used for both `ValidationContext.MODULE` at 118 and
  `ValidationContext.WORLD` at 136), `src/lab/orchestrator.py:88`, `src/lab/mutation.py:178`,
  `src/lab/mutation_orchestrator.py:93`, `src/lab/cli.py:113`. **The rule engine as it stands is
  catalog-blind.**

**Module-level validation has no quest data to check.** `WorldAssemblyValidator.validate()`
(`src/worldassembly/resolver.py:76-140`) builds a `dummy_spec` per module (95-117) for
`ValidationContext.MODULE` that populates `regions`/`factions`/`entities`/`resources`/`buildings`
but **never sets `quest_definitions`** — it defaults to `[]`. Quest definitions only exist in the
final composed `world_spec` validated at `ValidationContext.WORLD` (136). A reachability rule
registered for `MODULE` context would be a functional no-op there.

**`WorldCompiler.compile()` step 7** (`src/worldbuilding/compiler.py:464-519`):
- Builds `tag_pool` (467-477) from `RegionSpec.type` + `RegionSpec.tags` across `spec.regions`.
- Checks `required_location_tags` against `tag_pool`, appending a plain warning string (not a
  `ValidationIssue`) to the compile report's `warnings` list if unmatched (484-490) — WARNING-only,
  confirmed.
- `required_participant_tags` is read at line 505 and copied verbatim into
  `QuestState.metadata["required_participant_tags"]` with **zero verification against any
  entity/population/archetype data** — this is the exact gap the ticket targets.
- `compiled_quests` (465, appended at 519) is used **only** for the `quest_count` metric in the
  compile report (627). The `AuthoritativeState` constructor (594-610) never receives
  `compiled_quests` — confirmed by direct read, it is not one of the constructor's kwargs. This
  re-confirms `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s own finding
  ("`compiler.py`'s `compiled_quests` confirmed independently dead — computed only for a
  `quest_count` metric, never attached to any entity") still holds today.

**Schema** (`src/worldbuilding/schema.py`):
- `QuestDefinition` (195-219): `required_participant_tags: List[str]` (default `[]`),
  `required_location_tags`, `source_module: Optional[str]` ("Set by assembly resolver at
  composition time; not authored directly").
- `PopulationSpec` (151-162): `role: str`, `faction: str`, `spawn_region: str`, and
  `archetype_id: Optional[str] = None` ("set at assembly time, never inferred from the id string").
- `source_module` is genuinely populated: `src/worldassembly/resolver.py:897-899` stamps
  `qd.model_copy(update={"source_module": normalized_module.module_id})` during composition — so
  "source_file mapped to the authoring module" (per AC) resolves to a **module_id string**, not a
  literal YAML path. Hand-built `WorldSpec` fixtures (as in existing unit tests) will have
  `source_module=None`.
- `archetype_id` is genuinely populated too, but **only on the real assembly path**:
  `src/worldassembly/resolver.py:839-881` (`PopulationRecipeResolver.resolve()` expansion) sets
  `archetype_id=resolved_arch.archetype_id` on every expanded `PopulationSpec`. Raw
  `data/content/world_modules/*.yaml` files reference `populations: ["<recipe_id>"]`
  (a `PopulationRecipeDefinition`), not literal `role`/`archetype_id` — confirmed zero
  `archetype_id:` occurrences across all 20 world-module YAML files (expected: it's assembly-time
  derived, not authored). Hand-built `WorldSpec`/`PopulationSpec` test fixtures (e.g.
  `test_world_validator.py`'s `create_valid_base_spec()`) have `archetype_id=None`.

**Content catalog data** (`src/content/schema.py`, `data/content/`):
- `EntityArchetypeDefinition` (content/schema.py:206-218) inherits `CatalogBaseDefinition.tags:
  List[str]` (default `[]`) — a real, usable field structurally, but **`data/content/entities/
  entity_archetypes.yaml` never populates it**: confirmed via `grep -c "^  tags:"` → `0` across all
  24 archetypes.
- `RoleDefinition` (content/schema.py:169-184) has `role_family: str` and `compatible_traits:
  List[str]`. `data/content/social/roles.yaml` (24 roles) shows `role_family` values that are
  fine-grained and don't match authored quest tags at all (e.g. `"attacker"`, `"ecological_predator"`,
  `"recon"`, `"authority"`) — no `role_family` value equals a `required_participant_tags` value used
  anywhere in the real corpus. `compatible_traits` vocabulary across all 24 roles: `humanoid,
  tool_user, carnivore, pack_hunter, leader, undead, large_body, spiritual, merchant_minded,
  craftsman, magic_sensitive`.
- Real `required_participant_tags` value-sets across all 20 world modules (grepped and
  deduplicated): `["humanoid"]`, `["humanoid","merchant_minded"]`, `["humanoid","opportunistic"]`,
  `["humanoid","magic_sensitive"]`, `["spiritual"]`, `["undead"]`, `["beast"]`, `[]`. **5 of these 6
  non-empty tag values are covered by `compatible_traits`** (`humanoid`, `merchant_minded`,
  `magic_sensitive`, `spiritual`, `undead`) but **`opportunistic` and `beast` appear in NEITHER
  `compatible_traits` NOR `role_family` NOR any populated `tags` field anywhere in the catalog.**
  `opportunistic` is used in `bandit_road_trade_pressure.yaml`, `goblin_camp_conflict.yaml`, and
  `scalable_bandit_camp.yaml` (6 quest defs total); `beast` is used in `wolf_den_near_forest.yaml`
  (2 quest defs). These quests clearly intend to reference real goblin/bandit/wolf archetypes that
  do exist in the corpus (`goblin_raider`, `bandit_scout`, `hungry_wolf`, `alpha_wolf`) — so
  **whichever matching field is chosen, this reachability check will flag real, semantically
  fine content as unreachable on first run**, unless the design decision also accounts for this
  vocabulary gap.
- `RoleSemanticsService` (`src/content_semantics/role.py`) exposes `get_role_family`,
  `is_combatant`, `is_civilian`, `is_worker` — but **no method wraps `compatible_traits`**; a caller
  would have to reach into `repo.get_role(role_id).compatible_traits` directly, bypassing the
  service's existing encapsulation pattern.
- `CatalogRepository.get_entity_archetype(def_id)` / `.get_role(def_id)`
  (`src/content/repository.py:465-468`) are the real accessor methods that would be needed to
  resolve `archetype_id` → `EntityArchetypeDefinition.role` → `RoleDefinition.compatible_traits`.

**Directly relevant, already-fixed precedent for the catalog-access gap**:
`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION` (DONE) found that `WorldCompiler.compile()`
itself "has no catalog access of its own" and can only resolve role/faction correctly via an
externally-injected `CompileContext` (`src/worldassembly/context.py`) — 4 of 6 real callers
silently omitted it. The fix centralized loading via
`WorldRepository.load_world_with_context()`. **However, `CompileContext` itself
(`entities`/`buildings`/`resources`/`factions`/`region_ownership`/`legacy_factions`/`legacy_roles`)
does not carry raw `compatible_traits`/tag vocabulary either** — it was purpose-built for legacy
enum resolution and per-population stat overrides, not semantic tag matching. Reusing it as-is
would not solve this ticket's problem; it would need its own extension, same as a fresh
`CatalogRepository` injection would.

## Mechanics / Engine Constraints

- `docs/mechanics/06_worldbuilding_foundation.md` §7 ("Integrity Validation Laws & Severity Gates"):
  the 3-level gate diagram (Pydantic → Structural/Spatial-Link → Runtime-Gated Compiler); ERROR
  aborts compilation, WARNING logs only; "Gating Profiles: Production compilation profiles elevate
  warnings to errors, whereas development/procedural-testing profiles operate under relaxed warning
  tolerance." The new rule must honor this via `get_severity(context)`/`severity_overrides`, the
  same mechanism `BudgetGuardrailRule` already uses for its own per-metric severity overrides —
  matches AC's "at minimum WARNING severity (elevated to ERROR only when the compiler profile
  requires it)".
- §9 (Content Catalog Database Structure): establishes `data/content/social/` (Layer 3) and
  `data/content/entities/` (Layer 4) as the authoritative catalog sources — any new catalog-aware
  rule must read from these, not invent a parallel vocabulary.
- `docs/plans/idea_world_grammar_semantic_constraints.md`'s proposed `WorldGrammarReport` /
  `GrammarViolation` schema (`rule_id`, `severity`, `message`, `source_file`, `source_entity`,
  `summary`) is the acceptance-criteria-cited target shape. Current `ValidationIssue` has no
  `source_entity`/`source_file` — a schema gap, see Risks.

## Docs Requiring Update

- `docs/mechanics/06_worldbuilding_foundation.md`: §7's integrity-validation-laws section describes
  the full gate model; adding a new semantic reachability rule class to the pipeline is a real
  addition to "what the pipeline checks" and must be reflected there per the Authoritative Mechanics
  Rule (logic changes require doc parity in the same session).
- `docs/parity_ledger/substrate.yaml`: no existing entry tracks any of `WorldValidator`'s 8 rules or
  this new one (confirmed — grepped all `docs/parity_ledger/*.yaml` for `WorldValidator`/`WORLD-REF`/
  `WORLD-WARN`/`WORLD-BUDGET`/`WORLD-TOPO`: zero hits anywhere). `substrate.yaml` ("World generation,
  authoritative objects, determinism") is the closest-matching subsystem file and already carries
  the directly-related `SUB-384` entry (the `CompileContext`/catalog-access fix from
  `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`) — a new `SUB-xxx` entry for this
  reachability rule belongs alongside it.

The `docs/plans/idea_world_grammar_semantic_constraints.md` idea doc does not need its own content
changed by this ticket: the ticket's own Out-of-Scope explicitly excludes "Promoting
`docs/plans/idea_world_grammar_semantic_constraints.md`'s maturity/authority frontmatter beyond
citing it as a related doc."

`docs/mechanics/content_usage_matrix.md` was checked directly (`grep -n "required_participant_tags\|
reachab\|quest"`) and contains zero matches — it documents content *resolution* rules unrelated to
this validation-layer addition, so it is not required to change.

`docs/content/content_semantics_contract.md` (which documents `RoleSemanticsService`) is a
**contingent, not-yet-required** doc: it would need updating only if the Plan phase's resolved
matching-field decision adds a new method to `RoleSemanticsService` (e.g. a `compatible_traits`
wrapper) — precedent exists for this exact doc being touched when a `content_semantics` service's
calling contract changed (`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION` added "a real
structural caveat" to it). Since the matching-field decision is explicitly open (see Risks), this
doc is not listed as a required bullet now — Plan must re-evaluate once that decision is made.

`docs/simulation/quest_contract.md` is not required: it documents the separate, legacy
`QuestGenerator`/`QuestTemplate` system (`src/quests/generator.py`), not
`WorldSpec.QuestDefinition`/`WorldCompiler.compile()`'s quest pipeline this ticket touches.

## Parity Ledger Overlap

- **No existing parity ledger entry anywhere tracks `WorldValidator`'s rule engine at all** —
  confirmed by grepping every `docs/parity_ledger/*.yaml` for `WorldValidator`, `WORLD-REF-*`,
  `WORLD-WARN-*`, `WORLD-BUDGET-*`, `WORLD-TOPO-*`: zero matches. This ticket will be creating the
  **first** parity-ledger tracking for this rule engine, not updating one.
- `docs/parity_ledger/substrate.yaml` `SUB-384`: the `CompileContext`/catalog-access fix
  (`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`) — most relevant existing entry; the new
  entry should live in the same file.
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-248`: `GuildVisitPhase` wiring
  (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`) — **not** reachability-related; this is exactly the
  entry the ticket's own AC6 correction concerns (wrong prior-work citation), not something this
  ticket's own change touches.
- `docs/parity_ledger/progression.yaml` `PROG-119`/`PROG-120`: `QuestGenerator`/`QuestTemplate`
  target_kind population (`TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP`) — a **different subsystem**
  (see Risks item 6); informs the general failure class but is not literal overlap.
- No P0 parity entries are touched by this ticket's scope.

## Prior Work

- **`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`** (DONE, `SUB-384`): established that
  `WorldCompiler.compile()` (the sibling stage to the validator this ticket extends) has no catalog
  access of its own, and that the fix pattern used (`CompileContext` injection via
  `WorldRepository.load_world_with_context()`) still doesn't carry the tag/trait vocabulary this
  ticket needs — directly informs, but does not solve, this ticket's central open design question
  (see Risks item 2).
- **`TCK-20260630-WORLD-QUEST-LOCATION`**: "Fix quest `required_location_tags` matching against
  region *type* instead of region *id*" — the direct historical precedent for the sibling
  `required_location_tags` check already live in `compiler.py`; establishes the working convention
  (match against a semantic vocabulary field, not a raw identifier) that this ticket's
  `required_participant_tags` check should mirror for the role/archetype side.
- **`TCK-20260614-WORLDMOD-QUEST-SCHEMA`** / **`TCK-20260614-WORLDMOD-QUEST-MOD`**: foundational
  tickets that introduced `QuestDefinition` as a world-level authoring schema and its module
  contribution/merge behavior — the schema this ticket extends with a new validation rule, unchanged
  since.
- **`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`** (DONE): its own Implementation Notes independently
  confirm `compiler.py`'s `compiled_quests` path is dead code (quest_count metric only) — re-verified
  directly in this investigation, still true.
- **`TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION`** (downstream, blocked on this ticket): its
  own investigation explicitly states "the API must be scoped explicitly, not just a CLI/report
  output" and that it will apply the reachability rule engine "against `AuthoritativeState` rather
  than `WorldSpec`." This means the tag-matching predicate built here should be structured as a
  reusable, spec-shape-agnostic unit (e.g. a pure function over resolved tag sets), not hardcoded
  entirely inside a `WorldValidationRule.validate(WorldSpec, context)` method body — otherwise the
  downstream ticket cannot reuse it as designed.

## Risks and Open Questions

1. **[BLOCKS IMPLEMENTATION] Matching-field decision has no clean answer with current data.**
   `EntityArchetypeDefinition.tags` is real but 0% populated in the corpus.  `RoleDefinition.
   role_family` values don't match any authored `required_participant_tags` value.
   `RoleDefinition.compatible_traits` covers 5 of 6 real tag-sets (`humanoid`, `merchant_minded`,
   `magic_sensitive`, `spiritual`, `undead`) but not `opportunistic` (6 quest defs across 3 modules)
   or `beast` (2 quest defs in 1 module). Whichever field Plan selects, the corpus regression run
   (AC4) will produce real, non-empty violations for those `opportunistic`/`beast` quests on first
   run — this must be documented as an expected baseline, not "fixed" by loosening the check or by
   backfilling catalog content (explicitly Out of Scope).
2. **[ARCHITECTURAL] The rule engine is catalog-blind and the sibling `CompileContext` mechanism
   doesn't carry the needed vocabulary either.** `WorldValidationRule.validate(spec, context)` has
   no `CatalogRepository`/`CompileContext` parameter. Every real `WorldValidator()` call site
   (7 distinct files) constructs it with zero catalog wiring today. Whatever DI mechanism Plan
   chooses (constructor-injected repo like `BudgetGuardrailRule`'s `profile` param, an extended
   `CompileContext`, or a new optional `validate()` kwarg) must degrade gracefully — skip / do not
   crash — when no catalog is available, mirroring `get_role_enum()`/`get_faction_enum()`'s existing
   `catalog_repo=None` fallback pattern in `compiler.py`.
3. **`ValidationIssue` has no `source_entity`/`source_file` fields; AC49 requires both.** Adding them
   as new optional fields is additive/backward-compatible (frozen Pydantic model, `Optional[str] =
   None`), but confirm no consumer treats `ValidationIssue`'s field set as closed (checked
   `test_world_validator.py` and the dict-comprehension serializers in `worldassembly/resolver.py`
   lines 82, 120, 138 — all use explicit field access, not `model_dump()` diffing, so this is
   low-risk but should be re-checked at Plan/Implement).
4. **Hand-authored `WorldSpec`/`PopulationSpec` fixtures have `archetype_id=None`.** Reachability is
   only decidable for assembly-composed populations that carry a real `archetype_id`. The rule must
   define explicit behavior for `archetype_id=None` populations (exclude from the "available tags"
   pool? treat as an unknown/no-signal population rather than silently widening or narrowing
   coverage?) — unresolved, must be an explicit Plan decision, not an assumption.
5. **Sequencing constraint from the downstream ticket**: `TCK-20260822-QUEST-OPPORTUNITY-
   PREEMIT-VALIDATION` needs a runtime-callable, `AuthoritativeState`-reusable rule API, not just a
   `WorldSpec`-bound validator method. The internal tag-matching logic should be extracted into a
   reusable unit from the start.
6. **[FACTUAL PRECISION on AC6] `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP` is a different
   subsystem, not a literal catch.** That ticket's `q_slime_cull` gap lives entirely in
   `src/quests/generator.py`'s `QuestTemplate.target_kind`/`entity.kind` (== `race_id`) matching — a
   fully separate legacy quest-generation pipeline from `WorldSpec.QuestDefinition.
   required_participant_tags`/`WorldCompiler.compile()` (which this ticket's validator operates on).
   It is a valid precedent for the *general failure class* ("a quest references content that doesn't
   exist, discovered only via expensive live runs") but this new validator would **not** have
   mechanically caught that specific bug, since it never touches `QuestTemplate` or `race_id`
   matching. The ticket documentation correcting the record (Scope bullet 6 / AC6) should state this
   precisely — "on-point precedent for the failure class" rather than "would have caught this bug" —
   to avoid a second incorrect-precedent claim replacing the first one.
7. **`compiled_quests` remains fully dead code today** (re-confirmed, see Current Behavior) — this
   validator's target content (`QuestDefinition`/`compiled_quests`) has no live runtime consumer at
   all yet. This doesn't block the ticket (its value is catching authoring errors before any future
   wiring makes them matter) but should be disclosed so the baseline isn't mistaken for "these quests
   are live and broken" — they're not live at all yet.

## Anti-Drift Hazards

- Do not backfill `EntityArchetypeDefinition.tags` (or any catalog field) across the corpus to make a
  naive match "work" — explicitly Out of Scope.
- Do not tune the matching field until the 20+-module regression baseline shows zero violations —
  AC4 explicitly expects (and permits) a documented non-empty violation list; a suspiciously clean
  first-run result is a signal the check isn't actually checking anything real.
- Do not register the new rule for `ValidationContext.MODULE` — `dummy_spec` there never populates
  `quest_definitions`; doing so is a no-op that looks like coverage but isn't.
- Do not conflate this ticket's build-time/`WorldSpec` validator with the separate runtime/
  `AuthoritativeState` pre-emit check — that is `TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION`'s
  explicit scope. Keep the matching predicate reusable for it, but do not implement its call site
  here.
- Do not restate `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP` as if this validator would have
  caught it verbatim (see Risks item 6) — correct precisely.
- Do not mutate the input `WorldSpec` — matches the existing `test_validator_does_not_modify_spec`
  pattern; any catalog resolution must be read-only.
- The existing default `WorldValidator()` rule list is depended on by `test_validator_valid_world`
  (`issues == []` for a spec with empty `quest_definitions`) and other call sites assuming today's
  8-rule set. Adding a 9th default rule must not produce any issue for empty/absent
  `quest_definitions`, or it silently breaks that test and every other unmodified caller.
- Do not fold or duplicate the sibling `required_location_tags` WARNING check already living in
  `compiler.py` (lines 484-490) — this ticket only adds the `required_participant_tags` check; the
  two remain independent mechanisms (one compiler-level plain-string warning, one validator-level
  `ValidationIssue`) unless a future ticket explicitly unifies them.
