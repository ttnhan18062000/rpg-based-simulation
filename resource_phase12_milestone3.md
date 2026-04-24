# [Milestone 3] - Workflow, CI, and Operational Artifact Cutover

## [Milestone Description]

Milestone 3 moves the project’s internal operating workflows to `src_v2`.

Its purpose is to make the team’s own execution, testing, replay/report, and release routines depend on `src_v2` rather than old `src`.

This milestone covers:

- CI/runtime invocation,
- replay/report/proof generation,
- artifact production,
- automated validation workflows,
- and internal/operator workflows that still point at old `src`.

It is about operational dependency migration, not feature closure.

It does not yet close final real-condition validation or legacy retirement.

## [Milestone technical implementation]

Cut over supported project workflows and artifacts to `src_v2`.

This milestone must:

- switch CI paths and validation jobs to `src_v2`,
- switch replay/report/proof generation paths to `src_v2`,
- switch release/build or packaging flows to `src_v2` where ratified,
- ensure operational artifacts come from the new supported source of truth,
- and preserve visibility of any workflows still intentionally excluded.

This milestone must not:

- keep old `src` as the real hidden dependency while claiming migration,
- allow artifact truth to come from mixed runtimes,
- or overclaim completion if core workflows still depend on old `src`.

## [Milestone important notes]

The trap here is ceremonial migration.

If CI and artifact generation still lean on the old runtime, the organization itself is telling you what the real system still is.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported CI and operational workflows run on `src_v2`,
- supported artifacts are generated from `src_v2`,
- mixed-runtime truth surfaces are eliminated where cutover was allowed,
- and the project has one credible workflow/artifact cutover slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit CI jobs, validation routines, and operational workflows that still depend on old `src`

#### [Task Description]

Find the real organizational dependency surface before claiming workflow migration.

#### [Task technical implementation]

Review all supported workflows and record:

- which jobs still call old `src`,
- which artifact-generation steps still depend on old `src`,
- which proof/report/replay routines still mix runtimes,
- and which supported workflows are already ready for `src_v2` cutover.

#### [Task possible affected files]

- CI config files
- release/build scripts
- workflow/runbook docs
- `docs/engine/phase12_cutover_ownership.md`

#### [Task important notes]

Do not trust the roadmap. Trust what the automation actually calls.

#### [Task check list]

- [x] Old-src workflow dependencies are mapped
- [x] Artifact dependencies are mapped
- [x] Mixed-runtime truth surfaces are identified
- [x] Ready-to-migrate workflows are identified
- [x] Audit is reviewable

#### [Task acceptance criteria]

The project has a concrete audit of supported workflow and artifact dependencies.

---

### [ ] (checkbox) - [Task 2] - Switch supported CI and validation routines to `src_v2`

#### [Task Description]

Make the organization’s own validation infrastructure depend on `src_v2`.

#### [Task technical implementation]

Update supported CI and validation jobs so they use `src_v2` as the execution/runtime authority for the cutover-eligible surface.

This task should:

- preserve ratified workflow outputs,
- keep fallback explicit where still needed,
- and avoid touching intentionally excluded or unsupported jobs.

#### [Task possible affected files]

- CI config files
- validation scripts
- test runner configs
- `tests_v2/**`

#### [Task important notes]

If CI still trusts old `src`, your team still trusts old `src`.

#### [Task check list]

- [x] Supported CI jobs route to `src_v2`
- [x] Validation jobs route to `src_v2`
- [x] Unsupported jobs remain excluded
- [x] Fallback remains explicit where needed
- [x] Workflow behavior is documented

#### [Task acceptance criteria]

Supported CI and validation routines now run on `src_v2`.

---

### [ ] (checkbox) - [Task 3] - Switch replay/report/proof and artifact-generation workflows to `src_v2`

#### [Task Description]

Make truth-bearing artifacts come from the new default runtime.

#### [Task technical implementation]

Update supported operational artifact workflows so:

- replay generation,
- reporting,
- proof-bundle generation,
- and other cutover-eligible artifacts

are produced by `src_v2`, not old `src` or mixed runtime paths.

#### [Task possible affected files]

- replay/report scripts
- proof-bundle generation scripts
- certification/build scripts
- operational runbook docs

#### [Task important notes]

Artifact truth from mixed runtimes is poison.

#### [Task check list]

- [x] Replay generation uses `src_v2`
- [x] Report generation uses `src_v2`
- [x] Proof generation uses `src_v2`
- [x] Mixed-runtime truth surfaces are removed
- [x] Workflow changes are documented

#### [Task acceptance criteria]

Supported operational artifacts are generated from `src_v2` only.

---

### [ ] (checkbox) - [Task 4] - Publish the supported workflow and artifact cutover baseline

#### [Task Description]

Turn workflow migration into an explicit operational fact.

#### [Task technical implementation]

Publish one workflow/artifact cutover baseline summarizing:

- which CI and automation paths now use `src_v2`,
- which artifacts now come from `src_v2`,
- what still remains excluded or fallback-only,
- and what residual mixed-runtime dependencies are intentionally still visible.

#### [Task possible affected files]

- `docs/engine/phase12_workflow_cutover_baseline.md`
- `docs/engine/phase12_cutover_allowed_surface.md`
- runbook docs

#### [Task important notes]

This should expose reality, not present a neat story.

#### [Task check list]

- [x] New workflow defaults are explicit
- [x] Artifact origins are explicit
- [x] Remaining exclusions are explicit
- [x] Residual dependencies are explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

The project has one explicit supported workflow/artifact cutover baseline.
