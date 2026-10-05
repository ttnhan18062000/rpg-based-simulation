---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, audit]
---

# import-linter Evaluation (M5, report only)

Decision record for `TCK-20261004-IMPORT-LINTER-EVALUATION`. Nothing in the repository changed to produce it:
no dependency, CI, test, `pyproject.toml` or `src/` edit. Everything ran in a scratch copy outside the repo.

## Recommendation: ADD, with a narrow replace

1. **Add** import-linter for what the tests do not cover: the layer order (a `layers` contract built from
   `codebase/structure/package_registry.jsonl`) and the loopholes in Section 4. It would need an `ignore_imports`
   baseline of 99 to 113 current violations (Section 3) before it can gate anything.
2. **Replace, only with the owner's and the testing planner's agreement**, the 8 rules whose contract is equivalent
   (Section 5, class E). One of them, `test_hot_path_does_not_import_heavy_analyzers`, is a no-op today; the contract
   catches the 3 real violations it was written for.
3. **Keep** the other 42 rules as tests. 20 lose detail in a contract (imported names, pins, keywords) and 22
   cannot be written as one (text, name or stdlib-module rules). They are also candidates for ast-grep, listed in
   Section 6.
4. **Dependency on a `src/` decision:** import-linter covers the 20 namespace packages only if each is listed as
   its own `root_packages` entry (`src.core`, ...). That works without any `__init__.py`. One directory stays
   uncovered, `src/engine/intent` (no `__init__.py` inside a regular package); adding the file is a `src/` edit and
   is an M7 / rpg decision, not part of this batch.
5. Never as a second copy (roadmap Section 4): adoption means retiring the class E tests in the same change.

## 1. Reproduction

- Versions: import-linter 2.15, grimp 3.17 (from `uvx`), Python 3.13 (`.venv`).
- Scratch tree: `git archive c4304a7a3dfcbb3e03aed80b3a0b732de1924425 src tests codebase pyproject.toml`, not the
  shared working tree. Every injected violation is made in a fresh copy of that tree.
- Command (each run, one at a time, 2 GB cap):
  `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 uvx --from import-linter==2.15 lint-imports --config <scratch>/.importlinter`
  Existing tests ran in the scratch copy with `PYTHONPATH=<scratch> .venv/bin/python -m pytest <test id> -p no:cacheprovider -o addopts=`,
  because they locate `src/` by a path relative to the working directory.
- Config shape: `root_packages` = `src` plus the 20 namespace packages as `src.<pkg>`; `include_external_packages = True`;
  contracts in Appendix A.
- Cost: 774 files, 2,309 dependencies; 0.4 s and 47 MB peak for the whole contract set (a cold `uvx` install adds about 2 s).

## 2. Namespace packages, measured

20 of the 36 top-level packages have no `__init__.py`: actions, ai, api, certification, content, content_semantics,
core, domains, logging, observability, perf, strategy, systems, testing, town, views, world, worldassembly,
worldgeneration, worldmodules.

| `root_packages` | Modules seen | Result |
|---|---|---|
| `src` | 215 of 744 files | the 20 packages and 1 file of `engine` are absent |
| `src.core`, `src.api`, `src.perf`, `src.certification`, `src.content_semantics` only | 114 | covers those 5 |
| `src` + all 20 `src.<pkg>` | 774 (744 files plus package nodes) | all files covered except `src/engine/intent` (1 file) |
| `src` only, with a contract naming `src.core` | error | `Module 'src.core' does not exist.` Loud, not silent |

`random` as a `root_packages` entry fails: `'random' is a module, not a package. root_packages should only contain packages`. `PIL` was not tried (not installed in the `uvx` environment), so the rendering image-dependency contract below omits it.

## 3. Contracts, the 2 x 2 flag matrix, and the baseline

Violations on `src/` at the scratch commit, per contract and per configuration. `K` = kept, `B` = broken, then the
count of import lines reported. Columns: `allow_indirect_imports` true or false, crossed with
`exclude_type_checking_imports` false or true (a root-level option, not per contract). Contracts carry `ignore_imports`
that reproduce each test's pins; Appendix A.

