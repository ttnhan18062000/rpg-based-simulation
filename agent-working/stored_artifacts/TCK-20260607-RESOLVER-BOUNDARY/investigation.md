---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-RESOLVER-BOUNDARY
artifact_type: investigation
tags: [resolver, boundary]
---

# TCK-20260607-RESOLVER-BOUNDARY — Investigation

## Findings

### 1. Where exactly does the union type appear?

`src/worldassembly/resolver.py` lines 652–657:

```python
def resolve_module_contribution(
    self,
    module: WorldModuleSpec | NormalizedWorldModule,
    prefix: str = "",
    param_vals: Dict[str, Any] = None
) -> ResolvedModuleContribution:
```

The parameter is named `module`, typed as the union `WorldModuleSpec | NormalizedWorldModule`.
There is no existing runtime isinstance guard — the function assumes duck-typing compatibility
between the two types.

### 2. Is WorldModuleSpec ever passed directly to resolve_module_contribution in real code?

**No.** Grep of all `.py` files under `src/` and `tests/` finds exactly four call sites:

| Location | Argument passed |
|---|---|
| `src/worldassembly/resolver.py:286` (inside `assemble()`) | `spec` — a `NormalizedWorldModule` (assigned from `WorldModuleAuthoringNormalizer.normalize(module_spec)` at line 233) |
| `tests/unit/worldassembly/test_archetype_preservation.py:92` | `normalized_spec` — explicitly normalized beforehand |
| `tests/unit/worldassembly/test_archetype_preservation.py:124,153,222` | `normalized` or `normalized_spec` — explicitly normalized beforehand |
| `tests/integration/worldassembly/test_real_content_world_modules.py:86` | `normalized` — explicitly `WorldModuleAuthoringNormalizer.normalize(spec)` |

**Every call site already passes a `NormalizedWorldModule`.** No call site passes a raw `WorldModuleSpec`.
The union type is therefore a latent footgun with no active use.

### 3. Does assemble() always normalize first?

Yes. `assemble()` (resolver.py lines 229–234) calls:
```python
module = WorldModuleAuthoringNormalizer.normalize(module_spec)
graph_map[ref.module_id] = module
```
Then at line 286 calls `self.resolve_module_contribution(spec, ...)` where `spec = graph_map[m_id]`
— which is the already-normalized `NormalizedWorldModule`.

(Note: the local variable is named `spec` at line 271 (`spec = graph_map[m_id]`) — this is
a naming artifact that could cause confusion but does NOT mean a raw `WorldModuleSpec` is passed.)

### 4. What is the snapshot test the ticket refers to?

The ticket defines a test `test_contribution_snapshot_after_normalization` that:
- Constructs a minimal `WorldModuleSpec` fixture (no catalog dependencies needed for empty-field module)
- Runs `WorldModuleAuthoringNormalizer.normalize()` on it
- Calls `resolve_module_contribution(normalized, ...)`
- Asserts the structural shape of `ResolvedModuleContribution` fields:
  `resource_refs`, `building_refs`, `service_refs` are `{}` for an empty module;
  `regions`, `factions`, `population_refs`, `resolved_population_specs`, etc. are empty lists.

**The test currently does not exist** — `test_resolver.py` has no tests for `resolve_module_contribution`
itself; it tests `CompileProfileResolver.resolve()` and `WorldCompiler.compile()` only.

### 5. NormalizedWorldModule field note

`NormalizedWorldModule` is a frozen dataclass (not Pydantic). Its `biomes`, `ecologies`,
`populations`, `relationships` fields are `Tuple[str, ...]` (recently changed from `List[str]`
per companion ticket TCK-20260607-NORMALIZEDMODULE-TYPING — that ticket is now DONE).
`resources`, `buildings`, `services` are `Dict[str, int]`. This is what the snapshot test
should assert against.

### 6. Parity ledger scan

No entry in `docs/parity_ledger/substrate.yaml` specifically covers `resolve_module_contribution`
or the resolver boundary. The assembly pipeline entries (SUB-series) cover world generation
determinism and authoritative pipeline correctness, but none target this specific type guard.
A new parity entry SUB-367 is referenced in `resolver.py` comments for the service_refs gap
(docs/parity_ledger/substrate.yaml entry for SUB-367 is the service_refs gap guard test).

No existing parity entry is affected by this refactor.

## Open Questions

None. All questions from the ticket's open questions section are resolved by the grep:
- No external caller bypasses normalization. All four call sites pass `NormalizedWorldModule`.
