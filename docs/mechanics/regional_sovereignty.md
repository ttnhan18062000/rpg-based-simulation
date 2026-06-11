---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-06-06
---

# Regional Sovereignty & Governance

## 1. Sovereignty (Territorial Control)
Regional Sovereignty represents the authoritative ownership of a world region by a specific faction. It is a dynamic state driven by **Regional Influence**.

### 1.1 Influence Dynamics
Influence is shifted through death-triggered events within a region:
- **Monster Death**: +1.0 Hero Guild Influence.
- **Hero Death**: +1.0 Monster Horde Influence.
- **Stronghold Destruction**: +50.0 Hero Guild Influence.

### 1.2 Ownership Thresholds
A region flips ownership when influence crosses specific boundaries:
- **Hero Guild Control**: Influence > 100.0.
- **Monster Horde Control**: Influence < -100.0.
- **Contested**: Between -50.0 and 50.0.

### 1.3 Territorial Effects
| Ownership | Effect |
| :--- | :--- |
| **Hero Guild** | 50% slower monster spawn rate; 50% lower hazard damage. |
| **Monster Horde** | 100% faster monster spawn rate; 100% higher hazard damage (Aura of Despair). |
| **Contested** | Normal rates. |

## 2. Governance (Economic Control)
Governance represents the extraction and utilization of resources by the regional owner.

### 2.1 Regional Taxation
Every `TAX_INTERVAL` (100 ticks), the regional owner extracts gold:
- **Entity Tax**: 2.0 Gold from every entity in a town.
- **Building Tax**: 10.0 Gold per functional town building.

### 2.2 Faction Vaults
Extracted gold is deposited into **Faction Vaults** in `AuthoritativeState.global_resources`:
- Key format: `faction_{id}_gold`.

### 2.3 Service Maintenance
Town services require gold from the Faction Vault to remain functional:
- **Maintenance Cost**: 5.0 Gold per building per tax tick.
- **Insolvency**: If the vault is empty, buildings become `functional=False`.
