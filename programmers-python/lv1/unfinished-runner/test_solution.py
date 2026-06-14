import pytest

from solution import solution, solution_timeout, solution_with_dict


@pytest.mark.parametrize(
    ("participant", "completion", "expected"),
    [
        (["leo", "kiki", "eden"], ["eden", "kiki"], "leo"),
        (
            ["marina", "josipa", "nikola", "vinko", "filipa"],
            ["josipa", "filipa", "marina", "nikola"],
            "vinko",
        ),
        (["mislav", "stanko", "mislav", "ana"], ["stanko", "ana", "mislav"], "mislav"),
        (["alice", "bob", "charlie"], ["bob", "charlie"], "alice"),
        (["alice", "bob", "charlie"], ["alice", "bob"], "charlie"),
        (["a", "a", "a", "b"], ["a", "a", "b"], "a"),
    ],
)
def test_solution(participant, completion, expected):
    assert solution(participant[:], completion[:]) == expected


@pytest.mark.parametrize(
    ("participant", "completion", "expected"),
    [
        (["leo", "kiki", "eden"], ["eden", "kiki"], "leo"),
        (
            ["marina", "josipa", "nikola", "vinko", "filipa"],
            ["josipa", "filipa", "marina", "nikola"],
            "vinko",
        ),
        (["mislav", "stanko", "mislav", "ana"], ["stanko", "ana", "mislav"], "mislav"),
        (["a", "a", "a", "b"], ["a", "a", "b"], "a"),
    ],
)
def test_solution_timeout_returns_correct_answer_for_small_inputs(
    participant, completion, expected
):
    assert solution_timeout(participant[:], completion[:]) == expected


@pytest.mark.parametrize(
    ("participant", "completion"),
    [
        (["leo", "kiki", "eden"], ["eden", "kiki"]),
        (
            ["marina", "josipa", "nikola", "vinko", "filipa"],
            ["josipa", "filipa", "marina", "nikola"],
        ),
        (["mislav", "stanko", "mislav", "ana"], ["stanko", "ana", "mislav"]),
        (["alice", "bob", "charlie"], ["bob", "charlie"]),
        (["alice", "bob", "charlie"], ["alice", "bob"]),
        (["a", "a", "a", "b"], ["a", "a", "b"]),
    ],
)
def test_solution_and_dict_solution_return_same_result(participant, completion):
    assert solution(participant[:], completion[:]) == solution_with_dict(
        participant[:], completion[:]
    )


def test_solution_handles_large_input():
    participant = [f"runner{i}" for i in range(20000)]
    completion = participant[:-1]

    assert solution(participant[:], completion[:]) == "runner19999"
    assert solution_with_dict(participant[:], completion[:]) == "runner19999"
