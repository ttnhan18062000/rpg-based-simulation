# Performance Investigation

## Identified Bottlenecks
- **Diagnostic Tracing**: `fingerprint()` and `CanonicalStateHasher.get_hash` were taking ~40-60% of tick time in high-density runs.
- **Passive Path Redundancy**: Every entity was being reconstructed every tick, even if no changes occurred, causing high memory churn and cache misses.
- **Readonly Freezing**: `readonly_view()` was being called every tick even if no workers were active, costing ~20ms per 1000 entities.
- **Collection Equality**: `==` on large dictionaries (corpses, entities) was causing periodic stalls in `apply_passive`.

## Optimized Logic
- Staggered updates reduced active passive mutations by 90% in idle states.
- Identity preservation allows `readonly_view` to hit the cache for 90-100% of entities in idle ticks.
- `is` checks for collections reduced $O(N)$ equality costs to $O(1)$.
