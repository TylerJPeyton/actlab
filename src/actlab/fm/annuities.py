"""Annuities certain.

Function names mirror actuarial notation:
    a_n   PV of an annuity-immediate (payments at end of period)
    ad_n  PV of an annuity-due (a-double-dot, payments at start of period)
    s_n   accumulated value of an annuity-immediate
    sd_n  accumulated value of an annuity-due
"""

from __future__ import annotations

import math

from actlab.fm.interest import discount_rate, effective_to_nominal, force_of_interest


def a_n(i: float, n: float) -> float:
    """a_n = (1 - v^n) / i."""
    if i == 0:
        return float(n)
    return (1.0 - (1.0 + i) ** (-n)) / i


def ad_n(i: float, n: float) -> float:
    """ä_n = (1 - v^n) / d = (1 + i) a_n."""
    return (1.0 + i) * a_n(i, n)


def s_n(i: float, n: float) -> float:
    """s_n = ((1 + i)^n - 1) / i."""
    if i == 0:
        return float(n)
    return ((1.0 + i) ** n - 1.0) / i


def sd_n(i: float, n: float) -> float:
    """s̈_n = (1 + i) s_n."""
    return (1.0 + i) * s_n(i, n)


def perpetuity_immediate(i: float) -> float:
    """a_∞ = 1 / i."""
    return 1.0 / i


def perpetuity_due(i: float) -> float:
    """ä_∞ = 1 / d."""
    return 1.0 / discount_rate(i)


def a_n_m(i: float, n: float, m: int) -> float:
    """a_n^(m): pays 1/m at the end of every 1/m of a year for n years."""
    return (1.0 - (1.0 + i) ** (-n)) / effective_to_nominal(i, m)


def a_n_continuous(i: float, n: float) -> float:
    """ā_n = (1 - v^n) / delta, a continuous payment stream at rate 1."""
    return (1.0 - (1.0 + i) ** (-n)) / force_of_interest(i)


def increasing_annuity(i: float, n: int) -> float:
    """(Ia)_n: payments 1, 2, ..., n at times 1..n.  (Ia)_n = (ä_n - n v^n) / i."""
    return (ad_n(i, n) - n * (1.0 + i) ** (-n)) / i


def decreasing_annuity(i: float, n: int) -> float:
    """(Da)_n: payments n, n-1, ..., 1 at times 1..n.  (Da)_n = (n - a_n) / i."""
    return (n - a_n(i, n)) / i


def geometric_annuity(i: float, g: float, n: int) -> float:
    """PV of payments 1, (1+g), (1+g)^2, ... at times 1..n.

    PV = [1 - ((1+g)/(1+i))^n] / (i - g), or n / (1 + i) when i == g.
    """
    if math.isclose(i, g):
        return n / (1.0 + i)
    return (1.0 - ((1.0 + g) / (1.0 + i)) ** n) / (i - g)
