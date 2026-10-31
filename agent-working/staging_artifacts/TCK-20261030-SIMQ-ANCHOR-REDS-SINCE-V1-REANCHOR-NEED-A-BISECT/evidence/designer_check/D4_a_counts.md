
### A. retreat-active project ticks after t452

| entity | ticks | threat, hp<0.5 | threat, hp>=0.5 | no threat, hp<0.5 | no threat, hp>=0.5 | unclassified |
|---|---|---|---|---|---|---|
| all | 0 | 0 | 0 | 0 | 0 | 0 |

### B. ticks with a retreat_pull call that changes a score, after t452

| entity | ticks | threat, hp<0.5 | threat, hp>=0.5 | no threat, hp<0.5 | no threat, hp>=0.5 | unclassified |
|---|---|---|---|---|---|---|
| all | 0 | 0 | 0 | 0 | 0 | 0 |

### C. ticks where COMBAT_RETREAT is the top raw score of a scoring call, after t452

| entity | ticks | threat, hp<0.5 | threat, hp>=0.5 | no threat, hp<0.5 | no threat, hp>=0.5 | unclassified |
|---|---|---|---|---|---|---|
| 5 | 5 | 0 | 0 | 5 | 0 | 0 |
| 6 | 4 | 0 | 0 | 4 | 0 | 0 |
| 14 | 1 | 1 | 0 | 0 | 0 | 0 |
| all | 10 | 1 | 0 | 9 | 0 | 0 |

### Retreat project spans (whole run; contiguous ticks with a combat_retreat current project, alive)

| entity | spans (start-end, project id) | ends before t2000 | open at the last tick |
|---|---|---|---|

last tick in log: 1999; alive entities with a retreat span open at the last tick: 0

### Positive control: entity 18 at t42 (the known retreat_pull case)

th record: {'k': 'th', 't': 42, 'e': 18, 'acting': True, 'adj': True, 'perc': 2, 'terms': ['ThreatTerm.WOUNDED', 'ThreatTerm.ADJACENT', 'ThreatTerm.TARGETED', 'ThreatTerm.CLOSING', 'ThreatTerm.OUTMATCHED'], 'hpr': 0.25, 'pr': ''}
rp record(s): []
classification: threat, hp<0.5
