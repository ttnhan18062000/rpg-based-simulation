# Plan — TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE

Peer approved Option 3 (named constant + catalog-existence test).

1. Add `GUILD_LEAD_RESOURCE_KIND = "iron_vein"` as a named module-level constant in
   `src/town/guild.py`, replacing the inline `node.kind == "iron_vein"` literal.
2. Derive the second hardcode (`subject="iron_ore"`) from `ResourceRegistry.get(node.kind).yield_item`,
   reusing the same `ResourceRegistry` lookup the scarcity block a few lines below already performs
   — no new infrastructure.
3. Add a fail-loud test asserting `GUILD_LEAD_RESOURCE_KIND` still exists in the real content
   catalog (`ResourceRegistry`, bootstrapped from `data/content/world/resources.yaml` via the
   existing `tests/conftest.py` autouse fixture) — the exact check that would have caught the
   original `"iron"` vs. `"iron_vein"` mismatch.
4. Add a test proving the derived `subject` matches the real catalog's own `yield_item`, not a
   value copied into the test (so a future catalog change to `yield_item` would also be caught).
5. Full regression, close the ticket.
