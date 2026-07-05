"""Deterministic static backstops for the `architecture-reviewer` gate.

Built for TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER: `architecture-reviewer`'s durable-state/
API-boundary/reason-metadata judgments are entirely LLM-judged today. This module gives the
Architecture-Verify phase (a new, second, post-Implement `architecture-reviewer` call — see
`.claude/workflows/implement-ticket.js`) a deterministic pre-check for a narrow subset of those
judgments, run against the *actual* changed files (`implementation.files_changed`), since the
*original* pre-Implement Review call has no code to parse yet (only `plan.md` prose).

Three check functions, one aggregator:

- `check_durable_state_mutation` — AST scan for direct durable-state mutation bypassing frozen-
  dataclass discipline (`object.__setattr__` outside an explicit field-name allowlist, nested
  mutable-container mutation by field-name heuristic, direct nested attribute assignment).
- `check_api_boundary_exposure` — AST scan of `src/api/` top-level route functions for a return
  annotation naming a raw domain model class instead of a shaped read model (`Dict`/`*Response`).
- `check_reason_metadata_smuggling` — regex scan for a durable-meaning-in-a-string anti-pattern:
  a `reason`/`metadata` value packed from 2+ values via a non-alphanumeric delimiter, later
  unpacked via a matching `.split(...)` elsewhere in the same file.

**Deliberately imperfect, and disclosed as such** (per the ticket's own stated preference for "a
first version that catches only the clearest violations... over an over-ambitious one that's
unreliable"): each check function's docstring states plainly what it cannot see. In particular:

- There is no `src/engine/authoritative_pipeline*` module in this codebase (confirmed absent by
  investigation) — the durable-state check is therefore field-name-based only, never a directory-
  prefix test, and does not attempt to resolve which object a `.items`/`.global_resources`-shaped
  attribute chain actually belongs to (no type inference available in plain `ast`).
- The reason/metadata check has **zero confirmed historical incidents** behind it in this repo
  (investigation.md searched `git log`, `tickets/done/`, `docs/archive/`, and all 31 recorded
  `NEEDS_CHANGES`/`BLOCKED` architecture-review verdicts in `agent-monitoring/events.jsonl` and
  found none) — its patterns are derived from CLAUDE.md's Durable State Rule prose, not mined from
  a real corpus of past violations.

Every parse-dependent function tolerates malformed/legacy input gracefully (`SKIP` with evidence,
never raise) — this scan runs against every changed `src/` file on every ticket and must never crash
the gate it backstops, mirroring `parity_updater_static.derive_mapping`'s `except Exception: continue`
convention (applied per-file here, since this is a file-scoped check, not a corpus-scoped one).

Mirrors `tools/gate_checks/done_checker_static.py`'s shape: plain functions, `(status, evidence)`
tuples, a `run_*` aggregator returning `list[dict]`, no argparse/CLI — consumed exclusively via
`python3 -c "..."` from `.claude/workflows/implement-ticket.js`.
"""

import ast
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Check 1 — durable-state mutation
# ---------------------------------------------------------------------------

_CACHE_SUFFIX = "_cache"

# Named exceptions for `object.__setattr__` field names that do not end in `_cache` but are
# confirmed-legitimate at their real call sites (investigation.md's grep of all ~13 non-test
# `object.__setattr__` call sites in src/, plus a re-grep at implementation time that additionally
# surfaced `src/simulation_quality/weights.py`'s `ScoringWeights` fields). Field-name-based, never
# path-based — two of the legitimate call sites (`src/world/environment.py:87`,
# `src/systems/strategic_systems/intelligence.py:240`) are outside `src/engine/` entirely, so a
# directory-prefix test would misfire on them.
_ALLOWLISTED_SETATTR_FIELDS = {
    "_index_hits",
    "_index_misses",
    "world_indexes",
    "transient_claims",
    "occupancy_snapshot",
    "_opt_profile",
    "_force_full_scan",
    "_flat_rules",
    "_pillar_weights",
}

_MUTATING_METHODS = {
    "append", "extend", "insert", "remove", "pop", "popitem", "update", "clear", "sort", "add", "discard",
}

