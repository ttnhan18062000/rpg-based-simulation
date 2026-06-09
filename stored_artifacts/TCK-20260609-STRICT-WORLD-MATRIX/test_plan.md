---
ticket: TCK-20260609-STRICT-WORLD-MATRIX
phase: test_plan
---

# Test Plan

22 pass unconditionally; 35 xfail (CAT-REL-099 pre-existing).

| Group | Count | Status |
|---|---|---|
| Module loads (7 modules × 7 rows) | 7×3=21 pre-assembly | PASS |
| Registry seeding | 1 | PASS |
| Full-assembly: WorldSpec | 7 | XFAIL |
| Full-assembly: CompileContext entities | 7 | XFAIL |
| Full-assembly: no blocking errors | 7 | XFAIL |
| Full-assembly: determinism | 7 | XFAIL |
| Full-assembly: no hidden legacy fallback | 7 | XFAIL |
