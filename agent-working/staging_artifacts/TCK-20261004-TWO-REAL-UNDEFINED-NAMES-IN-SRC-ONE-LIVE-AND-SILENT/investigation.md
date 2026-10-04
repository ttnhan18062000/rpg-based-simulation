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
- Decision for `issue_party_command`: kept while escalated, then removed under `TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD` after the rule owner ruled wiring out permanently and the Bible wrong (`TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS`).
- A first test version used `chdir(tmp_path)`; `ContentWarmupService` then loaded an empty catalog into process-wide singletons and broke later legality tests. Fixed by staying in the repo cwd and removing only the test's own run directories.

## Docs Requiring Update
- `docs/mechanics/07_social_political_dynamics.md` — corrected in place under `TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS` (rule-owner ruling); not part of this ticket's own diff.

## Risks and Open Questions
- Historical lab runs carry the wrong fingerprints; any measurement that relied on their provenance metadata did not have it.
