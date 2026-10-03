---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-03
tags: [architecture, planning, benchmarking]
---

# Python Code Craft — Type-Checker Trial: mypy, basedpyright, Pyrefly

Decision record for `TCK-20261003-TYPE-CHECKER-TRIAL` (roadmap `python_code_craft_roadmap.md` 6.2: mypy +
mypy-baseline is primary; basedpyright and Pyrefly are the named trials; `ty` is excluded because its only
suppression path edits source). Report only: nothing in `src/`, `pyproject.toml`, `uv.lock`, CI or the Makefile
changed. Advice, not an adoption: adopting anything would be a new ticket.

## Recommendation

**Keep mypy + mypy-baseline as the primary checker. Do not replace it. Do not add basedpyright. Consider Pyrefly as a
cheap, advisory second opinion after the M4 soak (a new ticket), not as a gate.**

- Replacing mypy would throw away the baseline, the ledger entry (`INFRA-TYPE-001`), the gate module and tests that
  just landed, for no measured gain: both alternatives report **fewer** errors, and 395 of mypy's 1,081 flagged
  (file, line) pairs are reported by neither (Section 4). Fewer errors is not evidence of better accuracy; the
  unique findings were not triaged (Section 6).
- basedpyright costs the most (about 70 s and 1 GB per run, plus a 200 MB Node runtime wheel) and its overlap with
  Pyrefly is high (484 shared lines), so it adds the least that Pyrefly does not.
- Pyrefly is nearly free to run (about 2 s, 207 MB, one 33 MB binary wheel, no dependencies) and has 100 flagged
  lines neither mypy nor basedpyright reports. That is worth a look as an advisory second opinion once the soak is
  over; it is not worth gating.

## 1. What was measured

- **Commit:** `e6b3f97fde4bdce921369e7c5f9190a0c9e379c3` (branch `python-code-craft-gates`). All three checkers ran on
  one clean `git clone --no-hardlinks` of that commit, so uncommitted or ignored files cannot affect the numbers.
- **Scope, identical for all three:** `src/` minus the five V1 packages mypy excludes (`ai`, `town`, `quests`,
  `entities`, `progression`), Python 3.11 semantics, no strict mode, missing third-party imports ignored. Third-party
  packages resolve from the project environment (`.venv`, Python 3.13) for all three.
- **Machine:** 6 cores, 11 GB RAM, no swap. Each run was alone, under `systemd-run --user --scope -p
  MemoryMax=2G -p MemorySwapMax=0`, wall time and peak RSS from `/usr/bin/time -v`. No run hit the cap.
- **Equivalence to non-strict mypy:** basedpyright `typeCheckingMode: "standard"` (the nearest to mypy's defaults;
  `basic` and `recommended` were run once each as sensitivity points). Pyrefly has no modes; its defaults were used.
- **Versions:** mypy 2.1.0 (the locked one); basedpyright 1.40.1 (based on pyright 1.1.414) plus
  `nodejs-wheel-binaries` 24.19.0; Pyrefly 1.3.2. basedpyright and Pyrefly were installed alone, each in its own
  scratch environment outside the repository.

## 2. Results

| | mypy 2.1.0 | basedpyright 1.40.1 (`standard`) | Pyrefly 1.3.2 |
|---|---|---|---|
| Wall time, cold / second run | 30.0 s / 0.49 s (incremental cache) | 71.2 s / 68.7 s (no cache effect) | 2.25 s / 2.10 s |
| Peak memory (RSS) | 406 MB cold, 76 MB warm | 1,041 MB | 207 MB |
| Errors | 1,569 (plus 147 `note:` lines) | 711 (plus 1 warning) | 817 (plus 74 warnings not shown, 5 suppressed) |
| Files with at least one error | 236 | 160 | 151 |
| Files analysed | n/a | 710 | about 710 |
| Errors inside the excluded packages | 16 (it follows imports into them) | 0 | 0 |
| Dependencies to add | none (already locked) | `basedpyright` + `nodejs-wheel-binaries` (Node 24, about 200 MB on disk; 274 MB environment) | `pyrefly` only: one 33 MB binary wheel |
| Baseline mechanism | `mypy-baseline` (separate package), text file | built in: `.basedpyright/baseline.json` | built in: `--baseline FILE` |
| Baseline size here | 1,569 lines, 204,569 bytes | 175,694 bytes JSON | 217,256 bytes JSON |

