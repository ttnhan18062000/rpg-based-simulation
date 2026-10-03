---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT
artifact_type: investigation
---

# Investigation — TCK-20260921-INTERPRETER-SELECTION-PROBES-INCONSISTENT

## Part (a): Makefile PYTHON3/PYTHON_KNOWLEDGE hardening decision

The ticket's own scope frames this as a real design question ("`make`'s own error surface... an
acceptable difference?"), not a foregone "be consistent." Read both variables' real context:

- Both are `:=` (immediate) assignments — the `$(shell for py in ...; do ...; done)` runs once, at
  Makefile-parse time, on **every** `make` invocation (even `make help`), not lazily on first use
  of the target.
- Without a capability probe, a single candidate is chosen by existence alone (`command -v`), and
  every `$(PYTHON3)`/`$(PYTHON_KNOWLEDGE)`-consuming target then fails against that one candidate
  with no fallthrough — the identical failure shape PR #233 fixed in the shell launchers (a real,
  observed breakage there: a rename made `start_search_mcp.sh` silently pick a
  `sentence_transformers`-less `.venv`).

**Decision: harden both, using `importlib.util.find_spec` rather than a full import.** The shell
launchers' original probe (PR #233) did a full `import`, acceptable there because the probe cost
is paid only when that specific script actually runs. It is *not* acceptable for a `:=`-assigned
Makefile variable, because the probe cost would tax every `make` invocation regardless of target —
confirmed directly: `sentence_transformers` alone costs ~5.66s to fully import (this same ticket's
own part (b) measurement). `find_spec` avoids executing `__init__.py`, keeping the added cost
negligible (`time make -n dev` before/after: both ~0.05s).

## Part (b): start_search_mcp.sh probe cost

Measured directly on this machine, `tools/start_search_mcp.sh --test`, one real query, cold:

| Run | Real time |
|---|---:|
| Before (full `import sentence_transformers` probe) | 10.899s |
| After (`importlib.util.find_spec`), run 1 | 6.176s |
| After (`importlib.util.find_spec`), run 2 | 7.179s |

A real ~35-45% cut, smaller than the ticket's own pre-implementation ~5s estimate. The estimate
assumed only the probe's own cost (~5.66s) would drop to near-zero; it did not account for the
exec'd server's own single remaining `sentence_transformers` import (now measured at ~6-7s here,
never independently measured before this ticket) still being the dominant remaining cost. The
improvement is real and substantial, just not as large as the pre-measurement estimate implied —
recorded honestly per the ticket's own "measure the actual changed code, not the estimate" AC.

## `find_spec`'s weaker guarantee, weighed

`find_spec` confirms the module's spec is locatable (files exist, finder resolves it); it does
**not** execute `__init__.py`, so a corrupted install or missing native `.so` extension would pass
the probe and only fail when the exec'd server (or, for the Makefile variables, the actual `make`
target) imports it for real. Decision: accept this. The failure still surfaces immediately and
loudly (an ImportError at the point of real use), not silently or as a hang — the probe's actual
job (catching the wrong-venv-silently-selected case PR #233 fixed) is unaffected, since a
wrong-venv candidate's spec genuinely isn't locatable at all (the package was never installed
there), which is exactly what `find_spec` does detect.

## Related
- `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` (PR #233) — origin of the shell-launcher probe pattern.
