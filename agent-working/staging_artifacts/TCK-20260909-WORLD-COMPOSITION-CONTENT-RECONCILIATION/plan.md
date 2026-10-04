---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION
artifact_type: plan
tags: [architecture, content]
---

# Implementation Plan — TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION

## Summary

`data/worlds/<world_id>/` is authoritative (settled by the rule owner; do not re-open). The content
side of this ticket therefore collapses to **one recorded decision plus one explicit call-out**, and
the real work is: (a) build the structural guard that makes "one `world_id`, one definition" and
"the committed `resolved/` projection equals a fresh resolve" checkable, and observe it **red on
today's tree first**; (b) state the law once, in the ADR, with Bible 06 and `content_authoring.md`
pointing at it; (c) repoint every test and code path that genuinely depends on
`data/content/world_compositions/` at the authoritative layout; (d) only then delete the directory,
after the generator stops writing into it. The `dungeon_crawl` `danger_scale` value is **not this
ticket's content decision** — it belongs to
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`; this ticket's only
obligation there is to leave no test or doc asserting either `2` or `4` as intended design on its own
authority.

**No step is blocked.** The one open question — Gap 1, the generator's output location — was resolved
by the rule owner on 2026-10-04 in favour of **Option A**: the generator writes
`data/worlds/<id>/world.yaml` directly, with a history-only provenance marker, because "authored"
names the file's role rather than who wrote the bytes. That ruling also **revised the ADR clause's
first sentence** (Step 3 uses the new text) and supplies the condition carried as Step 11's three
hard constraints. A second rule-owner correction tightened Step 2: the `resolved/` agreement guard is
a **full fresh-resolve equality**, never a fingerprint comparison standing in for it.

Context-search note: `mcp__knowledge-search__search_docs` returns `{"error":"index not found"}` and
`graphify-out/` does not exist in this worktree (recorded in `investigation.md` §"Context-search
provenance"). The sanctioned `tools/knowledge_search.py` fallback was used there; this plan builds on
that investigation plus direct re-verification of every file:line it cites below.

---

## Steps

### Step 1 — Extract one reusable "resolve a composition world" helper

**Files:** `src/worldbuilding/cli.py` (new module-level helper, or a new
`src/worldassembly/resolve_io.py` if the implementer prefers; keep it out of `tests/`).

**Change:** The AC-6 agreement half (Step 2) must compare a committed
`data/worlds/<id>/resolved/world.resolved.yaml` against a **fresh resolve**. Today the only code that
produces that file is inline inside `src/worldbuilding/cli.py::handle_resolve` — verified: it loads
`world.yaml` (`src/worldbuilding/cli.py:140-148`), validates `WorldCompositionSpec`
(`:156-160`), loads `CatalogRepository("data/content")` + `WorldModuleRepository(
ContentPathConfig().world_modules_dir)` (`:162-166`), calls `WorldAssemblyResolver(...).assemble(
composition)` (`:168-170`), then writes with
`yaml.safe_dump(bundle.world_spec.model_dump(exclude_none=True), f, sort_keys=False,
allow_unicode=True)` (`src/worldbuilding/cli.py:177,183-184`).
Extract exactly that sequence into a helper returning the bundle **and** the rendered YAML text, and
have `handle_resolve` call it so the CLI and the guard cannot drift in serialization (a byte
comparison is worthless if the two sides dump differently).

**REQUIRED SIGNATURE SHAPE (re-review advisory A1, folded in 2026-10-04 — this is load-bearing for
Step 11).** The helper **takes an already-validated `WorldCompositionSpec`, not a path.** The sequence
above begins by reading `world.yaml` off disk (`src/worldbuilding/cli.py:140-148`), and a path-in helper
makes Step 11's chosen option (a) — *resolve from the in-memory spec, commit both only on success* —
**not implementable**, which would silently push Step 11 onto its fallback (b). The clean seam already
exists: `handle_resolve` validates at `:157` (`WorldCompositionSpec.model_validate(raw_data)`) and only
then loads repos and assembles (`:162-170`). So:
- helper signature: `(spec: WorldCompositionSpec, ...) -> (bundle, rendered_yaml_text)`;
- a **thin path-loading wrapper** for the CLI does the `:140-157` read-and-validate, then calls the
  helper;
- Step 11 calls the helper directly with its in-memory spec, which makes option (a) the natural path
  rather than the awkward one.

**Other writers to this shared resource** (`data/worlds/<id>/resolved/*`), enumerated — grep over
`src/` and `tools/` for `world.resolved.yaml` returns exactly one writer and five readers:
- **Writer (only):** `src/worldbuilding/cli.py:177-205` (`make world-resolve WORLD=<id>`,
  `Makefile:139-140`). No other `src/` or `tools/` path creates or mutates `resolved/`.
- Readers, unaffected but must keep working: `src/worldbuilding/repository.py:78` (`load_world`),
  `:132` (`load_world_with_context`), `src/lab/orchestrator.py:181-184` (reads only),
  `tools/generate_corpus_registry.py:108,139`, `tools/calibrate_simq.py:150`,
  `tools/perf/profile_sweep.py:73`.
Because there is a single writer, the helper extraction carries no ordering or race risk; the only
interaction to preserve is that `handle_resolve` keeps writing the same five sidecars
(`world.resolved.yaml`, `compile_context.json`, `provenance_manifest.json`, `assembly_report.json`,
`validation_report.json`, `src/worldbuilding/cli.py:176-205`).

**Do NOT touch:** `WorldAssemblyResolver.assemble()` itself; `WorldRepository`'s
composition→`resolved/` redirect (`src/worldbuilding/repository.py:74-81`); the ADR §2 vs.
`world_compile_report.json` naming drift (pre-existing, out of scope).

**Verify:** `pytest tests/unit/worldbuilding/ -q` green (behavior-preserving refactor);
`make world-resolve WORLD=wilderness_survival` still writes all five sidecars.

---

### Step 2 — Add the AC-6 guard and observe it RED before changing any content

**Files:** `tests/architecture/test_world_definition_single_source.py` (new).

**Change:** Two guards, per `test_plan.md` §"AC-6 / AC-10":
1. `test_world_id_resolves_to_exactly_one_definition` — walk for any YAML whose `schema_version` is a
   `worldcomposition` version and that is **not** at `data/worlds/<id>/world.yaml`, and fail naming
   every offender. Key on **existence of a second definition, not on difference** —
   `simq_scale_stress_seed42` is a byte-identical pair and a difference-based check would pass there
   while the duplicate still exists.
   **Implementation constraints (architecture review V5), both of which a grep-shaped version gets
   wrong:** (a) key on the **parsed** `schema_version` value — `yaml.safe_load` the candidate and read
   the field — never on the presence of the substring `worldcomposition` in the file text; (b) **bound
   the walk to data roots and exclude `docs/`**. Verified false offenders under a text-matching,
   unbounded implementation: `docs/parity_ledger/progression.yaml` and `docs/REGISTRY.yaml` both
   contain the string in prose, as do `docs/testing/test_taxonomy.md`,
   `docs/guidelines/intentional_divergences.md` and the ADR itself.
2. `test_no_source_outside_data_worlds_defines_a_known_world_id` — for every id in
   `WorldRepository("data/worlds").list_worlds()` (verified to index only direct children holding a
   `world.yaml`, `src/worldbuilding/repository.py:46-61`), assert no other path declares that
   `world_id` with a composition schema.
3. `test_committed_resolved_projection_equals_a_fresh_resolve` — for every one of the 24
   `data/worlds/<id>/` worlds (measured: all 24 are `worldcomposition.v1`), re-resolve via Step 1's
   helper and compare to the committed `resolved/world.resolved.yaml`. **Equality against a fresh
   resolve, never a field-by-field diff against `world.yaml`** (rule-owner constraint; the projection
   legitimately contains expanded content). Mark it `@pytest.mark.slow` if runtime demands, but do
   not reduce the corpus.
   **The full equality is the check — a content fingerprint may not stand in for it.** Rule-owner
   correction (2026-10-04), which overrides any earlier suggestion that a recorded fingerprint would
   suffice: a `content_fingerprint` is computed from the resolver's *inputs*, so it detects a **stale**
   snapshot but **cannot** detect a **hand-edited** `world.resolved.yaml` whose recorded fingerprint
   still matches — and "never hand-edited" is half the ADR clause. A fingerprint comparison is
   permitted only as a cheap first pass **in front of** the equality (skip-fast when it already
   disagrees), never as a substitute for it. If the implementer finds a fingerprint-only variant
   cheaper to write, that is not a reason to use it.

**Record the red run.** Paste the guard's own failure output into the ticket's Implementation Notes:
guard 1/2 must name the 9 catalog duplicates today; guard 3's result is unknown and unmeasured by
Investigate. **If guard 3 fails for any world, or a fresh resolve is not byte-deterministic, file
that as a new finding ticket and leave the guard strict — do not weaken it to a subset and do not
regenerate snapshots to make it green** (see Scope Guards).

**The red state must be reconstructible, not just asserted (architecture review V5).** AC-6 makes
this the ticket's mandatory negative control, and pasted prose is not evidence — an implementer who
never ran the guard against the untouched tree produces Implementation Notes indistinguishable from
one who did. So: **this guard file lands in its own commit, before any `data/` or test change in
Steps 7-12.** Anyone can then check out that commit and re-run the guard to reproduce the red. (The
mutual independence of Steps 7-10 does not threaten this — the constraint is only that the guard
commit precedes all of them.)

**Expect guards 1 and 2 to stay red from here until Step 12.** That is the intended state for the
whole middle of the plan, not a defect to chase: the duplicates are not gone until the directory is
deleted. Guard 3 should be green throughout (or red with a filed finding). Note this in the ticket so
a later reader of a mid-stream CI run does not misdiagnose it.

**Do NOT touch:** any `data/` content in this step. The guard must be red against the untouched tree
or it proves nothing (AC-6's own wording).

**Verify:** `pytest tests/architecture/test_world_definition_single_source.py -q` **fails**, the
failure message names the offending ids, and the guard file is committed on its own — `git log` shows
that commit touching nothing under `data/` or `tests/` other than the new guard file. This red
observation, reproducible from that commit, is the deliverable of this step.

---

### Step 3 — Add the two normative sentences to the ADR §1

**Files:** `docs/architecture/world_repository_layout.md`.

**Change:** In §1 "Unified Directory Layout", directly after the existing normative sentence at
`:21` ("The root source file inside a world folder is always `world.yaml`. The schema version within
the YAML determines how the repository indexes it"), add **two** sentences as one rule block (not a
new section):
1. `data/worlds/<world_id>/` is the sole authoritative definition of a `world_id`; no other location
   may define a `world_id`.
2. The rule owner's verbatim clause. **Use this wording, not the version quoted in the ticket's
   BLOCKER section** — the rule owner revised the first sentence on 2026-10-04 when ruling UQ-1, so
   that "authored" (which reads as a claim about *who typed the bytes*) cannot be misread as
   excluding a generator. The rest of the clause is unchanged:

   > *"Within that directory, `world.yaml` is the source definition, whether written by hand or by a
   > generator; once written it is edited, not regenerated. For a `worldcomposition.v1` world,
   > `resolved/world.resolved.yaml` is a generated projection of it: it is never hand-edited, and it
   > must equal what the resolver produces from the current `world.yaml` and the current module/catalog
   > content. A committed projection that differs from a fresh resolve is a defect. It is not an
   > alternative definition."*

   Do not paraphrase, re-order or "tidy" this text — it is the rule owner's, and Step 6's guard and
   Step 11's whole design rest on its exact second clause ("once written it is edited, not
   regenerated").

Verified: the ADR is 54 lines, `ACCEPTED` (`:10-11`), and does **not** mention
`data/content/world_compositions/` anywhere — so this is an amendment, not a citation. §2 already
draws the source/projection structure at `:40-51`; only the authority and freshness rule is missing.

**Do NOT touch:** ADR §2's `resolved/compile_report.json` line (`:50`) vs. the tree's real
`world_compile_report.json` — pre-existing drift, explicitly out of scope. ADR §3 (`:53-54`)
backwards-compatibility clause stays as-is and constrains later steps to path changes, not loader
changes.

**Verify:** Step 6's docs guard.

---

### Step 4 — Bible 06 states the invariant and cites the ADR

**Files:** `docs/mechanics/06_worldbuilding_foundation.md`.

**Change:** Add the invariant — *"the world the engine loads is the one its authored definition
resolves to"* (the ticket's own AC-8 wording, kept verbatim; "authored" here carries the **role**
sense the ADR clause establishes — the source definition, whoever or whatever wrote the bytes — and
must not be read as "hand-written") — i.e. a `world_id` resolves to exactly one definition, and
**cite** `docs/architecture/world_repository_layout.md` for the location.

**It must NOT be written as a §7 severity-gate rule, and NOT in `WORLD-REACH-001`'s block shape.**
This corrects the plan's first draft (architecture review V1, verified against the chapter):
- §7's ladder is a **real compile-time** mechanism. `docs/mechanics/06_worldbuilding_foundation.md:93`
  opens "Integrity Validation Laws & Severity Gates"; `:114` defines **ERROR** as a failure that
  *"abort[s] the compilation pipeline immediately"*; `:118-119`'s Level 2 example is an actual
  `ParticipantReachabilityRule` whose `rule_id = "WORLD-REACH-001"` is a live class attribute at
  `src/worldbuilding/validator.py:337-338`. Chapter 06 is **Certified Level 1 (Authoritative)**
  (`:255`).
- This invariant is enforced by a **pytest architecture guard** (Step 2), not by the compiler, and it
  structurally **cannot** be a `WorldValidationRule`: whether a second definition of the same
  `world_id` exists somewhere else in the repo is unknowable to a validator handed one spec.
- Writing it in as a "Level 2 structural ERROR gate" would therefore document a gate nothing aborts
  on — the exact parity break the Authoritative Mechanics Rule forbids — and would be
  self-contradictory, since ERROR aborts compilation yet all 24 worlds compile cleanly today **with**
  the duplicate definitions present.

**Follow the chapter's own existing distinction instead.** It already separates the build-time ladder
from invariants enforced elsewhere, twice: `:198-202` ("This gate runs inside `WorldEmergencePhase` …
not the WorldSpec → Compile pipeline described in §7. It is a distinct, sibling gate — not an
extension of §7's build-time gate ladder or the `WORLD-REACH-001` rule") and `:230-235` (the same
build-time-vs-live split; corrected from `:233-237` per re-review advisory A4 — `:237-239` is the
determinism/purity paragraph, not the split). Write **one sentence** in that shape: explicitly a **repository-layout
law**, enforced by the ADR plus the Step 2 architecture guard, and explicitly **not** a
compile-pipeline gate. Place it as its own short sibling note, not inside §7's ladder.

**Do NOT touch:** do not restate the path `data/worlds/<world_id>/` or any freshness mechanics here.
One normative sentence, in the ADR; this chapter points at it. Restating it is how three sources
drift, and Step 6's guard will fail on a restatement. Do not add a catalog Rule under
`docs/world_rules/` — the rule owner explicitly declined (storage/build is below catalog scope; cite
"by analogy to `OWN-01`", never "`OWN-01` governs"). Do not give the invariant a `WORLD-*` rule id, do
not assign it a severity, and do not add it to §7's rule list.

**Verify:** Step 6's docs guard.

---

### Step 5 — Correct `content_authoring.md` at all four sites

**Files:** `docs/guides/content_authoring.md`.

**Change:** Re-verified by grep — the retired path is taught at exactly four places: `:27` (§1 type
table row "World composition | `data/content/world_compositions/`"), `:72` (§2 Step 4 example path
`data/content/world_compositions/frontier_living_world.yaml`), `:167` (§4's location sentence
`data/content/world_compositions/<world_id>.yaml`), `:292` (a YAML comment "# in
`world_compositions/<id>.yaml`"). Change all four to `data/worlds/<world_id>/world.yaml` and link the
ADR from §4 instead of restating the rule.

**Do NOT touch:** §4's `make world-validate` / `make world-compile` workflow block — verified
`Makefile:133-140` already drives `src.worldbuilding.cli` against `data/worlds/`, so the tooling
instructions are already correct. **Only the file-location sentences are wrong.**

**Verify:** Step 6's docs guard; `grep -rn "data/content/world_compositions" docs/guides/` returns
nothing.

---

### Step 6 — Add the docs-agreement guard

**Files:** `tests/architecture/test_world_definition_single_source.py` (extend).

**Change:** `test_authoritative_world_location_stated_once` — asserts (a) the normative
"sole authoritative definition" sentence appears in `docs/architecture/world_repository_layout.md`,
(b) neither `docs/mechanics/06_worldbuilding_foundation.md` nor `docs/guides/content_authoring.md`
restates the authoritative path without citing the ADR, (c) no file under `docs/guides/` presents
`data/content/world_compositions/<world_id>.yaml` as an authoring target.

Plus a second guard (architecture review V1): `test_bible_06_does_not_present_the_invariant_as_a_compile_gate`
— asserts the one-definition invariant sentence in `docs/mechanics/06_worldbuilding_foundation.md` is
**not** presented as a §7 Level-2/ERROR severity-gate rule (no `WORLD-*` rule id attached to it, no
`ERROR`/`Level 2` severity wording in its sentence or block, and it does not sit inside §7's rule
list). This exists because the temptation to "tidy" the invariant into the neighbouring gate ladder is
exactly how a documented-but-unenforced gate gets created; a later editor promoting it must trip a
test, not merely contradict a plan.

**Do NOT touch:** `docs/archive/`, `docs/audits/`, `docs/brainstorm/`,
`docs/plans/world_generation_organic_terrain_epic.md` — frozen historical records; the guard must
exclude them, and no step may edit them.

**Verify:** `pytest tests/architecture/test_world_definition_single_source.py -q -k docs`.

---

### Step 7 — Repoint the seven named-world sites in `test_real_content_world_compositions.py`

**Files:** `tests/integration/worldassembly/test_real_content_world_compositions.py`.

**Change:** Swap `Path("data/content/world_compositions/<id>.yaml")` →
`Path("data/worlds/<id>/world.yaml")` at the seven verified path lines `:30`, `:44`, `:62`, `:86`
(`frontier_living_world`), `:345` (`wilderness_survival`), `:385` (`urban_political`), `:436`
(`dungeon_crawl`) — the tests at `:28`, `:42`, `:59`, `:83`, `:333`, `:374`, `:424`. Both sides carry
`schema_version: worldcomposition.v1` and validate against the same `WorldCompositionSpec`, and all
24 `data/worlds/*/world.yaml` were measured to validate and assemble, so the swap is mechanically
safe. Then resolve the measured assertion deltas:
- `:52` `len(normalized.module_refs) == 6` → `7`
- `:112` `len(provenance_manifest.module_fingerprints) == 6` → `7`
- `:374`'s test: `len(spec.module_refs) == 3` → `4`
- `:333`'s test: `len(spec.module_refs) == 4` — unchanged, clean swap
- `test_real_world_compositions_normalization` (`:42-56`) **must be redesigned, not repointed.**
  Verified at `:54-56`: it loops `assert ref.order == 0` and its docstring says "normalizes shorthand
  modules". `data/worlds/frontier_living_world/world.yaml` uses `module_refs` with explicit
  `order: 0..6`, so its subject does not exist on the authoritative side. Either (a) rename it to a
  `module_refs`-form normalization test with assertions that match the authoritative file, or (b)
  keep a **synthetic** shorthand fixture inside the test and say so in a comment. Do not delete the
  shorthand-conversion coverage silently — `WorldCompositionNormalizer` still supports both shapes.
- `test_dungeon_crawl_composition` (`:424`): remove the two content-value assertions
  `len(spec.module_refs) == 2` (`:437`) and
  `bandit_ref.parameters.get("danger_scale") == 2` (`:452`), and rewrite the docstring (which
  currently states "danger_scale=2 (6 bandits)… reduce entity count from 32 to 12
  (TCK-20260627-P1I-WORLD-BALANCE-FIX)"). Replace both with a comment naming
  `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` as the owner of the
  module-count and `danger_scale` oracle. **Do not change `2` to `4`** — per the ticket's amended
  AC-5, this ticket must carry neither `2` forward as authoritative nor `4` forward as
  confirmed-correct. Keep the remaining structural assertions (`world_id`, `schema_version`,
  `provided_features`, `default_perspectives`, `bandit_ref` exists, quest count ≥ 2) and keep the
  `scalable_bandit_camp` ref lookup so the other ticket has a seam to assert into.

**Do NOT touch:** the six out-of-reach tests at `:171`, `:188`, `:205`, `:224`, `:265`, `:300`. They
build synthetic specs / synthetic `world_id`s and the ADR says nothing about them; a `git diff` over
those six must be empty.

**Verify:** `pytest tests/integration/worldassembly/test_real_content_world_compositions.py -q`.

---

### Step 8 — Repoint the other genuinely-dependent test files

**Files:** `tests/integration/worldassembly/test_e2e_smoke.py`,
`tests/unit/worldassembly/test_assembly.py`,
`tests/integration/content/test_swamp_border_pack.py`,
`tests/integration/content/test_expansion_gate.py`.

**Change:** All four were re-verified as genuine dependencies (they load or glob the directory and
would break on deletion):
- `test_e2e_smoke.py:54` (`_compile_composition`) and `:74` (`_compile_generated_composition`) →
  `data/worlds/{world_id}/world.yaml`. The two helpers collapse into one: both
  `generated_frontier_3_42` and `simq_scale_stress_seed42` exist as real `data/worlds/<id>/`
  directories (verified by listing — 24 dirs), so the `generated/` special case disappears. Its four
  tests assert only `entity_count > 0`, `quest_count >= 2`, `len(state.resource_nodes) >= 3` — no
  exact counts — so the repoint needs no assertion changes; only the module docstring's prose counts
  at `:17-20` ("dungeon_crawl: 10 ticks, 32 entities") must be corrected or made non-numeric. This
  file was **not** in the rule owner's repoint table, but deletion forces the change and the
  assertions carry no content oracle, so repointing it is a mechanical consequence, not a new
  semantics decision.
- `test_assembly.py:1058` and `:1079` → `data/worlds/frontier_living_world/world.yaml` (both have
  `assert comp_path.is_file()`). Leave `:1185`/`:1190` alone — error-string mentions of the family
  name `'world_compositions'`, not a path.
- `test_swamp_border_pack.py:93` → `data/worlds/{cid}/world.yaml` for each
  `manifest.sample_compositions` (sourced from `data/content/packs/swamp_border_pack.yaml`; the ids
  resolve under `data/worlds/`).
- `test_expansion_gate.py:184` (Gate 08, `compositions_dir.glob("*.yaml")`) and `:248` (Gate 11,
  `sorted(glob("*.yaml"))[0]`) → iterate `Path("data/worlds").glob("*/world.yaml")`. Gate 11 raises
  **`IndexError`**, not an assertion failure, on an empty directory — if the implementer sees an
  `IndexError` here, it is this ticket's step ordering (deletion before this step), not a new bug.

**Do NOT touch:** `tests/unit/content/test_content_usage_matrix.py` (`:87`, `:97`, `:397`) and
`tests/integration/scenarios/test_content_foundation.py` (`:27-61`) — classified as mentions. The
former uses `"world_compositions"` as a structural-folder *name* in a one-directional
`scanned_families - CONTENT_USAGE_MATRIX.keys()` check (verified at `:104-108` and `:411-415`), so
deleting the directory keeps it green; the latter reads the `world_composition` *field* on scenario
YAMLs under `data/content/simulation_scenarios/` and never touches the directory.

**Verify:** `pytest tests/integration/worldassembly/ tests/unit/worldassembly/ tests/integration/content/ -q`.

---

### Step 9 — Flip the resolver default, revert the Campaign override, fix the stale citation

**Files:** `src/scenarios/resolver.py`, `src/domains/campaigns/orchestrator.py`,
`tests/unit/scenarios/test_resolver_defaults.py` (new),
`tests/unit/domains/campaigns/test_campaign_orchestrator.py`,
`tests/integration/scenarios/test_scenario_setup_resolver.py` (only if its error-message assertion
breaks).

**Change:**
1. `src/scenarios/resolver.py:34`: `_DEFAULT_COMPOSITIONS_DIR = Path("data/content/world_compositions")`
   → `Path("data/worlds")`. No loader change is needed: `_load_composition()` (`:58-95`) already tries
   `<dir>/<world_id>/world.yaml` first and falls back to `<dir>/<world_id>.yaml`. **Keep the dual
   layout** (the ticket's open question) — the fallback is three lines, costs nothing, and the flat
   shape still appears in third-party/ad-hoc `compositions_dir` overrides; record that choice in the
   ticket. Update the now-stale explanatory comment at `:59-72` (it describes
   `data/content/world_compositions/` as "this repo's existing default").
2. **Only after 9.1 has landed** (see the hard ordering constraint below):
   `src/domains/campaigns/orchestrator.py:199-201`: drop `compositions_dir=Path("data/worlds")` from
   the `CatalogScenarioStateBuilder(...)` construction so Campaign rides the now-unified default, and
   rewrite the comment block at `:172-188` — it both carries the "data/content/world_compositions/ is
   the anomaly" interpretation (`:178`, the real origin of the mis-attribution the ticket corrects)
   and the dead citation `TCK-20260909-WORLD-COMPOSITION-DIRECTORY-CONSOLIDATION` (`:186`, Gap 3).
   Replace the citation with this ticket's ID and point the authority claim at the ADR as amended in
   Step 3.
3. The two default-riding tests: verified neither asserts a module count or any other
   content-sensitive number — `test_scenario_catalog_matrix.py`'s assertions are at `:158-212`
   (ids, perspective, modifier non-emptiness) and its unoverridden fixture is at `:47-49`;
   `test_scenario_setup_resolver.py`'s fixture is at `:37` and its assertions at `:57-101` are
   structural. `default_perspectives` was measured identical on both sides for all 9 pairs, so
   `_validate_perspective()` (`:97-108`) cannot break. The one thing to check by running it:
   `test_invalid_composition_fails_with_scenario_id` (`:114-121`) asserts on the "not found at …"
   message, whose two paths change.
4. New `tests/unit/scenarios/test_resolver_defaults.py`:
   `test_scenario_setup_resolver_default_compositions_dir_is_data_worlds` (asserts the constant and
   that an unoverridden resolver resolves `frontier_living_world` from
   `data/worlds/frontier_living_world/world.yaml`), and append
   `test_campaign_orchestrator_uses_resolver_default_not_an_override` to the campaign orchestrator
   test — proving the revert happened and was not replaced by a second hard-coded path.
   **Plus a content oracle (architecture review V4):** assert the default-resolved
   `frontier_living_world` carries the **7-module** definition — compare
   `len(spec.module_refs)` against the module count parsed from
   `data/worlds/frontier_living_world/world.yaml` rather than hard-coding `7`, so the assertion
   survives a legitimate later edit to that world. Without this, the 6-vs-7-module fallback described
   below is **undetectable by the whole Step 9 verify command**, because none of the existing
   scenario tests carry a module-count oracle.
   **Non-zero guard REQUIRED (re-review advisory A2, folded in 2026-10-04):** also assert the parsed
   count is `> 0` before comparing. `module_refs` is `Field(default_factory=list)`
   (`src/worldassembly/schema.py:32`), so an empty module list is schema-valid and a
   parsed-count-vs-spec-count comparison is structurally capable of degrading to `0 == 0` — passing
   while testing nothing. Step 10 item 5 already applies exactly this discipline to the inventory
   counter; apply it here for the same reason. (A vacuous-pass assertion has already shipped green in
   this repo once, on a position test whose fixture produced no entities.)

**Hard ordering constraint inside this step: 9.1 MUST land before 9.2.** If the Campaign override is
dropped while the default still points at `data/content/world_compositions/`, Campaign silently falls
back to the retired flat directory and runs the **6-module** `frontier_living_world` instead of the
7-module one — and **the Step 9 verify command stays GREEN**, because those tests assert only ids,
perspectives and modifier non-emptiness. The window is transient (Step 12's deletion closes it by
making the fallback raise), but a silent wrong-world run is worse than a loud failure, and this is the
one place in the plan where doing the right edits in the wrong order produces no signal. Recorded
again in the Dependency Map so it is not read as mere list position.

**Do NOT touch:** `CatalogScenarioStateBuilder`'s own signature; the legacy
`build_scenario_state()` / `ArenaInjector` / `V2EngineManager` spawn paths (explicitly out of scope);
`WorldRepository`'s production load path. Do **not** remove the flat-layout fallback in
`_load_composition()` — three lines, and it is the seam third-party `compositions_dir` overrides use.

**Verify:** `pytest tests/integration/scenarios/ tests/unit/scenarios/ tests/unit/domains/campaigns/test_campaign_orchestrator.py tests/integration/campaigns/ -q`.

---

### Step 10 — Resolve the content-layer path registration (investigation Risks #8)

**Files:** `src/content/paths.py`, `src/content/validator.py`, `src/content/repository.py`,
`tests/unit/content/test_content_paths.py`, `tools/generate_content_inventory.py`,
`tests/tools/test_content_inventory.py`.

**Change:** The decision the planner owes here — **repoint the loader, retire the
`data/content/`-relative path field**:
1. `src/content/paths.py:8`: remove `world_compositions_dir: str = "data/content/world_compositions"`.
   **Do not add a `world_definitions_dir` field in its place** — this corrects the plan's first draft
   (architecture review V2, independently verified): `ContentPathConfig` declares only children of its
   own root (`src/content/paths.py:6`, `content_root = "data/content"`), its pinning test is literally
   named `test_default_content_paths_point_to_data_content`
   (`tests/unit/content/test_content_paths.py:8-13`), and
   `test_non_catalog_dirs_constant_matches_path_config` (`:164-175`) **derives** its expected set from
   three `ContentPathConfig` basenames. A `data/worlds` field would make the content-path registry
   declare another layer's root, falsify that test's name, and force a hand-trim of the derivation —
   after which the guard still passes but stops catching the next field anyone adds. That weakening is
   the part the plan's earlier "deliberate and recorded, not a literal edited to go green" note did
   **not** cover: it was true of the removal, not of the mechanism.
   Verified the removed field has exactly **two** production consumers —
   `src/content/validator.py:38` and `:153` — plus two test pins
   (`tests/unit/content/test_content_paths.py:12`, `:169`) and one doc row
   (`docs/content/pipeline_contract.md:34`).
2. **Source the validator's default from the layer that owns `data/worlds/`.**
   `src/content/validator.py:38` becomes
   `load_all_compositions(worlds_dir: str = DEFAULT_WORLDS_ROOT)` importing from
   `src/worldbuilding/repository.py`, and `:153` passes the same constant instead of a
   `ContentPathConfig` field — the content layer consumes the owner's constant rather than
   re-declaring another layer's root.
   **One correction to the review's own prescription, flagged rather than papered over:** it says to
   use "the existing `WorldRepository` default root", but **no such default exists** — verified
   `WorldRepository.__init__(self, worlds_dir: str | Path)` at `src/worldbuilding/repository.py:22`
   takes a **required** argument, and all 10+ call sites pass the literal `"data/worlds"`
   (`src/worldbuilding/cli.py:59,88,140,227,311,347`, `src/cli/entry.py:220`,
   `src/domains/campaigns/orchestrator.py:745`, `src/api/engine_manager.py:134`). So this step must
   **introduce** `DEFAULT_WORLDS_ROOT = "data/worlds"` as a module-level constant in
   `src/worldbuilding/repository.py` (the owning layer) and import it. The review's intent is
   satisfied exactly; only its premise about an existing constant was wrong.
   **Scope bound:** define the constant and use it in the two `validator.py` sites only. Do **not**
   sweep the 10+ existing `WorldRepository("data/worlds")` literals onto it — that is unrelated
   cleanup and would inflate this ticket's diff across `src/api/`, `src/cli/` and `src/domains/`.
   The repoint is safe without changing the glob: verified at `src/content/validator.py:43-58` it globs
   `**/*.yaml` and `**/*.yml` but only appends entries whose `schema_version` contains
   `worldcomposition` (`:46`), so the `resolved/world.resolved.yaml` sidecars (tagged
   `worldspec.v1`) are skipped and the nested `<id>/world.yaml` layout is found.
3. `src/content/repository.py:150`: drop `"world_compositions"` from `NON_CATALOG_DIRS`. That
   frozenset names directories **inside `data/content/`** managed by other loaders; after the
   deletion there is no such directory. It must change in lockstep with
   `tests/unit/content/test_content_paths.py:164-175`, which derives the expected set from
   `ContentPathConfig` basenames — leaving either side alone breaks that invariant test. After this
   step the derivation is over **two** fields (`world_modules_dir`, `simulation_scenarios_dir`)
   instead of three, and it stays **fully derived** — no hand-written member, no trimmed expectation,
   so it still fails if someone adds a fourth content directory without registering it.
4. `tests/unit/content/test_content_paths.py:12`: **delete** the
   `world_compositions_dir == "data/content/world_compositions"` pin and add an explicit assertion
   that `ContentPathConfig` no longer exposes a `world_compositions_dir` attribute (so the field
   cannot quietly return). Do **not** substitute a `data/worlds` pin here — that is what V2 forbids;
   the worlds root is pinned in the worldbuilding layer's own tests, next to `DEFAULT_WORLDS_ROOT`.
   Update `:169` to drop the member, leaving the set derived from the two remaining fields.
   The test's name (`test_default_content_paths_point_to_data_content`) stays accurate, which is the
   point: every field it checks is still a child of `content_root`.
5. `tools/generate_content_inventory.py:91-94`: replace the two counters
   `"World compositions"` = `glob("data/content/world_compositions/*.yaml")` and
   `"World compositions (generated)"` = `glob(".../generated/*.yaml")` with a single
   `"World compositions"` = `glob("data/worlds/*/world.yaml")`. Update
   `tests/tools/test_content_inventory.py:46-49` to match **and to assert a non-zero count** — after
   deletion the old equality would have had `0 == 0` on both sides and passed while measuring
   nothing (the silent-degradation case). Note the tool writes
   `config/content_inventory.json` (`:20`, `:100`) via `make content-inventory`; that generated file
   will show the changed key set on its next regeneration — expected, not a defect.

**Deliberate non-changes, recorded so a later reader does not read them as misses:**
`src/content/matrix.py:550-561` (the `world_compositions` `ContentFamilyMatrixEntry`) and `:637-639`
(`_STRUCTURAL_DIRS`), and `src/content/reference_graph.py:42` — these name a content **family**, not
a filesystem location (`repository_index="None"`, and `file_path` is advisory: verified nothing
resolves it to disk for a structural family, `src/content/matrix.py:682-688` only uses it for
auto-discovered entries). The family survives the move. Also note
`docs/mechanics/content_usage_matrix.md` is **generated** by
`tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report` (verified: it
writes the file at `:111-120`), so it must never be hand-edited — it regenerates unchanged if
`matrix.py` is left alone.

**Verify:** `pytest tests/unit/content/ tests/integration/content/ tests/tools/test_content_inventory.py -q`.

---

### Step 11 — The generator writes the source definition directly (Gap 1 / AC-9) — Option A, RESOLVED

**Files:** `src/worldgeneration/generator.py`, `src/worldassembly/schema.py`,
`src/worldbuilding/cli.py`, `tests/unit/worldgeneration/test_composition_generator.py`,
`docs/world/generator_contract.md`.

**Decided by the rule owner, 2026-10-04 — Option A is conformant.** Cite the reasoning as theirs, do
not restate it as the plan's own: *"authored" names the FILE'S ROLE, not who wrote the bytes.* The
ADR clause splits the record-of-truth file from the derived projection, and **each is defined by an
obligation, not by authorship**: a projection must equal a fresh derivation from other committed
inputs, so it may never be edited independently; the definition file carries no such obligation — it
is what everything else derives from. Who typed the bytes plays no part in either definition.
Therefore the generator may write `data/worlds/<world_id>/world.yaml` directly, with a provenance
marker. (Options B and C are closed: B measured out via `list_worlds()`, C unnecessary once
authorship is irrelevant to the source/projection split.)

**Verified facts this step changes:** `src/worldgeneration/generator.py:536-538` does
`output_dir = Path("data/content/world_compositions/generated")`, `mkdir(parents=True,
exist_ok=True)`, then writes `{world_id}.yaml`; the docstring at `:383` declares that path as the
output contract; the **only production caller** is `src/worldbuilding/cli.py:421-422`
(`generator.generate(intent, mod_repo)`), everything else is tests.
`docs/world/generator_contract.md:27` and `:305` state the same path and must change in the same
commit. Because this is a **single writer** to the retired directory there is no ordering/race
interaction — but **Step 12 cannot run until this step lands**: one generation run recreates the
directory and silently re-opens the split.

**The condition attached to the ruling, and the three hard constraints it imposes.** Once the
generator writes `world.yaml`, that file **is** the definition; the generator acted as a one-time
author, not a continuing projection. If the design ever expects `world.yaml` to be regenerable from a
seed and params stored elsewhere, those params become the real definition and `world.yaml` degrades
into a projection of them — re-creating a second definition location, i.e. Option C's problem by
another route. So:
1. **The provenance marker records HISTORY only** — generator name, version, seed, intent params — as
   a fact about origin. It is not an input contract.
2. **No check may assert `world.yaml == generate(marker)`.** That would convert the marker into a
   re-derivation obligation and make `world.yaml` a projection. No test, guard, make target or CI job
   may be shaped that way.
3. **Nothing outside `data/worlds/<id>/` may hold generation inputs as a definition.** The
   `GenerationIntentSpec` that drove a run is history inside the marker, not a stored definition
   elsewhere.

**Change:**
1. **Typed provenance marker.** Add a frozen `GenerationProvenanceSpec` to
   `src/worldassembly/schema.py` (generator name, generator version, `generation_id`, `seed`, the
   intent's parameter values, timestamp) and an **optional** `generation_provenance` field on
   `WorldCompositionSpec`. It must be a declared field: verified `WorldCompositionSpec.model_config`
   is `ConfigDict(frozen=True, extra="forbid")` (`src/worldassembly/schema.py:23`), so an undeclared
   marker key would make every generated file fail validation. `GenerationIntentSpec`
   (`src/worldgeneration/schema.py:8-22`) is the source of the recorded params. Optional ⇒ all 24
   existing `data/worlds/*/world.yaml` files stay valid, and because `handle_resolve` dumps with
   `exclude_none=True` (`src/worldbuilding/cli.py:184`) the new field cannot perturb any existing
   `resolved/` snapshot — which matters, because Step 2's guard 3 compares those bytes.
   Note the existing `generation_seed` field (`:38`, default `42`) is the resolver's determinism seed,
   **not** origin history — do not overload it as the marker.
2. **Output location.** Parameterize `generate(..., output_dir: Path | None = None)` (option D's
   shape, so the path stops being hard-coded) defaulting to `Path("data/worlds")`, write
   `<output_dir>/<world_id>/world.yaml`, and populate `generation_provenance`. Update the docstring at
   `:383` and `docs/world/generator_contract.md:27,305`.
3. **Refuse to overwrite an existing definition.** If `<output_dir>/<world_id>/world.yaml` already
   exists, raise `GenerationCompositionError` (already defined, `src/worldgeneration/generator.py:26`)
   rather than rewriting it. This is constraint (1)/(2) enforced in code: a second generation run must
   not silently re-derive a file that is now the definition and may have been edited since.
4. **Produce the `resolved/` sibling — and commit both writes atomically.** The new world needs
   `resolved/world.resolved.yaml` + four sidecars, because `WorldRepository.load_world()` raises
   `WorldRepositoryError` for a composition world with no snapshot (verified
   `src/worldbuilding/repository.py:78-81`), so a generated world would otherwise be immediately
   unloadable and Step 2's guard 3 would fail on it. Reusing Step 1's helper also keeps
   **single-writer discipline**: `resolved/` is still produced by exactly one code path, now reached
   from two callers (the `resolve` CLI subcommand and the generator).

   **The coupling is right and must not be split, but the failure path must be handled** —
   architecture review V3, and it is a real unrecoverable state, not a theoretical one. Naively
   sequenced, these are **two durable writes with no atomicity**: if resolve fails *after*
   `world.yaml` has landed, `repository.py:78-81` raises on every load **and** item 3's
   refuse-to-overwrite makes a retry raise too — the world is simultaneously unloadable and
   un-regenerable, and guard 3 goes red on it. Resolve it with **(a)**: resolve from the
   **in-memory** `WorldCompositionSpec` first and commit `world.yaml` + `resolved/` only once the
   resolve has succeeded. If (a) proves awkward against Step 1's helper signature, **(b)** is
   acceptable: remove the just-written `world.yaml` (and any partial `resolved/`) on resolve failure
   so a retry starts clean.
   **Do not take option (c)** — exempting the "`world.yaml` exists but `resolved/` is absent" case
   from item 3's refusal. It would widen exactly the overwrite seam the rule owner's condition
   narrows, and "a definition with no projection" is precisely the state an interrupted hand-edit
   also produces, so the exemption cannot tell a failed generation from a real definition.
   Either way, nothing here touches the three hard constraints: the marker still records history
   only, there is still no re-derivation check, and no generation inputs live outside
   `data/worlds/<id>/`.
5. **Tests** in `tests/unit/worldgeneration/test_composition_generator.py` (already `tmp_path` +
   `monkeypatch`-chdir isolated):
   - Replace — not sit beside — the `"generated" in str(output_path)` assertion at `:198` with an
     exact `output_path == tmp_path / "data/worlds" / world_id / "world.yaml"`. The old assertion
     survives Option A only by accident (the id itself starts with `generated_`), which is precisely
     the fragility to remove.
   - `test_generation_run_does_not_create_data_content_world_compositions` — asserts
     `not (tmp_path / "data/content/world_compositions").exists()`. Assert the **absence** explicitly;
     asserting only that the new path exists would pass a "wrote to both" implementation. This is the
     test that discharges AC-9.
   - `test_generated_world_records_provenance_history` — the marker is present and carries
     generator/seed/params.
   - `test_generate_refuses_to_overwrite_an_existing_definition` — second run raises.
   - `test_resolve_failure_leaves_no_half_written_world` — **the sixth test, added by review V3**:
     force the resolve to fail (e.g. monkeypatch the helper to raise, or feed an intent whose module
     selection cannot assemble), then assert that either no `world.yaml` was committed (option a) or
     it was removed (option b) — and that a subsequent successful `generate()` for the same
     `world_id` works rather than hitting item 3's refusal. The other five tests cover happy path,
     absence, provenance, exact output path and refuse-to-overwrite; **none of them covers cleanup**,
     which is the one path that produces the unrecoverable state.
   - **No test asserting `world.yaml == generate(marker)`.** Constraint (2) is a design rule on this
     step, not a suggestion; if a re-derivation-shaped test appears, it is wrong even if green.

**Engineering decisions taken here (explicitly mine, not routed to the rule owner):**
- **`list_worlds()` does not distinguish generated worlds.** The in-YAML marker suffices as
  provenance; no structural or indexer change. This also keeps scope guard #5 intact.
- **`generate()` does run the resolve step** (item 4 above). The alternative — leaving the world
  unresolved and expecting a follow-up `make world-resolve` — ships a definition that
  `WorldRepository.load_world()` refuses, and would make Step 2's guard 3 red on arrival.
- **Single-writer discipline on the authored side** is item 3: the generator authors `world.yaml`
  once and never rewrites it; thereafter it is edited like any hand-authored definition.

**Do NOT touch:** `WorldRepository`'s indexer or `list_worlds()`. Do not add a `generated/` grouping
directory (Option B is measured out — `list_worlds()` indexes direct children only, so a nested id is
invisible). Do not store the `GenerationIntentSpec` anywhere outside the marker.

**Verify:** `pytest tests/unit/worldgeneration/ -q`; plus Step 2's guard 3 still green for a
freshly generated world.

---

### Step 12 — Delete `data/content/world_compositions/` and add the absence guard

**Files:** `data/content/world_compositions/` (removed: 7 top-level + `generated/` with 2 files —
re-verified by listing), `tests/architecture/test_world_definition_single_source.py` (extend).

**Change:** `git rm -r data/content/world_compositions/`. Add
`test_catalog_world_compositions_directory_is_absent` asserting
`not Path("data/content/world_compositions").exists()`. Also add
`test_no_test_contradicts_the_authoritative_danger_scale`: scan `tests/` for any `danger_scale`
equality literal and fail if one exists whose value differs from
`data/worlds/dungeon_crawl/world.yaml`'s `scalable_bandit_camp.parameters.danger_scale`. Written that
way it discharges AC-5's "no surviving copy of the `== 2` assertion may reappear in another file"
**and** stays correct whichever order this ticket and
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` land in — a hard-coded
"no `== 2` anywhere" guard would become wrong the moment that ticket sets the authoritative value
to `2`.

**Do NOT touch:** anything under `data/worlds/`. In particular do **not** edit
`data/worlds/dungeon_crawl/world.yaml` and do **not** regenerate any `resolved/` snapshot — see
Scope Guards.

**Verify:** `pytest tests/architecture/test_world_definition_single_source.py -q` now **green**
(guards 1 and 2 at minimum; guard 3 green or its failures filed per Step 2). Re-run Steps 7-10's
commands to confirm nothing depended on the deleted files.

---

### Step 13 — Write the AC-7 measurement-validity assessment

**Files:** `agent-working/tickets/inprogress/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION.md`
(Completion Summary / Implementation Notes).

**Change:** Bound the sweep so the AC can close honestly (the investigation flags the general case as
unbounded): grep `agent-working/stored_artifacts/` for `world_compositions` and for
`WorldAssemblyResolver`, re-check only the hits, and state the method and its bound in the write-up.
Required content: the one confirmed affected artifact
(`agent-working/stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED/investigation.md`,
which compiled via `data/content/world_compositions/frontier_living_world.yaml`); the five sibling
`UNREACHABLE-CLASSIFY-*` artifacts as the first sweep; and the two conclusions recorded as
**surviving** — the demographic-cohort truncation finding (its decisive probe used
`load_world_with_context` across 21 worlds) and the camp `STALE-PREMISE` closure (both its modules
present in both definitions of `frontier_living_world`). **Survivals are stated as survivals with
what was re-checked** — silence does not satisfy this AC. Do not re-litigate the two surviving
conclusions.

**Do NOT touch:** the stored artifacts themselves — they are historical records; the assessment is
written in this ticket.

**Verify:** no test; the written section exists and names its own sweep bound.

---

### Step 14 — Parity ledger (AC-10) and the two remaining contract docs

**Files:** `docs/parity_ledger/substrate.yaml`, `docs/parity_ledger/infrastructure.yaml`,
`docs/parity_ledger/faction.yaml`, `docs/content/pipeline_contract.md`.

**Change:**
1. Add **`SUB-394`** to `docs/parity_ledger/substrate.yaml` — re-verified the max existing numeric id
   is `SUB-393` at `docs/parity_ledger/substrate.yaml:5081` (confirmed independently by the
   architecture review); do **not** extend the legacy `SUBSTRATE-NEW-0NN` series. Entry asserts
   one-`world_id`-one-definition; `test_path` = Step 2's
   `tests/architecture/test_world_definition_single_source.py::test_world_id_resolves_to_exactly_one_definition`
   node id; priority P1; `v2_evidence` cites the ADR §1 amendment and the guard.
2. Update `SUBSTRATE-NEW-010` and `SUBSTRATE-NEW-011` `v2_evidence` for the generator's new output
   location (both describe `ProceduralCompositionGenerator`) — follows Step 11's decision.
3. Review and update where wording changed: `FAC-012` (`faction.yaml`, composition-level
   `faction_tension_overrides` — present only on the running side in 8 of 9 pairs, so the
   reconciliation changes which worlds exercise it), `SUB-390` (the "both real compilation paths"
   framing this ticket collapses), `INFRA-256`/`INFRA-257` (`information_source_profiles` /
   `pending_information_responses`, running-side-only; their `test_path`s include the repointed
   `tests/unit/worldassembly/test_assembly.py`).
4. `INFRA-373` pins `TVD(sandbox_world, dungeon_crawl) == 0.23161981243456373` at seed 42. It
   resolves `dungeon_crawl` through `WorldRepository`, and **this ticket edits no `data/worlds/`
   content**, so it should be untouched — run its test once to confirm, and leave the anchor alone.
   If it moves, that is evidence this ticket touched content it must not have.
5. `docs/content/pipeline_contract.md:34` — the `world_compositions_dir` |
   `data/content/world_compositions/` table row must reflect the retirement.

**Do NOT touch:** `SUBSTRATE-NEW-001` and `INFRA-187` — both are P0 with `test_path: None`, a
pre-existing ledger violation reported by the investigation. Filling them is **not** this ticket's
obligation; note them, do not fix them here. State them in the ticket as **reported, not fixed**, with
the ticket that would own them left unfiled-or-filed separately, so the **Parity phase does not read
them as this ticket's debt** and block on a gap that predates it. `INFRA-373` is likewise listed as a
**tripwire that must not move**, not as an entry to update. Do not hand-edit `docs/mechanics/content_usage_matrix.md`
(generated — see Step 10). Prefer `parity_ledger_writer.py` over a full-file rewrite and check
`git diff --stat` before committing.

**Verify:** `make parity-index-check`; `pytest tests/unit/rendering/test_variants.py -q` (the
`INFRA-373` tripwire).

---

### Step 15 — Full scoped regression

**Files:** none.

**Change:** Run `test_plan.md`'s five scoped commands plus the new guards, all green:
```
pytest tests/integration/worldassembly/ tests/unit/worldassembly/ -q
pytest tests/integration/scenarios/ -q
pytest tests/unit/content/ tests/integration/content/ tests/tools/test_content_inventory.py -q
pytest tests/unit/worldgeneration/ -q
pytest tests/unit/worldbuilding/ tests/integration/campaigns/ tests/unit/domains/campaigns/test_campaign_orchestrator.py -q
pytest tests/architecture/test_world_definition_single_source.py -q
pytest tests/unit/rendering/test_variants.py -q
```
Never `pytest tests/`.

**Do NOT touch:** nothing. If a test fails, fix the cause; do not relax an assertion to go green.

**Verify:** all seven commands green, plus `git diff` empty over the six out-of-reach test sites.

---

## Resolved Decisions

Decisions that were open while this plan was drafted and have since been ruled on. They are **not
historical context** — Step 3's clause wording and Step 11's whole design rest on what follows, and
scope guard #10 is what keeps it from being re-opened.

### UQ-1 — RESOLVED 2026-10-04 by the rule owner: the generator writes the source definition (Option A)

Was: *where do generated compositions land?* (Gap 1, `src/worldgeneration/generator.py:383,536`.) It
blocked Step 11 and therefore Step 12 and AC-1/AC-9.

**Ruling (the rule owner's reasoning, cited not restated):** *"authored" names the FILE'S ROLE, not
who wrote the bytes*, so **Option A is conformant** — the generator may write
`data/worlds/<id>/world.yaml` directly with a provenance marker. The ADR clause splits the
record-of-truth file from the derived projection, and each is defined by an **obligation, not by
authorship**: a projection must equal a fresh derivation from other committed inputs, so it may never
be edited independently; the definition file carries no such obligation — it is what everything else
derives from. Authorship plays no part in either definition.

**The condition attached to the ruling.** Once the generator writes `world.yaml`, that file **is** the
definition; the generator acted as a one-time author, not a continuing projection. If the design ever
expects `world.yaml` to be regenerable from a seed and params stored elsewhere, those params become
the real definition and `world.yaml` degrades into a projection of them — re-creating a second
definition location, i.e. Option C's problem by another route. The three hard constraints this imposes
are implemented in Step 11:
1. the provenance marker records **history only** (generator, version, seed, params) as a fact about
   origin;
2. **no check may assert `world.yaml == generate(marker)`** — that would convert the marker into a
   re-derivation obligation and make `world.yaml` a projection;
3. nothing outside `data/worlds/<id>/` may hold generation inputs as a definition.

**Consequences recorded elsewhere in this plan:**
- The ADR clause's first sentence was **revised** with this ruling — Step 3 now uses *"`world.yaml`
  is the source definition, whether written by hand or by a generator; once written it is edited, not
  regenerated"*, superseding the "authored definition" wording quoted in the ticket's BLOCKER
  section. The rest of the clause is unchanged.
- Constraint 2 is why Step 11's test list deliberately contains **no** re-derivation test, and why the
  AC-9 row of the Acceptance Criteria Map says so explicitly.
- Option C is closed as unnecessary (authorship is irrelevant to the split); Option B stays closed by
  measurement (`list_worlds()` indexes direct children only).
- Three sub-questions were returned as **engineering-only** and are decided inside Step 11, not
  escalated: `list_worlds()` does not distinguish generated worlds (the marker suffices);
  `generate()` does also run resolve, so the new world has its `resolved/` sibling; single-writer
  discipline on the authored side is enforced by refusing to overwrite an existing `world.yaml`.

### Implementer flag — the provenance marker must be a declared typed field

Not a style preference, and it fails late if missed: `WorldCompositionSpec.model_config` is
`ConfigDict(frozen=True, extra="forbid")` (`src/worldassembly/schema.py:23`), so a plain comment or a
loose YAML key will make **every generated file fail validation** after the code looks finished. Step
11 therefore adds a frozen `GenerationProvenanceSpec` plus an **optional** `generation_provenance`
field. Optional matters twice: all 24 existing `data/worlds/*/world.yaml` files stay valid, and
because `handle_resolve` dumps with `exclude_none=True` (`src/worldbuilding/cli.py:184`) the new field
cannot perturb any existing `resolved/` snapshot — which it must not, since Step 2's guard 3
byte-compares those. **Do not overload `generation_seed`** (`src/worldassembly/schema.py:38`) as the
marker: it is the resolver's determinism seed, not origin history.

## Scope Guards

Named specifically, from the ticket's Out of Scope and the investigation's anti-drift hazards:

1. **`data/worlds/dungeon_crawl/` is not edited by this ticket.** `danger_scale` and the module set
   are owned by `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`. Do not
   carry the catalog's `2` forward as authoritative, do not carry `4` forward as confirmed-correct,
   and do not resolve it with a one-line assertion edit from `2` to `4`.
2. **No `resolved/` snapshot is regenerated as a convenience.** Not for all 24 worlds, not for
   `dungeon_crawl`. That rewrites compiled artifacts for 15 worlds this ticket never touches and
   churns determinism fingerprints across unrelated tests. If Step 2's guard 3 finds a stale or
   non-deterministic projection, **file a finding ticket**.
3. **The six out-of-reach tests in `test_real_content_world_compositions.py`** (`:171`, `:188`,
   `:205`, `:224`, `:265`, `:300`) are byte-unchanged. They build synthetic specs / a synthetic
   `world_id` (`"pack_test_world"`) / generated ids, and the ADR does not reach them.
4. **The directory is not deleted before the generator stops writing to it** (Step 11 → Step 12).
5. **`data/worlds/` is not reorganized.** Option B was measured invisible to `list_worlds()`;
   changing the repository indexer is a different ticket.
6. **ADR §2's `resolved/compile_report.json` vs. the tree's `world_compile_report.json`** naming
   drift stays unfixed — real, pre-existing, out of scope.
7. **The authoritative location is stated exactly once**, in the ADR. Bible 06 and
   `content_authoring.md` cite it and must not restate the path or the freshness mechanics. No new
   Rule under `docs/world_rules/`.
8. **No expansion into `build_scenario_state()` / `ArenaInjector` / `V2EngineManager`** spawn paths,
   and no Campaign entity-spawn logic (closed in
   `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`).
9. **The two P0 ledger entries with `test_path: None`** (`SUBSTRATE-NEW-001`, `INFRA-187`) are
   reported, not fixed.
10. **The generator's output location is settled (Option A) and is not re-litigated at line 536.**
    Equally, the ruling's condition is not to be softened in code: no re-derivation check, no
    generation inputs stored as a definition outside `data/worlds/<id>/`, no overwrite of an existing
    `world.yaml`.
11. **`docs/archive/`, `docs/audits/`, `docs/brainstorm/`,
    `docs/plans/world_generation_organic_terrain_epic.md`** are frozen historical records — not
    edited, and excluded from the docs guard.
12. **`docs/mechanics/content_usage_matrix.md` is generated**, never hand-edited.
13. Two test-architecture questions are **routed out, not answered here**: whether the repointed
    named-world tests now duplicate existing coverage, and whether the directory-shaped authoritative
    layout should change how they load input. Route to `test-architecture-reviewer`; do not merge or
    move tests on this ticket's authority.

## Dependency Map

- **Step 1 → Step 2** (guard 3 needs the extracted helper).
- **Step 2 must precede any `data/` or test change**, and must land **in its own commit** — it has to
  be observed red on the untouched tree, and the red state has to be reconstructible from git history
  rather than only from pasted prose (review V5). This is the rule owner's sequencing advice: run the
  agreement check across every composition world before anything is re-applied.
- **Step 3 → Steps 4, 5, 6** (the ADR sentence must exist before the others cite it and before the
  guard checks for it).
- **Steps 7, 8, 9, 10 are independent of one another** and can be done in any order after Step 2.
- **HARD ordering *inside* Step 9: 9.1 (flip the resolver default) → 9.2 (drop the Campaign
  override).** Not list position — a real constraint (review V4). Reversed, Campaign silently falls
  back to the retired flat directory and runs the 6-module `frontier_living_world` instead of the
  7-module one, **and Step 9's verify command stays green** because no existing scenario test carries
  a module-count oracle. Step 9.4's new content-oracle assertion is what makes that regression
  detectable at all; the ordering is what stops it happening.
- **Step 11 is unblocked** (UQ-1 resolved — Option A). It depends on **Step 1** (it calls the
  extracted resolve helper to write the new world's `resolved/` sibling) and is otherwise independent
  of Steps 7-10.
- **Step 12 depends on Steps 7, 8, 9, 10, 11** — every reader and the single writer must be off the
  directory first.
- **Step 13 independent** (documentation; can run any time after Step 2).
- **Step 14 after Steps 11 and 12** (its `v2_evidence` describes the settled end state).
- **Step 15 last.**

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC-1 — one authoritative source per composition; catalog dir empty/removed | 12 (with 7-11 as prerequisites) | `test_world_id_resolves_to_exactly_one_definition`, `test_no_source_outside_data_worlds_defines_a_known_world_id`, `test_catalog_world_compositions_directory_is_absent` |
| AC-2 — every `ScenarioSetupResolver` caller on the unified layout, verified by a real test | 9 | `test_scenario_setup_resolver_default_compositions_dir_is_data_worlds`, `test_campaign_orchestrator_uses_resolver_default_not_an_override`, `tests/integration/scenarios/`, `tests/integration/campaigns/` |
| AC-3 — ONE recorded evidenced authority decision + explicit `danger_scale` call-out | 13 (recorded in the ticket), 3 (the ADR sentence it rests on) | not testable — prose, grounded in the investigation's three measurements (24/24 valid; 15 running-only vs 0 catalog-only; zero catalog-only keys in 9/9) |
| AC-4 — whole test surface resolved; repoint-or-delete decision recorded with reasoning | 7, 8 (+10 for the content-layer tests) | `pytest tests/integration/worldassembly/ tests/unit/worldassembly/ tests/integration/content/ -q`; `git diff` empty on the six out-of-reach sites |
| AC-5 — `danger_scale`: carry neither value forward; no test/doc asserts either as intended design | 7 (de-assert `:437`/`:452` + docstring), 12 (the contradiction guard) | `test_no_test_contradicts_the_authoritative_danger_scale`; oracle stays `unresolved` for this ticket (correct, not a gap) |
| AC-6 — one `world_id` → one module set, **and** committed `resolved/` equals a fresh resolve; must fail on today's content first | 1, 2 | the three guards in `tests/architecture/test_world_definition_single_source.py`, guard 3 being a **full fresh-resolve equality** (a fingerprint cannot detect a hand-edited projection); red run recorded in Implementation Notes as the mandatory negative control |
| AC-7 — written measurement-validity assessment, survivals stated as survivals | 13 | not testable — written section with a stated sweep bound |
| AC-8 — ADR (2 sentences) + Bible 06 invariant + `content_authoring.md` 4 sites, all agreeing | 3, 4, 5 | `test_authoritative_world_location_stated_once` |
| AC-9 — nothing writes into the retired directory; a generation run does not recreate it | 11, 12 | `test_generation_run_does_not_create_data_content_world_compositions` (the explicit-absence test), plus the exact-output-path, provenance-history and refuse-to-overwrite tests. **No `world.yaml == generate(marker)` test** — forbidden by the ruling's condition |
| AC-10 — parity ledger entry added/updated with AC-6's check as `test_path` | 14 | `make parity-index-check`; `SUB-394` carries the guard node id |
| (ticket's "full scoped regression" bullet) | 15 | the seven scoped commands |

## Unresolved Questions

None.

See "Resolved Decisions" above for UQ-1 (the generator's output location), which was open when this
plan was first drafted and was ruled on by the rule owner before implementation began.

## Anti-Drift Notes

- The known scope-creep direction on this ticket is *"while I'm in this file"*. The six synthetic
  tests in `test_real_content_world_compositions.py` and `data/worlds/dungeon_crawl/world.yaml` are
  the two places that will feel most tempting and are the two most explicitly forbidden.
- `tests/tools/test_content_inventory.py` **degrades silently**: after deletion both sides of its
  equality become `0` and it passes while asserting nothing. Treat a green there as uninformative
  unless Step 10's non-zero assertion landed.
- `tests/integration/content/test_expansion_gate.py:248` raises **`IndexError`**, not an assertion
  failure, on an empty directory. That symptom means step ordering, not a new bug.
- The direction of this ticket's two biggest corrections is **opposite**: the content work shrank
  from 8 decisions to 1, the test work grew ~4.5x. Do not let the "it's just one decision" framing
  shrink the test and docs work.
- `make world-validate` / `make world-compile` already operate on `data/worlds/` via
  `WorldRepository` (`Makefile:133-140`). In `content_authoring.md` §4, only the file-location
  sentence is wrong — do not "fix" the workflow block.
- The "`data/content/world_compositions/` is the anomaly" wording originates at
  `src/domains/campaigns/orchestrator.py:178`, **not** in the ADR. The conclusion holds on three
  independent grounds; only the citation was wrong. Do not reintroduce the mis-attribution when
  rewriting that comment.
- Finalize note (not an implementation step): a duplicate copy of this ticket still exists at
  `agent-working/tickets/todos/TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION.md`; it must be
  removed before the Verify/done-checker gate, per the folder-cleanup rule.

## Deviations

Recorded during Implement. Nothing here was changed silently.

1. **Step 1 — the helper takes the repositories, not a catalog root.** As planned, the core helper
   takes an already-validated `WorldCompositionSpec` (advisory A1 honoured). But repository loading
   was split out into `load_content_repositories()`, so the signature is
   `resolve_composition(composition, catalog, module_repo)`. Forced by Step 11: the generator
   already holds the `WorldModuleRepository` it selected modules from, and re-loading one from disk
   inside the helper would both discard it and make the generator's own unit tests unable to supply
   modules at all. `resolve_composition_file()` is the path-loading wrapper the CLI and the guard
   use. The anti-drift property the step exists for is unaffected — there is still exactly one
   renderer (`render_resolved_world_yaml`).

2. **Step 2 — guard 3 is not marked `@pytest.mark.slow`.** The step permits the marker "if runtime
   demands"; measured, all three guards together run in ~10s for the full 24-world corpus, and a
   `slow`-marked guard is deselected by the PR-blocking job. No fingerprint fast path was added,
   for the same reason. The walk is bounded to `data/` **and** `content/` (a second real content
   root at the repository top level), both excluding `docs/`.

3. **Step 4 — placed as a numbered section, `## 11`, after §10.** The step says "its own short
   sibling note, not inside §7's ladder". An unnumbered block between §7 and §8 would have read as
   section-less, and inserting a numbered section there would have renumbered §8-§10 and broken
   external citations to them. Placing it after §10 — itself the chapter's precedent sibling gate —
   satisfies the intent and renumbers nothing. The Step 6 guard checks the enclosing section is not
   §7, so the placement is pinned.

