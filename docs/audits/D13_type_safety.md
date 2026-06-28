---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, type-safety, mypy, annotations, validation, api-boundary, dict, Any]
---

# D13 — Type Safety & Validation Boundary

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | B — Codebase / Architecture |
| **State** | `done` |
| **Impact** | 3 / 5 |
| **Interest** | 2 / 5 |
| **Priority** | 5 |
| **Method** | measure |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Where do untyped surfaces and missing validation create
risk — what would a type checker catch that currently goes undetected?

**Related dimensions:** D12 (Pattern Consistency) — F4 there (3 domain phases missing
typed return annotations) is the border finding between D12 and D13; D18 (CI Pipeline) —
adding a type checker step to CI would enforce all findings here automatically; D09 (System
Wiring) — the API route handlers audited here are the public-facing surface of the wired
system.

---

## Measure Method

An AST scanner (`ast` module) enumerated all public functions in `src/` (excluding
leading-`_` private helpers). Return annotations, argument annotations, `Any` usages, and
`dict` / `Dict` return types were counted per file. Type checker configuration was checked
across `mypy.ini`, `pyproject.toml [tool.mypy]`, `pyrightconfig.json`, and `setup.cfg`.

Each gap finding is scored by Type Safety Risk — how likely a type error at this surface
propagates silently to incorrect behavior.

### Type Safety Risk Scoring

3 dimensions, each 1–5. Maximum: 15. Higher score = more urgent to address.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Boundary Criticality** | Lab / tooling only; no effect on live simulation | Engine state exposed to downstream callers | API contract or authoritative pipeline; correctness depends on type shape |
| **Gap Severity** | A few isolated missing annotations | Entire class or subsystem unannotated | Complete interface returns `Any` / untyped dict; no caller can trust the shape |
| **Silent Failure Risk** | Runtime always raises on type error | Type error visible in tests with some coverage | Type mismatch silently produces wrong behavior (wrong key, wrong shape, silent None) |

---

## Coverage Baseline

AST scan of all public functions in `src/`:

| Metric | Count | % of 2,057 |
|---|---|---|
| Public functions scanned | 2,057 | — |
| Missing return annotations | 186 | 9.0% |
| Missing argument annotations | 26 | 1.3% |
| `Any` in annotations | 455 | — |
| `dict` / `Dict` return types | 163 | — |

**91% of public functions have return annotations** — annotation discipline is solid as a
convention. The problem is enforcement: no type checker is configured anywhere.

### Top files by annotation gap

| File | fns | !ret | !arg | Any | dict |
|---|---|---|---|---|---|
| `api/server.py` | 20 | 18 | 0 | 0 | 0 |
| `core/state.py` | 42 | 11 | 3 | 23 | 22 |
| `api/engine_manager.py` | 28 | 11 | 0 | 10 | 4 |
| `api/ws/stream.py` | 8 | 8 | 0 | 0 | 0 |
| `api/routes/history.py` | 8 | 8 | 0 | 0 | 0 |
| `lab/workflows.py` | 16 | 7 | 0 | 8 | 7 |
| `api/routes/behavior.py` | 7 | 7 | 0 | 0 | 0 |
| `engine/patches.py` | 56 | 1 | 2 | 20 | 0 |
| `lab/validator.py` | 18 | 3 | 0 | 9 | 0 |

---

## Key Findings

### F1 — No type checker configured: annotation discipline is documentation only — Priority: 15 / 15 — **RESOLVED (TCK-20260623-TYPE-CHECKER)**

> **Resolution (2026-06-23):** `[tool.mypy]` section added to `pyproject.toml` with
> `python_version="3.11"`, `strict=false`, `ignore_missing_imports=true`,
> `warn_return_any=true`, `warn_unused_ignores=true`. Excluded V1 modules
> (`src/ai/`, `src/town/`, `src/quests/`, `src/entities/`, `src/progression/`).
> `make typecheck-py` Makefile target added. mypy step wired into CI fast job
> (`continue-on-error: true` on first pass). Parity ledger entry INFRA-TYPE-001 added.

