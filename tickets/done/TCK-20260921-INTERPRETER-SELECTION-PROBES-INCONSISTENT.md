---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT
phase: done
date: 2026-09-21
tags: [ai, process-improvement, performance]
---

# TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT

## Title
Interpreter selection is inconsistent across this repo's tooling — `Makefile` still selects by
existence alone (the exact weakness #233 fixed in the MCP launchers), and the search launcher's own
new probe roughly doubles cold-start time doing it

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Filed while scoping a follow-up batch after `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` (PR #233)
hardened `tools/start_search_mcp.sh`/`tools/start_headroom_mcp.sh` to probe real import capability
before selecting a candidate interpreter, instead of `[ -x "$py" ]` existence alone. Two follow-on
gaps found, both real, neither fixed here.

**(a) The Makefile's own interpreter-selection variables have the identical unfixed weakness.**
`PYTHON3` (`Makefile:35`) and `PYTHON_KNOWLEDGE` (`Makefile:42`) both select via `command -v "$$py"`
— existence/PATH-resolvability only, never whether the resolved interpreter can actually run what
the target needs. This is exactly the shape #233 fixed in the two shell launchers; it was never
applied to the Makefile's own variables. A future rename or a stale/incomplete venv would make any
`$(PYTHON3)`/`$(PYTHON_KNOWLEDGE)`-using `make` target fail loudly (or silently misbehave) instead
of falling through to a working candidate — the same failure class, just in `make` instead of
`bash`.

**(b) The search launcher's own new hardening has a real, measured performance cost.**
`tools/start_search_mcp.sh`'s probe (`"$py" -c "import sentence_transformers"`) does a FULL import —
which pulls in `torch` — purely to check availability, and then the `exec`'d server
(`search_mcp.py` → `knowledge_search.py`) imports the same module again in a fresh process, paying
the full cost twice. Measured directly, not assumed:

| What | Real time |
|---|---:|
| Probe alone (`import sentence_transformers`, `.venv-knowledge/bin/python3`) | 5.66s |
| `importlib.util.find_spec("sentence_transformers")` alone, same interpreter | 0.04s |
| Full current launcher, cold, one real query (`tools/start_search_mcp.sh --test`) | 10.60s |

The probe alone accounts for roughly half the total cold-start cost (5.66s of 10.60s). Replacing it
with `importlib.util.find_spec(...)` — which locates the module without executing its `__init__.py`
— would be expected to cut total cold-start time to roughly 5s (the probe's own ~5.66s replaced by
~0.04s), based on these measurements. Not implemented or further profiled here; a real before/after
timing of the actual replacement is still owed before it ships, since these numbers are for the
current code and the estimate, not a measurement of the changed code.

## Scope
When picked up:
- Decide whether the Makefile's `PYTHON3`/`PYTHON_KNOWLEDGE` should gain the same
  probe-before-select hardening #233 gave the shell launchers, or whether `make`'s own error surface
  (a failed command inside a recipe) is an acceptable difference from a shell script's silent
  fallthrough risk — this is a real design question, not assumed answered by "make it consistent."
- If hardening is chosen: probe via `command -v "$$py" >/dev/null 2>&1 && "$$py" -c "import X"` (or
  equivalent) for each candidate in the `for py in ...` discovery loop, falling through on failure,
  matching the shell launchers' own pattern.
- Replace `start_search_mcp.sh`'s `import sentence_transformers` probe with
  `importlib.util.find_spec("sentence_transformers")`, and MEASURE the real before/after cold-start
  delta on the changed code (not just the current code, as this ticket's own numbers are) before
  claiming a specific improvement figure.
- Weigh `find_spec`'s own weaker guarantee explicitly (see Assumptions) rather than treat it as a
  strict improvement with no tradeoff.

## Out of Scope
- Any change to `tools/start_headroom_mcp.sh`'s `import headroom` probe — that one is comparatively
  cheap (headroom-ai doesn't pull in torch), and not measured or flagged as a problem here.
- Any change to the actual selection ORDER of candidates in any of these tools, or which venvs are
  candidates — only the probe MECHANISM (existence vs. real-capability check; full-import vs.
  spec-lookup) is in scope.
- Implementing anything. This ticket is deferred, per the user's own defer-minor-effect rule — it
  rides along unbuilt until someone picks it up deliberately.

## Acceptance Criteria
- [x] A deliberate decision is recorded on whether `Makefile`'s `PYTHON3`/`PYTHON_KNOWLEDGE` get the
      same hardening as the shell launchers, with reasoning, not just "yes, be consistent." Decided
      yes, via `find_spec` (not a full import, since `:=` runs on every `make` invocation) — see
      `investigation.md` § Part (a).
- [x] If hardened: a planted stale/wrong-venv case demonstrates a `make` target falls through to a
      working candidate instead of failing on the wrong one. Demonstrated live (not statically) by
      `tests/tools/test_makefile_interpreter_selection.py`, extracting the real Makefile shell
      command and running it against planted broken/working candidates.
- [x] `start_search_mcp.sh`'s probe uses `importlib.util.find_spec` (or an equivalently non-importing
      check), with a real measured before/after cold-start timing recorded — not the estimate this
      ticket makes, a fresh measurement of the actual changed code. Measured: 10.899s before,
      6.176s/7.179s after (two runs) — a real ~35-45% cut, smaller than the pre-implementation ~5s
      estimate; the gap and why is recorded honestly in `investigation.md` and the script's own
      comment.
- [x] `find_spec`'s weaker guarantee (module locatable ≠ module actually importable without error) is
      explicitly weighed and the decision recorded, not silently accepted as strictly better. See
      `investigation.md` § weighed.

## Related Tickets
- `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` (done) — the PR #233 hardening this generalizes from.

## Related Docs
- None yet.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT/` (plan.md,
  investigation.md, test_plan.md).

## Related Code Areas
- `Makefile` (`PYTHON3` line 35, `PYTHON_KNOWLEDGE` line 42, and every target that consumes either)
- `tools/start_search_mcp.sh` (the `import sentence_transformers` probe)
- `tools/start_headroom_mcp.sh` (out of scope for the perf fix, in scope only if the Makefile
  hardening decision generalizes to it)

## Assumptions / Open Questions
- **`find_spec` is faster but a weaker guarantee than a real import.** It confirms the module's spec
  is locatable (its files exist, its finder resolves it) but does NOT execute `__init__.py` — a
  corrupted install, a missing native `.so` extension, or a version mismatch that only surfaces at
  import time would pass a `find_spec` check and still fail when the server actually imports it
  later. Whether that tradeoff is acceptable (probe cheaply, let the real import fail loudly if it
  ever does) or not (probe must be a true guarantee) is a real design call, not obvious either way.
- Whether hardening `make` targets the same way as the shell launchers is worth the complexity is
  itself open — `make`'s own failure mode (a recipe line fails, `make` reports the error) may already
  be "loud enough" compared to a shell script's silent-fallthrough risk that motivated the original
  hardening. Not decided here.
- The measured numbers above are for the CURRENT code on THIS machine at THIS moment (2026-09-21) —
  torch import cost varies by machine/cache-warmth; the numbers are directional evidence that the
  problem is real and worth ~2x, not a permanent SLA to hold any future implementation to exactly.

## Implementation Notes
See `stored_artifacts/TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT/investigation.md` for
the full decision record and measurements. Summary:
- `Makefile:PYTHON3`/`PYTHON_KNOWLEDGE` hardened to probe real capability (`pydantic` /
  `sentence_transformers`) via `importlib.util.find_spec`, not existence alone — decision recorded
  with reasoning (a `:=`-assigned variable's probe cost is paid on every `make` invocation, so
  `find_spec` was chosen over a full import even though the original shell-launcher pattern used a
  full import).
- `tools/start_search_mcp.sh`'s probe switched from `import sentence_transformers` to
  `importlib.util.find_spec('sentence_transformers')`. Real before/after measured, not estimated:
  10.899s → 6.176s/7.179s (two runs).
- `find_spec`'s weaker guarantee weighed explicitly and accepted, both in `investigation.md` and in
  the script's own updated comment.
- Pre-existing static guard test (`test_mcp_launcher_hardening.py`) updated for the new probe text
  shape; a new live-behavior test added for the Makefile fallthrough case.

## Test Summary
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_makefile_interpreter_selection.py \
  tests/tools/test_mcp_launcher_hardening.py \
  tests/tools/test_dashboard_makefile_targets.py \
  tests/tools/test_search_mcp.py \
  tests/tools/test_mcp_json_registration.py -q
# 46 passed
```
`graphify update .` run after the code/test changes — no topology changes detected.

## Files Changed
- `Makefile` — `PYTHON3`/`PYTHON_KNOWLEDGE` hardened with `find_spec`-based capability probes.
- `tools/start_search_mcp.sh` — probe switched from full import to `find_spec`.
- `tests/tools/test_makefile_interpreter_selection.py` (new) — live fallthrough regression test.
- `tests/tools/test_mcp_launcher_hardening.py` — updated for the new probe text shape.
- `docs/REGISTRY.yaml` — regenerated.

## Completion Summary
Both parts of the ticket's scope implemented. (a) Makefile's `PYTHON3`/`PYTHON_KNOWLEDGE` now probe
real capability via `find_spec`, matching the shell launchers' fallthrough resilience without
paying a full-import cost on every `make` invocation — the design tradeoff the ticket asked to be
decided explicitly, not assumed. Demonstrated live with a planted broken-then-working candidate
test. (b) `start_search_mcp.sh`'s probe switched to `find_spec`; real before/after cold-start timing
measured on the actual changed code (10.899s → 6.176s/7.179s), a genuine ~35-45% improvement,
smaller than the ticket's own pre-implementation estimate — recorded honestly rather than claiming
the original estimate held. `find_spec`'s weaker guarantee weighed and accepted in both places, with
the reasoning for why it's an acceptable tradeoff recorded in code comments, not just the ticket.
