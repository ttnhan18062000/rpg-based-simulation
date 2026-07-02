# obs-isolation — Implementation Sequence

Epic: `TCK-20260702-OBSISO-EPIC`. Source analysis: `docs/plans/observability_process_isolation.md` (gaps G1–G5, verified 2026-07-02).

| Order | Ticket | Gap | Why this order |
|---|---|---|---|
| 1 | TCK-20260702-OBSISO-TRACE-ASYNC | G4 | Independent of broker work; removes the standing hot-path contract violation and cleans the baseline that ticket 4 will benchmark |
| 2 | TCK-20260702-OBSISO-BROKER-CONFIG | G1+G3 | Makes broker mode functional end-to-end (stream identity + kernel routing); prerequisite for any broker-mode testing |
| 3 | TCK-20260702-OBSISO-WORKER-PARITY | G2 | Needs a connectable broker pipeline (ticket 2) to run its parity/integration tests meaningfully |
| 4 | TCK-20260702-OBSISO-ISOLATION-PROOF | G5 | Benchmarks all three modes — requires 1–3 landed so the numbers reflect the fixed system |

## Dependency Notes
- Ticket 1 can run in parallel with ticket 2 (no shared files except kernel init/shutdown regions — coordinate merge order if concurrent).
- Ticket 3's parity test doubles as the acceptance evidence for ticket 2's config unification; if 3 reveals a scorer reading live engine state, that is a new isolation finding — file it, do not widen scope.
- Ticket 4 sets the numeric overhead bands; until it lands, R1 remains contract-asserted, not measured.
- Grade anchors: tickets 1–3 must not change in-process grades (`make evaluate --dry-run` clean). If any diff appears, stop and investigate before recalibrating — per `docs/plans/observability_process_isolation.md` §4.1.
