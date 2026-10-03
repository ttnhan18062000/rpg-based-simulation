---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
artifact_type: investigation
tags: [ai, workflows, process-improvement, hooks, skills]
---

# Investigation — TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE

**Read this note first (workflow note from the launching agent, carried forward for the external
implementer):** Claude performs Investigate/Plan/Review for this ticket only. The actual
Implement-phase code/config changes — including the real Codex CLI fixture-capture experiment —
will be performed externally by Codex CLI, working from `plan.md` alone, without this
conversation's implicit context. Every finding below is written with real file paths, line-level
detail, and explicit unknowns so `plan.md` can be self-contained for that external implementer.

## Current Behavior

### 1. Legacy `.agents/skills/` — containment target

`ls .agents/skills/` and `find .agents/skills -name SKILL.md` both confirm **exactly 18**
`SKILL.md` files, one per subdirectory:

```
api-design-principles  architecture  backend-testing  brainstorming  clean-code
codebase-search  code-review  create-skill  debugging-strategies  doc-coauthoring
frontend-design  graphify  prompt-builder  python-performance-optimization
python-testing-patterns  receiving-code-review  requesting-code-review
test-driven-development
```

`docs/ai/agents_dir_disposition.md` (read in full) classifies every one of these 18 paths, but
the classification is **Claude-surface-only**:

- 11 dirs (`api-design-principles`, `architecture`, `backend-testing`, `brainstorming`,
  `debugging-strategies`, `doc-coauthoring`, `frontend-design`, `prompt-builder`,
  `python-performance-optimization`, `python-testing-patterns`, `test-driven-development`) —
  `archive-retire`, superseded by identically-named `.claude/skills/*/SKILL.md` entries.
- `graphify` — `archive-retire`, superseded by the **user-level global**
  `~/.claude/skills/graphify/SKILL.md` (different tier, not a `.claude/skills/` migration target).
- 6 dirs (`clean-code`, `codebase-search`, `code-review`, `create-skill`,
  `receiving-code-review`, `requesting-code-review`) — `retain-and-migrate`: **no**
  `.claude/skills/` equivalent exists, no test asserts their content, nothing supersedes them.
  Disposition doc records these as candidates for a *future* promotion-review ticket, explicitly
  **not** executed by that doc or (per this ticket's scope) by this one.

The doc's "Approved active location" section (line 41) states the exact containment law this
ticket must implement, verbatim:

> "The first Codex-delivery implementation ticket must quarantine/archive the legacy tree, or
> atomically replace it with the contract-generated catalog, before enabling root `AGENTS.md` or
> any project Codex configuration."

Neither mechanism (quarantine vs. atomic replace) is picked by that doc — it names both as valid.
The follow-on review-response doc
(`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_final_corrections_response_codex.md`,
"Implementation constraint carried forward") narrows the requirement further, verbatim:

> "It must preserve an archived, reviewable copy outside Codex's discovery path and use an atomic
> or otherwise recoverable replacement strategy."

So the constraint is: (a) an archived, byte-identical, reviewable copy must exist **outside**
Codex's discovery path (Codex scans `.agents/skills` from cwd up to repo root per
`codex_capability_matrix.md` §5 — so the archive location must not itself be a `.agents/skills`
directory anywhere on that upward path), and (b) the swap itself must be atomic/recoverable. This
does **not** pick "quarantine" vs. "atomic replace" for this ticket — that choice is still open
(see Risks/Open Questions #1).

**Consequence for the 6 `retain-and-migrate` dirs:** since the containment law applies to the
*whole* `.agents/skills/` tree regardless of per-item Claude-classification (the classification
column only ever compared against Claude's `.claude/skills/`, never against Codex discoverability
— disposition doc line 43 says this explicitly), all 18 dirs leave Codex's live discovery path
together, including the 6 that have no Claude-side successor yet. Their unique content survives
only in the archived copy, not in Codex's newly generated catalog (see next section) — this is
consistent with the disposition doc's own explicit deferral of their promotion review to a future
ticket, not a regression this ticket introduces.

### 2. Contract-driven generation — `generate()` has no AGENTS.md/SKILL.md mode

`agent-orchestration/skills.yaml` (read in full) lists **16** skill entries:
`agent-monitoring-retro, api-design-principles, architecture, backend-testing, brainstorming,
create-tickets, debugging-strategies, doc-coauthoring, frontend-design, implement-epic,
implement-ticket, prompt-builder, python-performance-optimization, python-testing-patterns,
simq-audit, test-driven-development`. Each entry has exactly four fields per
`tools/agent_orchestration/loader.py`'s `_REQUIRED_SKILL_ENTRY_KEYS`: `id`, `description`
(one-line string), `workflows`, `roles`. **There is no body/instructional-content field.**

Cross-checked against `ls .claude/skills/`: the 16 dirs there match `skills.yaml`'s 16 ids
**exactly, 1:1** — `skills.yaml` is a catalog of Claude's own skills, not an independently
Codex-scoped list. None of the 18 legacy `.agents/skills/` dirs' unique 6 (`clean-code`,
`codebase-search`, `code-review`, `create-skill`, `receiving-code-review`,
`requesting-code-review`) or `graphify` appear in `skills.yaml`.

