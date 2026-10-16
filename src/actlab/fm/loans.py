"""Loan repayment: amortization and sinking funds."""

from __future__ import annotations

from dataclasses import dataclass

from actlab.fm.annuities import a_n, s_n


@dataclass(frozen=True)
class AmortizationRow:
    period: int
    payment: float
    interest: float
    principal: float
    balance: float


def level_payment(loan: float, i: float, n: int) -> float:
    """Level end-of-period payment that repays `loan` in n periods: L / a_n."""
    return loan / a_n(i, n)


def outstanding_balance(loan: float, i: float, n: int, k: int) -> float:
    """Balance just after the k-th payment, by the prospective method: P a_(n-k)."""
    return level_payment(loan, i, n) * a_n(i, n - k)


def outstanding_balance_retrospective(loan: float, i: float, n: int, k: int) -> float:
    """Balance just after the k-th payment, by the retrospective method: L(1+i)^k - P s_k.

    Should always match `outstanding_balance`. Seeing why is a good exercise.
    """
    return loan * (1.0 + i) ** k - level_payment(loan, i, n) * s_n(i, k)


def amortization_schedule(loan: float, i: float, n: int) -> list[AmortizationRow]:
    """Full amortization schedule for a level-payment loan."""
    payment = level_payment(loan, i, n)
    balance = loan
    rows = []
    for k in range(1, n + 1):
        interest = balance * i
        principal = payment - interest
        balance -= principal
        # The final balance is zero up to floating-point noise; report it as exactly 0.
        rows.append(AmortizationRow(k, payment, interest, principal, 0.0 if k == n else balance))
    return rows


def sinking_fund_payment(loan: float, loan_rate: float, fund_rate: float, n: int) -> float:
    """Total periodic outlay under the sinking fund method.

    The borrower pays interest L * i to the lender each period and deposits
    L / s_n (at the fund rate j) into a sinking fund that accumulates to L.
    """
    return loan * loan_rate + loan / s_n(fund_rate, n)