| contract | ind, TC counted | ind, TC excl. | direct-only, TC counted | direct-only, TC excl. |
|---|---|---|---|---|
| `c01_core_not_domains` | B 4 | K 0 | B 4 | K 0 |
| `c02_obs_engine_via_kernel` | K 0 | K 0 | B 11 | B 7 |
| `c03_obs_domains_systems_allowlist` | K 0 | K 0 | B 51 | B 43 |
| `c04_domains_not_obs_pinned` | B 2 | K 0 | B 8 | B 6 |
| `c05_systems_not_engine_pinned` | K 0 | K 0 | B 12 | B 8 |
| `c06_hot_path_not_heavy` | B 3 | B 3 | B 14 | B 15 |
| `c07_api_not_core_state` | K 0 | K 0 | B 63 | B 67 |
| `c08_domain_models_pure` | B 1 | K 0 | B 32 | B 3 |
| `c09_admission_governor` | K 0 | K 0 | K 0 | K 0 |
| `c11_rendering_pure` | K 0 | K 0 | K 0 | K 0 |
| `c12_entities_no_catalog` | K 0 | K 0 | K 0 | K 0 |
| `c13_campaign_state` | K 0 | K 0 | B 5 | B 2 |

Reading it:
- The existing tests are direct-only, so `allow_indirect_imports = true` is required to match them. With it false,
  the same contracts report chains (`c07` 63, `c03` 51).
- `exclude_type_checking_imports` is **all-or-nothing per config**, and the tests differ: the belief, fame, fidelity,
  `phase18` and `api` guard rules skip `TYPE_CHECKING` imports; `admission_control`, `campaign_state`, the rendering
  and entity rules and `phase2_determinism` do not. A single config therefore cannot match every test. Matching rows
  above: `c01`, `c04`, `c08` are broken only with TC counted (4, 2 and 1 `TYPE_CHECKING` imports), which is why the
  tests pass today.
- `c06` stays broken in every configuration: `src.engine.kernel` imports `src.observability.reporting.artifact_repository`,
  `.reporting.metric_recorder`, `.cognition.recorder` and `.cognition.decision_trace_writer` inside functions (function-local
  imports, lines 149, 304, 305, 316 and 1241; grimp counts them).
- `unmatched_ignore_imports_alerting` found one stale allowlist entry: the phase18 test allows
  `observability/cognition/recorder.py` to import domains/systems, but that file no longer does
  (`No matches for ignored import src.observability.cognition.recorder -> src.domains.**`). The test cannot see this;
  import-linter warns (or fails, by default).
- A `layers` contract from the registry (consumer, simulation-systems, engine, domain, content-pipeline, foundation, top
  to bottom) is **broken: 113 import lines with TC counted, 99 with it excluded**. That is the baseline an adoption
  would have to carry in `ignore_imports`, and it matches audit finding 1 (the real graph is not the D14 layer model).

## 4. Injected-violation parity

One violation injected per rule, in three forms (module level, function-local, under `if TYPE_CHECKING:`) and,
where the test has a known blind spot, a fourth form. "test" is the existing test's result in the injected tree
(FAIL = it caught the violation); the two contract columns are `allow_indirect_imports = true` with TC counted and
excluded, `caught` meaning the violation count rose from the baseline in Section 3.

