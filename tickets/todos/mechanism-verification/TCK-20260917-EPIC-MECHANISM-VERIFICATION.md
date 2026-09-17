---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-EPIC-MECHANISM-VERIFICATION
phase: open
date: 2026-09-17
tags: [architecture, documentation, schema]
---

# TCK-20260917-EPIC-MECHANISM-VERIFICATION

## Title
Mechanism registry follow-up work: claims-as-tests detectors, binding coverage, and the atlas
caveat audit — the epic's own next phase, not absorbed into the closed registry PR

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260915-EPIC-MECHANISM-REGISTRY` closed with the registry itself built and converged into
three artifacts. The work that followed in the same PR (#209) — completeness passes,
`implemented_by` binding, the combined view, the tools package move, claims-as-tests phase 1, the
orphan-state batch verification — surfaced four real, separately-scoped follow-up items that were
never given a home together: two report-only detectors, a binding-coverage precondition those
detectors need, and an atlas re-read audit. This epic exists so they're tracked as one deliberate
sequence rather than four independent todos someone has to notice are related.

**Added 2026-09-17, sequenced first**: `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`.
The registry's 89 nodes inherited accidental granularity (71 from atlas cards, 11 from directory
structure) with no rule for what one mechanism is — some entries bundle two or three concepts
(`regional_trauma_hazards_sovereignty`, `inventory_trade_conservation`), others split one concept
across three rows (combat). This surfaced as a real cost, not a hypothetical one: coverage
extension (item 2 below) is about to bind 63 entries, and the identity-rules ticket can **split**
some of them — `action_pacing_readiness` (already bound, already verified) is its own worked
example of an entry that should split into a working gate and a starved scaling half sharing one
overloaded verdict today. Splitting after binding means redoing that subset's binding; splitting
first avoids it, which is why this now runs before coverage extension rather than after it (see
`SEQUENCE.md`'s own updated "Why This Order Matters" for the full reasoning and the correction to
its prior text).

Scoping document: `docs/plans/mechanism_claims_as_tests_initiative.md`.

**Scope limit, explicit**: this epic holds exactly these five tickets, nothing more. It does not
absorb the other ~35 tickets already sitting in `tickets/todos/` — most predate this PR and belong
to a separate, dormant-mechanism arc (calamity producers, lair trauma, worldbuilding, parity gates,
performance costs). `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` in
particular stayed at `tickets/todos/` root when it closed — it was an RPG simulation defect, not
registry infrastructure, even though it was found by this same epic's own verification work.
`TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — a real sibling, blocked on the
identity-rules ticket above — is filed at `tickets/todos/` root rather than in this epic for the
same reason: it is P2, and a P1 coverage-extension ticket should not wait on a P2 tier-system
ticket just because they touch the same registry file. An epic that absorbs unrelated tickets
stops meaning anything.

## Scope
1. `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` — state what makes one mechanism one
   mechanism, and what a design proposal does to the registry (a seven-kind change taxonomy), then
   test both against the registry's own bundled entries. Runs first; see Request Summary.
2. `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` — extend `implemented_by` coverage
   beyond its current 26 of 89 mechanisms. Filed by this epic specifically because it was the one
   piece of clearly-necessary follow-up work that existed only in conversation, never as a real
   ticket — the same orphan-knowledge failure shape this whole arc exists to catch.
3. `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` — detect status-vocabulary in
   atlas/capabilities/wiring-map prose; status belongs to the registry, never to hand-written
   descriptions.
4. `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` — flag a PR that changes
   `implemented_by`-cited code without touching the mechanism's own registry entry.
