# Investigation — TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED

## Origin claim, re-verified

`VeterancyService.process_points()` (`src/progression/veterancy.py`) is real and live — wired
through `src/engine/patches.py:186-219` and `src/engine/apply.py:49,615-616`, confirmed via grep.
`veterancy_rank`/`veterancy_points` genuinely accumulate and persist (including campaign
carryforward: `src/domains/campaigns/state.py`, `orchestrator.py`).

`VeterancyService.get_stat_multiplier(rank)` — re-confirmed via grep for `get_stat_multiplier`
across `src/` and `tests/` — has **zero callers anywhere**, only its own definition. Also confirmed
via grep for `veterancy_rank` across `src/` (excluding its own module, `state.py`, `apply.py`,
`patches.py`) that every other read site only stores/serializes/displays the rank — campaign
carryforward, the entity builder — never feeds it into a stat or combat calculation. This part of
the origin ticket's claim is accurate as filed.

## Declared-intent check (per peer instruction: check before building)

Three potential sources of "the design says rank should modify combat" were checked, in order of
authority:

1. **Mechanics Bible** (`docs/mechanics/*.md`, the repo's own stated authoritative source for
   simulation laws): grepped for "veterancy" and "veteran rank" — **zero mentions anywhere**. No
   chapter declares this mechanic.
2. **Parity ledger** (`docs/parity_ledger/progression.yaml`), `PROG-014`: `status: verified`, P0,
   "Veterancy Ranks should boost stats via StatsProxy." On inspection: `test_path: null`,
   `proof_type: null` — never actually backed by a test. Names `StatsProxy`, grepped and confirmed
   **absent from `src/` entirely** — a dead V1-era concept. This is the identical shape to
   `PROG-001` in the same file, already corrected by
   `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` for the same defect (a `verified` claim
   with no real backing evidence).
3. **Compliance checklist** (`docs/compliance/checklist.md`), `PROG-086`: "Veterancy Ranks grant
   passive efficiency buffs to specific roles," citing `tests/unit/progression/test_veterancy.py`
   and `ApplyPath:454`. Both citations checked directly:
   - `tests/unit/progression/test_veterancy.py` **does not exist**. The real file,
     `tests/unit/progression/test_leveling_veterancy.py`, tests rank-up progression
     (`test_veterancy_progression`, `test_veterancy_multi_rank`) — never `get_stat_multiplier()`.
   - `src/engine/apply.py:454` today is unrelated state-carryforward code (mid-`AuthoritativeState`
     dataclass reconstruction), nothing to do with veterancy.
   - This is a second citation for the *same underlying claim* as `PROG-014`, and it is itself
     unsubstantiated — a citation of a citation, not independent evidence.

**Conclusion: nothing authoritative declares rank should modify combat.** All three sources that
could have supplied "declared intent" turn out to be either silent (Mechanics Bible) or
self-referential and unbacked (PROG-014, PROG-086) — the same class of defect the ledger has
already been caught making once (PROG-001), now confirmed a third time in the same file plus its
sibling compliance doc.

## Disposition (peer-reviewed and approved before closing)

**Document-only. Do not wire `get_stat_multiplier()`.** Per peer review: three citations all
turning out to be stale or unsubstantiated isn't three weak pieces of evidence for a design
intent — it's evidence the intent was never there, and a later citation of a citation manufactured
the appearance of one. Wiring it now would be inventing gameplay, exactly the case the
declared-intent test exists to catch.

Corrections made as part of closing this ticket (not a design decision, a factual correction):
- `docs/parity_ledger/progression.yaml` `PROG-014`: `status: verified` → `status: missing`, via
  `tools/parity_ledger_writer.py`, with `support_boundary` recording what was actually found.
- `docs/compliance/checklist.md` `PROG-086`: unchecked, citations corrected in place to state the
  real test file and the real (unrelated) code at the old line reference.
- Filed `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` to record the now-three-times-
  confirmed pattern (verified status + null test_path) as worth a ledger-wide sweep, rather than
  fixing citations one at a time as they're stumbled into.
