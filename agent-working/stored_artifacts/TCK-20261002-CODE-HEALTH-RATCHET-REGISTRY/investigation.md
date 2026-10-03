---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY

## Context scan
- `search_docs` (ratchet, grandfathered baseline, reviewed field) and `graphify query`: `tools/capability_envelope_baseline.py` and `registries/capability_envelope_registry.jsonl` are the template for CLI shape and the typed `reviewed` field; `TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION` is the lesson to avoid (one number for frozen debt and live regressions); `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS` names the seven files of the four class pairs.
- Prior tools reused: `tools/code_health/line_count.py` (symbols), `tools/parity_ledger_writer.py` (ledger write; a dry-run re-dump of `infrastructure.yaml` was byte-identical, so no reformat diff).

## Findings
1. **Real output shapes.** ruff JSON gives absolute paths, a rule code, a row and no symbol. complexipy JSON gives `path`, `function_name` as `Class::method` and an integer complexity. jscpd gives `firstFile`/`secondFile` names relative to the scanned directory and a line count. `line_count --format json` gives qualname symbols and levels.
2. **Match keys** (documented in `tools/code_health/findings.py` and the registry docstring): ruff `(file, None, rule)` with value = count (ruff gives no symbol; per-file counts are the ticket's suggested key and keep the registry small); complexipy and line_count `(file, qualified symbol, rule)` with value = measured; jscpd `(lower path, "dup:" + higher path, "duplicate-block")` with value = total duplicated lines for the pair. None uses a line number.
3. **Repeated keys.** Python allows one symbol name twice in a file (property getter and setter, `typing.overload`, if/else definitions). line_count and complexipy keep the larger value; jscpd and ruff sum. Tested.
4. **Registry size.** A full scan gives 3,617 rows (ruff 2,892; complexipy 384; line_count 283; jscpd 58), 730 KB. Per-function ruff rows would have been about 1,000 more, so ruff stays per-file-per-rule.
5. **Deleted source files.** A strict "file must exist" check would make the registry unusable the moment another session deletes a file. The validator keeps the check (required by the ticket) but `check`, `list`, `delete` and `tighten` skip it, so a vanished file is a "gone" row.
6. **complexipy: adapter, not native snapshot.** Roadmap 6.3 says tools with a native baseline keep their own file; the ticket's request and first acceptance criterion say one adapter per adopted tool. The adapter wins: one ratchet, one registry, symbol keys straight from complexipy's JSON, and no second baseline file with its own semantics. This departs from the roadmap's default and is flagged to the planner; reversing it means dropping `adapt_complexipy` and recording the snapshot file in the registry.
7. **Planner review (TOOL-CONFIG), Important:** ruff's default `F` (pyflakes) set had been switched off by the explicit `select`, hiding 1,043 existing findings, so a new undefined name would be invisible to the ratchet. `F` and `E9` are added to `select` before seeding, with a rule X1 in the standard.
8. **Same-name pairs.** None of the seeded duplication rows touches the seven files, so no row carries the link today; a test shows a row that does would link `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS` and nothing else, and that no other tool's row on those files is linked.
9. **Known limits** (stated, not fixed): fixing one violation and adding another of the same rule in the same file nets to zero for ruff rows; a renamed or moved function shows as new (its old row is "gone"); a ruff or complexipy version bump changes findings and needs a reseed; jscpd runs through `npx` with unpinned transitive dependencies, so this must not become a blocking CI gate in that form.
