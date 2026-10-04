---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT
phase: open
date: 2026-10-04
tags: [engine, social, root-cause, observability]
---

# TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT

## Title

Two genuine `F821` undefined names in `src/`: `kernel.py`'s missing `import json` silently discards the
provenance manifest on every lab run, and `party.py`'s missing `StrategicUpdate` import is a latent
`NameError` in a dormant method

## Status

INPROGRESS

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

**Reported by `codebase-planner` via the PR #322 handoff** (`docs/plans/codebase_health/handoffs/handoff_to_rpg.md`
§2), which asked the RPG side to decide whether to ticket them. **Both confirmed by direct reading; the
handoff's facts hold.** But it presented them as a matched pair, and **they are not** — one is live and
silent, the other is unreachable. That asymmetry is the whole reason this ticket splits their priority.

`ruff F821` reports 111 undefined names in `src/`; 109 are inside quoted annotations and harmless at
runtime. These two are real.

### Bug 1 — `src/engine/kernel.py:157`. LIVE, and silent. This is the P1.

```python
prov_manifest_data = None
if provenance_manifest_path and os.path.exists(provenance_manifest_path):
    try:
        with open(provenance_manifest_path, "r", encoding="utf-8") as f:
            prov_manifest_data = json.load(f)
    except Exception:
        pass
```

`json` has **no module-level import** in `kernel.py` — only function-local imports at `:894` and `:979`,
neither in scope here. So `json.load` raises `NameError`, and `except Exception: pass` **swallows it**.

**It is reached, which the handoff did not establish:** `src/lab/orchestrator.py:184` builds
`provenance_manifest_path = world_dir / "resolved" / "provenance_manifest.json"` and passes it through
(`kernel.py:68` accepts it, `:186` forwards it). **So on every lab-orchestrated run the provenance
manifest is silently never loaded**, and `prov_manifest_data` stays `None` with no error, no log line, and
no failing test.

**Why this is worse than a crash:** a `NameError` that propagated would have been found years ago. The
bare `except Exception: pass` converts a hard failure into a permanent, invisible absence of provenance —
exactly the "an artifact nothing validates, so an error in it stays invisible" shape that
`TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION` and
`TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION` both have.

### Bug 2 — `src/systems/social_systems/party.py:143`. Real, but DORMANT. Lower priority.

```python
@staticmethod
def issue_party_command(...) -> StrategicUpdate:
    from src.core.strategic import DirectiveState, DirectivePriority   # :132 — StrategicUpdate NOT imported
    ...
    return StrategicUpdate(directives_add_or_update=[directive])        # :143 — NameError
```

`StrategicUpdate` appears only at `:128` (a return annotation, deferred by `from __future__ import
annotations`, so harmless) and `:143` (a **runtime call**). It is imported nowhere — not at module level,
not in the `if TYPE_CHECKING:` block at `:6-7` (which imports only `EntityState`, `AuthoritativeState`),
and not in the function-local import at `:132`, which pulls `DirectiveState` and `DirectivePriority` from
the very module `StrategicUpdate` lives in.

**But `PartyCoordinationSystem.issue_party_command` has ZERO callers** — `grep -rn "issue_party_command"
src/ tests/` returns only its own definition. **So the `NameError` cannot fire today.** The handoff's
"raises `NameError` whenever that path runs" is accurate but conditional on a path nothing invokes.

This makes it the same class as `TCK-20261004-POSITION-SWAP-CONTRACT-NEVER-CONSTRUCTED`: a dormant method
carrying a latent defect, invisible because nothing executes it.

## Scope

- **Bug 1:** add a module-level `import json` to `src/engine/kernel.py` and remove the two now-redundant
  function-local imports at `:894`/`:979` only if they are genuinely redundant after the change.
- **Bug 1, the part that matters more than the import:** decide whether `except Exception: pass` is
  acceptable there at all. A bare swallow around provenance loading is what made a one-word bug
  permanent. At minimum it should log; consider narrowing to the exceptions actually expected
  (`OSError`, `json.JSONDecodeError`).
- **Bug 1, assess the blast radius:** establish what consumed `prov_manifest_data` and what has been
  silently degraded by it always being `None`. **Any prior measurement that believed it had provenance
  metadata from a lab run did not.** This is the real cost and it is unmeasured.
- **Bug 2:** add `StrategicUpdate` to the existing function-local import at `:132`. One word.
- **Bug 2, the real question:** `issue_party_command` is dormant. Decide whether party commands are an
  unfinished feature (wire a caller) or dead code (remove the method). Do **not** fix the import and
  leave an uncalled method — that preserves the dormancy while removing the evidence of it.
- A regression test for Bug 1 that fails on today's code: a lab-style run with a real
  `provenance_manifest.json` must end with `prov_manifest_data` populated.

## Out of Scope

- The other **109** `F821` findings. They are inside quoted annotations and harmless at runtime; the
  handoff verified that and this ticket accepts it rather than re-deriving it.
- Shrinking the mypy baseline generally. Both of these are already in it, so neither blocks any PR —
  fixing them shrinks it as a side effect, which is not the motivation.
- The `src/` package-structure decisions in the same handoff's §3. Separate concern, and gated on the
  owner reopening `src/` (M7).

