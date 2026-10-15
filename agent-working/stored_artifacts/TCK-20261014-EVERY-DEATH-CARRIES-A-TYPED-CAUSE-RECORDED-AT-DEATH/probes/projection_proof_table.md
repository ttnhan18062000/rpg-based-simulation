# Projection proof, 3 worlds x seeds 42-46 x 5000 ticks

Base arm f7d3c25a0 (rpg-next), new arm a0c3ef39f (death-cause-typed). audit_mode, PYTHONHASHSEED=0. Script: death_proof.py, driver dp3_jobs.sh + dp3_list.txt.
Projection drops exactly lifecycle.death_record and combat.last_attacker_id (tests/helpers/death_field_projection.py).
Pass = projected digest, alive, dead, cause and movement counts identical in all 15 pairs, and every dead body carries a record.

| world | seed | projected digest identical | counts identical | dead | records | FULL fingerprint, new arm (base for later steps) |
|---|---|---|---|---|---|---|
| frontier_living_world | 42 | True | True | 35 | 35 | `df2771c9aa6b309bd111fb139975af4eebaf640dcdb1a5f6d5ed3fe8d556327c` |
| frontier_living_world | 43 | True | True | 28 | 28 | `cebf404ebc6a2a61c8e4b6e769772d9da4cbf9ab40b9498c46335359d27f0a75` |
| frontier_living_world | 44 | True | True | 36 | 36 | `e6a9bb98393e44d8307facf11f1dad3603b705a74bf26535f818ea035e79fe31` |
| frontier_living_world | 45 | True | True | 35 | 35 | `21fe5fe5a923e59a46e30d3d5c295efcf8c1e71947c9611ab92e8235a78c5551` |
| frontier_living_world | 46 | True | True | 34 | 34 | `6f3471918644f030947168689bb3b9b66de277275f93aabb8dca787cd97c407a` |
| urban_political | 42 | True | True | 13 | 13 | `2ce5225e442c7296db6a995f37f0dd200cdce7409ddfbb8b71b0e2916d70e0d3` |
| urban_political | 43 | True | True | 9 | 9 | `55feff951a9a9de30d9dd2e02bb88f5e0ddaf58c5a4e5f28738729cf2b4808a9` |
| urban_political | 44 | True | True | 12 | 12 | `722b1efb0c8bfddb3b880bf44840fe1ce39610580b83a4e7a0e7ec777db03ec5` |
| urban_political | 45 | True | True | 9 | 9 | `75e9a99d7856d6a8e308a950564382a913b28b96b16a43678be31ce4a2363bf3` |
| urban_political | 46 | True | True | 11 | 11 | `67629ba0e1bc4a6788516f58fb2913633a955a20a91c0386dbf9e6a40c3af9d1` |
| crowded_frontier | 42 | True | True | 34 | 34 | `0266c8609632c26ae951547a06970f57ea5c20029d3471ca62f5b247e35dc66b` |
| crowded_frontier | 43 | True | True | 31 | 31 | `4ace95abff9a8bd67f62c5a6082c7e82cb5f58cfb821c2da6f38de366d9dfb33` |
| crowded_frontier | 44 | True | True | 36 | 36 | `f965506abc2786f0f798abefcb55ca1350b98a1b87331f862195eb98c455118d` |
| crowded_frontier | 45 | True | True | 32 | 32 | `35059440dba053c0be2e8d35f13bca0645633b81467ea01a40e677ed2498dd28` |
| crowded_frontier | 46 | True | True | 34 | 34 | `16025982aaaa2502991126b63caa5905e27b6ba35c407f3fa9863b909ad4ec2e` |

Result: 15/15 pairs identical. Full digests differ from the base arm in all 15 pairs, as expected (the two new fields are in the canonical state).