| Dimension | Score | Reason |
|---|---|---|
| Boundary Criticality | 5 | Affects every module in `src/`; zero automated enforcement across 2,057 public functions |
| Gap Severity | 5 | No `mypy.ini`, no `[tool.mypy]` in `pyproject.toml`, no `pyrightconfig.json`, no `mypy` Makefile target |
| Silent Failure Risk | 5 | Type errors can only be caught at runtime; 455 `Any` usages and 186 missing annotations create silent drift opportunities |
| **Total** | **15** | |

No type checker is configured anywhere in the project. Checked:
- `mypy.ini` — does not exist
- `pyproject.toml [tool.mypy]` — section absent; only test markers reference `strict_matrix`
- `pyrightconfig.json` — does not exist
- `Makefile` — no `mypy` or `pyright` target

All 91% of annotated functions are annotated for documentation value only. There is no tool
that reads those annotations and enforces them. A caller passing a `str` where an `int` is
expected, or a function returning `None` where a typed record is expected, produces no
tooling signal — only a runtime error when the path is exercised.

**Fix:** Add `[tool.mypy]` to `pyproject.toml` and a `make typecheck` target. Baseline
with `ignore_missing_imports = true` and `warn_return_any = true` to get value immediately
without requiring full annotation of the codebase.

---

### F2 — api/server.py: 18 route handlers with no return type / no response_model — Priority: 11 / 15 — **RESOLVED (TCK-20260623-TYPE-CHECKER)**

> **Resolution (2026-06-23):** `response_model=` added to 13 of 18 inline routes in
> `src/api/server.py`. The remaining 5 routes (`/metrics`, `/history/runs/{id}/report`,
> `/observability/ui`, two `RedirectResponse` routes) are intentionally excluded — they
> return raw `Response`, `RedirectResponse`, or `HTMLResponse` types that are incompatible
> with `response_model`. The 3 highest-risk engine_manager routes use typed TypedDict
> schemas (`WorldStateResponse`, `EntityPageResponse`, `Optional[EntityDetailResponse]`)
> from `src/api/schemas.py`. The remaining 10 actionable routes use `Dict[str, Any]`
> as a typed placeholder.

| Dimension | Score | Reason |
|---|---|---|
| Boundary Criticality | 5 | These are the public API endpoints clients call; FastAPI uses return type or `response_model=` for output schema generation and validation |
| Gap Severity | 4 | All 18 primary route handlers lack annotations; `api/routes/history.py` (8) and `api/routes/behavior.py` (7) are also fully unannotated |
| Silent Failure Risk | 2 | FastAPI still serializes any dict/object returned; a wrong response shape serializes silently without error |
| **Total** | **11** | |

18 route handlers in `api/server.py` are missing return type annotations and have no
FastAPI `response_model=` decorator parameter. The full list includes core endpoints:

```python
async def get_live_snapshot() -> MISSING     # L102
async def get_state() -> MISSING             # L126
async def get_entities() -> MISSING          # L141
async def get_entity() -> MISSING            # L150
async def inspect_live_entity() -> MISSING   # L112
async def health_check() -> MISSING          # L88
async def get_run_report() -> MISSING        # L210
# ... 11 more
```

FastAPI generates OpenAPI schema from return annotations. Without them the generated
client/docs shows these routes as returning an empty schema. A shape regression in a
response (e.g. a key renamed in `EngineManager.get_state()`) serializes silently — no
validation step catches the change before the client receives it.

This finding also covers `api/routes/history.py` (8 handlers) and `api/routes/behavior.py`
(7 handlers), which are all unannotated.

---

### F3 — api/engine_manager.py: core state-query methods return Dict[str, Any] — Priority: 10 / 15 — **RESOLVED (TCK-20260623-TYPE-CHECKER)**

> **Resolution (2026-06-23):** Investigation confirmed all 4 state-query methods
> (`get_state()`, `get_full_snapshot()`, `get_entities_paged()`, `get_entity()`) already
> carry explicit return type annotations (`-> Dict[str, Any]` / `-> Optional[Dict[str, Any]]`).
> The remaining F3 work — typed response schemas and `response_model=` wiring — is
> satisfied by `src/api/schemas.py` (new file with `WorldStateResponse`,
> `EntityPageResponse`, `EntityDetailResponse` TypedDicts) and the `response_model=`
> additions on the corresponding routes in `server.py`.

