# Investigation — TCK-20260607-COMBAT-REWARD-SERVICE

## EntityRole definition

`src/core/enums.py` line 6:
```python
class EntityRole(IntEnum):
    HERO = 0
    SHOPKEEPER = 1
    MONSTER = 2
    CITIZEN = 3
    WORKER = 4
    GUARD = 5
```
`EntityRole` is already an `IntEnum`. Import path: `from src.core.enums import EntityRole`.

---

## All EntityRole checks in combat.py (with reward context)

| Line | Method | Role check | Purpose |
|------|--------|-----------|---------|
| 136 | `resolve_attack` | `defender.identity.role != EntityRole.HERO` | Lethality gate — HERO forced to DEFEAT/REBIRTH not KILL. **Not a reward check — out of scope.** |
| 175–180 | `resolve_attack` | `== MONSTER` / `elif == HERO` | XP and gold formula selection + rebirth/permadeath branch. **In scope.** |
| 277 | `resolve_skill_usage` | `== MONSTER` | XP and gold formula selection (MONSTER only, HERO not checked). **In scope.** |
| 383–388 | `resolve_multi_attack` | `== MONSTER` / `elif == HERO` | XP and gold formula selection. **In scope.** |
| 480–492 | `resolve_aoe_attack` (primary) | None — hardcoded `evolution_level * 10` / `* 5`. Monster-only formula, no role check. **Partial scope — AoE uses raw formula without role dispatch.** |
| 542–554 | `resolve_aoe_attack` (splash) | None — hardcoded `evolution_level * 10` / `* 5`. Same issue. |
| 585 | `_get_wound_infliction` | `attacker.identity.role == EntityRole.HERO` | Wound kind (SLASH vs CRUSH). **Not a reward check — out of scope.** |

### Summary of in-scope checks

Four explicit EntityRole reward checks (ticket lines 175-178, 277, 383, 386 confirmed), plus two implicit reward sites in `resolve_aoe_attack` that use hardcoded MONSTER-equivalent formulas without role dispatch.

The ticket scopes to the four named checks. The AoE hardcoding is a separate architectural gap — it is noted here but will NOT be addressed in this ticket (per "Out of Scope" — this ticket is about where checks live, not formula changes).

---

## EntityRole reward checks outside combat.py

Grepped `src/` for `EntityRole.MONSTER|EntityRole.HERO` with reward-adjacent terms (xp, gold, reward, evo, grant). **No reward-gating checks found outside `combat.py`.** The `evolution.py:115` hit is for a lifecycle event (not reward gating). Generator usages are entity construction, not reward logic.

---

## Where CombatRewardClassificationService should live

- `src/engine/` is the correct layer — it owns `CombatResolutionSystem`, legality, tactical, and all combat-adjacent logic.
- No systems registry is used for combat logic; services are instantiated or called statically.
- File: `src/engine/combat_rewards.py` (as specified in ticket).
- The service should use `@staticmethod` or `classmethod` for `classify()`, matching the pattern of `CombatResolutionSystem` (all static methods). No instance state required.

---

## Existing reward tests

`tests/unit/combat/test_combat_reward_hardening.py` covers:
- `test_combat_reward_consolidation_xp_gold` — verifies MONSTER at `evolution_level=5` produces XP=50, gold=25 through the full pipeline (matches formula `LVL*10`, `LVL*5`).
- `test_skill_reward_consolidation` — verifies MONSTER at `evolution_level=2` produces XP=20.

These are integration-level tests that will continue to pass unchanged after refactor (service produces same numeric outputs).

---

## Mechanics Bible — Chapter 02 reward table

`docs/mechanics/02_combat_laws.md` lines 47–52:

| Target Role | XP Reward | Gold Reward |
|---|---|---|
| Monster | `LVL * 10` | `LVL * 5` |
| Hero | `LVL * 20` | `LVL * 50` |

Hero rebirth: generation 1-3 → rebirth (gen increment). Generation 4 → permadeath.

This exactly matches the code in `resolve_attack` lines 175-187. The service must preserve these exact multipliers.

---

## Parity ledger — reward-relevant P0 entries

From `docs/parity_ledger/combat_movement.yaml`:
- **COMB-279** (P0): "Combat result emits kill/death consequence when applicable." Status: verified. test_path: null.
- **COMB-280** (P0): "Combat result emits reward/progression consequence when applicable." Status: verified. test_path: null.

From `docs/parity_ledger/progression.yaml`:
- **PROG-004** (P0): "Combat and progression rewards update gold, XP, veterancy, effects, and consequences through authoritative updates." Status: legacy_verified. test_path: null.
- **PROG-064** (P0): "XP/reward grant is authoritative and traceable to event." Status: verified. test_path: null.

**None of these P0 entries have a `test_path` set**, so there is no concrete test file reference to update. However PROG-064 directly mandates the `source` tracing that this ticket implements — adding `classification.source` strengthens PROG-064 compliance.

---

## Open questions resolved

1. Are there reward checks outside `combat.py`? **No.**
2. Is `EntityRole` already an enum? **Yes — `IntEnum` at `src/core/enums.py:6`.**
3. Does `resolve_skill_usage` check HERO for rewards? **No — only MONSTER.** The service must handle this cleanly (HERO classify returns XP+gold too per Ch02, but `resolve_skill_usage` only rewards MONSTER kills; the service must not force HERO reward onto skill path unless that was intended).
4. Does `resolve_aoe_attack` use role checks? **No — hardcoded MONSTER formula.** Noted but excluded from this ticket's scope.
