# Core-RPG test report v0

- SHA: `54a2198f9de928dc1135f3c04d2ba1744aaa08ed`
- As of: 2026-09-30
- Test files scanned: 1516
- Uncommitted changes under scanned inputs: False

## Inputs

- junit: `scenario_lane_junit.xml` (sha256 `85a946282cbf`)
- mutation-record: `tests/mutation/baselines/src_core_conservation.json` (sha256 `880c7c264f80`)
- tag-registry: `registries/tag_registry.jsonl` (sha256 `67e77577fefc`)
- workflow: `.github/workflows/test.yml` (sha256 `1e819cab679d`)

## Classification (heuristic)

Denominator: 1516 test files.

- classified: 69 / 1516
- uncertain: 116 / 1516
- unowned-domain: 7 / 1516
- not-core-rpg: 1324 / 1516
- parse-error: 0 / 1516
- directory-only signal: 81, import-only signal: 35

## CI lanes

State: parsed. Candidate files: 185; pytest lane steps: 31.

- covered by a fast lane: 185 / 185
- no fast lane: 0 / 185
- lane steps uploading JUnit: 6 / 31

## Execution

State: **junit-supplied**. Denominator: 185 core-RPG candidate files.

- run `scenario_lane_junit-85a946282cbf`: 53 testcases (passed 53, failed 0, errors 0, skipped 0, unmapped 0); candidate files pass 21, fail 0, skipped 0, not-run 164 / 185

## Package coverage

State: **no-coverage-artifact**. Domain coverage: not-derived.


## Parity ledger (read-only)

Denominator: 2190 entries.
- divergent: 15
- legacy_verified: 226
- missing: 28
- unsupported: 33
- verified: 1888

## SimQ and census

- SimQ: skipped-no-data (SimQ anchor checks skip when no corpus data is present; v0 reads no corpus)
- census: unstable (census reachability is not yet a stable input; v0 reports the state only)

## Mutation evidence

State: **recorded**.

- `src/core/conservation.py`: **fresh**  (age 1 d, real-target, mutmut 2.5.1); killed 60, survived 117, timeout 0, suspicious 0, equivalent not-classified / 177 mutants; 7 material survivors flagged

## Escaped defects

State: **counting**.
Tag registered 2026-09-29; 2276 tickets scanned. Month = ticket creation date (frontmatter `date`); includes open tickets under todos/ and inprogress/.

- 2026-09: 0
- tagged outside the window: 0

## v0 limits

- Execution data is a supplied input: in CI only the `api-tools` job uploads JUnit, so most lanes have no JUnit artifact to supply unless a local run produces one.
- There is no CI coverage job. Package coverage comes only from a supplied local run (`provisional-local`); otherwise it shows `no-coverage-artifact`.
- Package coverage is not domain coverage. Domain coverage stays `not-derived` until a defensible mapping exists.
- Classification is heuristic (directory and import signals). `domain`/`level` markers a file declares are listed beside its class and never override it; few tests declare them yet. Disagreeing signals stay `uncertain`.
- Import signals follow the ownership map in architecture_design_notes.md §3.1; party/group code has no oracle or owner (decision D-P, deferred), so files that only import it are `unowned-domain`, outside the core-RPG candidate set.
- The manifest hashes the supplied artifacts, the workflow, the tag registry and the mutation records; the scanned tests/, tickets/ and parity ledger are covered only by the `worktree_dirty` flag, which needs a git checkout.
- Lane triggers and path filters are not derived; the lane layer records which pytest steps list which paths.
- Mutation evidence covers one declared target. `mutmut` is not a project dependency, so the run is not reproducible from a clean install.
- Equivalent mutants are not classified (`equivalent: not-classified`); every survivor is unreviewed.
- `mutmut` 3.x cannot run in this repo: its trampoline rejects modules whose import path starts with `src.`.
- SimQ and census states are fixed read-only states in v0; the parity layer counts ledger statuses and is not proof.
- Escaped defects depend on tagging discipline (`escaped-defect`); history before the tag was registered is not backfilled. A defect's month is its ticket's creation date, and open tickets (todos/, inprogress/) are counted.
- The report never runs tests and is not a gate.
