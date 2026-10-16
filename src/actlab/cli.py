"""Command-line interface.

    actlab quiz [--exam FM|FAM] [--topic TOPIC] [-n N] [--seed SEED]
    actlab topics
    actlab amortize LOAN RATE YEARS
    actlab bond FACE COUPON_RATE YIELD PERIODS
"""

from __future__ import annotations

import argparse
import random
import sys

from actlab.fm import bonds, loans
from actlab.practice import GENERATORS, generate


def _quiz(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    correct = 0
    print("Enter a number, or press Enter to skip and see the solution. Type q to quit.\n")
    for k in range(1, args.n + 1):
        p = generate(rng, args.exam, args.topic)
        print(f"[{k}/{args.n}] {p.exam} · {p.topic}")
        print(p.prompt)
        # Strip a stray BOM, which Windows can prepend to piped input.
        reply = input("> ").strip().lstrip("﻿").replace(",", "")
        if reply.lower() in {"q", "quit", "exit"}:
            args.n = k - 1
            break
        if reply:
            try:
                guess = float(reply)
            except ValueError:
                guess = None
            if guess is not None and p.check(guess):
                correct += 1
                print(f"Correct! ({p.answer:.6g})\n")
                continue
            print(f"Not quite. Answer: {p.answer:.6g}")
        else:
            print(f"Answer: {p.answer:.6g}")
        print(f"Solution: {p.solution}\n")
    if args.n:
        print(f"Score: {correct}/{args.n}")
    return 0


def _topics(_: argparse.Namespace) -> int:
    seen: dict[str, set[str]] = {}
    for g in GENERATORS:
        seen.setdefault(g.exam, set()).add(g.topic)
    for exam, topics in seen.items():
        print(f"{exam}: {', '.join(sorted(topics))}")
    return 0


def _amortize(args: argparse.Namespace) -> int:
    rows = loans.amortization_schedule(args.loan, args.rate, args.years)
    print(f"{'k':>4} {'payment':>12} {'interest':>12} {'principal':>12} {'balance':>14}")
    for r in rows:
        print(f"{r.period:>4} {r.payment:>12.2f} {r.interest:>12.2f} {r.principal:>12.2f} {r.balance:>14.2f}")
    return 0


def _bond(args: argparse.Namespace) -> int:
    price = bonds.bond_price(args.face, args.coupon_rate, args.yield_rate, args.periods)
    print(f"Price: {price:.4f}\n")
    print(f"{'k':>4} {'coupon':>10} {'interest':>12} {'amortized':>12} {'book value':>14}")
    for r in bonds.book_value_schedule(args.face, args.coupon_rate, args.yield_rate, args.periods):
        print(f"{r.period:>4} {r.coupon:>10.2f} {r.interest_earned:>12.4f} {r.amortization:>12.4f} {r.book_value:>14.4f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="actlab", description="Practice and tools for SOA Exams FM and FAM.")
    sub = parser.add_subparsers(dest="command", required=True)

    quiz = sub.add_parser("quiz", help="answer randomly generated practice problems")
    quiz.add_argument("--exam", choices=["FM", "FAM", "fm", "fam"])
    quiz.add_argument("--topic", help="limit to one topic (see `actlab topics`)")
    quiz.add_argument("-n", type=int, default=5, help="number of problems (default 5)")
    quiz.add_argument("--seed", type=int, help="random seed, to replay the same set of problems")
    quiz.set_defaults(func=_quiz)

    topics = sub.add_parser("topics", help="list available practice topics")
    topics.set_defaults(func=_topics)

    amort = sub.add_parser("amortize", help="print a loan amortization schedule")
    amort.add_argument("loan", type=float)
    amort.add_argument("rate", type=float, help="effective rate per period, e.g. 0.05")
    amort.add_argument("years", type=int, help="number of payments")
    amort.set_defaults(func=_amortize)

    bond = sub.add_parser("bond", help="print a bond's price and book value schedule")
    bond.add_argument("face", type=float)
    bond.add_argument("coupon_rate", type=float, help="coupon rate per period, e.g. 0.03")
    bond.add_argument("yield_rate", type=float, help="yield rate per period, e.g. 0.025")
    bond.add_argument("periods", type=int)
    bond.set_defaults(func=_bond)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (KeyboardInterrupt, EOFError):
        print()
        return 130
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
