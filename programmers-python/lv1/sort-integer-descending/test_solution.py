import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (118372, 873211),
        (15, 51),
        (1000000, 1000000),
        (9876543210, 9876543210),
        (10200, 21000),
        (999, 999),
    ],
)
def test_solution(n, expected):
    assert solution(n) == expected


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (118372, 873211),
        (15, 51),
        (1000000, 1000000),
        (9876543210, 9876543210),
        (10200, 21000),
        (999, 999),
    ],
)
def test_solution_refactored(n, expected):
    assert solution_refactored(n) == expected


@pytest.mark.parametrize(
    "n",
    [118372, 15, 1000000, 9876543210, 10200, 999],
)
def test_solution_and_refactored_return_same_result(n):
    assert solution(n) == solution_refactored(n)
