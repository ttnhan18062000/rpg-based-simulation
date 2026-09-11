---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE
artifact_type: investigation
tags: [testing, architecture]
---

# Investigation — TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE

Verified against `origin/main` on 2026-09-11. `search_docs` has no index in this worktree; duplicate-work
detection used the documented `docs/REGISTRY.yaml` fallback.

## 1. Premise confirmed, scope wider than the ticket

`tests/architecture/test_phase18_import_boundaries.py` has **three** pinned-exception structures. Two
are line-keyed; the ticket names only one.

| Structure | Line | Keyed by | Entries | Line-keyed? |
|---|---|---|---|---|
| `_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS` | 115 | `(module, names)` | 4 | **No** — already content-keyed |
| `_DOMAINS_OBSERVABILITY_PINNED` | 176 | `(rel_path, lineno)` | 2 | Yes — the ticket's subject |
| `_SYSTEMS_ENGINE_PINNED` | 217 | `(rel_path, lineno)` | 13 | Yes — **not in the ticket** |

Only two test functions build `key = (rel_path, node.lineno)` — lines 197 and 271. `_SYSTEMS_ENGINE_PINNED`
(13 entries across 5 files: 9 in `intelligence.py`, 1 each in `detour.py`, `redirection.py`,
`market.py`, `routine.py`) has already drifted in production:
`TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT`. It has 13 entries against the 2 in the
dict the ticket targets.

**Survey result for the ticket's Out of Scope item** ("any other line-keyed pinning mechanism... not
surveyed"): searched every `tests/**/*.py` for `("src/...py", <int>)` tuples. Only this one file contains
them. No other line-keyed mechanism exists in the suite.

## 2. The fix already exists in the same file

`_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS` is matched by pure membership at line 155:
`(module, _names_as_written(node)) in _OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS`. No line number. That is the
exact scheme the ticket proposes, already in production use beside the brittle dicts.

The line-keyed dicts are closer to it than they look. Their *values* already hold `(module, names)`, and
the test already asserts the value matches (line 205). Dropping the line number from the key and folding
the value into it reuses data that is already present.

**One difference that must not be copied.** The precedent omits the file path because its loop is
restricted to three specific files in `src/observability/`. The domains→observability loop walks all of
`src/domains/`, and the systems→engine loop all of `src/systems/`. Keyed without the file, a pin for
`narrative_ledger.py` would silently authorize the same import in any other domain file. The key must be
`(rel_path, module, names)`.

## 3. The D14 coupling has already broken

The ticket asks that expanding pins still require updating `docs/audits/D14_coupling_depth.md` alongside
the test. That discipline has already failed silently:

| Import | Actual line | Test pin | D14 says |
|---|---|---|---|
| `narrative_ledger.py` → `SimulationEvent` | 71 | 71 | 71 |
| `orchestrator.py` → `SimulationEvent` | **487** | **487** | **418** |

The test stays correct because line drift breaks CI and forces a re-pin. The doc has no equivalent
forcing function, so it drifted without anyone noticing. D14 carries 11 line-number citations in total.

Line-keying therefore does not only make the gate fragile — it makes the gate and its documentation
diverge, because only one of the two is enforced.

## 4. Constraints to preserve

- **`TYPE_CHECKING` imports stay exempt.** Both files also import `EventRecorder` from
  `src.observability.event_recorder` (lines 23 and 26), unpinned. They are inside `TYPE_CHECKING` blocks and
  correctly skipped via `_type_checking_lines()`. The rewrite must keep that skip.
- **The negative path.** A genuinely new, unpinned boundary import must still fail.
- **Multiplicity — a real case exists.** `intelligence.py` lines 832 and 904 both import
  `SystemCadence as DefaultCadence, should_run` from `src.engine.cadence` — identical
  `(rel_path, module, names)`. A plain set would collapse 13 pins into 12 keys, and a third identical
  import anywhere in that file would then pass unnoticed. The key must carry an expected count (§6).

## 5. Why this is more than P3

The ticket already explains it: the correct repair (re-pin to the new line) and the prohibited one
(weaken the exception) are one-line edits to the same dict and look alike in a diff. §3 adds concrete
evidence — the coupled documentation has already drifted while every reviewer looked at the test diff
only. The reachability findings doc's Finding 8 records two occurrences; this file has at least three
(two in `_DOMAINS_OBSERVABILITY_PINNED`, one in `_SYSTEMS_ENGINE_PINNED`).

## 6. Correction (after Review NEEDS_CHANGES, 2026-09-11)

The first version of this investigation was wrong on three points. Review caught two of them, and
re-checking caught the third:

1. **`_SYSTEMS_ENGINE_PINNED` has 13 entries, not 10.** The count missed `redirection.py:25`,
   `market.py:50`, and `routine.py:180`. The survey of other line-keyed structures stands: these are
   extra entries in a dict that was already in scope, not a new mechanism.
2. **D14's systems→engine table is a pinned-entry citation table**, mapping one-to-one to the dict
   (`D14_coupling_depth.md`, "Layer: `src/systems/`" section). It is not free-standing documentation.
   Both D14 sections also describe the pins as "a `(file, lineno)`-exact grandfather list", which
   becomes false once keys are content-based.
3. **The "no duplicate imports" claim was false** — see the §4 multiplicity entry
   (`intelligence.py:832` and `:904`).

Lesson, the same as the parity audit's: count and compare against the source structure itself; don't
rely on a partial read.

