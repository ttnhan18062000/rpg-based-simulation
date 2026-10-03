---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
artifact_type: plan
tags: [ai, workflows, process-improvement, hooks, skills]
---

# Implementation Plan — TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE

> **READ THIS FIRST.** Claude performed Investigate/Plan/Review for this ticket. Every step below
> — all code, all config, and the real Codex CLI fixture-capture experiment — is executed
> **externally by Codex CLI, run directly by the human operator**, working from this document
> alone. Nothing in this file assumes you have access to the conversation that produced it. Every
> file path, command, and decision rationale needed to execute this plan is written out explicitly
> below. If something is genuinely undetermined (there is exactly one such point — the literal
> `.codex/config.toml` hook-registration TOML syntax, see Step 11), this document says so plainly
> and tells you how to discover it; it does not ask you to guess.
>
> Step 10 is a hard, non-skippable checkpoint: it consumes real Codex API usage under the human
> operator's own account and requires them to run commands themselves. Do not proceed past Step 10
> until the human operator has confirmed, in their own words, that they ran it and the captured
> payload looks right.

## Summary

This ticket replaces the legacy, Codex-auto-discoverable `.agents/skills/` tree (18 hand-written
`SKILL.md` files) with a fresh catalog generated from the validated `agent-orchestration/`
contract, adds a corrected root `AGENTS.md` generated the same way, and captures a real Codex CLI
hook-payload fixture via an isolated scratch-directory experiment — all without ever enabling a
production Codex hook. The approach: (1) quarantine the legacy tree with a single atomic `git mv`
into `docs/archive/`, bracketed by a new append-only-diff check on `agent-monitoring/*.jsonl`; (2)
build a new `tools/agent_orchestration_codex_adapter/` generator package (sibling to, not a copy
of, the existing `tools/agent_orchestration/` and `tools/agent_orchestration_claude_adapter/`
packages) that renders root `AGENTS.md` and per-skill `SKILL.md` files purely from
`load_contract()` output plus each skill's existing `.claude/skills/<id>/SKILL.md` body; (3) run
the real fixture-capture experiment in a directory entirely outside this repo, after an explicit
human-consent checkpoint, and commit only the captured JSON payload (not the scratch
`.codex/config.toml`) as a fixture; (4) commit a repo-side `.codex/config.toml` that contains zero
hook registrations by construction; (5) narrow (not delete) the now-conflicting
`test_no_dot_codex_directory_exists_in_repo` test owned by a different, closed ticket, flagged
explicitly as a cross-ticket edit.

## Decisions (resolving the 5 blocking questions from investigation.md)

These are final decisions for this plan, not options for the implementer to choose between.

1. **Containment mechanism: quarantine via `git mv`.** Run
   `git mv .agents/skills docs/archive/legacy_agents_skills_20260722/` as a single command. This
   is one atomic filesystem/git operation, preserves full git blame/history for all 18 files
   (strictly better than copy+delete), and produces a byte-identical reviewable copy at a path
   `docs/archive/legacy_agents_skills_20260722/` that is never on Codex's `.agents/skills`
   upward-from-cwd discovery walk (per `codex_capability_matrix.md` §5) — no ancestor directory of
   that path is ever named `.agents/skills`. A fresh `.agents/skills/` is then populated by the
   new generator (Step 5), strictly after the `git mv` completes (see Dependency Map).

