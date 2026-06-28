---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-E11B-PERSONALITY-AUDIT
phase: done
date: 2026-06-28
tags: [personality, ocean, calibration, audit, observability, p3]
---

# TCK-20260628-E11B-PERSONALITY-AUDIT

## Title
Personality Calibration Audit: 1k-tick OCEAN trait → behavioral diversity analysis

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Run D05-style behavioral audit with LIGHT observability (P2O personality snapshots
enabled) at 1,000+ ticks. Analyze per-entity personality trait vs. route diversity
to confirm OCEAN traits produce distinct behavioral clusters and identify calibration
gaps for E11C weight tuning.

## Scope
1. Write `tools/personality_audit.py` — runs 1k-tick sim with LIGHT obs, reads
   `entity_personality_snapshots.jsonl`, computes Shannon entropy of project_kind
   distribution per entity, groups by OCEAN quartile.
2. Add `make personality-audit` target to Makefile.
3. Run audit and save report to `reports/personality_audit.json`.
4. Document calibration findings.

## Out of Scope
- OCEAN weight tuning (E11C).
- Abandonment rate measurement (E11D).

## Acceptance Criteria
- [x] `make personality-audit` runs without error.
- [x] Report saved to `reports/personality_audit.json`.
- [x] Personality traits confirmed non-zero (E11 initialization working).
- [x] At least one trait produces clear behavioral differentiation.
- [ ] ≥ 3 statistically distinct behavioral clusters correlated with OCEAN bands.
      *Partially met: bravery differentiates combat-facing clearly; greed/sociability
      need E11C weight tuning before clusters are fully distinct.*

## Related Tickets
- Parent: TCK-20260628-E-PERSONALITY-CALIBRATION
- Prerequisite: TCK-20260627-P2O-ENTITY-PERSONALITY-OBS (DONE)
- Next: TCK-...-E11C-WEIGHT-TUNING (greed/sociability weight uplift)
- Next: TCK-...-E11D-ABANDONMENT-RATE (industry/bravery abandonment comparison)

## Related Docs
- `docs/audits/D05_entity_differentiation.md` — D05 methodology
- `docs/mechanics/04_strategic_cognition.md` — OCEAN weight application

## Related Code Areas
- `tools/personality_audit.py` (new)
- `src/observability/personality/recorder.py` — snapshot emitter
- `src/domains/adventure/scoring.py` — OCEAN personality_bias computation

## Implementation Notes
**Calibration findings (1000-tick audit, urban_political, seed=42):**

Entity stats: 33 entities, 81 snapshots, 30/33 with non-zero OCEAN traits.

OCEAN trait ranges (non-zero entities):
- bravery:     n=30, mean=0.569, range [0.052–0.939]
- greed:       n=30, mean=0.481, range [0.003–0.942]
- industry:    n=30, mean=0.557, range [0.035–0.993]
- sociability: n=30, mean=0.449, range [0.027–0.981]

Behavioral diversity (Shannon entropy) by quartile:
| Trait       | Q1 (low) | Q4 (high) | Delta  | Verdict             |
|---|---|---|---|---|
| bravery     | 1.3443   | 0.6250    | -0.719 | ✅ STRONG effect    |
| industry    | 1.1740   | 0.9481    | -0.226 | ✅ MODERATE effect  |
| greed       | 1.0481   | 1.0142    | -0.034 | ⚠️ WEAK effect     |
| sociability | 1.1270   | 1.0833    | -0.044 | ⚠️ WEAK effect     |

Key behavioral finding:
- High bravery (≥0.5): 18 entities → combat_engage PRESENT in dominant projects
- Low bravery (<0.25): 6 entities → combat_engage ABSENT (only NONE + town_return)
- Bravery → combat/no-combat split is clear and mechanistically expected.

**Gap confirmed for E11C**: greed and sociability have near-zero behavioral impact.
In `src/domains/adventure/scoring.py`, greed applies to economic routes and
sociability to cooperation routes — but economic/social projects are underrepresented
in urban_political at 1k ticks (harvesting: 2, combat_engage: 22). The scoring
weights may be correct but the opportunity set is thin. E11C should investigate
whether weight uplift or scenario content (more economic/social route opportunities)
is the right fix.

## Test Summary
- Audit script produces valid JSON report.
- Personality traits confirmed non-zero via to_canonical_dict() output.
- `make personality-audit` works end-to-end.
- No regression: existing tests unaffected.

## Files Changed
- `tools/personality_audit.py` (new)
- `Makefile` (+personality-audit target)
- `reports/personality_audit.json` (generated, not committed)

## Completion Summary
Audit infrastructure built and run. Confirmed: (1) OCEAN initialization working,
(2) bravery → combat behavior differentiation is clear, (3) greed/sociability
near-zero impact — opportunity set too thin at 1k ticks, or weights need uplift.
`make personality-audit` is the reproducible entry point for future calibration runs.
