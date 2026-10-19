---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261014-SIMQ-COMPARE-TOOLS-REFUSE-RUNS-NOT-RECORDED-HOST-INDEPENDENT
phase: done
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# Investigation

**Finding: no committed producer of `rows.jsonl` existed.** `simq_reanchor.load_rows` is its only reader. The rows came from a driver that lived in one session's scratch directory (run each key twice under `calibrate_simq --audit-mode`, copy the report, delete the run dir). Neither that driver nor `quality_report.json` recorded `audit_mode` or `signals_zeroed`, and `simq_pillar_compare.compare_report` took a parsed report with no manifest. Hence the re-tier to standard and the new producer.

**Manifest file name.** `run_manifest.json`, from `RunArtifactRepository.resolve_path(run_id, "manifest")`; never hard-coded. rpg's `RunManifest` has `audit_mode` and `signals_zeroed` (`Optional[bool]`), written by `Kernel` at run start (`src/engine/kernel.py`).

**Consumers of `data/calibration/<key>/` and where each directory comes from (CI blast radius):**

| Consumer | Where its directory comes from | Effect of the sidecar refusal |
|---|---|---|
| `simq-grade-drift` job (test.yml, push to main / schedule / dispatch, informational) | `make simq-full-audit-full` runs `evaluate_simq` (non-dry-run, regenerates every key through `calibrate_simq`), then `test_grade_regression -m "not slow"` in the same job | the sidecar exists, no refusal |
| PR-gating "Simulation quality" jobs running `test_grade_regression` | no `data/calibration/` (gitignored); the anchor tests `pytest.skip` | unchanged: they skip |
| slow-regression `make simq-corpus-diversity-slow-isolated` | in-process engine runs under `audit_mode` (no calibration dir, `compare_pillar` directly, no `compare_report`) | not wired; unchanged |
| `evaluate_simq --dry-run` / `make evaluate` / `make simq-full-audit` step 1 (local) | a directory already on disk | a stale directory (no sidecar) refuses with exit 2: intended; re-run `make evaluate-full` |
| `evaluate_simq` without `--dry-run` | regenerated through `calibrate_simq` in the same call | the sidecar exists |

So no scheduled slow run goes red wholesale from stale directories.

**Campaign mode.** Only `config/simulation_quality/profiles/campaign_life_arc.yaml` sets `campaign_episodes`; no key in `grade_anchors.json` uses it (23 world prefixes checked). `_run_campaign_engine` returns the campaign directory, which has no `run_manifest.json` (each episode has its own), so its sidecar would record `None` and refuse at compare time. No CI red.

**Not wired:** the corpus-diversity guards (`tests/unit/worldassembly/test_corpus_diversity.py`) run their own engine in-process with `audit_mode=True` (pinned by `test_anchors_audit_mode.py`) and call `compare_pillar`, never `compare_report`; they have no manifest to hand and are out of the ticket's two named callers.
