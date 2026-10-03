---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-ENGINE
artifact_type: test_plan
tags: [mutation, engine]
---

# Test Plan - Mutation Engine

We will write a comprehensive unit test suite in `tests/unit/lab/test_mutation_engine.py` covering:

## Tests
- `set` operation successfully overwrites values.
- `add` operation applies positive/negative changes.
- `multiply` operation scales numeric targets.
- `remove` operation deletes targets (e.g. resource nodes, region fields).
- `toggle` operation flips booleans or forces specific overrides.
- `duplicate` duplicates objects in list fields with a brand new ID.
- Immutability check ensuring the base specs remain unchanged.
- Path traversal verification (handling both direct list-id search and optional dummy placeholder segments like `nodes`).
- Rejection of invalid paths, raising explicit exceptions and reporting failures gracefully.
- Schema validation barriers ensuring invalid target types or validation failures (like duplicate IDs, overlapping bounds, or invalid coordinate systems) are detected and blocked.
