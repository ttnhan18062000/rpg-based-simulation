---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC

## Origin
Continuation of a prior session's work, resumed from
`.claude/handover/world-rule-catalog-design.md`: PR #223 (World Rule Catalog relocation +
Simulation Semantic Control Plane epic design) merged to `main` at commit `a4333bcef`
(confirmed via `git merge-base --is-ancestor a4333bcef origin/main`). The handover named "epic
ticket creation for `docs/plans/simulation_semantic_control_plane/`" as the next, not-yet-started
work, on a fresh branch off `origin/main` (this branch had already been squash-merged and is
finished per CLAUDE.md's PR Lifecycle §7).

## Summary of evidence
- Direct grep confirmed zero cross-references between the World Rule Catalog (172 Rule IDs,
  `docs/world_rules/`) and the Mechanism Registry (93 mechanisms, `registries/mechanisms.yaml`) —
  the gap this whole epic exists to close, restated from `roadmap.md`'s own appendix.
- No prior epic or child ticket existed for this initiative (`find tickets -iname
  "*SEMANTIC-CONTROL-PLANE*"` returned nothing before this session).
- `roadmap.md` itself states no milestone has started and no ticket had been opened.
- Six `concern-investigator` runs against M0's own section each independently found the three
  schemas, the validator, its broken-fixture proof, and the `architecture.md` §3 doc-sync are not
  separable into independent tickets — most concretely, `TCK-20260915-MECHANISM-REGISTRY-
  FOUNDATION` (the ticket that built the *original* Mechanism Registry) treated schema + validator
  + broken-fixture proof as one ticket's own AC list, not separate tickets — the direct precedent
  this epic's own M0 reuses.

## Related
- `docs/plans/simulation_semantic_control_plane/roadmap.md` (full M0–M4 sequencing)
- `tickets/todos/semantic-control-plane-m0/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION.md` (the
  one child ticket this pass produced)
