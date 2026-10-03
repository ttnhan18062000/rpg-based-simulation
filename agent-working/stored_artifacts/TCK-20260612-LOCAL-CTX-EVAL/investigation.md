# Investigation — TCK-20260612-LOCAL-CTX-EVAL

PHASE_TS: 2026-06-12T00:00:00Z

## Key Findings

### Query output format (`knowledge_search.py query --top-k 10`)

Each result line is tab-separated with 8 columns:
```
doc_id  path  heading  section  final_score  semantic_score  keyword_score  snippet
```
Column 0 (`doc_id`) is the document identity: `{section}/{stem}` (e.g., `mechanics/02_combat_laws`). This is what `expected_doc_ids` in queries.json should match against.

### doc_id space confirmed from docs/ structure

Section → representative doc_ids:
- `mechanics` → `mechanics/01_entity_anatomy`, `mechanics/02_combat_laws`, `mechanics/03_economic_laws`, `mechanics/04_strategic_cognition`, `mechanics/05_world_evolution`, `mechanics/06_worldbuilding_foundation`
- `engine` → `engine/kernel`, `engine/authoritative_pipeline`, `engine/authoritative_mutation_pipeline_contract`, `engine/governance_logic`, `engine/performance_contract`, `engine/known_limitations`
- `core` → `core/state`, `core/entities`, `core/attributes_and_classes`
- `architecture` → `architecture/world_assembly_architecture`, `architecture/world_repository_layout`, `architecture/adr-004-simulation-watchdog`, `architecture/adr-005-performance-optimization`
- `engine/contracts` → `engine/contracts/replay_contract`, `engine/contracts/scheduler_contract`, etc.

### Match strategy

The eval script checks whether any result in the top-K has a `doc_id` equal to one of the `expected_doc_ids`. Multiple `expected_doc_ids` per query means "any of these is acceptable."

### Recall@5 threshold choice

0.80 (i.e., 32/40 queries) is realistic for a BM25+semantic hybrid on first deploy. The threshold is configurable via `--threshold`.
