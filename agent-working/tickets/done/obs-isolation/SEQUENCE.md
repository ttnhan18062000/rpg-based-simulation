# obs-isolation — Implementation Sequence

Epic: `TCK-20260702-OBSISO-EPIC`. Source analysis: `docs/plans/observability_process_isolation.md` (gaps G1–G5, verified 2026-07-02).

| Order | Ticket | Gap | Why this order |
|---|---|---|---|
| 1 | TCK-20260702-OBSISO-TRACE-ASYNC | G4 | Independent of broker work; removes the standing hot-path contract violation and cleans the baseline that ticket 4 will benchmark |
| 2 | TCK-20260702-OBSISO-BROKER-CONFIG | G1+G3 | Makes broker mode functional end-to-end (stream identity + kernel routing); prerequisite for any broker-mode testing |
| 3 | TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX (supersedes TCK-20260702-OBSISO-WORKER-PARITY) | G2 | `build_all_scorers()` factory already existed and needed no broker pipeline to wire in — landed directly as a hotfix; the cross-process grade-parity proof (which does need ticket 2's pipeline) is deferred to ticket 4 |
| 4 | TCK-20260702-OBSISO-ISOLATION-PROOF | G5 | Benchmarks all three modes — requires 1–3 landed so the numbers reflect the fixed system; also now inherits the cross-process grade-parity proof deferred from ticket 3 |

## Dependency Notes
- Ticket 1 can run in parallel with ticket 2 (no shared files except kernel init/shutdown regions — coordinate merge order if concurrent).
- Ticket 3 (WORKER-PARITY-HOTFIX) landed independently of ticket 2 — its scope turned out not to need a connectable broker pipeline. The cross-process grade-parity proof that originally motivated ordering ticket 3 after ticket 2 is deferred to ticket 4, which does need ticket 2's pipeline.
- Ticket 4 sets the numeric overhead bands; until it lands, R1 remains contract-asserted, not measured.
- Grade anchors: tickets 1–3 must not change in-process grades (`make evaluate --dry-run` clean). If any diff appears, stop and investigate before recalibrating — per `docs/plans/observability_process_isolation.md` §4.1.
