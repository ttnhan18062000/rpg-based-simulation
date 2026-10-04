---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
artifact_type: test_plan
tags: [delivery]
---

# Test Plan — TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET

Scoped runs only (`tests/codebase`, `tests/tools/test_parity_ledger_*.py`, `tests/docs`, `tests/static`), venv `.venv/bin`, under the 2 GB cap.

Unit (synthetic ledgers in `tmp_path`, real `schema.json`):
- clean ledger equals baseline: exit 0, no output of rises.
- add one entry with `status: verified` and `test_path: null`: exit 1, message names the file, the rule `allOf/0/then/properties/test_path/type`, baseline vs current counts and the entry id (failure mode, the ticket's AC).
- remove one error: exit 0 and the decrease is reported with the `tighten` hint.
- same total, different rule (swap across rules): fails on the new `(file, rule)`.
- a new shard file with errors fails; a shard that disappears is a decrease.
- root-level failure (a shard that is a mapping, not a list) is counted under its own rule.
- unparsable YAML shard, missing baseline, malformed baseline, missing schema: exit 2 with a message, never a traceback.
- `tighten`: dry run writes nothing; `--yes` writes decreases; refuses (exit 1, nothing written) when any count rose or a rule is new; output is sorted and stable (byte-identical on a second run).
- `seed`: refuses to overwrite without `--force`.
- pure functions `count_errors` and `compare` directly (edge: empty ledger, zero counts dropped from the baseline).
Live: the real ledger against the committed baseline passes (no rise); the baseline's three rule keys are exactly the ones on main; `schema.json` parses and the gate loads it unmodified.
Mutation proofs (verify the mutant applied and failed for the right reason): flip the rise comparison; skip the new-rule branch; make `tighten` accept a rise. Each must fail at least one named test.
Real CLI: `python3 -m codebase.gates.parity_ledger_schema check` from the repo root on main's ledger prints 2,862 as split and exits 0; the AC demo in a scratch copy (add a verified/null entry: exit 1 naming file and rule; remove an error: exit 0 plus decrease).
Also: `git diff --stat` shows `schema.json` and every ledger YAML absent; CI coverage test (`tests/codebase` already in `tools-a-e`); frontmatter validators.
