# Impact report v0

_Recommendation only. Never use this report to skip, remove or narrow a test or a lane._

## Changes
- `docs/parity_ledger/town_resource.yaml` — no-runtime-impact-rule (documentation): documentation/ticket/registry path: no runtime code; informational only, CI rules still decide what runs; but 3 test(s) read this path
- `src/core/conservation.py` — mapped (ownership-map): module src.core.conservation is under the substrate component roots
- `tests/integration/kernel/test_node_charge_cross_actor.py` — mapped (changed-test): the test file itself changed
- `tests/unit/resource/test_node_charge_accounting.py` — mapped (changed-test): the test file itself changed

## Domains
- **substrate**: src/core/conservation.py: module src.core.conservation is under the substrate component roots

## Levels
- unit: src component changed
- kernel_integration: src component changed

## Recommended tests (10)
- `tests/integration/content/test_resource_region_coverage_corpus.py` — reads docs/parity_ledger/town_resource.yaml | lanes: {'integration': 'always-on'} | executed: not-run
- `tests/integration/kernel/test_node_charge_cross_actor.py` — changed test file | lanes: {'integration': 'always-on'} | executed: not-run
- `tests/integration/pipeline/test_transaction_completion.py` — imports src.core.conservation | lanes: {'integration': 'always-on'} | executed: not-run
- `tests/tools/test_done_checker_static.py` — reads docs/parity_ledger/town_resource.yaml | lanes: {'api-tools': 'always-on'} | executed: not-run
- `tests/tools/test_parity_index_baseline.py` — reads docs/parity_ledger/town_resource.yaml | lanes: {'api-tools': 'always-on'} | executed: not-run
- `tests/unit/combat/test_combat_matrix.py` — imports src.core.conservation | lanes: {'unit-gameplay': 'always-on'} | executed: not-run
- `tests/unit/domains/adventure/test_craft_upgrade_execution.py` — imports src.core.conservation | lanes: {'unit-infra': 'always-on'} | executed: not-run
- `tests/unit/economy/test_gold_sink.py` — imports src.core.conservation | lanes: {'unit-gameplay': 'always-on'} | executed: not-run
- `tests/unit/resource/test_durability_repair.py` — imports src.core.conservation | lanes: {'unit-gameplay': 'always-on'} | executed: not-run
- `tests/unit/resource/test_node_charge_accounting.py` — changed test file; imports src.core.conservation | lanes: {'unit-gameplay': 'always-on'} | executed: not-run

## Lanes
- api-tools (always-on): 2 x covers a selected test
- integration (always-on): 3 x covers a selected test
- unit-gameplay (always-on): 4 x covers a selected test
- unit-infra (always-on): covers a selected test

## Known gaps
- tactical navigation is listed under Movement in the ownership map but has no code root; changed paths that only belong to it cannot be mapped and are reported as impact-unknown
- transitive src dependents are not followed (one hop, domains only)
- tests are matched to docs/registry paths by literal path mention, directly or through an imported tools/src module; a test that builds the path dynamically is missed
- PR-eligible lanes are approximated as the parsed lanes that exclude slow tests
