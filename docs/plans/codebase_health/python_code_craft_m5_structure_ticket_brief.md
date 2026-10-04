---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, planning, process-improvement]
---

# Python Code Craft — M5 Structure Ticket Brief

Scoping brief for `create-tickets`. The binding plan is
`docs/plans/codebase_health/python_code_craft_roadmap.md` (rev 2; M5 row in Section 7, package registry in
6.4, toolchain in 6.2, owner decisions in Section 8). M1 to M3 are done; M4 is in its advisory soak until
2026-10-17 (`agent-working/tickets/todos/python-code-craft-gates/`). The roadmap allows M5 to start after
M3. The owner chose M5 as the next codebase batch on 2026-10-04.

## Constraints that apply to every ticket

- **No file under `src/` may be modified** (decision 8.7). This includes moving, merging or deleting a
  package: the structure audit produces decisions only. Every ticket's acceptance criteria include a
  `git diff --stat` check showing no `src/` path.
- Governing files (`CLAUDE.md`, `.claude/settings.json`, Claude Code hooks, `.claude/agents|workflows|skills/`)
  are not edited. Agent guidance that points at the package registry is an M6 request to agent-working.
- **Nothing in this batch blocks a PR.** New checks are advisory. A check joins the blocking set only
  after its own two-week soak (decision 8.10), in a ticket of its own.
- **The M4 soak is not disturbed.** No ticket here changes a threshold, the ruff or complexipy versions,
  or the rows already in `codebase/baselines/code_health_exceptions.jsonl`. New ast-grep rows are added
  under their own tool key, so the M4 flip ticket can exclude them by tool.
- Tests that pin CI or the Makefile may be edited (decision 8.11); the `testing` planner is told before the
  change lands. Tests owned by other domains (the `tests/architecture/` boundary tests) are **not** edited or
  deleted here: replacing one is a later ticket agreed with its owner.
- Heavy local runs go one at a time under a memory cap (`systemd-run --user --scope -p MemoryMax=2G`).

## Facts measured 2026-10-04 (planner, on `main` at b9251cf5)

- **36 tracked top-level packages in `src/`**, 744 `.py` files. Largest by lines: `observability` 27.6k
  (136 files), `engine` 19.8k (94), `domains` 16.6k (133), `systems` 8.0k, `api` 8.0k, `lab` 8.0k,
  `core` 9.5k. Smallest: `views` 63 lines (1 file), `logging` 71 (1), `actions` 88 (2), `economy` 159 (3),
  `platform` 192 (4), `runtime` 193 (2), `testing` 276 (2), `replay` 282 (2), `strategy` 300 (5).
- Importers outside the package itself (src, tests, tools, codebase): `views` 1, `actions` 2, `runtime` 2,
  `testing` 2, `quests` 5, `logging` 6, `worldgeneration` 6, `replay` 8, `strategy` 9, `economy` 10,
  `content_semantics` 30, `worldmodules` 42, `platform` 157. A grep count, not an import graph.
- **`src/social/` and `src/graphify-out/` are untracked local leftovers** in the main checkout (a
  `__pycache__` only; a June graphify output), not packages. The roadmap's "empty `social`" is this. The
  audit records them as local clutter for the owner to delete; no ticket action.
- `registries/system_registry.jsonl` (7 rows: combat, progression, cognition, social, ...) names
  gameplay **systems**, not packages. The package registry may reference a system name per row; it does
  not duplicate that registry.
- ast-grep, import-linter and grimp appear nowhere in `pyproject.toml`, `uv.lock`, the Makefile or CI.
- Reviewer-only rules in `docs/guidelines/python_code_standard.md` that a structural pattern can check:
  **N3** (importing a `_private` name from another module), **N4** (version markers in new names:
  `V2`, `_v2`, `_new`), **E3** (silent exception swallowing: an `except` body that is only `pass`;
  about 107 occurrences in `src/` by a rough grep), and the `dict[str, Any]` part of **T3** in public
  signatures. M5 (new top-level `src/` package) is checked by the package registry, not by ast-grep.
- The RNG determinism boundary is already enforced by
  `tests/integration/kernel/test_phase2_determinism.py` (P0 determinism work); ast-grep would only be a
  cheaper home for it.
