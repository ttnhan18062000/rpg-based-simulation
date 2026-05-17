# Architectural Investigation: Static Guard Against Direct DirtySet Usage

## Current State Analysis

In Milestone 1, we centralized candidate selection within `CandidateSelector` in `src/core/dirty.py`. Helper functions like `get_relevant_entity_ids` and `get_relevant_group_ids` provide safe, fallback-aware access to candidate sets based on domain requirements.

A codebase grep for `dirty_set` confirms that current usage is restricted entirely to authoritative core modules:
- `src/core/state.py` (Validation)
- `src/core/updates.py` (StateUpdate schema and merging)
- `src/core/dirty.py` (CandidateSelector implementation)
- `src/engine/apply.py` (Applying updates and auditing)
- `src/engine/pipeline.py` (Building and refreshing dirty sets)
- `src/engine/kernel.py` (Audit flags and passing update context)

## Vulnerability & Protection Need

If an engineer writing a new simulation phase or AI behavior directly calls `update.dirty_set.movement_entities`, they bypass the `force_full_scan=True` check and any fallback logic for `dirty_set is None`. This leads to subtle optimization bugs where entities are incorrectly skipped during full-scan audits or benchmarks.

## Verification Approach

We will implement a static AST/text analysis test in `tests/static/test_no_direct_dirtyset_candidate_selection.py` that scans all `.py` files inside:
- `src/engine/pipeline_phases/`
- `src/systems/`
- `src/ai/`

The test will verify that none of these files contain direct references to `.dirty_set` or property lookups on `dirty_set` outside the allowed core infrastructure.
