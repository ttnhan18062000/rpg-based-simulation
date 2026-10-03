---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-AI-AGENT-OVERVIEW-DOC
artifact_type: test_plan
tags: [documentation, ai, workflows]
---

# Test Plan — TCK-20260705-AI-AGENT-OVERVIEW-DOC

## Regression Surface

N/A in the code-execution sense — no `src/` or `tests/` files are touched by this ticket. The only
mechanical regression surface is frontmatter compliance:

- `tools/validate_frontmatter.py` must pass against the new document (once Plan/Implement chooses its
  path and writes it) and against this ticket's own two staging artifacts. Valid enum values confirmed
  from the tool itself (`tools/validate_frontmatter.py` L24-31): `STATUS_VALUES = {"authoritative",
  "active", "historical", "archive"}`, `LAYER_VALUES` includes `"ai"`, `AUTHORITY_VALUES = {"P0", "P1",
  "P2"}`, `AUDIENCE_VALUES = {"developer", "agent", "designer", "historical"}`. The new document (a
  `doc`, not a `ticket`/`artifact`) should use `status: active`, `layer: ai`, `authority: P1`,
  `audience: developer` — matching the pattern of every other file in `docs/ai/` (all 6 existing files
  use exactly this frontmatter shape).
- If `docs/README.md` or `docs/ai/README.md` are edited (per the ticket's Acceptance Criteria — adding
  index rows), their existing frontmatter is untouched by this ticket's edits (only body/table content
  changes), so no frontmatter regression risk there — confirm no accidental frontmatter mutation with a
  diff review, not a schema re-validation (their frontmatter doesn't change).

## New Tests Required

None in the pytest sense — this is a documentation-only ticket with no code behavior to test. Required
verification is manual/agent-driven fact-checking of the new document's claims against the source docs
and actual `.claude/workflows/*.js` / `.claude/agents/*.md` files. Checklist for Plan/Implement/Verify:

1. **Every workflow name mentioned in the new doc must exist** in `docs/ai/workflows.md`'s catalog OR
   (for `simq-audit`, which `workflows.md` omits) in `docs/simulation_quality/audit_workflow.md` /
   `.claude/workflows/simq-audit.js` directly.
2. **Every phase name mentioned for a workflow must match the actual `.claude/workflows/<name>.js`
   `meta.phases` array** — NOT `docs/ai/workflows.md`'s prose, for the 4 workflows this investigation
   found stale there:
   - `create-tickets`: Comprehend, Investigate, Structure, Write, Link (NOT Parse/Write/Link)
   - `generate-simulation-setup`: Scan, Draft, Validate (NOT Spec Draft/Validation/Promotion)
   - `investigate-simulation-result`: Load, Analyze, Report (NOT ...Correlate...)
   - `compact-simulation-result`: Scan, Compact, Archive (NOT Inventory/Compact/Archive)
   For all other workflows (`implement-ticket`, `implement-epic`, `prepare-simulation-execution`,
   `register-simulation-result`, `propose-simulation-enhancements`, `update-knowledge-store`,
   `simq-audit`), `workflows.md`'s/`audit_workflow.md`'s phase lists already match code — safe to cite
   those docs directly.
3. **Every subagent named must exist** in `.claude/agents/*.md` (11 files: `ticket-scoper`,
   `investigator`, `planner`, `architecture-reviewer`, `done-checker`, `implementer`, `test-scoper`,
   `parity-updater`, `mechanics-auditor`, `world-debugger`, `simulation-analyst`).
4. **Every file path cited in the new doc must actually exist** — spot-check with `test -f <path>` or
   equivalent for every `docs/...`, `src/...`, `.claude/...`, `tests/...` path mentioned.
5. **The 9-phase pipeline, tier table (hotfix/standard/epic), and 11+1 DoD condition count** must match
   `CLAUDE.md`'s own "Workflow Rule" / "Tier Routing" / "Definition of Done" sections verbatim in
   substance (verified already consistent in this investigation — Verify should re-confirm no drift was
   introduced by copy-paraphrasing).
6. **The lab_contract.md 6-stage session lifecycle and the workflows.md 7-workflow simulation sequence
   must be presented as related-but-distinct**, not merged into one incorrectly-numbered list (see
   investigation.md Risk #3).
7. **The SimQ audit workflow's "Do not" list item** ("do not use this to change SimQ scoring formulas/
   pillar logic — `src/simulation_quality/*` is out of scope") should be preserved verbatim in spirit if
   the new doc characterizes what `simq-audit` is/isn't for, since it is the one explicit scope boundary
   in that source doc.
8. **The `agent_infrastructure_audit.md` score (8.0/10) and headline framing** ("Mature, gated, not yet
   deterministic") should be cited exactly as written if referenced — not re-derived or re-averaged from
   its category table.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_validate_frontmatter.py -q
```

(Regression-only — confirms the frontmatter validator itself still behaves correctly; it is not testing
the new document's content, only that the tool used to gate it is unaffected. No other test files are in
scope since no `src/` code changes.)

Additionally, once the new document's path is chosen and written, run the validator directly against it
and against both staging artifacts (already conformant per the frontmatter above):

```
python3 tools/validate_frontmatter.py docs/ai/<new-doc-name>.md
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/investigation.md
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/test_plan.md
```

## Anti-Drift Test Guards

- **Every specific claim (phase name, file path, tier rule, gate name, return-status literal) in the new
  document must be traceable to either (a) a source doc section that this investigation confirmed
  matches code, or (b) a direct `.claude/workflows/*.js` / `.claude/agents/*.md` read, for the 4 sections
  this investigation found `workflows.md` stale on.** A reviewer should not accept "workflows.md says X"
  as sufficient sourcing for `create-tickets`, `generate-simulation-setup`,
  `investigate-simulation-result`, or `compact-simulation-result`'s phase lists — those four must be
  independently re-verified against the `.js` file at review time, not copied from this investigation.md
  verbatim without a fresh check (staleness could theoretically be fixed between investigation and
  implementation, though unlikely within this ticket's lifetime).
- **Reviewer spot-check**: pick 3 random facts from the new document (a phase name, a file path, a gate
  name) not already covered by the checklist above and independently verify each against the primary
  source, to catch any synthesis drift the checklist didn't anticipate.
- **Do not let the new document's Prior Work / cross-reference section imply `workflows.md`/`skills.md`/
  README.md's stale counts were corrected as part of this ticket** — this ticket is explicitly barred
  from editing those 8 source documents' content (only README.md's Document Index gets a new row per the
  Acceptance Criteria, and `docs/README.md`'s AI Tooling section gets a new bullet — neither of those
  edits touches the stale phase-list prose found above). If the new doc's own text mentions the staleness
  at all, it must be phrased as an observation, not a claim of having fixed it.
- **Confirm no `data/runs/` or `reports/release_proof/` artifacts were created by this investigation** —
  none should exist since no simulation was run for this ticket; `done-checker`/Verify should still check
  per the standard DoD condition 10, even though it is a no-op here.
