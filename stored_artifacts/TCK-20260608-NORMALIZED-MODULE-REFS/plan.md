# Plan — TCK-20260608-NORMALIZED-MODULE-REFS

## Steps
1. normalizer.py: rename 4 dataclass fields + 4 normalize() assignments
2. reference_graph.py: rename 4 field accesses in add_module_edges()
3. resolver.py: rename 4 field accesses
4. test_reference_graph.py: rename kwargs in _make_normalized_module + 3 inline kwargs
5. test_modules.py: sed rename all 12 field access occurrences
6. test_real_content_world_modules.py: rename 2 normalized.populations → population_refs

## Deviations
None.
