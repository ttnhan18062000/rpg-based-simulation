---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
artifact_type: investigation
tags: [delivery]
---

# Investigation — TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET

Order: `search_docs` (surfaced the writer's lockstep with `schema.json`, the earlier "equality gate penalizes improvement" ticket and the P0 test-path tickets), `graphify query` (the writer, `validate_entry`, and `tests/tools/test_parity_ledger_schema.py` form their own communities, no gate over the data), then reads on head `f15cc33f3`.

- `docs/parity_ledger/schema.json` is Draft 7, `items.allOf` with three conditionals; `tests/tools/test_parity_ledger_schema.py` checks only the schema file; `parity_ledger_writer.validate_entry` runs on writes only and never loads the schema. Nothing validates the 2,197 existing entries.
- Reproduction (script in the session scratchpad, not committed): 2,862 errors = 1,525 + 1,312 + 25 over 8 files; `faction.yaml` clean. Run time about 2 s.
- `jsonschema` lives in the `dev` dependency group; every test job syncs default groups, so it is importable in `tools-a-e` and `arch-docs`.
- No test job in `.github/workflows/test.yml` is path-filtered (only `frontend` and the migration lanes are), so a ledger-only PR runs every test job.
- `codebase/health/__main__.py` already has `seed`/`check`/`tighten` commands to mirror; `tighten` there refuses to raise a ceiling.
- Test-scope gate maps `codebase/**` to `tests/codebase/` (root-move ticket), so the checker's tests belong there.
- The ledger is owned by the domains whose mechanics it records; this ticket adds a check, not content.
