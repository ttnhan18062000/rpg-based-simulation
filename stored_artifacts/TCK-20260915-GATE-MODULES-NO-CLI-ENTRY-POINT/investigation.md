# Investigation — TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT

Reproduced the defect first, per this ticket's own Implementation Notes: ran all 3 modules
directly (`python3 tools/parity_ledger_scan.py`, `python3 tools/registry_query.py`, `python3
tools/ticket_field_values.py tickets/done/<real-ticket>.md`) — all 3 print nothing and exit 0,
confirmed today, matching `grep -c "__main__\|argparse"` = 0 for each as the ticket states.

## Primary function(s) per module

- `tools/ticket_field_values.py` — one clear primary function, `check_ticket_field_values(ticket_path)`.
  Real PASS/FAIL semantics (matches the ticket's own AC framing exactly).
- `tools/parity_ledger_scan.py` — one clear primary function, `find_p0_intersection(files_changed,
  ledger_dir=...)`. Not literally PASS/FAIL, but a real binary outcome: empty result = safe to
  skip the Parity agent call (exit 0); any hit = not safe (exit 1, one line per hit).
- `tools/registry_query.py` — **two** real functions, confirmed by reading the file in full before
  assuming a single entry point (per the ticket's own explicit instruction not to assume one):
  `candidate_tags_from_text(*texts, root=None)` and `filter_registry(entries, layers=None,
  candidate_tags=None)`. Neither has a PASS/FAIL "check" outcome — both are pure queries. Exposed
  as two mutually exclusive CLI modes (`--text` vs `--layers`/`--tags`) rather than forcing one
  function to be "the" entry point.

## Make target decision

The ticket's own Assumptions/Open Questions flags this as open, but leans toward matching
`done_checker_static.py`'s own precedent (no target added for that fix). Followed that precedent:
no Makefile changes for this ticket, for consistency with the sibling fix it explicitly asks to
mirror.
