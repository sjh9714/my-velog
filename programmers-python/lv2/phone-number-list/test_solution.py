import pytest

from solution import solution, solution_failed, solution_refactored


TEST_CASES = [
    (["119", "97674223", "1195524421"], False),
    (["123", "456", "789"], True),
    (["12", "123", "1235", "567", "88"], False),
    (["1", "11"], False),
    (["911", "97625999", "91125426"], False),
    (["1235", "12", "567"], False),
    (["123", "124", "125"], True),
    (["987654321"], True),
]


@pytest.mark.parametrize(("phone_book", "expected"), TEST_CASES)
def test_solution(phone_book, expected):
    assert solution(phone_book[:]) == expected


@pytest.mark.parametrize(("phone_book", "expected"), TEST_CASES)
def test_solution_refactored(phone_book, expected):
    assert solution_refactored(phone_book[:]) == expected


@pytest.mark.parametrize(("phone_book", "expected"), TEST_CASES)
def test_solution_and_refactored_return_same_result(phone_book, expected):
    assert solution(phone_book[:]) == solution_refactored(phone_book[:])


def test_solution_failed_shows_iteration_mutation_edge_case():
    assert solution_failed(["1", "11"]) is True
