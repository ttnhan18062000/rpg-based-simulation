---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES

## Re-confirmed the dead-code finding
Direct re-read of `src/engine/tactical.py`'s current state (lines 391-401, 596-603): `target` and
`is_attack_legal` are both computed at line 400-401, via `LegalityServiceV2.verify_attack_legality`
against the entity's own real, un-biased `combat.range`/`effective_range`. The `AGGRESSIVE`/
`EVASIVE` `attack_range` local-variable computation runs *after* this, at lines 596-603, and
nothing in the function's own remaining ~65 lines (the `SKILL`/`ATTACK` emission branches, the
pursuit `else` branch) ever reads that local variable again. Confirmed dead: not a design
decision, a genuine disconnect between the code's own comments ("Aggressive entities ignore range
buffers", "Evasive skirmishers might choose to reposition") and what it actually does (nothing).

## Real decision: remove (option a), not implement (option b)
The ticket's own Scope named two options. Chose (a) remove, not (b) implement, for a real,
evidence-based reason: implementing this "for real" would require feeding an `ActionStyle`-biased
range into `is_attack_legal`'s own computation — the exact combat-legality decision point this
same session's earlier tickets (`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`,
`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`) spent significant, real, corpus-verified
effort hardening (0% → 28.5%/36.6% real legal rate, confirmed via live probes against real
compiled worlds). Re-touching that same decision point for a speculative, never-requested "range
buffer" game-feel effect (with no real `EVASIVE` reposition logic even existing to pair it with)
risks regressing a freshly-verified, hard-won fix for no confirmed benefit. Removing the dead code
closes the real technical-debt/misleading-comment issue without touching that fragile path at all.

Confirmed via grep: no test anywhere references this specific `AGGRESSIVE`/`EVASIVE` sub-branch's
behavior (`ActionStyle` in `tests/unit/tactical/`, `tests/unit/combat/` only exercises the real,
separate, working consumers — kiting distance, opportunity-attack suppression) — safe to remove.

## Adjacent, disclosed finding: COMB-263's own test citation was already stale
`docs/compliance/checklist.md`'s own COMB-263 entry ("Weapon range affects tactical choice",
checked off, P0-adjacent) cited `tests/unit/movement/test_tactical_movement.py` as proof — but
that file has no test exercising this claim at all (confirmed via direct read: its only
`ActionStyle`-related test, `test_evasive_retreat_skips_oa`, tests the real, separate
opportunity-attack-suppression mechanism in `movement.py`, unrelated to `tactical.py`'s own range
logic). This citation was wrong before this ticket touched anything — the removed dead code was
never what COMB-263 actually needed to cite in the first place. The underlying claim itself
remains real and true (weapon range genuinely gates `is_attack_legal`'s own `OUT_OF_RANGE` check,
and the real kiting-distance logic at `tactical.py:549` also depends on `entity.combat.range`) —
only the specific test citation was wrong. Corrected to
`tests/unit/combat/test_tactical_legality.py::test_tactical_legality_filtering` (a real test that
constructs `attack_range=5` and demonstrates its real effect on target reachability/legality) — a
small, adjacent, in-scope correction, not a full compliance-checklist re-audit.

## Real re-verification: the freshly-hardened legality path is unaffected
Re-ran this session's own `is_attack_legal` live-corpus probe (same methodology used throughout)
against both real worlds already used as this session's own combat-legality baseline:
`dungeon_crawl` 27.7% legal (was 28.5% pre-removal — within real sampling variance, not a
regression), `urban_political` 36.6% legal (unchanged). Confirms removing the dead code did not
disturb the real, working legality computation, as expected given the dead code never influenced
it in the first place.

## Docs Requiring Update
- `docs/compliance/checklist.md`: corrected COMB-263's own stale test citation (found adjacent to
  this ticket's own real scope, disclosed and fixed rather than left silently wrong).
