# Projects

Ways to grow `actlab` while studying. For each one: derive the formula on
paper first, implement it, then write a test that checks it against a brute-force
calculation or a known textbook/SOA sample answer. Add a practice-problem
generator in `src/actlab/practice/problems.py` when you finish a topic.

## Exam FM

- [ ] **Newton's method IRR.** Replace bisection in `interest.irr` with Newton-Raphson. Compare iteration counts.
- [ ] **Dollar- vs time-weighted returns.** Add `dollar_weighted_return` and `time_weighted_return` for a fund with deposits and withdrawals.
- [ ] **Varying interest.** Accumulation under a force of interest δ(t) given as a Python function (numerical integration).
- [ ] **Callable bonds.** Price a callable bond to the investor's worst case over a set of call dates and prices.
- [ ] **Bond schedule details.** Add the price-plus-accrued vs market-price split between coupon dates.
- [ ] **Term structure.** Spot rates → forward rates → bond prices, and bootstrap spot rates from par yields.
- [ ] **Full immunization.** Check the full-immunization conditions, and solve for the asset amounts that immunize a liability (generalize the hand solution in `tests/test_fm.py`).
- [ ] **Swaps.** Compute the swap rate for a level or deferred interest rate swap from a spot curve; market value of a swap after rates change.
- [ ] **Loans with irregular payments.** Amortization schedule when payments vary (e.g. increasing payments or a balloon payment).

## Exam FAM-L (long-term)

- [ ] **Fractional ages.** Add UDD and constant-force interpolation for t_p_x at non-integer t.
- [ ] **Continuous and m-thly benefits.** Ā_x under UDD (i/δ · A_x), ä_x^(m) by UDD and Woolhouse.
- [ ] **Variance of loss.** Second moments ²A_x and Var(L_0) for whole life.
- [ ] **Select tables.** Model a select-and-ultimate table like the SULT's select period.
- [ ] **Gross premiums.** Equivalence principle with expenses (initial and renewal, percent of premium).
- [ ] **Reserve recursion.** Implement (tV + P)(1 + i) = q b + p (t+1)V and check it matches the prospective reserve at every duration.
- [ ] **Joint life.** Two independent lives: joint-life and last-survivor annuities and insurance.

## Exam FAM-S (short-term)

- [ ] **More severity distributions.** Gamma, Weibull, single-parameter Pareto; add closed-form E[X∧u] where available.
- [ ] **Franchise deductibles.** Payment per loss / per payment for a franchise deductible.
- [ ] **(a, b, 1) class.** Zero-truncated and zero-modified frequency distributions in the Panjer recursion.
- [ ] **Stop-loss premiums.** E[(S − d)+] from the Panjer output.
- [ ] **Bühlmann–Straub.** Credibility with varying exposure, and empirical Bayes estimation of EPV/VHM from data.
- [ ] **Bayesian credibility.** Discrete prior/posterior calculations; compare to Bühlmann.
- [ ] **Estimation.** Maximum likelihood for exponential/Pareto with censored and truncated data (use `scipy.optimize` or write your own optimizer).
- [ ] **Simulation check.** Monte Carlo a compound Poisson process and compare the empirical distribution to the Panjer result.

## Tooling

- [ ] Add a GitHub Actions workflow that runs `pytest` on every push.
- [ ] Track quiz history (topic, right/wrong, time) in a JSON file and add `actlab stats` to show weak topics.
- [ ] Jupyter notebooks that plot things: yield curves, bond price vs yield with the duration tangent line, survival curves.
