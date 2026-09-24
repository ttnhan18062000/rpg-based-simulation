---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE
phase: done
date: 2026-09-24
tags: [architecture, schema, registry, combat]
---

# TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE

## Title

M3 narrow triage: ingest existing Territory/Control and Combat/Conflict prose findings into the
Semantic Control Plane, or record why each stays UNKNOWN

## Status

DONE

## Tier

standard

## Type

chore

## Priority

P1

## Request Summary

`docs/plans/simulation_semantic_control_plane/roadmap.md`'s M3 is a **permanent, incremental
ingestion stream, not a bounded milestone** — it has no "complete" state and is explicitly not a
full-catalog prerequisite. But it carries one narrow minimum bar, and that bar is the only
remaining gate on M4:

> **M3's own minimum bar** — before M4 begins, triage the Implementation Candidates sections
> specifically for **Territory/Control and Combat/Conflict** — the two domains M1 and M4 actually
> need. The rest of the Catalog remains `UNKNOWN` until later tickets or a targeted sweep touches
> it, exactly per Stage D.

This ticket delivers exactly that bar and nothing wider. Every named existing finding in those two
domains is re-verified against the **current** registry/code state and given one explicit
disposition: promoted to a real mapping entry, or recorded as staying `UNKNOWN` with a written
reason.

The re-verification requirement is not ceremony. `mechanism_identity_and_change_taxonomy.md` §4 is
the on-record precedent: an earlier prose claim of "no separate implementation exists" was based on
an incomplete search and was simply wrong. **Prose findings are leads, never facts to copy
forward** — that is the whole meaning of `rollout_plan.md` Stage C's "ingest, don't launder."

## Scope

**The two domains' triage sources, which are not symmetric** — this was checked directly, do not
assume a uniform shape:

| Domain | Triage sources |
|---|---|
| Territory/Control | `docs/world_rules/places-culture/territory-control.md` → `## Implementation Candidates — Non-Binding` (1 candidate) and `## Open questions carried forward` (2); `docs/world_rules/review-exports/places-territory-batch-11a-review.md` → `## Implementation Candidates — Non-Binding` (L311) and `## Repository Findings` (L247) |
| Combat/Conflict | `docs/world_rules/capability-progression/conflict-combat.md` → `## Repository Findings (significant, cross-referenced)` (L179, 4 findings) and `## Open questions carried forward` (L213); `docs/world_rules/review-exports/capability-progression-batch-07-review.md` → `## Repository Findings` (L269, 12 numbered findings) |

**`conflict-combat.md` has no `Implementation Candidates` section at all** — its equivalent content
lives under `Repository Findings`. Triaging by section *name* alone would silently skip the entire
Combat half of this ticket's bar and report success. Triage by content.

**Per finding, produce exactly one of:**
1. **Promote** — write the corresponding row(s) to `registries/rule_mechanism_edges.yaml` and/or
   `registries/rule_classifications.yaml` through M0's validator, with real evidence and today's
   date. Subject to the Territory/Combat asymmetry rule below.
2. **Stays UNKNOWN** — recorded with a written reason. `UNKNOWN` is a permanent, valid, expected
   value per `architecture.md` §7; a well-reasoned `UNKNOWN` is a complete triage outcome, not a
   deferred one. Never silently upgrade `UNKNOWN` to `MISSING` — `MISSING` asserts someone
   investigated and confirmed absence.
3. **Not a control-plane fact** — some findings are real but map to nothing in this schema (e.g.
   batch-07 finding 12, the `src/world/displacement.py` naming near-collision; finding 11, a
   doc/implementation mismatch). Disposition them as out-of-model with a one-line reason rather
   than forcing a row.

**Territory/Combat promotion asymmetry — the key scope decision in this ticket.** M1 already
populated Territory's mapping and M2's detector already watches it, so a Territory finding that
warrants a row **is promoted here, now**. Combat has no mapping rows at all yet, and **creating
Combat's mapping is M4's own named deliverable** — so a Combat finding that warrants promotion is
dispositioned `PROMOTE-AT-M4` with its verified evidence recorded, and M4 consumes that record
rather than re-deriving it. This ticket must not pre-empt M4 by writing Combat mapping rows.

**Deliverable artifact.** A triage record at
`docs/plans/simulation_semantic_control_plane/finding_triage_log.md`: one row per triaged finding
with source citation, re-verification result (what was actually checked, today, against live
state), disposition, and reason. This is the durable record M4 reads. Per the project's own
"define information once" discipline, it records the *triage decision*; it does not restate the
finding's prose or duplicate registry row content.

