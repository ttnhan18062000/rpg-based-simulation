---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, schema, registry, combat]
---

# Finding Triage Log — Simulation Semantic Control Plane

Durable record of every existing-finding triage decision made against the Rule Catalog's
`Implementation Candidates` / `Repository Findings` sections, per `roadmap.md`'s M3 stream
(`rollout_plan.md` Stage C, "ingest, don't launder"). Each row is a **triage decision**, not a
restatement of the finding's own prose or a duplicate of registry evidence text — see
`docs/plans/mechanism_identity_and_change_taxonomy.md` §4 for why prose is re-verified, never
copied forward as already-current fact. This file grows as later tickets touch more of the
Catalog; it is never "complete."

Dispositions used: **Promote** (a row now exists in `registries/rule_mechanism_edges.yaml` and/or
`rule_classifications.yaml`), **Already covered** (an existing row already answers this finding,
no new row needed), **UNKNOWN** (a permanent, valid, expected value per `architecture.md` §7 —
never silently upgraded to `MISSING`), **Not a control-plane fact** (real, but maps to nothing in
this schema), **PROMOTE-AT-M4** (Combat's mapping doesn't exist yet — M3 records verified evidence,
M4 writes the row and makes the classification call).

## TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE (2026-09-24)

M3's own minimum bar: Territory/Control and Combat/Conflict, re-verified against live state today.
Sources per the ticket's Scope table; the Territory-vs-Combat asymmetry (Territory promotes now,
Combat's rows are M4's own deliverable) is `roadmap.md`'s own explicit design, not this ticket's
invention.

### Territory/Control

Source enumeration confirmed as fact, not judgment (per the ticket's own
"Scoping Decisions" §D3): `places-territory-batch-11a-review.md`'s Repository Findings list is
mechanically separable by per-item Rule ID. Only items 1, 2, and 8 are Territory-scoped; items
3–7, 9, 10 are Places/Settlements (Rule IDs PLACE-02, PT-S02/PT-S05, SETT-03/SETT-01, SETT-02,
`settlements.md`, SETT-02/PT-S13, SETT-01) and are out of scope for this ticket — checked, not
silently dropped.

| Finding | Source | Re-verified today | Disposition | Reason |
|---|---|---|---|---|
| `TerritorialRelation` typed-record proposal | `territory-control.md` Implementation Candidates; `places-territory-batch-11a-review.md` Implementation Candidates (L311, byte-identical duplicate) | Grepped `TerritorialRelation` across `src/` and `registries/` — zero hits | **Not a control-plane fact** | Forward-looking design proposal, explicitly `DEFERRED — no commitment in Rule Catalog phase`; not a claim about current Rule↔Mechanism reality. One entry, two citations — not two rows. |
| "Does Territory need its own authoritative relation model, or can it remain a derived projection?" | `territory-control.md` Open Questions #1 | Checked `registries/{rule_mechanism_edges,rule_classifications}.yaml` — no mechanism or classification answers this | **UNKNOWN** | Genuinely undecided design question, explicitly "Not decided here" in source. Not resolvable by re-verification. |
| "Whether `owner_faction_id`'s assignment traces to a real causal basis" | `territory-control.md` Open Questions #2; same fact as `places-territory-batch-11a-review.md` item 8 | Read `rule_classifications.yaml` TERR-02 row directly today (dated 2026-09-24) | **Already covered — TERR-02 `PARTIAL`** | TERR-02 already answers this with real, exhaustively-traced evidence (`FactionInfluenceService.process_influence_shift()`, `src/world/influence.py:33-71`) plus two confirmed gaps (world-gen-time bare assignment; ±50 vs ±100 threshold mismatch between two governing docs). No new row. |
| `owner_faction_id` control/sovereignty conflation + contested-claim divergence | `places-territory-batch-11a-review.md` Repository Findings item 1 | Read `rule_classifications.yaml` TERR-01/TERR-03 rows directly today | **Already covered — TERR-01/TERR-03 `CONFLICTING`** | Word-for-word match to the existing rows. No new row. |
| No residence/cultural-association field on Territory-adjacent state | `places-territory-batch-11a-review.md` Repository Findings item 2 | Read `src/core/state.py`'s `PlaceState`/`RegionState` fields today (via M1's own edge evidence, `src/core/state.py:344-383`) — confirmed no such field exists anywhere; cross-checked TERR-01's current evidence text — the sub-fact is not separately itemized there, only the control/sovereignty overload is | **Promote — amend TERR-01 evidence text** | Real gap in the *itemization* of already-existing evidence, not a new fact. Schema allows one classification row per Rule ID; TERR-01 already has one (`CONFLICTING`). Evidence text amended (see `registries/rule_classifications.yaml`); aggregate verdict unchanged, correct as-is. |

