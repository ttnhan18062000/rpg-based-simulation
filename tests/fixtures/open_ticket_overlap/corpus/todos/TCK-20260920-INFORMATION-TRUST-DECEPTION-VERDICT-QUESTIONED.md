---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED
phase: open
date: 2026-09-20
tags: [architecture, schema]
---

# TCK-20260920-INFORMATION-TRUST-DECEPTION-VERDICT-QUESTIONED

## Title
`information_trust_deception`'s own "flag-gated" `verified` note doesn't match the best real
candidate found — a genuine "which mechanism is this actually?" question, not decided here

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`registries/mechanisms.yaml`'s `information_trust_deception` entry (`layer: entity`,
`systems: [cognition]`, `state: gated`) carries a `verified` block dated 2026-09-16: "Code read
confirms the mechanism is correctly built; currently flag-gated off." No specific code citation was
given.

While resolving the entity-layer unbound-claims batch
(`TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION`), this claim was checked directly.
The most plausible named candidate, `SourceTrustUpdateService.update()`
(`src/domains/information/trust.py`), has **zero real callers anywhere in `src/`** — not
flag-gated-off (a real caller exists, behind an `ENABLE_*` check), simply never invoked at all. That
is a different, and inconsistent, claim shape from what the 2026-09-16 note describes.

A second candidate, `InformationBeliefPhase.apply()` (`src/domains/information/phase.py`), is real
and genuinely gated behind `ENABLE_BELIEF_ASSIMILATION` — matching the note's own "flag-gated"
framing structurally. But its own actual concern (observation routing and belief assimilation)
reads closer to the separately-registered `belief_cycle` mechanism's own scope than to
"trust/deception" specifically. Binding it here without more confidence risks the exact
misattribution shape already caught once this session (the `trauma` incident, `docs/plans/
mechanism_claims_as_tests_initiative.md` §3.2).

The original 2026-09-16 investigator's own working notes (whatever code they actually read) were
not found anywhere in `stored_artifacts/` — there is no trail to recover what "code read confirms"
was actually pointing at.

## Scope
- Determine which real code (if any) `information_trust_deception` actually refers to —
  `SourceTrustUpdateService`, `InformationBeliefPhase`, something else entirely, or genuinely no
  single real implementation (in which case the mechanism itself may need a state correction, not
  just a binding).
- If the original 2026-09-16 investigation's own reasoning can be reconstructed (session logs,
  related tickets from that date), use it rather than re-guessing from scratch.
- Resolve whether this is one mechanism or should be split (trust-of-sources vs. deception, which
  may be two different concepts sharing one bundled name — check against this registry's own
  identity rule, `docs/plans/mechanism_identity_and_change_taxonomy.md` §1).

## Out of Scope
- Fixing or wiring any code found to be genuinely unused — this ticket is about correctly
  identifying and citing the real implementation (or correcting the state if none exists), not
  building anything new.
- `belief_cycle`'s own entry — already resolved and bound this session
  (`src/systems/strategic_systems/belief.py::BeliefCycleSystem`), not reopened here even though
  `InformationBeliefPhase` was considered as a candidate for this ticket's own mechanism.

## Acceptance Criteria
- [ ] A real, cited implementation for `information_trust_deception`, or an explicit,
      evidence-backed state correction if none exists.
- [ ] The `verified` block's own "flag-gated" framing either confirmed against a real citation or
      corrected.

## Related Tickets
- `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION` — where this discrepancy was
  found while resolving a different (unbound-claims) task; not resolved there per that batch's own
  scope guard against re-verifying already-verified entries.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` §3.2 — the misattribution failure class this
  ticket's own investigation must avoid repeating.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §1 — the identity rule, relevant if this
  turns out to be a bundled name needing a split.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up. (The original 2026-09-16
investigation's own artifacts, if they existed, were not found.)

## Related Code Areas
- `src/domains/information/trust.py` (`SourceTrustUpdateService`)
- `src/domains/information/phase.py` (`InformationBeliefPhase`)
- `registries/mechanisms.yaml` (`information_trust_deception` entry)

## Assumptions / Open Questions
Whether the 2026-09-16 "code read" was ever accurate for some code that has since changed/been
removed, or was never precisely cited in the first place, is not known — no trail exists either way.

## Implementation Notes
Not yet started.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
Open. Filed 2026-09-20 per peer-relayed direction, routing a wrong-verdict-shaped finding (a
`verified` note whose claim doesn't match the best candidate evidence) into its own scoped ticket
rather than resolving it in passing during an unrelated binding batch.
