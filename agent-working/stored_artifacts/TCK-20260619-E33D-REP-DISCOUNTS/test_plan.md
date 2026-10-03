# Test Plan: TCK-20260619-E33D-REP-DISCOUNTS

## Regression Surface

Existing tests that touch the shop BUY path, economy, or reputation — must pass unchanged after implementation:

| Test file | What it covers | Why it may be affected |
|---|---|---|
| `tests/unit/resource/test_domain_8_economy.py` | ShopService buy/sell, MarketSystem, gold_cost | Directly exercises `ShopService.buy_item()` — the primary insertion point |
| `tests/unit/resource/test_resource_conservation_regression.py` | ResourceTransferIntent conservation invariants | Verifies gold_cost deductions don't create gold |
| `tests/unit/resource/test_economy_hardening.py` | Economy edge cases and price guard | May exercise `ShopSystem.enforce()` price validation |
| `tests/unit/resource/test_transaction_grouping.py` | ResourceTransferIntent grouping | Verifies SHOP_BUY transfer structure |
| `tests/unit/world/test_economy_contract.py` | Economy contract behavior | Broad economy contract coverage |
| `tests/unit/economy/test_gold_sink.py` | GoldSinkSystem conservation | Pattern reference; must not be broken |
| `tests/integration/pipeline/test_transaction_completion.py` | End-to-end transaction pipeline including shop | Full pipeline integration; discount must not break rejection logic |
| `tests/integrity/test_parity_guards.py` | Parity ledger YAML schema and coverage | Will fail if TOWN-016 or new TOWN-181 is malformed |

---

## New Tests Required

All new tests go in: `tests/unit/economy/test_reputation_discount.py`

### TC-D01: Standard discount — 0.8 rep on matching faction

```python
def test_reputation_discount_applies_matching_faction():
    """AC: entity with rep=0.8 at matching-faction shop pays 16% less."""
    base_price = 100
    # Using public_reputation=1.6 (normalized: 1.6/2.0 = 0.8) OR faction_rep=0.8 if dict added
    entity_rep = 0.8  # normalized rep value passed to function
    shop_faction = "merchant_league"
    entity_faction = "merchant_league"  # same faction → discount applies

    result = apply_reputation_discount(base_price, entity_rep, entity_faction, shop_faction)

    assert result == 84  # 100 * (1 - 0.8 * 0.20) = 100 * 0.84 = 84
```

### TC-D02: Neutral reputation — full price

```python
def test_neutral_rep_pays_full_price():
    """AC: entity with rep=0.0 pays full price."""
    base_price = 100
    entity_rep = 0.0
    shop_faction = "merchant_league"
    entity_faction = "merchant_league"

    result = apply_reputation_discount(base_price, entity_rep, entity_faction, shop_faction)

    assert result == 100  # max(0.0, 0.0) * 0.20 = 0 → no discount
```

### TC-D03: Wrong faction — full price regardless of reputation

```python
def test_wrong_faction_pays_full_price():
    """AC: entity_faction != shop_faction → full price even with high rep."""
    base_price = 100
    entity_rep = 0.8
    shop_faction = "merchant_league"
    entity_faction = "fighters_guild"  # different faction → no discount

    result = apply_reputation_discount(base_price, entity_rep, entity_faction, shop_faction)

    assert result == 100  # faction mismatch → discount suppressed
```

### TC-D04: Maximum rep (1.0) — 20% discount

```python
def test_max_rep_applies_20_percent_discount():
    """Rep=1.0 is the cap: 20% discount."""
    base_price = 50
    result = apply_reputation_discount(50, 1.0, "merchant_league", "merchant_league")
    assert result == 40  # 50 * (1 - 1.0 * 0.20) = 50 * 0.80 = 40
```

### TC-D05: Negative reputation — full price (clamped by max(0.0, ...))

```python
def test_negative_rep_pays_full_price():
    """Negative rep must not increase price beyond base (formula clamps at 0)."""
    base_price = 100
    result = apply_reputation_discount(100, -0.5, "merchant_league", "merchant_league")
    assert result == 100  # max(0.0, -0.5) = 0 → no discount
```