**Batch-07 scope guard.** `capability-progression-batch-07-review.md` covers **three** rule
families (Capability/Progression, Learning/Adaptation, Conflict/Combat), not just Combat. Of its 12
numbered Repository Findings, only the Combat/Conflict-scoped ones are in scope for this ticket —
on a first read that is roughly findings 1 (perception-gated targeting, SUPPORTED), 2
(`combat_engagement` INERT/OFF), 7 (no surrender/capture/forced-displacement outcome), and 12
(naming near-collision). Findings 4, 5, 6, 10 and 11 are progression/learning-domain and are
explicitly **out of scope** — do not triage them, and do not let them expand this ticket into the
full-catalog migration the roadmap specifically argues against. **Verify that split yourself
during Investigate rather than trusting this list** — it is a scoping read, not a checked fact.

## Out of Scope

- Any domain other than Territory/Control and Combat/Conflict. The remaining ~10 batches stay
  `UNKNOWN` by design.
- Writing Combat's mapping rows (M4's deliverable — see the asymmetry rule above).
- M4's cross-domain view, and any change to M0's schema or M2's detector.
- **Fixing any gap a triaged finding names.** Several are real, live defects (the permissive
  `try/except Exception: pass` perception-gate fallback at `src/engine/tactical.py`'s call site;
  the absent `max_xp_per_tick` symbol that
  `docs/engine/supported_progression_surface_phase5.md` claims exists). Triage *records* them; it
  does not repair them. A repair is its own ticket.
- Resolving `tactical_decision`'s `verified.verdict: contradicted` or the paused
  `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`. Both are named in `roadmap.md` as things
  M4 re-checks, not gates — record their state as of today, do not act on them.
- Turning `ENABLE_COMBAT_ENGAGEMENT` on, or any other feature-flag flip.

## Acceptance Criteria

1. `finding_triage_log.md` exists and carries a disposition for every finding in every source
   named in the Scope table, scoped to the two domains (and, for batch-07, to the Combat family).
2. Every disposition cites what was **re-verified today** against live state — a registry row read,
   a code path opened, a `make` target run — not the prose finding restated. A disposition whose
   only evidence is the original prose is not a valid triage outcome.
3. Territory findings warranting promotion are written to `registries/rule_mechanism_edges.yaml`
   and/or `registries/rule_classifications.yaml` and pass
   `python3 tools/semantic_control_plane/registry.py` with **zero manual overrides of a reported
   violation**.
4. Combat findings warranting promotion carry `PROMOTE-AT-M4` plus verified evidence sufficient for
   M4 to write the row without re-investigating. No Combat rows are written to either registry by
   this ticket.
5. `make semantic-control-plane-drift-check` still reports clean after any Territory promotion —
   newly-promoted rows dated today must not themselves register as drift. **If they do, that is a
   real M2 finding to report, not a date to adjust to silence it.**
6. At least one triaged finding lands on `UNKNOWN` or out-of-model with a written reason, or the
   triage log states explicitly why every single finding promoted — an all-promote result is
   possible but is the kind of outcome the `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`
   precedent says to justify rather than present as a clean score.
7. `roadmap.md`'s M3 section records that the narrow Territory+Combat bar is met, **without**
   marking M3 "complete" — M3 has no complete state and the section says so.
8. The epic ticket's milestone disposition table carries M3's narrow-bar disposition.

## Related Tickets

- `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` — parent
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` — the schema and validator every promotion goes
  through
- `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE` — Territory's existing mapping rows
- `TCK-20260924-M2-MAPPING-DRIFT-DETECTION` — the detector AC5 re-runs
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` — closed; the settled fact behind
  `tactical_decision`'s `contradicted` verdict
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` — paused; could move combat's numbers if
  it resumes. Record, do not act.
- `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION` — known dangling Rule-ID citation in
  `territory-control.md`; do not re-derive or re-file it.

## Related Docs

- `docs/plans/simulation_semantic_control_plane/{roadmap,architecture,rollout_plan,agent_operating_model}.md`
- `docs/plans/status_axis_model.md` — governs every status word used on this track
- `docs/world_rules/places-culture/territory-control.md`,
  `docs/world_rules/capability-progression/conflict-combat.md`
- `docs/world_rules/review-exports/{places-territory-batch-11a,capability-progression-batch-07}-review.md`
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §4 — the re-verify-don't-launder precedent

## Related Stored Artifacts

- `stored_artifacts/TCK-20260924-M2-MAPPING-DRIFT-DETECTION/investigation.md` — includes the
  written reason drift class 2 was descoped; relevant if a triaged finding looks like a lineage
  case
- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/`

