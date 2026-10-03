---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP
artifact_type: investigation
tags: [ai, documentation]
---

# Investigation — TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP

## Origin
User exploratory session on the parity ledger's overall health, using the existing
`tools/parity_index.py` SQLite-backed query tooling (`build`/`entry`/`impact`/`health`/
`check-staleness`) rather than raw YAML reads, per the user's own note that this tooling exists
specifically to make the ledger query-able instead of requiring pure-text read/write. Explicitly
scoped as a **high-level overview**, not a single-record fixation — every number below is a
population-level count from the SQLite index, not an anecdote.

## Headline: the ledger is healthy overall

2,047 entries across 9 subsystem shards (`docs/parity_ledger/*.yaml`). **98.8% verified or
legacy_verified** (1,796 + 227). Only 24 entries aren't green: 13 `unsupported`, 7 `divergent`, 4
`missing`. No duplicate IDs across shards (checked directly). Of the 17 P0 entries among those 24,
15 are already correctly, honestly documented — 11 are RabbitMQ/Kafka broker-fallback
requirements marked `unsupported` with a `divergence_note` explicitly citing
`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` (this session's own broker-removal work), and 2
(`COMB-133`/`COMB-134`) are intentionally-stubbed future-phase placeholders. This is not a system
in trouble — the four items below are real but each individually small.

## Four concrete findings, each independently actionable

### 1. Two malformed entries (isolated anomaly, not a pattern)
`TOWN-040`/`TOWN-041` (`docs/parity_ledger/town_resource.yaml`) are the **only 2 of 2,047 entries**
(verified via a full-table SQL scan for "every evidence field NULL") with every evidence field
empty. Their `text` fields (`` `test_rng`: Rng. ``, `` `test_entity`: Entity. ``) look like a
fixture-name leak, not real requirement descriptions — contrast with the ledger's real, correct
`` `test_name`: description `` convention used legitimately by hundreds of other entries (e.g.
`COMB-014` through `COMB-027`, all populated with real evidence). **Correction to an earlier,
narrower read this session**: this convention itself is fine and widespread; only these 2 specific
rows are degenerate.

### 2. `absent_file` health findings (173) — likely dominated by checker imprecision, not real drift, except for one real sub-category
The `entry_health` table flags 173 `code_refs`/`test_refs`/`constraint_refs` citing paths that
don't exist on disk. Breakdown: **120 `test_refs`, 51 `code_refs`, 2 `constraint_refs`**. Two
distinct causes found by sampling, not by exhaustively checking all 173:
- **~29 are frontend path false positives**: the checker only resolves paths against the repo
  root, but real frontend code lives under `dashboard-frontend/src/...`, not bare `src/...`
  (confirmed: `dashboard-frontend/src/App.tsx` exists; the ledger cites it as `src/App.tsx`).
- **Some are prose-mention false positives, not live citations**: sampled `INFRA-211` cites
  `src/domains/adventure/phase.py` — genuinely deleted — but only inside a sentence explicitly
  narrating that the file "no longer exists, file deleted" as historical context, not as a current
  evidence pointer. The `_populate_entry_health()` path-extraction doesn't distinguish narrative
  mentions from live citations.
- **The 120 `test_refs` bucket is the one most likely to contain genuine, current drift**: unlike
  free-text `code_refs` prose, `test_refs` come from the importer's structured reference parser
  (`_REF_TABLES`), so a hit there is more likely a real "this test path was true when the entry
  was written, the test has since moved" case — directly plausible given how much test-file
  relocation has happened in this exact session (`TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`
  alone touches 61 files' worth of paths, still in flight as of this investigation).
- **Not resolved here**: which specific entries among the 173 are real vs. false positives needs
  per-item triage, explicitly left to the implementer (see Out of Scope) rather than done
  exhaustively in this investigation, per instruction not to fixate on individual records.

### 3. `legacy_unstructured` (1,552 of 2,047 — 76%) — a real automation gap, not a defect
Entries whose `v2_evidence`/`legacy_evidence` prose exists but couldn't be parsed into a
structured `code_refs`/`test_refs` row. These entries work fine for human reading but can't
participate in the `impact` (blast-radius) query the SQLite indexing project was built to enable
— the exact use case `tools/parity_index.py`'s own docstring cites as its Phase-2 purpose.
Concentrated in the oldest subsystems: `substrate.yaml` (360), `combat_movement.yaml` (275),
`social_narrative.yaml` (213). This is large and would be a substantial, separate modernization
effort if pursued — flagged as out of scope for this ticket (see below), not silently dropped.

### 4. `docs/logic_checklist_exhaustive.md` — orphaned predecessor of the parity ledger itself
Confirmed via `git log` + cross-reference, not assumption: this 3,197-line markdown checklist is
the direct historical predecessor of today's `docs/parity_ledger/*.yaml` system. Its own already-
archived design spec, `docs/archive/specs/2026-05-03-checklist-governance-design.md`, describes
migrating this exact file's legacy items into a `DOMAIN-NNN` stable-ID scheme — the same ID
pattern (`^[A-Z]+-[0-9]{3}$`) the real ledger's `schema.json` enforces today. **Correction made
during Review**: this investigation originally claimed the checklist's last commit was 2026-07-02;
it was actually touched again on 2026-08-19 (commit `280639aa`, unrelated test-path-comment
updates from `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` keeping its inline `TEST:` markers
accurate — see this file's own "Caveat observed live" note below). This does not change the core
finding: the file received no new content since 2026-05-04, has no Makefile/CI wiring, and is
superseded by the real ledger. Five support scripts
(`scripts/validate_checklist.py`, `scripts/ledger_validator.py`, `scripts/remediate_checklist.py`,
`scripts/report_coverage.py`, `scripts/apply_traceability.py`) are wired into neither `Makefile`
nor any `.github/workflows/*.yml` job — dead automation. **Correction made during Review**: this
investigation originally claimed one dangling internal reference; the real count, confirmed during
Review, is **3**: `src/engine/rpg_depth.py`'s docstring, `scripts/certification_long_run.py:154`,
and `tests/integration/kernel/test_certification_scenarios.py:112` all reference
`logic_checklist_exhaustive_v2.md` — a filename variant that does not exist under that name
anywhere in the repo.

**Caveat observed live during this investigation**: the domain-nesting ticket's implementer is
currently patching `TEST:` path comments inside `logic_checklist_exhaustive.md` to match its test
moves (e.g. `tests/unit/optimization/...` → `tests/unit/domains/optimization/...`) — so the file
is not entirely inert; something in that ticket's own scope treats keeping its references accurate
as worth doing. This doesn't change the core finding (no CI/Makefile wiring, no new content added
since 2026-07-02, superseded by the real ledger) but the implementer of this ticket should confirm
*why* that upkeep is happening (grep-based habit vs. a real, undiscovered dependency) before
archiving, not just trust this investigation's snapshot.

## Out of Scope for the eventual implementation ticket
- Retrofitting the 1,552 `legacy_unstructured` entries with structured references (finding 3) —
  large, speculative, separate effort; not blocking, not broken, just less automatable.
- Exhaustively triaging all 173 `absent_file` findings one-by-one before the domain-nesting ticket
  (`TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`) finishes moving test files — re-running the
  `absent_file` health check after that ticket lands will avoid re-doing work against a moving
  target.

## Related
- `tools/parity_index.py` (the query tooling used for this investigation)
- `docs/archive/specs/2026-05-03-checklist-governance-design.md` (documents the checklist →
  ledger migration this ticket's finding 4 confirms was completed but never archived)
- `TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` (source of the 11 correctly-`unsupported` broker entries
  cited under "the ledger is healthy overall" — context only, not itself a finding)
- `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` (in-flight test-file moves relevant to finding 2)
