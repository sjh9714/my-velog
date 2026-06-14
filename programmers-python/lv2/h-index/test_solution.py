import pytest

from solution import solution, solution_refactored


TEST_CASES = [
    ([3, 0, 6, 1, 5], 3),
    ([0, 0, 0], 0),
    ([1, 3, 5, 7, 9], 3),
    ([10, 8, 5, 4, 3], 4),
    ([25, 8, 5, 3, 3], 3),
    ([1], 1),
    ([0], 0),
    ([4, 4, 4, 4], 4),
]


@pytest.mark.parametrize(("citations", "expected"), TEST_CASES)
def test_solution(citations, expected):
    assert solution(citations[:]) == expected


@pytest.mark.parametrize(("citations", "expected"), TEST_CASES)
def test_solution_refactored(citations, expected):
    assert solution_refactored(citations) == expected


@pytest.mark.parametrize(("citations", "expected"), TEST_CASES)
def test_solution_and_refactored_return_same_result(citations, expected):
    assert solution(citations[:]) == solution_refactored(citations)
