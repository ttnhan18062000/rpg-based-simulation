# Investigation: TCK-20260619-E33D-REP-DISCOUNTS

## Current Behavior

### Shop BUY path — file:line references

The BUY transaction flows through two layers:

**Worker/proposal layer** (`src/town/shop.py`):
- `ShopService.buy_item()` — the public decision-layer entry point.
- Line 35: `unit_price = DynamicPriceService.calculate_buy_price(item_def.value, state)` — sole price computation call.
- Line 36: `total_cost = unit_price * quantity` — **this is where gold_cost is set before being committed to the intent.**
- Line 52–59: emits `ResourceTransferIntent(source_kind="SHOP_BUY", gold_cost=total_cost, ...)`.
- No reputation check exists anywhere in this path.

**Authoritative enforcement layer** (`src/engine/shop.py`):
- `ShopSystem.enforce()` re-validates every `SHOP_BUY` intent at line 79–90.
- Line 79: re-computes `legal_price = DynamicPriceService.calculate_buy_price(item_def.value, state)`.
- Line 83: rejects intent if `intent.gold_cost < legal_total` (price too low guard).
- **This guard will reject any discount applied only at the proposal layer** unless the enforcement layer also applies the discount. The discount function must be called in both places, or only in the enforcement layer.

**Price computation** (`src/systems/economy_systems/economy.py`):
- `DynamicPriceService.calculate_buy_price(base_value, state)` — reads `state.pressure_signals["global_salience"]`, applies multiplier, caps at 3.0×, returns `max(1, int(base_value * multiplier))`.
- Signature accepts only `(base_value, state, governor_mode)` — no entity or faction parameters. Must be extended or a new `apply_reputation_discount()` helper added.

**Conservation resolver** (`src/core/conservation.py`):
- Lines 138, 151, 173, 181, 187: `SHOP_BUY` intents deduct `gold_cost` from entity and credit shop. The resolver does not inspect reputation.

### Reputation model — entity field

`entity.social.public_reputation: float` (range 0.0–2.0, default 1.0) in `src/core/models/social.py:42`.