# Confirmed at implementation time (not anticipated by plan.md, which claimed the depth>=2
# attribute-assignment pattern has "no sanctioned legitimate use" in this codebase): real
# production code in src/lab/workflows.py configures MagicMock instances with
# `mock_world_repo.list_worlds.return_value = [...]`, an identical AST shape to
# `entity.combat.hp = 5`. Excluding these two canonical unittest.mock attributes is a narrow,
# evidence-driven exception — not a broad allowlist — since they are never legitimate durable-state
# field names.
_MOCK_CONFIGURATION_ATTRS = {"return_value", "side_effect"}

# Deliberately short and incomplete (per investigation.md/plan.md) — mined only from
# `src/core/models/inventory.py:42` (`InventoryComponent.items`) and `src/core/state.py:1124`
# (`AuthoritativeState.global_resources`). Must be extended by hand as new mutable durable-state
# fields are added; this is an accepted, ongoing maintenance cost, not a bug.
_KNOWN_MUTABLE_CONTAINER_FIELDS = {"items", "global_resources", "trust_history"}


def _is_object_setattr_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "__setattr__"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "object"
        and len(node.args) == 3
    )


def _literal_str(node) -> "str | None":
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_allowlisted_setattr_field(field_name: str) -> bool:
    return field_name.endswith(_CACHE_SUFFIX) or field_name in _ALLOWLISTED_SETATTR_FIELDS


