import pytest

from solution import solution, solution_failed, solution_refactored


@pytest.mark.parametrize(
    ("num", "expected"),
    [
        (6, 8),
        (16, 4),
        (626331, -1),
        (1, 0),
        (2, 1),
        (3, 7),
    ],
)
def test_solution(num, expected):
    assert solution(num) == expected


@pytest.mark.parametrize(
    ("num", "expected"),
    [
        (6, 8),
        (16, 4),
        (626331, -1),
        (1, 0),
        (2, 1),
        (3, 7),
    ],
)
def test_solution_refactored(num, expected):
    assert solution_refactored(num) == expected


@pytest.mark.parametrize("num", [6, 16, 626331, 1, 2, 3])
def test_solution_and_refactored_return_same_result(num):
    assert solution(num) == solution_refactored(num)


def test_failed_solution_does_not_handle_one_before_loop():
    assert solution_failed(1) == 3
    assert solution(1) == 0
