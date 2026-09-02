"""Deterministic static backstop for the `test-scoper` gate's directory-coverage judgment.

Built for TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP: `TCK-20260818-STANDARD-KGMCP-
CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD` legitimately changed `tools/retrieval_cache.py` (new
table, schema version bump) but its Test phase's `pytest_command` never covered `tests/tools/` —
the two pre-existing tests that broke (`test_knowledge_gateway_cache.py`,
`test_knowledge_gateway_redaction.py`) both live there. Root cause: `test-scoper`'s own Test
Directory Map only ever documented `src/` -> `tests/unit/`; it had no entry at all for `tools/`
(a second, equally-real source tree — 52 files under `tools/*.py` alone, 128 test files under
`tests/tools/`). That agent's map/rules are now fixed too (`.claude/agents/test-scoper.md`), but
per this project's stated preference for a structural guard over discipline alone when one is
feasible (this ticket's own Assumptions/Open Questions), this module gives the Test phase a
deterministic, code-level check that the actual `pytest_command` the agent ran really does cover
every directory implicated by `files_changed` — not just trusting the agent's own judgment a
second time.

One check function, one aggregator, matching `architecture_reviewer_static.py`'s shape:

- `expected_test_dirs_for` — pure mapping function, changed file path -> expected test directory
  (or `None` if no mapping rule applies — e.g. `docs/`, `tickets/`, config files). Mirrors
  `.claude/agents/test-scoper.md`'s Test Directory Map exactly; keep both in sync if either
  changes.
- `check_test_scope_coverage` — the aggregator: for each changed file with a known expected test
  directory, checks whether that directory string appears anywhere in the real
  `pytest_command` string test-scoper reported running. Returns `FAIL` (not `SKIP`) for a missing
  directory — this is the one check in the gate_checks/ family designed to be a hard blocker, not
  an advisory judgment, because the failure mode it guards against (a broken pre-existing test
  that ships to CI) is unambiguous and doesn't need LLM judgment to detect.

**Deliberately narrow, and disclosed as such**: this checks that the *bare, whole directory*
(e.g. `tests/tools/`, not a specific file inside it) appears in `pytest_command` as a standalone
path token — deliberately stricter than a plain substring check, since a command naming only the
ticket's own new test files would otherwise contain the directory string as a path prefix and
falsely "pass" (this is exactly the real incident's shape: the reported command DID mention
`tests/tools/...` — as a prefix of the new tests it wrote — while never running the whole
directory, so the pre-existing broken tests were never executed). It does not verify that every
individual relevant test file within a covered whole-directory run actually executed (e.g. a
`-k` filter or `--ignore` flag after a bare directory reference is invisible to this check). It
also cannot see whether the reported `pytest_command` was the command *actually executed* vs. one
the agent merely intended to run — that trust boundary still rests on `test-scoper`'s own Step 4
("Run the command via Bash. Capture stdout/stderr."). Closing those two residual gaps is out of
scope for this ticket; this check closes the specific, confirmed, real failure mode (a whole
source-tree directory silently never in the map at all, compounded by a command that lists
individual files instead of the directory).

No CLI/argparse entry point — consumed exclusively via `python3 -c "..."` from
`.claude/workflows/implement-ticket.js`'s Test phase, mirroring
`architecture_reviewer_static.run_architecture_checks`'s own consumption pattern.
"""

import re

# ---------------------------------------------------------------------------
# Directory mapping — keep in sync with .claude/agents/test-scoper.md's Test Directory Map
# ---------------------------------------------------------------------------

# tools/<subdir>/... -> tests/<subdir>/... (1:1 same-name mirror; checked before the flat-tools
# fallback below, longest-prefix-first so e.g. "agent_codex_pilot_orchestration" doesn't get
# shadowed by a shorter "agent_codex" that doesn't actually exist as a directory here).
_TOOLS_SUBDIR_MIRROR_PREFIXES = (
    "tools/agent_codex_live_transport/",
    "tools/agent_codex_pilot_entrypoint/",
    "tools/agent_codex_pilot_executor/",
    "tools/agent_codex_pilot_guardrails/",
    "tools/agent_codex_pilot_orchestration/",
    "tools/agent_codex_posttool_adapter/",
    "tools/agent_codex_realrepo_pilot_harness/",
    "tools/agent_codex_runtime_shadow/",
    "tools/agent_orchestration_claude_adapter/",
    "tools/agent_orchestration_codex_adapter/",
    "tools/agent_orchestration/",
    "tools/agent_replay_codex/",
    "tools/agent_replay/",
)