Sensitivity (basedpyright): `basic` 684 errors + 1 warning, 73.5 s, 1,041 MB; `standard` 711 errors + 1 warning,
about 70 s, 1,041 MB; `recommended` 1,207 errors + **25,657 warnings**, 87.6 s, 1,129 MB (not a usable setting for
this code base without a policy decision).

Rule families (top): mypy `call-arg` 443, `arg-type` 342, `assignment` 207, `union-attr` 109, `name-defined` 104,
`no-any-return` 98. basedpyright `reportArgumentType` 261, `reportOptionalMemberAccess` 115,
`reportUndefinedVariable` 110, `reportCallIssue` 101, `reportAttributeAccessIssue` 64. Pyrefly `bad-argument-type`
260, `missing-attribute` 168, `unsupported-operation` 116, `unknown-name` 110, `bad-assignment` 62. The undefined-name
family agrees across all three (104, 110, 110): the likely real bugs routed to the rpg domain separately.

## 3. Baselines (a no-source-edit gate)

Both alternatives have a baseline file that does not touch source, so decision 8.7 (no `# type: ignore` in `src/`)
does not exclude either. Pyrefly *also* has a separate `pyrefly suppress` command that writes inline ignore comments
into source; it was **not** run, and it is the path that would conflict with 8.7 (the reason `ty` was excluded).

Behaviour, tested on the clone with one file (`src/engine/cache_registry.py`), exactly as was done for
mypy-baseline:

| Case | mypy-baseline | basedpyright baseline | Pyrefly baseline |
|---|---|---|---|
| Unchanged tree with the baseline | 0 new | 0 errors | 0 errors |
| 40 lines inserted above existing errors | 0 new | 0 errors | 0 errors |
| One genuinely new error appended | only that error | 1 error (`reportReturnType`, line 174) | 1 error (`bad-return`, line 174) |

Caveats found: basedpyright only baselines files **inside its project root** (the directory of its config), so the
config and the baseline have to live at the repository root; with the config elsewhere it refuses ("located outside
the project root") and writes nothing. These tests edited one file in the **scratch clone's** `src/` (an inserted
comment block, then an appended function) and restored it with `git checkout`; the real repository was not touched.

## 4. Overlap with mypy (same commit, (file, line) pairs)

| | mypy | basedpyright | Pyrefly |
|---|---|---|---|
| Distinct flagged (file, line) pairs | 1,081 | 649 | 724 |
| Shared with mypy | | 546 | 588 |
| Shared with all three | 448 | 448 | 448 |
| Flagged by this checker only | 395 | 67 | 100 |
| Shared basedpyright / Pyrefly | | 484 | 484 |
| Files with errors shared with all three | 133 | 133 | 133 |

Reading it: the three agree on a large core (448 lines); mypy flags far more on its own (395), mostly in families
the others word differently or do not report; basedpyright and Pyrefly each add a smaller set of their own.

## 5. Cost if adopted

- **mypy (status quo):** no new dependency; 30 s cold / under 1 s warm; the gate, baseline, ledger entry and tests exist.
- **basedpyright:** a second environment dependency with a Node runtime (about 200 MB), about 70 s and 1 GB per CI
  run with no useful cache, a second baseline file to re-sync with the code-health reseed, and a ledger/test update.
- **Pyrefly:** one dependency-free binary wheel, about 2 s and 207 MB; a second baseline file and ledger/test update;
  its output format and rule names are new to the agents that read CI summaries.
- **Both:** any second checker doubles the number of "new error" signals to triage per PR during and after the soak.

