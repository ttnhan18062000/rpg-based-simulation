---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION
date: 2026-10-15
tags: [performance, benchmarking, regression]
---

# Evidence: every profile of the tick-cost investigation

Host `ubuntu` (i5-11400H, 6 vCPU, loaded); main merged at 2dabff8c1; branch head when written 16d9ac6ba. Copied from `reports/perf/tick_cost/` (git-ignored). Columns: mean tick ms over the measured ticks, ticks, modes, child peak RSS (MB, only for runs after that field was added), top 3 phases (ms, share). Shares are the finding; py-spy at 250 Hz.

| profile | mean ms | ticks | modes | child RSS MB | top phases |
|---|---|---|---|---|---|
| corpus/frontier_extended_canonical | 101.6 | 30 | NORMAL,CONSTRAINED | - | cooperation 23 (23%); resolution_overhead 23 (22%); advancement 14 (14%) |
| corpus/frontier_extended_pinned | 104.9 | 30 | NORMAL | - | resolution_overhead 23 (22%); cooperation 22 (21%); collection 17 (16%) |
| corpus/frontier_extended_pinned_late | 129.7 | 40 | NORMAL | 127.1 | advancement 52 (40%); cooperation 21 (16%); collection 19 (14%) |
| corpus/frontier_marches_canonical | 92.9 | 30 | NORMAL,CONSTRAINED,DEGRADED | - | cooperation 27 (29%); resolution_overhead 14 (15%); advancement 13 (14%) |
| corpus/frontier_marches_pinned | 107.1 | 30 | NORMAL | - | cooperation 33 (31%); collection 17 (16%); resolution_overhead 16 (15%) |
| corpus/frontier_marches_pinned_late | 113.7 | 40 | NORMAL | 125.5 | advancement 51 (45%); collection 14 (13%); resolution_overhead 13 (12%) |
| synthetic/combat_20_canonical | 96.6 | 30 | NORMAL | - | collection 25 (26%); combat_engagement 19 (20%); cooperation 17 (17%) |
| synthetic/combat_20_pinned | 51.4 | 60 | NORMAL | - | combat_engagement 12 (23%); collection 10 (20%); cooperation 10 (19%) |
| synthetic/idle_100_canonical | 124.6 | 30 | NORMAL | - | combat_engagement 44 (36%); resolution_overhead 36 (29%); collection 25 (20%) |
| synthetic/idle_100_live | 119.2 | 30 | NORMAL,DEGRADED,SURVIVAL | - | combat_engagement 48 (40%); resolution_overhead 42 (35%); scheduling 7 (6%) |
| synthetic/idle_100_pinned | 125.9 | 30 | NORMAL | - | combat_engagement 43 (34%); collection 33 (26%); resolution_overhead 33 (26%) |
| synthetic/mixed_200_canonical | 261.3 | 30 | CONSTRAINED | - | cooperation 78 (30%); combat_engagement 65 (25%); resolution_overhead 48 (19%) |
| synthetic/mixed_200_pinned | 232.6 | 30 | NORMAL | - | cooperation 72 (31%); combat_engagement 50 (21%); resolution_overhead 38 (16%) |
| synthetic/movement_1000_canonical | 3132.8 | 30 | SURVIVAL | - | combat_engagement 2284 (73%); resolution_overhead 620 (20%); scheduling 83 (3%) |
| synthetic/movement_1000_pinned | 5590.4 | 30 | NORMAL | - | combat_engagement 3632 (65%); resolution_overhead 883 (16%); collection 845 (15%) |
| synthetic/movement_100_canonical | 156.3 | 30 | NORMAL | - | combat_engagement 51 (33%); resolution_overhead 43 (28%); collection 33 (21%) |
| synthetic/movement_100_pinned | 159.8 | 30 | NORMAL | - | combat_engagement 55 (35%); resolution_overhead 52 (33%); collection 28 (17%) |
| synthetic/movement_2000_canonical | 11395.3 | 10 | SURVIVAL | - | combat_engagement 6309 (55%); resolution_overhead 4583 (40%); scheduling 185 (2%) |
| synthetic/movement_2000_pinned | 10322.8 | 10 | NORMAL | - | combat_engagement 7279 (71%); collection 1405 (14%); resolution_overhead 1308 (13%) |
| synthetic/movement_500_canonical | 1573.4 | 30 | SURVIVAL | - | combat_engagement 1004 (64%); resolution_overhead 436 (28%); scheduling 52 (3%) |
| synthetic/movement_500_pinned | 1610.5 | 30 | NORMAL | - | combat_engagement 989 (61%); resolution_overhead 291 (18%); collection 220 (14%) |
| synthetic/strategic_100_audit | 615.4 | 30 | NORMAL | - | cooperation 350 (57%); resolution_overhead 101 (16%); collection 58 (9%) |
| synthetic/strategic_100_canonical | 603.8 | 30 | SURVIVAL | - | cooperation 375 (62%); resolution_overhead 102 (17%); combat_engagement 50 (8%) |
| synthetic/strategic_100_live | 638.7 | 30 | NORMAL,SURVIVAL | - | cooperation 417 (65%); resolution_overhead 95 (15%); combat_engagement 50 (8%) |
| synthetic/strategic_100_pinned | 615.4 | 30 | NORMAL | - | cooperation 365 (59%); resolution_overhead 94 (15%); combat_engagement 48 (8%) |