`tools/agent_orchestration/generator.py::generate()` (read in full, 99 lines) is the only existing
generation entry point. It does exactly one thing: calls `load_contract()` then re-serializes
`contract.yaml`, `workflows/implement-ticket.yaml`, `roles/*.yaml`, `skills.yaml`,
`monitoring-schema.yaml`, `hook-events.yaml` back out as **YAML** files under `target_dir` — a
pure contract-to-contract round-trip, same field names, same shape, just re-materialized. It has
**no mode that produces Markdown** (no `AGENTS.md` rendering, no per-skill `SKILL.md`
directory-with-frontmatter rendering). This is confirmed identical to the prior ticket's own
finding for the Claude-adapter case
(`stored_artifacts/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER/investigation.md:30-40`): `generate()`
is reusable as a **read** path (`load_contract()`) but not as a template for this ticket's output
shape.

`tools/agent_orchestration_claude_adapter/generator.py` (ticket 3/7's deliverable, read via its
test file `tests/agent_orchestration_claude_adapter/test_generator_containment.py`) is also not a
template to copy: it renders a single YAML file
(`agent-orchestration/rendered/claude-adapter.yaml`) with a `claude_adapter_schema_version`,
`phase_order`, `terminal_statuses` shape — still YAML, still not the two-format
(Markdown-file + Markdown-file-per-directory) output this ticket needs.

**Conclusion: this ticket needs genuinely new generation logic**, in a new package (a Codex-adapter
generator distinct from both `tools/agent_orchestration/` and
`tools/agent_orchestration_claude_adapter/`), that:
- reads the same `load_contract()` bundle (reuse, don't reimplement — matches this repo's existing
  reuse pattern for `loader.py`),
- renders a root `AGENTS.md` (Markdown) from `contract.yaml`/`workflows/implement-ticket.yaml`
  content,
- renders one `.agents/skills/<id>/SKILL.md` per `skills.yaml` entry, with Codex's required
  `name` + `description` frontmatter fields (per `codex_capability_matrix.md` §5) populated from
  `id`/`description`.

**Open question this creates (see Risks #2):** `skills.yaml` has no body/instruction-content
field, so where does each generated `SKILL.md`'s *instructional body* (beyond the one-line
description) come from? Options are enumerated there, not decided here.

### 3. The stale `.agents/rules/AGENTS.md` draft — phase-count claim does NOT live where the ticket says

Read `.agents/rules/AGENTS.md` in full (169 lines). It is a generic rules draft (Priority Order,
Hard Rules, Context Scan, Clarification, Traceability, Architecture, Graph Awareness, During Work,
Testing, Completion, Stop Conditions) — **it contains no mention of "17", "32", or "phase" at
all** (`grep -n "phase\|17\|32" .agents/rules/AGENTS.md` → zero hits).

The "17-phase vs. real 32-phase pipeline drift" the ticket's AC and Related Docs cite actually
lives in a **different** file: `.agents/rules/authoritative_mechanics.md:18` —
`` `docs/engine/authoritative_pipeline.md`: The 17-phase apply sequence. `` — confirmed factually
wrong against `docs/engine/authoritative_pipeline.md:11`'s own text: "refined through these **32**
phases." `docs/ai/agents_dir_disposition.md`'s per-path table (line 25) already attributes this
drift correctly to `authoritative_mechanics.md`, not `AGENTS.md`.

