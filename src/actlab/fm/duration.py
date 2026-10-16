"""Duration, convexity and immunization.

Cash flows are sequences of (time, amount) pairs, as in `actlab.fm.interest`.
"""

from __future__ import annotations

import math

from actlab.fm.interest import CashFlows, npv


def macaulay_duration(cashflows: CashFlows, i: float) -> float:
    """D_mac = sum(t v^t CF_t) / sum(v^t CF_t)."""
    flows = list(cashflows)
    return sum(t * cf * (1.0 + i) ** (-t) for t, cf in flows) / npv(flows, i)


def modified_duration(cashflows: CashFlows, i: float) -> float:
    """D_mod = -P'(i) / P(i) = D_mac / (1 + i)."""
    return macaulay_duration(cashflows, i) / (1.0 + i)


def convexity(cashflows: CashFlows, i: float) -> float:
    """C = P''(i) / P(i) = sum(t(t+1) v^(t+2) CF_t) / P."""
    flows = list(cashflows)
    return sum(t * (t + 1) * cf * (1.0 + i) ** (-t - 2) for t, cf in flows) / npv(flows, i)


def macaulay_convexity(cashflows: CashFlows, i: float) -> float:
    """Macaulay convexity = sum(t^2 v^t CF_t) / P."""
    flows = list(cashflows)
    return sum(t * t * cf * (1.0 + i) ** (-t) for t, cf in flows) / npv(flows, i)


def first_order_price_estimate(price: float, i: float, new_i: float, d_mod: float) -> float:
    """First-order modified approximation: P(i + h) ≈ P(i) (1 - h D_mod)."""
    return price * (1.0 - (new_i - i) * d_mod)


def first_order_macaulay_estimate(price: float, i: float, new_i: float, d_mac: float) -> float:
    """First-order Macaulay approximation: P(j) ≈ P(i) ((1 + i) / (1 + j))^D_mac."""
    return price * ((1.0 + i) / (1.0 + new_i)) ** d_mac


def is_redington_immunized(assets: CashFlows, liabilities: CashFlows, i: float, rel_tol: float = 1e-6) -> bool:
    """Redington's three conditions at rate i:

    1. PV(assets) = PV(liabilities)
    2. Modified duration of assets = that of liabilities  (equivalently PV'(A) = PV'(L))
    3. Convexity of assets > convexity of liabilities      (PV''(A) > PV''(L))

    Conditions 1 and 2 are checked to a relative tolerance `rel_tol`.
    """
    a, l = list(assets), list(liabilities)
    if not math.isclose(npv(a, i), npv(l, i), rel_tol=rel_tol):
        return False
    if not math.isclose(modified_duration(a, i), modified_duration(l, i), rel_tol=rel_tol):
        return False
    return convexity(a, i) > convexity(l, i)
