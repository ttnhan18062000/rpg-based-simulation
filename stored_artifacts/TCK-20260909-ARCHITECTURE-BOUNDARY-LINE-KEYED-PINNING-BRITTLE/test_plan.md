---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE
artifact_type: test_plan
tags: [testing, architecture]
---

# Test Plan — TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE

## The ticket's core acceptance criterion — line-shift survival

For **each** of the two converted dicts: take a pinned file, insert blank or comment lines above the pinned
import in a temporary copy, run the boundary check against it, and confirm the pin still matches. Run it
against a `tmp_path` copy of the tree — never modify `src/` to prove this.

Without this test the change is unverified: the current tests pass today because nothing has shifted yet.

## Negative paths (must still fail)

- A brand-new `src.observability` import in a domain file with no pin.
- A pinned file whose import changes to different names (content change is detected, not waved through).
- **Cross-file:** a pinned `(module, names)` copied verbatim into a *different* domain file is **not**
  authorized. This is the test that proves `rel_path` belongs in the key; drop it and the design regresses to
  the file-agnostic precedent.

## Counts (multiplicity)

- A third copy of the `intelligence.py` `SystemCadence as DefaultCadence, should_run` import (pinned at
  count 2) **fails**.
- Removing one of the two existing copies **fails** as a stale pin, so the count must be lowered
  deliberately.
- Every other pinned key at count 1: a second identical copy **fails**.

## Preserved behavior

- `TYPE_CHECKING` imports (`EventRecorder` in both campaign files) are still skipped.
- Every currently-pinned import in both dicts still passes after conversion — guards against a typo silently
  unpinning an entry.

## Regression

```
pytest tests/architecture/ -q
```

Full directory, not the single file: other architecture tests share `_iter_py_files`/`_parse` helpers.

## Doc check

`docs/audits/D14_coupling_depth.md` no longer contains `orchestrator.py:418`. Neither pinned-entry section
(domains → observability, systems → engine) cites line numbers for pinned imports. Neither still
describes a "`(file, lineno)`-exact" list. The systems → engine total (13) equals the sum of the pinned
counts.
