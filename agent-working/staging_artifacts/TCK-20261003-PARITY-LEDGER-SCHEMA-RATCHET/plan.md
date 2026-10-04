---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET

Base: `f15cc33f3` (root-move closure). Adds a ratchet over `docs/parity_ledger/*.yaml` against `docs/parity_ledger/schema.json`; changes no ledger entry and not `schema.json`.

## What I measured (reproduced, not taken from the ticket)
`jsonschema.Draft7Validator(schema).iter_errors(data)` over the 9 shards: 2,197 entries, **2,862 errors**, in 8 of 9 files (`faction.yaml` is clean). By schema path (relative to `items`): `allOf/0/then/properties/test_path/type` 1,312; `allOf/2/else/then/properties/test_path/type` 1,525; `properties/proof_type/enum` 25. Matches the ticket's split. Validation takes about 2 s. `jsonschema` is in the `dev` group, which every CI test job installs (`--no-group lint` only drops lint).

## Design
- **Module** `codebase/gates/parity_ledger_schema.py` (a gate, beside `mypy_gate`), run as `python3 -m codebase.gates.parity_ledger_schema <cmd>`. Reads only; the only write is the baseline, by `seed`/`tighten`.
- **Counting**: for each `docs/parity_ledger/*.yaml` (sorted), load, validate with Draft 7 against `schema.json`, count errors per `(file name, rule)` where `rule` = the failing schema path with the leading `items/` removed (a root-level failure, e.g. a shard that is not a list, keeps its path). A shard that does not parse as YAML is not a count: the check exits 2 (could not run) and says which file. Pure functions `count_errors(ledger_dir, schema_path) -> {file: {rule: n}}` and `compare(current, baseline) -> Result(rises, new, decreases, gone)`.
- **Baseline** `codebase/baselines/parity_ledger_schema_baseline.json`: `{"version": 1, "counts": {file: {rule: n}}}`, written with indent and sorted keys so each count is on its own line (two PRs that tighten different rules merge cleanly). No hash of `schema.json`: a schema change simply changes the counts.
- **Commands**: `check` (exit 0 when no `(file, rule)` count rose and no new `(file, rule)` appeared; 1 on a rise or new; 2 when it cannot run: missing/invalid baseline, missing schema, unparsable shard). On failure it names the file, the rule, baseline vs current, and up to 5 entry ids that fail that rule. Decreases are printed with "run `tighten`". `tighten [--yes]` rewrites the baseline to the current counts **only if there is no rise or new** (otherwise exits 1 and writes nothing; dry run without `--yes`). `seed [--force]` writes the first baseline (refuses to overwrite without `--force`), used once here.
- **Blocking from the start**, as the ticket says. I found no reason to soak: the ledger has no pending soak decision, `check` is read-only and about 2 s, and a decrease never fails. A decrease that is not tightened does not fail the PR (the lesson of `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`: an equality gate penalises fixing entries), so the test asserts "no rise", never "baseline == current".
- **Known limit, stated in the docs**: counts per `(file, rule)` cannot see a swap (one entry fixed and another broken in the same file and rule leaves the count equal). Entry-level keys would catch it but make the baseline 2,862 lines and make every id edit a baseline edit. I follow the ticket (counts) and ask the planner to confirm; the shape allows adding ids later.
- **Where the test runs**: `tests/codebase/test_parity_ledger_schema_gate.py`, in `tools-a-e` (no job is path-filtered, so a ledger-only PR runs it). The ticket said "static or docs lane"; I put it in `tests/codebase` because the module is under `codebase/` and `expected_test_dirs_for` maps `codebase/**` there (so the done-gate requires it). Say so if you want it in `tests/static` instead; the module does not change.
- **Not shared with `parity_ledger_writer.validate_entry`**: it hand-rolls the rules and never loads `schema.json`; reusing it would not give the per-rule paths. Left untouched (ticket allows).
- **Makefile**: one new target `parity-ledger-schema-check` (`python3 -m codebase.gates.parity_ledger_schema check`); no existing target or CI job name changes.
- **Docs**: `docs/parity_ledger/README.md` gets a "Schema check and baseline" section (what runs, the rule key, how to tighten, never raise by hand, the swap limit); `codebase/README.md` gets a row in the `gates/` entry.

## Steps (one commit each, tests green per commit)
1. Fold the planner's nits: Makefile comment `tools/codebase_health_*.py` -> `codebase/reports/codebase_health_*.py`; `test_domain_root_layout.py` on-disk check uses `exists()` (the `is_file()` on a directory never fired).
2. Module + unit tests (synthetic ledgers in `tmp_path` against the real `schema.json`).
3. `seed` the real baseline (must be 2,862 and 1,312 / 1,525 / 25), live test, Makefile target, docs.
4. Verify and close.

## Scope guards
`schema.json` byte-identical (`git diff --stat` shows it absent); no ledger YAML touched; no `src/`, `.claude/` or `CLAUDE.md`; no change to `parity_ledger_writer.py`. The `rule` key is derived from the schema path, so it is never a free-form string stored as meaning.

## Risks
- A ledger PR from another domain that adds an invalid entry now fails CI: intended; the error names file, rule and entry id.
- Entry ids in the message come from the YAML instance only; no ledger content is written anywhere.
- jsonschema version drift could change a `schema_path` spelling: the live test pins the three rule keys present on main, so a spelling change is caught as "baseline rule gone, new rule appeared" in review, not silently.
