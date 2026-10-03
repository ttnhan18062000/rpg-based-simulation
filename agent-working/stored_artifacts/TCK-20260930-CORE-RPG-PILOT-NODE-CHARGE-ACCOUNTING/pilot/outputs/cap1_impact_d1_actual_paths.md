# Impact report v0

_Recommendation only. Never use this report to skip, remove or narrow a test or a lane._

## Changes
- `docs/parity_ledger/town_resource.yaml` — no-runtime-impact-rule (documentation): documentation/ticket/registry path: no runtime code; informational only, CI rules still decide what runs; but 3 test(s) read this path
- `tests/integration/kernel/test_node_charge_cross_actor.py` — mapped (changed-test): the test file itself changed
- `tests/unit/resource/test_node_charge_accounting.py` — mapped (changed-test): the test file itself changed

## Domains
- **economy**: tests/integration/kernel/test_node_charge_cross_actor.py: declared-marker domain('economy'); tests/unit/resource/test_node_charge_accounting.py: declared-marker domain('economy')
- **substrate**: tests/integration/kernel/test_node_charge_cross_actor.py: declared-marker domain('substrate'); tests/unit/resource/test_node_charge_accounting.py: declared-marker domain('substrate')

## Levels
- kernel_integration: declared-marker: tests/integration/kernel/test_node_charge_cross_actor.py declares level('kernel_integration')
- unit: declared-marker: tests/unit/resource/test_node_charge_accounting.py declares level('unit')

## Recommended tests (5)
- `tests/integration/content/test_resource_region_coverage_corpus.py` — reads docs/parity_ledger/town_resource.yaml | lanes: {'integration': 'always-on'} | executed: not-run
- `tests/integration/kernel/test_node_charge_cross_actor.py` — changed test file | lanes: {'integration': 'always-on'} | executed: not-run
- `tests/tools/test_done_checker_static.py` — reads docs/parity_ledger/town_resource.yaml | lanes: {'api-tools': 'always-on'} | executed: not-run
- `tests/tools/test_parity_index_baseline.py` — reads docs/parity_ledger/town_resource.yaml | lanes: {'api-tools': 'always-on'} | executed: not-run
- `tests/unit/resource/test_node_charge_accounting.py` — changed test file | lanes: {'unit-gameplay': 'always-on'} | executed: not-run

## Lanes
- api-tools (always-on): 2 x covers a selected test
- integration (always-on): 2 x covers a selected test
- unit-gameplay (always-on): covers a selected test

## Known gaps
- tactical navigation is listed under Movement in the ownership map but has no code root; changed paths that only belong to it cannot be mapped and are reported as impact-unknown
- transitive src dependents are not followed (one hop, domains only)
- tests are matched to docs/registry paths by literal path mention, directly or through an imported tools/src module; a test that builds the path dynamically is missed
- PR-eligible lanes are approximated as the parsed lanes that exclude slow tests
