---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR
artifact_type: plan
tags: [world, content]
---

# Implementation Plan — TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR

## Summary

Add a new `WorldValidationRule` (`ParticipantReachabilityRule`, `rule_id="WORLD-REACH-001"`) to
`src/worldbuilding/validator.py` that checks each `QuestDefinition.required_participant_tags`
against the `RoleDefinition.compatible_traits` reachable via each `WorldSpec` population's
`archetype_id -> EntityArchetypeDefinition.role -> RoleDefinition.compatible_traits` chain — the
only real vocabulary in the catalog that covers a majority (5 of 6) of the actual
`required_participant_tags` value-sets used in the corpus (`EntityArchetypeDefinition.tags` is 0%
populated; `RoleDefinition.role_family` matches none of them). The matching predicate is factored
into a new pure-function module (`src/worldbuilding/reachability.py`) so it is reusable, spec-shape
agnostic, by the downstream `TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION` ticket against
`AuthoritativeState`. Catalog access is threaded into `WorldValidator` via a new optional
constructor parameter (mirroring the existing `BudgetGuardrailRule(profile=...)` constructor-arg
pattern), defaulting to `None` everywhere except the one real call site
(`WorldAssemblyValidator.validate()` in `src/worldassembly/resolver.py`) that already holds a
`CatalogRepository` instance and validates at `ValidationContext.WORLD`. Every other real
`WorldValidator()` call site is left untouched and continues to receive `catalog_repo=None`, under
which the new rule degrades to zero issues rather than crashing. `ValidationIssue` gains two
additive optional fields (`source_entity`, `source_file`) to satisfy AC2. A corpus-wide regression
test records the real, non-empty first-run violation baseline (the known `opportunistic`/`beast`
vocabulary gap) rather than tuning the check to produce a false clean pass.

## Design Decisions Made in This Plan

1. **Matching field: `compatible_traits` via the `archetype_id -> role -> compatible_traits`
   chain**, not `EntityArchetypeDefinition.tags` (0% populated, confirmed
   `data/content/entities/entity_archetypes.yaml`, investigation) and not `role_family` (no value
   overlaps any real `required_participant_tags` value-set, investigation). `compatible_traits`
   covers `humanoid`, `merchant_minded`, `magic_sensitive`, `spiritual`, `undead` (5 of 6 real
   value-sets) — the best available real vocabulary. `opportunistic` (6 quest defs, 3 modules) and
   `beast` (2 quest defs, 1 module) are covered by neither this nor any other catalog field today;
   this is accepted as a documented, expected AC4 baseline violation, not something to work around
   by loosening the check or backfilling catalog content (both explicitly Out of Scope).
2. **DI mechanism: optional constructor parameter on `WorldValidator` and on the new rule class**,
   `catalog_repo: Optional[CatalogRepository] = None`, mirroring `BudgetGuardrailRule`'s existing
   `profile` constructor-arg pattern (`src/worldbuilding/validator.py:249-251`). This is narrower
   than extending `CompileContext` (investigation confirmed `CompileContext` doesn't carry
   trait/tag vocabulary either and would need its own extension regardless) and does not change the
   shared `WorldValidationRule.validate(spec, context)` signature that all 8 existing rules
   implement.
3. **`archetype_id=None` populations contribute no tags to the reachable pool** (excluded, not
   treated as a wildcard match). Rationale: a population with no resolved archetype carries no
   verifiable evidence of what it can satisfy; silently counting it as a match would create false
   negatives that make the check look clean without actually checking anything, which the
   investigation's own anti-drift note warns against ("a suspiciously clean first-run result is a
   signal the check isn't actually checking anything real").
4. **`applicable_contexts = {WORLD, COMPILE, EXPERIMENT}`** (excludes `MODULE` per explicit
   anti-drift instruction; also excludes `ASSEMBLY`/`GENERATED_WORLD`, which is narrower than some
   existing rules default to). Rationale: `quest_definitions` is only genuinely populated in the
   final composed `world_spec` validated at `WORLD` (investigation, confirmed via
   `src/worldassembly/resolver.py:95-117` dummy_spec construction never setting
   `quest_definitions`); mirrors `RegionBoundsWithinTopologyRule`'s narrower context set
   (`validator.py:164-168`), which similarly depends on fully-resolved spec data.
