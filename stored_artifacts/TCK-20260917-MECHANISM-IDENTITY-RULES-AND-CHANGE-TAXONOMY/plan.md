---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY

## Steps

1. State the identity rule and the seven-kind change taxonomy in a new sibling doc
   (`docs/plans/mechanism_identity_and_change_taxonomy.md`), per Acceptance Criterion #1's own
   requirement that this not live in a ticket body alone.
2. Resolve the `depends_on` semantics open question by applying the registry's own already-stated
   definition (found in `registries/mechanisms.yaml`'s own header, not missing) to the two
   contested edges on `combat_resolution`, rather than inventing a new definition.
3. Test the identity rule against the 7 bundled entries named in Scope §3, investigating each
   directly against real code — verify any sub-agent-reported finding before trusting it, per this
   epic's own standing discipline.
4. Assess `action_pacing_readiness` explicitly (the falsification test) and `combat_resolution`
   (the multiple-entry-point test) against the rule.
5. Perform every split the rule's own test confirms, propagating each to `depends_on`, dependent
   re-pointing, `verified` blocks, and consumer artifacts (atlas badge, capabilities tier) — not
   leaving a split half-done in the registry alone.
6. Fix any real defect found along the way (the `regional_sovereignty` `implemented_by`
   mis-binding) rather than silently absorbing it or leaving it for later.
7. Update any pinned test whose expected value legitimately changed as a consequence of the
   registry restructuring — never routing around a gate, only updating counts/assertions that are
   now factually different for a real, explained reason.

## Non-goals

- Re-splitting the already-fine-grained combat mechanisms (`combat_engagement`,
  `tactical_decision`, `combat_resolution` stay as three entries — this ticket asks whether the
  coarse bundled entries are wrong, not whether the fine ones should merge).
- Forcing uniform granularity — `inventory_trade_conservation`/`cognition_capacity_fatigue`/
  `information_trust_deception`/`attributes_biology` are kept as single entries since no real
  divergence was found, not split for symmetry with the four that did split.
- A full re-audit of all 65 `depends_on` edges under the tightened `depends_on` reading — only the
  one edge the open question named (`combat_resolution` → `tactical_decision`) is corrected here.
- Filing a new ticket for `RegionalSovereigntyService`'s own orphan finding, or resolving whether
  `lair`'s own `gap` state is consistent with the boss-gate reachability ticket's findings — both
  flagged, not resolved, to keep this ticket's own scope bounded.
- Implementing the declared-versus-actual registry-diff check (the natural follow-up to the change
  taxonomy) — the rules need to survive contact with real entries first.
