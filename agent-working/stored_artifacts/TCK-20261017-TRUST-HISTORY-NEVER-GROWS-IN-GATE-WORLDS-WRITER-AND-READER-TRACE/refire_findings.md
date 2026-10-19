# Follow-up: does one abandonment apply more than once? (read-only, rpg-next f1973e446, seed 42 x 5000t)

Probe `refire_probe.py` (outside src) wraps `CooperationLearningService.learn`, `PartyCohesionService.evaluate`, `process_update` (trust values logged per tick; every `trust_history.get` that reads a present value <= -0.5 is logged with its caller file:line). Raw: `results/refire_*.json`.

## Verdict: YES, hard-bug candidate. One abandonment re-fires every tick.
`CooperationPhase` (src/domains/cooperation/phase.py:210-252) re-evaluates every live group each tick, and on MEMBER_ABANDONING / LEADER_LOST calls `learn("abandoned")` for every non-leader member. `PartyCohesionService.evaluate` (services.py:408) reports a member as abandoning when `trust_history[leader] < 0.2`, so once the first penalty lands (`process_update` adds the delta to a missing key as 0.0, relationships.py:40, giving -0.25 < 0.2; the first trigger itself may be the HP rule at services.py:401, which the probe did not log) the member abandons on every later evaluation, and each one applies -0.25 trust and +0.3 grudge again. Nothing in the phase dissolves the group; the hits stop only when the group is dissolved elsewhere or a body dies.

## (a) Hits per (member, leader) pair
| world | pairs hit | hits per pair | gap between hits |
|---|---|---|---|
| urban_political | 2 | 4, 52 | max 1 tick (52-pair: ticks 440-491) |
| crowded_frontier | 6 | 3, 4, 5, 5, 29, 30 | max 1 tick |
| frontier_living_world | 3 | 10, 38, 56 | max 1-3 ticks (56-pair: ticks 451-506) |
Per abandonment episode (consecutive abandoning evaluations of one group): most episodes are a single hit (urban 4 of 5, crowded 5 of 10, frontier 10 of 12), but the remaining ones are 3 to 56 consecutive hits for one pair. Exactly one member is hit per evaluation in these groups (learn calls == abandoning evaluations: 56 / 76 / 104).

## (b) Trust over time
The first hit lands -0.25; the holder reaches -1.0 after 4 hits (2-9 ticks after the first hit; urban 4 and 9, crowded 4,4,4,7,7, frontier 2,4,7). From then the clamp absorbs every later hit: 52 hits is 48 no-op trust writes. Final values: -1.0 for 2 / 5 / 3 pairs, -0.62 or -0.75 for pairs whose group ended early. Grudge gets +0.3 per hit (computed from the code, not probed): a 52-hit pair would reach the 5.0 grudge clamp after 17 hits.

## (c) Which readers of those holders' trust are live
Reads of a present trust value <= -0.5 (count of reads in 5000 ticks: urban / crowded / frontier):
| reader | file:line | reads | what it does with it |
|---|---|---|---|
| partner shortlist (near candidates) | providers.py:77 | 1006 / 38 / 190 | keeps the candidate (distance rule), carries trust -1.0 into `PartnerCandidate.trust_score`; a far candidate needs trust > 0.7 so it is dropped, as it is at the 0.5 default |
| partner shortlist (far fallback) | providers.py:69 | 28 / 56 / 16 | `trust <= 0.7 -> continue`: -1.0 decides the same as the 0.5 default, no new effect |
| partner fit | evaluators.py:140 | 0 / 29 / 103 | `trust_score = max(trust, bond.sentiment)` then minus grudge, floored at 0: with -1.0 the fit falls to the bond sentiment (or 0) instead of 0.5, so the pair is rated worse; grudge also subtracts. LIVE, changes the decision |
| group objective propagation (no-bond fallback) | groups.py:242 | 21 / 55 / 0 | raw trust used on the 0..1 scale: -1.0 < 0.3, the member does not receive GROUP_OBJECTIVE (default 0.5 would). LIVE, changes the decision |
| party cohesion | services.py:408 | 31 / 1 / 18 | trust < 0.2 -> abandoning: this is the loop that sustains the re-fire |
| grief trigger | grief_triggers.py:34 | 4 / 2 / 2 | reads it, threshold 0.30 not met, no trigger |
| party.py:60, tactical.py:388, appraisal.py:53/526, social_contract_scorer.py:110, party_composition.py:126 | | 0 / 0 / 0 | never saw a negative: bond exists for the pair, so the bond branch is taken (or the pair never meets that rule) |
Scale note: the no-bond fallbacks (groups.py:242, tactical, party, appraisal, scorer) read `trust_history` as if it were the 0..1 trust but it is stored on -1..1; only the bond branch maps `(sentiment+1)/2`. So -1.0 reads as "far below 0", not as "0.0".
Caveat: bond sentiment for the trust pairs is mostly positive (urban 2/2 pos; crowded 6 pos / 5 neg; frontier 2 pos / 4 neg), which is why most readers never use the trust value.