2. **`SKILL.md` body-content source: pull the body verbatim from `.claude/skills/<id>/SKILL.md`.**
   All 16 `skills.yaml` ids have a confirmed 1:1 `.claude/skills/<id>/SKILL.md` counterpart. The
   generator re-shapes only the frontmatter (`name` = the skill's `id`, `description` =
   `skills.yaml`'s `description` field verbatim — **not** `.claude`'s own frontmatter description,
   which is worded differently for several skills, e.g. `brainstorming`). The instructional body
   is copied verbatim, unmodified. This treats Claude's skill body as the one shared canonical
   instruction text, now also generated into Codex's format, not a second independently-authored
   copy.

   **Amendment (blocker correction, discovered during Implement, 2026-07-22 — dual source-shape
   policy):** the original wording above assumed every `.claude/skills/<id>/SKILL.md` has a
   leading YAML frontmatter block to strip. This is false for 4 of the 16 ids — confirmed by
   direct check of every file's first line:
   `create-tickets`, `implement-epic`, `implement-ticket`, and `simq-audit` all begin directly
   with a Markdown heading (e.g. `# create-tickets`), no leading `---` frontmatter at all. (Codex's
   blocker report cited `create-tickets` as its example; the other 3 were found by an independent
   full sweep of all 16 sources during this review, not by Codex — all 4 need the same handling.)
   The body-extraction rule is therefore amended to a **dual-shape policy**:
   - If the source `SKILL.md` begins with a `---\n...\n---\n` frontmatter block, preserve only its
     body (everything after the closing `---`), exactly as originally specified.
   - If the source `SKILL.md` has no leading frontmatter, preserve the **entire file content** as
     the body, unmodified.
   - In both cases, the generated Codex `SKILL.md`'s frontmatter (`name`/`description`) always
     comes from `skills.yaml`, never from the Claude source file's own frontmatter (if any) — this
     was already the rule and is unaffected by which body-extraction branch fires. Semantic
     authority for frontmatter stays the validated contract, not Claude-side metadata, regardless
     of source shape.
   This is a body-extraction implementation detail, not a change to the underlying policy
   (Claude's skill content is still the one shared canonical instruction source) — no `.claude/`
   file is modified to accommodate this, and the ticket's no-`.claude/`-edits scope guard is
   unaffected. See Step 5 for the exact extractor logic and Step 6 for the required test coverage
   of both shapes.

3. **`test_no_dot_codex_directory_exists_in_repo`: narrow it (option b).** Replace the
   unconditional "no `.codex/` may exist" assertion with: if `.codex/config.toml` exists, parse it
   with the stdlib `tomllib` module (available — this repo requires Python >=3.11, confirmed) and
   recursively walk every table/array in the parsed structure; fail if any table anywhere (at any
   nesting depth) contains a key literally named `hooks`. This is schema-agnostic (does not
   presuppose the still-unknown hook-registration TOML syntax) and directly enforces "zero
   production-facing hook entries." See Step 9 for the exact code. This is a cross-ticket edit to
   `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py`, owned by
   `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER` (closed) — flagged explicitly, not silent. The
   sibling test in the same file, `test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree`,
   is **not** touched (confirmed by investigation: its scanned paths never overlap this ticket's
   new files).

4. **`.codex/config.toml` schema: requirements only, discovered empirically at Step 11.** This
   plan does not fabricate literal TOML hook-registration syntax — it is confirmed genuinely
   unknown (capability matrix documents the hook `stdin` payload contract but not the config
   registration syntax, and WebFetch is sandbox-blocked). The plan instead pins the requirements
   the eventual config must satisfy (Step 11/13) and — because the requirement is "zero production
   hooks enabled" — resolves the tension by having the **committed** `.codex/config.toml` contain
   no hook-shaped content at all (see Step 13). The scratch experiment's own throwaway config
   (which *does* need real hook-registration syntax to run the experiment) is never committed;
   only the captured JSON payload is.

5. **Real-API-usage consent: its own named, non-skippable step — Step 10.** See Step 10 below. It
   is not folded into the fixture-capture step; the fixture-capture step (Step 11) cannot begin
   until Step 10 is independently satisfied.

**AC wording correction (non-blocking, per investigation finding #6):** the ticket's AC bullet
"Root AGENTS.md exists and is verifiably NOT a copy of the stale `.agents/rules/AGENTS.md` draft
(e.g. does not repeat the confirmed 17-phase pipeline drift...)" is imprecise: `.agents/rules/AGENTS.md`
contains no phase-count text at all (confirmed: `grep -n "phase\|17\|32" .agents/rules/AGENTS.md`
→ zero hits). The real 17-phase-vs-32-phase drift lives in a **different** file,
`.agents/rules/authoritative_mechanics.md:18`. This plan implements the AC's real intent as: the
new root `AGENTS.md` must (a) not be a copy of `.agents/rules/AGENTS.md`, and (b) must positively
state the real 32-phase authoritative mutation pipeline, sourced from
`docs/engine/authoritative_pipeline.md:11` ("refined through these 32 phases"), independent of
which stale file the wrong number originally came from. See Step 6/8.

## Steps

### Step 1 — Verify entry criterion: the contract has landed

**Files:** none changed. Read-only verification of `agent-orchestration/contract.yaml`,
`agent-orchestration/workflows/implement-ticket.yaml`, `agent-orchestration/roles/*.yaml`,
`agent-orchestration/skills.yaml`, `agent-orchestration/monitoring-schema.yaml`,
`agent-orchestration/hook-events.yaml`, and `tools/agent_orchestration/loader.py`.

**Change:** From the repo root, run:

```
python3 -c "from pathlib import Path; from tools.agent_orchestration.loader import load_contract; load_contract(Path('.')); print('contract OK')"
```

This must print `contract OK` and exit 0, with no `ContractValidationError` raised. This confirms
`TCK-20260721-ORCHESTRATION-CONTRACT-CORE` (a prerequisite ticket, already DONE per
`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/`) has genuinely landed a loadable
contract before any generation work begins — this is the ticket's AC #1 and AC #8 hard entry
gate. Do not proceed to Step 3 or later until this command succeeds.

**Do NOT touch:** any of the six `agent-orchestration/` contract files, or
`tools/agent_orchestration/{loader,generator,errors}.py` — this step is read-only verification
only.

**Verify:** the command above exits 0 and prints `contract OK`.

---

### Step 2 — Build append-only monitoring-snapshot tooling

**Files:** `tools/agent-monitoring/manifest.py` (extend, do not rewrite);
new `tests/agent_orchestration_codex_adapter/__init__.py` (empty file, new test package);
new `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`.

**Change:** Add two new functions to `tools/agent-monitoring/manifest.py`, alongside the existing
`_scan_file`/`build_manifest` functions (do not modify those):

```python
def capture_lines(agent_monitoring_dir: Path) -> dict[str, list[str]]:
    """Read raw lines from each of runs.jsonl/events.jsonl/tools.jsonl exactly as they exist on
    disk right now, in original order. Read-only — never writes, never parses/mutates content."""
    result: dict[str, list[str]] = {}
    for filename in _FILES_BY_SOURCE:
        path = agent_monitoring_dir / filename
        with open(path, "r", encoding="utf-8") as f:
            result[filename] = f.readlines()
    return result


def assert_prefix_preserved(pre: dict[str, list[str]], post: dict[str, list[str]]) -> None:
    """Raise AssertionError if any pre-existing line captured in `pre` was rewritten, reordered,
    or deleted in `post`. New lines appended strictly after `pre`'s recorded length are allowed —
    this is the correct invariant for a live workflow execution that legitimately appends to these
    files during the same run that also performs the containment action (unlike
    tests/agent_replay/test_no_mutation_snapshot.py's stronger, wrong-for-this-case zero-diff
    check)."""
    for filename, pre_lines in pre.items():
        post_lines = post.get(filename, [])
        prefix = post_lines[: len(pre_lines)]
        if prefix != pre_lines:
            raise AssertionError(
                f"{filename}: pre-existing lines were rewritten/reordered/deleted "
                f"(pre-snapshot had {len(pre_lines)} lines; post-snapshot's prefix does not match)"
            )
```

Add a new committed unit test, `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`,
that proves these two functions are correct in isolation (it does **not** re-run the real
containment event — that already happened once, historically, in Step 4, and cannot be
retroactively re-executed by a pytest run):

- `test_assert_prefix_preserved_passes_when_only_appended(tmp_path)` — write a 2-line file, call
  `capture_lines`, append a 3rd line to the file, call `capture_lines` again, assert
  `assert_prefix_preserved(pre, post)` does not raise.
- `test_assert_prefix_preserved_fails_when_a_line_is_rewritten(tmp_path)` — same setup, but mutate
  line 1's content before the second capture; assert `assert_prefix_preserved` raises
  `AssertionError`.
- `test_assert_prefix_preserved_fails_when_a_line_is_reordered(tmp_path)` — same setup, but swap
  lines 1 and 2 before the second capture; assert it raises.
- `test_capture_lines_reads_all_three_monitoring_files` — call `capture_lines` against the real
  `agent-monitoring/` directory (`Path(__file__).parent.parent.parent / "agent-monitoring"`) and
  assert the returned dict has exactly the keys `{"runs.jsonl", "events.jsonl", "tools.jsonl"}`.

Import both new functions via `sys.path` insertion matching `manifest.py`'s own existing pattern
(`tools/agent-monitoring/` is not an importable package name in Python — it has a hyphen — so tests
must add its directory to `sys.path` the same way `manifest.py` itself does for `legacy_reader`, or
use `importlib.util.spec_from_file_location`; do not rename the `tools/agent-monitoring/` directory
to make it import cleanly — that is out of scope and would break every existing caller).

**Do NOT touch:** `tools/agent-monitoring/legacy_reader.py`, `tools/agent-monitoring/post_tool_hook.py`,
or any other file under `tools/agent-monitoring/` besides `manifest.py`. Do not modify
`_scan_file`, `build_manifest`, `_assert_safe_output_path`, or `main` in `manifest.py` — only add
the two new functions.

**Verify:** `pytest tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py -v`
— all new tests pass.

---

### Step 3 — Legacy skills containment (quarantine via `git mv`)

**Files:** `.agents/skills/` (moved, not edited), `docs/archive/legacy_agents_skills_20260722/`
(new, via move).

**Change:** This is a procedural step executed in this exact order:

1. Compute and record the sha256 of each of the 18 existing files, e.g.:
   ```
   sha256sum .agents/skills/*/SKILL.md
   ```
   Record all 18 `filename → hash` pairs — you will hardcode them as literal expected values into
   the new test in Step 4. Do this **before** anything else in this step.
2. Capture the pre-containment monitoring snapshot using Step 2's new tooling — a small one-off
   Python invocation is sufficient, e.g.:
   ```
   python3 -c "
   import sys, json
   sys.path.insert(0, 'tools/agent-monitoring')
   from manifest import capture_lines
   from pathlib import Path
   pre = capture_lines(Path('agent-monitoring'))
   json.dump({k: len(v) for k, v in pre.items()}, sys.stdout)
   "
   ```
   Save the actual line lists (not just counts) in memory or a local variable/scratch file
   **outside the repo** (e.g. `/tmp/codex-guidance-precontainment-snapshot.json` — this file must
   never be committed; it is a procedural safety check, not a deliverable).
3. Run the containment command:
   ```
   git mv .agents/skills docs/archive/legacy_agents_skills_20260722/
   ```
4. Immediately capture the post-containment monitoring snapshot the same way, and call
   `assert_prefix_preserved(pre, post)`. **This must pass before you proceed to any later step.**
   If it raises, STOP — do not continue this ticket's work; investigate what wrote to
   `agent-monitoring/*.jsonl` between steps 2 and 4 before proceeding.
5. In this ticket's `## Implementation Notes` section (in `tickets/inprogress/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`),
   record: the pre- and post-snapshot line counts for each of the three files, and a one-line
   confirmation that `assert_prefix_preserved` passed. This is the durable evidence for AC #7,
   since the live check itself cannot be re-run after the fact.

**Do NOT touch:** `docs/ai/agents_dir_disposition.md` (its per-item classification table is a
closed decision record from a different ticket — this step executes the containment law it
states, it does not re-litigate or edit the classification itself). Do not create, populate, or
write anything new into `.agents/skills/` in this step — that happens only in Step 5, strictly
after this step completes. Do not touch any file under `.agents/rules/`.

**Verify:** `git status` shows `.agents/skills/` gone and `docs/archive/legacy_agents_skills_20260722/`
present with exactly 18 subdirectories, each containing one `SKILL.md`; `git log --follow docs/archive/legacy_agents_skills_20260722/brainstorming/SKILL.md`
shows history carried over from the pre-move path.

---

### Step 4 — Legacy tree containment tests

**Files:** new `tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py`.

**Change:** Add two tests:

1. `test_no_stale_skill_md_on_codex_discovery_path()` — asserts no `SKILL.md` file exists at
   `.agents/skills/**/SKILL.md` relative to the repo root (Codex's documented discovery walk per
   `codex_capability_matrix.md` §5 is `.agents/skills` from cwd up to repo root — the repo-root
   case is the one this test can directly assert). At the point this test runs (after Step 5 has
   also run), `.agents/skills/` will exist again, freshly populated by the new generator — this
   test must therefore assert something narrower and still true: that none of the files currently
   under `.agents/skills/**/SKILL.md` are byte-identical to any of the 18 originally-archived
   files (i.e., the *stale* content specifically is gone, not that the directory itself is empty).
   Compare via the hardcoded sha256 list from test #2 below: assert none of those 18 hashes appear
   among the sha256 hashes of whatever `SKILL.md` files currently exist under `.agents/skills/`.
2. `test_archived_copy_exists_and_is_byte_identical()` — for each of the 18 filenames recorded in
   Step 3.1, assert `docs/archive/legacy_agents_skills_20260722/<name>/SKILL.md` exists and its
   sha256 matches the hardcoded expected hash recorded in Step 3.1 exactly. Hardcode the 18
   `name: expected_sha256` pairs as a module-level dict literal in this test file, computed from
   the values you captured in Step 3.1 — do not compute them from any live source at test-run time
   (the whole point is proving fidelity against the pre-containment snapshot, not re-deriving it).
3. `test_archived_copy_is_not_on_codex_discovery_path()` — asserts
   `docs/archive/legacy_agents_skills_20260722/` is never named or nested such that any ancestor
   directory literally equals `.agents/skills` — i.e. walk up from the archive path and assert no
   ancestor's basename pair is `("skills", ".agents")` in sequence. This directly guards against a
   "quarantine to a still-discoverable nested path" mistake (e.g. an accidental
   `.agents/skills/_archive/` instead).

**Do NOT touch:** `tests/unit/lab_agent/test_workflow_registry.py` or its fixtures under
`tests/unit/lab_agent/fixtures/` — confirmed by investigation to already be decoupled from the
live `.agents/skills/` tree; this ticket's containment action does not require any change there.
Run it as a regression check only (see Step 14).

**Verify:** `pytest tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py -v`
— all three tests pass. Must be run **after** Step 5 (the generator has repopulated
`.agents/skills/`) for test #1's comparison to be meaningful; see Dependency Map.

---

### Step 5 — Build the new Codex-adapter generator package

**Files:** new `tools/agent_orchestration_codex_adapter/__init__.py`,
new `tools/agent_orchestration_codex_adapter/errors.py`,
new `tools/agent_orchestration_codex_adapter/generator.py`.

**Change:**

`errors.py` — one new exception, mirroring `tools/agent_orchestration_claude_adapter/generator.py`'s
own independent-exception-class pattern (do not import or subclass
`tools.agent_orchestration.errors.GeneratorWriteGuardError` or
`tools.agent_orchestration_claude_adapter.generator.ClaudeAdapterWriteGuardError` — each sibling
package owns its own error type):

```python
class CodexAdapterWriteGuardError(Exception):
    """Raised when a write target resolves outside the allowed Codex-adapter output set
    (repo root AGENTS.md, .agents/skills/) and allow_outside_contract=True was not passed."""


class CodexAdapterMissingSkillSourceError(Exception):
    """Raised when a skills.yaml entry's id has no matching .claude/skills/<id>/SKILL.md file to
    pull the instructional body from. Fails loudly rather than silently emitting a bodyless
    SKILL.md."""
```

`generator.py` — read `tools.agent_orchestration.loader.load_contract()` (reuse, do not
reimplement, exactly matching the reuse pattern both sibling generators already follow):

- `_assert_write_allowed(repo_root, target_path, allow_outside_contract)`: **resolve `target_path`
  with `.resolve()` first** (mirrors the claude-adapter generator's own `.resolve()` +
  `is_relative_to()` technique — do not compare unresolved/relative paths, which a crafted or
  malformed `id` could use to escape the intended directory). Allowed targets (when
  `allow_outside_contract=False`) are exactly `repo_root.resolve() / "AGENTS.md"` and anything
  whose resolved path `is_relative_to(repo_root.resolve() / ".agents" / "skills")`. Raise
  `CodexAdapterWriteGuardError` otherwise. Regardless of `allow_outside_contract`'s value,
  **hard-deny** (always raise, no override) any target whose resolved path
  `is_relative_to(repo_root.resolve() / ".claude")` or
  `is_relative_to(repo_root.resolve() / ".codex")` — this generator never writes to either
  directory under any flag combination, mirroring the claude-adapter generator's "never targets
  `.claude/`" hard exception.
- **`id` validation (Review-phase required fix — path-traversal guard):** before constructing any
  per-skill target path, `render_codex_guidance` must validate each `skills.yaml` entry's `id`
  against a simple-name pattern (e.g. `re.fullmatch(r"[a-z0-9][a-z0-9-]*", id)` — matches the
  existing convention of every real `skills.yaml` id) and raise `CodexAdapterWriteGuardError` for
  any `id` that contains `/`, `\`, `..`, or otherwise fails that pattern, **before** calling
  `_assert_write_allowed` on the constructed path. This is defense in depth: `_assert_write_allowed`'s
  `is_relative_to()` check (above) would already catch an escaping path after resolution, but
  validating the `id` shape directly gives a clearer error message and fails before any path
  construction happens at all. `agent-orchestration/skills.yaml`'s loader currently enforces no
  character/format constraint on `id` — this generator must not assume upstream validation exists.
- `_extract_body(claude_skill_md_text: str) -> str`: **dual-shape policy (Decision #2 amendment)**
  — if `claude_skill_md_text` begins with a `---\n...\n---\n` frontmatter block (starts with `---`
  as its first line), split on the first two `---` delimiters and return everything after the
  second `---`, unmodified, including its leading newline(s). If the text does **not** begin with
  `---` as its first line, return the entire text unmodified — this is not an error case; several
  real `.claude/skills/<id>/SKILL.md` sources (confirmed: `create-tickets`, `implement-epic`,
  `implement-ticket`, `simq-audit`) are plain Markdown with no frontmatter at all, and their full
  content is the body.
- `build_codex_skill_md(repo_root: Path, skill_id: str, description: str) -> str`: read
  `repo_root / ".claude" / "skills" / skill_id / "SKILL.md"`; if it doesn't exist, raise
  `CodexAdapterMissingSkillSourceError(skill_id)`. Extract its body via `_extract_body`. Return:
  ```
  ---
  name: {skill_id}
  description: {description!r as a YAML-safe scalar, quoted the same way .claude/skills entries are}
  ---
  {body}
  ```
- `build_agents_md(repo_root: Path) -> str`: call `load_contract(repo_root)`, then render a
  Markdown document with these sections, each sourced as stated (do not invent additional
  contract-derived content beyond what's listed; do not omit any of these five sections):
  1. A title `# AGENTS.md` plus a one-line provenance note: "Generated by
     `tools/agent_orchestration_codex_adapter/generator.py` from the validated
     `agent-orchestration/` contract. Do not hand-edit — regenerate instead."
  2. `## Engine Authority` — a literal, hardcoded citation (module-level constant
     `_AUTHORITATIVE_PIPELINE_NOTE` in `generator.py`, see below) stating the real 32-phase
     authoritative mutation pipeline, citing `docs/engine/authoritative_pipeline.md`. This is the
     one section not derived from `load_contract()`'s bundle — the 32-phase engine fact lives in
     `docs/engine/`, not in `agent-orchestration/`'s ticket-workflow contract. Define it as:
     ```python
     _AUTHORITATIVE_PIPELINE_NOTE = (
         "All durable-state changes in this simulation are refined through the 32-phase "
         "authoritative mutation pipeline defined in `docs/engine/authoritative_pipeline.md` "
         "(the Singular Bottleneck Law: no system, worker, or external process may mutate "
         "`AuthoritativeState` directly; all changes are represented as a `StateUpdate` and "
         "refined through these 32 phases)."
     )
     ```
  3. `## Workflow: {bundle.workflow["workflow_id"]}` — the ordered list of
     `[p["name"] for p in bundle.workflow["phases"]]`, one per line.
  4. `## Roles` — one line per `bundle.roles` entry: `` `{role.role_id}` — {role.description} ``.
  5. `## Skills` — one line per `bundle.skills["skills"]` entry:
     `` `{id}` — {description} (see `.agents/skills/{id}/SKILL.md`) ``.
- `render_codex_guidance(repo_root: Path, target_repo_root: Path, *, allow_outside_contract: bool = False) -> list[Path]`:
  writes `target_repo_root / "AGENTS.md"` (content from `build_agents_md(repo_root)`) and, for
  every entry in `bundle.skills["skills"]`, writes
  `target_repo_root / ".agents" / "skills" / {id} / "SKILL.md"` (content from
  `build_codex_skill_md(repo_root, id, description)`). Returns the list of paths written. Note the
  two-`repo_root`-parameter shape (`repo_root` to read the contract/`.claude/skills` from,
  `target_repo_root` to write into) exists specifically so tests can point writes at `tmp_path`
  while still reading the real repo's contract — mirror
  `tools/agent_orchestration_claude_adapter/generator.py::render_claude_adapter`'s
  `(repo_root, target_dir)` two-parameter shape for the same reason.

**Do NOT touch:** `tools/agent_orchestration/{loader,generator,errors}.py`,
`tools/agent_orchestration_claude_adapter/*.py` — this package only imports
`tools.agent_orchestration.loader.load_contract`, it never edits either predecessor package.

**Verify:** module imports cleanly:
`python3 -c "from tools.agent_orchestration_codex_adapter.generator import render_codex_guidance"`.
Full behavioral verification happens in Step 6.

---

### Step 6 — Generator tests

**Files:** new `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py`,
new `tests/agent_orchestration_codex_adapter/test_generator_traceability.py`,
new `tests/agent_orchestration_codex_adapter/test_requires_valid_contract.py`.

**Change:**

`test_generator_write_guard.py` (mirrors
`tests/agent_orchestration_claude_adapter/test_generator_containment.py`'s write-guard pair):
- `test_render_codex_guidance_refuses_writes_outside_allowed_targets_without_flag(tmp_path)` —
  call `render_codex_guidance(_REPO_ROOT, tmp_path / "not_agents_md_or_skills")` without
  `allow_outside_contract`; assert it raises `CodexAdapterWriteGuardError` and nothing was written.
- `test_render_codex_guidance_allows_writes_outside_with_explicit_flag(tmp_path)` — same call with
  `allow_outside_contract=True`; assert it succeeds and both `AGENTS.md` and 16
  `.agents/skills/<id>/SKILL.md` files exist under `tmp_path`.
- `test_render_codex_guidance_never_targets_dot_claude_directory()` — call with
  `target_repo_root=_REPO_ROOT / ".claude" / "codex_scratch"` **and** `allow_outside_contract=True`;
  assert it still raises `CodexAdapterWriteGuardError` (the hard-deny applies regardless of the
  flag) and nothing was written.
- `test_render_codex_guidance_never_targets_dot_codex_directory()` — same, targeting
  `_REPO_ROOT / ".codex" / "codex_scratch"`; same assertion.
- `test_render_codex_guidance_rejects_path_traversal_skill_id(tmp_path, monkeypatch)` — build a
  `tmp_path` copy of the real `agent-orchestration/` tree with `skills.yaml` patched to include one
  malicious entry (e.g. `id: "../../etc"`), call `render_codex_guidance` pointed at that broken
  tree as its read-source `repo_root`; assert it raises `CodexAdapterWriteGuardError` (from the
  `id`-shape validation, Review-phase required fix in Step 5) and that nothing was written outside
  `tmp_path`'s target directory (assert no file exists at any resolved path outside the intended
  `.agents/skills/` target).

`test_generator_traceability.py` (mirrors
`test_generator_containment.py::test_build_claude_adapter_representation_derives_purely_from_load_paths`'s
technique):
- `test_every_generated_skill_id_and_description_traces_to_skills_yaml(tmp_path)` — run
  `render_codex_guidance(_REPO_ROOT, tmp_path, allow_outside_contract=True)`, then for every
  `skills.yaml` entry, parse the corresponding generated `.agents/skills/<id>/SKILL.md`'s
  frontmatter and assert `name == id` and `description == skills.yaml`'s `description` field
  **verbatim** (not `.claude/skills/<id>/SKILL.md`'s own frontmatter description, which differs in
  wording for several ids — assert this explicitly for at least `brainstorming`, where the two
  descriptions are known to differ).
- `test_generated_skill_body_matches_claude_skill_md_body(tmp_path)` — for at least
  `brainstorming` and `test-driven-development` (both frontmatter-bearing sources), assert the
  generated `.agents/skills/<id>/SKILL.md`'s body (everything after its frontmatter) is
  byte-identical to `.claude/skills/<id>/SKILL.md`'s own body (everything after its frontmatter).
- `test_generated_skill_body_matches_full_content_for_frontmatter_less_sources(tmp_path)`
  (**required, Decision #2 amendment**) — for all 4 confirmed frontmatter-less sources
  (`create-tickets`, `implement-epic`, `implement-ticket`, `simq-audit`), assert the generated
  `.agents/skills/<id>/SKILL.md`'s body is byte-identical to `.claude/skills/<id>/SKILL.md`'s
  **entire raw file content** (not "everything after frontmatter," since there is none to strip).
  This is the direct regression test for the blocker Codex found during Implement — without it,
  a future edit could silently reintroduce the frontmatter-only assumption for these 4 ids.
- `test_skills_yaml_sixteen_entry_set_is_not_expanded()` — assert
  `len(load_contract(_REPO_ROOT).skills["skills"]) == 16` and that none of the six
  `retain-and-migrate` legacy-only ids (`clean-code`, `codebase-search`, `code-review`,
  `create-skill`, `receiving-code-review`, `requesting-code-review`) appear among the generated
  `.agents/skills/` ids. This is the anti-drift guard from investigation.md's Anti-Drift Hazards —
  those 6 ids are explicitly deferred to a future promotion-review ticket, not this one.

`test_requires_valid_contract.py` (residual testable form of AC #1/#8):
- `test_render_codex_guidance_raises_on_missing_contract_file(tmp_path, monkeypatch)` — construct
  a `tmp_path` that is missing one required `agent-orchestration/` file (e.g. no `skills.yaml`),
  call `render_codex_guidance` pointed at that broken tree as its read-source `repo_root`, and
  assert it raises `ContractValidationError` (propagated from `load_contract`) rather than
  silently falling back to any hand-curated content. This proves the generator structurally cannot
  proceed without a valid contract.

**Do NOT touch:** the real `agent-orchestration/` files to construct the "broken tree" fixture in
`test_requires_valid_contract.py` — build the broken tree under `tmp_path` (copy the real files in,
then delete/corrupt one copy), never mutate the committed contract files themselves.

**Verify:** `pytest tests/agent_orchestration_codex_adapter/test_generator_write_guard.py tests/agent_orchestration_codex_adapter/test_generator_traceability.py tests/agent_orchestration_codex_adapter/test_requires_valid_contract.py -v`
— all pass.

---

### Step 7 — Materialize the real output: generate root `AGENTS.md` and `.agents/skills/`

**Files:** new `AGENTS.md` (repo root), new `.agents/skills/<id>/SKILL.md` × 16.

**Change:** Run the generator against the real repo root and commit its output:

```
python3 -c "
from pathlib import Path
from tools.agent_orchestration_codex_adapter.generator import render_codex_guidance
render_codex_guidance(Path('.'), Path('.'))
"
```

This must succeed with `allow_outside_contract` left at its default `False` — the real repo root
is inside the allowed target set (`AGENTS.md` at root, `.agents/skills/` — no override needed).
Inspect the output: root `AGENTS.md` should exist with the five sections specified in Step 5, and
`.agents/skills/` should contain exactly 16 subdirectories (the `skills.yaml` set), each with one
`SKILL.md`.

**Do NOT touch:** anything under `docs/archive/legacy_agents_skills_20260722/` (the archived
copy must remain exactly as `git mv` left it in Step 3 — do not re-run any generation step that
targets that path). Do not hand-edit the generated `AGENTS.md` or any generated `SKILL.md` after
this step — if content is wrong, fix `generator.py` (Step 5) and re-run this step, don't patch the
output directly (the whole point of AC #3 is traceable generation, not hand-curation).

**Verify:** `ls .agents/skills/ | wc -l` → `16`; `test -f AGENTS.md`. Re-run Step 4's tests now
(they depend on this step having run — see Dependency Map) and Step 6's tests (idempotency check:
re-running the generator against the real repo root a second time should produce byte-identical
output — not a required new test, but worth a manual sanity check here).

---

### Step 8 — Root `AGENTS.md` content correctness test

**Files:** new `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`.

**Change:** Add:
- `test_agents_md_is_not_a_copy_of_stale_draft()` — read both `AGENTS.md` (repo root) and
  `.agents/rules/AGENTS.md`; assert their contents are not equal and assert the new file's content
  is not a superstring/near-duplicate (a simple `assert stale_text not in new_text and new_text not in stale_text`
  is sufficient — do not build a fuzzy-diff similarity metric, that's over-engineering for this
  guard).
- `test_agents_md_states_32_phase_pipeline_not_17()` — assert `"17-phase" not in text` and
  `"17 phase" not in text`, and assert the literal substring `"32 phases"` (or `"32-phase"`) does
  appear, in the same paragraph as a reference to `docs/engine/authoritative_pipeline.md`.
- `test_agents_md_pipeline_note_matches_live_engine_doc()` — a forward-looking drift guard: read
  `docs/engine/authoritative_pipeline.md`, assert it still contains the string `"32 phases"` (i.e.
  this test fails loudly if a future ticket changes the real phase count without updating
  `generator.py`'s `_AUTHORITATIVE_PIPELINE_NOTE` constant to match).

**Do NOT touch:** `.agents/rules/AGENTS.md` or any other `.agents/rules/*.md` file — out of this
ticket's scope entirely (note for the record: `.agents/rules/engine_contracts.md:33` was found
during planning to *also* contain a stale "17-phase" reference, a second, separate, pre-existing
drift instance in a file this ticket does not touch — do not fix it here; it belongs to a future
cleanup ticket).

**Verify:** `pytest tests/agent_orchestration_codex_adapter/test_agents_md_generation.py -v` — all
pass.

---

### Step 9 — Cross-ticket edit: narrow the conflicting `.codex/` scope-creep test

**⚠ Cross-ticket edit — flagged explicitly.** This step modifies
`tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py`, a file delivered and
owned by the closed ticket `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER` (3/7 in this batch). This
edit is required because that ticket's own unconditional assertion ("no `.codex/` directory may
ever exist in this repo") is factually superseded the moment this ticket's own `.codex/`
directory legitimately lands (Step 13) — this repo's own investigation confirmed the conflict is
real and would otherwise cause a false regression failure in an unrelated ticket's delivered test
suite. Record this edit explicitly under this ticket's `Files Changed` in the ticket doc, with this
same rationale.

**Files:** `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py`.

**Change:** Replace only the `test_no_dot_codex_directory_exists_in_repo` function body. Do not
touch `test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree`, `_SCANNED_DIRS`,
`_SCANNED_FILES`, `_SCOPE_CREEP_MARKERS`, or `_all_scanned_paths` — those remain exactly as
delivered by ticket 3/7. New function body, exact code:

```python
def test_no_production_hook_registered_in_codex_config():
    """Replaces the prior unconditional 'no .codex/ directory may exist' assertion
    (superseded 2026-07-22 by TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE, this repo's own
    legitimate, scoped .codex/ producer — see that ticket's plan.md Decision #3). The guard
    that survives, still meaningful post-that-ticket: whatever .codex/config.toml this repo
    commits must register zero hooks, at any nesting depth, under any key name literally
    called 'hooks'. This is schema-agnostic by design — it does not presuppose the (still
    only partially documented) Codex hook-registration TOML syntax."""
    config_path = _REPO_ROOT / ".codex" / "config.toml"
    if not config_path.exists():
        return

    import tomllib

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    def _walk(node):
        if isinstance(node, dict):
            assert "hooks" not in node, (
                f"{config_path}: found a 'hooks' key — production hook wiring is forbidden "
                "in the committed project config"
            )
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(data)
```

Rename the function from `test_no_dot_codex_directory_exists_in_repo` to
`test_no_production_hook_registered_in_codex_config` (the old name no longer describes what it
asserts) and update the module docstring's second bullet to describe the new assertion instead of
the old one. Keep the docstring's first bullet (describing
`test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree`) unchanged.

**Do NOT touch:** anything in this file besides the one function (and its name) plus the docstring
paragraph describing it.

**Verify:** `pytest tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py -v` —
both tests pass, including the untouched
`test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree`.

---

### Step 10 — REAL-API-CONSENT CHECKPOINT (non-skippable)

**This step performs no file changes.** It is a hard gate on Step 11.

**What this step is:** the next step (Step 11) runs the real Codex CLI against a live scratch
directory, which consumes real API usage under the human operator's own authenticated Codex
account. This is not something Codex CLI (running unattended) may consent to on the operator's
behalf, and it is not something Claude's Investigate/Plan/Review phases could grant in advance —
this ticket's own `Assumptions / Open Questions` section flags exactly this.

**Required action:** the human operator must, in their own words, confirm they understand that
Step 11:
1. runs the real `codex` CLI (not a mock, not a dry-run) in a directory entirely outside this
   repository's working tree and outside this repository's git trust boundary;
2. consumes real API usage/quota against their own authenticated Codex account;
3. is being run by them directly (they type and execute the commands themselves in their own
   terminal session) — Codex CLI acting as "the implementer" for this ticket does not run Step 11
   on the operator's behalf, and must not proceed past this point without the operator having
   already done so and reported back what was captured.

**Do NOT touch:** no files change in this step. Do not write any code, config, or fixture file
until this checkpoint has been explicitly confirmed by the operator.

**Verify:** the operator has stated, in the session transcript, that they ran Step 11 themselves
and are reporting its actual captured output — not a prediction or placeholder.

**Review-phase note (recommended, evidentiary reinforcement):** a plan-doc instruction cannot
mechanically stop an external actor from skipping straight to Step 11 — this gate is honor-based by
construction. To make the honoring of this gate independently checkable after the fact (mirroring
this plan's own Step 3.5 evidentiary pattern), Step 11's own first recorded action must be to write
the operator's literal consent confirmation (their own words, timestamped) into this ticket's
`## Implementation Notes` section **before** any Codex CLI command in Step 11 is run — not
after-the-fact. Step 12/14 do not re-derive or verify this retroactively (there is no code-level
way to do so), but its presence in `Implementation Notes` is what Verify/done-checker will look for
as evidence this checkpoint was honored in sequence, not skipped.

---

### Step 11 — Real Codex CLI fixture-capture experiment (isolated scratch directory)

**Files:** exactly two edits inside this repository — both plain-text appends to this ticket's
`## Implementation Notes` section (step 0's consent-confirmation append, and substep 6's
empirical-TOML-syntax-finding append) — and nothing else. Every other action in
this step happens in a directory entirely outside `/home/u24desktop/Working/rpg-based-simulation`
(e.g. `/tmp/codex-fixture-capture-scratch/` or `~/scratch/codex-fixture-capture/` — exact path is
not load-bearing, only "outside this repo's working tree and git history" is).

**Change:**

0. **Before any Codex CLI command runs** (per Step 10's evidentiary-note requirement): append the
   operator's literal, timestamped consent confirmation to
   `tickets/inprogress/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`'s `## Implementation Notes`
   section — this single append is the one narrow, explicit exception to this step's otherwise
   strict "no file inside this repository" rule (Step 10 itself makes no file changes; this is
   where that checkpoint's evidence is actually recorded). Do not proceed to step 1 below until
   this append is done.

This step's exact literal commands cannot be pinned in advance — Decision #4 above
confirms the `.codex/config.toml` hook-registration TOML syntax is genuinely undocumented in this
repo today and WebFetch is sandbox-blocked for a fresh manual re-fetch. Follow this procedure and
record what you actually discover:

1. Create the scratch directory and `cd` into it. Initialize it as its own minimal git repository
   (`git init`) if Codex's project-trust model requires a git repo to exist for a "project" to be
   recognized — confirm this empirically; do not assume.
2. Establish Codex's project trust for this scratch directory (per `codex_capability_matrix.md`
   §3: project-scoped config only loads once trusted). Discover and use whatever real command/flag
   Codex CLI provides for this (e.g. an explicit trust prompt on first run, or a CLI subcommand) —
   record exactly what worked.
3. Write a throwaway `.codex/config.toml` in the scratch directory that registers exactly **one**
   hook, for the **`PostToolUse`** event (chosen because it's the single event this repo's own
   `agent-orchestration/hook-events.yaml` already normalizes as feeding `tools.jsonl` on the
   Claude side — the natural first-slice target if Codex-side monitoring is ever wired later). The
   hook's command should be a trivial script (e.g. a one-line shell script or `python3 -c`
   one-liner) that reads its full `stdin` and writes it verbatim to a file in the scratch
   directory, e.g. `captured_stdin.json`.
4. Run a Codex CLI invocation inside the scratch directory that triggers at least one tool call
   (so `PostToolUse` fires at least once) — e.g. `codex exec` with a trivial prompt that causes a
   `Bash` or file-read tool call.
5. Inspect `captured_stdin.json`. Confirm it is valid JSON and record: the exact set of top-level
   keys present, their types, and the literal `hook_event_name` value. Cross-check against
   `codex_capability_matrix.md` §1's documented `PostToolUse` field table (`session_id`,
   `transcript_path`, `cwd`, `hook_event_name`, `model`, `turn_id`, `permission_mode`) — note any
   discrepancy explicitly rather than silently reconciling it.
6. Record the literal `.codex/config.toml` TOML syntax you used in step 3 that actually worked —
   this is the empirical answer to Decision #4's open schema question. Write it into this ticket's
   `## Implementation Notes` section verbatim (as a documented finding, not as repo config — see
   Step 13, which deliberately does *not* commit this hook-bearing config).
7. Copy only `captured_stdin.json` (the payload) back toward the repo for Step 12 — never copy the
   scratch directory's `.codex/config.toml` itself into this repository.

**Do NOT touch:** any file inside `/home/u24desktop/Working/rpg-based-simulation` during this step,
**except** the two explicit `## Implementation Notes` appends this step itself specifies (step 0's
consent-confirmation append, and substep 6's empirical TOML-syntax-finding append) — both are
plain text appends to the ticket file, never code/config. Do not run this experiment against this
repository's own working tree otherwise, even in a subshell or worktree — the entire point of
"isolated scratch directory" is that this repo's real `.codex/` state (added in Step 13) is never
derived from a hook-bearing config, only from the empirical findings this step reports.

**Verify:** a valid `captured_stdin.json` exists in the scratch directory and the operator has
reported its contents (or a redacted/representative excerpt if it contains anything sensitive)
back into the session for Step 12 to consume.

---

### Step 12 — Commit the captured fixture and its validating test

**Files:** new `tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json`,
new `tests/tools/test_codex_hook_payload_fixture.py`.

**Change:** Create `tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json` (a new
directory, deliberately separate from `tests/fixtures/agent_replay/` — this is a different fixture
format for a different purpose; do not reuse `replay_fixture_spec.md`'s `phases:`/`transition:`
envelope shape here) with this shape:

```json
{
  "fixture_schema_version": 1,
  "capture_grade": "direct_experiment",
  "hook_event_name": "PostToolUse",
  "codex_cli_version": "<exact output of `codex --version`, recorded during Step 11>",
  "captured_at_utc": "<ISO-8601 timestamp of when Step 11 was actually run>",
  "capture_method": "isolated scratch directory outside this repo; throwaway .codex/config.toml registering one PostToolUse hook that dumped its real stdin verbatim; codex exec triggered one tool call",
  "raw_stdin_payload": { "<the exact JSON object captured in Step 11, byte-for-byte>": "..." }
}
```

`capture_grade: "direct_experiment"` is required and must never be set to anything else in this
file — it is the marker distinguishing this from `codex_capability_matrix.md`'s
documentation-citation-grade evidence (per that doc's §6 distinction).

Add `tests/tools/test_codex_hook_payload_fixture.py`:
- `test_fixture_file_exists_and_parses_as_json()`.
- `test_fixture_is_direct_experiment_grade()` — asserts `capture_grade == "direct_experiment"`.
- `test_fixture_hook_event_name_is_post_tool_use()`.
- `test_fixture_raw_payload_contains_documented_common_fields()` — asserts
  `raw_stdin_payload` is a dict containing at least `session_id`, `cwd`, `hook_event_name` (per
  `codex_capability_matrix.md` §1's documented common-input-fields excerpt for `PostToolUse`); if
  Step 11 found a discrepancy (a documented field genuinely absent from the real payload), this
  test should assert the fields that were *actually* observed present, not blindly assert every
  documented field — match this test to Step 11's actual recorded findings, not to the
  documentation table blindly.

**Do NOT touch:** `docs/ai/replay_fixture_spec.md` or `tools/agent_replay/` — this is a distinct
fixture concern, not an extension of the phase-slice replay envelope.

**Verify:** `pytest tests/tools/test_codex_hook_payload_fixture.py -v` — all pass.

---

### Step 13 — Add minimal `.codex/config.toml` (zero production hooks, by construction)

**Files:** new `.codex/config.toml`.

**Change:** Create `.codex/` and `.codex/config.toml` containing **only** a header comment — no
TOML keys, tables, or hook registrations of any kind. Exact content:

```toml
# .codex/config.toml — TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
#
# Minimal project marker, committed only after the isolated scratch-directory fixture-capture
# experiment (Step 11 of this ticket's plan.md; captured payload at
# tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json) confirmed real
# PostToolUse hook stdin-payload behavior and the project-trust/hook-registration mechanics.
#
# This file deliberately contains ZERO hook registrations — no [hooks] table, no per-event
# hook arrays, at any nesting level. This ticket's scope explicitly forbids enabling any
# production hook. A future, separate ticket (live-Codex-pilot-guardrails, out of this
# ticket's scope) owns actually wiring a production hook, using the registration syntax this
# ticket's Step 11 discovered and recorded in this ticket's Implementation Notes.
```

This is deliberately the safest resolution to Decision #4's open schema question: since the
literal hook-registration TOML syntax was only discovered empirically in a scratch directory
(Step 11) and this ticket's hard requirement is zero production hooks, the committed file simply
never encodes any hook syntax at all — there is nothing to get wrong.

**Do NOT touch:** do not add a `[hooks]` table "commented out" as an example — a commented-out
`[hooks]` block still risks a future careless uncomment turning it into a live production hook,
and it isn't required by any AC. A bare provenance comment is sufficient and strictly safer.

**Verify:** `test -f .codex/config.toml`; `tomllib.load` on it succeeds and parses to an empty
dict `{}` (a comment-only TOML file parses to `{}`).

---

### Step 14 — No-production-hook verification test + final full verification pass

**Files:** new `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py`.

**Change:** Add `test_no_production_hook_registered_in_committed_codex_config()` — identical
walk-for-`"hooks"`-key logic as Step 9's narrowed test (parse `.codex/config.toml` with `tomllib`,
recursively assert no dict anywhere contains a `hooks` key), applied here as this ticket's own
first-class assertion (not merely inherited via the cross-ticket edit in Step 9) — this is AC #6's
direct verification, owned by this ticket's own test tree rather than depending solely on the
edited file from a different ticket.

Then run the full verification pass:

```
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -v
pytest tests/agent_replay/ -v
pytest tests/tools/test_codex_capability_diagnostics.py tests/tools/test_post_tool_hook.py tests/tools/test_codex_hook_payload_fixture.py -v
pytest tests/unit/lab_agent/test_workflow_registry.py -v
```

All must pass. Additionally, run these explicit scope-guard checks:

- `git diff --stat docs/ai/agents_dir_disposition.md` → must be empty (no changes).
- `git diff --stat .claude/` → must be empty (no changes to any `.claude/` file, including
  `.claude/workflows/implement-ticket.js`).
- `git diff --stat .agents/rules/` → must be empty.
- Confirm `.codex/config.toml`'s only content is the provenance comment from Step 13 (no hook
  table was accidentally added by any later edit).

**Do NOT touch:** do not run `pytest tests/` (the full suite) — scope every command to the paths
listed above, per this repo's testing rule.

**Verify:** every command above passes/returns empty diff. This is the final gate before the
ticket can be considered implementation-complete (Finalize-phase ticket-closing steps — moving the
ticket to `tickets/done/`, updating `working_log.csv`, migrating staging artifacts — are outside
this plan's scope; they follow the project's standard After-Work checklist once this plan's steps
are verified).

## Scope Guards

- Must NOT modify `.claude/workflows/implement-ticket.js` or any file under `.claude/`.
- Must NOT re-litigate or edit `docs/ai/agents_dir_disposition.md`'s per-item classification
  table — this ticket executes the containment law that doc already states, it does not revise
  the classification itself.
- Must NOT promote any of the 6 `retain-and-migrate` `.agents/skills/` dirs' content
  (`clean-code`, `codebase-search`, `code-review`, `create-skill`, `receiving-code-review`,
  `requesting-code-review`) into the new generated catalog — they are not in `skills.yaml`;
  omitting them is correct, per the disposition doc's own deferral to a future promotion-review
  ticket, not a bug to fix here.
- Must NOT enable any production Codex hook. Step 13's committed `.codex/config.toml` contains
  zero hook registrations by construction; Step 14's final verification explicitly checks this at
  ticket close.
- Must NOT conflate this ticket's raw hook-`stdin`-payload fixture
  (`tests/fixtures/codex_hook_payloads/`) with `docs/ai/replay_fixture_spec.md`'s
  phase-slice-replay envelope (`tests/fixtures/agent_replay/`) — different shape, different
  purpose, different directory.
- The edit to `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` (Step 9) is
  an explicit, flagged cross-ticket edit (owned by the closed `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`)
  — record it under this ticket's `Files Changed` with the rationale given in Step 9. The sibling
  test in that file, `test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree`, must
  remain byte-for-byte unmodified.
- Must NOT hand-edit generated `AGENTS.md` or any generated `.agents/skills/<id>/SKILL.md` file
  directly — fix `tools/agent_orchestration_codex_adapter/generator.py` and re-run Step 7 instead.
- Must NOT touch `.agents/rules/*.md` (any of the 9 files there) — out of this ticket's scope,
  including the separately-discovered stale "17-phase" reference at
  `.agents/rules/engine_contracts.md:33`, which belongs to a future cleanup ticket.
- Must NOT copy the Step 11 scratch directory's hook-bearing `.codex/config.toml` into this
  repository — only the captured JSON payload is committed (Step 12); the repo's own
  `.codex/config.toml` (Step 13) is a separately-authored, hook-free file.
- Must NOT run `pytest tests/` (full suite) at any verification point — always scope to the
  paths listed in each step's Verify section or in Step 14.

## Dependency Map

- Step 1 gates everything else (entry-criterion check).
- Step 2 (monitoring-snapshot tooling) must complete before Step 3 (containment), since Step 3
  uses Step 2's functions procedurally.
- Step 3 (containment) must complete before Step 5 (generator build only *writes* correctly once
  `.agents/skills/` is clear — the generator itself can be authored in parallel with Step 3/4, but
  Step 7 (materialize real output) must run strictly after Step 3).
- Step 4 (containment tests) must run **after** Step 7 (real output materialized), not
  immediately after Step 3 — test #1 in Step 4 needs the regenerated `.agents/skills/` to exist to
  prove the *stale* content specifically is gone (see Step 4's own note). Author the test file in
  either order, but only run/pass it after Step 7.
- Step 5 (generator package) and Step 6 (generator tests) can be authored together; Step 6's tests
  exercise the generator against `tmp_path`, so they do not strictly require Step 3 to have run
  first — but running them after Step 3 is simplest since `_REPO_ROOT` will already be in its
  post-containment state either way.
- Step 7 depends on Step 3 (clear `.agents/skills/`) and Step 5 (generator exists).
- Step 8 depends on Step 7 (real `AGENTS.md` must exist to test its content).
- Step 9 (cross-ticket test edit) is independent of Steps 1–8; it can be done any time, but must
  be done before Step 14's final verification pass (which relies on it passing). **Review-phase
  correction:** Step 9 must also complete no later than Step 13 — if Step 13 (which creates the
  real `.codex/` directory) lands first, the old, still-unnarrowed
  `test_no_dot_codex_directory_exists_in_repo` assertion would fail for any incidental partial-suite
  run in that window. Do Step 9 before Step 13, not merely "any time before Step 14."
- Step 10 (consent checkpoint) gates Step 11 absolutely — no prior step depends on Step 10, and no
  later step (12, 13, 14) can begin until Step 10 and Step 11 both complete.
- Step 12 depends on Step 11 (needs the real captured payload).
- Step 13 depends on Step 11 (needs Step 11's empirical findings recorded, even though it doesn't
  encode them as hook syntax) and should also come after Step 9/14's narrowed test exists so its
  correctness can be checked immediately.
- Step 14 depends on all prior steps having completed.
- Steps 1–9 (contract/containment/generator track) and Steps 10–12 (fixture-capture track) are
  otherwise independent of each other and could be executed in either relative order, but Step 14
  requires both tracks complete, and Step 9 specifically must precede Step 13 (see Step 9's own
  entry above — not merely "any order").

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Generation work does not begin until CONTRACT-CORE landed and its generator is available | Step 1 | `load_contract()` manual check (Step 1); structurally reinforced by `test_requires_valid_contract.py` (Step 6) |
| Legacy `.agents/skills/` quarantined with byte-identical archived copy before new content goes live | Step 3, Step 4 | `tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py` |
| Replacement catalog generated from validated contract, not hand-curated — traceable to source fields | Step 5, Step 7 | `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` |
| Root `AGENTS.md` exists, is not a copy of the stale draft, documents real 32-phase pipeline | Step 5, Step 7, Step 8 | `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py` |
| Committed fixture captures real hook-payload JSON via isolated scratch-directory Codex CLI invocation | Step 10, Step 11, Step 12 | `tests/tools/test_codex_hook_payload_fixture.py` |
| No production hook enabled, verified by explicit `.codex/` config-state check at ticket close | Step 13, Step 14 | `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py`; also `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py::test_no_production_hook_registered_in_codex_config` (Step 9) |
| `agent-monitoring/*.jsonl` unchanged (append-only diff) after the containment action | Step 2, Step 3 | `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py` (validates the tooling); procedural pass/fail recorded in ticket's Implementation Notes (validates the actual event) |
| Containment action sequenced first, before AGENTS.md/skills regeneration proceeds | Step 3 precedes Step 5/7 (Dependency Map) | Enforced structurally: Step 7 cannot produce correct output until Step 3 has run; no automated test proves ordering post-hoc, this is a procedural sequencing requirement |

## Anti-Drift Notes

- The `.agents/rules/AGENTS.md` draft has **no** phase-count text at all — do not waste time
  hunting for a literal "17-phase" string there; the real drift this ticket must avoid repeating
  lives in `.agents/rules/authoritative_mechanics.md:18`, a file this ticket does not touch.
  Verification is instead: new `AGENTS.md` states "32 phases" correctly (Step 8).
- A second, independent stale "17-phase" reference exists at `.agents/rules/engine_contracts.md:33`
  — discovered during planning, out of scope for this ticket, do not fix it here.
- `skills.yaml`'s 16-entry set must not silently grow to include the 6 `retain-and-migrate`
  legacy-only skill ids during generator development — guarded explicitly by
  `test_skills_yaml_sixteen_entry_set_is_not_expanded` (Step 6).
- The archived legacy-skills copy must never itself land somewhere still on Codex's
  `.agents/skills` upward-discovery walk (e.g. a nested `.agents/skills/_archive/` would defeat
  the entire containment action while appearing to satisfy a naive "moved the files" check) —
  guarded by `test_archived_copy_is_not_on_codex_discovery_path` (Step 4).
- `.codex/config.toml`'s hook-registration TOML syntax is genuinely unknown until Step 11 runs —
  do not fabricate a plausible-looking schema anywhere in this repo before that step completes;
  Step 13's committed file avoids the question entirely by containing no hook syntax at all.
- Do not let the real fixture-capture experiment (Step 11) touch this repository's own working
  tree, even transiently — it must run in a directory outside
  `/home/u24desktop/Working/rpg-based-simulation`.
- Step 9's cross-ticket test edit is a one-function, one-name change — do not use it as an
  opportunity to also "clean up" or restructure the rest of
  `test_no_codex_scope_creep.py`, which belongs to a different, closed ticket.


## Deviations

1. **Test-first ordering.** New behavioral tests are written and observed failing before their
   corresponding production code, rather than the code-first ordering in several steps. This is
   required by the project test-driven-development guidance and changes no scope, output, or
   acceptance criterion. Authorized by `CLAUDE_RESPONSE_TO_TAKEOVER_NOTE.md`.
2. **Exact skill-body concatenation.** `build_codex_skill_md()` concatenates the closing
   frontmatter delimiter directly with the source body because `_extract_body()` preserves that
   body's leading newline(s). The original illustrative template would otherwise add an extra
   blank line and violate Step 6's byte-identical-body test. Authorized by
   `CLAUDE_RESPONSE_TO_TAKEOVER_NOTE.md`.
3. **Project Python interpreter.** Commands use `.venv/bin/python3` rather than bare `python3`
   so all validation and tests use the repository's declared virtual environment. Authorized by
   `CLAUDE_RESPONSE_TO_TAKEOVER_NOTE.md`.