## 6. Limits of this trial

- One commit, one machine, one run each of the sensitivity points; counts are exact and repeatable, time and memory
  are single measurements (cold and second run for each checker).
- Configurations are approximations of mypy's non-strict setup, not tuned. Import resolution depends on the project
  environment being passed to each tool; the editable install of this repository in `.venv` points at the main
  checkout, so the clone's own root was added as an extra search path for basedpyright and Pyrefly (mypy uses the
  working directory).
- The findings only one checker reports were not triaged for true or false positives, apart from the undefined-name
  family where all three agree. A different conclusion would need that triage.

## 7. Reproducing it

Set `REAL` to the repository, `C` to a scratch clone path and `PY` to the project interpreter
(`$REAL/.venv/bin/python`). Run each command alone under the cap shown; check exit status separately (mypy,
basedpyright and Pyrefly exit 1 when they find errors).

```bash
# 0. A clean clone of the pinned commit (never run these in the real repository)
git clone --no-hardlinks "$REAL" "$C" && cd "$C" && git checkout --detach e6b3f97fde4bdce921369e7c5f9190a0c9e379c3

# 1. Scratch environments outside the repository
uv venv --python 3.13 "$T/env-bpr" && uv pip install --python "$T/env-bpr/bin/python" basedpyright==1.40.1
uv venv --python 3.13 "$T/env-pyr" && uv pip install --python "$T/env-pyr/bin/python" pyrefly==1.3.2

# 2. Configs, in $T (the five excluded packages are src/ai, src/town, src/quests, src/entities, src/progression)
#    $T/pyrightconfig.json
{ "include": ["$C/src"], "exclude": ["$C/src/ai", "$C/src/town", "$C/src/quests", "$C/src/entities", "$C/src/progression"],
  "extraPaths": ["$C"], "pythonVersion": "3.11", "typeCheckingMode": "standard",
  "reportMissingImports": "none", "reportMissingModuleSource": "none" }
#    $T/pyrefly.toml
project-includes = ["$C/src/**/*.py"]
project-excludes = ["$C/src/ai/**", "$C/src/town/**", "$C/src/quests/**", "$C/src/entities/**", "$C/src/progression/**"]
search-path = ["$C"]
python-version = "3.11"
python-interpreter-path = "$PY"
ignore-missing-imports = ["*"]

# 3. Measurements (each: systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 /usr/bin/time -v ... )
rm -rf "$C/.mypy_cache"; "$PY" -m mypy src/ --config-file pyproject.toml --no-error-summary          # cold, then again for warm
"$T/env-bpr/bin/basedpyright" -p "$T/pyrightconfig.json" --pythonpath "$PY" --outputjson              # sed standard->basic|recommended for the sensitivity runs
PYREFLY_COLOR=never "$T/env-pyr/bin/pyrefly" check -c "$T/pyrefly.toml" --output-format json

# 4. Baselines (config copied to $C/pyrightconfig.json for basedpyright; both baseline files stay out of src/)
"$T/env-bpr/bin/basedpyright" -p "$C/pyrightconfig.json" --pythonpath "$PY" --outputjson --baselinefile "$C/.basedpyright/baseline.json" --writebaseline
"$T/env-pyr/bin/pyrefly" check -c "$T/pyrefly.toml" --output-format json --baseline "$T/pyrefly-baseline.json" --update-baseline
#    then repeat each checker with the baseline flag only: unchanged tree, 40 comment lines inserted at the top of one
#    file, and one appended `def f() -> int: return "x"`; restore the file with `git checkout -- <file>`.
```

Counts to expect on that commit: mypy 1,569 errors in 236 files; basedpyright (`standard`) 711 errors and 1 warning in
160 files; Pyrefly 817 errors in 151 files. Overlap is computed from each tool's machine-readable output (mypy text
`path:line: error:`, basedpyright `generalDiagnostics[].range.start.line + 1`, Pyrefly `errors[].line`) as sets of
(repository-relative file, line).
