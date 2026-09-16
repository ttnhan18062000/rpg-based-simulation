# Plan — TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT

1. Reproduce the silent no-op for all 3 modules (done — investigation.md).
2. Add `main(argv=None) -> int` + `if __name__ == "__main__": sys.exit(main())` to each,
   mirroring `tools/gate_checks/done_checker_static.py`'s own CLI shape exactly (argparse,
   readable per-line output, non-zero exit on failure/error, zero only on a real pass or a
   successful query).
3. `ticket_field_values.py`: positional `ticket_path` argument, calls
   `check_ticket_field_values()`, exits 1 on any FAIL.
4. `parity_ledger_scan.py`: positional `files_changed` (nargs="+") plus `--ledger-dir`, calls
   `find_p0_intersection()`, exits 1 if any hit found (not safe to skip Parity).
5. `registry_query.py`: two mutually exclusive modes (`--text` → `candidate_tags_from_text`;
   `--layers`/`--tags` → `filter_registry` against the real `docs/REGISTRY.yaml`), since neither
   function is a clear single "primary" one. Exits 1 only if no mode selected or the registry file
   is missing — no PASS/FAIL check semantics for a pure query tool.
6. Add CLI tests to each module's existing test file (not a new file — small, additive changes to
   an already-tested module): presence-of-output assertions (not just return codes), exit-code
   checks on both the pass and fail paths, `--help` producing usage text, and a pin that the
   existing function-level import path still works unchanged.
7. No Makefile target added, matching `done_checker_static.py`'s own precedent (the ticket's own
   Assumptions/Open Questions leans this way).
8. Run the 3 affected test files, then the full `tests/tools/` suite for regression.
