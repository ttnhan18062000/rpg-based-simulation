# Investigation: Milestone B Governor Hardening

Confirmed that the previous governor used point-in-time signals and hard-coded scalars.
Implemented a strict "Confidence Window" check in `_can_recover` that requires all signals in the last N ticks to be below recovery watermarks.
Standardized all thresholds against the Milestone B Signals Contract.
Verified that monotonic recovery (one level at a time) is enforced.
Verified that the rolling average window (5 ticks) combined with the confidence window (3 ticks) effectively blocks thrashing from single-tick spikes.