### Combat/Conflict

Scope per the ticket's own guard: `conflict-combat.md`'s 4 Repository Findings + 4 Open Questions
(this doc has **no** `Implementation Candidates` section — the equivalent content lives under
`Repository Findings`, triaged by content not section name), plus
`capability-progression-batch-07-review.md`'s Combat-scoped Repository Findings only. That review
export covers three rule families (Capability/Progression, Learning/Adaptation, Conflict/Combat);
verified directly against each of the 12 numbered findings' own content (not trusted from the
ticket's first-read guess, which — flagged as a process gap, not a blocker — never mentioned items
3, 8, or 9 at all): the Combat-scoped set is items **1, 2, 7, 12**. Items 3 (`BreakthroughService`,
Progression), 4 (combat-XP-farming counterforce, Progression), 5 (`TRAIN_SKILL` unreachable,
Learning/Progression), 6 (capability-improving mechanism gap, Learning/Progression), 8
(fame-to-followers, Progression PROG-07), 9 (non-HERO significance tracking, Progression CP-S15),
10 (success-only progression, Learning) and 11 (`max_xp_per_tick` doc/implementation mismatch,
Progression) are all Progression/Learning-domain — checked individually, out of scope.

**Important constraint on every Combat row below**: per this ticket's own asymmetry rule, **M3
records verified evidence — M3 does not assert a classification** (`SUPPORTED`, `INERT-OFF`, or
otherwise) for any Combat finding. Combat has zero mapping rows in either registry today
(confirmed by direct read); creating them, and judging their classification, is M4's own named
deliverable. No row below writes anything to `registries/rule_mechanism_edges.yaml` or
`rule_classifications.yaml`.

| Finding | Source | Re-verified today | Disposition | Reason |
|---|---|---|---|---|
| Perception-gated targeting (`TacticalDecisionSystem`/`PerceptionGate`) | `conflict-combat.md` Repository Findings #1; `capability-progression-batch-07-review.md` Repository Findings item 1 (duplicate, cross-cited) | Opened `src/engine/tactical.py:181,199` directly — `PerceptionGate.can_perceive()` genuinely runs inside the per-neighbor loop before `hostiles.append(n)` | **PROMOTE-AT-M4** | Confirmed current, matches source prose exactly. Evidence recorded for M4 to consume without re-investigating. |
| `combat_engagement` domain / `ENABLE_COMBAT_ENGAGEMENT` flag state | `conflict-combat.md` Repository Findings #2; `capability-progression-batch-07-review.md` Repository Findings item 2 (duplicate, cross-cited) | **See flagged catch below** | **PROMOTE-AT-M4, corrected evidence** | See below — this is the ticket's own re-verification requirement (AC2) catching a stale premise, not an incidental note. |
| No surrender/capture/forced-displacement combat outcome | `conflict-combat.md` Repository Findings #3; `capability-progression-batch-07-review.md` Repository Findings item 7 (duplicate, cross-cited) | Read `src/engine/combat.py`'s `outcome_kind` values and `src/engine/movement.py`'s `FLED` property today — no surrender/capture/displacement value exists among them | **PROMOTE-AT-M4** | Confirmed current, real gap. Evidence recorded for M4. |
| No non-combat Conflict superclass / contest-resolution mechanism | `conflict-combat.md` Repository Findings #4 | Re-read the source doc's own framing today | **Not a control-plane fact** | Source itself frames this as a stated Scope Boundary, not a gap needing a fix — no registry check applies. |
| `src/world/displacement.py` naming near-collision | `capability-progression-batch-07-review.md` Repository Findings item 12 (explicitly framed as clarifying item 7 above) | Read `src/world/displacement.py` header + `DisplacementService` today — calamity-driven population relocation (idea 65, "Named Refugee Threads"), gated on `RegionState.calamity_intensity >= 0.6`, structurally unrelated to any combat-defeat outcome | **Not a control-plane fact** | Naming collision only, not semantic overlap — confirmed exactly as the source claims. |
| Whether `ENABLE_COMBAT_ENGAGEMENT` should be turned on | `conflict-combat.md` Open Questions, item 1 | See flagged catch below | **Resolved by event, not open** | The question the world already answered — see below. Not carried forward as still-open. |
| Whether the `try/except Exception: pass` perception-gate fallback should fail closed | `conflict-combat.md` Open Questions, item 2 | Re-read `src/engine/tactical.py:198-202` today — code unchanged | **UNKNOWN** | Genuinely open, unresolved implementation question. This ticket's Out of Scope forbids deciding it (records findings, does not repair gaps). |
| Whether surrender/capture/forced-displacement should become real outcomes | `conflict-combat.md` Open Questions, item 3 | Confirmed no new outcome kind exists (same check as the Repository Finding above) | **UNKNOWN** | Real open design question, not decided here. |
| Whether a dedicated non-combat Conflict-resolution mechanism should be built | `conflict-combat.md` Open Questions, item 4 | No registry-checkable state change found | **UNKNOWN** | Real open design question, not decided here. |

