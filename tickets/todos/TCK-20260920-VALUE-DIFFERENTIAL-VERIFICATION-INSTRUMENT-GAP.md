---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP
phase: open
date: 2026-09-20
tags: [simulation-quality, testing, cognition]
---

# TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP

## Title
The differential scenario harness can only detect "does this mechanism run" — it cannot detect a
mechanism that runs faithfully and changes nothing; `personality` is the first case that needs it

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Found while pre-screening `personality` for `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-
RUNTIME-VERIFICATION`'s batch 2, filed rather than forced into that batch, per direct peer
instruction: `personality` doesn't fit the harness's own reachability-differential shape at all.

`PersonalityComponent` (greed/bravery/sociability/industry) is a pure data component, always
present on every entity, read unconditionally at ~8 real call sites (`src/engine/tactical.py`,
`src/engine/movement.py`, `src/engine/cognition.py`, `src/ai/goals/scorers.py`,
`src/systems/social_systems/clan_lifecycle.py`, `src/systems/social_systems/party_lifecycle.py`).
"Is it reachable" is not the interesting question for it — it always is, trivially, since it's a
required field on every entity, not an optional phase behind a gate. The real question is: **do
different personality values actually produce different observable behavior** — does a high-bravery
entity make a different combat-vs-flee decision than a low-bravery one, given the same situation?
That's a *value* differential, not the *presence/absence* differential every scenario in this
program so far has built.

**Named as its own gap, per peer framing**: this harness currently cannot detect a mechanism that
executes faithfully and changes nothing — a dormancy of a different kind from the ones this program
has been finding (`perception`, unreached; `temporal_pressure`, gated) and arguably the more common
one for RPG mechanics specifically. Stats, traits, and modifiers don't usually fail by not running;
they fail by not mattering. `personality`'s own real read sites (combat-vs-flee scoring in
`scorers.py`) are a plausible first instance, but not confirmed — nobody has checked whether varying
`bravery` actually changes `scorers.py`'s own output, only that the field is read.

## Scope
Not scoped here — this ticket names the instrument gap and the first candidate case, per explicit
instruction ("don't build it now... leave `personality` unverified rather than giving it a verdict
the instrument can't support"). A future ticket/program would need to:
1. Design a value-differential assertion shape (distinct from the present/absent shape
   `docs/plans/mechanic_verification_scenarios_proposal.md` §3.3/§5 already codifies) — likely:
   stage two entities identical except for one real value (e.g. `bravery`), same real precondition,
   assert their real, observable outputs differ in the direction the value's own documented meaning
   predicts.
2. Apply it to `personality` first (the concrete case found here), then assess how many other
   registered `done` mechanisms are actually stats/traits/modifiers with the same shape (not scoped
   here — a sizing question for whoever picks this up, same discipline as
   `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`).
3. Decide whether `personality`'s own registry entry should get a `verified` block at all under the
   new instrument, or whether "unverified, value-differential instrument doesn't exist yet" is
   itself the honest, recorded state in the meantime.

## Out of Scope
- Any code change to `personality` or its consumers.
- Any other mechanism in `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`'s own
  batch — this is explicitly a separate, later program, not folded into the current one.

## Acceptance Criteria
(none yet — gap-naming ticket; criteria belong to whichever future ticket picks this up)

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — where this gap was found
  (batch 2's own pre-screen)

## Related Docs
- `docs/plans/mechanic_verification_scenarios_proposal.md` — the existing (presence/absence-shaped)
  differential harness this gap sits alongside, not inside

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/core/state.py::PersonalityComponent`
- `src/ai/goals/scorers.py` (the plausible first real value-differential candidate — combat-vs-flee
  scoring)

## Assumptions / Open Questions
Whether `personality`'s own values actually change any real output is genuinely unverified, not
assumed either way — that's exactly the gap this ticket exists to name, not to prejudge.

## Implementation Notes
(none yet — not started)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)
