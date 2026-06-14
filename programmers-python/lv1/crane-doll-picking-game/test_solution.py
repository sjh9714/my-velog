import copy

import pytest

from solution import solution, solution_refactored


@pytest.mark.parametrize(
    ("board", "moves", "expected"),
    [
        (
            [
                [0, 0, 0, 0, 0],
                [0, 0, 1, 0, 3],
                [0, 2, 5, 0, 1],
                [4, 2, 4, 4, 2],
                [3, 5, 1, 3, 1],
            ],
            [1, 5, 3, 5, 1, 2, 1, 4],
            4,
        ),
        (
            [
                [0, 0],
                [0, 0],
            ],
            [1, 2, 1],
            0,
        ),
        (
            [
                [1, 1],
                [0, 0],
            ],
            [1, 2],
            2,
        ),
        (
            [
                [1, 2],
                [0, 0],
            ],
            [1, 2],
            0,
        ),
        (
            [
                [1, 1, 2, 2],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
            [1, 2, 3, 4],
            4,
        ),
    ],
)
def test_solution(board, moves, expected):
    assert solution(copy.deepcopy(board), moves) == expected


@pytest.mark.parametrize(
    ("board", "moves", "expected"),
    [
        (
            [
                [0, 0, 0, 0, 0],
                [0, 0, 1, 0, 3],
                [0, 2, 5, 0, 1],
                [4, 2, 4, 4, 2],
                [3, 5, 1, 3, 1],
            ],
            [1, 5, 3, 5, 1, 2, 1, 4],
            4,
        ),
        (
            [
                [0, 0],
                [0, 0],
            ],
            [1, 2, 1],
            0,
        ),
        (
            [
                [1, 1],
                [0, 0],
            ],
            [1, 2],
            2,
        ),
        (
            [
                [1, 2],
                [0, 0],
            ],
            [1, 2],
            0,
        ),
        (
            [
                [1, 1, 2, 2],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
            [1, 2, 3, 4],
            4,
        ),
    ],
)
def test_solution_refactored(board, moves, expected):
    assert solution_refactored(copy.deepcopy(board), moves) == expected


@pytest.mark.parametrize(
    ("board", "moves"),
    [
        (
            [
                [0, 0, 0, 0, 0],
                [0, 0, 1, 0, 3],
                [0, 2, 5, 0, 1],
                [4, 2, 4, 4, 2],
                [3, 5, 1, 3, 1],
            ],
            [1, 5, 3, 5, 1, 2, 1, 4],
        ),
        ([[0, 0], [0, 0]], [1, 2, 1]),
        ([[1, 1], [0, 0]], [1, 2]),
        ([[1, 2], [0, 0]], [1, 2]),
        ([[1, 1, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], [1, 2, 3, 4]),
    ],
)
def test_solution_and_refactored_return_same_result(board, moves):
    assert solution(copy.deepcopy(board), moves) == solution_refactored(copy.deepcopy(board), moves)
