---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-MATRIX
artifact_type: investigation
tags: [mutation, matrix]
---

# Investigation - Variant Matrix Builder

## Combinatorics
- For $N$ mutations, the full factorial space of combinations has size $2^N$. For $N = 20$, this is over $1,000,000$ combinations, causing a memory and CPU explosion.
- Under `factorial_limited`, we must generate combinations sorted by cardinality size (starting with combinations of size 2, then size 3, up to $N$).
- We can use standard library `itertools.combinations(mutations, k)` for $k \ge 2$, generating combinations sequentially and adding them until the variant count reaches `max_variants`.
- If $2^N > \text{limit}$ and no explicit limit is specified, the builder must raise an exception or clamp to a default maximum variant count of 50 to prevent unbounded execution.

## Storage Layout
- Generated variants must be stored in standard file-system subdirectories (e.g. under standard lab run directories) to isolate specs during execution sandboxes.
- The `VariantManifest` must reference these paths, so it serves as the authoritative manifest for child sandbox runs.
