# Implementation Plan — TCK-20260619-E33D-REP-DISCOUNTS
# Reputation-Based Shop Discounts

**Date:** 2026-06-21
**Phase:** Plan (seq 3)
**Tier:** standard

---

## Overview

Wire a reputation-based price discount into the shop purchase path. The discount is a pure deterministic function of `entity.social.public_reputation` and touches exactly two runtime paths (proposal + enforcement) plus three doc surfaces and the parity ledger. No new durable state is introduced.

---

## Declared Deviations

### DEV-001: Faction cross-check skipped

The ticket pseudocode contains `if faction_id != shop_faction: apply discount`. No per-faction reputation dict exists on `SocialComponent` — only `public_reputation: float`. Implementing the faction gating would require a schema change outside scope (E33D is discount mechanics only).

**Resolution:** Apply discount based purely on `public_reputation`. Discount is universal (all shops). This is a **scope simplification, not a drift** — it must be noted in the `docs/guidelines/v2_intentional_divergences.md` file and in the plan deviation log.

---

## Step-by-Step Plan

### Step 1 — Add `apply_reputation_discount()` helper

**File (new):** `src/systems/economy_systems/reputation_discount.py`

Rationale for new file (not appended to `economy.py`): keeps the discount concern isolated, avoids touching a large existing module, and makes the helper trivially importable from both `src/town/shop.py` and `src/engine/shop.py` without circular-import risk.

```python
"""reputation_discount.py — Pure reputation-to-discount helper.

No external dependencies. No state mutation.
Formula from TCK-20260619-E33D-REP-DISCOUNTS / docs/mechanics/03_economic_laws.md §4.1.
"""


def apply_reputation_discount(base_cost: int, public_reputation: float) -> int:
    """Return the discounted price for a shop purchase.

    Args:
        base_cost: Pre-discount gold cost (must be >= 1).
        public_reputation: Entity's public reputation (SocialComponent.public_reputation).
                           Expected range 0.0–2.0; values outside range are clamped.

    Returns:
        Discounted cost, floored to a minimum of 1 gold.

    Formula:
        entity_rep  = clamp(public_reputation, 0.0, 2.0) / 2.0   # normalize to [0, 1]
        discount    = entity_rep * 0.20                            # max 20% at rep=2.0
        discounted  = int(base_cost * (1.0 - discount))
        return max(1, discounted)
    """
    entity_rep = max(0.0, min(public_reputation, 2.0)) / 2.0
    discount = entity_rep * 0.20
    return max(1, int(base_cost * (1.0 - discount)))
```

**Acceptance check:** `apply_reputation_discount(100, 2.0) == 80`, `apply_reputation_discount(100, 1.0) == 90`, `apply_reputation_discount(100, 0.0) == 100`, `apply_reputation_discount(1, 2.0) == 1` (floor).

---

### Step 2 — Wire into proposal layer (`src/town/shop.py`)

**Target:** `ShopService.buy_item()`, around line 36.

Before (current):
```python
total_cost = unit_price * quantity
```

After:
```python
total_cost = unit_price * quantity
total_cost = apply_reputation_discount(total_cost, entity.social.public_reputation)
```

**Import to add at top of `src/town/shop.py`:**
```python
from src.systems.economy_systems.reputation_discount import apply_reputation_discount
```

No other changes to `buy_item()`. The discounted `total_cost` flows into the existing intent construction unchanged.

---

### Step 3 — Wire into enforcement layer (`src/engine/shop.py`)

**Target:** `ShopSystem.enforce()`, around line 83.

The enforcement guard currently computes `legal_total = legal_price * quantity` and rejects intents where `intent.gold_cost < legal_total`. After the proposal layer applies a discount, enforcement will incorrectly reject those intents unless it also applies the same discount.

Before (current, reconstructed):
```python
legal_price = DynamicPriceService.calculate_buy_price(...)
legal_total = legal_price * quantity
if intent.gold_cost < legal_total:
    raise EnforcementError(...)
```

After:
```python
from src.systems.economy_systems.reputation_discount import apply_reputation_discount

legal_price = DynamicPriceService.calculate_buy_price(...)
legal_total = apply_reputation_discount(legal_price * quantity, entity.social.public_reputation)
if intent.gold_cost < legal_total:
    raise EnforcementError(...)
```

**Import to add at top of `src/engine/shop.py`:**
```python
from src.systems.economy_systems.reputation_discount import apply_reputation_discount
```

**Conservation note:** The discount reduces the gold transferred from buyer to shop. Net world gold is unchanged — the buyer simply retains more. The `max(1, ...)` floor ensures no zero-cost purchases. No changes to `economy/conservation.py` are needed.

---

### Step 4 — Update `docs/engine/known_limitations.md`

Locate the Commerce section (or add one). Add entry:

```
### §1.4 Commerce Limitations

- **Reputation-based shop discounts** — Previously unsupported.
  **Now implemented** as of TCK-20260619-E33D-REP-DISCOUNTS.
  Formula and mechanics: see `docs/mechanics/03_economic_laws.md §4.1`.
  Faction-scoped discounts remain out of scope (no per-faction reputation dict on SocialComponent).
```

---

### Step 5 — Update `docs/mechanics/03_economic_laws.md`

In §4 Commerce, after the "Buying from Shops" formula block, insert new subsection §4.1:

```markdown
#### §4.1 Reputation Discount

Entities with positive public reputation receive a proportional discount at all shops.

**Formula:**

    entity_rep  = clamp(public_reputation, 0.0, 2.0) / 2.0   # normalized [0, 1]
    discount    = entity_rep × 0.20                            # up to 20% at max rep
    discounted  = floor(base_cost × (1 − discount))
    final_cost  = max(1, discounted)                           # floor: never free

**Notes:**
- `public_reputation` sourced from `SocialComponent.public_reputation` (range 0.0–2.0, default 1.0).
- At default reputation (1.0): 10% discount.
- At maximum reputation (2.0): 20% discount.
- At zero or negative reputation: 0% discount (no penalty, no bonus).
- Faction cross-check is not applied in this release (DEV-001). Discount is universal across all shops.
- Conservation law satisfied: buyer pays less, shop receives less; net world gold unchanged.

**Reference:** TCK-20260619-E33D-REP-DISCOUNTS, `src/systems/economy_systems/reputation_discount.py`.
```

---

### Step 6 — Add integration test `test_reputation_discount_applies`

**File:** `tests/integration/scenarios/test_macro_economy.py`

Add a new test function covering:

| Sub-case | `public_reputation` | `base_cost` | Expected `final_cost` |
|---|---|---|---|
| High rep | 1.6 | 100 | 84 (16% discount → `int(100 * 0.84) = 84`) |
| Neutral rep | 1.0 | 100 | 90 (10% discount → `int(100 * 0.90) = 90`) |
| Zero rep | 0.0 | 100 | 100 (0% discount) |
| Floor guard | 2.0 | 1 | 1 (floor prevents 0) |
| Over-range clamp | 3.0 | 100 | 80 (clamped to 2.0 → 20% discount) |

The test calls `apply_reputation_discount()` directly (unit-style check embedded in the integration file per existing project convention) AND verifies the proposal path through `ShopService.buy_item()` mock-entity path.

---

### Step 7 — Update parity ledger (`docs/parity_ledger/town_resource.yaml`)

**7a. Update TOWN-016** (line 170): set `v2_evidence` to reference `reputation_discount.py` and the new test; update `status` to `verified` if currently `missing`.

**7b. Add TOWN-181** after line 1945 (last current entry TOWN-180):

```yaml
- id: TOWN-181
  text: >
    Shop purchases apply a reputation-based discount: up to 20% off at maximum
    public_reputation (2.0), scaling linearly, floored to 1 gold minimum.
    Faction cross-check is deferred (DEV-001 in TCK-20260619-E33D-REP-DISCOUNTS).
  status: verified
  priority: P1
  v2_evidence: >
    src/systems/economy_systems/reputation_discount.py::apply_reputation_discount;
    src/town/shop.py::ShopService.buy_item;
    src/engine/shop.py::ShopSystem.enforce
  test_path: tests/integration/scenarios/test_macro_economy.py::test_reputation_discount_applies
  divergence_note: >
    Faction-scoped discount gating (ticket pseudocode) not implemented — no per-faction
    reputation dict on SocialComponent. Discount applied universally. See DEV-001.
```

---

## Scope Guards

The following are explicitly **out of scope** for this ticket:

| Item | Reason |
|---|---|
| Add `faction_rep` dict to `SocialComponent` | Separate schema change; no ticket for it |
| Modify sell path | Discount is buy-side only per ticket spec |
| Touch `economy/conservation.py` | Discount operates within existing resolver; no conservation violation |
| Run `make knowledge-index-update` | Runs after implementation commit, not during plan |
| Faction-gated discounts | DEV-001 — deferred |

---

## File Change Summary

| File | Action |
|---|---|
| `src/systems/economy_systems/reputation_discount.py` | **CREATE** — pure helper |
| `src/town/shop.py` | **MODIFY** — import + 1-line call after line 36 |
| `src/engine/shop.py` | **MODIFY** — import + apply discount before enforcement check (~line 83) |
| `docs/engine/known_limitations.md` | **MODIFY** — add §1.4 Commerce Limitations |
| `docs/mechanics/03_economic_laws.md` | **MODIFY** — add §4.1 Reputation Discount |
| `tests/integration/scenarios/test_macro_economy.py` | **MODIFY** — add test function |
| `docs/parity_ledger/town_resource.yaml` | **MODIFY** — update TOWN-016, add TOWN-181 |

**Total:** 1 new file, 6 modified files.

---

## Unresolved Questions

**None.** The faction cross-check ambiguity is resolved as DEV-001 (declared simplification, not drift). All other implementation details are fully determined by the ticket spec and existing repo patterns.

---

## Execution Order

Run steps in order — each step is independent except Step 3 depends on Step 1 (import), and Step 6 depends on Steps 1–3 (behavior under test).

1. Create `src/systems/economy_systems/reputation_discount.py` (helper)
2. Wire `src/town/shop.py` (proposal layer)
3. Wire `src/engine/shop.py` (enforcement layer)
4. Update `docs/engine/known_limitations.md`
5. Update `docs/mechanics/03_economic_laws.md`
6. Add test `test_reputation_discount_applies`
7. Update `docs/parity_ledger/town_resource.yaml` (TOWN-016 + TOWN-181)