4. **Step 7 — two extra edits in files the step already names.**
   `test_real_composition_normalization_preserves_perspectives` (`tests/unit/worldassembly/test_assembly.py`)
   needed its count 6 → 7 **and** its mixed-shorthand-conflict case now sets `mixed["modules"]`
   explicitly: the authoritative definition carries only the structured form, so the
   both-forms-present conflict the test asserts could no longer arise and `pytest.raises` was
   DID-NOT-RAISE. Neither was in the step's measured delta list.

5. **Step 8 — Gates 08 and 11 needed a `schema_version` filter.** Iterating
   `data/worlds/*/world.yaml` would otherwise validate `worldspec.v1` worlds against
   `WorldCompositionSpec`. All 24 worlds are compositions today so nothing fails yet; the filter
   plus a non-zero assertion keeps Gate 08 measuring compositions rather than breaking on the 25th
   world. Gate 11 picks the first composition rather than the first file.

6. **Step 10 — one extra test updated.** `tests/tools/test_content_inventory.py::test_all_categories_present`
   also pinned the now-absent `"World compositions (generated)"` key; the step named only `:46-49`.

7. **Step 11 — three things the step's test list did not anticipate.**
   (a) `_make_repo` in `test_composition_generator.py` and `test_seed_params.py` returned a
   `MagicMock`, which a real resolve cannot traverse. It is now an in-memory-populated real
   `WorldModuleRepository` — no file I/O and no mock, which is strictly better than what it
   replaced.
   (b) `generation_provenance.generated_at` makes the authored YAML no longer byte-identical across
   runs, contradicting `generator_contract.md`'s determinism clause and
   `test_two_calls_produce_identical_output`. Resolved exactly as this repo already resolves the
   same problem for `provenance_manifest.created_at`: the timestamp is legitimate provenance
   outside the artifact's identity, so the test and the doc exclude that one field. The timestamp
   was not deleted to make a comparison easy.
   (c) `test_no_bounds_no_default_leaves_absent` now observes the same fact through the resolve
   (`AssemblyParameterError` naming the absent param), because leaving a required param absent is
   precisely what makes the composition unassemblable.
   One test was added beyond the step's list, `test_generated_world_has_its_resolved_sibling`,
   because item 4's whole justification is that `WorldRepository.load_world()` refuses a world with
   no snapshot and nothing else asserted the snapshot exists.
   Also: the marker is popped in `WorldCompositionNormalizer`, since
   `NormalizedWorldComposition` is `extra="forbid"` too and origin history is not a compilation
   input — the same treatment `pack_refs` already gets. The step did not mention this, and without
   it every generated composition fails normalization.

