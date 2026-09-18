---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION
artifact_type: test_plan
tags: [architecture, documentation, investigation]
---

# Test Plan — TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION

Investigation-only ticket; no code, schema, or generator changed. "Testing" here means the
derivation methodology's own correctness, not a new pytest suite.

## Derivation correctness

`transitive_dependencies_of()` is an already-tested, existing function
(`tools/mechanism_registry/registry.py`, covered by
`tests/unit/tools/test_mechanism_priority_derivation.py`) reused as-is, not modified — no new test
coverage needed for the function itself. Its output was spot-checked by hand for `combat_resolution`
(8 members, matching the same set already visible in that mechanism's own `verified` note from
`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`) before trusting it for the other 3
domains.

## Edge-trust count correctness

The "audited" edge set (5 edges: `combat_resolution → {combat_engagement, movement, status_effects,
entity_role, skill_unlocks}`) was taken directly from `combat_resolution`'s own current
`depends_on` list in `registries/mechanisms.yaml`, cross-checked against
`docs/plans/mechanism_identity_and_change_taxonomy.md` §3's own description of what was checked
during that ticket — not assumed or guessed.

## No regression risk

No `registries/mechanisms.yaml`, `tools/`, or `src/` file changed by this investigation — the
standard scoped test suite was not re-run since there is nothing for it to catch; this investigation
reads the committed registry, it does not write to it.
