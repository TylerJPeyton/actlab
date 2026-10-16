"""Interest rate measures and the time value of money.

Notation follows the SOA convention:
    i       effective annual interest rate
    i^(m)   nominal annual rate convertible m times per year
    d       effective annual discount rate
    d^(m)   nominal annual discount rate convertible m times per year
    delta   force of interest
    v       discount factor 1 / (1 + i)
"""

from __future__ import annotations

import math
from typing import Iterable

CashFlows = Iterable[tuple[float, float]]
"""A sequence of (time, amount) pairs."""


def v(i: float) -> float:
    """Discount factor v = 1 / (1 + i)."""
    return 1.0 / (1.0 + i)


def discount_rate(i: float) -> float:
    """Effective discount rate d = i / (1 + i) = 1 - v."""
    return i / (1.0 + i)


def rate_from_discount(d: float) -> float:
    """Effective interest rate i = d / (1 - d)."""
    return d / (1.0 - d)


def effective_to_nominal(i: float, m: int) -> float:
    """i^(m) = m[(1 + i)^(1/m) - 1]."""
    return m * ((1.0 + i) ** (1.0 / m) - 1.0)


def nominal_to_effective(i_m: float, m: int) -> float:
    """i = (1 + i^(m)/m)^m - 1."""
    return (1.0 + i_m / m) ** m - 1.0


def effective_to_nominal_discount(i: float, m: int) -> float:
    """d^(m) = m[1 - (1 + i)^(-1/m)]."""
    return m * (1.0 - (1.0 + i) ** (-1.0 / m))


def nominal_discount_to_effective(d_m: float, m: int) -> float:
    """i = (1 - d^(m)/m)^(-m) - 1."""
    return (1.0 - d_m / m) ** (-m) - 1.0


def force_of_interest(i: float) -> float:
    """delta = ln(1 + i)."""
    return math.log1p(i)


def rate_from_force(delta: float) -> float:
    """i = e^delta - 1."""
    return math.expm1(delta)


def accumulate(amount: float, i: float, t: float) -> float:
    """Accumulated value of `amount` after t years at compound rate i."""
    return amount * (1.0 + i) ** t


def present_value(amount: float, i: float, t: float) -> float:
    """Present value of `amount` due at time t at compound rate i."""
    return amount * (1.0 + i) ** (-t)


def npv(cashflows: CashFlows, i: float) -> float:
    """Net present value at time 0 of (time, amount) cash flows."""
    return sum(amount * (1.0 + i) ** (-t) for t, amount in cashflows)


def irr(
    cashflows: CashFlows,
    lo: float = -0.99,
    hi: float = 1.0,
    tol: float = 1e-12,
    max_iter: int = 500,
) -> float:
    """Internal rate of return: the i with npv(cashflows, i) = 0.

    Uses bisection, so [lo, hi] must bracket a sign change in the NPV.
    Bisection is slow but always converges, which makes it a good first
    root-finder to understand. Try replacing it with Newton's method
    (you'll need the derivative of NPV with respect to i).
    """
    flows = list(cashflows)
    f_lo, f_hi = npv(flows, lo), npv(flows, hi)
    if f_lo * f_hi > 0:
        raise ValueError("NPV does not change sign on [lo, hi]; widen the bracket.")
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        f_mid = npv(flows, mid)
        if abs(f_mid) < tol or (hi - lo) / 2.0 < tol:
            return mid
        if f_lo * f_mid < 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0