8. **Step 14 — `SUB-394` was validated through `parity_ledger_writer.validate_entry()` but appended
   by hand.** `write_entry()` re-dumps the entire shard, which would have produced a ~5000-line
   diff on `substrate.yaml`. The step itself says to check `git diff --stat`; the hand-append keeps
   it at 40 lines, the validator still gated the entry, and `tools/parity_index.py build` was run
   so the derived index reports FRESH. `SUB-390`, `FAC-012`, `INFRA-256` and `INFRA-257` were
   reviewed and found not stale, so item 3 produced no edits.

9. **Step 15 — NOT satisfied. Blocking conflict between Step 11 item 4 and Scope Guard 3.**
   `generate()` running the resolve breaks
   `test_real_content_world_compositions.py::test_generated_composition_is_valid_worldcompositionspec`
   and `::test_generated_composition_determinism` — two of the six tests Scope Guard 3 names
   byte-unchanged. Both `monkeypatch.chdir(tmp_path)` and pass no catalog, so the cwd-relative
   `CatalogRepository("data/content")` load inside `generate()` comes back empty and the resolver
   raises on a region the real module references. Step 11 enumerated only
   `tests/unit/worldgeneration/test_composition_generator.py` as the generator's test surface and
   did not notice these two integration tests also call `generate()`. The two tests were left
   untouched; four options are recorded in the ticket's Implementation Notes for whoever owns the
   scope decision.

