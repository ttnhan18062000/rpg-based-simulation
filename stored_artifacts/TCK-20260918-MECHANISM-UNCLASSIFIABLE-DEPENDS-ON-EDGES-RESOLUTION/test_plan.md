---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION
artifact_type: test_plan
tags: [architecture, schema]
---

# Test Plan — TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION

## Normal flow
`registry.py::validate()` must pass clean against the edited registry (93 mechanisms, all
`depends_on` edges resolve, `unaudited_depends_on_edges` shrunk to 2 with both still naming real
declared edges per invariant 8).

## Edge cases
- Removing an edge from a mechanism's `depends_on` list changes its own transitive-dependent count
  and derived priority — every downstream consumer of that (priority view, registry view,
  state-caller check's own findings) needed re-verification, not just the registry file itself.
- A state correction (`trauma`: done → orphan) must propagate to every consumer artifact per this
  epic's own established discipline (atlas, capabilities, wiring map), not just the registry field.

## Failure modes / regression-prone paths
- **Downstream drift**: regenerating atlas/capabilities/wiring-map views after every edge/state
  change and re-running their own `--check` modes is the only way to catch silent propagation gaps
  — confirmed necessary here (trauma's correction did require all three).
- **Pinned-count test staleness**: 5 pre-existing tests hardcoded specific mechanism picks
  (`action_pacing_readiness`, `betrayal_siege_war`) whose real transitive-dependent counts changed
  as a direct, correct consequence of this ticket's own edge removals — each updated with a real
  recomputed number and a citation to what changed, never silently adjusted.
- **False-positive callers**: `trauma`'s new `orphan_with_callers` finding
  (`mechanism_state_caller_check.py`) needed direct verification that the "1 real caller" was a
  package `__init__.py` re-export, not an actual method call, before trusting the orphan
  correction — same discipline the pinned test's own `genetics_aptitude` precedent already
  documents.

## Coverage delivered
`tests/unit/tools/` full suite: 218 passed after all edits. `registry.py::validate()` clean.
`mechanism_atlas_regenerate.py --check`, `mechanism_capabilities_regenerate.py --check`,
`mechanism_wiring_map_classdef.py` all report zero drift against the final registry state.
