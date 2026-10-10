---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD
artifact_type: plan
tags: [architecture, testing]
---

# Plan (DESIGN ONLY, no code yet): committed local Aseprite proof record (ADR D10 kept)

Status: awaiting asset-planner approval of the guarded-path list and record shape, then owner approval of the D10 addendum.

## Guarded paths (what the `needs_aseprite` tests exercise)
Computed, not hand-listed, by one pure module `tools/visual_assets_aseprite_proof.py`, from tracked files (`git ls-files`) so CI and the local run see the same set:
1. `visual_assets/drawing/**` (the drawing tools, the sandbox, the Lua pin, the server) and `visual_assets/store/**` (intake, build/exporter, pixels, records; everything the real renderer path touches), excluding `*.md`;
2. `visual_assets/catalog/build-config/**` (the export config and its pins);
3. tests: every file under `tests/visual_assets/` that contains the marker `needs_aseprite`, plus the shared support they import: `tests/visual_assets/conftest.py`, `strict_aseprite.py`, `tests/visual_assets/drawing/conftest.py`, `tests/visual_assets/store/{builders,adoption_support,runtime_fixture}.py` (any new marked test file changes the set, so adding one makes the record stale);
4. the runner and the hasher themselves: `tools/visual_assets_aseprite_local.py`, `tools/visual_assets_aseprite_proof.py`.
Not guarded: docs, review tooling (`visual_assets/review/**`), draft sets, committed art (the rc rebuild verdict below covers the art path), the record itself, `reports/`.
Trade-off for the planner: guarding all of `store/**` and `drawing/**` makes the record stale on any code edit there (the intent: those files are what the real run proved), at the price of a fresh local run per code change. A narrower list (import closure of the marked tests) is possible with an `ast` walk but is a larger, more fragile mechanism.

## Hash
`guarded_hash` = sha256 over the sorted lines `<path>\0<sha256 of file bytes>\n`. The record also lists `guarded_files` (path + sha256 each, about 100 files, about 10 KB) so the CI failure can NAME the changed, added or removed files.

## Record shape (`docs/assets/aseprite_local_proof.json`, canonical JSON, typed in the test; excluded from the hash by being outside the set)
```
{"record_type":"aseprite_local_proof","schema_version":1,
 "make_target":"visual-assets-aseprite-local",
 "run_commit":"<HEAD the tests ran on; the record's own commit cannot contain itself>",
 "run_at_utc":"2026-..Z","aseprite_version":"Aseprite 1.3.18.6-x64","strict":true,
 "counts":{"passed":N,"failed":0,"errors":0,"skipped":0,"total":N},
 "release_rebuild":{"release":"pilot/rc-0008","entries":70,"identical":70,"bytes_differ_pixels_match":0},
 "guarded_hash":"sha256:...","guarded_files":[{"path":"...","sha256":"..."}]}
```
The runner writes it ONLY when strict, exit 0, failed = errors = skipped = 0 and total > 0, so a record always means a clean strict run. `release_rebuild` comes from child 3's test, which writes its verdict JSON to the path in `VISUAL_ASSETS_REBUILD_VERDICT_OUT` when the runner sets it.

## CI test (no Aseprite): `tests/visual_assets/test_aseprite_local_proof.py`
Recompute the guarded set from `git ls-files` (falls back to a walk when not a checkout), compare with the record: fail naming changed/added/removed files and the make target. Also: record parses strictly, `strict` true, counts clean, `total` > 0, rebuild entries == identical + drift. Pure functions over text, proven on planted violations.

## Skip line
`tools/ci_aseprite_skip_line.py`: `Real-Aseprite tests: N skipped: local only, ADR D10; proof record: <run_commit>, <aseprite_version>, run <date> (<days> days ago), guarded files <match|DIFFER>`. Reporting only, exit 0, no new gate.

## Proposed D10 addendum (owner to approve; D10's decision unchanged)
"Addendum (2026-10-10): the real-Aseprite tests still run only on the licence holder's own machine. `make visual-assets-aseprite-local` also writes a committed proof record (`docs/assets/aseprite_local_proof.json`): the Aseprite version, the commit it ran on, the pass/skip/fail counts of a strict run and a hash over the files those tests exercise. CI never runs Aseprite; it recomputes the hash and fails when a guarded file changed since the record, naming the make target. The record states what the licence holder ran, it does not authenticate who ran it."

## Proof Plan
Mutation: change one guarded byte (a store file, a marked test, a new marked test file) -> CI test fails naming it; refresh the record via a real local run -> passes. Planted violations (changed/added/removed, dirty counts, skipped>0, strict false). First record committed from a real local run on this machine.