### Deviation 10 — the generator's catalog is INJECTED (coordinator scope decision, supersedes my option (1))

My Implement-phase report framed the two failing `test_generated_composition_*` tests as an
overbroad Scope Guard 3 and recommended relaxing it. **That reading was one level too shallow and
the coordinator's decision overrides it.** Checked and confirmed:
`git show c86fa3a21:src/worldgeneration/generator.py | grep -nE "CatalogRepository\("` returns
**nothing** — there was no catalog construction in that module before this ticket. The
`CatalogRepository("data/content")` at `:565` was introduced by **this diff**, as part of Step 11
item 4. So the defect was a **cwd-dependent hidden dependency added inside a library function**,
not a guard that was too broad. The two tests `monkeypatch.chdir(tmp_path)` to isolate their
output, which is correct, and they caught a real design problem.

Applied instead:

1. `ProceduralCompositionGenerator.generate()` takes `catalog_repo: CatalogRepository` as a
   required parameter and the in-function construction is gone. **Deliberately no default** — a
   default would re-introduce the same cwd dependency, just less visibly. This matches the
   convention the module already establishes at `src/worldgeneration/generator.py:65`
   (`WorldProceduralGenerator.__init__(self, catalog_repo, module_repo)`), and the comment at
   `:148` already describes that class as "constructor-injectable with ANY CatalogRepository" — my
   `:565` construction was the only thing in the module violating its own convention.