## Run log: synthetic (memory, swap and load before each run)

```
scenario	entities	contract	ticks	avail_mb	swap_mb	load1	start	exit
idle	100	pinned	30	3823	7685	3.05	00:15:14	0
idle	100	canonical	30	3941	7685	4.32	00:15:22	0
idle	100	live	30	4049	7685	3.89	00:15:29	0
combat	20	pinned	30	4062	7685	3.73	00:15:36	1
combat	20	canonical	30	3959	7685	3.21	00:15:52	0
mixed	200	pinned	30	4109	7685	6.40	00:15:58	0
mixed	200	canonical	30	4106	7685	5.75	00:16:08	0
strategic	100	pinned	30	4075	7685	5.01	00:16:21	0
strategic	100	canonical	30	4052	7685	4.29	00:16:44	0
strategic	100	live	30	4120	7685	3.70	00:17:07	0
strategic	100	audit	30	4206	7685	3.07	00:17:30	0
movement	100	pinned	30	4219	7685	3.26	00:17:52	0
movement	100	canonical	30	4159	7685	2.98	00:18:01	0
movement	500	pinned	30	4160	7685	2.84	00:18:10	0
movement	500	canonical	30	4112	7685	3.50	00:19:05	0
movement	1000	canonical	30	3805	5316	1.68	00:58:29	0
movement	2000	pinned	10	3923	5315	1.23	01:00:14	0
movement	2000	canonical	10	3831	5315	3.63	01:02:26	0
combat	20	pinned	60	3389	5315	10.71	01:04:43	0
old:132bf09ca	1000	movement	6	3485	5315	9.46	01:04:48	0
old:c84352465	1000	movement	6	3547	5315	8.23	01:04:59	0
old:20f773dee	1000	movement	6	3510	5314	7.65	01:05:05	0
old:20f773dee	100	idle	20	3500	5314	7.65	01:05:08	0
old:now	1000	movement	6	3484	5314	7.12	01:05:11	0
old:now	100	idle	20	3532	5314	9.50	01:05:40	0
DONE
old:d135dd6be	1000	movement	6	3458	5314	10.14	01:06:41	0
```


## Run log: corpus (memory, swap and load before each run)

```
world	contract	avail_mb	swap_mb	load1	start	exit
frontier_extended	pinned	3392	6027	2.71	01:12:41	0
frontier_extended	canonical	3373	6026	2.58	01:12:47	0
frontier_marches	pinned	3384	6026	2.33	01:12:54	0
frontier_marches	canonical	3329	6026	4.31	01:13:00	0
DONE
frontier_extended_late	pinned	3455	6026	3.20	01:13:37	0
frontier_marches_late	pinned	3501	6029	2.96	01:15:03	0
DONE_LATE
```


## Run log: overhead (memory, swap and load before each run)

