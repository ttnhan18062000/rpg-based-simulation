---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT
artifact_type: plan
---

# Plan — TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT

## Steps

1. Decide and record whether `Makefile`'s `PYTHON3`/`PYTHON_KNOWLEDGE` get the same probe
   hardening as the shell launchers — see `investigation.md`. Decision: yes, via
   `importlib.util.find_spec`.
2. Harden `Makefile:PYTHON3` (probe `pydantic`) and `Makefile:PYTHON_KNOWLEDGE` (probe
   `sentence_transformers`), both via `find_spec`, matching the shell launchers' fallthrough shape.
3. Add a live regression test proving the fallthrough actually happens for a planted
   exists-but-fails-capability candidate, for both variables, extracting the real shell command
   from the Makefile (not a hand-copied reimplementation).
4. Replace `start_search_mcp.sh`'s `import sentence_transformers` probe with
   `importlib.util.find_spec("sentence_transformers")`.
5. Measure real before/after cold-start timing on the actual changed code.
6. Weigh `find_spec`'s weaker guarantee explicitly, record the decision.
7. Update the pre-existing static guard test (`test_mcp_launcher_hardening.py`) that asserted the
   old full-import probe text, so it doesn't false-fail against the new probe shape.

## Acceptance criteria map

| Ticket AC | How this plan satisfies it |
|---|---|
| A deliberate decision recorded on Makefile hardening, with reasoning | `investigation.md` § Part (a) |
| Planted stale/wrong-venv case demonstrates fallthrough | `tests/tools/test_makefile_interpreter_selection.py` — live, not static |
| `start_search_mcp.sh` uses `find_spec`, real measured before/after timing | `investigation.md` § Part (b), applied in `tools/start_search_mcp.sh`'s own comment |
| `find_spec`'s weaker guarantee explicitly weighed | `investigation.md` § weighed, and in the script's own comment |

## Out of scope (per ticket)
- `tools/start_headroom_mcp.sh` — untouched, not measured/flagged as a problem.
- Candidate selection order or which venvs are candidates — unchanged in all three places.
- `Makefile:PYTHON` (line ~480) and the one-off `agent-monitoring-index` inline selector — not
  named in this ticket's own Scope/Related Code Areas; left untouched.
