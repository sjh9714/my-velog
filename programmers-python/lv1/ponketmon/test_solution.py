import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("nums", "expected"),
    [
        ([3, 1, 2, 3], 2),
        ([3, 3, 3, 2, 2, 4], 3),
        ([3, 3, 3, 2, 2, 2], 2),
        ([1, 2, 3, 4], 2),
        ([1, 1], 1),
        ([1, 2, 1, 2], 2),
    ],
)
def test_solution(nums, expected):
    assert solution(nums) == expected


@pytest.mark.parametrize(
    ("nums", "expected"),
    [
        ([3, 1, 2, 3], 2),
        ([3, 3, 3, 2, 2, 4], 3),
        ([3, 3, 3, 2, 2, 2], 2),
        ([1, 2, 3, 4], 2),
        ([1, 1], 1),
        ([1, 2, 1, 2], 2),
    ],
)
def test_solution_refactored(nums, expected):
    assert solution_refactored(nums) == expected


@pytest.mark.parametrize(
    "nums",
    [
        [3, 1, 2, 3],
        [3, 3, 3, 2, 2, 4],
        [3, 3, 3, 2, 2, 2],
        [1, 2, 3, 4],
        [1, 1],
        [1, 2, 1, 2],
    ],
)
def test_solution_and_refactored_return_same_result(nums):
    assert solution(nums) == solution_refactored(nums)


def test_solution_handles_large_input():
    nums = list(range(5000)) + list(range(5000))

    assert solution(nums) == 5000
    assert solution_refactored(nums) == 5000
