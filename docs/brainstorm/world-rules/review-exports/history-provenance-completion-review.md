---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: History / Provenance — Milestone A Completion Pass

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess this pass without opening every canonical file. It is never edited directly as the fix
for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

Not a numbered batch — the Milestone A completion pass `roadmap.md` planned after Batch 03,
before any per-domain Milestone B batch begins. Drafts History/Provenance's own Rules for the
first time; the family was only named at scope level during Batch 01. Six Rules total, all
either migrated from Causality (CAUSE-05/CAUSE-06's persistence-specific substance) or
consolidated from already-accepted rules (OWN-04, OWN-06, REACH-04) — two (HP-01, HP-02) restate
existing findings in this family's own home, and none introduce a genuinely new claim this
Catalog hasn't already made somewhere.

## Canonical files included

- `foundations/history-provenance.md` (HP-01–06)
- `scenarios/history-provenance-completion.md` (HP-S01–S02)
- `foundations/causality.md` (CAUSE-05/CAUSE-06, updated to reflect the completed migration —
  no semantic change, only forward-reference notes resolved to actual references)

## Rule Inventory

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| HP-01 | Historical Continuity Survives Ordinary Change | A subject's causal history stays attached through form/state/occupant changes. | Accepted (restates ID-05/TIME-07) |
| HP-02 | Provenance ≠ Truth | A record's causal ancestor is tracked separately from whether its content is true. | Accepted (new claim, this family's own) |
| HP-03 | Persistence Bounded by Declared Reach | Migrated from CAUSE-05 — retention must be honestly bounded, not silently universal. | Accepted (migrated) |
| HP-04 | Compression Must Not Fabricate | Migrated from CAUSE-06 — compression may drop detail, never invent a causal link. | Accepted (migrated) |
| HP-05 | Significance May Legitimately Fade | Migrated from CAUSE-06 — fading weight ≠ erasure ≠ fabrication ≠ outcome value. | Accepted (migrated) |
| HP-06 | Historical Record ≠ Present Authority/Reach/Truth | Consolidates OWN-06 + REACH-04 + OWN-04 in one place for future chronicle content authors. | Accepted (consolidation, no new claim) |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Deferred domain dependencies | Result |
|---|---|---|---|---|---|
| HP-S01 | A Lineage's History Survives Three Transformations | succession → evolution → death-referenced-in-feud, history intact throughout | History/Provenance, Identity, Authority | Family/lineage | Covered |
| HP-S02 | A False Rumour With Real Provenance | witness reports false claim → provenance real, content false | History/Provenance, Causality | Perception/knowledge/information | Covered |

HP-03–HP-06 are evidenced by direct reuse of `FND-S04`, `FND-S09`, `FND-S20`, `FND-S21`
(Batch 01) and `TAR-S13` (Batch 02) — no new scenario rows, per this pass's own stated economy
(re-tracing an already-migrated finding adds nothing).

## Coverage Summary

- Historical continuity across three distinct kinds of change (succession, form change, death)
  — HP-S01
- Provenance vs. truth, the one genuinely new claim this pass makes — HP-S02
- Declared-reach retention, compression discipline, significance fading, and the
  record-vs-authority/reach/truth consolidation — all reused directly from Batch 01/02 evidence

## Deferred Semantics

- HP-04's compression-tier mechanism and HP-05's significance-fading mechanism remain
  undesigned — this pass drafts the constraints, not the mechanisms, per this family's own
  stated non-goal (carried forward unchanged from the scope-only draft).
- Whether Batch 04 (Space/Environment/Movement, next) needs its own History/Provenance
  touchpoint ("historical location significance") is not pre-decided — that batch's own
  investigation should cite this family rather than assume a link in advance.
- Chronicle/legend/notability/naming/myth/rumour-propagation content stays entirely with
  Perception/knowledge/information and Social relations & identity, unchanged from the
  scope-only draft's own exclusion.

## Cross-domain findings

- History/Provenance ↔ Causality: HP-03/HP-04/HP-05 are direct migrations, not new findings —
  `causality.md`'s CAUSE-05/CAUSE-06 now carry completed-migration notes rather than forward
  references, with zero semantic change to either family's causal-validity core.
- History/Provenance ↔ Identity: HP-01 restates ID-05/TIME-07 at this family's own point of use;
  HP-02 explicitly resolves the "is this the same 'provenance' as ID-04's?" open question from
  the scope-only draft (related uses of the same word at different scales: record-ancestor vs.
  subject-lineage).
- History/Provenance ↔ State Ownership/Reach: HP-06 consolidates OWN-04, OWN-06, and REACH-04
  into one place for future chronicle-content authors — explicitly not a new claim on any of the
  three.

## Open questions

1. HP-04/HP-05's actual mechanism design (compression tiers, fading rates) — deferred to
   whichever future need first requires one; not this pass's job, per its own stated non-goal.
2. Whether Batch 04 needs a History/Provenance touchpoint — left for that batch's own
   investigation, not pre-decided here.

## Repository evidence

No CONFLICTING or UNKNOWN findings. Two MISSING findings, both already known and unchanged by
this pass: no compression-tier mechanism (HP-04) and no significance-fading mechanism (HP-05)
exist anywhere in `src/domains/chronicle/` or `src/domains/fame/legend.py`. All other evidence
is reused directly from Batch 01/02's own already-verified citations (`LifecycleSystem`,
`EvolutionSystem`, `ClanLifecycleService`, `BeliefEntry`/`LeadState`/`process_rumor`) — no
re-verification was performed, consistent with this pass's own stated economy.

## Owner-attention decisions

- Whether HP-04/HP-05's mechanism design should be prioritized ahead of Batch 04, given that
  "historical location significance" (one of Batch 04's own stated interests) may end up wanting
  a working fading/compression mechanism sooner than otherwise expected.

## Starter-candidate disposition summary

Six rules drafted for the first time (HP-01–06): 2 new claims stated in this family's own home
for the first time (HP-01 as a restatement, HP-02 as this pass's one genuinely original
contribution), 3 direct migrations from Causality (HP-03/HP-04/HP-05), 1 explicit consolidation
of three already-accepted rules (HP-06). All 6 accepted; 0 rejected, 0 split, 0 merged. This
pass resolves both of the scope-only draft's own open questions (the ID-04-vs-HP-02 "provenance"
question; whether this family gets its own scenario file — yes, a small one).

---

> **HISTORY / PROVENANCE MILESTONE A COMPLETION PASS: READY FOR HIGH-LEVEL EXTERNAL REVIEW.**

All required artifacts exist: one rule-family file (6 rules), one small scenario file (2 new
scenarios, 4 rules reusing existing evidence), this review export, and `causality.md`'s
completed-migration notes. No contradiction was found, against Batches 01/02/03 or within this
pass — by design, since 5 of 6 rules are migrations or consolidations of already-accepted
findings, not new claims requiring independent verification. Milestone A (Identity, State
Ownership, Causality, Time, Authority, Reach, Capability, Cost, Capacity, Resource,
Transformation, History/Provenance) is now fully drafted. Per the batch-04 instruction: Batch 04
(Space/Environment/Movement) begins only after this pass receives high-level review — not
automatically upon this export's completion.
