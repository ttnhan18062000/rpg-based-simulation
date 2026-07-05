---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-SIX-SKILLS-INVESTIGATION
artifact_type: investigation
tags: [skills, process-improvement, investigation]
---

# Investigation — TCK-20260705-SIX-SKILLS-INVESTIGATION

## Current Behavior

### Sample scope
All 27 session-transcript files under `/home/vboxuser/.claude/projects/-home-vboxuser-Work-rpg-based-simulation/*.jsonl` (Jun 13 – Jul 5 2026) were scanned. This is fewer files than the prior ticket's "last 30 sessions" framing, but per this ticket's own instructions all 27 available files were used rather than assuming a shortfall.

### Skill invocation counts (fresh, all 27 transcripts)

Counted every `{"type":"tool_use","name":"Skill",...}` block and its `input.skill` value, across all 27 files (script: `count_skills.py`, reproduced in `test_plan.md`):

Total `Skill` tool_use invocations found: **41**, distributed as:

| Skill invoked | Count |
|---|---|
| `graphify` | 21 |
| `create-tickets` | 6 |
| `implement-epic` | 5 |
| `implement-ticket` | 4 |
| `update-config` | 2 |
| `artifact-design` | 1 |
| `fewer-permission-prompts` | 1 |
| `agent-monitoring-retro` | 1 |

The 6 skills under investigation each show **zero** invocations in this fresh, larger count — confirmed, not assumed:

| Skill | Invocations (fresh) |
|---|---|
| `test-driven-development` | 0 |
| `python-testing-patterns` | 0 |
| `backend-testing` | 0 |
| `architecture` | 0 |
| `brainstorming` | 0 |
| `doc-coauthoring` | 0 |

This matches the original ticket's finding (also zero) — no change in verdict-relevant fact from a larger sample.

### Each skill's actual "use when" description (quoted verbatim from SKILL.md)