| contract | injected | test | contract (TC counted) | contract (TC excl.) |
|---|---|---|---|---|
| `c01_core_not_domains` | top: `import src.domains.campaigns.state` | FAIL | caught (4→5) | caught (0→1) |
| `c01_core_not_domains` | local: `import src.domains.campaigns.state` | FAIL | caught (4→5) | caught (0→1) |
| `c01_core_not_domains` | tc: `import src.domains.campaigns.state` | PASS | caught (4→5) | missed (0→0) |
| `c02_obs_engine_via_kernel` | top: `import src.engine.cadence` | FAIL | caught (0→1) | caught (0→1) |
| `c02_obs_engine_via_kernel` | local: `import src.engine.cadence` | FAIL | caught (0→1) | caught (0→1) |
| `c02_obs_engine_via_kernel` | tc: `import src.engine.cadence` | PASS | caught (0→1) | missed (0→0) |
| `c03_obs_domains_systems_allowlist` | top: `import src.domains.fame.model` | FAIL | caught (0→1) | caught (0→1) |
| `c03_obs_domains_systems_allowlist` | local: `import src.domains.fame.model` | FAIL | caught (0→1) | caught (0→1) |
| `c03_obs_domains_systems_allowlist` | tc: `import src.domains.fame.model` | PASS | caught (0→1) | missed (0→0) |
| `c04_domains_not_obs_pinned` | top: `import src.observability.events` | PASS | caught (2→3) | caught (0→1) |
| `c04_domains_not_obs_pinned` | local: `import src.observability.events` | PASS | caught (2→3) | caught (0→1) |
| `c04_domains_not_obs_pinned` | tc: `import src.observability.events` | PASS | caught (2→3) | missed (0→0) |
| `c04_domains_not_obs_pinned` | top: `from src.observability.events import SimulationEvent` | FAIL | caught (2→3) | caught (0→1) |
| `c05_systems_not_engine_pinned` | top: `import src.engine.cadence` | PASS | caught (0→1) | caught (0→1) |
| `c05_systems_not_engine_pinned` | local: `import src.engine.cadence` | PASS | caught (0→1) | caught (0→1) |
| `c05_systems_not_engine_pinned` | tc: `import src.engine.cadence` | PASS | caught (0→1) | missed (0→0) |
| `c05_systems_not_engine_pinned` | top: `from src.engine.cadence import should_run` | FAIL | caught (0→1) | caught (0→1) |
| `c06_hot_path_not_heavy` | top: `import src.observability.reporting` | PASS | caught (3→4) | caught (3→4) |
| `c06_hot_path_not_heavy` | local: `import src.observability.reporting` | PASS | caught (3→4) | caught (3→4) |
| `c06_hot_path_not_heavy` | tc: `import src.observability.reporting` | PASS | caught (3→4) | missed (3→3) |
| `c07_api_not_core_state` | top: `from src.core.state import AuthoritativeState` | FAIL | caught (0→1) | caught (0→1) |
| `c07_api_not_core_state` | local: `from src.core.state import AuthoritativeState` | FAIL | caught (0→1) | caught (0→1) |
| `c07_api_not_core_state` | tc: `from src.core.state import AuthoritativeState` | PASS | caught (0→1) | missed (0→0) |
| `c07_api_not_core_state` | top: `from src.core import state as _s` | PASS | caught (0→1) | caught (0→1) |
| `c08_domain_models_pure` | top: `import src.engine.cadence` | FAIL | caught (1→2) | caught (0→1) |
| `c08_domain_models_pure` | local: `import src.engine.cadence` | FAIL | caught (1→2) | caught (0→1) |
| `c08_domain_models_pure` | tc: `import src.engine.cadence` | FAIL | caught (1→2) | missed (0→0) |
| `c08_domain_models_pure` | top: `from src.core import state as _s` | PASS | caught (1→2) | caught (0→1) |
| `c09_admission_governor` | top: `from src.engine.governor import GovernorPolicy` | FAIL | caught (0→1) | caught (0→1) |
| `c09_admission_governor` | local: `from src.engine.governor import GovernorPolicy` | FAIL | caught (0→1) | caught (0→1) |
| `c09_admission_governor` | tc: `from src.engine.governor import GovernorPolicy` | FAIL | caught (0→1) | missed (0→0) |
| `c09_admission_governor` | top: `import src.engine.governor` | PASS | caught (0→1) | caught (0→1) |
| `c09_admission_governor` | top: `from src.engine import governor as _g` | PASS | caught (0→1) | caught (0→1) |
| `c10_random_ban` | top: `import random` | FAIL | not expressible | not expressible |
| `c10_random_ban` | local: `import random` | FAIL | not expressible | not expressible |
| `c11_rendering_pure` | top: `import src.rendering.render` | FAIL | caught (0→1) | caught (0→1) |
| `c11_rendering_pure` | local: `import src.rendering.render` | FAIL | caught (0→1) | caught (0→1) |
| `c11_rendering_pure` | tc: `import src.rendering.render` | FAIL | caught (0→1) | missed (0→0) |
| `c11_rendering_pure` | top: `from src.rendering import render as _r` | PASS | caught (0→1) | caught (0→1) |
| `c12_entities_no_catalog` | top: `from src.content.repository import CatalogRepository` | FAIL | caught (0→1) | caught (0→1) |
| `c12_entities_no_catalog` | local: `from src.content.repository import CatalogRepository` | FAIL | caught (0→1) | caught (0→1) |
| `c12_entities_no_catalog` | tc: `from src.content.repository import CatalogRepository` | FAIL | caught (0→1) | missed (0→0) |
| `c13_campaign_state` | top: `import src.engine.cadence` | FAIL | caught (0→1) | caught (0→1) |
| `c13_campaign_state` | local: `import src.engine.cadence` | FAIL | caught (0→1) | caught (0→1) |
| `c13_campaign_state` | tc: `import src.engine.cadence` | FAIL | caught (0→1) | missed (0→0) |

