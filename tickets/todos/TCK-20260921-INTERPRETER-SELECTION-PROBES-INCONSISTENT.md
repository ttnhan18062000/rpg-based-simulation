---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT
phase: open
date: 2026-09-21
tags: [ai, process-improvement, performance]
---

# TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT

## Title
Interpreter selection is inconsistent across this repo's tooling — `Makefile` still selects by
existence alone (the exact weakness #233 fixed in the MCP launchers), and the search launcher's own
new probe roughly doubles cold-start time doing it

## Status
OPEN

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
- [ ] A deliberate decision is recorded on whether `Makefile`'s `PYTHON3`/`PYTHON_KNOWLEDGE` get the
      same hardening as the shell launchers, with reasoning, not just "yes, be consistent."
- [ ] If hardened: a planted stale/wrong-venv case demonstrates a `make` target falls through to a
      working candidate instead of failing on the wrong one.
- [ ] `start_search_mcp.sh`'s probe uses `importlib.util.find_spec` (or an equivalently non-importing
      check), with a real measured before/after cold-start timing recorded — not the estimate this
      ticket makes, a fresh measurement of the actual changed code.
- [ ] `find_spec`'s weaker guarantee (module locatable ≠ module actually importable without error) is
      explicitly weighed and the decision recorded, not silently accepted as strictly better.

## Related Tickets
- `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` (done) — the PR #233 hardening this generalizes from.

## Related Docs
- None yet.

## Related Stored Artifacts
- None yet.

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
Not implemented. Measure the real before/after delta on the actual changed code before claiming a
number in any future closure of this ticket — the numbers here are for the CURRENT (unfixed) code,
establishing that the problem is real, not a benchmark of the fix.

## Test Summary
_Not yet — deferred._

## Files Changed
_None — filed, not implemented._

## Completion Summary
_Open. Filed 2026-09-21 with real measured evidence for the performance claim (probe alone: 5.66s;
find_spec alone: 0.04s; full launcher: 10.60s) rather than an assumed number, per the user's
defer-minor-effect rule: record now with evidence, fix later when someone has a reason to
prioritize it._