- **Import-boundary tests over `src/`: 31 files, 41 distinct rules**, spread across `tests/architecture/`,
  `tests/unit/*`, `tests/integration/*` and `tests/api/` (an inventory by a read-only search, not
  re-verified rule by rule). 37 rules can be written as import-linter `forbidden` contracts; about 11
  of those lose detail (they pin imported names, exact counts or name keywords). 4 cannot be written:
  `rendering` may import only stdlib and `src`; the `numpy.random` text check; the `random.Random`
  attribute check; and one test that requires an import (`compute_terrain_histogram` from
  `rendering.density`). All AST checks use `ast.walk`, so function-local imports count, as they do in
  grimp. Only 7 tests skip `if TYPE_CHECKING:` imports; import-linter's
  `exclude_type_checking_imports` is all-or-nothing per contract. `forbidden` contracts also flag
  indirect chains unless `allow_indirect_imports = true`, which the current direct-only tests need.
- **One existing boundary test looks like a no-op:**
  `tests/architecture/test_phase19_observability_boundaries.py::test_hot_path_does_not_import_heavy_analyzers`
  matches the bare `observability.*` prefix, so it never fires on real `src.` imports; a comment in the
  test says a correct check would flag `kernel.py`. Concern 4 confirms it with an injected violation; the
  finding goes to the test's owner (testing planner), and the codebase domain does not fix it.
- Layer model: `docs/audits/D14_coupling_depth.md` ("Layer Architecture"): content isolated; core imports
  nothing; domains → core; engine → core + domains (`pipeline.py` is the single engine→domains point);
  observability → engine; api → engine + core; lab → engine; systems → core + engine with pinned
  exceptions. It covers 8 of the 36 packages; the audit (Concern 1) places the other 28.

## Owner decisions (recorded 2026-10-04; both as recommended)

1. **Layout:** the package registry and ast-grep rules live in new codebase folders (table below), not
   in `registries/`.
2. **ast-grep soak:** the M4 flip on 2026-10-17 excludes the `ast_grep` tool; the rules get their own
   14-day advisory soak and their own flip ticket (Concern 3).
3. **Parity `proof_type`** (for the remediation epic, not M5): the 25 values outside the enum
   (`feature` 13, `architecture` 6, `unit` 5, `integration` 1) are **remapped** by each owning domain's
   remediation child, entry by entry with a reason; the enum is not extended.

## Layout

| Path | Holds |
|---|---|
| `codebase/structure/` | the package registry data file `package_registry.jsonl`, its loader and validator (`python3 -m codebase.structure.packages validate`), and later the import-linter adapter |
| `codebase/rules/` | ast-grep `sgconfig.yml`, one YAML file per rule, and ast-grep's own rule tests |
| `pyproject.toml` | `[tool.importlinter]`, only if Concern 4 recommends adoption (tool config stays at the root, as for ruff and mypy) |

This differs from roadmap 6.4, which named `registries/package_registry.jsonl`: since the root move,
`registries/` holds only cross-domain registries, and the package registry is owned by the codebase domain.
The roadmap is updated in Concern 1's ticket.

## Concern 0: Epic — Python Code Craft M5 Structure

Scope-only epic tracking tickets 1 to 4. Closes when all four are done. Any follow-up it produces
(an adoption ticket for import-linter, a blocking flip for the ast-grep rules, package merges for the
rpg domain) is filed, not done, by this epic.

## Concern 1: Structure audit of `src/` packages (decisions only)

- One decision record, `docs/plans/codebase_health/src_package_structure_audit.md`, with one row per
  tracked top-level package: purpose in one line, size (files, lines), outside importers, the
  architectural layer it sits in (extending D14's layer model, see Facts, to all 36 packages; where
  D14 and the real import graph disagree, record both), and a decision:
  `keep`, `merge-candidate into <pkg>`, `retire-candidate`, or `investigate`.
- It focuses on the packages the roadmap named: `actions`, `logging`, `views`, `runtime`, `replay`, the
  `world*` family (`world`, `worldassembly`, `worldbuilding`, `worldgeneration`, `worldmodules`),
  `content` / `content_semantics`, plus the small ones in Facts (`economy`, `platform`, `testing`,
  `strategy`, `quests`). Overlap is shown with evidence (shared responsibilities, import edges), not
  assumed.
- Every non-`keep` decision names the domain that would own the move (normally `rpg-planner`) and goes
  to that planner as an outbox note. Nothing moves in M5 or before the owner reopens `src/` (M7).
- Out of scope: subpackages of `domains/`, `observability/`, `engine/` (the registry rows are top-level
  only); renaming anything.

## Concern 2: Package registry, seeded from the audit

- `codebase/structure/package_registry.jsonl`: one row per tracked top-level `src/` package. Fields:
  `package`, `purpose`, `layer` (from the layer model the audit uses), `status`
  (`active | legacy | frozen`), `strictness_tier` (a name for a future per-package gate level; every
  row starts at the same tier, and the tier names are defined in the ticket), `exemplar_modules`
  (0 to 3 paths), `do_not_imitate` (0 or more paths, each with a reason), `system` (optional, a name
  from `registries/system_registry.jsonl`), `audit_decision`, `added_date`, `reviewed`.
