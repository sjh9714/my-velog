import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (10, True),
        (12, True),
        (11, False),
        (13, False),
        (18, True),
        (100, True),
        (101, False),
    ],
)
def test_solution(x, expected):
    assert solution(x) is expected


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (10, True),
        (12, True),
        (11, False),
        (13, False),
        (18, True),
        (100, True),
        (101, False),
    ],
)
def test_solution_refactored(x, expected):
    assert solution_refactored(x) is expected


@pytest.mark.parametrize("x", [10, 12, 11, 13, 18, 100, 101])
def test_solution_and_refactored_return_same_result(x):
    assert solution(x) == solution_refactored(x)
