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

# Investigation — TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT

## Findings
- Bug 1 is LIVE and silent: `src/lab/orchestrator.py:184` builds the provenance path and passes it to `Kernel`; `json.load` raised NameError which `except Exception: pass` swallowed.
- Blast radius, measured: `prov_manifest_data` feeds only the `catalog_fingerprint` and `module_fingerprints` fallbacks of the `RunManifest`, and the orchestrator passes neither explicitly. So every lab-orchestrated run recorded the process-wide catalog fingerprint and `module_fingerprints=None` rather than the resolve-time values. On the old code the test saw `ecc8ccad...` where the provenance file said `cat-fp-from-provenance`.
- Bug 2 is DORMANT: `issue_party_command` has zero callers. `StrategicUpdate` lives in `src/core/updates.py` (the ticket and handoff said `src/core/strategic.py`; importing it there fails).
- Decision for `issue_party_command`: kept, now tested, dormancy escalated to the planner. `docs/mechanics/07_social_political_dynamics.md` documents it as existing behavior (removal breaks doc-code parity) and wiring a caller is Lane A feature work.
- A first test version used `chdir(tmp_path)`; `ContentWarmupService` then loaded an empty catalog into process-wide singletons and broke later legality tests. Fixed by staying in the repo cwd and removing only the test's own run directories.

## Docs Requiring Update
- None. The Mechanics Bible already describes `issue_party_command()` as behavior; this ticket makes the code match it.

## Risks and Open Questions
- Historical lab runs carry the wrong fingerprints; any measurement that relied on their provenance metadata did not have it.
