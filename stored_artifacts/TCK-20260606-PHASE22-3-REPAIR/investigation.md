# Staging Investigation - TCK-20260606-PHASE22-3-REPAIR

## Current Findings
- List conversions in `WorldModuleAuthoringNormalizer.normalize` evaluate `list(spec.resources)` etc.
- If `spec.resources` is a dict `{"wood_node": 2}`, `list(spec.resources)` becomes `["wood_node"]`.
- The quantity `2` is discarded entirely.
- In `src/worldassembly/resolver.py`, `assemble` merges resources by looking at `spec.resources` dynamically if it is a dict, but `resolve_module_contribution` parses it as `resource_refs.append(res_id)`.
- If `schema_version` is v2, we want clean count mapping representation.