def check_durable_state_mutation(file_path: str, source: str) -> "tuple[str, str]":
    """Flag direct durable-state mutation outside the sanctioned frozen-dataclass discipline.

    Three independent violation shapes (FAIL with a file:line citation if any is found; PASS
    otherwise):

    1. `object.__setattr__(obj, "field", value)` where `field` is a string literal not matching
       `_ALLOWLISTED_SETATTR_FIELDS` (the `_cache`-suffix convention, confirmed by
       `src/engine/apply.py`'s own `replace()` helper, plus a short named-exception list). A
       non-literal field name (e.g. built from a variable) is skipped, never guessed.
    2. A subscript-assignment or mutating-method call (`.append`/`.update`/etc.) on an attribute
       chain ending in a name from `_KNOWN_MUTABLE_CONTAINER_FIELDS` — the highest-value, hardest-
       to-catch case (frozen dataclasses block *rebinding* their own fields but not mutation of a
       mutable object a field already points to).
    3. Direct nested attribute assignment (`entity.combat.hp = 5`) — an attribute-of-attribute
       assignment chain with no `object.__setattr__` involved. This pattern would already raise
       `FrozenInstanceError` at runtime on any real frozen dataclass in this codebase; this check's
       value is catching it before a test run, not catching a bug that would otherwise ship.
       Excludes `.return_value`/`.side_effect` assignment targets (`_MOCK_CONFIGURATION_ATTRS`) —
       confirmed at implementation time that real production code (`src/lab/workflows.py`'s
       `MagicMock` configuration, e.g. `mock_world_repo.list_worlds.return_value = [...]`) matches
       this exact AST shape and is not a durable-state violation; this is the one narrow, evidence-
       driven exception to (3)'s otherwise-unconditional rule.

    DISCLOSED LIMITATIONS (do not silently "fix" these — they are accepted, per investigation.md):
    - Field-name matching cannot resolve `.items`/`.global_resources` to a *specific* class's
      field — an unrelated object with a same-named attribute will false-positive (no type
      inference is available from plain `ast`).
    - The allowlist in (1) is field-name-only, not (file, field) paired. Two files whose entire
      purpose IS legitimate authoritative-state construction — `src/engine/apply.py` (per-field
      `object.__setattr__` during its own `replace()`-style helpers, on a freshly `object.__new__`'d
      instance) and `src/core/state.py` (per-field `object.__setattr__` inside its own dataclasses'
      `__post_init__`/canonicalization methods) — use dozens of ordinary domain field names (e.g.
      `combat`, `role`, `position`, `identity`) this way, and the same shape recurs more widely
      across the engine's own internal state-reconstruction code (confirmed at implementation time
      against real files: `src/engine/kernel.py`'s direct-nested-attribute-assignment pattern,
      `src/engine/pipeline_phases/actions.py`'s `object.__setattr__(sliding_state, "entities", ...)`
      sliding-window rebuild). None of these are special-cased here (doing so would require either
      a directory/file-path exception — rejected per investigation.md's "field-name-based only,
      never path-based" design — or growing the allowlist to cover nearly every domain field name,
      which would erode this check's value everywhere else). If a future ticket's diff includes any
      of the engine's own internal apply/kernel/pipeline construction code, expect a non-trivial
      false-positive rate on their own field-replacement logic; this is a known, disclosed gap, not
      a silent one.
    - No attempt is made to distinguish `__post_init__`/authoritative-construction code from
      genuinely external mutation — this check is file-scoped and syntactic only.

    Never raises: unparseable source returns `("SKIP", ...)`.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return ("SKIP", f"unparseable: {e}")

    violations: "list[str]" = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if _is_object_setattr_call(node):
                field_name = _literal_str(node.args[1])
                if field_name is not None and not _is_allowlisted_setattr_field(field_name):
                    violations.append(
                        f"{file_path}:{node.lineno}: object.__setattr__ bypass on "
                        f"non-allowlisted field '{field_name}'"
                    )
            elif isinstance(node.func, ast.Attribute) and node.func.attr in _MUTATING_METHODS:
                receiver = node.func.value
                if isinstance(receiver, ast.Attribute) and receiver.attr in _KNOWN_MUTABLE_CONTAINER_FIELDS:
                    violations.append(
                        f"{file_path}:{node.lineno}: mutating-method call "
                        f"'.{receiver.attr}.{node.func.attr}(...)' on known mutable-state field "
                        "(name-heuristic match, not type-resolved)"
                    )
        elif isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Attribute)
                    and target.value.attr in _KNOWN_MUTABLE_CONTAINER_FIELDS
                ):
                    violations.append(
                        f"{file_path}:{node.lineno}: subscript assignment on known mutable-state "
                        f"field '.{target.value.attr}[...]' (name-heuristic match, not type-resolved)"
                    )
                elif (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Attribute)
                    and target.attr not in _MOCK_CONFIGURATION_ATTRS
                ):
                    violations.append(
                        f"{file_path}:{node.lineno}: direct nested attribute assignment "
                        f"'...{target.value.attr}.{target.attr} = ...' — would already raise "
                        "FrozenInstanceError at runtime on a real frozen dataclass"
                    )

    if violations:
        return ("FAIL", "; ".join(violations))
    return ("PASS", "no durable-state-mutation violations detected")


# ---------------------------------------------------------------------------
# Check 2 — raw-domain-object API-boundary exposure
# ---------------------------------------------------------------------------

_DOMAIN_MODEL_SOURCE_FILES = (
    "src/core/state.py",
    "src/core/strategic.py",
    "src/core/self_model.py",
)


def _collect_domain_class_names(base_dir: "Path | str" = Path(".")) -> "set[str]":
    """Dynamically derive the raw-domain-model class name set from the real source of truth at
    call time (mirrors `parity_updater_static.derive_mapping`'s own convention) — avoids a second
    hardcoded list that drifts from the actual domain model as classes are added/renamed.

    Skips a file silently (no raise) if it doesn't exist or fails to parse.
    """
    base = Path(base_dir)
    paths = [base / p for p in _DOMAIN_MODEL_SOURCE_FILES]
    models_dir = base / "src/core/models"
    if models_dir.is_dir():
        paths.extend(sorted(models_dir.glob("*.py")))

    names: "set[str]" = set()
    for path in paths:
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                names.add(node.name)
    return names


def _annotation_base_name(annotation: ast.expr) -> "str | None":
    while isinstance(annotation, ast.Subscript):
        annotation = annotation.value
    if isinstance(annotation, ast.Attribute):
        return annotation.attr
    if isinstance(annotation, ast.Name):
        return annotation.id
    return None


def check_api_boundary_exposure(
    file_path: str, source: str, domain_class_names: "set[str]"
) -> "tuple[str, str]":
    """Flag a `src/api/` route function whose return annotation names a raw domain model class
    instead of a shaped read model (`Dict[...]` or a `*Response` type).

    Only meaningful for files under `src/api/` — filtering by path is the caller's responsibility
    (see `run_architecture_checks`). Walks top-level `FunctionDef`/`AsyncFunctionDef` nodes only
    (module scope — does not descend into nested/inner functions, and does not descend into class
    bodies, so presenter methods like `StatePresenter.present_entity` are correctly out of scope:
    they are called BY a route, they are not themselves a registered route handler).

    Per function:
    - Leading-underscore names are skipped entirely (never flagged) — confirmed real example:
      `src/api/routes/decisions.py:_get_index`, a private helper never registered as a route.
    - No return annotation at all → `SKIP` for that function, never a silent `PASS` — an
      unannotated handler is genuinely unchecked, not indistinguishable from "checked, clean".
    - Annotation base name (unwrapping `Subscript`/`Attribute`, e.g. `Dict[str, Any]` → `Dict`) in
      `domain_class_names` → `FAIL`.
    - Base name is `Dict` or ends in `Response` → `PASS` (the confirmed real convention).
    - Any other annotation (`str`, `bool`, etc.) → `PASS` — this check's job is to catch raw-
      domain-model exposure specifically, not to enforce every handler use `Dict`/`*Response`.

    Aggregate: `FAIL` if any function-level check is `FAIL`; else `PASS` if at least one function
    was checkable; else `SKIP` if every function was unannotated (or none found).

    DISCLOSED LIMITATION: this check is blind to the more common real gap — a handler with no
    return annotation that returns a raw domain model at runtime. Closing that requires a runtime/
    dynamic check, out of scope for a static `ast` pass (investigation.md).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return ("SKIP", f"unparseable: {e}")

    per_function: "list[tuple[str, str]]" = []
    checked_any = False

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue

        if node.returns is None:
            per_function.append(
                ("SKIP", f"{file_path}:{node.lineno}:{node.name}: no return annotation — cannot statically verify")
            )
            continue

        base_name = _annotation_base_name(node.returns) or ""
        if base_name in domain_class_names:
            per_function.append(
                ("FAIL", f"{file_path}:{node.lineno}:{node.name}: returns raw domain model '{base_name}'")
            )
            checked_any = True
        elif base_name == "Dict" or base_name.endswith("Response"):
            per_function.append(
                ("PASS", f"{file_path}:{node.lineno}:{node.name}: shaped return type '{base_name}'")
            )
            checked_any = True
        else:
            per_function.append(
                ("PASS", f"{file_path}:{node.lineno}:{node.name}: return type '{base_name}' — not a "
                          "raw-domain or shaped-response shape, not flagged")
            )
            checked_any = True

    if not per_function:
        return ("SKIP", f"{file_path}: no top-level route functions found")

    fails = [ev for status, ev in per_function if status == "FAIL"]
    if fails:
        return ("FAIL", "; ".join(fails))
    if checked_any:
        return ("PASS", "; ".join(ev for _, ev in per_function))
    return ("SKIP", "; ".join(ev for _, ev in per_function))


# ---------------------------------------------------------------------------
# Check 3 — reason/metadata-smuggling
# ---------------------------------------------------------------------------

_PACK_ASSIGN_RE = re.compile(
    r"\b(?:reason|metadata)\w*[\"']?\s*[:=]\s*f([\"'])((?:(?!\1).)*)\1",
    re.IGNORECASE,
)
_JOIN_PACK_RE = re.compile(
    r"\b(?:reason|metadata)\w*[\"']?\s*[:=]\s*([\"'])([^\"']*)\1\s*\.\s*join\s*\(\s*\[([^\]]*)\]",
    re.IGNORECASE,
)
_PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")


def _fstring_pack_delimiter(body: str) -> "str | None":
    """Return the delimiter text if `body` is an f-string with 2+ placeholders separated purely
    by non-alphanumeric delimiter text (e.g. `"{a}|{b}|{c}"`); None otherwise (e.g. a single
    placeholder, or placeholders separated by ordinary prose words)."""
    segments = _PLACEHOLDER_RE.split(body)
    placeholder_count = len(segments) - 1
    if placeholder_count < 2:
        return None
    betweens = segments[1:-1]
    if not betweens:
        return None
    for sep in betweens:
        if not sep or any(ch.isalnum() for ch in sep):
            return None
    return betweens[0]


def check_reason_metadata_smuggling(file_path: str, source: str) -> "tuple[str, str]":
    """Flag durable meaning encoded as a delimiter-packed string inside a `reason`/`metadata`
    field, later unpacked via a matching `.split(...)` call elsewhere in the same file — the
    round-trip is the actual signature this check targets, not a single interpolated diagnostic
    value (e.g. `f"Malformed or unparseable run manifest: {e}"`, confirmed clean in
    `src/lab/workflows.py:1176`, is a single placeholder and never matches).

    Text/regex-based (not AST), per the ticket Scope's own "regex check" framing.

    DISCLOSURE — this check has ZERO confirmed historical incidents behind it in this repo.
    investigation.md searched `git log --all --grep`, `tickets/done/`, `docs/archive/`, and all 31
    recorded `NEEDS_CHANGES`/`BLOCKED` architecture-review verdicts in `agent-monitoring/events.jsonl`
    (the actual historical corpus of confirmed findings) and found no real instance of this exact
    pattern. Its regex patterns are derived from CLAUDE.md's Durable State Rule prose alone, not
    mined from any confirmed violation — this is the weakest-evidenced of the three checks in this
    module and must be treated as speculative/preventive, not evidence-backed.

    Never raises: this check does not parse with `ast` at all, so there is no unparseable case;
    a file with no matches simply returns `PASS`.
    """
    pack_hits: "list[tuple[int, str]]" = []

    for m in _PACK_ASSIGN_RE.finditer(source):
        delimiter = _fstring_pack_delimiter(m.group(2))
        if delimiter is not None:
            line = source.count("\n", 0, m.start()) + 1
            pack_hits.append((line, delimiter))

    for m in _JOIN_PACK_RE.finditer(source):
        items = [item for item in m.group(3).split(",") if item.strip()]
        delimiter = m.group(2)
        if len(items) >= 2 and delimiter and not any(ch.isalnum() for ch in delimiter):
            line = source.count("\n", 0, m.start()) + 1
            pack_hits.append((line, delimiter))

    if not pack_hits:
        return ("PASS", "no delimiter-packed reason/metadata field found")

    for line, delimiter in pack_hits:
        split_re = re.compile(r"\.split\(\s*[\"']" + re.escape(delimiter) + r"[\"']\s*\)")
        if split_re.search(source):
            return (
                "FAIL",
                f"{file_path}:{line}: reason/metadata field packed with delimiter {delimiter!r} "
                f"and later unpacked via .split({delimiter!r}) elsewhere in this file — durable "
                "meaning smuggled into a string instead of a typed field",
            )

    return ("PASS", "delimiter-packed candidate(s) found but no matching .split(...) round-trip in this file")


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


def run_architecture_checks(files_changed, base_dir: "Path | str" = Path(".")) -> "list[dict]":
    """Run all applicable checks against each `src/*.py` path in `files_changed`. Non-`.py` and
    non-`src/` paths are skipped silently (docs/tests/config changes are not this check's concern).

    Returns a flat `list[dict]` of `{"condition", "status", "evidence"}` — matches
    `done_checker_static.run_static_precheck`'s shape (the closest structural sibling: a per-
    condition checklist, not a per-file cross-reference like `parity_updater_static`).

    No CLI/argparse entry point — consumed exclusively via `python3 -c "..."` from
    `.claude/workflows/implement-ticket.js`'s Architecture-Verify phase.
    """
    base = Path(base_dir)
    domain_class_names = None
    results: "list[dict]" = []

    for path in files_changed:
        if not path.endswith(".py") or not path.startswith("src/"):
            continue

        try:
            source = (base / path).read_text(encoding="utf-8")
        except OSError as e:
            results.append({
                "condition": f"file_read:{path}",
                "status": "SKIP",
                "evidence": f"could not read {path}: {e}",
            })
            continue

        status, evidence = check_durable_state_mutation(path, source)
        results.append({"condition": f"durable_state_mutation:{path}", "status": status, "evidence": evidence})

        status, evidence = check_reason_metadata_smuggling(path, source)
        results.append({"condition": f"reason_metadata_smuggling:{path}", "status": status, "evidence": evidence})

        if path.startswith("src/api/"):
            if domain_class_names is None:
                domain_class_names = _collect_domain_class_names(base)
            status, evidence = check_api_boundary_exposure(path, source, domain_class_names)
            results.append({"condition": f"api_boundary_exposure:{path}", "status": status, "evidence": evidence})

    return results
