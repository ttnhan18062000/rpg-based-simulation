---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE
artifact_type: investigation
tags: [world, engine]
---

# Investigation — TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE

Method, at main 3533fde71 (2026-10-26), `git grep` over tracked files outside `agent-working/`, `graphify-out/`, `docs/archive/`, `frontend/`.

## The four kinds, repo-wide (not per symbol)
- **K3 importlib / dynamic import.** The only dynamic-import sites in `src/` are `src/domains/feature_packs/loader.py:90` (`importlib.import_module(ep.class_path)`; the only manifest class_path in the repo is `content.packs.demo_escort_pack.generator:EscortDignitaryGenerator`) and, in `tools/`, `tools/test_architecture/rpg_gate_run.py:21` (its callers pass `tools.*` and `src.engine` spec names). No site can resolve any module below.
- **K4 phase table.** Every `run_phase("...")` name in `src/engine/pipeline.py` (action_routing ... town_resolution, guild_visit, quest_rewards, shop, blacksmith, contracts, ...) is backed by a live engine class; none names a deleted or dead class. The pipeline's own `src.systems` imports are `strategic`, `lifecycle`, `world_systems.generator` (EntityGenerator, unrelated to `quest_generator`) and, at runtime, `social_systems.contracts.ContractService`. `pyproject.toml` `[project.scripts]` has three entry points, none in `src/systems/`.
- **K1 import by class name, K2 string registration**: per symbol below.

## Per symbol
| symbol | K1 import / name | K2 string | verdict |
|---|---|---|---|
| `QuestGenerator` (world_systems/quest_generator.py) + shim `src/systems/quest_generator.py` | shim imports it; no other import; `generate_for_entity` has no caller (the live same-name class is `src/quests/generator.py`) | only the architecture allowlist string `systems/world_systems/quest_generator.py` and generated audits/baselines | DELETE |
| `RecruitmentAppraiser` (appraisal.py) | none outside its own docstring; its body just forwarded to `SocialAppraisalSystem._appraise_recruitment`, which stays (used at appraisal.py:83) | the mutation baseline `tests/mutation/baselines/src_systems_social_appraisal_v1.json` quotes diffs that mention it (a dated observation with `stale_after`, no tool regenerates it; left as is) | DELETE |
| `ChestSystem` (economy_systems/chests.py) + shim `chest_system.py` | shim; `tests/unit/world/test_chest_lifecycle.py` (3 tests, only this class) ; comments in test_lifecycle.py | completeness-check and state-caller tests used the shim as an example (moved to `market`) | DELETE with its test |
| `SocialContractSystem` (contracts.py) + shim `social_contract.py` | **`ContractService.accept_contract` (:177) and `resolve_contract_outcome` (:203) call `SocialContractSystem.transition_contract`; `accept_contract` is called from `src/domains/cooperation/phase.py:179`**; tests import via the shim | none | **KEEP, live** — the ticket's premise was wrong |
| `LootSystem` (loot.py) + shim | shim; tests/unit/resource/test_loot_channeling.py (9), tests/integration/kernel/test_resource_conservation.py (2 loot tests); comments in actions/loot.py:42 and world/boss.py:295 | none | no src caller; **kept** — see group C |
| `TownServiceSystem` (town_service.py) + shim | shim; tests/unit/world/test_town_services.py (4) | none | no src caller; **kept** — group C |
| `GuildIntelSystem` (guilds.py) + shim `guild_system.py` | shim; tests/unit/world/test_guild_intel.py (2) | tools/test_architecture/core_rpg_report.py maps `src.systems.guild_system*` | no src caller; **kept** — group C |
| `QuestSystem` (quest_engine.py) + shim `quest_system.py` | shim; tests/unit/quest/test_quest_system.py (3), test_resource_conservation.py (1) | none | no src caller; **kept** — group C |
| `CraftingSystem` (crafting.py) + shim `crafting.py` | shim; tests/unit/quest/test_progression_lifecycle.py (2 crafting tests) | tools/test_architecture/core_rpg_report.py maps `src.systems.crafting*` | no src caller; **kept** — group C |

## Group C: dead code that parity, Bible and compliance claims cite
See the ticket's Implementation Notes for the table (ledger ids, Bible section, tests, live path where one exists).
