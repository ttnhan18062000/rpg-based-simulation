# Investigation — D06 Long-Run Simulation Health

## Prior Context
- D03 found behavioral stasis by tick 20 (RC1/RC2/RC3); those are now fixed.
- TCK-20260518-LONG-RUN-STABILITY ran 1,000 entities × 5,000 ticks proving bounded memory/compute — but that was against the pre-RC-fix engine where the adventure pipeline was inert.
- SpawnService and ResourceEcologyService implemented in TCK-20260428-PH9-WORLD-LIFECYCLE.
- D03 F4: 25% attrition (5/20 entities die in first ~15 ticks) with no replenishment observed in 200-tick runs.

## Key Risk Areas
1. Entity attrition without replenishment — if SpawnService doesn't fire, entity count approaches 0.
2. Resource node depletion without ecology recovery — if ResourceEcologyService doesn't fire, nodes exhaust.
3. Stale-project rejection cascade — D03 found 0.97–4.63 rejections/tick; at 1,000 ticks this is 970–4,630 cumulative.
4. PerformanceBudgets reset confirmed at `kernel._phase_init()` — but still only 500 calls/tick budget; at 20 entities that is 25 calls/entity which is fine per-tick.

## Findings
(populated after runs complete)
