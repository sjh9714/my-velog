import pytest

from solution import solution, solution_refactored


TEST_CASES = [
    (
        [
            ["yellow_hat", "headgear"],
            ["blue_sunglasses", "eyewear"],
            ["green_turban", "headgear"],
        ],
        5,
    ),
    (
        [
            ["crow_mask", "face"],
            ["blue_sunglasses", "face"],
            ["smoky_makeup", "face"],
        ],
        3,
    ),
    (
        [
            ["hat", "headgear"],
        ],
        1,
    ),
    (
        [
            ["hat", "headgear"],
            ["sunglasses", "eyewear"],
            ["shirt", "top"],
        ],
        7,
    ),
    (
        [
            ["hat", "headgear"],
            ["cap", "headgear"],
            ["sunglasses", "eyewear"],
            ["glasses", "eyewear"],
            ["shirt", "top"],
        ],
        17,
    ),
    (
        [
            ["a", "type1"],
            ["b", "type1"],
            ["c", "type1"],
            ["d", "type2"],
        ],
        7,
    ),
]


@pytest.mark.parametrize(("clothes", "expected"), TEST_CASES)
def test_solution(clothes, expected):
    assert solution(clothes) == expected


@pytest.mark.parametrize(("clothes", "expected"), TEST_CASES)
def test_solution_refactored(clothes, expected):
    assert solution_refactored(clothes) == expected


@pytest.mark.parametrize(("clothes", "expected"), TEST_CASES)
def test_solution_and_refactored_return_same_result(clothes, expected):
    assert solution(clothes) == solution_refactored(clothes)
