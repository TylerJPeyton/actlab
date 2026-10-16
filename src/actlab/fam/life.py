"""Life contingencies on an integer-age life table (FAM-L).

Notation:
    l_x       number alive at age x
    t_p_x     probability (x) survives t years
    t_q_x     probability (x) dies within t years
    A_x       EPV of 1 paid at the end of the year of death (whole life)
    A1_x:n    EPV of n-year term insurance
    nE_x      EPV of a pure endowment of 1 at time n
    ä_x       EPV of a life annuity-due of 1 per year

All benefits are discrete (paid at the end of the year of death) and all
annuities are annual. Extending this to 1/m-thly or continuous versions
(with UDD or Woolhouse) is a good project; see docs/PROJECTS.md.
"""

from __future__ import annotations

import math
from typing import Literal

Kind = Literal["whole", "term", "endowment"]


class LifeTable:
    """An integer-age life table built from l_x values at consecutive ages.

    Everyone is assumed dead by age max_age + 1.
    """

    def __init__(self, lx: dict[int, float]):
        ages = sorted(lx)
        if ages != list(range(ages[0], ages[-1] + 1)):
            raise ValueError("Ages in a life table must be consecutive integers.")
        self._lx = dict(lx)
        self.min_age = ages[0]
        self.max_age = ages[-1]

    @classmethod
    def from_makeham(
        cls, a: float, b: float, c: float, min_age: int, max_age: int, radix: float = 100_000.0
    ) -> "LifeTable":
        """Build a table from Makeham's law, mu_x = A + B c^x.

        Under Makeham, p_x = exp(-A - B c^x (c - 1) / ln c).
        """
        lx = {min_age: radix}
        for x in range(min_age, max_age):
            p = math.exp(-a - b * c**x * (c - 1.0) / math.log(c))
            lx[x + 1] = lx[x] * p
        return cls(lx)

    @classmethod
    def sult(cls) -> "LifeTable":
        """The SOA Standard Ultimate Life Table used on Exam FAM-L.

        Makeham with A = 0.00022, B = 2.7e-6, c = 1.124, and l_20 = 100,000.
        """
        return cls.from_makeham(0.00022, 2.7e-6, 1.124, 20, 120)

    def l(self, x: int) -> float:
        if x < self.min_age:
            raise ValueError(f"Age {x} is below the table's minimum age {self.min_age}.")
        return self._lx.get(x, 0.0)

    def tpx(self, t: int, x: int) -> float:
        """t_p_x = l_(x+t) / l_x."""
        return self.l(x + t) / self.l(x)

    def tqx(self, t: int, x: int) -> float:
        """t_q_x = 1 - t_p_x."""
        return 1.0 - self.tpx(t, x)

    def p(self, x: int) -> float:
        return self.tpx(1, x)

    def q(self, x: int) -> float:
        return self.tqx(1, x)

    def deferred_q(self, u: int, t: int, x: int) -> float:
        """u|t_q_x: probability (x) survives u years then dies within the next t."""
        return (self.l(x + u) - self.l(x + u + t)) / self.l(x)

    def curtate_expectation(self, x: int) -> float:
        """e_x = sum over k >= 1 of k_p_x."""
        return sum(self.tpx(k, x) for k in range(1, self.max_age - x + 2))

    def _remaining(self, x: int) -> int:
        """Number of years until everyone alive at x has died."""
        return self.max_age - x + 1


def term_insurance(table: LifeTable, x: int, n: int, i: float) -> float:
    """A1_x:n = sum_{k=0}^{n-1} v^(k+1) k_p_x q_(x+k)."""
    v = 1.0 / (1.0 + i)
    return sum(v ** (k + 1) * table.deferred_q(k, 1, x) for k in range(n))


def whole_life_insurance(table: LifeTable, x: int, i: float) -> float:
    """A_x: term insurance to the end of the table."""
    return term_insurance(table, x, table._remaining(x), i)


def pure_endowment(table: LifeTable, x: int, n: int, i: float) -> float:
    """nE_x = v^n n_p_x."""
    return (1.0 + i) ** (-n) * table.tpx(n, x)


def endowment_insurance(table: LifeTable, x: int, n: int, i: float) -> float:
    """A_x:n = A1_x:n + nE_x."""
    return term_insurance(table, x, n, i) + pure_endowment(table, x, n, i)


def annuity_due(table: LifeTable, x: int, i: float, n: int | None = None) -> float:
    """ä_x:n = sum_{k=0}^{n-1} v^k k_p_x. Whole life when n is None."""
    if n is None:
        n = table._remaining(x)
    v = 1.0 / (1.0 + i)
    return sum(v**k * table.tpx(k, x) for k in range(n))


def annuity_immediate(table: LifeTable, x: int, i: float) -> float:
    """Whole life annuity-immediate a_x = ä_x - 1."""
    return annuity_due(table, x, i) - 1.0


def insurance(table: LifeTable, x: int, i: float, kind: Kind, n: int | None) -> float:
    """EPV of a unit benefit of the given kind ("whole", "term" or "endowment")."""
    if kind == "whole":
        return whole_life_insurance(table, x, i)
    if n is None:
        raise ValueError(f"A term n is required for {kind} insurance.")
    if kind == "term":
        return term_insurance(table, x, n, i)
    if kind == "endowment":
        return endowment_insurance(table, x, n, i)
    raise ValueError(f"Unknown insurance kind: {kind}")


def net_level_premium(
    table: LifeTable, x: int, i: float, kind: Kind = "whole", n: int | None = None, benefit: float = 1.0
) -> float:
    """Annual net premium by the equivalence principle: P = b A / ä.

    Premiums are payable annually in advance for the term of the policy
    (for life, for whole life insurance).
    """
    premium_years = None if kind == "whole" else n
    return benefit * insurance(table, x, i, kind, n) / annuity_due(table, x, i, premium_years)


def net_premium_reserve(
    table: LifeTable, x: int, t: int, i: float, kind: Kind = "whole", n: int | None = None, benefit: float = 1.0
) -> float:
    """Prospective net premium reserve at duration t (just before the premium due at t):

    tV = b A_(x+t) - P ä_(x+t), with insurance and annuity over the remaining n - t years.
    """
    premium = net_level_premium(table, x, i, kind, n, benefit)
    remaining = None if kind == "whole" else n - t
    if remaining is not None and remaining <= 0:
        return benefit if kind == "endowment" else 0.0
    epv_benefits = benefit * insurance(table, x + t, i, kind, remaining)
    return epv_benefits - premium * annuity_due(table, x + t, i, remaining)