## Related Code Areas

- `registries/{rule_mechanism_edges,rule_classifications,mechanisms}.yaml`
- `tools/semantic_control_plane/{registry,rule_catalog,mapping_drift_check}.py`
- Read-only during re-verification: `src/engine/tactical.py`, `src/domains/combat_engagement/`,
  `src/world/{threat,displacement}.py`, `RegionState`/`PlaceState` `owner_faction_id`

## Assumptions / Open Questions

1. **Triage-log location and shape are this ticket's own call.** A markdown log under the plan
   directory is proposed above because the triage decision is process state, not durable simulation
   state; if Investigate finds a registry-backed shape is genuinely better, say so and justify it
   rather than silently switching.
2. **The batch-07 in-scope/out-of-scope finding split is a scoping read, not a verified fact** —
   confirm it during Investigate. Getting it wrong in the permissive direction turns this ticket
   into the full-catalog sweep the roadmap explicitly rejects.
3. Whether any Territory finding actually warrants a *new* row is unknown — M1 may already cover
   all of them. "Already covered by M1's existing row" is a complete, valid disposition, and a
   triage that promotes nothing in Territory is an acceptable outcome if that is what the evidence
   shows.
4. Tests for this track live in `tests/unit/tools/`, **not** `tests/tools/`.
5. `search_docs` MCP returns "index not found" in this worktree (`make knowledge-index` has never
   been run here). Use `graphify query` and direct reads; do not report the missing index as a
   defect.

## Scoping Decisions (2026-09-24, post-Investigate)

Three questions surfaced by Investigate, resolved by the ticket owner. Each was independently
re-verified before answering; none is a relayed claim.

**D1 — `ENABLE_COMBAT_ENGAGEMENT` is dispositioned `PROMOTE-AT-M4` with corrected evidence, not
`CONFLICTING`.** Verified independently: `src/domains/optimization/feature_flags.py:32` is
`FeatureMode.ON`, flipped by `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (#190, commit
`1e075b807`) — nine days before both Combat source docs' own `last_verified: 2026-09-23`. The
implementer's lean was right; the reason matters more than the answer. **`CONFLICTING` is part of
the realization-classification vocabulary, which describes code-vs-Rule: "code exists and actively
does the wrong thing relative to the Rule."** What is conflicting here is doc-vs-reality — a stale
prose premise. Recording documentation staleness as `CONFLICTING` would assert a semantic violation
of a Rule that has not been shown to exist, which is exactly the vocabulary laundering
`docs/plans/status_axis_model.md` governs against.

Further: **M3 records verified evidence; M4 makes the classification.** This triage must not assert
`INERT-OFF`, `SUPPORTED`, or any other classification for `combat_engagement` — it records that the
flag is ON, live-wired into `src/engine/pipeline.py`'s tick loop, with observed runtime effect
already in `registries/mechanisms.yaml` (posture gate 1960→837 attacks), and lets M4 judge.

This is the first case where the re-verification requirement (AC2) earned its keep — a finding
would have entered the control plane with an inverted premise. **Call that out explicitly in the
triage log**; it is evidence the "ingest, don't launder" discipline works, not an incidental catch.

**D2 — do not edit `conflict-combat.md`'s stale prose. Out of scope.** Three reasons, in order:
`docs/world_rules/` is the **frozen** Rule Catalog — changing it is a deliberate documented
decision, not a routine correction ridden in on another ticket; `world-rule-catalog-design` owns
that catalog, not this track; and correcting the prose *and* recording the fact in the triage log
would put live flag state in two places, which is how it drifted in the first place ("define
information once"). The registries and the triage log are the live layer now; the catalog prose is
a dated artifact and reads correctly as one. The staleness has been handed to
`world-rule-catalog-design` separately as a verified report, not left implicit.

**D3 — the Territory source enumerates 3 findings, not 10. Confirmed as fact, not judgment.**
`places-territory-batch-11a-review.md`'s Repository Findings list is mechanically separable: every
numbered item carries its own Rule ID. Items 1 (TERR-01/TERR-03), 2 (TERR-01) and 8 (TERR-02) are
Territory; items 3 (PLACE-02), 4 (PT-S02/PT-S05), 5 (SETT-03/SETT-01), 6 (SETT-02), 7
(`settlements.md`), 9 (SETT-02/PT-S13) and 10 (SETT-01) are Places/Settlements and are out of
scope. **AC1's "every finding in every source" means these 3 for this source.**

Item 2 is a real, in-scope Territory promotion: verified directly against
`registries/rule_classifications.yaml` — TERR-01's evidence text names cultural-association only as
one of the overloaded-slot concepts, and does not record the separate MISSING sub-fact that no
residence or cultural-association field exists anywhere and nothing reads `owner_faction_id` as
either. Amend that row's evidence. The aggregate `CONFLICTING` verdict stays correct and does not
move.

**Process note accepted (not a decision, a correction to this ticket).** The Scope section's
first-read batch-07 split listed only some items as out-of-scope and never mentioned 3, 8 or 9 at
all — a partial enumeration presented as a near-complete one. It worked only because the ticket
also said to verify it. M4's ticket will enumerate every item with an explicit in/out disposition
rather than a partial list, and the Scope table will carry the "triage by content, not section
name" warning for **both** domains' sources — it was written for batch-07 only, and the Territory
source turned out to have the identical hazard.

## Implementation Notes

Investigate re-verified every named finding against live state and surfaced two real scope
questions, sent back to the epic owner rather than resolved unilaterally (per the ticket's own
instruction): (1) how to disposition the `ENABLE_COMBAT_ENGAGEMENT` staleness — both Combat source
docs claim default-OFF, live state is ON since 2026-09-14, nine days before their own
`last_verified` date; (2) whether `places-territory-batch-11a-review.md`'s Repository Findings
enumerates 10 Territory items or fewer (it mixes three rule families under one list, the same
hazard the ticket flagged for batch-07 but not for this Territory source). Both resolved by the
epic owner in the ticket's own `## Scoping Decisions` section (D1/D2/D3) before Plan proceeded.

