---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PARITY
artifact_type: plan
tags: [ai, workflows, process-improvement, hooks]
---

# Implementation Plan — TCK-20260721-CODEX-REPLAY-PARITY

## Summary

This plan builds a new, sibling package — `tools/agent_replay_codex/` — that drives a **real**
Codex CLI process through the exact same `Scope → Investigate → Plan → Review` fixture-replay code
path `tools/agent_replay/runner.py::replay_slice()` already exercises in pure Python, and compares
the two outputs for exact parity. The design is **execution-driven, not prompt-driven**: Codex is
never asked to "reason about" gate logic — it is instructed (via `codex exec`) to run a small
wrapper script that imports and calls the literal same `load_fixture()`/`replay_slice()` functions
`tools/agent_replay/` already ships, unmodified. This is the only design that actually tests
whether a real Codex-invoked process can be driven through the deterministic code path, rather than
testing Codex's own comprehension of workflow rules.

Containment uses the technique with real, working precedent in this repo — **isolated scratch
directory + git-porcelain/content-hash snapshot diff** — strengthened with Codex CLI's own
documented `-C`/`--sandbox`/`--skip-git-repo-check` flags (confirmed via `codex exec --help`,
not previously surfaced in investigation.md), rather than introducing unprecedented `strace`/
`bwrap`/`unshare` tooling. A real, programmatically-enforced consent gate
(`CODEX_REPLAY_PARITY_LIVE_CONSENT=1`) gates every code path that can spawn a `codex` subprocess,
checked strictly before any subprocess is constructed — refusal is a raised exception, never a
silent skip. Shadow mode reuses N=1: the one already-committed
`tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` fixture, whose `source`
block and header comments already embed Claude's real historical result (derived from the real,
done `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` ticket and its real `agent-monitoring/events.jsonl`
rows) — no new fixture, no envelope-format extension. The canonical provider string is bare
`"codex"`, matching the bare `"claude"` convention already live in `tests/tools/test_record_run.py`,
`test_post_tool_hook.py`, and `test_record_events.py` (real shipped test code from
`MONITORING-WRITER-UNIFICATION`, not that ticket's own synthetic-illustration doc text). Nothing
this ticket builds ever writes to the real ticket tree or the real monitoring corpus — every real
Codex invocation is comparison-only, verified by dedicated provenance and containment checks.

## Decisions (resolving the 5 investigation-flagged questions — final, not options for Implement to choose between)

1. **Adapter design: execution-driven.** New `tools/agent_replay_codex/wrapper_script.py` is the
   literal script `codex exec` invokes. It imports `tools.agent_replay.fixture_envelope.load_fixture`
   and `tools.agent_replay.runner.replay_slice` **unmodified** (not merely the two leaf gate
   functions) and writes their result as JSON to a caller-supplied output path. This gives the
   strongest possible parity proof for AC #4: Codex is proven to drive the exact same function that
   produces `ReplayOutcome`, not a Codex-side reimplementation.
2. **Containment: isolated scratch dir + git-porcelain/content-hash snapshot diff**, mirroring
   `tests/agent_replay/test_no_mutation_snapshot.py`'s porcelain-if-clean/content-hash-if-dirty
   technique (read, not modified — a new sibling module reimplements the same logic against a
   parameterized `repo_root`) plus `tools/agent-monitoring/manifest.py`'s
   `capture_lines`/`assert_prefix_preserved` pair (imported, reused unmodified). Strengthened with
   `codex exec`'s own `-C <scratch_dir>` (sets Codex's working root explicitly),
   `-s workspace-write` (sandboxes writes to the workspace), and `--skip-git-repo-check` (the
   scratch dir is never `git init`-ed — simpler and safer than the fixture-capture precedent, which
   needed a git repo only for its now-unneeded hook-registration experiment). `strace`/`bwrap`/
   `unshare` are explicitly rejected — zero precedent in this repo, added complexity, and the
   selected technique plus Codex's own sandbox flags already give both a preventive and a detective
   guarantee.