```
scenario	entities	variant	rep	avail_mb	swap_mb	load1	start
idle	100	none	1	4035	7701	2.33	23:45:06
exit 0 reports/perf/tick_cost/overhead/idle_100_none_r1
idle	100	250	1	3939	7701	2.30	23:45:11
exit 0 reports/perf/tick_cost/overhead/idle_100_250_r1
idle	100	100	1	3997	7701	3.40	23:45:15
exit 1 reports/perf/tick_cost/overhead/idle_100_100_r1
strategic	100	none	1	3946	7701	3.37	23:45:19
exit 0 reports/perf/tick_cost/overhead/strategic_100_none_r1
strategic	100	250	1	4067	7701	3.00	23:45:29
exit 0 reports/perf/tick_cost/overhead/strategic_100_250_r1
strategic	100	100	1	4115	7701	2.77	23:45:41
exit 0 reports/perf/tick_cost/overhead/strategic_100_100_r1
idle	100	none	2	4099	7700	2.73	23:45:52
exit 0 reports/perf/tick_cost/overhead/idle_100_none_r2
idle	100	250	2	4145	7700	2.67	23:45:56
exit 0 reports/perf/tick_cost/overhead/idle_100_250_r2
idle	100	100	2	4126	7700	2.54	23:46:00
exit 0 reports/perf/tick_cost/overhead/idle_100_100_r2
strategic	100	none	2	4106	7700	2.33	23:46:04
exit 0 reports/perf/tick_cost/overhead/strategic_100_none_r2
strategic	100	250	2	4147	7700	2.20	23:46:15
exit 1 reports/perf/tick_cost/overhead/strategic_100_250_r2
strategic	100	100	2	4091	7700	3.73	23:46:27
exit 0 reports/perf/tick_cost/overhead/strategic_100_100_r2
idle	100	none	3	4057	7700	3.27	23:46:38
exit 0 reports/perf/tick_cost/overhead/idle_100_none_r3
idle	100	250	3	4051	7700	3.27	23:46:42
exit 0 reports/perf/tick_cost/overhead/idle_100_250_r3
idle	100	100	3	4077	7700	3.09	23:46:47
exit 0 reports/perf/tick_cost/overhead/idle_100_100_r3
strategic	100	none	3	4086	7700	2.92	23:46:51
exit 0 reports/perf/tick_cost/overhead/strategic_100_none_r3
strategic	100	250	3	4097	7700	2.58	23:47:03
exit 0 reports/perf/tick_cost/overhead/strategic_100_250_r3
strategic	100	100	3	4137	7700	3.70	23:47:17
exit 0 reports/perf/tick_cost/overhead/strategic_100_100_r3
DONE
```


## Run log: bisect (void, src-only trees) (memory, swap and load before each run)

```
sha	time	load	avail	swap	(combat_engagement_ms, tick_ms)	rc
edda25490	01:07:47	load=10.83	avail=3402	swap=5314	(469.733, 1427.72)	rc=0
426391b6e	01:08:17	load=21.10	avail=3414	swap=5314	(512.359, 1337.36)	rc=0
b396080cc	01:08:33	load=16.87	avail=3466	swap=5314	(669.783, 1723.764)	rc=0
f9da8ba82	01:08:46	load=13.50	avail=3474	swap=5314	(602.215, 1184.135)	rc=0
7fa1fc7bc	01:08:59	load=11.17	avail=3487	swap=5314	(558.498, 1219.627)	rc=0
e4a193f67	01:09:12	load=9.76	avail=3473	swap=5314	(588.484, 1290.774)	rc=0
dc9b63c99	01:09:25	load=8.04	avail=3477	swap=5314	(650.965, 1144.31)	rc=0
FIRST_BAD	2dabff8c15ed58382a198f3e661f1b708f63f364
```


## gc on versus off (RSS growth of the same world)

```
gc_on: RSS 95 -> 109 MB over 100 ticks (+14 MB, 0.14 MB/tick), 86 ms/tick, gc objects 118376
gc_off: RSS 95 -> 237 MB over 100 ticks (+142 MB, 1.42 MB/tick), 101 ms/tick, gc objects 241672
```
