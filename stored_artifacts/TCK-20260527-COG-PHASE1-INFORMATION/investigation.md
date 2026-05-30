# Investigation Report - Phase 1 Information Provider

## Findings
- Guide provider needs access to `ResourceRegistry` to locate resource locations, but must intercept secret queries (e.g. `moon_resin`) to return partial research leads instead of the exact node region.
- Gold costs can be checked against the entity's inventory, returning a failure if gold is insufficient.