**This is a citation mismatch in this ticket's own AC text**, not a blocker: the new root
`AGENTS.md` obviously won't copy `.agents/rules/AGENTS.md` verbatim regardless, so the AC's literal
requirement ("does not repeat the confirmed 17-phase pipeline drift") is trivially satisfiable —
there is no 17-phase claim in the file it's citing to begin with. Flagged so Plan doesn't waste
time hunting for phase-count text inside `.agents/rules/AGENTS.md` that isn't there, and so the AC
wording can be corrected/clarified in `plan.md` (the real 32-phase-pipeline documentation
obligation should instead be phrased as "must not copy `.agents/rules/authoritative_mechanics.md`'s
17-phase claim into the new AGENTS.md," or simply "must state 32 phases, sourced from
`docs/engine/authoritative_pipeline.md`," independent of which stale file the wrong number came
from).

### 4. The `.codex/` scope-creep test conflict — confirmed, must be resolved by this ticket

`tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` (read in full, 57 lines)
defines two tests:

- `test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree` (lines 42-49): scans only
  `tools/agent_orchestration_claude_adapter/**/*.{py,yaml,yml,md}` plus three named files
  (`agent-orchestration/terminal-statuses.yaml`, `agent-orchestration/rendered/claude-adapter.yaml`,
  `agent-orchestration/intentional-divergences.md`) for the substring markers `.codex/`,
  `conformance_diff`, `claude_conformance`, `.claude/conformance`. **This one is scoped narrowly
  enough to remain valid forever** — it proves ticket 3/7's own delivered tree never started
  Codex-adapter work, and this ticket's new files live in entirely different paths (a new
  `tools/agent_orchestration_codex_*` package, `.agents/`, `.codex/`, root `AGENTS.md`), none of
  which this test's `_SCANNED_DIRS`/`_SCANNED_FILES` touch. **No change needed here.**

- `test_no_dot_codex_directory_exists_in_repo` (lines 52-56): unconditionally asserts
  `not (_REPO_ROOT / ".codex").exists()`, repo-wide, with the docstring "`.codex/` must not be
  created by this ticket — Codex-side adapter implementation is owned by a different ticket." That
  "different ticket" is **this one** (`TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`), whose own
  scope explicitly requires "Add minimal trusted `.codex/` configuration only after fixture
  experiments confirm behavior." **This test will fail, repo-wide, the moment this ticket's own
  `.codex/` directory lands** — a real, confirmed regression this ticket's own work would otherwise
  introduce into an unrelated ticket's (3/7's) delivered test suite.

This must be resolved by **this ticket's own plan**, not left to break silently at Implement time.
See Risks/Open Questions #3 for the resolution options (a decision, not an investigation finding).

### 5. Real hook-payload fixture capture — what exists, what's missing

`docs/ai/replay_fixture_spec.md` (read in full) defines the envelope shape consumed by
`tools/agent_replay/runner.py::replay_slice()` — a **different** fixture concern entirely: it
replays the `implement-ticket` workflow's own Scope→Investigate→Plan→Review phase-slice logic
(`phase`, `agent`, `input`, `output`, `transition` per phase), not a raw Codex hook `stdin` JSON
payload capture. The doc's own text is explicit that this is not a draft of any other fixture
format; there's no cross-purpose overlap to exploit here.

`docs/ai/codex_capability_matrix.md` §6 ("Payload/Fixture Gaps", read in full) draws the exact
distinction this ticket's AC needs: **documentation-citation grade** evidence (the field tables in
§1, sourced from the cached Codex manual only) vs. **direct-experiment grade** evidence (the one
thing actually run: `codex features list`, confirming the hooks *capability* is enabled/stable on
the installed build — **not** confirming the actual per-event `stdin` payload shape). §6's
"Deferred" paragraph names the missing piece precisely: "an isolated stdin-payload-capture fixture
experiment — writing a throwaway `hooks.json` outside this repo's trust boundary and running
`codex exec` against a scratch fixture to capture one event's real JSON payload — was considered
and explicitly not performed... recorded here as future scope for a dedicated ticket." **This
ticket is that dedicated ticket.**

