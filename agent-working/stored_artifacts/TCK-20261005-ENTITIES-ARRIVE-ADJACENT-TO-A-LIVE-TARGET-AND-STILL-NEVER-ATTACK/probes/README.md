# Probes for TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK

Scratch measurement scripts, kept so the numbers in `../investigation.md` can be reproduced (the ticket asked for them to
be kept rather than rewritten). They hard-code the absolute worktree and scratchpad paths of the session that wrote them
(`/mnt/data/Working/rpg-based-simulation/...`, `/tmp/claude-1000/...`); edit the `ROOT`/`S`/`OLD`/`NEW` variables first. Run
one simulation at a time. The numbers cited in `../investigation.md` were re-taken on `origin/main` `544b1d341` (which contains the
dirty-set determinism fix) with `remeasure.sh` (edit its path variables), plus `adj_probe.py` and `forced_brain.py` run by hand; a
count is a "value" only where the identical run was repeated and matched, otherwise a "sample". The older scripts that still hard-code
the first session's paths (`ab.sh`, `after_fix.sh`, `volume_arms.sh`, `oa_control.sh`) were run pre-fix and are kept for reference
only; `remeasure.sh` supersedes `volume_arms.sh` and `oa_control.sh`.

Trace and gates (this ticket):
- `adj_probe.py <root> <world> <ticks>`: per tick, live entities holding an ACTIVE `defeat_enemy` objective within one tile
  of their live target: was the tactical pass called, what did it return, readiness, legality verdicts.
- `one_entity.py <root> <world> <entity_id> <ticks>`: tick-by-tick trace of one entity (task, payload, position, navigation
  target, whether the tactical pass was called).
- `dispatch_probe.py <root> <world> <ticks>`: `execute_attack` vs `resolve_attack` counts and the legality verdict inside
  each `execute_attack` call (Scope 2).
- `brain_adj.py`, `forced_brain.py`: what the tactical pass decides for an entity with a live hostile adjacent (forced
  read-only call on real states): the flee-gate finding.
- `panic_terms.py`: which term of `AppraisalSystem.evaluate_emotional_state` drives each flee.
- `trauma_ticks.py`, `trauma0.py`: per-tick regional `trauma_score` (+1.0 per death, uncapped).
- `combat_volume.py` + `volume_arms.sh` / `after_fix.sh` / `oa_control.sh`: decision-path attacks, resolve calls split by
  opportunity or not, and mutual tile-swap counts, before and after, plus the incidental-attack control.

From `TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` (not previously committed):
- `obj_probe.py`, `ab.sh`, `summ_ab.py`: the control-vs-fixed termination A/B (live holders only, per-project tracking).
