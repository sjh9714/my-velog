import pytest

from solution import solution, solution_failed, solution_refactored


@pytest.mark.parametrize(
    ("lottos", "win_nums", "expected"),
    [
        ([44, 1, 0, 0, 31, 25], [31, 10, 45, 1, 6, 19], [3, 5]),
        ([0, 0, 0, 0, 0, 0], [38, 19, 20, 40, 15, 25], [1, 6]),
        ([45, 4, 35, 20, 3, 9], [20, 9, 3, 45, 4, 35], [1, 1]),
        ([1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12], [6, 6]),
        ([1, 2, 3, 4, 5, 6], [1, 8, 9, 10, 11, 12], [6, 6]),
        ([0, 0, 1, 2, 3, 4], [1, 2, 5, 6, 7, 8], [3, 5]),
    ],
)
def test_solution(lottos, win_nums, expected):
    assert solution(lottos, win_nums) == expected


@pytest.mark.parametrize(
    ("lottos", "win_nums", "expected"),
    [
        ([44, 1, 0, 0, 31, 25], [31, 10, 45, 1, 6, 19], [3, 5]),
        ([0, 0, 0, 0, 0, 0], [38, 19, 20, 40, 15, 25], [1, 6]),
        ([45, 4, 35, 20, 3, 9], [20, 9, 3, 45, 4, 35], [1, 1]),
        ([1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12], [6, 6]),
        ([1, 2, 3, 4, 5, 6], [1, 8, 9, 10, 11, 12], [6, 6]),
        ([0, 0, 1, 2, 3, 4], [1, 2, 5, 6, 7, 8], [3, 5]),
    ],
)
def test_solution_refactored(lottos, win_nums, expected):
    assert solution_refactored(lottos, win_nums) == expected


def test_solution_failed_shows_test_15_like_edge_case():
    assert solution_failed([0, 0, 0, 0, 0, 0], [38, 19, 20, 40, 15, 25]) == [0, 6]


@pytest.mark.parametrize(
    ("lottos", "win_nums"),
    [
        ([44, 1, 0, 0, 31, 25], [31, 10, 45, 1, 6, 19]),
        ([0, 0, 0, 0, 0, 0], [38, 19, 20, 40, 15, 25]),
        ([45, 4, 35, 20, 3, 9], [20, 9, 3, 45, 4, 35]),
        ([1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]),
        ([1, 2, 3, 4, 5, 6], [1, 8, 9, 10, 11, 12]),
        ([0, 0, 1, 2, 3, 4], [1, 2, 5, 6, 7, 8]),
    ],
)
def test_solution_and_refactored_return_same_result(lottos, win_nums):
    assert solution(lottos, win_nums) == solution_refactored(lottos, win_nums)
