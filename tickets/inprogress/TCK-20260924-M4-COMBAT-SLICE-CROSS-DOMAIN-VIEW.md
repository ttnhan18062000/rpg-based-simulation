---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW
phase: open
date: 2026-09-24
tags: [architecture, schema, registry, combat]
---

# TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW

## Title

M4: Combat/Conflict mapping slice and the first cross-domain management view

## Status

OPEN

## Tier

standard

## Type

feature

## Priority

P1

## Request Summary

The final milestone of `docs/plans/simulation_semantic_control_plane/roadmap.md`. M1 mapped one
domain (Territory/Control); M4 maps a second (Combat/Conflict) and renders both in one view, to
prove the Rule↔Mechanism model generalizes past a single domain's idiosyncrasies rather than having
been shaped around them.

All gates are clear: M0 (schema + validator, #241), M1 (Territory slice, #241), M2 (drift detector,
#243), M3's narrow Territory+Combat triage (#244).

**This milestone ends the roadmap.** Past it, `rollout_plan.md`'s Stages D/E/F continue
indefinitely as maintenance. M4 does not finish the mapping and must not be scoped as if it does.

## Scope

### 1. Combat/Conflict mapping slice

**Source file: `docs/world_rules/capability-progression/conflict-combat.md` only.** Batch 07's
other two files (`capability-progression.md`, `learning-adaptation.md`) are Capability/Progression
and Learning domains — mapping them would make this a three-domain milestone, not a second slice.

**The mappable surface is 12 Rule IDs, not 1. Enumerate all 12 in `plan.md` before writing any
row.** Verified 2026-09-24 by scanning the file against the validator's own `scan_rule_ids()`:

`CONFLICT-01`, `PERC-01`, `KNOW-01`, `AGENCY-01`, `AGENCY-02`, `AGENCY-04`, `LIFE-01`, `LIFE-02`,
`BODY-07`, `OWN-02`, `CAP-01`, `ECOL-04`

Only `CONFLICT-01` is an own-local ID. The other 11 come from **Inherited/Applied Foundational
entries, which are referenceable under the original Rule ID they derive from** — "direct reuse of
an earlier Rule ID → Inherited, no new ID" means the reused ID *is* the entry's citable identity.
Confirmed by `world-rule-catalog-design` 2026-09-24 and verified independently here.

**This enumeration is an anti-bias requirement, not bookkeeping.** Reading `CONFLICT-01` as the
domain's whole surface would produce a one-row slice reported as proof the model generalizes —
the pre-filtered-sample failure already on record as
`TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`.

**`CONFLICT-02` does not resolve and is NOT a defect** — it appears only as "originally drafted as
CONFLICT-02" / "(formerly CONFLICT-02)", correctly marked historical after reclassification to
Inherited. Do not cite it, do not file it as a defect, and make sure any citation-scanning code
doesn't trip over it.

**Re-check against the live registry immediately before finalizing the mapping** (both named in
`roadmap.md`, neither a hard gate): `tactical_decision`'s own current `verified.verdict`, and
whether `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` has resumed. Never carry forward a
verdict quoted in any document, including this ticket.

**Consume `docs/plans/simulation_semantic_control_plane/finding_triage_log.md`, do not
re-investigate it.** M3 already triaged Combat's findings and recorded verified evidence for the
three dispositioned `PROMOTE-AT-M4`. That includes the corrected `ENABLE_COMBAT_ENGAGEMENT` state:
the flag is `FeatureMode.ON` (`feature_flags.py:32`) since 2026-09-14 (#190, `1e075b807`), **not**
the default-OFF that both Combat source docs originally claimed.

### 2. First cross-domain view

Territory's and Combat's management views combined into one (`architecture.md` §8).

**Must show raw `mapped`/`unmapped` and `verified`/`unverified` counts alongside any classification
breakdown or percentage** — never a percentage alone. Same precedent as above.

### 3. Written comparison

A short, honest comparison of what the two views actually show.

### 4. Document the inherited-entry citation rule

The rule in §1 above — that an Inherited entry is cited under its originating Rule ID — is written
down nowhere in `roadmap.md`, `architecture.md`, or the Catalog's admission-discipline section.
That undocumented assumption is what sent both `TERR-04`/jurisdiction and M4's own initial surface
count sideways. **Add it to `architecture.md` §3**, where the edge schema is defined.

`world-rule-catalog-design` asked that a parallel one-sentence addition to the Catalog's own
admission-discipline section ride on `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION` rather than
a new ticket — that stays theirs. This item covers only the control-plane side, which M4 cannot
write inherited-derived edges without.

### 5. Two small carried items

- **Fix the `core_rpg_design_direction.md` §10 run-on paragraph.** PR #241's pointer sentence and
  the 2026-09-24 status note merged into one paragraph with no break (`...Rule realization axis.`
  immediately followed by `**Status note (2026-09-24).**`). Content is correct; it needs a blank
  line. Deferred from #244 to avoid resetting green CI for a cosmetic fix.
- **Report which §10 runtime-status terms the cross-domain view actually needs.** That doc now
  explicitly defers defining-or-pruning its eight undefined values "until the Semantic Control
  Plane's M4 milestone actually needs specific terms." **Report the list only — do not define,
  prune, or edit the vocabulary.** That call belongs to `world-rule-catalog-design`; this ticket
  supplies the evidence they asked for.

## Out of Scope

- Any third domain, and Batch 07's other two files.
- Mapping the remaining ~46 rule families. They stay `UNKNOWN` by design (`architecture.md` §7).
- Defining or pruning §10's vocabulary (see §5 — report only).
- Editing `docs/world_rules/` — the frozen Catalog is not changed by this track (M3's D2).
- Fixing any defect the mapping surfaces. Record it; a repair is its own ticket.
- Resolving `tactical_decision`'s `contradicted` verdict, or resuming the paused hostility sweep.
- CI wiring for the drift detector. Reassess after M4 adds volume; not automatic.
- Adding a lineage field to `mechanisms.yaml`. If M4 has a genuine need for one, say so and stop —
  it would make M2's descoped drift class 2 buildable, which is a separate decision.

## Acceptance Criteria

1. All 12 Rule IDs enumerated in `plan.md` with an explicit disposition each: mapped (with edges +
   classification), or explicitly not mapped with a written reason. `UNKNOWN` is a valid outcome.
2. Every edge and classification cites real evidence and passes
   `python3 tools/semantic_control_plane/registry.py` with zero manual overrides of a violation.
3. `tactical_decision`'s verdict and the paused sweep's status re-checked against live state at
   execution time, with what was found recorded — not quoted from any document.
4. The cross-domain view renders both domains and shows raw mapped/unmapped and
   verified/unverified counts alongside any classification breakdown.
5. `make semantic-control-plane-drift-check` reports clean after the new rows. If it does not,
   that is a real M2 finding to report, never a date to adjust to silence it.
6. The inherited-entry citation rule is documented in `architecture.md` §3.
7. The written comparison records what the two views actually show, including any result that is
   inconvenient. **The success condition is that two structurally different domains are both
   faithfully representable — not that Combat comes out cleaner than Territory.** If Combat maps to
   meaningful `PARTIAL`/`CONFLICTING`/`UNKNOWN` (likely, given `tactical_decision` `contradicted`,
   `status_effects` `orphan`, `skill_unlocks` `partial`), record it as-is. Never adjust the
   classification model to manufacture a cleaner contrast.
8. §10's run-on paragraph fixed; the list of §10 terms the view needs reported without the
   vocabulary being edited.
9. `roadmap.md`'s M4 section and the epic's milestone table both record M4's disposition and that
   the roadmap is complete — while stating plainly that the *mapping* is not finished and Stages
   D/E/F continue.

## Related Tickets

- `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` — parent
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION`, `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE`,
  `TCK-20260924-M2-MAPPING-DRIFT-DETECTION`, `TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE`
- `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` — the pre-filtered-sample precedent
  behind AC1 and AC4
- `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION` — same admission-discipline edge; the Catalog
  side of §4 rides there, not here
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` — closed; the settled fact behind
  `tactical_decision`'s verdict
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` — paused; re-check status, do not resume

## Related Docs

- `docs/plans/simulation_semantic_control_plane/{roadmap,architecture,rollout_plan,agent_operating_model}.md`
- `docs/plans/simulation_semantic_control_plane/finding_triage_log.md` — M4's own input
- `docs/plans/status_axis_model.md` — governs every status word used here
- `docs/world_rules/capability-progression/conflict-combat.md` — read-only
- `docs/brainstorm/core_rpg_design_direction.md` §10

## Related Stored Artifacts

- `stored_artifacts/TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE/`
- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/` — the view M4 extends

## Related Code Areas

- `registries/{rule_mechanism_edges,rule_classifications,mechanism_causal_edges,mechanisms}.yaml`
- `tools/semantic_control_plane/` — `registry.py`, `rule_catalog.py`, `mapping_drift_check.py`,
  and M1's Territory view generator (`make territory-control-view`)
- Read-only during verification: `src/engine/tactical.py`, `src/domains/combat_engagement/`,
  `src/engine/{combat,combat_rewards}.py`
- Tests: `tests/unit/tools/` — **not** `tests/tools/`

## Assumptions / Open Questions

1. Whether the combined view extends M1's generator or is a new one is an implementation call —
   make it in `plan.md` with a reason. Prefer extending if the shape genuinely generalizes.
2. Some of the 11 inherited-derived IDs (`PERC-01`, `KNOW-01`, `AGENCY-01/02`) are already mapped
   by Batch 06's own domain. **A Rule ID receiving mapped edges from two different domains'
   mechanisms is expected and is the case Territory structurally could not test** — it is not a
   duplicate-row error. Confirm M0's validator treats it as valid (it rejects duplicate
   `(rule_id, mechanism_id, edge_type)` triples, which this is not). **If the validator does reject
   it, stop and report** — that is a real schema finding, not something to work around.
3. `search_docs` MCP returns "index not found" in this worktree. Use graphify and direct reads;
   not a defect to report.

## Implementation Notes

_(filled during implementation)_

## Test Summary

_(filled during implementation)_

## Files Changed

_(filled during implementation)_

## Completion Summary

_(filled during implementation)_
