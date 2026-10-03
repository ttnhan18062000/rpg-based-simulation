---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK

## No fix lands in this ticket
`investigation.md` found real, precise, high-confidence evidence (zero variance across 16 real
gap measurements across 3 distinct combat pairs) that readiness cooldown alone — not a compounded
readiness + brain-cadence effect, the ticket's own original hypothesis — is the real, sole
pacing mechanism for sustained combat, and that it operates exactly as documented
(`docs/mechanics/02_combat_laws.md` §7's own explicit "cooldown gate" framing). Per the
Uncertainty Rule and this session's own established precedent for investigations that find the
evidence doesn't support the originally-hypothesized problem, this ticket closes as
investigation-only.

## Rejected alternative
- **Tuning `readiness_speed`'s default value now**: rejected — no real evidence in this ticket's
  own investigation establishes the current 11-tick-per-hit rhythm is *too slow* relative to any
  real design target; it is simply what the documented mechanic produces. Changing a balance
  constant without a real, justified target and a corpus-verified before/after comparison would
  be an unjustified, out-of-scope change for a bug-investigation ticket.
- **Desynchronizing the readiness regen rate from the brain-cadence interval**: rejected —
  investigation found the two mechanisms do NOT actually compound for sustained combat (only for
  first-engagement and re-targeting, both already addressed by sibling tickets), so there is no
  real compounding effect to desynchronize.

## Verification plan
N/A — no code change in this ticket. If a future ticket decides to tune `readiness_speed` based
on the separate `TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK` ticket's own real
kill-volume findings, that ticket's own verification plan would need a real, live corpus
before/after comparison of the readiness-tuned rate.
