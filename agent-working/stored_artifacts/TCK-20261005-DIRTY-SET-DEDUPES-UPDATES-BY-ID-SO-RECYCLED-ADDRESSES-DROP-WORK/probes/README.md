# Probes for TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK

Scratch measurement scripts, kept so the numbers in `../investigation.md` can be reproduced. They hard-code the
absolute worktree and scratchpad paths of the session that wrote them (`/mnt/data/Working/rpg-based-simulation/...`,
`/tmp/claude-1000/...`); edit the `ROOT`/`OUT`/`P`/`S` variables before running. Run one simulation at a time.

- `dirty_probe.py <root> <plain|strong> <trials> <ticks>`: N identical seed-42 `frontier_living_world` trials per
  process; counts `id()` skips and groups canonical-hash traces. `dirty_arms.sh` / `dirty_fixed.sh` are the drivers
  for the plain-vs-strong arms and the fixed tree.
- `frozen_probe.py <root> <ticks> <world>`: `get_frozen` stale-hit probe (Scope 4).
- `det_probe.py`, `early_trials.py`: the original characterisation probes from
  `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` (per-tick hash traces; short-trial
  work-queue and `id()` shadow instrumentation).
