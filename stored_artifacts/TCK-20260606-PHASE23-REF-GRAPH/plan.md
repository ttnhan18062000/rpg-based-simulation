# Implementation Plan - Phase 23 Reference Graph and active-data validation

## Proposed Changes

### Content Graph and Validation

#### [MODIFY] [reference_graph.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content/reference_graph.py)
- Declare `self.edge_metadata: Dict[Tuple[str, str], Dict[str, Any]] = {}` in `__init__`.
- Update `add_edge(self, source, target, metadata = None)` to store metadata in `self.edge_metadata`.
- Modify `_build_graph` for `WorldModuleSpec` to explicitly add biome, ecology, population, faction, relationship, resource, building, and service edges, preserving counts as metadata.
- Modify `_build_graph` for `WorldCompositionSpec` to explicitly add composition -> module edges.

#### [MODIFY] [test_content_usage_matrix.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content/test_content_usage_matrix.py)
- Add `test_graph_ignores_yaml_comments` asserting graph validation works without comment text dependencies.
- Add `test_family_without_declared_consumer_fails_usage_contract` checking family-level consumer paths are declared if active.
- Add `test_design_only_family_may_have_no_runtime_consumer` checking design-only exceptions.
- Add `test_compatibility_family_points_to_clean_source` checking that compatibility projections reference existing archetypes.

#### [MODIFY] [test_layered_catalog.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content/test_layered_catalog.py)
- Add tests verifying module resource, building, and service count map edges and metadata preservation.
- Verify composition to module edges.
- Verify reverse lookup.

## Verification Plan

### Automated Tests
- Run content unit tests:
  ```bash
  pytest tests/unit/content/
  ```
