# Investigation — TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE

**Per this ticket's own explicit acceptance criteria: "No implementation without the design
decision above." This is a design question with real options and a recommendation, not a
decision. Nothing in `src/` or `tests/` is changed by this investigation.**

## The current hardcode, read directly from `src/town/guild.py`

`GuildAction.visit()`'s lead-generation block:

```python
for node in state.resource_nodes.values():
    if node.kind == "iron_vein":
        lead_id = f"iron_lead_{node.id}"
        ...
        LeadState(..., subject="iron_ore", ...)
```

**There are two independent hardcoded literals here, not one** — the ticket's own title names
`node.kind == "iron_vein"`, but `subject="iron_ore"` a few lines below is a second literal, for a
related but distinct piece of data (the resource's *yield material name*, not its *content id*).
Both would break identically and silently on a content rename; a fix that only addresses the first
leaves the second exposed to the exact same failure mode.

## What already exists to build on

`GuildAction.visit()` itself, a few lines below the lead-generation block, already reads
`ResourceRegistry` generically (not hardcoded to one kind) for its quest-pressure scarcity
calculation:

```python
for node in getattr(state, "resource_nodes", {}).values():
    if not ResourceRegistry.contains(node.kind):
        continue
    res_def = ResourceRegistry.get(node.kind)
    if region_id in res_def.source_region_tags and node.max_charges > 0:
        ratios.append(node.remaining_charges / node.max_charges)
```

`ResourceDef` (`src/core/registries.py`) schema: `id`, `yield_item`, `source_region_tags`,
`required_tool`, `base_difficulty`. **No generic `tags`/`metadata` field of its own** — unlike the
sibling `ItemDef`-shaped class a few lines above it in the same file, which does have `tags:
Tuple[str, ...]`. Checked directly rather than assumed.

`ResourceDef.yield_item` for `iron_vein` (`data/content/world/resources.yaml`) is `"iron_ore"` —
confirmed via direct read of the real content file. This means the second hardcode
(`subject="iron_ore"`) could be derived from `ResourceRegistry.get(node.kind).yield_item` using
the SAME registry lookup the scarcity block already performs a few lines below, rather than a
second independent literal.

## Candidates weighed (per the ticket's own Scope, not assuming either way)

**1. A content-declared "guild-relevant resource kinds" tag.** Would require adding a `tags:
Tuple[str, ...] = ()` field to `ResourceDef` (mirroring the sibling `ItemDef`-shaped class's own
existing `tags` field in the same file — a real, precedented shape, not invented from nothing),
updating `CatalogToResourceRegistryAdapter.adapt()` to read it from
`data/content/world/resources.yaml`, and authoring the tag onto `iron_vein`'s own content entry.
Most durable: survives both a rename AND a new iron-like resource being added under a different
id. Real cost: schema change + adapter change + content authoring, for a mechanic whose own Out of
Scope explicitly excludes ever covering more than iron/iron-vein-equivalent kinds.

**2. Derive from the existing `source_region_tags` mechanism.** Checked directly and rejected:
`source_region_tags` answers "which regions can this resource be found in," a different, unrelated
question from "should the guild generate rumor leads about this resource." Repurposing it would be
a real misuse of what that field means, not a genuine reuse of an existing mechanism — the ticket's
own suggestion to weigh this candidate is reasonable to raise, but it doesn't survive the check.

**3. A named constant + a catalog-existence test that fails loudly if it goes stale.** Cheapest:
replace the two inline literals with one named module-level constant (the resource kind id) plus a
registry-derived lookup for the yield material, and a real test asserting the constant's value
still exists in `ResourceRegistry`/the real content catalog — the exact test that would have caught
the original `"iron"` vs. `"iron_vein"` mismatch. Does not solve "a new iron-like resource under a
different id" (Option 1 does), but that case is explicitly out of this ticket's own scope
(lead-generation coverage staying at iron/iron-vein-equivalent only).

## Recommendation: Option 3, with Option 1 named as the natural next step if scope ever expands

Given the ticket's own Out of Scope explicitly excludes broadening lead-generation coverage beyond
iron/iron-vein-equivalent, building Option 1's full content-tagging mechanism now would be
building infrastructure for a need this ticket itself says isn't there — the kind of premature
abstraction this project's own conventions already warn against. Option 3 fixes the actual
disclosed problem (silent breakage on rename) at the scope this ticket actually asks for, converts
a currently-silent failure mode into a loud one, and additionally closes the second hardcode
(`subject="iron_ore"`) by deriving it from `ResourceRegistry` via the same lookup pattern the
scarcity block already uses two lines below — no new infrastructure, reusing what's already there.

If lead-generation is ever deliberately expanded to cover more resource kinds (a decision outside
this ticket, per its own Out of Scope), Option 1 becomes the right shape at that point — the `tags`
field precedent already exists on the sibling class in the same file, so it wouldn't be starting
from nothing.

## What the required test would look like

A test in `tests/unit/town/` (or wherever `guild.py`'s own tests live) asserting the named resource
kind constant is a real key in `ResourceRegistry` (bootstrapped from the real content catalog, not
a test fixture) — this is the specific, minimal check that would have caught `"iron"` vs.
`"iron_vein"` before it shipped, without needing a full corpus-run reproduction.