5. **No-catalog behavior: zero issues, not a crash and not a false ERROR.** Mirrors the existing
   `catalog_repo=None` fallback pattern already used for `get_role_enum()`/`get_faction_enum()` in
   `src/worldbuilding/compiler.py` (cited in investigation) — "cannot verify" is treated as
   no-signal, not as a violation.

## Steps

### Step 1 — Extend `ValidationIssue` with `source_entity`/`source_file`

**Files:** `src/worldbuilding/validator.py`

**Change:** In the `ValidationIssue` model (currently `rule_id`, `severity`, `message`, `path` —
confirmed `src/worldbuilding/validator.py:20-27`, no other fields exist), add two new fields:
`source_entity: Optional[str] = None` and `source_file: Optional[str] = None`. This is additive on
a frozen Pydantic model; investigation confirmed (re-check during implementation) that all three
real consumers that reshape `ValidationIssue` into dicts —
`src/worldassembly/resolver.py:81-84` (`catalog_report`, actually built from a different
`CatalogValidator` issue type, not `ValidationIssue` — leave untouched), `resolver.py:119-122`
(`module_reports`, explicit field access `severity/rule_id/message/path`), and
`resolver.py:137-140` (`world_report`, same explicit field access) — use explicit field access, not
`model_dump()` diffing, so adding fields is safe for all of them as written today.

**Do NOT touch:** `WorldValidationRule` base class fields/methods, any of the 8 existing rule
classes' `validate()` bodies (they simply won't set the two new fields, which default to `None` —
this is fine and matches AC constraints that don't require them).

