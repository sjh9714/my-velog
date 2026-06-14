import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("arr", "divisor", "expected"),
    [
        ([5, 9, 7, 10], 5, [5, 10]),
        ([2, 36, 1, 3], 1, [1, 2, 3, 36]),
        ([3, 2, 6], 10, [-1]),
        ([1, 2, 3, 4], 2, [2, 4]),
        ([4, 8, 12], 4, [4, 8, 12]),
        ([7, 5, 9], 5, [5]),
    ],
)
def test_solution(arr, divisor, expected):
    assert solution(arr[:], divisor) == expected


@pytest.mark.parametrize(
    ("arr", "divisor", "expected"),
    [
        ([5, 9, 7, 10], 5, [5, 10]),
        ([2, 36, 1, 3], 1, [1, 2, 3, 36]),
        ([3, 2, 6], 10, [-1]),
        ([1, 2, 3, 4], 2, [2, 4]),
        ([4, 8, 12], 4, [4, 8, 12]),
        ([7, 5, 9], 5, [5]),
    ],
)
def test_solution_refactored(arr, divisor, expected):
    assert solution_refactored(arr[:], divisor) == expected


@pytest.mark.parametrize(
    ("arr", "divisor"),
    [
        ([5, 9, 7, 10], 5),
        ([2, 36, 1, 3], 1),
        ([3, 2, 6], 10),
        ([1, 2, 3, 4], 2),
        ([4, 8, 12], 4),
        ([7, 5, 9], 5),
    ],
)
def test_solution_and_refactored_return_same_result(arr, divisor):
    assert solution(arr[:], divisor) == solution_refactored(arr[:], divisor)