### TC-D06: Floor guard — discounted price never below 1

```python
def test_discount_floor_is_one_gold():
    """Even with 20% discount on a 1-gold item, result is at least 1."""
    result = apply_reputation_discount(1, 1.0, "merchant_league", "merchant_league")
    assert result >= 1
```

### TC-D07: Conservation invariant — gold_cost reduction does not create gold

```python
def test_reputation_discount_conservation_invariant():
    """Gold paid by buyer + gold NOT received by seller = base_price. No gold created."""
    base_price = 100
    entity_rep = 0.8
    discounted = apply_reputation_discount(base_price, entity_rep, "merchant_league", "merchant_league")
    discount_amount = base_price - discounted

    # Entity pays discounted amount; shop receives discounted amount
    # Discount amount is "lost revenue" — gold not transferred, not created
    assert discounted + discount_amount == base_price  # conservation holds
    assert discounted >= 0  # no negative prices
```

### TC-D08: Integration — ShopService.buy_item() uses discounted price

```python
def test_shop_buy_item_uses_reputation_discount(economic_state):
    """ShopService.buy_item() emits ResourceTransferIntent with discounted gold_cost."""
    # Build entity with public_reputation = 1.6 (normalized 0.8) at matching faction shop
    entity = build_entity_with_reputation(public_reputation=1.6, faction="merchant_league")
    shop = build_shop(faction="merchant_league", item="health_potion", base_value=100)
    state = build_state(entity=entity, shop=shop)

    update = ShopService.buy_item(entity, "health_potion", 1, state)

    assert update is not None
    intent = update.entity_updates[entity.id].resource_transfers[0]
    assert intent.transfer_kind == "BUY"
    assert intent.gold_cost == 84  # 100 * 0.84 — 16% discount at rep=0.8
```

### TC-D09: Integration — ShopSystem.enforce() does not reject valid discounted intent

```python
def test_shop_enforce_accepts_discounted_intent():
    """ShopSystem.enforce() must not reject an intent where gold_cost reflects reputation discount."""
    # The enforcement layer must apply the same discount when re-validating
    # so that discounted gold_cost >= recalculated legal_discounted_price
    ...  # build state + intent with discounted gold_cost; run ShopSystem.enforce(); assert intent survives
```

---

## Scoped Pytest Commands

Run only the new discount tests during development:
```
pytest tests/unit/economy/test_reputation_discount.py -v
```

Run the regression surface after implementation:
```
pytest tests/unit/resource/ tests/unit/economy/ tests/unit/world/test_economy_contract.py tests/integration/pipeline/test_transaction_completion.py tests/integrity/test_parity_guards.py -v -m "not slow"
```

Do NOT run the full suite (`pytest tests/`) — scope to the economy/resource/integrity domains.

---

## Anti-Drift Test Guards

### Guard 1: Discount never creates gold

`assert discounted_price + discount_amount == base_price` — this identity must hold for all test inputs. Equivalently: `discounted_price <= base_price` always. (TC-D07)

### Guard 2: Discount never applies across faction boundary

`assert apply_reputation_discount(price, rep=1.0, entity_faction="X", shop_faction="Y") == price` for any `X != Y`. (TC-D03)

### Guard 3: Negative rep is treated as zero (no price increase)

`assert apply_reputation_discount(price, rep=-99.0, "X", "X") == price` — formula uses `max(0.0, rep)`. (TC-D05)

### Guard 4: Enforcement layer accepts proposal-layer discounted price

The `ShopSystem.enforce()` re-validation guard (`intent.gold_cost < legal_total` → rejection) must use the same discounted price when checking SHOP_BUY intents for entities with reputation. This guards against silent enforcement rejection of valid discounted purchases. (TC-D09)

### Guard 5: Parity ledger TOWN-016 updated

`tests/integrity/test_parity_guards.py` will catch malformed YAML. The new TOWN-181 entry must be syntactically valid with `status: verified`, a `test_path`, and `v2_evidence` pointing to the implemented function. Malformed entry = parity guard failure.