No fixture of this exact shape (a real, captured Codex `stdin` hook-event JSON payload) exists
anywhere in this repo today. `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`
is the only committed fixture in the adjacent family, and it follows `replay_fixture_spec.md`'s
different envelope — not reusable as a template for a raw hook-payload capture, though its
existence establishes the "committed fixture file under `tests/fixtures/`" convention this ticket
should follow for whatever new fixture(s) it adds.

**"Isolated scratch-directory" precedent in this repo — two partial precedents, no exact match:**
- `tests/tools/test_post_tool_hook.py` (read in full): drives `tools/agent-monitoring/post_tool_hook.py`
  as a real subprocess, `cwd=tmp_path`, JSON fed on `stdin`, asserting on the resulting file
  contents under `tmp_path`. This is the closest **isolation pattern** (subprocess + throwaway
  `cwd`) — but it invokes this repo's own Claude-side hook consumer script, not a live third-party
  Codex CLI process.
- `tests/tools/test_codex_capability_diagnostics.py` (read in full): the closest **real-Codex-CLI**
  precedent — `subprocess.run(["codex", "features", "list"], ...)`, with
  `shutil.which("codex") is None → pytest.skip(...)` as the environment-absence guard. It does
  **not** use an isolated scratch directory (runs in the ambient repo cwd) and only invokes a
  read-only diagnostic subcommand, never a hook.

No existing precedent combines both: an isolated scratch directory containing its own throwaway
`.codex/` trust/hook config, with a real `codex exec`/hook-triggering invocation inside it, whose
`stdin` payload is captured and written to a committed fixture file. This is genuinely new
experimental work — consistent with the launching agent's explicit instruction that this
experiment is Codex's own job to perform during Implement, not something Investigate should run.

### 6. `.codex/` config schema — confirmed partially unknown

`docs/ai/codex_capability_matrix.md` §3 ("Project Trust Behavior", read in full) cites the manual
verbatim: project-scoped config loads only when the project is trusted, and names the config file
as `.codex/config.toml` (manual line 3170's own heading: "Project config files
(`.codex/config.toml`)"). §1 documents the **hook I/O contract** in detail (per-event `stdin`
field tables, output-field support, matcher-value vocabulary per event) — but this is the payload
shape a hook *script* receives once invoked, not the **registration syntax** for declaring "run
this script on event X with matcher Y" inside `.codex/config.toml` (the Codex analogue of
`.claude/settings.json`'s `hooks: { PreToolUse: [{ matcher, hooks: [{ type, command }] }] }`
block). No excerpt in the matrix shows this registration-syntax shape. §7's own "Divergences /
Silences" section confirms `WebFetch` is blocked in this sandbox (TLS-interception error, three
attempts, all URLs) — live re-fetch of the manual's config-file-syntax section is not currently
possible from this environment.

