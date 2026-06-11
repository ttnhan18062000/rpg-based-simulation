---
status: historical
layer: artifact
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-LIVE
artifact_type: test_plan
---

# Test Plan — TCK-20260606-DOCSITE-FM-LIVE

## Objective

Verify that `tools/add_frontmatter_live.py` correctly classifies and injects frontmatter
into all 247 in-scope markdown files, that the result passes `tools/validate_frontmatter.py`
with zero violations, and that the script is idempotent.

---

## Test Cases

### T1 — Dry-run classification preview (manual verification)

**Method:** Run the script with a `--dry-run` flag (or inspect output before writing) to
print the classification for each file without modifying disk.

**Verify:**
- All `docs/mechanics/` files → `status: authoritative, authority: P0, layer: mechanics`
- All `docs/core/` files → `status: authoritative, authority: P0, layer: core`
- `docs/engine/kernel.md` → `status: active, authority: P1`
- `docs/engine/phase8_entry_package.md` → `status: historical, authority: P2`
- `docs/combat/rollout_hardening_rulebook_m7.md` → `status: active, authority: P1`
- `docs/combat/combat_movement_rulebook_m1.md` → `status: historical, authority: P2`
- `docs/performance/optimization_architecture.md` → `status: active, authority: P1`
- `docs/performance/2026-05-13-v2-performance-hardening-report.md` → `status: historical, authority: P2`
- `docs/observability/how_to_run_simulation.md` → `status: active, authority: P1`
- `docs/observability/phase_1.md` → `status: historical, authority: P2`
- `docs/test_coverage/phase10_optimization_scaling_coverage.md` → `status: historical, authority: P2`
- `docs/testing/v2_test_taxonomy.md` → `status: active, authority: P1`

### T2 — Script execution: full run

**Command:** `python3 tools/add_frontmatter_live.py` (from repo root)

**Verify:**
- Script exits with code 0
- Summary output reports ~247 modified, 0 skipped
- No Python tracebacks or errors

### T3 — Validator pass: authoritative dirs

**Command:**
```
python3 tools/validate_frontmatter.py docs/mechanics/
python3 tools/validate_frontmatter.py docs/core/
```

**Verify:**
- Exit code 0, zero violations
- `last_verified: 2026-06-06` present on all files in these dirs

### T4 — Validator pass: all in-scope dirs

**Command:**
```
python3 tools/validate_frontmatter.py docs/engine/
python3 tools/validate_frontmatter.py docs/architecture/
python3 tools/validate_frontmatter.py docs/systems/
python3 tools/validate_frontmatter.py docs/combat/
python3 tools/validate_frontmatter.py docs/observability/
python3 tools/validate_frontmatter.py docs/performance/
python3 tools/validate_frontmatter.py docs/strategy/
python3 tools/validate_frontmatter.py docs/compliance/
python3 tools/validate_frontmatter.py docs/testing/
python3 tools/validate_frontmatter.py docs/test_coverage/
python3 tools/validate_frontmatter.py docs/ai/
python3 tools/validate_frontmatter.py docs/guidelines/
```

**Verify:** All exit code 0, zero violations across all 12 directories.

### T5 — Validator pass: loose docs root files

**Command:**
```
python3 tools/validate_frontmatter.py docs/README.md
python3 tools/validate_frontmatter.py docs/logic_checklist_exhaustive.md
python3 tools/validate_frontmatter.py docs/optimization_audit_ledger.md
```

**Verify:** Exit code 0 on all three.

### T6 — Idempotency

**Method:** Run `python3 tools/add_frontmatter_live.py` a second time immediately after T2.

**Verify:**
- Summary reports 0 modified, ~247 skipped
- File contents are unchanged (no duplicated `---` blocks)
- Validator still passes (T4 re-run)

### T7 — last_verified conditional: non-authoritative files

**Verify:** Spot-check 5+ files outside mechanics/ and core/ to confirm `last_verified` is
absent from their frontmatter blocks.

```bash
head -10 docs/architecture/adr-004-simulation-watchdog.md
head -10 docs/engine/kernel.md
head -10 docs/combat/rollout_hardening_rulebook_m7.md
```

None should contain `last_verified`.

### T8 — No out-of-scope dirs touched

**Verify:**
```bash
head -3 docs/archive/$(ls docs/archive/ | head -1) 2>/dev/null
```
- `docs/archive/` files should still have `status: archive` frontmatter (already applied
  by Ticket 3 / add_frontmatter_archive.py), not been double-modified.
- `docs/parity_ledger/` files are YAML, not .md — confirm script does not touch them.
- `docs/scenarios/` YAML files untouched.

### T9 — engine edge-case review (manual)

Manually inspect the classification of these edge-case engine files:
- `runtime_completion_contract_ma.md` — may be HISTORICAL due to `_ma` suffix; verify intent
- `minimal_kernel_m2.md` — should be ACTIVE; confirm `m2` mid-name doesn't trigger historical
- `certification_contract_m9.md` — should be ACTIVE; confirm `m9` mid-name is safe

If any mis-classification found, adjust the heuristic regex before the full run.

### T10 — docs/README.md content update

After frontmatter injection, manually update `docs/README.md` to add a note that all docs
carry frontmatter and are browsable via Docusaurus (per acceptance criteria AC-8).

Verify the updated README.md still passes `python3 tools/validate_frontmatter.py docs/README.md`.

---

## Pass Criteria

- T2: zero errors, ~247 files modified
- T3–T5: validator exits 0 with zero violations across all files
- T6: second run reports 0 modified (idempotent)
- T7: no spurious `last_verified` on non-authoritative files
- T8: out-of-scope dirs untouched
- T9: edge-case engine files classified correctly
- T10: README.md updated and validator still passes