- Loader and validator, following `codebase/health/registry.py` and `tools/capability_envelope_baseline.py`:
  the schema rejects unknown fields; every row's package exists on disk; **every tracked top-level
  package has exactly one row** (a new package without a row fails the validator: that is the
  standard's rule M5 made checkable); cited module paths exist.
- The validator runs in the advisory `code-health` job (a step that reports and never fails the PR) and
  in `tests/codebase/`. Making "new package without a row" blocking is a later ticket.
- Docs: roadmap 6.4 path updated; `codebase/README.md` row for `structure/`; standard rule M5's
  Enforcement cell names the validator; a row in `docs/guidelines/subsystem_ownership_lifecycle.md`.
- Out of scope: per-package gates driven by `strictness_tier` (later); agent guidance pointing at
  exemplars (M6 request).

## Concern 3: ast-grep rule pack, advisory through the ratchet

- Add `ast-grep-cli` (pinned exactly) to the `lint` group. Rules in `codebase/rules/`, each with a
  message that states the fix (roadmap 6.2), and ast-grep rule tests (valid and invalid snippets) run by
  `ast-grep test` from `tests/codebase/`.
- First rules, from the reviewer-only standard rules in Facts: **N3**, **N4** (names in `def` and
  `class` only), **E3** (`except` whose body is only `pass`). The T3 `dict[str, Any]` rule is
  included only if Investigate shows a precise pattern (public functions only, signatures only);
  otherwise it stays a reviewer rule and the ticket says why.
- An adapter in `codebase/health/adapters.py` reads ast-grep's JSON output into the normalised finding
  format, keyed by file and enclosing symbol (roadmap 6.3), under its own tool key `ast_grep`. Seed only
  the `ast_grep` rows on `main`; the rows of every other tool are untouched (M4 soak constraint).
- The rules report in the advisory `code-health` job and in `make code-health`. The SARIF changed-line
  feedback includes them if `codebase/gates/sarif_feedback.py` takes a new tool without a structural
  change; otherwise that is noted as a follow-up.
- **Blocking interplay with M4:** the M4 flip ticket (`TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`)
  excludes the `ast_grep` tool from its blocking set. This ticket adds that exclusion to the flip
  ticket's scope and files its own flip ticket, dated 14 days after its merge.
- Docs: standard rules N3, N4, E3 get the rule ID in their Enforcement cell.
- Out of scope: porting existing hand-written AST tests to ast-grep (Concern 4 reports which could
  move); rules beyond the standard; autofix.

## Concern 4: import-linter evaluation (report only)

- Express the existing import-boundary tests as import-linter contracts in a scratch config (not
  committed into `pyproject.toml`), plus one `layers` contract built from the package registry's
  `layer` field. Run over `src/` on one commit.
- Record: version, wall time, peak memory; for each existing test, whether the contract catches the same
  violations (inject one known violation per rule in a scratch copy and confirm both fail); how
  `TYPE_CHECKING` and function-local imports are treated versus the existing tests; how many current
  `src/` violations each contract reports (the baseline import-linter would need, through its
  `ignore_imports`); the rules no contract can express.
- Start from the 41-rule inventory in Facts; re-verify it, do not trust it. Run each contract both with
  and without `allow_indirect_imports` and `exclude_type_checking_imports`, and report the difference.
- Confirm or refute the phase19 no-op finding with an injected violation; if confirmed, send it to the
  testing planner as an outbox note (no test edit here).
- Also list which hand-written AST tests in `tests/architecture/` could become ast-grep rules (for
  Concern 3's follow-ups), without changing them.
- Output: a decision record in `docs/plans/codebase_health/` (like the type-checker trial),
  recommending **replace** (named tests retire, owner and testing planner agree), **add** (contracts for
  what the tests do not cover, mainly the layer order), or **drop**. No dependency, CI or test change.
- Roadmap rule (Section 4): import-linter must replace or clearly add to the existing tests, never run
  as a second copy of them.

## Order

1 first (the audit's layer column feeds 2 and 4). 2 after 1. 3 is independent and may run in parallel
with 1 and 2, but merges after the M4 flip ticket has been updated with the `ast_grep` exclusion (it
does that itself). 4 after 2 (its `layers` contract reads the registry).

## Not in this batch

M6 (agent integration requests: exemplar pointers, the edit hook), M7 (refactor lane, deferred; any
package merge from the audit lands there), blocking flips for the package-registry validator and
the ast-grep rules (each filed by its ticket), and the parity-ledger remediation children (other
domains).
