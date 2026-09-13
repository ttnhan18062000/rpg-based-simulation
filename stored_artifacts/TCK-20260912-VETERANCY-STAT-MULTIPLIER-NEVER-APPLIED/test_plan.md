# Test Plan — TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED

This is a documentation-only disposition — no code changed, so no new automated tests. The real
verification is the investigation's own evidence trail:

## Real evidence (see investigation.md for full detail)
- Fresh grep re-confirmation: `get_stat_multiplier` has zero callers anywhere in `src/`/`tests/`.
- Fresh grep re-confirmation: `StatsProxy` (PROG-014's named mechanism) has zero presence in `src/`.
- Direct file check: `tests/unit/progression/test_veterancy.py` (PROG-086's citation) does not
  exist; `tests/unit/progression/test_leveling_veterancy.py` does, and does not test
  `get_stat_multiplier()`.
- Direct file check: `src/engine/apply.py:454` (PROG-086's citation) is unrelated carryforward
  code, not veterancy.
- Direct grep: `docs/mechanics/*.md` has zero mentions of "veterancy."

## Regression scope
None — `src/` is untouched. `docs/parity_ledger/progression.yaml`'s write went through
`tools/parity_ledger_writer.py`'s own `validate_entry()` (schema-validating), confirmed passing
(the write call succeeded, which only happens after validation).

## Results
- `python3 tools/validate_frontmatter.py` — passed for this ticket and the new sweep ticket.
- Parity ledger write: `write_entry()` returned `status: ok` for `PROG-014`, ledger rebuild
  succeeded (2187 entries, 9 shards).
