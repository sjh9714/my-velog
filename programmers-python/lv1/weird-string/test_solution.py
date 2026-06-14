import pytest

from solution import solution, solution_partial, solution_refactored


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("try hello world", "TrY HeLlO WoRlD"),
        ("hello", "HeLlO"),
        ("a b c", "A B C"),
        ("  hello", "  HeLlO"),
        ("hello  world", "HeLlO  WoRlD"),
        ("hello ", "HeLlO "),
        ("  multiple   spaces  ", "  MuLtIpLe   SpAcEs  "),
    ],
)
def test_solution(s, expected):
    assert solution(s) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("try hello world", "TrY HeLlO WoRlD"),
        ("hello", "HeLlO"),
        ("a b c", "A B C"),
        ("  hello", "  HeLlO"),
        ("hello  world", "HeLlO  WoRlD"),
        ("hello ", "HeLlO "),
        ("  multiple   spaces  ", "  MuLtIpLe   SpAcEs  "),
    ],
)
def test_solution_refactored(s, expected):
    assert solution_refactored(s) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("try hello world", "TrY HeLlO WoRlD"),
        ("hello", "HeLlO"),
        ("a b c", "A B C"),
    ],
)
def test_solution_partial_passes_simple_cases(s, expected):
    assert solution_partial(s) == expected


@pytest.mark.parametrize(
    ("s", "expected"),
    [
        ("  hello", "  HeLlO"),
        ("hello  world", "HeLlO  WoRlD"),
        ("hello ", "HeLlO "),
        ("  multiple   spaces  ", "  MuLtIpLe   SpAcEs  "),
    ],
)
def test_solution_partial_fails_when_spaces_must_be_preserved(s, expected):
    assert solution_partial(s) != expected


@pytest.mark.parametrize(
    "s",
    [
        "try hello world",
        "hello",
        "a b c",
        "  hello",
        "hello  world",
        "hello ",
        "  multiple   spaces  ",
    ],
)
def test_solution_and_refactored_return_same_result(s):
    assert solution(s) == solution_refactored(s)