# src/<subsystem>/... -> tests/unit/<subsystem>/... — only the subset that test-scoper's own map
# documents; a src/ change under a subsystem not listed here is intentionally left unmapped
# (SKIP, not FAIL) rather than guessing a directory that might not exist.
#
# `ai` and `systems` are DELIBERATELY absent, not an oversight (TCK-20260902-HOTFIX-TEST-SCOPE-
# COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP investigated and disclosed this after
# TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE found both fell through this map silently). Neither
# has a single reliable owning `tests/unit/<x>/` directory the way every subsystem above does:
# - `src/ai/coming_of_age.py`'s own real test lives in `tests/unit/strategic/`, not
#   `tests/unit/ai/` — a grep of real test-file references to `src/ai/*` across `tests/unit/` hits
#   `strategic/` (12), `ai/`+`ai/goals/` (4), `domains/adventure/`, `domains/optimization/`,
#   `observability/`, `systems/`, `world/` (1 each). No single directory is even the dominant real
#   owner, let alone universal.
# - `src/systems/` is not one subsystem but 5 real sub-packages (`lifecycle_systems/`,
#   `strategic_systems/`, `world_systems/`, `social_systems/`, `economy_systems/`), each tested by
#   a genuinely different, sometimes multi-directory set of real owners (e.g. `lifecycle_systems/`
#   spans `tests/unit/world/`, `tests/unit/strategic/`, `tests/unit/progression/`;
#   `economy_systems/` is tested only under `tests/integration/scenarios/` and
#   `tests/architecture/` — not `tests/unit/` at all). Unlike `domains/` (also multi-subpackage but
#   safely mapped below), `systems/`'s sub-package tests are NOT nested under one parent test
#   directory the way `tests/unit/domains/<subpkg>/` nests every `src/domains/` subpackage — there
#   is no structural equivalent to point at.
# Forcing either into this flat 1:1 map would make this check require the WRONG directory for many
# real tickets — actively worse than today's silent skip. The real backstop for both is
# `.claude/agents/test-scoper.md`'s cross-cutting-expansion grep-sweep step (Scoping Rules), which
# `src/systems/` already triggers and `src/ai/` was added to trigger by the same ticket that added
# this comment. See `tests/tools/test_test_scope_coverage_static.py`'s guard test for the two
# paths this reasoning covers.
_SRC_UNIT_SUBSYSTEMS = frozenset({
    "api", "campaigns", "cognition", "combat", "config", "content", "content_semantics", "core",
    "diagnostics", "domains", "entity", "kernel", "lab", "lab_agent", "movement", "observability",
    "optimization", "perf", "platform", "progression", "quest", "resource", "social", "strategic",
    "tactical", "views", "world", "worldassembly", "worldbuilding", "worldgeneration",
    "worldmodules",
})


def expected_test_dirs_for(path: str) -> "str | None":
    """Pure mapping: changed file path -> expected test directory substring, or None if this
    module has no rule for it (docs/, tickets/, config files, unrecognized src/ subsystem, etc.)
    — None means "not this check's concern", never "no tests needed"."""
    if path.startswith("tools/"):
        for prefix in _TOOLS_SUBDIR_MIRROR_PREFIXES:
            if path.startswith(prefix):
                mirror_name = prefix.split("/")[1]
                return f"tests/{mirror_name}/"
        if path.startswith("tools/agent-monitoring/") or path.startswith("tools/gate_checks/"):
            return "tests/tools/"
        if re.match(r"^tools/[^/]+\.py$", path):
            return "tests/tools/"
        return None

    if path.startswith("src/"):
        parts = path.split("/")
        if len(parts) >= 2 and parts[1] in _SRC_UNIT_SUBSYSTEMS:
            return f"tests/unit/{parts[1]}/"
        return None

    return None


def _directory_is_covered(expected_dir: str, command: str) -> bool:
    """True iff `command` references the BARE directory (optional trailing slash) as a standalone
    path token — e.g. `pytest tests/tools/ -v` — not merely as a prefix of one specific file
    within it, e.g. `pytest tests/tools/test_foo.py -v`. This is deliberately strict: it matches
    the Scoping Rule (`.claude/agents/test-scoper.md`) requiring the *whole* directory to run for
    a `tools/` change, never a guessed subset — a command naming only the new tests a ticket wrote
    is exactly the shape of the real incident this check exists to catch (the broken pre-existing
    tests were never in that subset), so counting it as "covered" would silently defeat the check.
    """
    dir_no_slash = expected_dir.rstrip("/")
    pattern = r"(?:^|\s)" + re.escape(dir_no_slash) + r"/?(?=\s|$)"
    return re.search(pattern, command) is not None


def check_test_scope_coverage(files_changed, pytest_command: str) -> "list[dict]":
    """For each changed file with a known expected test directory (`expected_test_dirs_for`),
    check whether the real `pytest_command` references that directory as a bare, whole-directory
    token (`_directory_is_covered`) — not just a specific file inside it. Returns a flat
    `list[dict]` of `{"condition", "status", "evidence"}` — matches
    `done_checker_static.run_static_precheck`'s shape. `status` is `PASS` or `FAIL` (never `SKIP`
    for a file this module has a rule for — that's the point of this being a hard check).

    An empty `pytest_command` (should never happen — schema requires it) is treated as covering
    nothing; every mapped file fails.
    """
    command = pytest_command or ""
    results: "list[dict]" = []
    checked_dirs: "set[str]" = set()

    for path in files_changed:
        expected_dir = expected_test_dirs_for(path)
        if expected_dir is None:
            continue
        if expected_dir in checked_dirs:
            continue
        checked_dirs.add(expected_dir)

        covered = _directory_is_covered(expected_dir, command)
        results.append({
            "condition": f"test_scope_covers:{expected_dir}",
            "status": "PASS" if covered else "FAIL",
            "evidence": (
                f"pytest_command includes '{expected_dir}' (required by changed file {path!r} "
                f"and possibly others mapping to the same directory)"
                if covered else
                f"pytest_command does NOT include '{expected_dir}', but {path!r} changed and maps "
                f"to it — a pre-existing test in that directory could break silently and ship to "
                f"CI unverified (real prior incident: TCK-20260818-STANDARD-KGMCP-CACHE-"
                f"ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD / TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-"
                f"GUARD-TESTS). Re-scope pytest_command to include this directory before Finalize."
            ),
        })

    return results