2. The two tests changed **minimally**: the `repos` fixture already loads the real catalog before
   any chdir, and both tests were discarding it with `_, mod = repos`. They now do
   `cat, mod = repos` and pass `cat` through. `monkeypatch.chdir(tmp_path)` is kept — it is doing
   its job. `test_generated_composition_determinism` additionally excludes
   `generation_provenance.generated_at` from its comparison, the same already-recorded treatment
   deviation 7(b) applies to the unit-level determinism test.
3. `src/worldbuilding/cli.py`'s `generate` handler passes the catalog it now loads via
   `load_content_repositories()` — the CLI is the boundary where resolving content paths against
   the process cwd is legitimate. Its two now-unused imports (`ContentPathConfig`,
   `WorldModuleRepository`) were dropped.
4. The generator's own unit tests gained an explicit `_make_catalog()` returning a loaded, empty
   `CatalogRepository` pointed at a nonexistent directory — explicit rather than cwd-relative, for
   the same reason.

**Scope Guard 3 was NOT weakened on its own axis.** Its rationale is the ADR's reach over *which
file defines a world*, and that still holds: the other four named tests (`:171`, `:188`, `:205`,
`:224`) remain byte-unchanged. These two changed because Step 11 legitimately changes
`generate()`'s **signature**, which is Step 11's own surface, not the ADR's.

