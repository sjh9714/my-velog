import pytest

from solution import solution, solution_refactored


TEST_CASES = [
    ([6, 10, 2], "6210"),
    ([3, 30, 34, 5, 9], "9534330"),
    ([0, 0, 0], "0"),
    ([0, 0, 1], "100"),
    ([12, 121], "12121"),
    ([1000, 0, 0], "100000"),
    ([10, 2], "210"),
    ([1, 10, 100, 1000], "1101001000"),
]


@pytest.mark.parametrize(("numbers", "expected"), TEST_CASES)
def test_solution(numbers, expected):
    assert solution(numbers) == expected


@pytest.mark.parametrize(("numbers", "expected"), TEST_CASES)
def test_solution_refactored(numbers, expected):
    assert solution_refactored(numbers) == expected


@pytest.mark.parametrize(("numbers", "expected"), TEST_CASES)
def test_solution_and_refactored_return_same_result(numbers, expected):
    assert solution(numbers) == solution_refactored(numbers)
