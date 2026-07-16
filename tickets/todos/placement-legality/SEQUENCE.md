# placement-legality — Implementation Sequence

Source: `docs/plans/idea_placement_legality_check.md`, distilled from `experiments/placement_integrity/PROPOSAL.md`. No epic ticket — two tightly-scoped, directly-dependent tickets, assessed as an isolated, not-too-large workload (see idea doc's own reproduced-bug evidence: one deterministic collision, corroborated by both a standalone prototype and real production run data).

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260716-PLACELEGAL-HARDLAW | New `HardLawMonitor` law + `Kernel.__init__` call-site wiring. Must land first — produces the `law_id` (working name `LAW-SPAWN-OCCUPANCY`) the second ticket routes. |
| 2 | TCK-20260716-PLACELEGAL-SIMQ-SIGNAL | Extends `_translate_invariant()` to route ticket 1's new law into a WORLD DYNAMICS frequency signal. Cannot be meaningfully implemented or tested before ticket 1 exists — there is no real `law_id` to dispatch on until then. |

## Dependency Notes
- Hard sequential dependency, not parallelizable: ticket 2's dispatcher branch and scoring test both require ticket 1's law to actually fire on real data (the reproduced seed-42 / entities-6-and-14 collision) to verify against.
- Ticket 1 alone already closes the practically-relevant gap (the bug is detected and persisted to `hard_law_violations.jsonl` at tick 0 instead of discovered 7+ ticks late, or never, in low-observability modes). Ticket 2 adds visibility into SimQ's gradient-scoring view on top of that — valuable but not a correctness fix in itself.
- If ticket 1's final `law_id` naming changes from the working name `LAW-SPAWN-OCCUPANCY` during its own Investigate phase, ticket 2 must be updated to match before its own Investigate phase begins — do not let the two tickets drift on the exact string.
- Explicitly out of scope for both tickets (do not silently fold in): `WorldEntitySpawner`'s separate, more severe shared-`default_position` bug in `src/worldassembly/`; the unrelated `CONSERVATION`-prefixed law gap in `HardLawMonitor`; `docs/guides/observability.md`'s stale event-listener description. All three are real findings from the originating investigation, each already flagged for whoever owns that specific area — see `docs/plans/idea_placement_legality_check.md` for full detail on each.