| Dimension | Score | Reason |
|---|---|---|
| Boundary Criticality | 4 | These methods are the bridge between engine internal state and the API layer; callers receive dicts with unknown shape |
| Gap Severity | 3 | 4 of 28 public methods return `Dict[str, Any]`; the others are unannotated (`-> MISSING`) but return simpler values |
| Silent Failure Risk | 3 | A key rename in engine state (e.g. `health_score` → `health`) only manifests when a client accesses the renamed key; no static signal |
| **Total** | **10** | |

The four methods that bridge engine state to the API layer all return `Dict[str, Any]`:

```python
get_metrics_snapshot() -> Dict[str, Any]   # L73
get_state()            -> Dict[str, Any]   # L176
get_full_snapshot()    -> Dict[str, Any]   # L183
get_entities_paged()   -> Dict[str, Any]   # L191
get_entity()           -> Optional[Dict[str, Any]]  # L198
```

The `api/server.py` route handlers call these methods and return their output directly.
The chain is: engine state → `EngineManager.get_state()` → `Dict[str, Any]` →
`api/server.py:get_state()` (no annotation) → FastAPI → client JSON.

No point in this chain validates shape. A regression in which keys `get_state()` returns
is invisible to any tooling until a client reports missing data.

**Remediation path:** Define `StateSnapshot`, `EntityPageResponse`, `MetricsSnapshot` as
Pydantic response models or TypedDicts. Wire them as `response_model=` on the route
decorators and as return types on `EngineManager` methods. FastAPI will then validate
response shape on every call.

---

### F4 — lab/workflows.py: all 7 Workflow.run() methods return dict[str, Any] — Priority: 7 / 15

> **Ticket:** TCK-20260627-P2I-WORKFLOW-TYPES

| Dimension | Score | Reason |
|---|---|---|
| Boundary Criticality | 2 | Lab/workflows is not on the live simulation path; results are consumed by platform scenarios and tests |
| Gap Severity | 4 | Every workflow type's `run()` returns `dict[str, Any]`; callers rely on key-name convention only |
| Silent Failure Risk | 1 | Tests fail loudly when a required key is missing; lab is developer-facing not user-facing |
| **Total** | **7** | |

All 7 workflow `run()` methods in `src/lab/workflows.py` return `dict[str, Any]`:

```python
class SweepWorkflow:     run() -> Dict[str, Any]   # L88
class MutationWorkflow:  run() -> Dict[str, Any]   # L597
class SandboxWorkflow:   run() -> dict[str, Any]   # L871, L1120, L1575, L2065, L2326
```

Callers in `platform/scenarios.py` and test files access specific keys (e.g. `result["summary"]`,
`result["health_score"]`) by name convention. A renamed key in `SweepWorkflow.run()` only
surfaces when the caller's key lookup raises `KeyError` at runtime — no static signal.

This is a medium-priority gap: lab code is developer-facing and tests cover the main result
keys, but the untyped interface makes refactoring fragile.

---

### F5 — engine/patches.py: merge() returns Any — Priority: 6 / 15

> **Ticket:** TCK-20260627-P2J-PATCHES-TYPE

| Dimension | Score | Reason |
|---|---|---|
| Boundary Criticality | 3 | `merge()` is used in the engine patch application path — moderate criticality |
| Gap Severity | 2 | Single function returning `Any`; `merge_dict()` is also unannotated but lower risk |
| Silent Failure Risk | 1 | Patch merging is covered by certification tests; errors surface during cert harness runs |
| **Total** | **6** | |

`engine/patches.py:L29 merge() -> Any` is used to apply patches in the engine. The `Any`
return type means callers cannot statically verify what `merge()` returns — a type error
in a merged patch value is invisible until the downstream consumer (in the authoritative
pipeline) processes it.

This is the only `Any` return in an engine-tier module that is not a serialization method.
It warrants a typed return — `merge()` should specify what it returns (likely the same
type as its inputs, or a `MergedPatch` TypedDict).

---

### F6 — core/state.py: 13 to_canonical_dict() methods return Dict[str, Any] — Priority: 5 / 15

