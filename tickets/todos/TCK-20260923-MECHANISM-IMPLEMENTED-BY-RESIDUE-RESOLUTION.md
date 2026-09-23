---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION
phase: open
date: 2026-09-23
tags: [architecture, investigation, schema, simulation-quality]
---

# TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION

## Title
The five `implemented_by`-unbound mechanisms with a real `state` claim, plus a registry rule that
`state: gap` means `implemented_by` doesn't apply

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Supersedes `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`, closed 2026-09-23 (see that
ticket's own Completion Summary for the full recount). That ticket's own hardest, mechanically
decidable target — `orphan` → 100% bound — is already met (13 of 13). `gated` is at 7 of 8. Overall
coverage is 76 of 93 mechanisms (`registries/mechanisms.yaml`, direct count of non-empty
`implemented_by`, not `len(report.bound)` from `mechanism_registry_completeness_check.py` — that
checker counts bound `src/domains/`/`src/systems/` *targets*, a different, narrower number, per the
counting caveat both tickets carry).

Of the 17 remaining unbound mechanisms, **12 are `state: gap`** — no implementing code exists for
these, so `implemented_by` is not applicable; they were never a real coverage hole, just an
uncorrected reading of the old ticket's own framing. **This ticket formalizes that as an explicit
rule** (Scope item 1) so `gap` mechanisms stop reading as missing coverage in every future report.

The real residue is **5 mechanisms** whose `state` claims something real
(`done`/`partial`/`gated`/`skeleton`) but which remain unbound. Direct re-check of
`registries/mechanisms.yaml` (2026-09-23) shows **3 of the 5 already have their own, separate, deep
investigation trail** — each one's own `verified` block explicitly says "flagged for the roadmap
session," and two already have a dedicated open ticket:

1. **`calamity_intensity`** (`state: done`) — `verified.verdict: contradicted`. Already tracked by
   `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (open). A 2026-09-20 re-check found the
   entry's own 2026-09-17 note ("wired code, data-starved") is itself now contradicted by evidence —
   `apply_calamity_consequences()` has zero real callers anywhere in `src/`, closer to `orphan` than
   `done`+`contradicted`. Not corrected unilaterally by that batch (its own rule: don't re-verify an
   already-verified entry). **This ticket's own job for this one: reconcile the entry's `state`
   against both findings, and bind or leave unbound on the reconciled state's own merits** — not
   re-derive the investigation from scratch.
2. **`xp_leveling`** (`state: partial`) — `verified.verdict: observed`. A 2026-09-20 Merge verdict
   was already recorded (`docs/plans/mechanism_identity_and_change_taxonomy.md` §8): merge
   `xp_leveling` into `evolution` (already bound to `src/engine/evolution.py::EvolutionSystem`) —
   recorded but **not executed**, deliberately, pending real review of the merge's own citation
   blast radius. Also tracked separately by
   `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (open, corpus-volume angle, distinct
   from the identity question). **This ticket's own job: either execute the already-recorded merge
   verdict (repointing citations) or make a documented decision not to, not leave the verdict
   sitting recorded-but-inert indefinitely.**
3. **`information_trust_deception`** (`state: gated`) — `verified.verdict: observed`, dated
   2026-09-16, framed as "flag-gated off." Already tracked in full by
   `TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED` (open) — a 2026-09-20 re-check found
   the most plausible candidate (`SourceTrustUpdateService.update()`) has zero real callers (not
   flag-gated, simply unreachable), and the actually-gated candidate
   (`InformationBeliefPhase.apply()`) reads as `belief_cycle`'s concern, not this one's. **This
   ticket does not duplicate that investigation — resolving it means resolving
   `TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED` itself**, which is this ticket's
   own dependency, not parallel scope.

The other 2 have no prior investigation trail at all — genuinely fresh work:

4. **`affection_relationship_bonds`** (`state: done`) — `verified.verdict: inconclusive`, dated
   2026-09-20. Zero literal `"affection"` matches anywhere in `src/` (a concept-name-not-a-symbol
   case). Three candidates checked and rejected as not-confident-enough
   (`RelationshipModel.private_trust`/`shared_quest_count`; `MarriageState`/`MarriageStatus`;
   `FactionSocialMemory`, faction- not entity-level). No `stored_artifacts/` citation trail exists
   for this id at all — the original seeding citation, if any, is unrecoverable.
5. **`social_memory`** (`state: skeleton`) — **no `verified` block exists at all.** Never
   investigated by any prior batch. The only registry-native starting point is `systems: [faction]`
   and its own atlas card (`faction-layer#4`, `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT`
   will have already re-read this card's own description for this exact ticket's benefit — check its
   findings before starting a fresh code search).

## Scope
1. **Add the `state: gap` → `implemented_by` N/A rule** to
   `docs/plans/mechanism_claims_as_tests_initiative.md` (the coverage-target section that section
   §7/Phasing or its own successor covers) and to
   `tools/mechanism_registry/mechanism_registry_completeness_check.py`'s own reporting — a `gap`
   mechanism should not appear in any future "N unbound" figure without a caveat distinguishing it
   from a real gap, ideally by excluding it from the raw "unbound" count entirely and reporting it
   under its own heading.
2. Resolve `calamity_intensity` and `xp_leveling` on the terms stated above — reconcile a
   contradicted-by-newer-evidence state, and either execute or explicitly decline the recorded merge
   verdict.
3. Resolve `TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED` (dependency, not
   duplicate scope) to close out `information_trust_deception`.
4. Real investigation for `affection_relationship_bonds` and `social_memory` — same rigor as every
   prior binding in this arc (real caller/symbol checks, not narrative-assumed), with a legitimate
   "no confident binding exists, `state` corrected instead" as an acceptable outcome, same as every
   other entry in this arc.
5. Any state correction found is propagated to every consumer artifact (atlas, capabilities, wiring
   map), not silently absorbed into the registry field alone — same discipline as every prior
   correction in this arc.

## Out of Scope
- Re-deriving the 3 already-investigated mechanisms' findings from scratch — build on the cited
  `verified` blocks and open tickets, don't re-run the same code search.
- Binding any of the 12 `state: gap` mechanisms — by definition, nothing to bind.
- Any binding-coverage work beyond these 5 — this ticket is deliberately the narrow tail, not a
  reopening of the general coverage-extension effort.

## Acceptance Criteria
1. The `state: gap` → N/A rule exists in both a doc and the completeness checker's own reporting,
   not just stated in this ticket.
2. Each of the 5 residual mechanisms has a disposition: bound, state corrected (with a real
   `verified` block), or an explicit "still genuinely undecided, here's exactly why" note distinct
   from what already exists — no mechanism leaves this ticket in the same ambiguous state it
   entered in.
3. `TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED` is closed as part of resolving
   item 3.
4. Any state correction is propagated to every consumer artifact; convergence tests
   (`test_mechanism_artifact_convergence.py`, `test_real_wiring_map_has_no_drift_against_the_real_registry`)
   still pass afterward.

## Related Tickets
- `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` (closed, superseded by this ticket).
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (open) — `calamity_intensity`.
- `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (open) — `xp_leveling`, corpus-volume
  angle.
- `TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED` (open) — `information_trust_deception`,
  this ticket's own dependency for item 3.
- `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION`,
  `TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION` (closed) — the
  batches that investigated 4 of these 5 and explicitly flagged them for a roadmap-level decision.
- `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT` — re-reads `social_memory`'s own atlas
  card description as part of its own unrelated sweep; check its findings before this ticket starts
  fresh on that mechanism.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` — coverage acceptance targets section.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §8 — the recorded-but-not-executed
  `xp_leveling` → `evolution` merge verdict.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/mechanism_registry_completeness_check.py`
- `src/domains/information/trust.py`, `src/domains/information/phase.py` (`information_trust_deception`)
- `src/engine/evolution.py` (`xp_leveling` merge target)
- `src/systems/calamity/` or equivalent (`calamity_intensity` — locate via the cited service)

## Assumptions / Open Questions
- Whether `calamity_intensity` and `xp_leveling`'s own flagged "roadmap session" decisions
  (state-shape reconciliation, merge execution) are within a `standard`-tier implementer's authority
  to execute directly, or need the roadmap/planning session's own sign-off first — genuinely unclear
  from the existing notes; check with the planning session before executing the merge specifically,
  since it changes what future citations point at.

## Implementation Notes
Filed 2026-09-23, hand-orchestrated, as the replacement half of a peer-planning-directed batch that
also closed `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` and ran the atlas caveat
audit. Numbers re-verified directly against live `registries/mechanisms.yaml` before filing, not
taken from the peer's own relayed figures on faith (they matched exactly: 76/93 bound, 13/13 orphan
bound, 5-mechanism residue with these exact ids).

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open.