3. **Consent gate: `CODEX_REPLAY_PARITY_LIVE_CONSENT=1`**, an environment variable checked by
   `tools/agent_replay_codex/consent_gate.py::require_live_consent()`, called as the **first**
   statement of `invoker.py::run_codex_replay()` — strictly before any `subprocess` call is
   constructed. Absent or any value other than the literal string `"1"` raises
   `ConsentNotGrantedError` and the function returns without ever touching `subprocess`. This is
   programmatically enforced (not honor-based like `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s Step 10),
   satisfying the AC's "refuses to proceed" wording literally.
4. **Shadow-mode N = 1**, reusing `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`
   unchanged. Claude's side of the shadow-mode comparison is read directly from that fixture's own
   `source`/`phases` blocks (already real, already derived from the done ticket + real
   `agent-monitoring/events.jsonl` rows per the fixture's own header comment) — no live query, no
   new fixture, no envelope extension.
5. **Provider string: bare `"codex"`**, matching the bare `"claude"` convention confirmed live in
   `tests/tools/test_record_run.py:181,193`, `test_post_tool_hook.py:109,122`, and
   `test_record_events.py:271,283` (real shipped `MONITORING-WRITER-UNIFICATION` test code — not
   `docs/ai/monitoring_writer_decision.md`'s `"claude-code"` synthetic illustration, which is not
   what actually shipped).

## Steps

### Step 1 — Entry-criterion guard

**Files:** new `tools/agent_replay_codex/__init__.py` (empty), new
`tools/agent_replay_codex/errors.py`, new `tools/agent_replay_codex/entry_criterion.py`, new
`tests/agent_replay_codex/__init__.py` (empty), new `tests/agent_replay_codex/test_entry_criterion.py`.

**Change:** `errors.py` defines the package's independent exception classes (one file, all of this
package's exceptions, not per-module — smaller surface than the two-file `errors.py`/generator
split the Codex-guidance package used, appropriate since this package has no write-guard of its
own):

```python
class EntryCriterionNotMetError(Exception):
    """Raised when MONITORING-WRITER-UNIFICATION's writer module is not importable/landed."""

class ConsentNotGrantedError(Exception):
    """Raised when a real Codex CLI invocation is attempted without CODEX_REPLAY_PARITY_LIVE_CONSENT=1."""

class ContainmentViolationError(Exception):
    """Raised when a pre/post snapshot diff detects an unexpected change to tickets/ or
    agent-monitoring/*.jsonl, or the committed .codex/config.toml changed."""

class CodexInvocationError(Exception):
    """Raised when the real `codex exec` subprocess exits non-zero or produces no parseable result."""
```

`entry_criterion.py::assert_monitoring_writer_landed(tools_dir: Path | None = None) -> None`:
imports `tools/agent-monitoring/writer.py` via `importlib.util.spec_from_file_location` (mirrors
`manifest.py`'s own existing technique for importing the hyphenated `agent-monitoring` directory —
do not rename that directory), asserts it defines both `write_line` and `write_lines` callables.
Raises `EntryCriterionNotMetError` with a clear message naming what's missing if the import fails
or either symbol is absent. This makes the ticket's entry criterion ("does not begin real-Codex-
execution work until MONITORING-WRITER-UNIFICATION has landed") a structural, code-level check, not
merely a documented precondition — MONITORING-WRITER-UNIFICATION is already confirmed DONE
(investigation.md), so this test is expected to pass immediately; it exists to make future removal
of `writer.py` a hard, loud failure here rather than a silent one.

**Do NOT touch:** `tools/agent-monitoring/writer.py` itself (read-only import) or any other file
under `tools/agent-monitoring/`.

**Verify:** `pytest tests/agent_replay_codex/test_entry_criterion.py -v` — passes; includes a
negative case (monkeypatch the import path to a nonexistent file, assert
`EntryCriterionNotMetError` raised) and a positive case (real `tools/agent-monitoring/writer.py`,
assert no exception).

---

### Step 2 — Consent gate

**Files:** new `tools/agent_replay_codex/consent_gate.py`, new
`tests/agent_replay_codex/test_consent_gate.py`.

**Change:** 

```python
CONSENT_ENV_VAR = "CODEX_REPLAY_PARITY_LIVE_CONSENT"

def require_live_consent(env: Mapping[str, str] | None = None) -> None:
    """Raise ConsentNotGrantedError unless env[CONSENT_ENV_VAR] == '1' exactly. Any other value
    (unset, empty, 'true', 'yes', '0') is treated as refusal — deliberately strict, no truthy
    coercion, to avoid accidental consent from an unrelated env var."""
    if env is None:
        env = os.environ
    if env.get(CONSENT_ENV_VAR) != "1":
        raise ConsentNotGrantedError(
            f"Real Codex CLI invocation refused: set {CONSENT_ENV_VAR}=1 to consent to real "
            "API usage under your own authenticated Codex account before proceeding."
        )
```

**Do NOT touch:** no other file. This module has zero dependency on `subprocess` — it must be
importable and callable without importing `subprocess` at all, so a test can prove it never reaches
subprocess construction.

**Verify:** `pytest tests/agent_replay_codex/test_consent_gate.py -v` — negative case (env var unset
→ raises `ConsentNotGrantedError`), negative case (env var set to `"true"` → still raises), positive
case (env var `"1"` → no exception).

---

### Step 3 — Wrapper script (the script Codex's CLI actually executes)

**Files:** new `tools/agent_replay_codex/wrapper_script.py`, new
`tests/agent_replay_codex/test_wrapper_script.py`.

**Change:** A standalone, directly-runnable script (`if __name__ == "__main__": main()`) that:

```python
"""Standalone entry point the real Codex CLI process invokes via `codex exec` (see invoker.py). Imports
and calls the exact same tools.agent_replay.fixture_envelope.load_fixture() / runner.replay_slice()
functions the Python-only replay proof already calls, unmodified — proving a real Codex-invoked
process can drive the identical deterministic code path, not a Codex-side reimplementation.

Never imports/subprocesses/references the four forbidden monitoring/hook scripts under
tools/agent-monitoring/ (pre_tool_hook, post_tool_hook, record_run, record_events), directly or
transitively — replay_slice()'s own _fake_write_monitoring/_fake_hook_boundary stand-ins already
guarantee this at the function level; this file additionally never names those four script files
literally anywhere in its own source (see tests/agent_replay_codex/test_no_forbidden_calls.py's
whole-file string-constant scan, a new sibling instance of tools/agent_replay's own guard).

Reads ONLY: the fixture YAML at --fixture (read-only) and the tools/agent_replay/*, tools/gate_checks/*,
tools/tag_registry.py Python source (import, read-only). Writes ONLY the JSON result file at --out —
never any path under tickets/ or agent-monitoring/.
"""
import argparse
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.fixture_envelope import load_fixture  # noqa: E402
from agent_replay.runner import replay_slice  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    fixture = load_fixture(args.fixture)
    outcome = replay_slice(fixture)

    Path(args.out).write_text(
        json.dumps({"final_status": outcome.final_status, "phases_completed": outcome.phases_completed}),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Add one guard test in `test_wrapper_script.py`:
`test_scope_boundary_only_scope_through_review_phases_supported()` — asserts, by inspecting
`fixture_envelope.py`'s and `runner.py`'s own real (unmodified) source, that `replay_slice()` only
recognizes `Scope`/`Investigate`/`Plan`/`Review` as phase names with special-cased branch logic
(reuse the existing fixture's 4-phase list as the ground truth: assert
`{p.phase for p in load_fixture(_REAL_FIXTURE_PATH).phases} == {"Scope", "Investigate", "Plan", "Review"}`).
This is the concrete enforcement of AC #9 ("no fixture inputs spanning Implement/Test/Parity/Verify/
Finalize are exercised") — since `wrapper_script.py` calls the same unmodified functions, whatever
scope boundary they already enforce is inherited automatically; this test pins it.

Also add `test_wrapper_script_runs_standalone_and_writes_result(tmp_path)` — invoke
`subprocess.run([sys.executable, str(wrapper_script_path), "--fixture", str(_REAL_FIXTURE_PATH), "--out", str(tmp_path / "result.json")])`
directly (no Codex involved — this proves the script itself works before any real API cost is
spent), assert exit code 0 and the written JSON matches
`replay_slice(load_fixture(_REAL_FIXTURE_PATH))` called directly in-process.

**Do NOT touch:** `tools/agent_replay/{runner.py,fixture_envelope.py}` — import only, never edit.

**Verify:** `pytest tests/agent_replay_codex/test_wrapper_script.py -v` — passes.

---

### Step 4 — Containment snapshot module

**Files:** new `tools/agent_replay_codex/containment.py`, new
`tests/agent_replay_codex/test_containment.py`.

**Change:** Reimplements (does not import, since the source lives in a test file, not an importable
module) the exact porcelain-if-clean/content-hash-if-dirty technique from
`tests/agent_replay/test_no_mutation_snapshot.py`, parameterized by `repo_root` so tests can point
it at a disposable `tmp_path` git repo instead of the real one:

```python
_WATCHED_GIT_PATHSPECS = ["tickets/", "agent-monitoring/runs.jsonl", "agent-monitoring/events.jsonl", "agent-monitoring/tools.jsonl"]

@dataclass(frozen=True)
class ContainmentSnapshot:
    porcelain: str
    content_hash: str | None  # populated only when porcelain was non-empty at capture time

def capture_snapshot(repo_root: Path) -> ContainmentSnapshot: ...
def assert_no_diff(pre: ContainmentSnapshot, post: ContainmentSnapshot) -> None:
    """Raises ContainmentViolationError (not AssertionError, so callers outside pytest get a
    typed exception) on any detected diff, using the same porcelain-clean-else-content-hash logic."""
```

`capture_snapshot` and `assert_no_diff` are pure functions of `repo_root` — same shape as
`tools/agent-monitoring/manifest.py::capture_lines`/`assert_prefix_preserved`, which this module
also imports and wraps for the narrower `agent-monitoring/*.jsonl`-only check the AC's own bullet
#6 asks for specifically (`snapshot_monitoring_lines(agent_monitoring_dir)` /
`assert_monitoring_prefix_preserved(pre, post)`, thin wrappers around the existing `manifest.py`
functions — no reimplementation, direct import and reuse).

Add `tests/agent_replay_codex/test_containment.py` with the **required negative control**: build a
tiny synthetic `tmp_path` repo (`git init`, create `tickets/inprogress/FAKE.md` and
`agent-monitoring/{runs,events,tools}.jsonl` with a couple of lines each, `git add -A && git commit`),
call `capture_snapshot(tmp_path)`, mutate one file's content, call `capture_snapshot(tmp_path)`
again, assert `assert_no_diff(pre, post)` raises `ContainmentViolationError`. Also test the positive
(no-mutation) case: capture twice with no change in between, assert `assert_no_diff` does not raise.
This exercises the real detection logic end-to-end against a real (but disposable, tmp_path-scoped)
git repository — never the actual project repo — satisfying the Anti-Drift Test Guard that "a
containment test with no negative control is not a valid guard."

**Do NOT touch:** `tests/agent_replay/test_no_mutation_snapshot.py` or
`tools/agent-monitoring/manifest.py`'s `_scan_file`/`build_manifest`/`main` — only import
`capture_lines`/`assert_prefix_preserved` from `manifest.py`, never edit it.

**Verify:** `pytest tests/agent_replay_codex/test_containment.py -v` — passes, including both the
negative control and the positive (no-op) case.

---

### Step 5 — Codex-config hook-free guard

**Files:** new `tools/agent_replay_codex/codex_config_guard.py`, new
`tests/agent_replay_codex/test_codex_config_guard.py`.

**Change:**

```python
def assert_committed_config_hook_free(repo_root: Path) -> None:
    """Raises ContainmentViolationError if repo_root/.codex/config.toml exists and contains a
    'hooks' key anywhere at any nesting depth. Mirrors
    tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py's walk logic (read,
    not imported — that test module isn't an importable production module)."""

def snapshot_config_bytes(repo_root: Path) -> bytes | None:
    """Returns raw bytes of repo_root/.codex/config.toml, or None if it doesn't exist."""

def assert_config_bytes_unchanged(pre: bytes | None, post: bytes | None) -> None:
    """Raises ContainmentViolationError if pre != post."""
```

This gives this ticket's own first-class, mechanical proof (not merely inherited from a different
ticket's test) that the real invocation never causes this repo's committed `.codex/config.toml` to
gain a hook registration or change at all — belt-and-suspenders on top of the scratch dir never
containing its own `.codex/config.toml` in the first place (Step 6 — this design needs no hook at
all, unlike the fixture-capture precedent, since the wrapper script's result is read from a file
Codex writes by running a plain shell command, not via a hook payload).

**Do NOT touch:** `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py` or
`.codex/config.toml` itself.

**Verify:** `pytest tests/agent_replay_codex/test_codex_config_guard.py -v` — passes: asserts the
real committed `.codex/config.toml` currently passes `assert_committed_config_hook_free`, plus a
`tmp_path`-based negative case (write a `tmp_path/.codex/config.toml` containing
`[hooks.PostToolUse]` and assert it raises).

---

### Step 6 — Invoker (orchestration)

**Files:** new `tools/agent_replay_codex/invoker.py`.

**Change:** The single entry point that wires Steps 1–5 together:

```python
@dataclass(frozen=True)
class CodexReplayOutcome:
    final_status: str
    phases_completed: list[str]
    scratch_dir: Path  # left on disk, not auto-deleted — auditable per this ticket's own AC wording

def run_codex_replay(
    fixture_path: Path,
    *,
    repo_root: Path,
    env: Mapping[str, str] | None = None,
    timeout_s: float = 300.0,
) -> CodexReplayOutcome:
    assert_monitoring_writer_landed()          # Step 1 — entry criterion, before anything else
    require_live_consent(env)                  # Step 2 — consent, strictly before any subprocess object exists

    scratch_dir = Path(tempfile.mkdtemp(prefix="codex-replay-parity-"))
    out_path = scratch_dir / "codex_result.json"

    pre_tickets = capture_snapshot(repo_root)
    pre_monitoring = snapshot_monitoring_lines(repo_root / "agent-monitoring")
    pre_config = snapshot_config_bytes(repo_root)

    wrapper_path = Path(__file__).resolve().parent / "wrapper_script.py"
    command = [
        "codex", "exec",
        "-C", str(scratch_dir),
        "-s", "workspace-write",
        "--skip-git-repo-check",
        f"Run: {sys.executable} {wrapper_path} --fixture {fixture_path.resolve()} --out {out_path}",
    ]
    result = subprocess.run(command, cwd=str(scratch_dir), capture_output=True, text=True, timeout=timeout_s)

    post_tickets = capture_snapshot(repo_root)
    post_monitoring = snapshot_monitoring_lines(repo_root / "agent-monitoring")
    post_config = snapshot_config_bytes(repo_root)

    assert_no_diff(pre_tickets, post_tickets)                 # raises ContainmentViolationError, never swallowed
    assert_monitoring_prefix_preserved(pre_monitoring, post_monitoring)
    assert_config_bytes_unchanged(pre_config, post_config)

    if result.returncode != 0 or not out_path.exists():
        raise CodexInvocationError(f"codex exec failed (rc={result.returncode}): {result.stderr[-2000:]}")

    parsed = json.loads(out_path.read_text(encoding="utf-8"))
    return CodexReplayOutcome(
        final_status=parsed["final_status"],
        phases_completed=parsed["phases_completed"],
        scratch_dir=scratch_dir,
    )
```

Never uses `--dangerously-bypass-approvals-and-sandbox` or `--dangerously-bypass-hook-trust` (both
confirmed present in `codex exec --help`) — these would defeat the sandbox/trust posture this step
relies on; they must never appear in this module under any code path. The exact `-C`/`-s
workspace-write`/`--skip-git-repo-check` flag combination's actual read/write behavior (does
`workspace-write` sandbox mode block the wrapper script's read of `tools/agent_replay/*.py` outside
the scratch-dir workspace? does an untrusted scratch-dir path prompt for trust confirmation in
non-interactive `exec` mode and hang?) is **not independently verified by this plan** — Implement
must confirm this empirically on the first real invocation (Step 7) and record what actually
happened in this ticket's `## Implementation Notes`, exactly as `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s
Step 11 did for its own genuinely-undocumented behavior. If `workspace-write` blocks the necessary
reads, the documented fallback is `-s read-only` (wrapper script only needs read access to the repo
and one write to `out_path`, which a well-behaved `read-only` sandbox may still permit for a path
Codex is explicitly told to write to — verify, don't assume) rather than reaching for
`--dangerously-bypass-approvals-and-sandbox`.

**Do NOT touch:** Steps 1–5's modules (import only).

**Verify:** `python3 -c "from tools.agent_replay_codex.invoker import run_codex_replay"` imports
cleanly. `run_codex_replay(fixture_path, repo_root=REPO_ROOT, env={})` (no consent) raises
`ConsentNotGrantedError` with `subprocess.run` monkeypatched to raise `AssertionError` if called —
proves the ordering (consent checked before subprocess is ever touched). Full behavioral
verification happens in Step 7.

---

### Step 7 — Real, consent-gated integration proof (shared fixture + 3 integration tests)

**Files:** new `tests/agent_replay_codex/conftest.py`, new
`tests/agent_replay_codex/test_containment_real_process.py`, new
`tests/agent_replay_codex/test_no_production_hook_invocation.py`, new
`tests/agent_replay_codex/test_pre_post_snapshot.py`, new
`tests/agent_replay_codex/test_no_forbidden_calls.py`.

**Change:** First, `test_no_forbidden_calls.py` — a new, sibling AST-mirrored guard (mirrors
`tests/agent_replay/test_runner_no_forbidden_calls.py`'s technique exactly, scoped to
`tools/agent_replay_codex/*.py`): no import/subprocess/importlib call anywhere in this new
package's own source references the four forbidden monitoring/hook script names, plus the same
whole-file string-constant scan. This is a **new instance** of the existing guard for the **new**
package's own Python source — distinct from, and not a substitute for, the process-level proof
below (the Anti-Drift Test Guard explicitly warns against conflating the two). Run this first,
since it costs zero API usage and must pass before any real invocation is attempted.

Then, `conftest.py` defines one **session-scoped** fixture, since every real `codex exec` call
costs real account usage and this ticket's own investigation flags that cost explicitly — one real
invocation is shared across every test that needs it, not one per test:

```python
@pytest.fixture(scope="session")
def real_codex_replay(request):
    if shutil.which("codex") is None:
        pytest.skip("codex CLI not on PATH")
    if os.environ.get(CONSENT_ENV_VAR) != "1":
        pytest.skip(f"real Codex invocation requires {CONSENT_ENV_VAR}=1 (not set) — skipping, not failing")
    pre_tickets = capture_snapshot(_REPO_ROOT)
    pre_config = snapshot_config_bytes(_REPO_ROOT)
    outcome = run_codex_replay(_REAL_FIXTURE_PATH, repo_root=_REPO_ROOT)
    post_tickets = capture_snapshot(_REPO_ROOT)
    post_config = snapshot_config_bytes(_REPO_ROOT)
    return {"outcome": outcome, "pre_tickets": pre_tickets, "post_tickets": post_tickets,
            "pre_config": pre_config, "post_config": post_config}
```

(Note: `run_codex_replay` itself already asserts no-diff internally and raises on violation before
returning — this fixture's own pre/post capture around the *whole* call, including the fixture's
own consent/entry-criterion checks, is the belt-and-suspenders outer layer the AC's bullet #6 asks
for specifically: "Pre/post ... snapshot ... around the real Codex invocation" as its own explicit
assertion, not merely relying on the inner one.)

- `test_containment_real_process.py::test_real_invocation_produces_zero_tickets_or_monitoring_diff(real_codex_replay)` —
  asserts `assert_no_diff` and `assert_monitoring_prefix_preserved` on the fixture's captured
  pre/post pairs do not raise (they already didn't, inside `run_codex_replay` — this test asserts
  the outer capture agrees, i.e. nothing changed between the fixture's own pre-capture and its
  post-capture either).
- `test_no_production_hook_invocation.py::test_committed_codex_config_byte_identical_across_real_invocation(real_codex_replay)` —
  asserts `pre_config == post_config` and `assert_committed_config_hook_free(_REPO_ROOT)` still
  passes after the real call.
- `test_pre_post_snapshot.py::test_ac_explicit_pre_post_snapshot_around_real_invocation(real_codex_replay)` —
  the literal AC-bullet-#6 assertion, phrased as its own named test for direct traceability even
  though it exercises the same underlying mechanism as the two tests above.

**Do NOT touch:** do not give this fixture `autouse=True` — it must only run for tests that
explicitly request it, so `pytest tests/agent_replay_codex/ -v` without consent set skips cleanly
(3 skips) rather than every test in the directory being gated on a real API call.

**Verify:** `pytest tests/agent_replay_codex/test_no_forbidden_calls.py -v` passes unconditionally.
With `codex` on `PATH` but `CODEX_REPLAY_PARITY_LIVE_CONSENT` unset:
`pytest tests/agent_replay_codex/test_containment_real_process.py tests/agent_replay_codex/test_no_production_hook_invocation.py tests/agent_replay_codex/test_pre_post_snapshot.py -v`
→ 3 skipped, 0 failed. With consent granted (human operator sets the env var themselves, mirroring
the precedent's own human-operator-consent pattern): same command → 3 passed, and the human
operator confirms in the session transcript that they set the env var themselves and are reporting
the real outcome, not a prediction (recorded in this ticket's `## Implementation Notes`, mirroring
`CODEX-GUIDANCE-FIXTURE-CAPTURE` Step 10's evidentiary pattern).

---

### Step 8 — Phase-parity test (Python runner vs. Codex-adapter, AC #4)

**Files:** new `tests/agent_replay_codex/test_phase_parity.py`.

**Change:** `test_codex_execution_path_matches_python_runner_output(real_codex_replay)` (uses the
same session-scoped fixture from Step 7 — no second real invocation):

```python
python_outcome = replay_slice(load_fixture(_REAL_FIXTURE_PATH))
codex_outcome = real_codex_replay["outcome"]
if python_outcome.final_status != codex_outcome.final_status or python_outcome.phases_completed != codex_outcome.phases_completed:
    divergences = load_divergences(_REPO_ROOT / "agent-orchestration" / "intentional-divergences.md")
    assert is_approved(divergences, "codex_parity", "TCK-20260721-ORCHESTRATION-CONTRACT-ADR"), (
        f"Codex-side execution ({codex_outcome}) diverges from Python runner ({python_outcome}) "
        "with no matching RATIFIED entry in agent-orchestration/intentional-divergences.md"
    )
else:
    assert python_outcome.final_status == codex_outcome.final_status
    assert python_outcome.phases_completed == codex_outcome.phases_completed
```

Since `wrapper_script.py` (Step 3) calls the literal same `replay_slice()` function, this is
expected to match exactly with zero real divergence for this fixture — the divergence-checking
branch exists as a fail-safe, not because a mismatch is anticipated.

**Do NOT touch:** `tools/agent_orchestration_claude_adapter/divergence_log.py` — import
`load_divergences`/`is_approved` unmodified; this ticket's axis is a new value
(`"codex_parity"`), not a new axis literal added to that module's docstring-listed set (the module
matches any axis string generically — no code change needed to add a new axis name).

**Verify:** with consent granted, `pytest tests/agent_replay_codex/test_phase_parity.py -v` → 1
passed (or, if a genuine divergence is found, 1 passed via the RATIFIED-entry branch after
Implement adds one — see Step 8's own contingency note under Anti-Drift). Without consent: 1
skipped.

---

### Step 9 — Monitoring-record provenance check (AC #8)

**Files:** new `tools/agent_replay_codex/provenance_check.py`, new
`tests/agent_replay_codex/test_monitoring_provenance.py`.

**Change:**

```python
def assert_no_codex_provider_writes(agent_monitoring_dir: Path, provider_value: str = "codex") -> None:
    """Reads the real runs.jsonl/events.jsonl/tools.jsonl and raises ContainmentViolationError if
    any record's 'provider' field equals provider_value. Read-only — never writes."""
```

This is an always-runnable structural invariant (does not require a real Codex invocation): nothing
in this package ever calls `tools/agent-monitoring/writer.py` with `provider="codex"` — the whole
package only reads fixtures and writes to a scratch-dir JSON file — so this check should hold at
any point in time, not merely "after tests ran." Test both a real-corpus positive check (the real
`agent-monitoring/*.jsonl` today has zero `provider=="codex"` records) and a `tmp_path` negative
control (write a fake record with `"provider": "codex"` into a `tmp_path` copy, assert it raises).

**Do NOT touch:** `agent-monitoring/*.jsonl` — read-only in this module and its tests; the negative
control writes only into `tmp_path`, never the real files.

**Verify:** `pytest tests/agent_replay_codex/test_monitoring_provenance.py -v` — passes
unconditionally (no `codex` on `PATH` or consent required).

---

### Step 10 — Divergence-registration test (AC #4's registration half)

**Files:** new `tests/agent_replay_codex/test_divergence_registration.py`.

**Change:** `test_is_approved_recognizes_a_ratified_codex_parity_entry(tmp_path)` — write a
synthetic `intentional-divergences.md` under `tmp_path` containing one
`## codex_parity:FAKE-TICKET` section with all required fields (`Approved-by`, valid
`Approved-date`, `Status: RATIFIED`), call `load_divergences`/`is_approved` (imported from
`tools.agent_orchestration_claude_adapter.divergence_log`, unmodified) against it, assert
`is_approved(..., "codex_parity", "FAKE-TICKET")` is `True`. Also assert a `DEFERRED`-status
variant returns `False`. This is a unit-level proof the reuse path (Step 8's fail-safe branch)
actually works, independent of whether a real divergence is ever found.

**Do NOT touch:** the real `agent-orchestration/intentional-divergences.md` — this test only
operates on a `tmp_path` copy; do not add a real entry here speculatively (only add one if Step 8's
real run genuinely finds a mismatch).

**Verify:** `pytest tests/agent_replay_codex/test_divergence_registration.py -v` — passes
unconditionally.

---

### Step 11 — Shadow-mode comparison (AC #7)

**Files:** new `tools/agent_replay_codex/shadow_mode.py`, new
`tests/agent_replay_codex/test_shadow_mode_comparison.py`.

**Change:**

```python
@dataclass(frozen=True)
class ShadowModeComparison:
    ticket_id: str
    claude_final_status: str
    claude_phases_completed: list[str]
    claude_gate_result: str          # Review phase's real recorded verdict, from the fixture
    claude_artifact_refs: list[str]  # fixture's source.stored_artifacts_dir
    codex_final_status: str
    codex_phases_completed: list[str]
    codex_gate_result: str
    match: bool

def compare_claude_and_codex(fixture: FixtureEnvelope, codex_outcome: CodexReplayOutcome) -> ShadowModeComparison:
    """Claude's side is read directly from the fixture's own embedded phases/source data — already
    real, already derived from the done ticket + real events.jsonl (see the fixture file's own
    header comment) — never a new live query, never a write anywhere."""
```

`test_shadow_mode_comparison.py::test_n1_comparison_against_existing_fixture(real_codex_replay)`
(uses the Step 7 shared fixture — no third real invocation): builds the comparison, asserts
`match is True` (or the Step 8-style divergence-registered fallback), and additionally asserts — as
its own explicit assertion, per the Anti-Drift Test Guard against a shadow-mode comparison silently
applying output anywhere — that no file under `tickets/`, `agent-orchestration/`, or `.claude/`
changed as a side effect of running `compare_claude_and_codex` itself (a pure in-memory function;
assert via a fresh `capture_snapshot`/`assert_no_diff` pair bracketing just this call, on top of the
outer one Step 7's fixture already performed around the real invocation).

**Do NOT touch:** `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` or
`fixture_envelope.py` — read the existing fixture's `source` dict fields as-is; do not add new keys
to satisfy this step (if a field this step wants isn't already in the fixture, derive it from what
is there — e.g. `claude_gate_result` comes from `fixture.phases[-1].output["verdict"]`, already
present).

**Verify:** with consent granted: `pytest tests/agent_replay_codex/test_shadow_mode_comparison.py -v`
→ 1 passed. Without consent: 1 skipped.

---

### Step 12 — Final scoped regression pass and ticket-doc bookkeeping

**Files:** none new. Updates `tickets/inprogress/TCK-20260721-CODEX-REPLAY-PARITY.md`'s
`## Implementation Notes` (evidentiary consent/finding records, mirroring the precedent's pattern)
and `## Files Changed` sections only — no code.

**Change:** Run, in order:

```
pytest tests/agent_replay_codex/ -v                       # new package; some real-Codex tests skip without consent
pytest tests/agent_replay/ -v                              # existing replay-proof regression — must stay green, untouched
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -v
                                                             # 1 known pre-existing failure expected — see below
pytest tests/tools/test_monitoring_writer.py tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py -v
pytest tests/tools/test_codex_capability_diagnostics.py tests/tools/test_codex_hook_payload_fixture.py -v
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py -v
pytest tests/unit/lab_agent/test_workflow_registry.py -v
```

**Regression-baseline expectation (do not treat as a new failure introduced by this ticket):**
`tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`
is expected to still fail with `FileNotFoundError` on a stale `staging_artifacts/` path — a known,
pre-existing, unrelated failure tracked by the still-open
`tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`. Report it in the Test phase
summary exactly as `CODEX-GUIDANCE-FIXTURE-CAPTURE` did (named explicitly as pre-existing/
unrelated); do not attempt to fix it and do not let it inflate this ticket's own failure count
silently.

Also run the explicit scope-guard checks: `git diff --stat tools/agent_replay/` → empty;
`git diff --stat tests/agent_replay/` → empty; `git diff --stat .claude/` → empty;
`git diff --stat agent-orchestration/intentional-divergences.md` → empty **unless** Step 8 found a
real divergence, in which case it must show exactly one new `## codex_parity:...` section with all
required RATIFIED fields.

**Do NOT touch:** do not run `pytest tests/` (full suite).

**Verify:** all commands above pass/skip cleanly per the expectations stated; scope-guard `git diff
--stat` checks return the expected (empty, or singly-justified) output.

## Scope Guards

- Must NOT modify `tools/agent_replay/{runner.py,fixture_envelope.py}` — import only, everywhere in
  this new package.
- Must NOT modify `tests/agent_replay/test_runner_no_forbidden_calls.py` or
  `tests/agent_replay/test_no_mutation_snapshot.py` — this ticket adds new, sibling instances of
  the same techniques scoped to the new package, never edits the existing ones.
- Must NOT extend `tools/agent_replay/fixture_envelope.py`'s schema (no `files_changed`/diff
  payload) and must NOT add any fixture beyond the one already-committed
  `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` (N=1, per Decision #4).
- Must NOT invoke any real `codex` subprocess anywhere in this package's code without
  `require_live_consent()` having been called first and having not raised.
- Must NOT invoke, import, or subprocess `tools/agent-monitoring/{pre_tool_hook,post_tool_hook,record_run,record_events}.py`
  under any condition, in either this package's own Python source (guarded by Step 7's AST scan) or
  in the wrapper script Codex executes (which only ever calls `replay_slice()`'s existing in-memory
  fake stand-ins).
- Must NOT register any hook in `.codex/config.toml` (repo-committed or scratch-dir) — this design
  needs none; Step 5/7 assert the committed file stays hook-free and byte-identical.
- Must NOT use `codex exec --dangerously-bypass-approvals-and-sandbox` or
  `--dangerously-bypass-hook-trust` anywhere in `invoker.py`.
- Must NOT write, apply, or commit any Codex-generated output to `tickets/`, `agent-orchestration/`
  (other than the single, explicitly-flagged divergence-log append if Step 8 finds a real
  divergence), or any `.claude/` file. Shadow mode is comparison-only.
- Must NOT let Codex become a live writer to `agent-monitoring/{runs,events,tools}.jsonl` —
  structurally impossible by this design (the package never imports `writer.py`'s write path for
  any Codex-attributed record), verified by Step 9.
- Must NOT fix `tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme` —
  out of scope, owned by `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`.
- Must NOT begin any step in this plan that spawns a real `codex` subprocess (Steps 7, 8, 11) until
  `CODEX_REPLAY_PARITY_LIVE_CONSENT=1` has been set by the human operator themselves, mirroring
  `CODEX-GUIDANCE-FIXTURE-CAPTURE` Step 10's human-operator-runs-it-themselves posture, but now
  code-enforced rather than honor-based.

## Dependency Map

- Steps 1, 2, 4, 5 are independent of each other and of Step 3; all are read by Step 6.
- Step 3 (wrapper script) is independent of Steps 1/2/4/5 but is referenced by Step 6 (invoker
  constructs the `codex exec` command targeting it) and consumed indirectly by every downstream
  Codex-side test.
- Step 6 depends on Steps 1, 2, 3, 4, 5 (imports all of them).
- Step 7 depends on Step 6 (full invoker) and must run its AST-scan sub-test
  (`test_no_forbidden_calls.py`) before any real invocation in that same step — ordered internally.
- Step 8 depends on Step 7's `conftest.py` shared fixture (reuses the same real invocation, no new
  API cost) and on `tools/agent_orchestration_claude_adapter/divergence_log.py` (imported, read-only).
- Step 9 is independent of Steps 6–8 — no real invocation required, can be built any time after
  Step 1 (shares no code with the invoker).
- Step 10 is independent of everything except `divergence_log.py` (already exists, pre-dates this
  ticket) — can be built any time.
- Step 11 depends on Step 7's shared fixture (reuses the same real invocation) and on the existing,
  unmodified fixture file.
- Step 12 depends on all prior steps having completed (or, for the consent-gated ones, having
  cleanly skipped).
- Steps 9 and 10 have no dependency on real Codex API usage at all and can be implemented and fully
  verified first, before any consent decision is even needed, if useful for early signal.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Does not begin real-Codex-execution work until MONITORING-WRITER-UNIFICATION has landed | Step 1 | `tests/agent_replay_codex/test_entry_criterion.py` |
| Explicit, programmatically-checked human-consent gate; workflow refuses to proceed without it | Step 2 (gate), Step 6 (wired first in `run_codex_replay`) | `tests/agent_replay_codex/test_consent_gate.py`; ordering proven in Step 6's own Verify |
| Investigate/Plan phase selects and documents ONE auditable containment technique before any paid/live invocation | This plan's Decision #2 (scratch dir + snapshot diff + Codex sandbox flags) | N/A — a documentation/decision AC, satisfied by this plan.md existing before Step 7 runs |
| Real Codex-side execution produces final_status/phases_completed matching the Python runner's output; divergence registered if found | Step 3 (shared function), Step 8 | `tests/agent_replay_codex/test_phase_parity.py` |
| Process-level/filesystem-level containment proof (not AST scan) demonstrates zero invocation of the 4 forbidden scripts | Step 7 (`test_containment_real_process.py`, `test_no_production_hook_invocation.py`); Step 7's `test_no_forbidden_calls.py` is a supplementary source-level guard, not a substitute | `tests/agent_replay_codex/test_containment_real_process.py`, `test_no_production_hook_invocation.py` |
| Pre/post content-hash or git-porcelain snapshot of `tickets/` and `agent-monitoring/*.jsonl` asserted identical | Step 4 (mechanism), Step 7 (real application) | `tests/agent_replay_codex/test_containment.py`, `test_pre_post_snapshot.py` |
| Shadow-mode comparison across N real implement-ticket inputs (phase completion, gate result, artifact refs, event intent) | Step 11 (N=1) | `tests/agent_replay_codex/test_shadow_mode_comparison.py` |
| Monitoring-record provenance confirms Claude is sole live writer | Step 9 | `tests/agent_replay_codex/test_monitoring_provenance.py` |
| Scope boundary (Scope through Review only) documented and enforced; no fixture inputs spanning Implement/Test/Parity/Verify/Finalize | Step 3 (`test_scope_boundary_only_scope_through_review_phases_supported`); enforced structurally by not modifying `fixture_envelope.py`/`runner.py` | `tests/agent_replay_codex/test_wrapper_script.py` |

## Anti-Drift Notes

- `tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`
  is a known, pre-existing, unrelated failure (stale `staging_artifacts/` path, tracked by
  `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`, still open). Test phase must
  report it as baseline noise, not a regression this ticket introduced, and must not "fix" it as an
  undocumented drive-by change.
- Never spell out the four forbidden monitoring/hook script filenames literally (with `.py` suffix)
  in any `tools/agent_replay_codex/*.py` source file, including docstrings — Step 7's whole-file
  string-constant AST scan enforces this the same way `tests/agent_replay/test_runner_no_forbidden_calls.py`
  already does for `tools/agent_replay/`. This plan document itself is not scanned and may name them
  for clarity (as it does above), but source files must not.
- `codex exec`'s exact read/write behavior under `-s workspace-write -C <scratch_dir>` combined
  with an untrusted scratch-dir path is **not empirically verified by this plan** — Implement must
  confirm on the first real invocation (Step 7) and record actual findings in `## Implementation
  Notes`, exactly as `CODEX-GUIDANCE-FIXTURE-CAPTURE` Step 11 did for its own genuinely-undocumented
  behavior. Do not silently swap in `--dangerously-bypass-approvals-and-sandbox` if something
  doesn't work on the first try — investigate and record, don't bypass the safety flags to make a
  test pass.
- Every real `codex exec` invocation this ticket performs must be gated by
  `CODEX_REPLAY_PARITY_LIVE_CONSENT=1`, set by the human operator themselves in their own shell
  session before running Step 7/8/11's tests — mirroring `CODEX-GUIDANCE-FIXTURE-CAPTURE` Step 10's
  human-operator-consents-and-runs-it-themselves posture, now code-enforced. Do not set this
  variable programmatically anywhere in this repo's own test setup/CI config as a way to make tests
  "just pass" — that would defeat the entire point of the gate.
- The `real_codex_replay` session fixture (Step 7) must be shared, not re-invoked, across
  `test_containment_real_process.py`, `test_no_production_hook_invocation.py`,
  `test_pre_post_snapshot.py`, `test_phase_parity.py`, and `test_shadow_mode_comparison.py` — one
  real API call total per full test-suite run with consent granted, not five. Do not give any
  individual test its own un-cached `run_codex_replay()` call.
- Do not conflate this ticket's `tools/agent_replay_codex/` package with the existing
  `tools/agent_replay/` package (Python-only, `CODEX-REPLAY-PROOF`) or with
  `tools/agent_orchestration_codex_adapter/` (static `AGENTS.md`/`SKILL.md` generator,
  `CODEX-GUIDANCE-FIXTURE-CAPTURE`) — three structurally distinct packages, none of which this
  ticket edits in place.
- If Step 8's real phase-parity run genuinely finds a mismatch (not expected, since the wrapper
  script calls the literal same `replay_slice()` function, but possible if the real `codex` process
  itself fails/times out/produces unexpected output), the fix is to add one real, fully-fielded
  `## codex_parity:TCK-20260721-ORCHESTRATION-CONTRACT-ADR` entry to
  `agent-orchestration/intentional-divergences.md` (RATIFIED, with a genuine human `Approved-by` and
  `Approved-date`) — never to silently loosen the parity assertion itself.
- Provider string is bare `"codex"` (Decision #5) — do not write `"codex-cli"`, `"Codex"`, or any
  other variant anywhere in this package's code, including the negative-control test in Step 9.

## Deviations

1. **Step 6 (`invoker.py`) statement ordering: consent check before entry-criterion check, not
   after.** This plan's own Step 6 pseudocode shows `assert_monitoring_writer_landed()` (entry
   criterion) as the literal first statement of `run_codex_replay()`, with
   `require_live_consent(env)` second. The orchestrating Implement-phase instructions for this
   ticket carried an explicit, architecture-approved critical constraint stating the consent check
   must be "the literal first two statements" of `run_codex_replay()`, strictly before any other
   check. Implemented as: `require_live_consent(env)` first, `assert_monitoring_writer_landed(...)`
   second. This does not change behavior for any currently-passing test (neither check touches
   `subprocess`/`tempfile`), and both orderings satisfy Step 6's own Verify text ("consent checked
   before subprocess is ever touched") — but the literal statement order in the source differs
   from this plan's illustrative pseudocode. Recorded here per this project's "never silently
   deviate" rule.
2. **Step 11 shadow-mode comparison: `claude_gate_result` derivation normalized, not read verbatim
   from the fixture's raw verdict field.** This plan's Step 11 description says
   `claude_gate_result` is "Review phase's real recorded verdict, from the fixture" — read
   literally, this is the raw string `"APPROVED"`. The first real, consent-gated run of
   `test_shadow_mode_comparison.py` during Implement genuinely failed with this literal reading:
   `codex_gate_result` (sourced from `CodexReplayOutcome.final_status`, which
   `tools.agent_replay.runner.replay_slice()` only ever sets to the literal string `"ok"` on a
   passing Review, never `"APPROVED"`) could never equal the raw `"APPROVED"` string, making
   `match` structurally always `False` for any successful run — not a real Codex-vs-Claude
   behavioral divergence, but a vocabulary mismatch in this ticket's own comparison code.
   `shadow_mode.py::compare_claude_and_codex()` was fixed to normalize
   `claude_gate_result = "ok" if review_verdict == "APPROVED" else review_verdict` — the same
   verdict-to-status mapping `replay_slice()` itself applies — so both sides of the comparison
   speak the same vocabulary. Re-run with real consent granted: `match=True`, genuinely observed,
   not predicted. This bug was caught specifically because Step 7/11 required a real, non-simulated
   invocation, exactly as intended.