Plan and Implement executed exactly those decisions: `finding_triage_log.md` written as the new
durable triage record; one existing registry row's evidence text amended (TERR-01, adding the
residence/cultural-association MISSING sub-fact — the aggregate `CONFLICTING` verdict did not
move); `roadmap.md`'s M3 section and the epic ticket's M3 milestone row both updated to record the
narrow bar met without marking M3 "complete." Zero Combat mapping rows written — Combat's mapping
stays M4's own deliverable, confirmed by direct grep at Verify. Post-Implement architecture review
passed all 7 checks (TERR-01 classification unchanged, no Combat rows, M3/M4 classification
boundary respected in the triage log's own prose, `docs/world_rules/` untouched, UNKNOWN/MISSING
discipline held, no `src/` or durable-state touch, AC7's "not complete" language preserved).

The `ENABLE_COMBAT_ENGAGEMENT` doc staleness was **not** corrected in `conflict-combat.md` itself
(D2 — out of scope, `world-rule-catalog-design` owns the frozen Rule Catalog); the epic owner
handed that staleness report to that track separately.

## Test Summary

`pytest tests/unit/tools/test_semantic_control_plane_schema.py
tests/unit/tools/test_semantic_control_plane_drift_detector.py
tests/unit/tools/test_territory_control_view.py -v` — 45/45 passed.

`python3 tools/semantic_control_plane/registry.py` — `OK`, zero manual overrides (AC3).

`make semantic-control-plane-drift-check` — `0 cited-code drift finding(s), 0 verdict drift
finding(s)` after the TERR-01 evidence-text edit (AC5).

Manual guard (AC4): `grep -n "CONFLICT-" registries/{rule_mechanism_edges,rule_classifications}.yaml`
— zero hits in both files, confirmed independently by the architecture-reviewer agent as well as
directly.

## Files Changed

- `docs/plans/simulation_semantic_control_plane/finding_triage_log.md` (new) — the triage record,
  M3's durable deliverable
- `registries/rule_classifications.yaml` — TERR-01 evidence text amended (classification unchanged)
- `docs/plans/simulation_semantic_control_plane/roadmap.md` — M3 section: narrow-bar-met note added
- `tickets/inprogress/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md` — M3 milestone row updated
- `staging_artifacts/TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE/{investigation.md,test_plan.md,plan.md}` (new)

## Completion Summary

M3's narrow Territory+Combat triage bar is met. 5 Territory findings and 8 Combat
findings/open-questions triaged, every disposition citing today's re-verification against live
state, not the original prose. Two real scope ambiguities were caught during Investigate and
resolved by the epic owner before Plan proceeded, rather than worked around — both are now
recorded permanently in the ticket's own Scoping Decisions section for future tickets to cite. The
`ENABLE_COMBAT_ENGAGEMENT` catch is the concrete proof AC2's re-verification requirement earns its
keep: a finding would otherwise have entered the control plane with an inverted premise. All
acceptance criteria met; full standard pipeline; architecture review clean; zero blocking gate
failures.