### Deviation 11 — a REAL generator defect surfaced by the injection, and NOT fixed here

With the real catalog injected, the two tests fail for a different and deeper reason:

```
ValueError: Duplicate region ID collision 'hometown' detected during assembly merge.
src/worldassembly/resolver.py:359
```

Measured, not inferred:

- `data/content/world_modules/frontier_village_core.yaml` and `trading_company_hub.yaml` **both
  declare region id `hometown`**.
- Today's `ModuleScorer` ranks them **1 and 2** for this intent
  (`generated_frontier_3_42`, seed 42, `settlement_style="frontier"`), so the generator selects
  both.
- The generator emits every `ModuleRefSpec` with `namespace=None` and never sets one. Its Rule 5
  fail-fast guards duplicate **`provides`** strings only, not duplicate region ids.
- The hand-authored `data/worlds/urban_political/world.yaml` composes the same two modules and
  resolves the collision with `namespace: trading` on `trading_company_hub` — exactly as
  `test_urban_political_composition`'s docstring states.
- The **committed** `data/worlds/generated_frontier_3_42/world.yaml`, authored by the generator
  *before* this ticket, contains `frontier_village_core` but **not** `trading_company_hub`. So the
  module corpus and/or the scorer moved since that world was generated, and today's selection
  picks a colliding pair.

**This is a pre-existing latent defect, newly surfaced rather than caused.** The selection code is
byte-unchanged by this diff — `git diff c86fa3a21 HEAD -- src/worldgeneration/generator.py`
contains no change to `ModuleScorer` use, the ranking, `selected_ids`, `BUDGET`, or Rule 5; the
only matching diff lines are docstring text. It was invisible because nothing ever resolved what
the generator authored. Step 11 item 4 made it visible, which is precisely what that item exists
for.

**Not fixed here, because every available fix is a world-semantics decision I do not own.** The
options are (a) auto-namespace colliding modules, (b) extend Rule 5 to reject region-id collisions
and fall through to the next candidate, or (c) filter colliding candidates during selection. All
three change *which world a given intent generates* — region ids, hence world content — and (a)
changes region identity itself. Per this repo's rule-owner ordering, that is routed, not decided by
the implementer. **The two tests therefore remain red, and the "Full scoped regression" AC stays
unchecked.**
