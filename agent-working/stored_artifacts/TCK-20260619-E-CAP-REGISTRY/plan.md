# Plan: TCK-20260619-E-CAP-REGISTRY

## Steps

1. Create `docs/engine/capability_registry.yaml` — 29 entries (16 OFFICIAL, 5 SUPPORTED, 1 EXPERIMENTAL, 7 UNSUPPORTED)
2. Create `src/engine/capability.py` — CapabilityRegistry class with is_supported()/get_status()/all_capabilities(); loads YAML lazily
3. Create `tests/unit/engine/test_capability_registry.py` — 9 unit tests
4. Create `tests/architecture/test_capability_references.py` — uniqueness guard
5. Update `docs/engine/known_limitations.md` — reference capability_registry.yaml; simplify to human-readable notes only
6. Append INFRA-209 to `docs/parity_ledger/infrastructure.yaml`

## Scope Guards
- Do NOT add runtime capability checks to engine hot path
- Do NOT modify existing tests

## Architecture Review
APPROVED — additive YAML + thin reader, no pipeline changes, no durable state mutations.