5. `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT` — re-read every mechanism card's
   description for effect-level caveats the badge doesn't carry (`camp`'s own shape), and against
   `docs/guidelines/intentional_divergences.md` for stale architecture framing
   (`motivation_doctrine`'s own shape).

See `tickets/todos/mechanism-verification/SEQUENCE.md` for the required implementation order and
the reasoning behind it.

## Out of Scope
- Every other ticket currently in `tickets/todos/` — not absorbed into this epic, per the scope
  limit stated above.
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` specifically — an RPG
  simulation defect this arc's own verification work found, not registry infrastructure; stays at
  `tickets/todos/` root (closed 2026-09-17, root-caused as content-composition/pacing).
- `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — P2, blocked on identity rules, filed
  at `tickets/todos/` root rather than in this epic so it never gates the P1 items here.
- Direct implementation — this is an epic-tier ticket; it tracks the five children, per the
  standard epic-tier routing rule (scope only, no direct implementation).

## Acceptance Criteria
1. All five children exist under `tickets/todos/mechanism-verification/`, in the order
   `SEQUENCE.md` specifies.
2. `SEQUENCE.md` names `docs/plans/mechanism_claims_as_tests_initiative.md` as the epic's own
   `tracking_doc`.
3. Both known drift items between the initiative document and this epic's own measured findings
   (§4.3's own forward-looking-only framing; phase 1's sample bias) are recorded here, not left to
   silently disagree with the closed tickets that found them.
4. The identity-rules ticket is sequenced before coverage extension, with `SEQUENCE.md`'s own "Why
   This Order Matters" text updated to match — not left arguing for the order this epic no longer
   uses.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — the closed parent epic this one continues from.
- `TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION`,
  `TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION` — the two closed tickets whose own
  measured findings are recorded here (see Implementation Notes) so they don't drift out of view
  once their own ticket files are historical.
- `TCK-20260917-MECHANISM-REGISTRY-RELOCATION` — moved the registry to `registries/mechanisms.yaml`
  immediately before this epic was filed.
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` (closed) and its own
  successor `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` — the RPG-defect arc this
  epic's own verification work fed, kept at `tickets/todos/` root per the scope limit above.
- `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — sibling ticket, blocked on this
  epic's own first child, filed at `tickets/todos/` root (see Out of Scope).

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` — this epic's own scoping document.

## Related Stored Artifacts
None yet — epic tier, no direct implementation of its own.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/`
- `docs/brainstorm/rpg_feature_atlas.html`, `simulation_capabilities.html`,
  `rpg_simulation_wiring_map.html`

## Assumptions / Open Questions
None outstanding beyond the two drift items recorded in Implementation Notes, which are known and
explicit, not silent.

## Implementation Notes

**§4.3 of the initiative document is known-incomplete, recorded here rather than left to silently
disagree with the evidence.** §4.3 describes the registration gate for new mechanisms as
forward-looking only — a CI check that stops *new* unregistered mechanisms from being added, with
no claim about the existing 75. `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` (closed)
directly disproved that framing's own sufficiency: a forward-looking-only gate would have left the
11 mechanisms that pass found invisible indefinitely, since none of them were *new* — they existed
in `src/domains/`/`src/systems/` the whole time, just never carded by the atlas Foundation's own
seed read from. The standing enumeration check
(`tools/mechanism_registry/mechanism_registry_completeness_check.py`) is the other, necessary half
— a one-time registration gate and a recurring completeness check are two different mechanisms,
not one. Whoever next edits the initiative document should reconcile §4.3's own text with this
finding rather than leave the document and the evidence disagreeing.

**Phase 1's own result was measured on a biased sample — both numbers matter, not just one.**
`TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION`'s first real run checked 20 (later 26) of
89 mechanisms — every one of them mechanisms this same session had just personally investigated
and bound while fixing already-known defects. "Zero new confirmed defects" against that sample is
close to tautological: it ran against the cleanest, most recently hand-verified slice of the
registry, not a representative one.
`TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION` then targeted the `orphan` state
specifically (chosen because it was suspected weakest) and found 4 of 6 newly-checked orphans
wrong (67%) — up to 6 of 11 `orphan` mechanisms wrong when combined with the 2 already known.
Whoever resumes this work needs both numbers and both caveats together, or they will draw a
conclusion from whichever one they happen to find first: neither "the registry is basically
accurate" nor "the registry is 60%+ wrong" is the right read from either result alone.

**A figure correction, found while filing this epic**: several prior reports in this arc (including
this session's own PR #209 description) stated `implemented_by` coverage as "24 of 89." Direct
recount says **26 of 89** — the completeness checker's own `len(report.bound)` counts bound
`src/domains/`/`src/systems/` *targets*, not *mechanisms with a binding*, and the two diverge
because several mechanisms bind multiple files (`fame`, `fidelity_drift`, `belief_institution`,
`commitment_pressure_consequences`) and two bind paths outside that checker's own scope entirely
(`declared_cognition_schema`, `committed_intentions` → `core/cognition.py`). Recorded here so the
correct figure is the one that persists past this epic's own filing.

## Test Summary
Not applicable — epic tier, scope-only.

## Files Changed
- `tickets/todos/mechanism-verification/` — new folder: this epic, `SEQUENCE.md`, and its four
  children (one new, three relocated from `tickets/todos/` root).

## Completion Summary
Open. Tracks four children in the order `SEQUENCE.md` specifies. Closes when all four close.
