"""
src/domains/progression/ledger.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — RewardLedgerComponent & utility service functions.

Utility and processing logic for the event-driven capacity-bounded reward ledger.
"""

from __future__ import annotations
from src.domains.progression.schema import RewardEntry, RewardLedgerComponent


class RewardLedgerService:
    """
    Manages bounded updates to the RewardLedgerComponent when new XP, gold, 
    or items are obtained.
    """

    MAX_ENTRIES = 20

    @classmethod
    def record_entry(
        cls,
        ledger: RewardLedgerComponent,
        tick: int,
        kind: str,
        subject: str,
        quantity: int | float = 1,
        source: str | None = None,
    ) -> RewardLedgerComponent:
        """
        Record a new reward event-driven in the ledger, enforcing a maximum boundary count.
        """
        new_entry = RewardEntry(
            tick=tick,
            kind=kind,
            subject=subject,
            quantity=quantity,
            source=source,
            consumed_by_plan=False
        )
        
        # Enforce capacity bound by trimming older entries
        all_entries = list(ledger.entries) + [new_entry]
        if len(all_entries) > cls.MAX_ENTRIES:
            all_entries = all_entries[-cls.MAX_ENTRIES:]

        return RewardLedgerComponent(
            entries=tuple(all_entries),
            last_processed_tick=ledger.last_processed_tick
        )

    @classmethod
    def mark_consumed(
        cls,
        ledger: RewardLedgerComponent,
        entry_index: int,
    ) -> RewardLedgerComponent:
        """
        Mark a specific ledger entry as consumed/processed by a conversion plan.
        """
        entries_list = list(ledger.entries)
        if 0 <= entry_index < len(entries_list):
            entry = entries_list[entry_index]
            entries_list[entry_index] = RewardEntry(
                tick=entry.tick,
                kind=entry.kind,
                subject=entry.subject,
                quantity=entry.quantity,
                source=entry.source,
                consumed_by_plan=True
            )
        return RewardLedgerComponent(
            entries=tuple(entries_list),
            last_processed_tick=ledger.last_processed_tick
        )