## Acceptance Criteria

1. `src/engine/kernel.py` imports `json` at module level, and a test proves the provenance manifest is
   actually loaded on a lab-style run — **failing on today's code**. Assert the loaded value is
   non-`None` *and* has expected content; asserting "no exception raised" would pass today.
2. The `except Exception: pass` around provenance loading either logs or is narrowed, with the choice
   recorded. A silent swallow must not survive this ticket unexamined.
3. A written assessment of what `prov_manifest_data` feeds and what has been degraded by its always
   being `None`. "Nothing downstream used it" is an acceptable finding **if measured**, not assumed.
4. `src/systems/social_systems/party.py:143` can no longer raise `NameError`, **and** a recorded decision
   on whether `issue_party_command` is wired up or removed. Not just the import.
5. `ruff` reports no `F821` for either site, and the mypy baseline is reduced rather than regenerated
   wholesale.

## Related Tickets

- `TCK-20261004-POSITION-SWAP-CONTRACT-NEVER-CONSTRUCTED` — same dormancy class as Bug 2. Read together;
  if the party-command decision is "dead code", these may share one removal.
- `TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`,
  `TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION` — same root shape as
  Bug 1: an artifact nothing validated, so an error in it stayed invisible. Three instances in one day.
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (done) — made `resolved/provenance_manifest.json`
  an authoritative projection, which is the file Bug 1 fails to read.

## Related Docs

- `docs/plans/codebase_health/handoffs/handoff_to_rpg.md` §2 — the report, and the source of record
- `docs/architecture/world_repository_layout.md` — the `resolved/` projection Bug 1 cannot read
- `docs/guidelines/python_code_standard.md` — the standard the gates flip to blocking on 2026-10-18

## Related Stored Artifacts

None. The evidence is in `codebase-planner`'s own handoff and re-verified in this ticket.

## Related Code Areas

- `src/engine/kernel.py:157` (the call), `:68`/`:186` (the parameter), `:894`/`:979` (the function-local
  imports)
- `src/lab/orchestrator.py:184` — the live caller that makes Bug 1 reachable
- `src/systems/social_systems/party.py:6-7` (`TYPE_CHECKING`), `:128` (annotation), `:132` (the
  function-local import that omits it), `:143` (the call)
- `src/core/updates.py:515` — where `StrategicUpdate` actually lives (corrected at close: this line originally named `src/core/strategic.py`, which exists but does not define it; the wrong path survived because the module was matched by name, not traced)

## Assumptions / Open Questions

- **Unverified: what consumes `prov_manifest_data`.** AC-3 exists because this is the unmeasured cost. I
  did not trace it.
- **Unverified: whether any other `except Exception: pass` in `kernel.py` hides a comparable bug.** This
  one was found by `ruff`, not by auditing the swallows. A sweep of bare swallows around file I/O would be
  a different and possibly larger finding.
- Unverified: whether `issue_party_command` was ever called historically (git history not checked), which
  would distinguish "never wired" from "caller removed".
- The handoff states both bugs are already in the mypy baseline and so block no PR. Accepted as reported,
  not independently checked.

## Implementation Notes

- Bug 1 (LIVE, silent): module-level `import json` in `src/engine/kernel.py`; the two function-local imports removed; `except Exception: pass` narrowed to `(OSError, ValueError)` with a `logger.warning` (a missing or corrupt manifest degrades fingerprints but must not abort a run, so it is logged, not raised).
- Blast radius, measured: `prov_manifest_data` only feeds `RunManifest.catalog_fingerprint` and `module_fingerprints` as fallbacks; `src/lab/orchestrator.py` passes neither, so every lab-orchestrated run recorded the process-wide catalog fingerprint and `module_fingerprints=None` instead of the resolve-time values. Anything that read those from a lab run's manifest did not have provenance.
- Bug 2 (DORMANT, zero callers): `StrategicUpdate` imported from `src/core/updates.py`. The ticket and the handoff named `src/core/strategic.py`, which does not define it; a first edit using that path failed the new test.
- Decision for `issue_party_command`: first kept and tested while escalated; the rule owner then ruled wiring out permanently and the Bible wrong (`TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS`), and the planner ruled removal (`TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD`). The method, the `StrategicUpdate` import added for it, and its test were removed, so Bug 2's `NameError` is gone because the method is gone. The import fix was made first and verified by a test that failed before it (the `StrategicUpdate` module path was learned that way), then superseded. Cross-lane exception recorded in `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md` section 5.

## Test Summary

- `tests/unit/engine/test_kernel_provenance_manifest_load.py` (2): both fail on the old code, pass on the fix. A third test, for `issue_party_command`, failed on the old code too but was deleted with the method (`TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD`).
- AC-5: `ruff` is not installed in this environment, so F821 was not run; the NameErrors are covered by tests instead. The mypy baseline was not regenerated or reduced here (not measured).
- Scoped run on the final tree: 1693 passed, 0 failed.

## Files Changed

`src/engine/kernel.py`; `tests/unit/engine/test_kernel_provenance_manifest_load.py`. (`src/systems/social_systems/party.py` and its test were touched and then removed under `TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD`; net diff for them from this ticket is nil.)

## Completion Summary

_(not started)_
