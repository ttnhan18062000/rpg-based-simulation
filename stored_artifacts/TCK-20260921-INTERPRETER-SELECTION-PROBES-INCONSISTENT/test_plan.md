---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT
artifact_type: test_plan
---

# Test Plan — TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT

## New tests

`tests/tools/test_makefile_interpreter_selection.py` (new) — live behavior, not static text
matching. Extracts the real `$(shell ...)` command for `PYTHON3` and `PYTHON_KNOWLEDGE` out of the
actual `Makefile` text (regex, converts Make's `$$` back to `$`), substitutes a planted
exists-but-capability-fails candidate followed by a working one, and runs the extracted command via
`bash -c`. Three cases per variable (parametrized, 6 tests total):
- broken-then-working candidate list → selects the working one (the ticket's own AC2).
- broken candidate alone → resolves empty (sanity check that the fixture's "broken" shim really
  does fail on its own, not a false pass).
- both candidates broken → resolves empty (matches the pre-existing documented empty-on-failure
  behavior, not a new failure mode).

## Updated tests

`tests/tools/test_mcp_launcher_hardening.py` — two assertions updated from matching the old
`import sentence_transformers` literal probe text to the new `find_spec('sentence_transformers')`
shape; one new test added asserting the old full-import invocation string is genuinely gone (not
just that the new one is present, which alone wouldn't catch a leftover duplicate probe).

## Scoped run

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_makefile_interpreter_selection.py \
  tests/tools/test_mcp_launcher_hardening.py \
  tests/tools/test_dashboard_makefile_targets.py \
  tests/tools/test_search_mcp.py \
  tests/tools/test_mcp_json_registration.py -q
```
Result: 46 passed.

## Manual verification (not pytest, but load-bearing)

- `make -p 2>/dev/null | grep '^PYTHON3 '` / `'^PYTHON_KNOWLEDGE '` — both still resolve to the
  real, capable venvs on this machine after the change (not broken by the hardening).
- `time make -n dev` — ~0.047s, confirming `find_spec`'s negligible per-invocation cost.
- `tools/start_search_mcp.sh --test` with a real query, before and after the probe change — real
  results returned in both cases (functional correctness preserved), with the timing difference
  recorded in `investigation.md`.
- `graphify update .` run after the code/test changes — no topology changes detected.
