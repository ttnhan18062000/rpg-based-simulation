# Implementation Sequence — worldgen-organic-terrain

Tickets must be implemented in this order. Generated from intra-batch dependency analysis
(cross-referencing each ticket's own `## Related Tickets` section against the other 4 tickets in
this batch). `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260821-NOISE-FILL-SCHEMA  (no deps in this batch)
2. TCK-20260821-COMPILER-NOISE-FILL  (depends on: TCK-20260821-NOISE-FILL-SCHEMA)
3. TCK-20260821-NOISE-FILL-DETERMINISM-TEST  (depends on: TCK-20260821-COMPILER-NOISE-FILL)
4. TCK-20260821-PROCEDURAL-GENERATOR-KEPT  (no deps in this batch)
5. TCK-20260821-WOLF-DEN-NOISE-MIGRATION  (depends on: TCK-20260821-NOISE-FILL-SCHEMA, TCK-20260821-COMPILER-NOISE-FILL)

## Why This Order Matters

TCK-20260821-NOISE-FILL-SCHEMA is the load-bearing prerequisite — the schema field
(`RegionRecipeSpec`/`RegionSpec`) every other content/compiler ticket in this batch needs to exist
before it can do anything real. TCK-20260821-COMPILER-NOISE-FILL is next: it's the only ticket that
makes the schema field have any visible effect, and it resolved a real design correction during
investigation (keying noise-fill RNG draws under a distinct `Domain` rather than sequencing within
`Domain.WORLD`'s existing draw order — `DeterministicRNG` is a stateless composite-key hash, not a
sequential stream, so this is simpler and safer than the epic's original framing).
TCK-20260821-NOISE-FILL-DETERMINISM-TEST only needs the compiler mechanism (a synthetic `WorldSpec`
fixture is sufficient per its own investigation) — it does **not** wait on the real-module migration.
TCK-20260821-WOLF-DEN-NOISE-MIGRATION waits on both the schema and the compiler mechanism, since it's
real content that needs both to have any effect, and its own investigation found the module's two
regions genuinely overlap, requiring an explicit paint-order decision this ticket must make.
TCK-20260821-PROCEDURAL-GENERATOR-KEPT is fully independent of the other four — it's a
documentation/decision-record ticket correcting the epic's own "investigate whether to delete"
premise (investigation found `WorldProceduralGenerator` is an intentionally preserved legacy path,
not dead code) — it can run at any point in this sequence, placement here is arbitrary.

Running alphabetically would attempt several tickets before their real prerequisites are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
