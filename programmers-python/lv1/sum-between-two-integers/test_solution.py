import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (3, 5, 12),
        (3, 3, 3),
        (5, 3, 12),
        (-3, 1, -5),
        (-5, -3, -12),
        (0, 0, 0),
    ],
)
def test_solution(a, b, expected):
    assert solution(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (3, 5, 12),
        (3, 3, 3),
        (5, 3, 12),
        (-3, 1, -5),
        (-5, -3, -12),
        (0, 0, 0),
    ],
)
def test_solution_refactored(a, b, expected):
    assert solution_refactored(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (3, 5),
        (3, 3),
        (5, 3),
        (-3, 1),
        (-5, -3),
        (0, 0),
    ],
)
def test_original_and_refactored_return_same_result(a, b):
    assert solution(a, b) == solution_refactored(a, b)