**Critical mismatch with ticket AC**: The ticket's acceptance criteria reference `entity.faction_rep["merchant_league"] = 0.8`. No such field exists on `EntityState` or any sub-component. The entity has:
- `entity.social.public_reputation` — a single unified float, not a per-faction dict.
- `entity.identity.faction: int` (hero's own faction, default 0).
- `BuildingState.faction: str` (shop's faction affiliation, default `"hostile"`).

There is no `faction_rep: Dict[str, float]` anywhere in the codebase. Implementation must resolve this: either (a) treat `entity.social.public_reputation` as the reputation input (normalized from 0–2 to 0–1 range), or (b) the ticket's formula implicitly assumes `public_reputation` is the discount input and the "merchant_league" / faction_id comparison is the cross-faction guard. See Risks section.

### Shop faction field

`BuildingState.faction: str` at `src/core/state.py:961` (default `"hostile"`). This is the `shop_faction` parameter referenced in the ticket. The entity's "faction" in this context is `entity.identity.faction: int` (an integer, not a string). The cross-faction guard `faction_id != shop_faction` therefore requires a type-consistent comparison strategy.

---

## Mechanics/Engine Constraints

### Chapter 03 §4 Commerce (docs/mechanics/03_economic_laws.md)

Current buy law: `Price = Item_Base_Value * Market_Multiplier`. No mention of reputation discounts. The discount slot belongs **after** the market multiplier is applied and **before** the gold transfer is committed:

```
Price = Item_Base_Value * Market_Multiplier
Discounted_Price = apply_reputation_discount(Price, entity_rep, entity_faction, shop_faction)
gold_cost = Discounted_Price * quantity
```

**Conservation constraint**: The discount reduces `gold_cost` (buyer pays less). The seller (shop) receives less gold. Gold is not created — total world gold does not increase. This satisfies Atomic Conservation Law §1 because both sides of the transfer are adjusted consistently: buyer loses less gold, shop gains less gold, net delta = 0 on world gold total.

### Engine authoritative mutation pipeline

Any price modification must be applied at both layers:
1. Proposal layer (`src/town/shop.py`) — sets the initial `gold_cost`.
2. Enforcement layer (`src/engine/shop.py`) — re-validates and rejects if `gold_cost < legal_price`. If the discount is applied in the proposal layer but NOT the enforcement layer, the intent will be rejected as an underpriced exploit.

**Required approach**: `apply_reputation_discount()` must be called in both `ShopService.buy_item()` and `ShopSystem.enforce()`, using identical logic, so the discounted price passes enforcement validation.

---

## Parity Ledger Overlap

Relevant entries in `docs/parity_ledger/town_resource.yaml`:

| Entry ID | Text summary | Status | Relevance |
|---|---|---|---|
| **TOWN-016** | Shop visits resolve bounded buy/sell behavior using inventory/gold truth. | verified | Primary entry for shop BUY. Must be updated with discount behavior or a new child entry added. |
| TOWN-002 | Every gameplay side effect is a typed update bucket. | verified | Governs that discount must produce typed intent, not raw mutation. |
| TOWN-004 | World mutation happens after proposal, not inside worker code. | verified | Enforces that `apply_reputation_discount` is read-only; result flows through intent. |
| TOWN-179 | GoldSinkSystem conservation. | verified | Precedent pattern: gold_cost reduction = acceptable; gold creation = forbidden. |
| TOWN-180 | Gold sink conservation invariant. | verified | Anti-drift guard model for the new discount invariant test. |

**New entry required**: TOWN-181 — reputation-based shop discount behavior and conservation invariant. No existing entry covers this feature.

**TOWN-016** `v2_evidence` must be updated to reference the discount path once implemented.

---

## Prior Work

### E33A (TCK-20260619-E33A-HEALTH-MONITOR)
Economy health monitoring infrastructure. Established `EconomyHealthMonitor`, `metric_windows.jsonl`, and `pressure_signals` read pattern. Not directly related to shop discounts.

### E33B (TCK-20260619-E33B-ALERTS-REST)
Alert dispatch infrastructure (`InflationSpiralEvent`, `GoldHoardingEvent`). Not directly related.

### E33C (TCK-20260619-E33C-GOLD-SINK)
Most relevant prior work. Key patterns applicable to E33D:
- Confirmed `ResourceTransferIntent` is the correct vector for all gold modifications (no direct state mutation).
- Established that `gold_cost` reduction is conservation-safe when matched by reduced shop credit.
- Confirmed `src/core/conservation.py` SHOP_BUY resolver path (lines 138–187) handles gold_cost deduction atomically.
- Pattern: new helper is read-only on state; writes only via typed intent; tested with conservation invariant test.

The E33C investigation also confirmed `BuildingState.faction: str` exists (the `shop_faction` comparand in the ticket formula).

---

## Risks and Open Questions

### Risk 1 (HIGH): faction_rep field does not exist

The ticket AC says `entity.faction_rep["merchant_league"] = 0.8 → 16% discount`. No `faction_rep` dict exists on `EntityState`. The actual field is `entity.social.public_reputation: float` (0.0–2.0).

**Resolution options:**
- Option A (recommended): Treat `entity.social.public_reputation` as the reputation input. Normalize: `entity_rep = entity.social.public_reputation / 2.0` → range [0.0, 1.0]. Then `discount = max(0.0, entity_rep) * 0.20`. An entity with `public_reputation = 1.6` (equivalent to the spirit of 0.8 on a 0–1 scale) would get `1.6/2.0 * 0.20 = 16%` off. The ticket may have used `faction_rep["merchant_league"]` as illustrative pseudocode.
- Option B: Add a new `faction_rep: Dict[str, float]` field to `SocialComponent` or a new sub-model. This is a larger schema change and requires a separate parity entry.

**This risk must be resolved before implementation begins.** The investigation flags it as an open question requiring implementer decision.

### Risk 2 (MEDIUM): faction_id vs shop_faction type mismatch

`entity.identity.faction` is `int`; `BuildingState.faction` is `str`. The cross-faction guard `faction_id != shop_faction` requires a normalization step. Likely: cast entity faction int to str, or define a canonical faction name registry. Existing code never compares these two fields directly.

### Risk 3 (MEDIUM): Two-layer enforcement gap

`ShopService.buy_item()` (proposal) and `ShopSystem.enforce()` (authoritative) both compute price. The discount must be applied at both, identically, or the enforcement layer will reject the discounted intent. The `apply_reputation_discount()` function must be pure and deterministic so both calls produce the same result.

### Risk 4 (LOW): known_limitations.md does not currently mention reputation discounts

The ticket says "close gap in docs/engine/known_limitations.md: reputation-based shop discounts unsupported." However, the current `known_limitations.md` (read in full) contains no such entry — the gap description itself is missing. Implementation must first ADD the limitation entry (§1.4 Commerce Limitations), then mark it resolved by implementation, or add it and remove it in the same commit. The natural approach: add a new §1.4 noting the prior absence of reputation discounts and document that it is now implemented.

---

## Anti-Drift Hazards

### Conservation law: discount must not create gold

The discount reduces `gold_cost` (what the buyer pays). In the `SHOP_BUY` conservation path (`src/core/conservation.py` lines 138–187), the resolver credits the shop with `gold_cost` and debits the entity with `gold_cost`. Reducing `gold_cost` means:
- Entity gold decreases by less (buyer benefit).
- Shop gold increases by less (seller revenue reduction).
- Net effect: gold redistributed differently, but total world gold is unchanged.

**Anti-drift invariant**: `entity_gold_delta + shop_gold_delta == 0` at all times. The discount does NOT break this — it only changes the magnitude. Verified pattern matches E33C conservation proof.

**Forbidden pattern**: `gold_cost` must never go below 0 (which would create gold for the buyer). The formula `max(0.0, entity_rep) * 0.20` caps discount at 20%, so `gold_cost` floor is `base_price * 0.80`. Safe by construction, but the implementation must enforce `max(1, discounted_price)` as the final floor (matching DynamicPriceService's own `max(1, ...)` guard).

### No direct state mutation

`apply_reputation_discount()` must be a pure function — takes price int and entity/faction inputs, returns discounted int. Must not write to `AuthoritativeState` or any component directly.
