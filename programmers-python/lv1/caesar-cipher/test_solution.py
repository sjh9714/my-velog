import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("s", "n", "expected"),
    [
        ("AB", 1, "BC"),
        ("z", 1, "a"),
        ("a B z", 4, "e F d"),
        ("Z", 1, "A"),
        ("Hello World", 5, "Mjqqt Btwqi"),
        ("A a Z z", 25, "Z z Y y"),
        ("   ", 3, "   "),
    ],
)
def test_solution(s, n, expected):
    assert solution(s, n) == expected


@pytest.mark.parametrize(
    ("s", "n", "expected"),
    [
        ("AB", 1, "BC"),
        ("z", 1, "a"),
        ("a B z", 4, "e F d"),
        ("Z", 1, "A"),
        ("Hello World", 5, "Mjqqt Btwqi"),
        ("A a Z z", 25, "Z z Y y"),
        ("   ", 3, "   "),
    ],
)
def test_solution_refactored(s, n, expected):
    assert solution_refactored(s, n) == expected


@pytest.mark.parametrize(
    ("s", "n"),
    [
        ("AB", 1),
        ("z", 1),
        ("a B z", 4),
        ("Z", 1),
        ("Hello World", 5),
        ("A a Z z", 25),
        ("   ", 3),
    ],
)
def test_solution_and_refactored_return_same_result(s, n):
    assert solution(s, n) == solution_refactored(s, n)