Findings:
- **Contract catches, test misses (loopholes):** plain `import src.observability.events` into `domains` and
  `import src.engine.cadence` into `systems` (their tests count `ImportFrom` only); `from src.core import state` into
  `api` routes and into the domain models (the tests match the module prefix `src.core.state` or the name
  `AuthoritativeState`); `import src.engine.governor` and `from src.engine import governor` into `admission_control`
  (`ImportFrom` of the exact module only); `from src.rendering import render` into `density.py` (the test checks
  `node.module`, not the imported name).
- **Test and contract agree** on top-level and function-local imports for every rule (function-local imports count in
  both, as in grimp). For `TYPE_CHECKING` they agree only when the config matches the test (above).
- **`test_hot_path_does_not_import_heavy_analyzers` is a no-op, confirmed.** `import src.observability.reporting` injected
  into `src/engine/kernel.py` leaves the test passing, while the contract's count rises 3 to 4. The test matches the bare
  prefix `observability.*`, which never occurs in real `src.observability.*` imports. The 3 existing violations in
  `kernel.py` are listed in Section 3. The finding goes to the testing planner as outbox Message 9; no test is edited.
- **Not measured:** relative imports. grimp resolves them and the `src.`-prefix tests do not match them; no injection of one was run.

## 5. The 50 rules, classified

The inventory was built by a read-only search (a subagent) and not re-verified rule by rule: its table has 50
rules in 29 test files, although the agent's summary said 53, and the brief said 41 rules in 31 files. 27 of the 50
were exercised in Section 4 (`c01` to `c13`: phase18 x5, phase19 hot path, api guard, belief/fame/fidelity x3,
admission, phase2 x10 (test side only, no contract can be written), rendering image-dependency x4, entities
contract, campaign state); the other 23 are classified from the inventory only.

- **E, equivalent (8):** core not domains; phase19 hot path (no-op today); belief, fame, fidelity model/deriver
  (3); admission control; campaign state; `visual_assets` (needs `visual_assets` added as a root package; not run).
- **L, expressible but loses detail (20):** observability to engine via `Kernel` only (imported name pinned);
  observability domains/systems allowlist (4 pinned name sets); domains to observability and systems to engine
  (exact per-name counts, stale-pin detection); the API read-model guard (names `AuthoritativeState`, `EntityState`);
  scenario resolver (keywords `telemetry`, `metrics`, ...); runtime contract, archetype factory, identity resolver
  (`CatalogRepository` by name); decision trace writer (text, partly vacuous); the rendering image-dependency x4
  (`PIL` is not a root package here) and the rendering `PillarScorer`/event-pipeline x6 (subclass ban lost).
- **N, not expressible (22):** the 10 `phase2_determinism` RNG rules (`random` is a stdlib module and cannot be a root
  package); `rng_hygiene` x2 (regex text; `numpy.random` is a submodule of an external package); `coming_of_age`
  (attribute `random.Random`); hot-path safety class-name text; rendering stdlib-only allowlist; modifier applicator
  keyword `tick`; catalog state builder x2 (text); world entity spawner x2 (required reference, column-0 text);
  `variants` required `compute_terrain_histogram` import; scenario lane exclusions (static reachability from tests).

## 6. Candidates for ast-grep rules (ticket 3 follow-ups; nothing changed)

Syntactic, single-file patterns that ast-grep can hold with path globs: `import random` / `from random import` per
package (the 10 `phase2` rules, plus the `rng_hygiene` regex, whose `^` anchor misses function-local imports);
`numpy.random`; `random.Random`; imports of a named symbol (`CatalogRepository`, `EntityGenerator`,
`CognitionDomain`, the five hot-path analyzer classes); the `V2EntityBuilder` column-0 rule. About 25 rules. ast-grep cannot
express cross-package reachability or the layer order; that stays with import-linter.

## 7. Open items for the owner

- Whether to add `src/engine/intent/__init__.py` (the one uncovered directory) and, more broadly, `__init__.py` to the
  20 namespace packages: a `src/` edit, M7 / rpg.
- The adoption ticket (to file if the owner agrees): the `layers` contract with a 99-line `ignore_imports` baseline, the
  loophole contracts, and the retirement of the 8 class E tests with the testing planner. Not started here.