**Confirmed: the exact `.codex/config.toml` hook-registration schema is not yet known/documented
in this repo.** This is a real open unknown, not an oversight — resolving it requires either (a)
the real fixture-capture experiment (§5 above, deferred to this ticket's Implement phase) actually
writing and testing a scratch `.codex/config.toml`, or (b) a successful live re-fetch of the
manual's config-file section (currently blocked). This directly constrains what `plan.md` can
specify: it can state the *requirements* the eventual `.codex/` config must satisfy (minimal,
explicit trust; no production hook enabled; matcher scoped to only the events the first slice
needs) but **cannot** specify exact file content today. See Risks/Open Questions #4.

### 7. agent-monitoring append-only-diff verification — existing precedent, and why it doesn't transfer directly

Three related precedents exist:

- `tools/agent-monitoring/manifest.py` (read in full): a read-only, line-lazy scanner producing
  `{file, line_count, byte_size, sha256, parser_result, legacy_warning_count}` per
  `agent-monitoring/{runs,events,tools}.jsonl`. Computes a **whole-file** SHA-256 (streamed via
  per-line `hasher.update(line_bytes)`), not a per-line or prefix hash. Never writes into
  `agent-monitoring/` itself (`_assert_safe_output_path` refuses that). This is the natural
  building block to extend/reuse for this ticket's append-only proof, but as written it only
  supports whole-file equality checks, not prefix/append-only checks.
- `tests/agent_replay/test_no_mutation_snapshot.py` (read in full): the closest **test-shape**
  precedent — porcelain-snapshot-if-clean, else whole-file content-hash-snapshot-fallback,
  asserting **pre-hash == post-hash** (i.e., zero diff, not append-only) across
  `tickets/*`, `agent-monitoring/*.jsonl`. Its own docstring explains *why* it needed the
  hash-fallback: this repo's tree (including `agent-monitoring/*.jsonl`) is routinely dirty/being
  appended to during real development, so a naive "must be clean before" gate would false-skip
  almost every real run — the same environmental fact this ticket's own AC lives inside.
- **Why the existing pattern doesn't transfer as-is:** that precedent proves **zero** diff for a
  narrow, synchronous `replay_slice()` call that itself never writes to monitoring files (enforced
  separately by `test_runner_no_forbidden_calls.py`'s AST guard). This ticket's containment action
  runs *inside* a live `implement-ticket` workflow execution, which **will** legitimately append
  new `runs.jsonl`/`events.jsonl`/`tools.jsonl` records of its own before/after/during the
  containment step (monitoring writes are not disabled for this ticket the way they are for the
  replay proof). A whole-file equality check would therefore be **guaranteed to fail** on any real
  run — the AC's own wording ("append-only diff, i.e. zero rewritten/reordered/deleted lines")
  already anticipates this and asks for the weaker, correct invariant: pre-existing lines must
  survive **unchanged and in original order**; new lines may be appended after them. No existing
  test or tool in this repo currently implements this weaker "is-a-prefix" check — it needs new,
  small tooling (most naturally: snapshot line-count + whole content immediately before/after only
  the containment step itself — not the whole ticket's execution — then assert
  `post_lines[:len(pre_lines)] == pre_lines`).

## Mechanics / Engine Constraints

Not applicable. This ticket touches only `agent-orchestration/` tooling, `.agents/`, `.codex/`,
and root `AGENTS.md` — no `src/` simulation code, no `docs/mechanics/` chapter, no `docs/engine/`
contract governs this subsystem, exactly as the two predecessor tickets in this batch
(`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`, `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`) already
established.

## Parity Ledger Overlap

None found. `docs/parity_ledger/infrastructure.yaml` was checked (grep for
`orchestrat|codex|agents_dir|skills\.yaml|SKILL\.md`) — the only hits are unrelated
`CampaignOrchestrator`/`LabOrchestrator` simulation-domain entries and existing
`implement-ticket.js` gate-check entries (`run_finalize_selfcheck`, workflow-orchestrator wiring),
none of which concern the `agent-orchestration/` contract, Codex, or `.agents/skills/`. No P0
entry anywhere references this subsystem. This is consistent with both predecessor tickets'
own "not applicable" parity findings — this ticket should not need a parity ledger entry either,
since it makes no `src/`-visible behavior change.

## Prior Work

- **`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`** (DONE, `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/`):
  built the six `agent-orchestration/` files this ticket consumes as its generation source, plus
  `tools/agent_orchestration/{loader,generator,errors}.py` and
  `tests/agent_orchestration/test_validator_no_network_calls.py` (the AST write/network-call guard
  + `_SCOPE_CREEP_MARKERS` precedent that ticket 3/7's `test_no_codex_scope_creep.py` mirrors).
- **`TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`** (DONE, `stored_artifacts/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER/`):
  built `tools/agent_orchestration_claude_adapter/` (the sibling, not-a-template, YAML-shaped
  generator this ticket must not mimic in output format) and
  `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` (the test this ticket
  must fix — see Current Behavior §4). Its own investigation.md is the direct structural precedent
  this document follows.
- **`TCK-20260721-AGENTS-DIR-DISPOSITION`** + its two follow-on fix tickets
  (`TCK-20260721-AGENTS-DISPOSITION-FIX`, `TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX`):
  produced `docs/ai/agents_dir_disposition.md`, the authoritative classification and containment
  law this ticket must implement (Current Behavior §1).
- **`TCK-20260721-CODEX-CAPABILITY-MATRIX`** (DONE): produced `docs/ai/codex_capability_matrix.md`,
  the source for hook I/O contract, project-trust behavior, and the explicit "deferred" note
  naming this ticket's fixture-capture obligation (Current Behavior §5, §6).
- **`TCK-20260721-CODEX-REPLAY-PROOF`** (DONE): built `tools/agent_replay/` +
  `docs/ai/replay_fixture_spec.md` + `tests/agent_replay/test_no_mutation_snapshot.py` — a
  **different** fixture concern (phase-slice replay, not hook-payload capture) but the closest
  existing precedent for both "committed YAML fixture under `tests/fixtures/`" and "zero-mutation
  proof against the real repo tree" (Current Behavior §7).
- **`tests/unit/lab_agent/test_workflow_registry.py`** (confirmed by direct read,
  `grep -n "\.agents\|fixtures"`): already decoupled from live `.agents/workflows/` and
  `.agents/skills/` (per `TCK-20260721-AGENTS-DIR-DISPOSITION`'s "Test-pairing note") — it now
  reads `tests/unit/lab_agent/fixtures/agents_workflows/*.md` and an empty
  `tests/unit/lab_agent/fixtures/agents_skills/`. **This ticket's containment action will not break
  this test** — confirmed directly, not assumed.

## Risks and Open Questions

1. **BLOCKING for Plan — containment mechanism (quarantine vs. atomic replace) is not chosen.**
   `docs/ai/agents_dir_disposition.md` names both as valid; the review-response doc only narrows
   the requirement to "archived reviewable copy outside discovery path" + "atomic or otherwise
   recoverable". Plan must pick one concretely (e.g., "quarantine: `git mv .agents/skills
   docs/archive/legacy_agents_skills_20260722/`, then generate a fresh, empty-until-populated
   `.agents/skills/` from the contract" vs. "atomic replace: write the new catalog to a staging
   path, then a single `os.rename()` swap, with the pre-swap tree preserved as a byte-identical
   copy under a non-discoverable path") and specify the exact source/destination paths, since
   Codex (the external implementer) will follow `plan.md` literally.

2. **BLOCKING for Plan — `SKILL.md` body-content source is undefined.** `skills.yaml` carries only
   `id`/`description` (one line) per entry, no instructional body. Plan must decide where each
   generated `.agents/skills/<id>/SKILL.md`'s full body comes from — candidates: (a) pull the full
   body verbatim from the matching `.claude/skills/<id>/SKILL.md` (since all 16 `skills.yaml` ids
   have a 1:1 `.claude/skills/` counterpart, confirmed above), treating Claude's own skill body as
   the shared canonical instruction text with only frontmatter re-shaped for Codex's schema; or
   (b) generate a minimal `SKILL.md` with just `name`/`description` frontmatter (satisfying
   Codex's stated minimum schema per `codex_capability_matrix.md` §5) and no body, deferring full
   parity to a later ticket. This is a real design decision, not something Investigate should
   assume.

3. **BLOCKING for Plan — `test_no_dot_codex_directory_exists_in_repo` must be resolved.** Confirmed
   in Current Behavior §4: this repo-wide, unconditional assertion will fail the moment this
   ticket's own `.codex/` directory lands. Do not leave this to break silently at Implement time.
   Concrete resolution options for Plan to choose between (not decided here):
   - (a) **Delete** the test function outright — its premise ("no `.codex/` ever, anywhere, full
     stop") is now obsolete once a legitimate `.codex/` producer ticket exists; the sibling marker-
     scan test in the same file remains sufficient to guard ticket 3/7's own delivered tree.
   - (b) **Narrow** it to assert something still true and still useful post-this-ticket — e.g. "no
     *production* hook is enabled in `.codex/config.toml`" (mirrors this ticket's own AC #6
     directly) or "`.codex/` contains no conformance-diff/adapter Python code" (mirrors the marker
     scan's existing vocabulary, moved from absence-of-directory to absence-of-content).
   - (c) **Relocate/rename** it into this ticket's own test tree as a positive assertion about
     what `.codex/` legitimately contains, retiring the old negative assertion from ticket 3/7's
     tree entirely.
   Whichever option Plan picks, it is a change to a file this ticket does not otherwise own
   (`tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py`, delivered by ticket
   3/7) — Plan should say so explicitly rather than silently editing an unrelated ticket's test
   file without acknowledgment.

4. **The `.codex/config.toml` hook-registration schema is confirmed unknown today, not merely
   unresearched.** Confirmed in Current Behavior §6: the capability matrix documents the hook I/O
   *payload* contract in detail but not the config *registration* syntax, and `WebFetch` is
   sandbox-blocked for a fresh manual re-fetch. Plan **cannot** specify literal `.codex/config.toml`
   content in advance — it should instead specify the *requirements* the eventual scratch-then-real
   config must satisfy (minimal explicit trust, matcher scoped to only the first slice's needed
   events, zero production hooks enabled), and explicitly delegate discovering the literal syntax
   to the real fixture-capture experiment performed during Implement (by Codex, per the launching
   agent's workflow note) — not assume or fabricate a schema now.

5. **Real hook-payload capture consumes real API usage under the user's authenticated Codex
   account.** This ticket's own "Assumptions / Open Questions" section already flags this and
   requires consent before running. Given the workflow note that Codex CLI (not Claude) performs
   Implement, this consent step is Codex's own responsibility during its Implement phase, not
   something Claude's Plan/Review can grant on the user's behalf — Plan should make this consent
   checkpoint an explicit, named step in the implementation sequence (not an implicit assumption
   folded into a larger step), so Codex cannot skip it silently.

6. **The "17-phase" AC citation targets the wrong file** (Current Behavior §3). Not blocking, but
   Plan's phrasing of this specific AC item should be corrected so the external implementer isn't
   sent looking for text that was never in `.agents/rules/AGENTS.md` to begin with.

7. **The append-only-diff proof needs new, purpose-built tooling** (Current Behavior §7) — the
   existing zero-diff precedent (`test_no_mutation_snapshot.py`) proves a *stronger*, wrong
   invariant for this ticket's actual situation (a live workflow execution that legitimately
   appends to the same files being protected). Plan must specify the narrower "is-a-prefix" check
   and the exact before/after snapshot boundary (immediately around the containment action itself,
   not the whole ticket's execution) rather than reusing the existing test's exact assertion.

## Anti-Drift Hazards

- **Do not let the containment action touch `docs/ai/agents_dir_disposition.md`'s per-item
  classification.** That doc's per-path table (archive-retire vs. retain-and-migrate) is a decision
  record already landed by a different, closed ticket; this ticket executes the *containment*
  (moving/archiving the whole tree off Codex's discovery path) but must not re-litigate or edit
  the classification itself, and must not silently promote any of the 6 `retain-and-migrate` dirs'
  content into the new Codex catalog (they are not in `skills.yaml`; leaving them out of the
  generated catalog is correct, expected behavior per the disposition doc's own deferral, not a
  bug to "fix" here).
- **Do not enable any production Codex hook.** Every doc in this chain (ticket AC, disposition doc,
  capability matrix, implementation plan Phase 2 exit criteria) repeats this as a hard boundary:
  fixture-capture and minimal trust config only, zero production wiring. A verification step must
  explicitly check `.codex/` config state at ticket close for this, per this ticket's own AC #6.
- **Do not conflate this ticket's fixture-capture concern with `replay_fixture_spec.md`'s envelope**
  (Current Behavior §5) — they are different fixture formats for different purposes; don't reuse
  `phases:`/`transition:` YAML shape for a raw hook-`stdin`-payload capture fixture.
- **Do not silently edit `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py`
  without flagging it** — it's owned by a different, closed ticket (3/7); any change here is a
  cross-ticket edit that must be called out explicitly in `plan.md` and `Files Changed`, not
  treated as this ticket's own new test file.
- **Do not fabricate `.codex/config.toml` schema content** to make Plan look more complete than the
  actual state of knowledge — Risk #4 is real and must stay flagged, not quietly resolved by
  guessing a plausible-looking TOML shape.
- **Do not let the new Codex-adapter generator write outside `agent-orchestration/`, `.agents/`,
  root `AGENTS.md`, or `.codex/` without an explicit opt-in flag** — mirror the existing
  `_assert_write_allowed`/`GeneratorWriteGuardError` structural write-guard pattern from
  `tools/agent_orchestration/generator.py:28-37`, which both sibling generators already follow.