**Flagged catch — `ENABLE_COMBAT_ENGAGEMENT` staleness (the ticket's own AC2 re-verification
requirement earning its keep):**

Both `conflict-combat.md` and `capability-progression-batch-07-review.md` (both dated
`last_verified: "2026-09-23"`) characterize `combat_engagement` as INERT/OFF — "gated behind
`ENABLE_COMBAT_ENGAGEMENT`, default OFF, never run in a real corpus profile." Re-verified directly
today against live state: `src/domains/optimization/feature_flags.py:32` is
`"ENABLE_COMBAT_ENGAGEMENT": FeatureMode.ON` — the live default, flipped 2026-09-14 by
`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (#190, commit `1e075b807`), nine days *before*
both source docs' own `last_verified` date. Wired live into the real tick pipeline
(`src/engine/pipeline.py:320`). `registries/mechanisms.yaml`'s own `combat_engagement` entry
already carries real observed runtime evidence (`verified.verdict: observed`, "posture gate moved
attacks 1960 -> 837"), contradicting the "nothing downstream consumes this" framing the same entry
explicitly flags as its own stale addendum.

**This is not an incidental correction.** Had this finding been ingested as prose without
re-verification, it would have entered the control-plane with its premise inverted — exactly the
failure mode `mechanism_identity_and_change_taxonomy.md` §4 is the precedent for. The fail-open
`try/except Exception: pass` half of the original finding (a separate, still-true robustness gap)
is unaffected and recorded unchanged above.

**Disposition reasoning (per the ticket owner's own written decision, `## Scoping Decisions
(2026-09-24, post-Investigate)` §D1):** dispositioned `PROMOTE-AT-M4` with corrected evidence, not
`CONFLICTING`. `CONFLICTING` belongs to the realization-classification vocabulary and describes
code-vs-Rule ("code exists and actively does the wrong thing relative to the Rule"). What is wrong
here is doc-vs-reality — a stale prose premise, not a demonstrated Rule violation. Classifying
documentation staleness as `CONFLICTING` would assert a semantic violation nobody has shown to
exist, the exact vocabulary laundering `docs/plans/status_axis_model.md` exists to prevent. This
triage log records that the flag is ON, live-wired, with observed runtime effect, and leaves the
classification call to M4.

**Not corrected in `conflict-combat.md` itself** — per §D2 of the same Scoping Decisions section,
out of scope for this ticket: `docs/world_rules/` is the frozen Rule Catalog, owned by
`world-rule-catalog-design`, not this track; and recording live flag state in two places (the doc
prose and this log) is how it drifted in the first place. The staleness has been reported to
`world-rule-catalog-design` separately.

## Summary

Territory: 5 findings triaged (2 not-a-control-plane-fact, 1 UNKNOWN, 2 already-covered — one via
an evidence-text amendment). Zero new registry rows; one existing row's evidence text amended.
Combat: 8 findings/questions triaged (3 PROMOTE-AT-M4, 2 not-a-control-plane-fact, 3 UNKNOWN, 1
resolved-by-event). Zero Combat rows written to either registry — Combat's mapping remains M4's own
deliverable. This is not an all-promote result (AC6): five findings land on UNKNOWN or
not-a-control-plane-fact.
