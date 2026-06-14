import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (12, 28),
        (5, 6),
        (1, 1),
        (16, 31),
        (25, 31),
        (2, 3),
    ],
)
def test_solution(n, expected):
    assert solution(n) == expected


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (12, 28),
        (5, 6),
        (1, 1),
        (16, 31),
        (25, 31),
        (2, 3),
    ],
)
def test_solution_refactored(n, expected):
    assert solution_refactored(n) == expected


@pytest.mark.parametrize("n", [12, 5, 1, 16, 25, 2])
def test_solution_and_refactored_return_same_result(n):
    assert solution(n) == solution_refactored(n)
