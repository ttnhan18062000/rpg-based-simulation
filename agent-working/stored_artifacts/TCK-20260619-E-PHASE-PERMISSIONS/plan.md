# Plan: TCK-20260619-E-PHASE-PERMISSIONS

## Ordered Steps

### Step 1 — Create `src/engine/phase_domain_permissions.py`
Declare `PHASE_READ_DOMAINS`, `PHASE_WRITE_DOMAINS`, `PHASE_EMIT_DOMAINS` as `Dict[TickPhase, FrozenSet[str]]`.
Domain labels: `entity`, `world`, `policy`, `schedule`, `proposals`, `lifecycle`, `infra`, `platform`, `replay`, `events`.
Cover all 7 phases (6 authoritative + PERSISTENCE).
**Files:** `src/engine/phase_domain_permissions.py` (new, ~55 lines)

### Step 2 — Create `tests/architecture/test_phase_domain_permissions.py`
Six tests: per-phase coverage for read/write/emit, plus architectural invariants (RESOLUTION sole entity writer, COLLECTION no entity write, PERSISTENCE non-authoritative).
**Files:** `tests/architecture/test_phase_domain_permissions.py` (new, ~55 lines)

### Step 3 — Check off RPG-INFRA-155/156/157 in logic checklist
In `docs/logic_checklist_exhaustive.md` L3001-3003:
`- [ ]` → `- [x]` with SOURCE/TEST comment.
**Files:** `docs/logic_checklist_exhaustive.md`

### Step 4 — Add parity ledger entries INFRA-206/207/208
Append to `docs/parity_ledger/infrastructure.yaml` after INFRA-205:
- INFRA-206: per-phase read domain declarations, status=verified, test_path=tests/architecture/test_phase_domain_permissions.py
- INFRA-207: per-phase write domain declarations, status=verified, test_path=same
- INFRA-208: per-phase emit domain declarations, status=verified, test_path=same
**Files:** `docs/parity_ledger/infrastructure.yaml`

### Step 5 — Update `docs/engine/kernel.md`
Add a "Phase Domain Permissions" table showing read/write/emit domains per phase. Reference `src/engine/phase_domain_permissions.py`.
**Files:** `docs/engine/kernel.md`

## Scope Guards (what NOT to touch)
- Do NOT add runtime enforcement (RPG-INFRA-158–163 is out of scope)
- Do NOT modify `src/engine/phases.py` (FROZEN per Phase 4 Baseline Freeze Contract)
- Do NOT modify the authoritative pipeline or kernel execution flow

## Dependency Map
Steps 1 → 2 (tests import from Step 1 declarations)
Steps 1-2 → 3-4-5 (all doc/ledger updates reference the new file/test)

## Acceptance Criteria Mapping
- AC1 (RPG-INFRA-155/156 verified): Step 3 (logic checklist) + Step 4 (parity ledger INFRA-206/207)
- AC2 (architecture guard test passes): Step 2

## Deviations
_(none yet)_