- **`test-driven-development`**: `"Use when implementing any feature or bugfix, before writing implementation code"`. Body states the Iron Law: `"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"` and mandates a Red→Green→Refactor cycle where the test is written and observed to fail *before* any implementation code exists.
- **`python-testing-patterns`**: `"Implement comprehensive testing strategies with pytest, fixtures, mocking, and test-driven development. Use when writing Python tests, setting up test suites, or implementing testing best practices."` Body covers pytest craft: AAA structure, fixtures, mocking, parameterization, coverage philosophy.
- **`backend-testing`**: `"Write comprehensive backend tests including unit tests, integration tests, and API tests. Use when testing REST APIs, database operations, authentication flows, or business logic. Handles Jest, Pytest, Mocha, testing strategies, mocking, and test coverage."` Explicitly multi-framework (Jest/Mocha/JUnit alongside Pytest) and API/DB/auth-flow oriented.
- **`architecture`**: `"Architectural decision-making framework. Requirements analysis, trade-off evaluation, ADR documentation. Use when making architecture decisions or analyzing system design."` Body is an ADR-writing and pattern-selection framework (context-discovery.md, trade-off-analysis.md, pattern-selection.md reference files), `source: community` (generic, not project-authored).
- **`brainstorming`**: `"You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."` Body is a hard-gated pre-implementation design dialog (one question at a time → 2-3 approaches → user-approved design doc saved to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` → spec-review subagent loop → hand-off to a `writing-plans` skill).
- **`doc-coauthoring`**: `"Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content."` Body is a 3-stage *human-interactive* workflow: Context Gathering (ask the user meta-questions, request an info dump) → Refinement & Structure (iteratively build sections with the user) → Reader Testing (paste into a fresh, context-free Claude session to catch blind spots).

### Applicable-work counts (fresh, path-normalized)

Two absolute repo roots appear across the 27 transcripts (`/home/vboxuser/Work/rpg-based-simulation/...` and an older `/home/u24desktop/Working/rpg-based-simulation/...`, evidently a prior machine). Counting `file_path` naively against only the current root undercounts docs edits by ~140 events. The counting script normalizes on the `rpg-based-simulation/` path marker instead (see `test_plan.md` for the exact script and re-run instructions).

| Category | Count (Edit+Write tool_use) | Unique files |
|---|---|---|
| `tests/` (any subpath) | **281** | 157 |
| `docs/architecture/` | **9** | 6 |
| `docs/` (any subpath, top-level dir) | **669** | ~115 |

Cross-check against the original ticket's cited figures (281 / 9 / 659): `tests/` and `docs/architecture/` match **exactly**; `docs/` overall is **669 vs. 659** — a +10 delta consistent with one additional day of activity since the original count, not a methodology contradiction (see Prior Work section for the reconciliation of an initial 528-vs-659 mismatch caused by the two-machine path issue).

**`tests/` subdirectory breakdown** (proxy for TDD/python-testing-patterns/backend-testing applicability):

| Subdir | Edits |
|---|---|
| `tests/unit/` | 127 |
| `tests/integration/` | 64 |
| `tests/simulation_quality/` | 32 |
| `tests/perf/` | 10 |
| `tests/integrity/` | 10 |
| `tests/conftest.py` (top-level) | 8 |
| `tests/tools/` | 7 |
| `tests/certification/` | 7 |
| `tests/observability/` | 4 |
| `tests/architecture/` | 4 |
| `tests/regression/` | 3 |
| `tests/docs/` | 2 |
| `tests/static/`, `tests/arena/`, `tests/api/` | 1 each |

Only **1 of 281** test edits targeted `tests/api/` — the domain `backend-testing`'s REST/DB/auth focus most directly maps to. The repo already has 5 `conftest.py` fixture files and **303** existing test files independently using `@pytest.fixture` / `unittest.mock` / `@pytest.mark.parametrize` — i.e. the pytest craft `python-testing-patterns` teaches is already a mature, self-propagating convention in the repo, predating and independent of any skill invocation.

**`docs/` subdirectory breakdown** (all 669 edits, categorized; script + counts reproducible per `test_plan.md`):

| Subdir | Edits | Unique files | Character |
|---|---|---|---|
| `docs/audits/` | 331 | 21 | TCK-20260618-AUDIT-EPIC's 18-dimension audit programme — formal ticket-epic deliverables |
| `docs/plans/` | 75 | 20 | Roadmaps, `idea_*.md` (maturity:idea) proposal docs, backlog/gap-analysis docs |
| `docs/engine/` | 49 | 29 | Engine contracts/matrices — mandated parity-ledger-adjacent updates |
| `docs/parity_ledger/` | 38 | 7 | Machine-readable YAML, explicitly mandated by CLAUDE.md's Parity Ledger rule |
| `docs/mechanics/` | 29 | 7 | Mechanics Bible — mandated 100% parity updates per Authoritative Mechanics Rule |
| `docs/simulation/` | 28 | 12 | Subsystem contracts |
| `docs/simulation_quality/` | 24 | 2 | SimQ scoring contract |
| `docs/world/` | 22 | 10 | World/worldbuilding contracts |
| `docs/systems/`, `docs/guidelines/` | 16 each | 2 / 4 | Subsystem + process docs |
| `docs/architecture/` | 9 | 6 | ADRs (see below) |
| `docs/cognition/`, `docs/agent-monitoring/` | 7 each | 4 / 2 | Subsystem contracts / monitoring schema |
| all others (`core`, `performance`, `observability`, `compliance`, `ai`, `guides`, `content`, `archive`, top-level files) | ≤3 each | — | Small, scattered |

**Categorization — ticket-workflow-internal/mandated vs. free-form proposal writing** (the key open question from the original ticket):

- **Mandated/ticket-workflow-internal** (parity ledger, engine contracts, mechanics bible, subsystem contracts, audits): `docs/audits/` + `docs/engine/` + `docs/parity_ledger/` + `docs/mechanics/` + `docs/simulation/` + `docs/simulation_quality/` + `docs/world/` + `docs/systems/` + `docs/guidelines/` + `docs/cognition/` + `docs/agent-monitoring/` + small others ≈ **575 of 669 (≈ 86%)**. These updates are driven directly by CLAUDE.md's "Authoritative Mechanics Rule" (`docs/mechanics/`, `docs/parity_ledger/`) and "After Work → Update related docs" step, not by a user asking to co-write a document from scratch.
- **Free-form proposal/spec/design writing** (the kind `doc-coauthoring` targets): `docs/plans/` (75) + `docs/architecture/` (9) + `docs/guides/` (1) ≈ **85 of 669 (≈ 13%)**.

Sampled `docs/plans/` files directly (`audit_fix_plan.md`, `idea_pressure_propagation_economy.md`, `engine_future_epics_roadmap.md`): all read as single-pass, agent-authored planning artifacts produced during an investigation/epic-scoping ticket ("Five parallel investigations were run... covering [subsystems]" — `engine_future_epics_roadmap.md`'s own Method section), not the product of an interactive back-and-forth co-authoring session with a human. `doc-coauthoring`'s actual mechanism (ask the user meta-questions, request an info dump, iterate section-by-section, reader-test with a fresh Claude) never appears in the transcripts for any of these files.

Sampled `docs/architecture/simulation_watchdog.md` directly: it already follows a Status → Context → Decision → Rationale → Trade-offs → Consequences structure — i.e. the exact ADR shape the `architecture` skill's `trade-off-analysis.md` template would produce — without the skill ever being invoked. All 6 `docs/architecture/*.md` files follow this same convention by precedent (established by earlier files, copied forward per CLAUDE.md's Clarification Rule: "follow existing patterns").

### `brainstorming` proxy (fuzzy — stated explicitly per the ticket's instructions)

File-path proxies don't apply to `brainstorming`. Proxy used: all 36 `AskUserQuestion` tool_use calls across the 27 transcripts were dumped and read in full (script: `dump_askuser.py`). None of the 36 match brainstorming's actual trigger shape (a brand-new feature/system idea, explored via 2-3 alternative designs before any ticket exists). All 36 are decision forks *embedded inside already-scoped ticket/investigation work*: bug-fix scope decisions (e.g. "How should TCK-...-INFORMATION handle the dead-code blocker?"), cleanup-mode choices, ticket-batching/ordering choices, audit-scoring-methodology choices, deliverable-format choices (Artifact vs. repo markdown). This is a materially different shape from brainstorming's "explore user intent for a new creative feature before any code" gate.

## Per-Skill Verdict Table

| Skill | Invocations | Applicable-work evidence | CLAUDE.md overlap? | Verdict |
|---|---|---|---|---|
| `test-driven-development` | 0 / 41 | 281 test-file edits across 27 sessions | **Yes, but divergent, not overlapping-and-covering.** CLAUDE.md's Testing Rule (line 157) is outcome-based ("run tests before claiming completion," "add/update tests whenever behavior changes") and the repo's own `implement-ticket.js` pipeline places **Phase 5: Implement before Phase 6: Test** — the opposite order of TDD's Iron Law ("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"). Invoking this skill as written would conflict with the codified pipeline sequencing, not merely duplicate it. | **Correctly redundant (by deliberate divergence, not by rule-content overlap)** — the repo has an established, different disicpline (implement→test→parity→verify) that a strict TDD skill would fight, not reinforce. |
| `python-testing-patterns` | 0 / 41 | Same 281 test-file edits; only 1 targets `tests/api/` | Partial. CLAUDE.md's Testing Rule is a one-line mention of "deterministic, isolated, readable" tests — thinner than the skill's craft content (fixtures, mocking, parameterization, AAA). But 5 `conftest.py` files + 303 existing test files already establish these patterns by precedent, which agents replicate per the Clarification Rule ("follow existing patterns"). | **Correctly redundant** — thinnest CLAUDE.md coverage of the three testing skills, but the gap is filled by mature in-repo precedent rather than by CLAUDE.md text itself. Softest verdict of the six; would be the first to reconsider if a genuinely novel test pattern (e.g. property-based testing, async mocking) were needed without existing precedent. |
| `backend-testing` | 0 / 41 | Only 1 of 281 test edits targets `tests/api/`; skill is Jest/Mocha/Express/auth-flow-oriented | N/A — domain mismatch, not a rule-overlap question. | **Correctly redundant** — near-zero applicable surface. This is a simulation engine, not a CRUD/auth backend; the skill's actual target domain (REST/DB/auth testing across multiple JS+Python frameworks) barely exists here. The already-wired `api-design-principles` gap (from `TCK-20260704-SKILL-TRIGGER-COVERAGE`) covers the adjacent `src/api/` surface that does exist. |
| `architecture` | 0 / 41 | 9 `docs/architecture/` edits, 6 unique files | **No real overlap** — CLAUDE.md's "Architecture Rule" (line 170) is about runtime code-architecture boundaries (durable-state rules, strategic/tactical separation, decision-vs-mutation boundaries), a *different subject* from the skill's ADR-authoring workflow. The actual redundancy source is that all 6 `docs/architecture/*.md` files already follow ADR structure (Status/Context/Decision/Rationale/Trade-offs/Consequences) by established precedent, independent of CLAUDE.md's Architecture Rule text. | **Correctly redundant, but for a different reason than the original ticket assumed** — not because CLAUDE.md's Architecture Rule covers ADR-writing (it doesn't), but because ADR-writing is already a self-propagating repo convention. |
| `brainstorming` | 0 / 41 | No clean file-path proxy; 36 `AskUserQuestion` calls sampled, none match the "new feature, 2-3 alternatives, pre-implementation design doc" shape | CLAUDE.md's Workflow Rule + Clarification Rule (mandatory `investigation.md`/`plan.md` staging artifacts before implementation, "ask only if it changes outcomes") function as a repo-native substitute pre-implementation gate. | **Correctly redundant** — the repo's own ticket-scoping discipline (investigation → plan → acceptance criteria, itself user-reviewable via the ticket file) already serves brainstorming's core function of "no implementation before a reviewed design," in a repo-native form. brainstorming's specific artifacts (`docs/superpowers/specs/`, a `spec-document-reviewer` subagent, a `writing-plans` hand-off skill) don't even correspond to this repo's actual conventions, suggesting it's a generic/off-template skill for this project regardless. |
| `doc-coauthoring` | 0 / 41 | 669 `docs/` edits; ≈13% (`docs/plans/` + `docs/architecture/`, ~85 edits) are free-form proposal/ADR-shaped rather than mandated parity/contract updates | CLAUDE.md's Workflow Rule mandates related-docs updates as a mechanical step but has no interactive human-co-authoring content — genuinely a different kind of guidance, not overlapping. | **Correctly redundant, narrow soft-gap noted** — ~87% of `docs/` edits are mandated parity/contract/audit updates outside `doc-coauthoring`'s scope entirely. The remaining ~13% (`docs/plans/`, `docs/architecture/`) are topically close to what the skill targets, but are produced via single-pass **agent-autonomous** ticket/investigation output, not an interactive **human**-co-authoring session — the skill's trigger condition (a user wanting to draft something with Claude) doesn't literally match what's happening. Not scored as a clean gap because the authorship mode differs from the skill's premise, but flagged as the closest of the six to a real gap if reader-quality issues in `docs/plans/` docs ever surface. |

## Mechanics / Engine Constraints
N/A — this is a process/documentation investigation; no simulation logic, formula, or engine contract was touched or evaluated for mechanical correctness.

## Parity Ledger Overlap
N/A — no parity ledger subsystem (`docs/parity_ledger/*.yaml`) covers agent-skill-usage patterns; this investigation's subject matter (Claude Code skill invocation telemetry) is outside the Mechanics Bible / Engine Contracts domain entirely.

## Prior Work
`TCK-20260704-SKILL-TRIGGER-COVERAGE` established the original methodology (grep transcripts for `Skill` tool_use blocks + cross-reference file-path activity) over "the last 30 session transcripts" and cited: 281 test-file edits, 9 `docs/architecture/` edits, 659 `docs/` edits overall, all six skills at zero invocations. It explicitly left the genuine-gap-vs-correctly-redundant question open, pending a follow-on investigation — this ticket.

This investigation's fresh count, over all 27 currently-available transcripts:
- `tests/` and `docs/architecture/` counts **match exactly** (281 and 9) — no drift.
- Raw `docs/` count using a naive current-machine-path filter initially undercounted at **528** (against the original ticket's 659) — a 131-event gap. Root-caused: two absolute repo roots appear across the 27 transcripts (`/home/vboxuser/Work/rpg-based-simulation/` on the current machine, and an older `/home/u24desktop/Working/rpg-based-simulation/` from a prior machine); a naive filter using only the current root's prefix silently dropped every edit logged under the old root. Re-counting by normalizing on the `rpg-based-simulation/` path marker (matching either root) recovers **669** — a +10 delta from the original 659, consistent with one additional day of work since that ticket, not a real discrepancy. This reconciliation itself is evidence for why `test_plan.md` insists on the exact reproducible script rather than an ad hoc grep.
- All six skills remain at zero invocations — the larger, fresher sample does not change this finding.
- No skill invocation count exceeded the original ticket's implicit assumption; the only new information this investigation adds is the CLAUDE.md-overlap reasoning and the docs/ composition breakdown, which the original ticket explicitly deferred.

## Risks and Open Questions
- **`brainstorming`'s proxy is inherently soft.** There is no file-path signature for "a creative-design conversation almost happened but didn't." The 36-`AskUserQuestion` sample is a reasonable proxy but not a proof; it's possible a genuine brand-new-feature brainstorming moment happened in prose-only dialogue with no `AskUserQuestion` call and wouldn't show up in this proxy at all. Treat the `brainstorming` verdict as lower-confidence than the file-path-based verdicts.
- **The Skill-tool-call log format was stable across all 27 files** (`{"type":"tool_use","name":"Skill","input":{"skill":"..."}}`) — no format-migration risk found, unlike the docs/-path double-machine-root issue.
- **`doc-coauthoring`'s ~13% "free-form" slice is itself an approximation.** `docs/plans/` and `docs/architecture/` were treated as the free-form bucket wholesale; a few individual files in those directories may still be closer to mandated-update territory (e.g. an ADR added purely to record a decision already made elsewhere, with no drafting dialog at all) and a few files elsewhere in `docs/` may be more free-form than assumed. The categorization is directionally solid (large majority mandated) but not file-by-file audited.
- **`python-testing-patterns` is the softest "correctly redundant" verdict of the six** — CLAUDE.md's actual rule text is thin here, and the redundancy argument leans entirely on in-repo precedent (conftest.py + 303 existing fixture/mock/parametrize files) rather than an explicit rule. If repo test conventions ever drift or a genuinely novel testing need arises (e.g., property-based testing, which doesn't appear anywhere in the 303-file sample), this verdict should be revisited before the other two testing skills.

## Anti-Drift Hazards
This investigation is read-only by design and must not be treated as authorization to act on its findings beyond documentation:
- **No skill was wired into `CLAUDE.md`, any agent prompt, or any other mechanism in this ticket.** All six verdicts above are findings, not implementations.
- Per the ticket's explicit sequencing note, any confirmed-gap wiring (this investigation found none of the six to be a clean, unambiguous gap — the closest, `doc-coauthoring`, was scored "correctly redundant, narrow soft-gap noted" rather than "genuine gap") is deferred to `tickets/todos/tag-taxonomy-followups/TCK-20260705-TAG-SKILL-SUGGEST.md`'s eventual scope, or a small explicitly-blocked follow-on ticket if that ticket is not yet done.
- No `.claude/skills/*/SKILL.md` file was modified, removed, or archived.
- No new ticket file was created by this investigation.
