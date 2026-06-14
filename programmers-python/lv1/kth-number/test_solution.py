import pytest

from solution import solution, solution_refactored


TEST_CASES = [
    (
        [1, 5, 2, 6, 3, 7, 4],
        [[2, 5, 3], [4, 4, 1], [1, 7, 3]],
        [5, 6, 3],
    ),
    (
        [3, 1, 2],
        [[1, 3, 2]],
        [2],
    ),
    (
        [1, 2, 3, 4, 5],
        [[1, 5, 5], [1, 5, 1]],
        [5, 1],
    ),
    (
        [10, 20, 30],
        [[2, 2, 1]],
        [20],
    ),
    (
        [9, 8, 7, 6],
        [[1, 4, 1], [1, 4, 4]],
        [6, 9],
    ),
    (
        [5, 5, 1, 3],
        [[1, 4, 2], [2, 3, 1]],
        [3, 1],
    ),
]


@pytest.mark.parametrize(("array", "commands", "expected"), TEST_CASES)
def test_solution(array, commands, expected):
    assert solution(array, commands) == expected


@pytest.mark.parametrize(("array", "commands", "expected"), TEST_CASES)
def test_solution_refactored(array, commands, expected):
    assert solution_refactored(array, commands) == expected


@pytest.mark.parametrize(("array", "commands", "expected"), TEST_CASES)
def test_solution_and_refactored_return_same_result(array, commands, expected):
    assert solution(array, commands) == solution_refactored(array, commands)
