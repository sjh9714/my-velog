import pytest

from solution import solution, solution_one_liner


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("pPoooyY", True),
        ("Pyy", False),
        ("abc", True),
        ("ppyy", True),
        ("pyp", False),
        ("PYpy", True),
        ("", True),
    ],
)
def test_solution(s, expected):
    assert solution(s) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("pPoooyY", True),
        ("Pyy", False),
        ("abc", True),
        ("ppyy", True),
        ("pyp", False),
        ("PYpy", True),
        ("", True),
    ],
)
def test_solution_one_liner(s, expected):
    assert solution_one_liner(s) == expected


@pytest.mark.parametrize(
    "s",
    ["pPoooyY", "Pyy", "abc", "ppyy", "pyp", "PYpy", ""],
)
def test_solution_and_one_liner_return_same_result(s):
    assert solution(s) == solution_one_liner(s)
