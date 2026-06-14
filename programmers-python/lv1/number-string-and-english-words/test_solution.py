import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("one4seveneight", 1478),
        ("23four5six7", 234567),
        ("2three45sixseven", 234567),
        ("123", 123),
        ("zero", 0),
        ("zero9eight", 98),
        ("onezerozero", 100),
        ("ninezero", 90),
    ],
)
def test_solution(s, expected):
    assert solution(s) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("one4seveneight", 1478),
        ("23four5six7", 234567),
        ("2three45sixseven", 234567),
        ("123", 123),
        ("zero", 0),
        ("zero9eight", 98),
        ("onezerozero", 100),
        ("ninezero", 90),
    ],
)
def test_solution_refactored(s, expected):
    assert solution_refactored(s) == expected


@pytest.mark.parametrize(
    "s",
    [
        "one4seveneight",
        "23four5six7",
        "2three45sixseven",
        "123",
        "zero",
        "zero9eight",
        "onezerozero",
        "ninezero",
    ],
)
def test_solution_and_refactored_return_same_result(s):
    assert solution(s) == solution_refactored(s)
