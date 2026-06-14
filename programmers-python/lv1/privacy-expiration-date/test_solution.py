import pytest

from solution import solution, solution_refactored


TEST_CASES = [
    (
        "2022.05.19",
        ["A 6", "B 12", "C 3"],
        ["2021.05.02 A", "2021.07.01 B", "2022.02.19 C", "2022.02.20 C"],
        [1, 3],
    ),
    (
        "2020.01.01",
        ["Z 3", "D 5"],
        ["2019.01.01 D", "2019.11.15 Z", "2019.08.02 D", "2019.07.01 D", "2018.12.28 Z"],
        [1, 4, 5],
    ),
    (
        "2022.05.19",
        ["A 1"],
        ["2022.04.19 A"],
        [1],
    ),
    (
        "2022.05.19",
        ["A 1"],
        ["2022.04.20 A"],
        [],
    ),
    (
        "2023.01.01",
        ["A 2"],
        ["2022.11.01 A"],
        [1],
    ),
    (
        "2022.12.28",
        ["A 1", "B 2", "C 12"],
        ["2022.11.28 A", "2022.11.01 B", "2021.12.28 C", "2021.12.29 C"],
        [1, 3],
    ),
]


@pytest.mark.parametrize(("today", "terms", "privacies", "expected"), TEST_CASES)
def test_solution(today, terms, privacies, expected):
    assert solution(today, terms, privacies) == expected


@pytest.mark.parametrize(("today", "terms", "privacies", "expected"), TEST_CASES)
def test_solution_refactored(today, terms, privacies, expected):
    assert solution_refactored(today, terms, privacies) == expected


@pytest.mark.parametrize(("today", "terms", "privacies", "expected"), TEST_CASES)
def test_solution_and_refactored_return_same_result(today, terms, privacies, expected):
    assert solution(today, terms, privacies) == solution_refactored(today, terms, privacies)
