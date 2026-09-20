---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP
phase: done
date: 2026-09-20
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP

## Finding: the page renders zero system membership

Read `tools/mechanism_registry/generate_mechanism_registry_html.py` in full (258 lines before this
batch). Confirmed peer's finding directly: the only occurrence of the substring "system" in the
rendered output was the CSS `font-family` stack (`-apple-system, ...`) — no per-mechanism systems
column, no rollup, no filter. `render()` built its table rows entirely from
`all_mechanisms_combined_view(data)`, which does not carry the `systems` field at all (it wasn't
designed to — that view predates the system tier).

## Finding: a `--check` mode already exists, unused

Lines 242-249 (pre-batch) already implemented `--check`: render fresh, compare against the file on
disk, exit 1 and print `STALE: ...` on mismatch, exit 0 and print `OK: ...` otherwise. It was never
wired to a Makefile target or to CI — confirmed via `grep -n "registry-html" Makefile
.github/workflows/test.yml` returning only the plain (non-check) `mechanism-registry-html` target
before this batch.

## Available building blocks (all reused unmodified)

- `registry.py::build_system_rollup(data)` — returns `{"baseline", "systems", "unassigned"}`, each
  a full stats dict (count, bound, bound_rate, bound_unverified, runtime_verified,
  static_verified, verified, verified_rate, unverified, state_counts). Landed
  `TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW`.
- `registry.py::mechanisms_by_system(data)` — not called directly by this ticket's own code;
  `build_system_rollup()` already calls it internally.
- `generate_mechanism_system_rollup_view.py::_rollup_row_html`-equivalent row logic (that module's
  own `_row()` helper) — used as the structural precedent for this ticket's own
  `_rollup_row_html()`, since the two views must show identical numbers in identical shape per the
  "reuse unmodified, never recompute a second way" constraint.

## Real registry numbers confirmed via direct comparison

Spot-checked the `combat` row's own numbers between the existing markdown rollup
(`docs/brainstorm/mechanism_system_rollup_view.md`) and this batch's new HTML rollup section —
byte-identical count/rate/vs-baseline text, confirming both consume the same
`build_system_rollup()` output with no independent recomputation.

Confirmed 8 real multi-system mechanisms render with multiple pill badges and a comma-joined
`data-systems` attribute: `movement` (combat,world), `personality` (progression,cognition),
`regional_sovereignty` (world,faction), `entity_trade` (social,economy), `fame` (world,social),
`guilds` (social,faction), `quest_generation_sourcing` (world,cognition), `adventure_routing`
(cognition,world).

## Test-isolation issue found while writing tests (not a product bug)

`tests/unit/tools/conftest.py` has an autouse fixture, `_empty_system_registry_by_default`, that
monkeypatches `tools.mechanism_registry.registry._load_system_registry` to return `{}` for every
test in this directory (documented rationale: keeps small synthetic fixtures used by pre-existing
tests from tripping invariant 10, which is a whole-corpus property). `generate_mechanism_registry_
html.py` imports `registry` via its own `sys.path.insert(0, tools/mechanism_registry)` +
`from registry import ...` — a separate module object under the bare name `"registry"`, distinct
from `sys.modules["tools.mechanism_registry.registry"]`. The autouse fixture only patches the
latter. A test that imported `build_system_rollup` via the dotted path and called it directly on
real registry data got zero registered systems (from the patched module) while `render()`'s own
internal call (via the unpatched bare-name module) correctly saw all 7 — a `StopIteration` when the
test looked for a `combat` row that build_system_rollup (patched copy) never produced. Root cause
confirmed by direct reproduction: same input dict, same function body, two different module
identities, only one patched. Fixed by importing `build_system_rollup` from
`generate_mechanism_registry_html`'s own namespace (the exact object `render()` calls), not by
touching the autouse fixture's scope — the fixture's own behavior for every pre-existing test is
correct and out of scope for this batch.

## Scope confirmation

No changes made to `registries/mechanisms.yaml`'s schema, any mechanism's `systems`/`state`/
`verified` fields, or `build_system_rollup()`/`mechanisms_by_system()`'s own computation. Confirmed
via `git diff --stat registries/mechanisms.yaml tools/mechanism_registry/registry.py` showing zero
diff on either file at the end of this batch.
