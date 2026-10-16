import math
import random

import pytest

from actlab.cli import main
from actlab.practice import GENERATORS, generate


@pytest.mark.parametrize("gen", GENERATORS, ids=lambda g: g.fn.__name__)
def test_every_generator_produces_a_checkable_problem(gen):
    rng = random.Random(0)
    for _ in range(25):
        p = gen.fn(rng)
        assert math.isfinite(p.answer)
        assert p.prompt and p.solution
        assert p.check(p.answer)
        assert p.check(round(p.answer, 4) if abs(p.answer) > 1 else p.answer)
        assert not p.check(p.answer * 1.05 + 1)


def test_generate_filters():
    rng = random.Random(1)
    assert generate(rng, exam="fm").exam == "FM"
    assert generate(rng, topic="credibility").topic == "credibility"
    with pytest.raises(ValueError):
        generate(rng, topic="nope")


def test_cli_commands(capsys):
    assert main(["topics"]) == 0
    assert main(["amortize", "1000", "0.05", "3"]) == 0
    assert main(["bond", "1000", "0.03", "0.025", "4"]) == 0
    assert "FM:" in capsys.readouterr().out


def test_quiz_skips_and_scores(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert main(["quiz", "-n", "3", "--seed", "42"]) == 0
    assert "Score: 0/3" in capsys.readouterr().out
