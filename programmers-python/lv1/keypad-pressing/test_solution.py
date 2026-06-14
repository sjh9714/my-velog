import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("numbers", "hand", "expected"),
    [
        ([1, 3, 4, 5, 8, 2, 1, 4, 5, 9, 5], "right", "LRLLLRLLRRL"),
        ([7, 0, 8, 2, 8, 3, 1, 5, 7, 6, 2], "left", "LRLLRRLLLRR"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "right", "LLRLLRLLRL"),
        ([1, 4, 7], "right", "LLL"),
        ([3, 6, 9], "left", "RRR"),
        ([2], "left", "L"),
        ([2], "right", "R"),
        ([0, 8, 5, 2], "left", "LLLL"),
    ],
)
def test_solution(numbers, hand, expected):
    assert solution(numbers, hand) == expected


@pytest.mark.parametrize(
    ("numbers", "hand", "expected"),
    [
        ([1, 3, 4, 5, 8, 2, 1, 4, 5, 9, 5], "right", "LRLLLRLLRRL"),
        ([7, 0, 8, 2, 8, 3, 1, 5, 7, 6, 2], "left", "LRLLRRLLLRR"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "right", "LLRLLRLLRL"),
        ([1, 4, 7], "right", "LLL"),
        ([3, 6, 9], "left", "RRR"),
        ([2], "left", "L"),
        ([2], "right", "R"),
        ([0, 8, 5, 2], "left", "LLLL"),
    ],
)
def test_solution_refactored(numbers, hand, expected):
    assert solution_refactored(numbers, hand) == expected


@pytest.mark.parametrize(
    ("numbers", "hand"),
    [
        ([1, 3, 4, 5, 8, 2, 1, 4, 5, 9, 5], "right"),
        ([7, 0, 8, 2, 8, 3, 1, 5, 7, 6, 2], "left"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "right"),
        ([1, 4, 7], "right"),
        ([3, 6, 9], "left"),
        ([2], "left"),
        ([2], "right"),
        ([0, 8, 5, 2], "left"),
    ],
)
def test_solution_and_refactored_return_same_result(numbers, hand):
    assert solution(numbers, hand) == solution_refactored(numbers, hand)
