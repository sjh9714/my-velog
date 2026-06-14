import pytest

from solution import gcd, lcm, solution, solution_refactored


@pytest.mark.parametrize(
    ("n", "m", "expected"),
    [
        (3, 12, [3, 12]),
        (2, 5, [1, 10]),
        (6, 6, [6, 6]),
        (4, 8, [4, 8]),
        (9, 27, [9, 27]),
        (14, 21, [7, 42]),
    ],
)
def test_solution(n, m, expected):
    assert solution(n, m) == expected


@pytest.mark.parametrize(
    ("n", "m", "expected"),
    [
        (3, 12, [3, 12]),
        (2, 5, [1, 10]),
        (6, 6, [6, 6]),
        (4, 8, [4, 8]),
        (9, 27, [9, 27]),
        (14, 21, [7, 42]),
    ],
)
def test_solution_refactored(n, m, expected):
    assert solution_refactored(n, m) == expected


@pytest.mark.parametrize("n, m", [(3, 12), (2, 5), (6, 6), (4, 8), (9, 27), (14, 21)])
def test_solution_and_refactored_return_same_result(n, m):
    assert solution(n, m) == solution_refactored(n, m)


def test_helper_functions():
    assert gcd(14, 21) == 7
    assert lcm(14, 21) == 42
