import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("abcde", "c"),
        ("qwer", "we"),
        ("a", "a"),
        ("ab", "ab"),
        ("hello", "l"),
        ("python", "th"),
    ],
)
def test_solution(s, expected):
    assert solution(s) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("abcde", "c"),
        ("qwer", "we"),
        ("a", "a"),
        ("ab", "ab"),
        ("hello", "l"),
        ("python", "th"),
    ],
)
def test_solution_refactored(s, expected):
    assert solution_refactored(s) == expected


@pytest.mark.parametrize(
    "s",
    [
        "abcde",
        "qwer",
        "a",
        "ab",
        "hello",
        "python",
    ],
)
def test_original_and_refactored_return_same_result(s):
    assert solution(s) == solution_refactored(s)
