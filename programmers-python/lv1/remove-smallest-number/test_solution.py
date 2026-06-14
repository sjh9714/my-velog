import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("arr", "expected"),
    [
        ([4, 3, 2, 1], [4, 3, 2]),
        ([10], [-1]),
        ([1, 2, 3, 4], [2, 3, 4]),
        ([2, 1], [2]),
        ([5, 3, 7, 2], [5, 3, 7]),
    ],
)
def test_solution(arr, expected):
    assert solution(arr[:]) == expected


@pytest.mark.parametrize(
    ("arr", "expected"),
    [
        ([4, 3, 2, 1], [4, 3, 2]),
        ([10], [-1]),
        ([1, 2, 3, 4], [2, 3, 4]),
        ([2, 1], [2]),
        ([5, 3, 7, 2], [5, 3, 7]),
    ],
)
def test_solution_refactored(arr, expected):
    assert solution_refactored(arr[:]) == expected


@pytest.mark.parametrize(
    "arr",
    [
        [4, 3, 2, 1],
        [10],
        [1, 2, 3, 4],
        [2, 1],
        [5, 3, 7, 2],
    ],
)
def test_solution_and_refactored_return_same_result(arr):
    assert solution(arr[:]) == solution_refactored(arr[:])