| Dimension | Score | Reason |
|---|---|---|
| Boundary Criticality | 2 | Serialization output consumed by JSON encoders and test assertions; not a correctness boundary |
| Gap Severity | 3 | 13 state dataclasses define this method; the return is intentionally untyped (serialization) |
| Silent Failure Risk | 0 | Test assertions on specific keys provide coverage; JSON serialization of extra/missing keys is not a silent failure |
| **Total** | **5** | |

13 dataclasses in `core/state.py` implement `to_canonical_dict() -> Dict[str, Any]` for
JSON serialization. This is the standard Python pattern for dataclass serialization.
The risk is that if a field is renamed in the dataclass but not in `to_canonical_dict()`,
the dict will be wrong — but this is already caught by integration tests that deserialize
the JSON and check fields.

This finding is low priority — `Dict[str, Any]` is idiomatic here, and the gap does not
introduce silent failures in practice.

---

### Type Safety Risk Summary

| Finding | Description | Risk Score |
|---|---|---|
| F1 | No type checker configured — 2,057 functions unenforced | **15 / 15** |
| F2 | `api/server.py` 18 route handlers: no return annotation, no `response_model` | **11 / 15** |
| F3 | `api/engine_manager.py` state-query methods return `Dict[str, Any]` | **10 / 15** |
| F4 | `lab/workflows.py` all `run()` methods return `dict[str, Any]` | **7 / 15** |
| F5 | `engine/patches.py` `merge()` returns `Any` | **6 / 15** |
| F6 | `core/state.py` 13 `to_canonical_dict()` methods return `Dict[str, Any]` | **5 / 15** |

---

## Validation Strengths

These surfaces are well-validated and do not require attention:

| Surface | Assessment |
|---|---|
| FastAPI input params (`api/routes/search.py`, `behavior.py`) | Fully typed via `Query()` with range constraints (`ge=`, `le=`); validated on every request |
| Content loading boundary (`WorldModuleSpec`, `WorldCompositionSpec`, etc.) | Pydantic with `extra="forbid"`; validation fires at YAML load time with clear errors |
| Domain phase `execute()` returns (5 of 8) | Typed: `ProgressionConversionResult`, `CooperationResult`, `CombatEngagementDecisionResult`, etc. |
| Engine authoritative pipeline typed records | `AuthoritativeUpdate`, `PhaseResult` etc. are typed dataclasses throughout the pipeline |
| `api/routes/entities.py` entity reads | Confirmed in D14 — uses `get_entity_dto()` not raw model |

---

## Recommended Follow-Up Tickets

| Priority | Action | Finding |
|---|---|---|
| **P1** | Add `[tool.mypy]` to `pyproject.toml` with `ignore_missing_imports = true`, `warn_return_any = true`; add `make typecheck` target; wire into CI `test.yml` (D18 P0) | F1 |
| **P1** | Add Pydantic `response_model=` to the 18 core route handlers in `api/server.py`; define `StateSnapshot`, `EntityPageResponse`, `MetricsSnapshot` typed response models | F2 + F3 |
| P2 | Define `WorkflowResult` TypedDict (or dataclass) and annotate all 7 `Workflow.run()` returns in `lab/workflows.py` | F4 |
| P2 | Narrow `engine/patches.py:merge()` return type from `Any` to the actual merged type | F5 |
| P2 | Add return annotations to 3 domain phase `execute()` methods: `world_emergence`, `perception`, `memory` (noted in D12 F4) | D12 F4 |

---

## Related Dimensions

- **D18 (CI Pipeline)** — F1 here (no type checker) is directly remediated by adding a `make typecheck` step to the `test.yml` CI workflow recommended in D18. Both gaps need to close together — configuring mypy without CI means it's still developer-opt-in only.
- **D12 (Pattern Consistency)** — F4 there (3 domain phases missing typed return annotations) is the entry point to D13's surface. D12 F4 is a consistency gap; D13 explains why enforcement is absent.
- **D09 (System Wiring)** — The API route handlers audited in F2 are the public-facing surface of the fully-wired system D09 confirmed. Adding `response_model=` to these routes would make the entire wired surface contractually verifiable.