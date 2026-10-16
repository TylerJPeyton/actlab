"""Bonds: price, yield, and book value (amortization of premium/discount).

All rates are per coupon period. Notation:
    F  face (par) value
    r  coupon rate per period, so the coupon is Fr
    C  redemption value (defaults to F)
    i  yield rate per period
    n  number of coupon periods
"""

from __future__ import annotations

from dataclasses import dataclass

from actlab.fm.annuities import a_n


@dataclass(frozen=True)
class BookValueRow:
    period: int
    coupon: float
    interest_earned: float
    amortization: float
    book_value: float


def bond_price(face: float, coupon_rate: float, yield_rate: float, n: int, redemption: float | None = None) -> float:
    """Basic formula: P = Fr a_n + C v^n."""
    c = face if redemption is None else redemption
    return face * coupon_rate * a_n(yield_rate, n) + c * (1.0 + yield_rate) ** (-n)


def bond_yield(
    price: float,
    face: float,
    coupon_rate: float,
    n: int,
    redemption: float | None = None,
    tol: float = 1e-12,
) -> float:
    """Yield per period that reproduces `price`. Bisection; price falls as yield rises."""
    lo, hi = -0.99, 1.0
    for _ in range(500):
        mid = (lo + hi) / 2.0
        if bond_price(face, coupon_rate, mid, n, redemption) > price:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2.0


def book_value_schedule(
    face: float, coupon_rate: float, yield_rate: float, n: int, redemption: float | None = None
) -> list[BookValueRow]:
    """Bond amortization schedule.

    Each period the bondholder earns i * BV on the prior book value; the
    difference between that and the coupon amortizes the premium (or
    accumulates the discount).
    """
    coupon = face * coupon_rate
    bv = bond_price(face, coupon_rate, yield_rate, n, redemption)
    rows = []
    for k in range(1, n + 1):
        interest = bv * yield_rate
        amortization = coupon - interest
        bv -= amortization
        rows.append(BookValueRow(k, coupon, interest, amortization, bv))
    return rows
