---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK
artifact_type: investigation
tags: [agent-monitoring, workflows, data-quality]
---

# Investigation: TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK

## Step 1 (mandatory first step): independent re-derivation of the Request Summary's 6/23/29 figures

The ticket's own text warns that an earlier pass of this ticket got the denominator wrong (1 finding
instead of 6, from reading the wrong `writeSidecar` argument position) and that no reproduction
script exists anywhere in the repo — `staging_artifacts/TCK-20260924-.../` did not exist before this
session, so the 6/23/29 figures were, until this investigation, asserted rather than reproducible.

Before trusting or acting on those figures, I wrote an independent scan
(`vocab_scan.py`, committed alongside this file — see below) from scratch, without reading the prior
attempt's code, and ran it against the current worktree's HEAD (`fa7c10e7df6a427e01816c6e626f6888e3ab24d0`,
`measurement-fidelity-followups` branched from this commit).

**Scan shape:**
- Reads all `.claude/workflows/*.js` files (11 found, matching the ticket's count).
- Strips comments first: full-line `//` comments and `/* ... */` block interiors are blanked out
  line-by-line before any literal is extracted. Confirmed no real call site has a trailing `//`
  comment sharing its line (the two lines a naive unclosed-paren scan flagged were both pure-prose
  comment lines mentioning "writeSidecar()" without parens matching real call syntax).
- Extracts, per file, two independent literal sets:
  - **Agent literals**: `agent: '<literal>'` and `writeSidecar(<seq>, '<phase>', '<agent>')`'s
    **third** positional argument.
  - **Phase literals**: `phase('<literal>')`, `pushEvent('<literal>', ...)`'s first positional
    argument, and `writeSidecar(...)`'s **second** positional argument.
- Confirmed via `grep -c writeSidecar` + an unclosed-paren awk scan that every real `writeSidecar(`
  call site in all 11 files is single-line (35 total call-site + comment mentions; the only
  "unclosed parens on this line" hits were the two comment-prose lines above) — so a single-line
  regex has full coverage here; no multi-line `writeSidecar(...)` calls exist to worry about
  (resolves Assumption/Open Question 1).
- Compares each literal against `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` (via `is_known_agent()` for the
  agent family, so the `create-tickets` `investigate:` prefix family is honored, not raw set
  membership) **keyed by the literal's own workflow** — a file not present as a key in a registry
  contributes every one of its literals as unregistered.

**Result: exact match with the ticket's stated figures.**

```
TOTAL agent: 6
TOTAL phase: 23
TOTAL combined: 29
Workflow files keyed in neither registry: ['compact-simulation-result', 'generate-simulation-setup',
  'investigate-simulation-result', 'prepare-simulation-execution', 'propose-simulation-enhancements',
  'register-simulation-result', 'update-knowledge-store']
```

Same 6 agent literals (`create-tickets: comprehend`; `implement-epic: batch-monitoring-write,
discover, epic-close, folder-cleanup, tracking-doc-update`), same 23 phase literals across the same
8 workflows, same 7 files unkeyed in either registry. Full output saved as
`vocab_scan_output.txt` alongside this file.

**Conclusion: AC2's "29 literals — 6 agent, 23 phase" figure is verified correct by an independent,
from-scratch re-derivation. No AC correction is needed. The design peer does not need to be notified
of a discrepancy, because there isn't one** — this differs from the outcome the peer's own note
anticipated as plausible, but the evidence is what it is.

## Existing precedent read

- `tools/gate_checks/workflow_meta_conformance.py` — the closest sibling. Confirms the regex-over-
  `.claude/workflows/*.js` approach is an accepted pattern in this codebase (`extract_meta_phases()`
  uses a bracket-depth scan, not a general JS parser). Its `run_id`-keyed, "unknown workflow -> skip
  silently" model (`infer_workflow` returning `None`) is exactly what AC1 forbids reusing for this
  ticket's keyed-workflow decision — this check must independently detect an unkeyed *file*, which
  `infer_workflow` (keyed on `run_id` prefixes, not filenames) cannot answer at all.
- `tools/gate_checks/monitoring_anomaly_validator.py` — precedent for the `List[dict]`
  `{"status": "PASS"|"FAIL", "evidence": ...}` shape and the `MARKER:` + `json.dumps(...)` stdout
  contract. Differs in one respect this ticket's AC8 requires: that module `sys.exit(1)` on any
  FAIL; this check must exit 0 even with findings (advisory only, per Scope item 8/AC8).
- `tools/agent-monitoring/vocabulary.py` — read in full. `is_known_agent()` exists;
  no `is_known_phase()` accessor exists (confirmed, matches ticket's Assumption 5). Every existing
  `WORKFLOW_AGENTS` registration carries an inline comment documenting its evidentiary basis — the
  standard this ticket's own Scope item 7 requires new entries to match.

## Decision: add `is_known_phase()`

Per Assumption/Open Question 5, decided here rather than left implicit: **add it.** It is a small,
symmetrical accessor mirroring `is_known_agent()`'s existing signature
(`is_known_phase(workflow: str, phase: str) -> bool`), and the new check needs *some* way to test
phase membership — reaching into `WORKFLOW_PHASES[workflow]` directly from a second module would be
exactly the kind of raw-set-membership shortcut AC1/Scope item 5 already reject for the agent side.
Symmetry with `is_known_agent()` costs one four-line function and removes a reason for the new
check module to import `WORKFLOW_PHASES` and reimplement lookup logic itself. No prefix-family
equivalent exists for phases today, so it is pure set membership, same shape as `is_known_agent()`
minus the prefix branch.

## Reproduction script

See `vocab_scan.py` in this directory — runnable standalone (`python3 vocab_scan.py` from repo
root), reads `tools/agent-monitoring/vocabulary.py`'s live registries and `.claude/workflows/*.js`
directly, no fixtures. This is the *investigation* reproduction; the actual gate-check module
(`tools/gate_checks/workflow_vocabulary_check.py`) is a separate, test-covered production module
built in Implement, sharing the same literal-extraction shape but returning the project's standard
`List[dict]` result contract instead of printing to stdout.
