# actlab: an actuarial exam lab

A from-scratch Python implementation of the math behind the Society of Actuaries
**Exam FM (Financial Mathematics)** and **Exam FAM (Fundamentals of Actuarial
Mathematics)**, plus a command-line quiz that generates practice problems with
worked solutions.

The library has no dependencies, so every formula is written out where you can
read it. Each function's docstring gives the exam notation, so the code doubles
as a formula sheet.

## What's inside

| Exam | Module | Topics |
|------|--------|--------|
| FM | `actlab.fm.interest` | i, i^(m), d, d^(m), δ; NPV; IRR |
| FM | `actlab.fm.annuities` | a_n, ä_n, s_n, perpetuities, m-thly, continuous, increasing/decreasing, geometric |
| FM | `actlab.fm.loans` | amortization schedules, outstanding balance (prospective and retrospective), sinking funds |
| FM | `actlab.fm.bonds` | price, yield, book value / amortization of premium |
| FM | `actlab.fm.duration` | Macaulay and modified duration, convexity, Redington immunization |
| FAM-L | `actlab.fam.life` | life tables (incl. the SULT), A_x, term, endowment, ä_x, net premiums, reserves |
| FAM-S | `actlab.fam.loss_models` | Exponential, Pareto, Lognormal; E[X∧u]; deductibles, limits, coinsurance, inflation; aggregate losses; Panjer recursion |
| FAM-S | `actlab.fam.credibility` | limited fluctuation (full and partial), Bühlmann |

## Getting started

Requires Python 3.10+.

```bash
git clone https://github.com/<your-username>/actlab.git
cd actlab
python -m venv .venv
.venv\Scripts\activate        # Windows; on macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Practice quiz

```bash
actlab quiz                    # 5 random problems from FM and FAM
actlab quiz --exam FM -n 10
actlab quiz --topic credibility
actlab quiz --seed 7           # replay the same set of problems
actlab topics                  # list topics
```

Answers within 0.1% of the true value count as correct. Press Enter to skip a
problem and see its worked solution.

## Calculators

```bash
actlab amortize 100000 0.05 30      # loan, rate per period, number of payments
actlab bond 1000 0.03 0.025 20      # face, coupon rate, yield rate, periods (per period)
```

## Using the library

```python
from actlab.fm import annuities, bonds
from actlab.fam import life

annuities.a_n(0.05, 10)                      # 7.7217
bonds.bond_price(1000, 0.03, 0.025, 20)      # 1077.95

sult = life.LifeTable.sult()
life.annuity_due(sult, 65, 0.05)             # ä_65 ≈ 13.5498
life.net_level_premium(sult, 45, 0.05, "endowment", n=20, benefit=100_000)
```

## Learning roadmap

See [docs/PROJECTS.md](docs/PROJECTS.md) for projects that extend the library,
ordered roughly by exam syllabus. Each one is a chance to derive a formula,
implement it, and prove it right with a test.

## Disclaimer

This is a personal study project and is not affiliated with or endorsed by the
Society of Actuaries. Check results against official SOA study materials.

## License

MIT