**Verify:** `test_validation_issue_source_entity_and_source_file_round_trip` (test #8).

---

### Step 2 — Reusable tag-matching predicate + WorldSpec tag-pool resolver

**Files:** new `src/worldbuilding/reachability.py`

**Change:** Create a new module with three pure/read-only functions, deliberately decoupled from
`WorldValidationRule` so the downstream `TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION` ticket
can reuse the core predicate against `AuthoritativeState`-derived tag sets without depending on
`WorldSpec`:

- `is_reachable(required_tags: list[str], available_tags: Optional[set[str]]) -> bool` — pure
  function. Returns `True` if `required_tags` is empty (no requirement = trivially satisfied) or if
  every tag in `required_tags` is a member of `available_tags`. Returns `True` (skip / cannot
  verify, not a violation) if `available_tags is None` — this is the "no catalog available" signal
  from Step 3's caller, kept out of this pure function's own concern by taking it as an explicit
  `None` input rather than special-casing catalog access here.
- `resolve_population_tags(population: PopulationSpec, catalog_repo: Optional[CatalogRepository])
  -> set[str]` — returns `set()` if `catalog_repo is None` or `population.archetype_id is None`
  (confirmed field: `PopulationSpec.archetype_id: Optional[str] = None`,
  `src/worldbuilding/schema.py:159-162`). Otherwise: `archetype =
  catalog_repo.get_entity_archetype(population.archetype_id)` (confirmed accessor,
  `src/content/repository.py:465-466`); if `archetype is None`, return `set()`; else `role =
  catalog_repo.get_role(archetype.role)` (confirmed `EntityArchetypeDefinition.role: str`,
  `src/content/schema.py:210`, and `get_role` accessor, `repository.py:468-469`); if `role is
  None`, return `set()`; else return `set(role.compatible_traits)` (confirmed field
  `RoleDefinition.compatible_traits: List[str] = Field(default_factory=list)`,
  `src/content/schema.py:176`).
- `build_available_participant_tags(spec: WorldSpec, catalog_repo: Optional[CatalogRepository]) ->
  Optional[set[str]]` — returns `None` immediately if `catalog_repo is None` (the explicit "cannot
  verify" signal consumed by `is_reachable`). Otherwise returns the union of
  `resolve_population_tags(p, catalog_repo)` over every `p` in `spec.entities` (confirmed field:
  `WorldSpec.entities: list[PopulationSpec]`, `src/worldbuilding/schema.py:236`) — may legitimately
  be an empty set if no population resolves any traits; that is a real (non-`None`) empty pool, not
  a "cannot verify" signal, and downstream `is_reachable` will correctly flag any non-empty
  `required_tags` against it as unreachable.

**Do NOT touch:** `PopulationRecipeResolver` or any other assembly-time `archetype_id`-resolution
code — this step only reads already-resolved `archetype_id` values, it does not resolve recipes.

**Verify:** exercised indirectly by tests #1, #2, #6, #7 (Step 5); no dedicated standalone test
file for this module per test_plan (not separately enumerated there) — its correctness is proven
through the rule's own tests.

---

### Step 3 — `ParticipantReachabilityRule` class

**Files:** `src/worldbuilding/validator.py`

**Change:** Add a new `WorldValidationRule` subclass:

```python
class ParticipantReachabilityRule(WorldValidationRule):
    rule_id = "WORLD-REACH-001"
    severity = "WARNING"
    description = "Verify each quest's required_participant_tags is satisfiable by at least one reachable population archetype's compatible_traits."
    applicable_contexts = {
        ValidationContext.WORLD,
        ValidationContext.COMPILE,
        ValidationContext.EXPERIMENT,
    }

    def __init__(self, catalog_repo: Optional[CatalogRepository] = None):
        super().__init__()
        self.catalog_repo = catalog_repo

    def validate(self, spec: WorldSpec, context: ValidationContext = ValidationContext.WORLD) -> list[ValidationIssue]:
        issues = []
        sev = self.get_severity(context)
        available = build_available_participant_tags(spec, self.catalog_repo)
        for i, quest in enumerate(spec.quest_definitions):
            if not is_reachable(quest.required_participant_tags, available):
                issues.append(ValidationIssue(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"Quest '{quest.id}' required_participant_tags {quest.required_participant_tags} "
                            f"not satisfiable by any reachable population's compatible_traits.",
                    path=f"quest_definitions.{i}.required_participant_tags",
                    source_entity=quest.id,
                    source_file=quest.source_module,
                ))
        return issues
```

Import `CatalogRepository` from `src.content.repository`, `PopulationSpec`/`QuestDefinition` are
already imported transitively via `WorldSpec`'s module; import `is_reachable`,
`build_available_participant_tags` from the new `src.worldbuilding.reachability` module (Step 2).

Uses `quest.source_module` (confirmed field, `src/worldbuilding/schema.py:217-219`, "Set by
assembly resolver at composition time") directly for `source_file`, per AC's own wording that
"source_file mapped to the authoring module" resolves to the module_id string, not a literal path
— matches investigation finding exactly.

**Do NOT touch:** the sibling `required_location_tags` WARNING-only plain-string check already in
`src/worldbuilding/compiler.py:484-490` — this rule only adds the `required_participant_tags`
check as a `ValidationIssue`; the two mechanisms stay independent per the ticket's own anti-drift
guard. Do not touch `compiler.py` at all in this step.

**Verify:** tests #1 (`test_reachability_rule_flags_unmatched_participant_tags`), #2
(`test_reachability_rule_passes_when_tags_satisfiable`), #3 (severity elevation), #4 (not
applicable at MODULE), #6 (`archetype_id=None` handled gracefully), #7 (no catalog available
handled gracefully).

---

### Step 4 — Wire catalog access into `WorldValidator` and the one real WORLD-context call site

**Files:** `src/worldbuilding/validator.py`, `src/worldassembly/resolver.py`

**Change:**
- `WorldValidator.__init__` (currently `(self, rules: list[WorldValidationRule] = None, profile:
  str = "local_dev")`, `src/worldbuilding/validator.py:339`) gains a new parameter
  `catalog_repo: Optional[CatalogRepository] = None`, and the default rules list (340-351) appends
  `ParticipantReachabilityRule(catalog_repo=catalog_repo)` as a 9th default rule.
- **Every other writer/caller of `WorldValidator()` is enumerated and accounted for** (7 real call
  sites total, confirmed by investigation grep): `src/worldbuilding/cli.py:101,262`,
  `src/worldgeneration/generator.py:307`, `src/worldassembly/resolver.py:89`,
  `src/lab/orchestrator.py:88`, `src/lab/mutation.py:178`, `src/lab/mutation_orchestrator.py:93`,
  `src/lab/cli.py:113`. Six of these seven are left completely untouched — they continue
  constructing `WorldValidator()` with zero arguments, so `catalog_repo` defaults to `None`, the
  new rule's `build_available_participant_tags` short-circuits to `None`, and `is_reachable`
  returns `True` unconditionally (Step 2/3) — i.e. exactly zero new issues at these six sites,
  identical to current behavior, no crash. Only `src/worldassembly/resolver.py:89`
  (`world_validator = WorldValidator()`, inside `WorldAssemblyValidator.validate()`) is changed to
  `WorldValidator(catalog_repo=self.catalog_repo)`, reusing the `CatalogRepository` instance already
  stored on the class (`self.catalog_repo`, confirmed set in `__init__`,
  `src/worldassembly/resolver.py:73-74`) — no new `CatalogRepository` is constructed. This single
  `world_validator` instance is used for both the per-module `ValidationContext.MODULE` loop (line
  118) and the composed-world `ValidationContext.WORLD` call (line 136); wiring the catalog in is
  safe for the MODULE path because the rule's `applicable_contexts` (Step 3) excludes `MODULE`
  entirely — `is_applicable()` (`validator.py:43-45`) filters it out before `validate()` is ever
  called there, so `dummy_spec`'s permanently-empty `quest_definitions` is never touched by this
  rule.
- Update the `world_report` list comprehension (`src/worldassembly/resolver.py:137-140`, currently
  `{"severity": ..., "rule_id": ..., "message": ..., "path": ...}`) to also include
  `"source_entity": issue.source_entity, "source_file": issue.source_file` — this is the one real
  report-shaping site through which this rule's `ValidationContext.WORLD` output is surfaced to
  callers of `WorldAssemblyValidator.validate()`; without this the new fields added in Step 1 would
  be silently dropped exactly where the rule actually runs in production.

**Do NOT touch:** the `catalog_report` comprehension (`resolver.py:81-84` — sourced from
`CatalogValidator` issues, a different type with a `target_id` field, not `ValidationIssue`, and
unrelated to this rule) or the `module_reports` comprehension (`resolver.py:119-122` — MODULE
context, structurally excluded from this rule per Step 3). Do not change the `dummy_spec`
construction (`resolver.py:95-117`) to populate `quest_definitions` — that would be scope creep
into cross-module reachability, explicitly out of scope per the anti-drift hazards.

**Verify:** test #7 (no-catalog callers unaffected), plus full regression of
`tests/unit/worldassembly/`, `tests/unit/lab/`, `tests/unit/worldgeneration/`, and the
`tests/unit/worldbuilding/` tests covering `cli.py` — confirms all six untouched call sites still
pass with zero behavior change.

---

### Step 5 — Dedicated unit tests for the new rule

**Files:** new `tests/unit/worldbuilding/test_world_grammar_reachability.py`;
`tests/unit/worldbuilding/test_world_validator.py` (extend only, for test #8 and the default-rule
guard)

**Change:** Implement tests #1–#7 (from test_plan.md) in the new file, using hand-built
`WorldSpec`/`PopulationSpec`/`QuestDefinition`/`EntityArchetypeDefinition`/`RoleDefinition` fixtures
and a minimal fake or constructed `CatalogRepository` (reuse whatever fixture-construction helper
already exists for `CatalogRepository` in the test suite — check
`tests/unit/content/` or `tests/unit/worldbuilding/test_compiler.py` for an existing pattern before
hand-rolling one). Add test #8 (`ValidationIssue` field round-trip) to the existing
`test_world_validator.py`, matching test_plan's explicit location. Also add the test_plan's
"default-rule-set guard": assert the 8 pre-existing `rule_id` values (`WORLD-REF-001..004`,
`WORLD-TOPO-001`, `WORLD-WARN-001/002`, `WORLD-BUDGET-GP`) plus the new `WORLD-REACH-001` are all
present in `WorldValidator()`'s default rules list, to catch accidental removal/renaming.

**Do NOT touch:** any of the 9 existing tests in `test_world_validator.py` beyond adding test #8
and the guard — `test_validator_valid_world`'s `issues == []` assertion for a spec with empty
`quest_definitions` must keep passing unmodified (it will, since `spec.quest_definitions` is `[]`
there, so Step 3's `for i, quest in enumerate(spec.quest_definitions)` loop body never executes).

**Verify:** `pytest tests/unit/worldbuilding/ -m "not slow" -q`.

---

### Step 6 — Corpus-wide regression baseline

**Files:** new `tests/unit/worldbuilding/test_corpus_reachability_baseline.py`; new baseline
fixture file (e.g. `tests/fixtures/world_grammar_reachability_baseline.json` or an inline literal
dict in the test — implementer's choice, but it must be committed and reviewable as a diff, not
silently regenerated)

**Change:** Iterate every real composed world under `data/worlds/*/resolved/world.resolved.yaml`
(confirmed to exist and carry `quest_definitions` — investigation spot-checked
`resource_dense_basin`, `wilderness_survival`, `unit_selfmodel_pilot`). For each: load the
`WorldSpec`, obtain a real `CatalogRepository` (locate and reuse whatever existing corpus-test
catalog-loading helper already exists — e.g. check `tests/unit/worldassembly/
test_corpus_diversity.py` for its own catalog-loading fixture/helper first; do not hand-roll a
second one), construct `WorldValidator(catalog_repo=repo)`, call
`.validate(spec, context=ValidationContext.WORLD)`, filter results to `rule_id ==
"WORLD-REACH-001"`, and assert the resulting `(world_id, quest_id)` violation set matches a
committed baseline exactly. Given the confirmed vocabulary gap, the baseline is expected to be
**non-empty**: at minimum the quests using `opportunistic`
(`bandit_road_trade_pressure.yaml`, `goblin_camp_conflict.yaml`, `scalable_bandit_camp.yaml` — 6
quest defs) and `beast` (`wolf_den_near_forest.yaml` — 2 quest defs) should appear as violations,
per investigation's corpus grep. Record the exact baseline as produced by the first real run against
the actual code (do not hand-guess the exact violation list before running it) and commit it.

**Do NOT touch:** `tests/unit/worldassembly/test_corpus_diversity.py` itself (keep this regression
isolated in its own file so a reachability-baseline failure is never conflated with unrelated
corpus-diversity assertions), `data/worlds/*/resolved/*.yaml` content, or
`data/content/entities/entity_archetypes.yaml` (no backfilling tags — explicitly Out of Scope).

**Verify:** test #9 (`test_full_corpus_reachability_regression`); this is the concrete
implementation of AC4.

---

### Step 7 — Docs and parity ledger

**Files:** `docs/mechanics/06_worldbuilding_foundation.md`, `docs/parity_ledger/substrate.yaml`

**Change:**
- In `docs/mechanics/06_worldbuilding_foundation.md` §7 ("Integrity Validation Laws & Severity
  Gates"), add a short addition describing the new `WORLD-REACH-001` reachability rule: what it
  checks (`required_participant_tags` against reachable populations' `compatible_traits` via
  `archetype_id -> role`), that it runs at `ValidationContext.WORLD` between structural
  `WorldValidator.validate()` and `WorldCompiler.compile()`, its default WARNING severity per the
  existing gating-profile mechanism, and the known `opportunistic`/`beast` vocabulary-coverage gap
  as a stated, accepted limitation (not a bug to silently work around).
- In `docs/parity_ledger/substrate.yaml`, add a new `SUB-xxx` entry (next available id after the
  existing `SUB-384`) alongside it: `text` describing the reachability rule, `status: verified`,
  `v2_evidence` pointing at `src/worldbuilding/validator.py`'s `ParticipantReachabilityRule` and
  `src/worldbuilding/reachability.py`, `test_path` pointing at Step 6's corpus regression test, and
  a `divergence_note` (or equivalent per `schema.json`) capturing the `opportunistic`/`beast`
  coverage gap so it's traceable as an accepted, documented limitation rather than silently absent.

**Do NOT touch:** `docs/plans/idea_world_grammar_semantic_constraints.md`'s maturity/authority
frontmatter (explicitly Out of Scope — cite it as a related doc only), `docs/mechanics/
content_usage_matrix.md` (confirmed unrelated), `docs/simulation/quest_contract.md` (confirmed a
different, legacy subsystem), `docs/parity_ledger/strategic_cognition.yaml` `STRAT-248` or
`docs/parity_ledger/progression.yaml` `PROG-119`/`PROG-120` (neither is this ticket's subsystem;
see Step 8's correction instead).

**Verify:** no automated test; checked by `done-checker`'s frontmatter/parity-ledger DoD conditions
and by re-reading §7 for consistency with the shipped rule.

---

### Step 8 — Ticket record correction (AC6)

**Files:** `tickets/inprogress/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR.md`
(`## Implementation Notes` section)

**Change:** Add prose stating precisely: `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` is **not**
evidence for this rule class — its root cause was decision-pipeline wiring (no `GoalKind`/scorer/
phase routed to `GuildAction.visit()`), not a content-reachability mismatch, and this validator
would not have caught it. `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP` is a genuine but
**general-failure-class** precedent, not a literal catch: its `q_slime_cull` bug lives entirely in
`src/quests/generator.py`'s `QuestTemplate.target_kind`/`race_id` matching, a fully separate legacy
quest-generation pipeline from `WorldSpec.QuestDefinition.required_participant_tags`/
`WorldCompiler.compile()` — this validator never touches `QuestTemplate` or `race_id` matching, so
it would not have mechanically caught that specific bug.

**Do NOT touch:** any other ticket's own files (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING.md`,
`TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP.md`) — the correction lives only in this ticket's own
Implementation Notes, per AC6's own wording ("Ticket documentation explicitly corrects the
record").

**Verify:** manual review against AC6; no test.

## Scope Guards

- Do not populate `EntityArchetypeDefinition.tags` (or any other catalog content field) across
  `data/content/entities/entity_archetypes.yaml` or any other content file to make the check
  produce fewer/zero violations — explicitly Out of Scope.
- Do not register `ParticipantReachabilityRule` for `ValidationContext.MODULE` — structurally a
  no-op there and explicitly forbidden by the anti-drift hazards.
- Do not implement, call, or stub the runtime/`AuthoritativeState` pre-emit check —
  that is `TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION`'s scope, which is blocked on this
  ticket landing first. Keep `src/worldbuilding/reachability.py`'s functions reusable for it, but
  do not add a call site for it here.
- Do not fold, duplicate, or alter the sibling `required_location_tags` WARNING-only plain-string
  check in `src/worldbuilding/compiler.py:484-490` — it remains an independent mechanism.
- Do not touch `compiled_quests` (`src/worldbuilding/compiler.py`) or wire it into
  `AuthoritativeState` — it remains intentionally dead code; that is
  `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s territory, not this ticket's.
- Do not promote `docs/plans/idea_world_grammar_semantic_constraints.md`'s maturity/authority
  frontmatter.
- Do not touch `docs/parity_ledger/strategic_cognition.yaml` `STRAT-248` or
  `docs/parity_ledger/progression.yaml` `PROG-119`/`PROG-120` — the correction in Step 8 is prose
  in this ticket's own file, not an edit to those entries.
- Do not modify any of the other 6 real `WorldValidator()` call sites
  (`src/worldbuilding/cli.py:101,262`, `src/worldgeneration/generator.py:307`,
  `src/lab/orchestrator.py:88`, `src/lab/mutation.py:178`,
  `src/lab/mutation_orchestrator.py:93`, `src/lab/cli.py:113`) beyond what automatically follows
  from `WorldValidator.__init__`'s new optional, defaulted parameter — they must continue
  constructing `WorldValidator()` exactly as today.
- Do not touch the `catalog_report`/`module_reports` dict comprehensions in
  `src/worldassembly/resolver.py` (lines 81-84, 119-122) — only `world_report` (137-140) is in
  scope.

## Dependency Map

- Step 1 (schema) — independent.
- Step 2 (pure functions) — independent.
- Step 3 (rule class) — depends on Step 1 (needs `source_entity`/`source_file` fields) and Step 2
  (needs `is_reachable`/`build_available_participant_tags`).
- Step 4 (DI wiring + resolver.py call site) — depends on Step 3 (rule class must exist to add to
  the default list).
- Step 5 (dedicated unit tests) — depends on Steps 1–4 all landing (exercises the fully wired
  rule).
- Step 6 (corpus regression) — depends on Step 4 (needs real catalog wiring to be meaningful); can
  be scaffolded in parallel with Step 5 but only produces a meaningful baseline once Step 4 lands.
- Step 7 (docs/parity) — depends on Steps 3–6 being final (needs the real rule_id, file paths, and
  test path to cite).
- Step 8 (ticket correction) — independent, no code dependency; can be done at any point.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: matching-field design decision explicitly documented | Design Decisions section (this plan) + Step 3 docstring/comment | Manual review; no test |
| AC2: `ValidationIssue`/`WorldGrammarReport` with reachability rule_id, `source_entity`=quest id, `source_file`=module, ≥WARNING severity | Steps 1, 3, 4 | tests #1, #3, #8 |
| AC3: zero violations when every quest's tags are satisfiable | Step 3 | test #2 |
| AC4: full 20+-module corpus regression, documented baseline | Step 6 | test #9 |
| AC5: runs between `WorldValidator.validate()` and `WorldCompiler.compile()`, no spec mutation, no raise on WARNING-only | Steps 3, 4 | test #5, existing `test_validator_does_not_modify_spec` pattern, `WorldValidator.validate()`'s existing ERROR-only raise behavior (`validator.py:383-389`, unmodified) |
| AC6: ticket record correction (GUILDACTION-DEAD-WIRING vs HUNT-TARGET-METADATA-GAP) | Step 8 | Manual review; no test |

## Deviations

- **Step 7 parity-ledger ID**: this plan assumed the next available ID after `SUB-384` would be
  `SUB-385`. By implementation time, `docs/parity_ledger/substrate.yaml` already contained
  `SUB-385` and `SUB-386` (landed by other concurrent work between Plan and Implement).
  Architecture-review flagged this before implementation began; the real next available ID,
  `SUB-387`, was used instead, with `priority: P2` (matching sibling `SUB-385`/`SUB-386`, both P2,
  consistent with this rule also being WARNING-severity and non-P0 per the investigation). No other
  step was affected.
- **Step 6 corpus source**: iterated `data/worlds/*/resolved/world.resolved.yaml` (21 real composed
  worlds found, satisfying the ticket's "20+" AC4 threshold) rather than raw
  `data/content/world_modules/*.yaml` files, exactly as the plan itself specifies — noted here only
  because the ticket body's own AC4 wording literally says "modules under
  data/content/world_modules/," which could otherwise read as a discrepancy; this was already an
  explicit, deliberate plan decision (Step 6), not a new deviation.
- **Baseline discovery**: the real, first-run corpus baseline (75 violations across 16 of 21
  worlds) includes a small subset of `spiritual`/`undead`-tagged quests (e.g.
  `undead_hunt_wraith_patrol`, `spirit_source_trace`) in addition to the plan's anticipated
  `opportunistic`/`beast` gap — these quests reference archetypes whose actual role trait does not
  match the tag the quest author chose (e.g. `undead_sentinel`'s role only carries
  `compatible_traits=['undead']`, not `spiritual`). This is additional real signal from running the
  rule for real, not a plan error or an implementation bug; recorded in Implementation Notes and the
  parity ledger's `divergence_note`.

## Anti-Drift Notes

- The corpus regression baseline (Step 6) is **expected to be non-empty** — the `opportunistic`
  (6 quest defs, 3 modules) and `beast` (2 quest defs, 1 module) vocabulary gap is a known,
  documented limitation of the chosen matching field, not a bug to fix by loosening the check.
  Getting a suspiciously clean (zero-violation) first run is a signal to re-check the
  implementation, not a success condition.
- `applicable_contexts` for the new rule must exclude `MODULE`. Verify this with test #4 before
  moving on — `dummy_spec` in `src/worldassembly/resolver.py:95-117` never populates
  `quest_definitions`, so a rule mistakenly scoped to `MODULE` would silently produce zero issues
  there forever, looking like coverage that isn't real.
- `WorldValidator()`'s existing 8-rule default list and its `rule_id` values must remain unchanged
  in name and content — only append the 9th rule. `test_validator_valid_world`'s `issues == []`
  assertion for empty `quest_definitions` is the load-bearing regression guard here.
- The six untouched `WorldValidator()` call sites must show **zero** behavior change — they were
  catalog-blind before this ticket and remain catalog-blind (by design) after it. If any of their
  existing tests newly fail, that is a signal the default-`None` short-circuit in
  `build_available_participant_tags`/`is_reachable` (Step 2) is not actually short-circuiting
  correctly — do not silently special-case those call sites individually to paper over it.
- Do not conflate this ticket's `WorldSpec`-bound, build-time validator with
  `TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION`'s separate runtime/`AuthoritativeState`
  check — the reusable unit is `src/worldbuilding/reachability.py`'s pure functions; no call site
  for the runtime check belongs in this ticket.
- `compiled_quests` remains fully dead code (never attached to `AuthoritativeState`) — this
  ticket's validator has no live runtime consumer yet. Disclose this in Implementation Notes so the
  corpus baseline isn't mistaken for "these quests are live and broken" — they're not live at all.
