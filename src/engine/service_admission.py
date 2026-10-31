"""One admission rule for the inn's services (TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY; AGENCY-03, SURV-07 row 27).

A way is open to a subject iff the service would actually deliver it to that subject now. The building service (``building_services.service_delta``)
and every "open" test (``ways_in_reach``, ``EatScorer``, ``FatigueScorer``, and through them the starvation record) ask :func:`admits`, so what the
service delivers and what the pull judges open cannot diverge. The payment law has exactly one definition, :data:`SERVICE_PAYMENT_LAW`:

* ``CLAMP`` (main today): the price is charged as far as the subject's purse reaches and the meal or bed is delivered anyway, so a broke subject is
  fed and bedded. Payment never closes a service.
* ``ATOMIC`` (the free-meal removal, D73 / N1): the full price or nothing; a subject holding less than the price is not served.

Flipping the law is a change to the one constant; no consumer is edited. The prices are read from ``service_prices`` only.

``keeps_coin`` is NOT yet part of admission (designer ruling 2026-10-29, option A): ``service_building`` also requires the subject to keep coin
(``serves.keeps_coin``), and ``admits`` does not, as adding it would change what the scorers answer on main. The gap is pinned by a test and tracked in
TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from src.engine.appraisal import can_use_inn_meal
from src.engine.service_prices import EAT_PRICE_GOLD, REST_PRICE_GOLD


class PaymentLaw(str, Enum):
    """How the inn is paid: CLAMP charges what the purse holds and delivers anyway; ATOMIC is the full price or no service."""

    CLAMP = "CLAMP"
    ATOMIC = "ATOMIC"


SERVICE_PAYMENT_LAW = PaymentLaw.CLAMP  # the one definition of how the inn is paid

_PRICES = {"EAT": EAT_PRICE_GOLD, "REST": REST_PRICE_GOLD}


def payment_covers(entity: Any, action: str, law: Optional[PaymentLaw] = None) -> bool:
    """True when the payment law lets the subject have the service at its purse: always under CLAMP, a full price under ATOMIC."""
    if (law or SERVICE_PAYMENT_LAW) is PaymentLaw.CLAMP:
        return True
    return int(entity.inventory.gold) >= _PRICES[action]


def admits(entity: Any, action: str, law: Optional[PaymentLaw] = None) -> bool:
    """True when the inn's ``action`` ("EAT" or "REST") would be delivered to ``entity`` now, by diet and by the payment law."""
    if action == "EAT" and not can_use_inn_meal(entity):  # decision 44: a diet without prepared food has no inn meal
        return False
    return payment_covers(entity, action, law)
