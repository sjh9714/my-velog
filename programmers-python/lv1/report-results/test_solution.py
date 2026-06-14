import pytest

from solution import solution, solution_refactored


TEST_CASES = [
    (
        ["muzi", "frodo", "apeach", "neo"],
        ["muzi frodo", "apeach frodo", "frodo neo", "muzi neo", "apeach muzi"],
        2,
        [2, 1, 1, 0],
    ),
    (
        ["con", "ryan"],
        ["ryan con", "ryan con", "ryan con", "ryan con"],
        3,
        [0, 0],
    ),
    (
        ["a", "b", "c"],
        ["a b", "a b", "c b"],
        2,
        [1, 0, 1],
    ),
    (
        ["a", "b"],
        [],
        1,
        [0, 0],
    ),
    (
        ["a", "b", "c", "d"],
        ["a d", "b d", "c a"],
        2,
        [1, 1, 0, 0],
    ),
    (
        ["a", "b", "c"],
        ["a b", "c a"],
        2,
        [0, 0, 0],
    ),
]


@pytest.mark.parametrize(("id_list", "report", "k", "expected"), TEST_CASES)
def test_solution(id_list, report, k, expected):
    assert solution(id_list, report, k) == expected


@pytest.mark.parametrize(("id_list", "report", "k", "expected"), TEST_CASES)
def test_solution_refactored(id_list, report, k, expected):
    assert solution_refactored(id_list, report, k) == expected


@pytest.mark.parametrize(("id_list", "report", "k", "expected"), TEST_CASES)
def test_solution_and_refactored_return_same_result(id_list, report, k, expected):
    assert solution(id_list, report, k) == solution_refactored(id_list, report, k)