**Answered 2026-10-05** (owner decision 2026-10-04, roadmap decision 20): no `__init__.py` is added to `src/`; the
20 `src.<pkg>` root entries are accepted and `src/engine/intent` stays uncovered. The adoption is advisory first
(`TCK-20261004-IMPORT-LINTER-ADOPTION`, config `codebase/structure/importlinter.toml`); against recommendation 5 it
retires **no** test (the testing planner's condition 1): contracts and tests run together until
`TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT`. Measured on `898c6f35a`: the `layers` baseline is 135 module
pairs (170 import lines), not 113; the same config at the evaluation's commit gives 134 pairs, so the evaluation's
own layers config (not preserved) differed.

## Appendix A: contract bodies (as run)

```ini
[importlinter:contract:c01_core_not_domains]
type = forbidden
source_modules =
    src.core
forbidden_modules =
    src.domains

[importlinter:contract:c02_obs_engine_via_kernel]
type = forbidden
source_modules =
    src.observability
forbidden_modules =
    src.engine
unmatched_ignore_imports_alerting = warn
ignore_imports =
    src.observability.** -> src.engine.kernel

[importlinter:contract:c03_obs_domains_systems_allowlist]
type = forbidden
source_modules =
    src.observability
forbidden_modules =
    src.domains
    src.systems
unmatched_ignore_imports_alerting = warn
ignore_imports =
    src.observability.event_extractor -> src.domains.**
    src.observability.event_extractor -> src.systems.**
    src.observability.event_shapers -> src.domains.**
    src.observability.event_shapers -> src.systems.**
    src.observability.cognition.recorder -> src.domains.**
    src.observability.cognition.recorder -> src.systems.**

[importlinter:contract:c04_domains_not_obs_pinned]
type = forbidden
source_modules =
    src.domains
forbidden_modules =
    src.observability
unmatched_ignore_imports_alerting = warn
ignore_imports =
    src.domains.campaigns.narrative_ledger -> src.observability.events
    src.domains.campaigns.orchestrator -> src.observability.events

[importlinter:contract:c05_systems_not_engine_pinned]
type = forbidden
source_modules =
    src.systems
forbidden_modules =
    src.engine
unmatched_ignore_imports_alerting = warn
ignore_imports =
    src.systems.strategic_systems.intelligence -> src.engine.policy
    src.systems.strategic_systems.intelligence -> src.engine.spatial_query
    src.systems.strategic_systems.intelligence -> src.engine.cadence
    src.systems.strategic_systems.intelligence -> src.engine.domain_logic
    src.systems.strategic_systems.intelligence -> src.engine.cognition
    src.systems.strategic_systems.detour -> src.engine.domain.lead_routing
    src.systems.strategic_systems.redirection -> src.engine.cadence
    src.systems.economy_systems.market -> src.engine.legality
    src.systems.world_systems.routine -> src.engine.legality

[importlinter:contract:c06_hot_path_not_heavy]
type = forbidden
source_modules =
    src.engine
    src.observability.config
    src.observability.event_extractor
    src.observability.event_recorder
forbidden_modules =
    src.observability.anomaly
    src.observability.cognition
    src.observability.reporting

[importlinter:contract:c07_api_not_core_state]
type = forbidden
source_modules =
    src.api.routes
    src.api.ws
    src.api.server
forbidden_modules =
    src.core.state

[importlinter:contract:c08_domain_models_pure]
type = forbidden
source_modules =
    src.domains.belief_institution.model
    src.domains.belief_institution.deriver
    src.domains.fame.model
    src.domains.fame.deriver
    src.domains.fidelity.model
    src.domains.fidelity.deriver
forbidden_modules =
    src.engine
    src.core.state

[importlinter:contract:c09_admission_governor]
type = forbidden
source_modules =
    src.api.admission_control
forbidden_modules =
    src.engine.governor
    src.engine.phase_governor

[importlinter:contract:c11_rendering_pure]
type = forbidden
source_modules =
    src.rendering.density
    src.rendering.variants
    src.rendering.grading
    src.rendering.shape
forbidden_modules =
    src.rendering.render
    src.rendering.incremental
    src.rendering.png_writer
    src.simulation_quality
    src.observability.events

[importlinter:contract:c12_entities_no_catalog]
type = forbidden
source_modules =
    src.entities.runtime_contract
forbidden_modules =
    src.content.repository

[importlinter:contract:c13_campaign_state]
type = forbidden
source_modules =
    src.domains.campaigns.state
forbidden_modules =
    src.engine
    src.systems
```
